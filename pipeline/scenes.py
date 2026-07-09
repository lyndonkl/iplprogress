"""R1a/R1b scene aggregates — scenes/coldopen.json + ch1.json + sandbox.json.

One chronological pass over the corpus (super-over innings excluded, per the
standing rule) computing every number the cold open and Chapter 1 put on
screen. All recipes follow research/metrics-catalog.md and reconcile exactly
with its verified teasers (the reconciliation is asserted by
tests/test_r1a.py against an independent recount):

  cold open   200+ totals per season (ANY innings with >= 200 total runs —
              the definition that reproduces the data-profile table, 65 in
              IPL 2026), avg full first-innings score (excludes D/L,
              no-results, and matches whose chase target was set for fewer
              than 20 overs), matches, deliveries, corpus facts.
  ch1         (a) ignition: per-ball-index SR curves 1..30 per era band +
              first-10-ball SR per season; (b) the out-rate, ball by ball
              (KM-style discrete hazard: dismissals at index n / batters
              reaching n) + the headline first-10 hazard (ALL dismissals of
              batters at faced-count 0..10 — non-striker run-outs and
              dismissals on wides included — per first-10 ball faced: the
              catalog's 5.04% vs 4.93%); (c) out-rate defiers per ball index
              1/3/5/10/15/20 (min 300 balls in band); (d) six democratization
              per season (>=10-six players; top-10 share over >=30-ball
              qualifiers — the catalog's 35.9% -> 28.1%; plus per-season
              legal-ball counts + balls_per_six so "a six every 21 -> every
              12" traces to an artifact); (e) the Aerial
              Risk Ledger (attempt proxy = sixes + caught excl. caught-and-
              bowled, per 100 balls faced, with the catalog's caveat text);
              (f) the WPL beat (first-10 SR, four-led run DNA, and the
              League Maturity Clock: RR = ALL runs / legal balls — wides
              AND no-balls excluded from the denominator).

  sandbox     (R6b) the full-bowl descriptor: the famous-match preset
              (2019 IPL Final, MI beat CSK by 1 run — resolved by
              league+season+stage+teams+margin, never a hard-coded index),
              the TEAM + SEASON facet lists (teams.json / groups.json), the
              tap-a-ball tooltip field roster, and the ten-flag guided-tour
              rail (tourFlags) — each flag resolved and count-validated against
              the real deliveries at build so it can never point at nothing.

Era bands (R1a data contract): IPL 2008-2010, 2011-2015, 2016-2019,
2020-2022, 2023-2026; WPL pooled 2023-2026.

Stdlib only; byte-deterministic (compact JSON, sorted keys). Run after
flatten.py (updates meta.json's file ledger).
"""

from __future__ import annotations

import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import canon
import flatten
import wallheat
import bowlerplane

SCENES_DIR = canon.OUT_ROOT / "scenes"

MAX_BALL_INDEX = 30  # ignition + out-rate curves cover balls-faced 1..30
# Ball indices the out-rate strip lets the reader tap for era defiers. Balls 1
# and 3 (the sighter's heart) are included so the scene's tap set — 1, 3, 5,
# 10, 15, 20 — is fully data-backed (storyboard C1-4 / finding #11).
DEFIER_INDICES = (1, 3, 5, 10, 15, 20)
DEFIER_MIN_BALLS = 300  # min balls faced in the era band to qualify
SIX_QUALIFIER_BALLS = 30  # >=30 balls faced -> six-concentration universe
RETIRED_KINDS = frozenset({"retired hurt", "retired out"})  # censored, not out

IPL_ERA_BANDS = (
    ("ipl", "2008-2010", 2008, 2010),
    ("ipl", "2011-2015", 2011, 2015),
    ("ipl", "2016-2019", 2016, 2019),
    ("ipl", "2020-2022", 2020, 2022),
    ("ipl", "2023-2026", 2023, 2026),
)
WPL_BAND = ("wpl", "2023-2026", 2023, 2026)  # pooled
ERA_BANDS = IPL_ERA_BANDS + (WPL_BAND,)

AERIAL_CAVEAT = (
    "Aerial-attempt proxy = sixes + caught dismissals (caught-and-bowled "
    "excluded), per 100 balls faced; execution = sixes / (sixes + caught). "
    "Caught includes keeper and slip edges — the corpus has no fielding-"
    "position data — a fixed noise floor that leaves era-over-era "
    "comparisons valid so long as edge rates are stable. True shot-level "
    "intent would need non-public ball-tracking."
)


def band_key(league: str, season: int) -> str:
    if league == "wpl":
        return "wpl " + WPL_BAND[1]
    for _lg, label, lo, hi in IPL_ERA_BANDS:
        if lo <= season <= hi:
            return "ipl " + label
    raise KeyError(f"season {season} outside every IPL era band")


BAND_KEYS = tuple(f"{lg} {label}" for lg, label, _lo, _hi in ERA_BANDS)


class BandStats:
    """Per-era-band accumulators for every Ch 1 metric."""

    def __init__(self):
        z = lambda: [0] * (MAX_BALL_INDEX + 1)  # index 0 unused
        self.ball_count = z()  # deliveries at faced-index n
        self.ball_runs = z()  # batter runs at faced-index n
        self.reaching = z()  # batter-innings that faced >= n balls
        self.dismissed_at = z()  # batters out at faced-count n (any kind bar retired)
        self.innings = 0  # batter-innings (appearances at the crease)
        self.first10_balls = 0
        self.first10_events = 0  # ALL dismissals at faced-count 0..10
        self.aerial_balls = 0  # balls faced (non-wide)
        self.aerial_sixes = 0
        self.aerial_caught = 0  # kind == 'caught' (c&b excluded)
        # per-batter: [innings, balls, reach5, reach10, reach15, reach20,
        #              runs<=5, balls<=5, runs<=10, balls<=10, ...]
        self.batters = defaultdict(lambda: [0] * (2 + len(DEFIER_INDICES) * 3))


class SeasonStats:
    """Per (league, season) accumulators for the cold open + Ch 1 seasonals."""

    def __init__(self):
        self.matches = 0
        self.deliveries = 0
        self.totals200 = 0  # innings (either innings) totalling >= 200
        self.first_full_totals = []  # full first-innings totals
        self.first10_balls = 0
        self.first10_runs = 0
        self.runs_total = 0  # all runs incl. extras
        self.four_runs = 0  # 4 x (runs.batter == 4)
        self.six_runs = 0  # 6 x (runs.batter == 6)
        self.legal_balls = 0  # wides AND no-balls excluded (RR denominator)
        self.batter_sixes = Counter()
        self.batter_balls = Counter()


def build(data_root: Path = canon.DATA_ROOT):
    """The one authoritative corpus pass for both scene documents."""
    bands = {k: BandStats() for k in BAND_KEYS}
    seasons = defaultdict(SeasonStats)
    players = set()
    n_matches = 0
    superover_balls = 0

    for _date, _mid, league, path in flatten.sorted_match_files(data_root):
        with open(path) as fh:
            match = json.load(fh)
        info = match["info"]
        season = canon.canon_season(info)
        reg = info.get("registry", {}).get("people", {})  # name -> stable person-id
        ss = seasons[(league, season)]
        ss.matches += 1
        n_matches += 1
        bs = bands[band_key(league, season)]

        outcome = info.get("outcome", {})
        full_first = not canon.is_dl(info) and outcome.get("result") != "no result"
        first_innings_total = None

        innings_no = 0
        for innings in match.get("innings", []):
            if canon.is_super_over(innings):
                superover_balls += sum(len(o["deliveries"]) for o in innings["overs"])
                continue
            innings_no += 1
            if innings_no == 2:
                target = innings.get("target") or {}
                overs = target.get("overs")
                if overs is not None and float(overs) < 20:
                    full_first = False  # chase target set for < 20 overs
            faced = Counter()
            appeared = set()
            out_at = {}
            per_batter_runs_to = defaultdict(lambda: [0] * len(DEFIER_INDICES))
            per_batter_balls_to = defaultdict(lambda: [0] * len(DEFIER_INDICES))
            innings_runs = 0
            for over in innings["overs"]:
                for dl in over["deliveries"]:
                    ss.deliveries += 1
                    extras = dl.get("extras", {})
                    wide = "wides" in extras
                    striker = dl["batter"]
                    rb = dl["runs"]["batter"]
                    innings_runs += dl["runs"]["total"]
                    ss.runs_total += dl["runs"]["total"]
                    if rb == 4:
                        ss.four_runs += 4
                    elif rb == 6:
                        ss.six_runs += 6
                    if not wide and "noballs" not in extras:
                        ss.legal_balls += 1
                    appeared.add(striker)
                    appeared.add(dl["non_striker"])
                    # n_players is a REGISTRY-PID count (folds spelling variants
                    # onto one person; keeps genuine namesakes distinct), matching
                    # this block's definition string and pipeline/registry.py.
                    players.add(reg.get(striker, striker))
                    players.add(reg.get(dl["bowler"], dl["bowler"]))
                    if not wide:
                        faced[striker] += 1
                        n = faced[striker]
                        ss.batter_balls[striker] += 1
                        if rb == 6:
                            ss.batter_sixes[striker] += 1
                        bs.aerial_balls += 1
                        if rb == 6:
                            bs.aerial_sixes += 1
                        if n <= 10:
                            ss.first10_balls += 1
                            ss.first10_runs += rb
                            bs.first10_balls += 1
                        if n <= MAX_BALL_INDEX:
                            bs.ball_count[n] += 1
                            bs.ball_runs[n] += rb
                        for j, idx in enumerate(DEFIER_INDICES):
                            if n <= idx:
                                per_batter_runs_to[striker][j] += rb
                                per_batter_balls_to[striker][j] += 1
                    for w in dl.get("wickets", []):
                        if w["kind"] == "caught":
                            bs.aerial_caught += 1
                        if w["kind"] in RETIRED_KINDS:
                            continue
                        player_out = w["player_out"]
                        c = faced[player_out]
                        out_at[player_out] = c
                        if c <= 10:
                            bs.first10_events += 1
            for batter in appeared:
                bs.innings += 1
                n = faced[batter]
                for i in range(1, min(n, MAX_BALL_INDEX) + 1):
                    bs.reaching[i] += 1
                c = out_at.get(batter)
                if c is not None and 1 <= c <= MAX_BALL_INDEX:
                    bs.dismissed_at[c] += 1
                rec = bs.batters[batter]
                rec[0] += 1
                rec[1] += n
                for j, idx in enumerate(DEFIER_INDICES):
                    if n >= idx:
                        rec[2 + j * 3] += 1
                    rec[3 + j * 3] += per_batter_runs_to[batter][j]
                    rec[4 + j * 3] += per_batter_balls_to[batter][j]
            if innings_no == 1:
                first_innings_total = innings_runs
            if innings_runs >= 200:
                ss.totals200 += 1
        if full_first and first_innings_total is not None:
            ss.first_full_totals.append(first_innings_total)

    return bands, seasons, players, n_matches, superover_balls


# ---------------------------------------------------------------------------
# Scene documents
# ---------------------------------------------------------------------------


def r1(x):
    return round(x, 1)


def coldopen_doc(seasons, players, n_matches, superover_balls) -> dict:
    rows = []
    keys = [("ipl", s) for s in canon.IPL_SEASONS] + [
        ("wpl", s) for s in canon.WPL_SEASONS
    ]
    for league, season in keys:
        ss = seasons[(league, season)]
        full = ss.first_full_totals
        rows.append(
            {
                "league": league,
                "season": season,
                "matches": ss.matches,
                "deliveries": ss.deliveries,
                "totals200": ss.totals200,
                "avg_first_innings_full": r1(sum(full) / len(full)) if full else None,
                "first_innings_full_count": len(full),
            }
        )
    points_rendered = sum(r["deliveries"] for r in rows)
    return {
        "corpus": {
            "points_rendered": points_rendered,
            "corpus_total": points_rendered + superover_balls,
            "superover_balls": superover_balls,
            "matches": n_matches,
            "players": len(players),
            "ipl_seasons": len(canon.IPL_SEASONS),
            "wpl_seasons": len(canon.WPL_SEASONS),
        },
        "definitions": {
            "totals200": (
                "Innings (either innings, super overs excluded) with a total "
                "of 200 or more runs, per season."
            ),
            "avg_first_innings_full": (
                "Mean first-innings total over uninterrupted matches only: "
                "no-results, D/L-method matches, and matches whose chase "
                "target was set for fewer than 20 overs are excluded."
            ),
            "players": "Distinct players who faced or bowled at least one ball.",
        },
        "seasons": rows,
    }


def band_meta():
    return [
        {"key": f"{lg} {label}", "league": lg, "label": label, "seasons": [lo, hi]}
        for lg, label, lo, hi in ERA_BANDS
    ]


def ignition_section(bands, seasons) -> dict:
    sr_by_ball = {}
    balls_by_ball = {}
    for key, bs in bands.items():
        sr_by_ball[key] = [
            r1(100.0 * bs.ball_runs[n] / bs.ball_count[n]) if bs.ball_count[n] else None
            for n in range(1, MAX_BALL_INDEX + 1)
        ]
        balls_by_ball[key] = bs.ball_count[1:]
    first10 = {"ipl": {}, "wpl": {}}
    for (league, season), ss in sorted(seasons.items()):
        if ss.first10_balls:
            first10[league][str(season)] = r1(100.0 * ss.first10_runs / ss.first10_balls)
    # Era-relative-intent scale + legend for the wall thesis-beat recolour.
    # wallheat.build() recomputes off its own corpus pass; the emitted
    # wallheat.u8 (flatten) uses the identical core, so buffer and scale agree.
    _wh_bytes, wh_config = wallheat.build()
    return {
        "sr_by_ball_index": sr_by_ball,
        "balls_by_ball_index": balls_by_ball,
        "first10_sr_by_season": first10,
        "wallheat": wh_config,
        "definition": (
            "Strike rate per balls-faced index (wides are not balls faced; "
            "no-balls are). Index n = the batter's n-th ball of the innings."
        ),
    }


def outrate_section(bands) -> dict:
    hazard = {}
    reaching = {}
    dismissed = {}
    samples = {}
    first10 = {}
    for key, bs in bands.items():
        hazard[key] = [
            round(100.0 * bs.dismissed_at[n] / bs.reaching[n], 2) if bs.reaching[n] else None
            for n in range(1, MAX_BALL_INDEX + 1)
        ]
        reaching[key] = bs.reaching[1:]
        dismissed[key] = bs.dismissed_at[1:]
        samples[key] = {
            "batter_innings": bs.innings,
            "balls_1_10": bs.first10_balls,
        }
        first10[key] = {
            "hazard_pct": round(100.0 * bs.first10_events / bs.first10_balls, 2),
            "events": bs.first10_events,
            "balls": bs.first10_balls,
        }
    return {
        "hazard_pct_by_ball_index": hazard,
        "reaching_by_ball_index": reaching,
        "dismissed_at_ball_index": dismissed,
        "sample_sizes": samples,
        "first10": first10,
        "definition": (
            "The out-rate, ball by ball (KM-style discrete hazard): "
            "dismissals at balls-faced index n / batter-innings reaching n. "
            "Retired hurt/out are censored, never events; run-outs count "
            "against the player given out (non-striker included, at their "
            "own count). The first10 headline counts every dismissal of a "
            "batter at faced-count 0-10 (dismissals on wides and diamond "
            "ducks included) per first-10 ball faced — the catalog's "
            "5.04% vs 4.93% definition."
        ),
    }


def defiers_section(bands) -> dict:
    out = {}
    for key, bs in bands.items():
        per_index = {}
        base_sr = {}
        base_surv = {}
        for j, idx in enumerate(DEFIER_INDICES):
            cum_runs = sum(bs.ball_runs[1 : idx + 1])
            cum_balls = sum(bs.ball_count[1 : idx + 1])
            base_sr[idx] = 100.0 * cum_runs / cum_balls
            base_surv[idx] = bs.reaching[idx] / bs.innings
        for j, idx in enumerate(DEFIER_INDICES):
            rows = []
            for name, rec in bs.batters.items():
                if rec[1] < DEFIER_MIN_BALLS:
                    continue
                innings, reached = rec[0], rec[2 + j * 3]
                runs_to, balls_to = rec[3 + j * 3], rec[4 + j * 3]
                if not balls_to:
                    continue
                surv = reached / innings
                sr = 100.0 * runs_to / balls_to
                score = surv / base_surv[idx] + sr / base_sr[idx] - 2.0
                rows.append(
                    {
                        "name": name,
                        "score": round(score, 3),
                        "survival_pct": r1(100.0 * surv),
                        "sr_through_ball": r1(sr),
                        "innings": innings,
                        "balls_in_band": rec[1],
                    }
                )
            rows.sort(key=lambda r: (-r["score"], r["name"]))
            per_index[str(idx)] = rows[:5]
        out[key] = {
            "by_ball_index": per_index,
            "baselines": {
                str(idx): {
                    "survival_pct": r1(100.0 * base_surv[idx]),
                    "sr_through_ball": r1(base_sr[idx]),
                }
                for idx in DEFIER_INDICES
            },
        }
    return {
        "bands": out,
        "definition": (
            "For each ball index n in {1, 3, 5, 10, 15, 20}: the batters (min "
            "300 balls faced in the era band) who most defied the era's "
            "out-rate — score = (share of innings surviving to ball n / era "
            "survival) + (SR through balls 1..n / era SR through n) - 2. Top 5 "
            "per index, sorted by score then name; a band+index with fewer "
            "than five qualifiers ships a shorter list (empty if none clear "
            "the 300-ball floor)."
        ),
    }


def sixes_section(seasons) -> dict:
    rows = {"ipl": [], "wpl": []}
    for (league, season), ss in sorted(seasons.items()):
        total = sum(ss.batter_sixes.values())
        qualified = {
            b for b, n in ss.batter_balls.items() if n >= SIX_QUALIFIER_BALLS
        }
        qual_sixes = sum(v for b, v in ss.batter_sixes.items() if b in qualified)
        top10 = sum(
            v
            for _b, v in Counter(
                {b: v for b, v in ss.batter_sixes.items() if b in qualified}
            ).most_common(10)
        )
        rows[league].append(
            {
                "season": season,
                "sixes": total,
                # legal balls (wides AND no-balls excluded) so the on-screen
                # "a six every 21 balls -> every 12" figure traces to an
                # artifact instead of being hardcoded (finding #12/#17c).
                "legal_balls": ss.legal_balls,
                "balls_per_six": round(ss.legal_balls / total, 1) if total else None,
                "players_10plus_sixes": sum(
                    1 for v in ss.batter_sixes.values() if v >= 10
                ),
                "top10_share_pct": r1(100.0 * top10 / qual_sixes) if qual_sixes else None,
            }
        )
    return {
        "seasons": rows,
        "definition": (
            "Sixes = runs.batter == 6. Top-10 share = the top ten hitters' "
            "sixes as a share of all sixes by qualifying batters (>= 30 "
            "balls faced that season) — the concentration universe the "
            "catalog's Gini uses. balls_per_six = legal balls (wides AND "
            "no-balls excluded) / sixes: IPL 2008 = 20.8, 2026 = 11.7 (the "
            "caption's rounded 'every 21 -> every 12'). Column heights are "
            "raw six counts; balls_per_six is the denominator-honest rate "
            "because seasons grew (more matches, more balls)."
        ),
    }


def aerial_section(bands) -> dict:
    rows = {}
    for key, bs in bands.items():
        attempts = bs.aerial_sixes + bs.aerial_caught
        rows[key] = {
            "attempts_per_100_balls": r1(100.0 * attempts / bs.aerial_balls),
            "execution_pct": r1(100.0 * bs.aerial_sixes / attempts),
            "balls": bs.aerial_balls,
            "sixes": bs.aerial_sixes,
            "caught_excl_cb": bs.aerial_caught,
        }
    return {"bands": rows, "caveat": AERIAL_CAVEAT}


def wpl_beat_section(bands, seasons) -> dict:
    def first10_sr(league, season):
        ss = seasons[(league, season)]
        return r1(100.0 * ss.first10_runs / ss.first10_balls)

    def rr(league, season):
        ss = seasons[(league, season)]
        return round(6.0 * ss.runs_total / ss.legal_balls, 2)

    def runs_share(keys, field):
        tot = sum(getattr(seasons[k], "runs_total") for k in keys)
        part = sum(getattr(seasons[k], field) for k in keys)
        return r1(100.0 * part / tot)

    wpl_keys = [("wpl", s) for s in canon.WPL_SEASONS]
    ipl_modern = [("ipl", s) for s in range(2023, 2027)]
    wpl_band = bands["wpl " + WPL_BAND[1]]
    ipl_early_band = bands["ipl 2008-2010"]
    return {
        "first10_sr": {
            "wpl_2023_2026": r1(
                100.0
                * sum(seasons[k].first10_runs for k in wpl_keys)
                / wpl_band.first10_balls
            ),
            "ipl_2008_2010": r1(
                100.0
                * sum(
                    seasons[("ipl", s)].first10_runs for s in range(2008, 2011)
                )
                / ipl_early_band.first10_balls
            ),
        },
        "runs_from_fours_pct": {
            "wpl_2023_2026": runs_share(wpl_keys, "four_runs"),
            "ipl_2023_2026": runs_share(ipl_modern, "four_runs"),
        },
        "runs_from_sixes_pct": {
            "wpl_2023_2026": runs_share(wpl_keys, "six_runs"),
            "ipl_2023_2026": runs_share(ipl_modern, "six_runs"),
        },
        "maturity_clock": {
            "league_years": [1, 2, 3, 4],
            "rr": {
                "ipl": [rr("ipl", s) for s in range(2008, 2012)],
                "wpl": [rr("wpl", s) for s in canon.WPL_SEASONS],
            },
            "first10_sr": {
                "ipl": [first10_sr("ipl", s) for s in range(2008, 2012)],
                "wpl": [first10_sr("wpl", s) for s in canon.WPL_SEASONS],
            },
            "definition": (
                "League year N = the league's N-th season (IPL year 1 = "
                "2008, WPL year 1 = 2023). RR = all runs (extras included) "
                "per 6 legal balls (wides and no-balls excluded from the "
                "denominator)."
            ),
        },
    }


def ball_index_axis() -> dict:
    """The shared balls-faced x-axis convention for the ignition/out-rate/SR
    curves — so scenes label the right edge honestly (finding #4/#13).

    The per-ball curves (ignition sr_by_ball_index, outrate
    hazard_pct_by_ball_index, and the WPL SR curves) run over the batter's
    EXACT n-th ball faced, n = 1..30. The final index (30) is exactly ball 30
    — it is NOT a capped "30+" aggregate: capping the discrete hazard at 30
    would fold the whole survival tail into one point and spike it, so these
    curves stop at ball 30 by design. The ignition WALL (ballsfaced.u8, in
    shader) is the surface that caps: it clamps balls-faced >= 30 into a
    single right-edge column labeled "30+". Scenes should therefore label the
    per-ball charts' right edge "30" (the shared "1-30" span still matches the
    wall visually); only the wall's clamped column is a genuine "30+" bucket.
    """
    return {
        "min": 1,
        "max": MAX_BALL_INDEX,
        "max_is_capped": False,
        "max_label": str(MAX_BALL_INDEX),
        "wall_capped_index": MAX_BALL_INDEX,
        "wall_capped_label": f"{MAX_BALL_INDEX}+",
        "note": (
            f"Per-ball curves run over the batter's exact n-th ball faced, "
            f"n = 1..{MAX_BALL_INDEX}; index {MAX_BALL_INDEX} is exactly ball "
            f"{MAX_BALL_INDEX}, NOT a capped {MAX_BALL_INDEX}+ aggregate "
            f"(capping the discrete hazard there would spike it). The ignition "
            f"wall (ballsfaced.u8) is the only surface that caps: it clamps "
            f"balls-faced >= {MAX_BALL_INDEX} into one '{MAX_BALL_INDEX}+' "
            f"column. Label the per-ball charts' right edge "
            f"'{MAX_BALL_INDEX}', the wall's right column '{MAX_BALL_INDEX}+'."
        ),
    }


# ---------------------------------------------------------------------------
# R1b — the minimal sandbox descriptor (scenes/sandbox.json)
# ---------------------------------------------------------------------------

# The tap-a-ball tooltip's field roster: what a tapped point resolves to, and
# where each field comes from. Emitted into sandbox.json so the contract is a
# build artifact (tested) rather than prose. columnar[i] = the tapped point.
TOOLTIP_FIELDS = [
    {"field": "batter", "source": "columnar.dicts.batter[arrays.batter[i]]"},
    {"field": "bowler", "source": "columnar.dicts.bowler[arrays.bowler[i]]"},
    {"field": "batting_team", "source": "columnar.dicts.batting_team[arrays.batting_team[i]]"},
    {"field": "opponent", "source": "the team in matches[arrays.match_index[i]].teams that is not batting_team"},
    {"field": "match_label", "source": "matches[arrays.match_index[i]]: season + stage + date"},
    {"field": "venue", "source": "matches[arrays.match_index[i]].venue"},
    {"field": "city", "source": "matches[arrays.match_index[i]].city"},
    {"field": "over_ball", "source": "f'{arrays.over[i] + 1}.{arrays.ball_index_in_over[i] + 1}' (over/ball are 0-based)"},
    {"field": "innings", "source": "arrays.innings[i]"},
    {"field": "runs_off_bat", "source": "arrays.runs_batter[i]"},
    {"field": "runs_total", "source": "arrays.runs_total[i]"},
    {"field": "wicket", "source": "arrays.wicket[i] (1 = a dismissal fell)"},
    {"field": "wicket_kind", "source": "columnar.dicts.wicket_kind[arrays.wicket_kind[i]] ('' when no wicket)"},
    {"field": "result_text", "source": "matches[arrays.match_index[i]].result_text"},
]

# The famous-match preset (RESOLVED owner decision, blueprint §7 #1): the 2019
# IPL Final, Mumbai Indians beat Chennai Super Kings by 1 run — Malinga's final
# over. Resolved robustly by (league, season, stage, teams) with a margin
# cross-check, never by a hard-coded match_index.
# NOTE: these two strings are kept in sync with the committed, voice-guide
# rewrite of scenes/sandbox.json (commit 0303051 "Rewrite all user-facing copy
# to the voice guide"). That commit edited the emitted JSON directly without
# updating this source, so a plain rebuild reverted it; syncing the source here
# restores byte-identity AND removes the em dashes the voice guide forbids.
PRESET_LABEL = (
    "2019 IPL Final: Mumbai Indians beat Chennai Super Kings by 1 run"
)
PRESET_BLURB = (
    "Chennai need nine off Lasith Malinga's final over. Mumbai hold on to win "
    "by a single run, the closest final in IPL history."
)
PRESET_TEAMS = frozenset({"Mumbai Indians", "Chennai Super Kings"})


def resolve_preset(matches: list) -> int:
    """The 2019 IPL-Final match_index, resolved by identity not by number."""
    hits = [
        i
        for i, m in enumerate(matches)
        if m["league"] == "ipl"
        and m["season"] == 2019
        and m["stage"] == "Final"
        and set(m["teams"]) == PRESET_TEAMS
    ]
    if len(hits) != 1:
        raise SystemExit(f"preset match not uniquely resolved: {hits}")
    idx = hits[0]
    result = matches[idx]["result_text"]
    if result != "Mumbai Indians won by 1 run":  # season+stage+teams+MARGIN
        raise SystemExit(f"preset margin mismatch: {result!r}")
    return idx


# ---------------------------------------------------------------------------
# R6b — the guided-tour flag rail (scenes/sandbox.json tourFlags)
# ---------------------------------------------------------------------------
#
# The ~10 one-tap curated views that onboard a reader who does not yet know
# what to filter (r6b spec §4/§12). Each flag is resolved and VALIDATED against
# the real flattened deliveries at build time so a flag can never point at
# nothing: the pipeline recounts every flag's ball set in one corpus pass,
# fails loudly (SystemExit) on a zero-ball flag, and asserts the recount equals
# the digest-verified count exactly (artifact wins — the emitted `count` is the
# recount, and the client's live buildFacetMask().count must reproduce it).
#
# The FACET VOCABULARY the client resolves into a mask (all keys AND-combine;
# only the constraining keys are present on a given flag):
#   league   "ipl" | "wpl"                (columnar arrays.league: ipl=0 wpl=1)
#   season   int   exact season           seasons [int] season-in-set
#   overLo   int   over >= overLo         overHi int over <= overHi  (0-based)
#   outcomes [int] off-the-bat outcome codes, OR-ed within the list
#   wicket   1     AND: a wicket fell on the ball (arrays.wicket == 1)
#   innings  int   1 | 2                  batter/bowler  player NAME string
#   matchSet [int] match_index in this set (two-hundred-club: the 228 matches)
#   mode     "hide"  render mode override (the match-preset flag only; the rest
#                    default to dim so the haze always survives)
# OUTCOME CODES (mirror flatten.outcome_class / arrays.outcome): dot 0,
# single 1, two_or_three 2, four 3, six 4, extras 5. The digest's trap: six=4,
# four=3. WICKET is an INDEPENDENT 0/1 flag (co-occurs with any outcome).
# batter/bowler are emitted BY NAME; the client resolves name -> col.dicts
# index (the raw delivery names are exactly the DictEncoder entries).
#
# final-2019 is the match-preset flag: it carries `match_index` (resolved by
# identity via resolve_preset, never a hard-coded number) and renders hide-mode.
# two-hundred-club is a computed-predicate flag: the pipeline precomputes the
# 228-match "first-innings total >= 200" set and emits it as facets.matchSet,
# which the client expands to a point mask (innings 1 AND match_index in set).

TWO_HUNDRED_CLUB_MIN = 200  # first-innings total (sum runs.total) that qualifies

# Rail order (§12): the human hooks (a famous final, a duel, a record season)
# lead, then the aggregate-pattern flags. `_expected` is the digest-verified
# count the build re-derives and asserts (§13). `_kind`: "match" resolves a
# match_index by identity; "club" is the computed 200-club predicate; the rest
# are pure per-column facet predicates. facets hold ONLY the emitted keys;
# match_index / matchSet are injected at resolve time from real data.
TOUR_FLAGS = [
    {
        "id": "final-2019",
        "label": "The 2019 Final, ball by ball",
        "blurb": (
            "Nine off Malinga's last over, and Mumbai win by one run. All 247 "
            "balls of the closest final there's been."
        ),
        "facets": {"mode": "hide"},
        "_kind": "match",
        "_expected": 247,
    },
    {
        "id": "bumrah-rahul",
        "label": "Bumrah's longest duel",
        "blurb": (
            "123 balls of India's deadliest yorker at its coolest head. "
            "Bumrah's most-bowled duel with anyone."
        ),
        "facets": {"bowler": "JJ Bumrah", "batter": "KL Rahul"},
        "_kind": "facet",
        "_expected": 123,
    },
    {
        "id": "kohli-2016",
        "label": "Kohli's record 2016",
        "blurb": (
            "The best single season the IPL has seen. All 655 balls Kohli "
            "faced in 2016, the summer he made 973."
        ),
        "facets": {"batter": "V Kohli", "season": 2016},
        "_kind": "facet",
        "_expected": 655,
    },
    {
        "id": "wpl-all-sixes",
        "label": "Every six in WPL history",
        "blurb": "Every maximum in the WPL, from the very first swing to now. 705 of them.",
        "facets": {"league": "wpl", "outcomes": [4]},  # 4 = six (four=3, six=4)
        "_kind": "facet",
        "_expected": 705,
    },
    {
        "id": "two-hundred-club",
        "label": "The 200 Club",
        "blurb": (
            "228 times a side has posted 200 batting first. Here's all 28,704 "
            "balls of it, up to the record 287."
        ),
        "facets": {"innings": 1},  # matchSet injected from the computed 228-set
        "_kind": "club",
        "_expected": 28704,
    },
    {
        "id": "wickets-2022",
        "label": "Every wicket of IPL 2022",
        "blurb": (
            "The first season after the mega-auction reshuffle. All 912 "
            "wickets that fell across IPL 2022."
        ),
        "facets": {"league": "ipl", "season": 2022, "wicket": 1},
        "_kind": "facet",
        "_expected": 912,
    },
    {
        "id": "death-carnage-2023",
        "label": "Death-overs carnage, 2023 to now",
        "blurb": (
            "Overs 16 to 20 in the Impact Player era. 4,470 fours and sixes "
            "launched at the death since 2023."
        ),
        "facets": {"overLo": 15, "seasons": [2023, 2024, 2025, 2026], "outcomes": [3, 4]},
        "_kind": "facet",
        "_expected": 4470,
    },
    {
        "id": "powerplay-six-explosion",
        "label": "The powerplay six explosion",
        "blurb": (
            "3,920 sixes in the first six overs, and the modern game nearly "
            "doubled the rate, from 1,106 back then to 1,934 now."
        ),
        "facets": {"overHi": 5, "outcomes": [4]},
        "_kind": "facet",
        "_expected": 3920,
    },
    {
        "id": "death-dot-storm",
        "label": "The death-overs dot storm",
        "blurb": (
            "When the bowlers slam the door. 19,414 dot balls squeezed out in "
            "the last five overs."
        ),
        "facets": {"overLo": 15, "outcomes": [0]},
        "_kind": "facet",
        "_expected": 19414,
    },
    {
        "id": "shafali-wpl",
        "label": "Shafali Verma in the WPL",
        "blurb": (
            "The WPL's biggest hitter, in full. All 778 balls Shafali Verma "
            "has faced, 53 of them sixes."
        ),
        "facets": {"batter": "Shafali Verma", "league": "wpl"},
        "_kind": "facet",
        "_expected": 778,
    },
]


def _flag_pass(facets: dict, rec: dict) -> bool:
    """Does one delivery `rec` satisfy a flag's per-column facet predicate?

    The build-time mirror of the client's buildFacetMask membership test:
    every present constraining key AND-combines; unknown keys (mode) and
    match-level keys (matchSet, handled separately for the 200 club) are
    ignored here.
    """
    if "league" in facets and rec["league"] != facets["league"]:
        return False
    if "season" in facets and rec["season"] != facets["season"]:
        return False
    if "seasons" in facets and rec["season"] not in facets["seasons"]:
        return False
    if "overLo" in facets and rec["over"] < facets["overLo"]:
        return False
    if "overHi" in facets and rec["over"] > facets["overHi"]:
        return False
    if "outcomes" in facets and rec["outcome"] not in facets["outcomes"]:
        return False
    if "wicket" in facets and rec["wicket"] != facets["wicket"]:
        return False
    if "innings" in facets and rec["innings"] != facets["innings"]:
        return False
    if "batter" in facets and rec["batter"] != facets["batter"]:
        return False
    if "bowler" in facets and rec["bowler"] != facets["bowler"]:
        return False
    return True


def resolve_tour_flags(matches: list, preset_index: int | None = None) -> list:
    """The ~10 tour flags, each resolved + validated against real deliveries.

    ONE chronological corpus pass (super overs excluded, the standing rule):
    counts every pure-facet flag's ball set, the 2019-final match's ball set,
    and the per-match first-innings totals + ball counts needed for the 200
    club. Then: resolves final-2019's match_index by identity (resolve_preset,
    with its SystemExit guards); builds the 228-match >=200 first-innings set;
    asserts every flag returns >= 1 ball (loud SystemExit on 0) and that the
    recount equals the digest-verified count exactly. Returns the emitted flag
    dicts in rail order: {id, label, blurb, facets, count, match_index?}.
    """
    if preset_index is None:
        preset_index = resolve_preset(matches)

    counts = {f["id"]: 0 for f in TOUR_FLAGS}
    facet_flags = [f for f in TOUR_FLAGS if f["_kind"] == "facet"]
    first_inn_total: dict[int, int] = {}
    first_inn_balls: dict[int, int] = {}

    for match_index, (_date, _mid, league, path) in enumerate(
        flatten.sorted_match_files()
    ):
        with open(path) as fh:
            match = json.load(fh)
        season = canon.canon_season(match["info"])
        innings_no = 0
        for innings in match.get("innings", []):
            if canon.is_super_over(innings):
                continue  # standing rule: super overs never enter the stream
            innings_no += 1
            for over in innings["overs"]:
                over_no = over["over"]
                for dl in over["deliveries"]:
                    rec = {
                        "league": league,
                        "season": season,
                        "over": over_no,
                        "outcome": flatten.outcome_class(dl),
                        "wicket": 1 if dl.get("wickets") else 0,
                        "innings": innings_no,
                        "batter": dl["batter"],
                        "bowler": dl["bowler"],
                    }
                    if match_index == preset_index:
                        counts["final-2019"] += 1
                    for f in facet_flags:
                        if _flag_pass(f["facets"], rec):
                            counts[f["id"]] += 1
                    if innings_no == 1:
                        first_inn_total[match_index] = (
                            first_inn_total.get(match_index, 0) + dl["runs"]["total"]
                        )
                        first_inn_balls[match_index] = (
                            first_inn_balls.get(match_index, 0) + 1
                        )

    club = sorted(
        mi for mi, total in first_inn_total.items() if total >= TWO_HUNDRED_CLUB_MIN
    )
    counts["two-hundred-club"] = sum(first_inn_balls[mi] for mi in club)

    resolved = []
    for f in TOUR_FLAGS:
        got = counts[f["id"]]
        if got < 1:  # a flag must never point at nothing (invariant 9)
            raise SystemExit(f"tour flag {f['id']!r} resolved to 0 balls")
        if got != f["_expected"]:  # artifact-vs-digest guard (tolerance 0)
            raise SystemExit(
                f"tour flag {f['id']!r} count {got} != digest {f['_expected']}"
            )
        facets = dict(f["facets"])
        entry = {"id": f["id"], "label": f["label"], "blurb": f["blurb"], "count": got}
        if f["_kind"] == "match":
            entry["match_index"] = preset_index
        elif f["_kind"] == "club":
            facets["matchSet"] = club  # the 228 qualifying match indices
        entry["facets"] = facets
        resolved.append(entry)
    return resolved


def sandbox_doc() -> dict:
    matches = flatten.build_matches()
    preset_index = resolve_preset(matches)
    tour_flags = resolve_tour_flags(matches, preset_index)
    teams = [
        {"id": t["id"], "short": t["short"], "name": t["name"], "league": t["league"]}
        for t in canon.TEAMS
    ]
    return {
        "preset": {
            "match_index": preset_index,
            "label": PRESET_LABEL,
            "blurb": PRESET_BLURB,
        },
        "tourFlags": tour_flags,
        "facets": {
            "team": {
                "source": "teams.json",
                "opens_prefiltered_to": (
                    "the reader's picked franchise id (team.u8, indexes "
                    "teams.json) — the sandbox is never blank"
                ),
                "options": teams,
            },
            "season": {
                "source": "groups.json",
                "ipl": list(canon.IPL_SEASONS),
                "wpl": list(canon.WPL_SEASONS),
            },
        },
        "tooltip": {
            "resolves_via": "matches.json (match_index) + columnar.json.gz arrays/dicts",
            "fields": TOOLTIP_FIELDS,
        },
        "scope": (
            "R6b full bowl: the field becomes a filterable instrument. The "
            "full facet grammar (league, team, season, phase, over-range, "
            "outcome, the wicket AND-toggle, batter, bowler, all combinable), "
            "the ten-flag guided-tour rail (tourFlags, each resolved and "
            "validated against real deliveries so a flag never points at "
            "nothing), the tap-a-ball tooltip, and shareable URLs. The team + "
            "season facets and the 2019-final preset carry over from the R1b "
            "minimal bowl unchanged; the linked worm/Manhattan breakdown panel "
            "is the remaining R6b UI surface (blueprint §3, r6b spec §5)."
        ),
    }


def ch1_doc(bands, seasons) -> dict:
    return {
        "era_bands": band_meta(),
        "ball_index_axis": ball_index_axis(),
        "ignition": ignition_section(bands, seasons),
        "outrate": outrate_section(bands),
        "defiers": defiers_section(bands),
        "sixes": sixes_section(seasons),
        "aerial": aerial_section(bands),
        "wpl_beat": wpl_beat_section(bands, seasons),
    }


# ---------------------------------------------------------------------------
# R2a — Chapter 2 "The Last of the Anchors" (scenes/ch2.json)
# ---------------------------------------------------------------------------
#
# One extra chronological corpus pass (super overs excluded) computing every
# number the elegy puts on screen. BALL-FACED CONVENTION (Ch 2-specific): a
# ball faced == a legal delivery — wides AND no-balls are both excluded (a
# scorecard strike rate). This differs deliberately from Ch 1's ballsfaced.u8,
# which counts no-balls; the legal-ball denominator is exactly what reconciles
# the catalog's archetype (249 qualifiers, WPL 19.8%) and anchor (8.5%) teasers.
# Recipes follow research/metrics-catalog.md and
# reconcile with its verified teasers; the reconciliation is asserted by
# tests/test_r2a.py against an independent recount:
#
#   (a) anchor extinction  anchor-ball share/season, players with >=5 anchor
#                          innings, and the anchor "penalty" win-rate (teams
#                          with vs without a top-4 anchor innings)
#   (b) run-out extinction run-outs as % of dismissals/season (IPL + WPL),
#                          striker/non-striker split, + Break-Even Running
#                          (run-outs per 1,000 legal balls; twos rate) footnote
#   (c) archetype occ.     sub-120-SR batter-season share/season (>=100-ball
#                          batter-seasons; catalog 38.7% -> 2.4%, WPL 19.8%)
#   (d) gear-shift         two-act innings share (2nd-half SR >= 1.5x 1st-half,
#                          >=25-ball innings; 33.5% -> 24.5%) + a thirds shape
#                          mix (three-act / flat-max) companion lens
#   (e) new-batter tax     post-wicket per-over deficit vs team phase-par over
#                          the next 10 legal balls, per era, + incoming-batter
#                          (position >=3) first-5-ball SR per era
#   (f) worm exemplars     K IPL seasons x a handful of real anchor innings as
#                          ball-by-ball cumulative-runs worms + the season par
#                          worm (mean cumulative runs by ball faced)
#   (g) WPL beat           anchor-ball share (~9%, dialect clock) paired with
#                          run-out share (~7%, timeline clock) — two clocks
#   (h) team payoff        each franchise's LAST qualifying anchor innings
#                          (batter, season, balls, SR, boundary%, par) + the
#                          designed empty state for born-post-anchor sides
#
# PAR MODEL (engine #1 stand-in): the anchor SR threshold and the new-batter
# tax both need a season x phase par baseline. Engine #1's table is built in a
# parallel R2 track and not consumed here yet, so this module computes a LOCAL
# phase-par with the SAME definition the catalog anchor recipe assumes:
#   par_bat_rpb[(league, season, phase)]  = sum(batter runs) / sum(balls faced)
#   par_team_rpb[(league, season, phase)] = sum(total runs)  / sum(legal balls)
# priced per league (each league against its own baseline — the house rule).
# INTEGRATION: when engine #1 lands, replace _par_bat_rpb / _par_team_rpb with
# its (league, season, phase) lookup; the anchor / tax definitions are unchanged
# (see ch2_doc["par_model"]["integration_note"]).

PHASE_LABELS = ("powerplay", "middle", "death")  # overs 1-6 / 7-15 / 16-20
ANCHOR_MIN_BALLS = 15
ANCHOR_SR_FACTOR = 0.85
ANCHOR_BOUNDARY_MAX = 0.12  # boundary ball = runs.batter >= 4
ANCHOR_PROLIFIC_MIN = 5  # players with >= this many anchor innings / season
ARCHETYPE_MIN_BALLS = 100  # batter-season qualifying floor (catalog: 150/249/81)
ARCHETYPE_SR_CEIL = 120.0
GEAR_MIN_BALLS = 25
GEAR_TWO_ACT_FACTOR = 1.5  # 2nd-half SR >= 1.5x 1st-half -> two-act
GEAR_THREE_ACT_FACTOR = 1.5  # 3rd-third SR >= 1.5x 1st-third, monotone -> three-act
GEAR_FLAT_TOL = 1.25  # max third SR <= 1.25x min third SR -> flat-max (one gear)
TAX_WINDOW = 10  # legal balls after a dismissal (full window only — trims innings end)
INCOMING_MIN_POS = 3  # a batter who entered after a wicket (not an opener)
INCOMING_FIRST_N = 5  # incoming batter's first-5-ball SR
WORM_SEASONS = (2010, 2014, 2018, 2022, 2026)  # IPL exemplar seasons (K = 5)
WORM_EXEMPLARS_PER_SEASON = 4
WORM_MAX_BALLS = 80  # longest anchor worm emitted (no T20 innings faces more)


def r2(x):
    return round(x, 2)


def phase_of(over_index: int) -> int:
    if over_index < 6:
        return 0
    if over_index < 15:
        return 1
    return 2


def build_ch2(data_root: Path = canon.DATA_ROOT) -> dict:
    """The one authoritative corpus pass for Chapter 2 (separate from the Ch 1
    build() so R1 scene bytes stay byte-identical)."""
    par_bat_runs = defaultdict(int)  # (lg, ss, phase) -> batter runs
    par_bat_balls = defaultdict(int)  # -> balls faced (non-wide)
    par_team_runs = defaultdict(int)  # (lg, ss, phase) -> total runs on legal balls
    par_team_balls = defaultdict(int)  # -> legal balls
    faced_runs = defaultdict(lambda: defaultdict(int))  # (lg, ss) -> {n: runs}
    faced_count = defaultdict(lambda: defaultdict(int))  # (lg, ss) -> {n: count}
    bseason = defaultdict(lambda: [0, 0])  # (lg, ss, batter) -> [balls, runs]
    innings_recs = []
    teaminn = {}  # (match_index, innings_no) -> team-innings record
    tax_windows = []  # (lg, ss, [(phase, total) * 10])
    incoming = defaultdict(lambda: [0, 0])  # band_key -> [balls, runs]
    dis_total = defaultdict(int)  # (lg, ss) -> non-retired dismissals
    runout_total = defaultdict(int)  # (lg, ss) -> run outs
    runout_striker = defaultdict(int)  # band_key -> striker run outs
    runout_nonstriker = defaultdict(int)  # band_key -> non-striker run outs
    band_legal = defaultdict(int)  # band_key -> legal balls (break-even)
    band_runouts = defaultdict(int)  # band_key -> run outs
    band_twos = defaultdict(int)  # band_key -> balls off which the batter ran 2
    band_nonboundary = defaultdict(int)  # band_key -> faced balls with runs.batter < 4
    matches = []

    for match_index, (_date, _mid, league, path) in enumerate(
        flatten.sorted_match_files(data_root)
    ):
        with open(path) as fh:
            match = json.load(fh)
        info = match["info"]
        season = canon.canon_season(info)
        matches.append(flatten.match_record(info, league))
        winner = info.get("outcome", {}).get("winner")
        winner = canon.canon_team(winner) if winner else None
        bk = band_key(league, season)

        innings_no = 0
        for innings in match.get("innings", []):
            if canon.is_super_over(innings):
                continue
            innings_no += 1
            team = canon.canon_team(innings["team"])
            teaminn[(match_index, innings_no)] = {
                "league": league,
                "season": season,
                "team": team,
                "won": None if winner is None else (winner == team),
                "has_top4_anchor": False,
            }
            faced_seq = defaultdict(list)  # batter -> [runs.batter, ...]
            phase_counts = defaultdict(lambda: [0, 0, 0])  # batter -> faced per phase
            boundary_balls = defaultdict(int)  # batter -> boundary balls faced
            position = {}
            next_pos = 1
            legal_seq = []  # (phase, total) per legal ball, innings order
            dismissal_L = []  # legal-ball count already elapsed at each dismissal
            cum_legal = 0
            for over in innings["overs"]:
                ph = phase_of(over["over"])
                for dl in over["deliveries"]:
                    extras = dl.get("extras", {})
                    wide = "wides" in extras
                    noball = "noballs" in extras
                    total = dl["runs"]["total"]
                    rb = dl["runs"]["batter"]
                    striker = dl["batter"]
                    nonst = dl["non_striker"]
                    if striker not in position:
                        position[striker] = next_pos
                        next_pos += 1
                    if nonst not in position:
                        position[nonst] = next_pos
                        next_pos += 1
                    # Ch 2 convention: a ball faced == a legal delivery (wides
                    # AND no-balls excluded — a scorecard strike rate). This
                    # differs deliberately from Ch 1's ballsfaced.u8 (which
                    # counts no-balls); the legal-ball denominator is what
                    # reconciles the catalog's archetype (249 qualifiers, WPL
                    # 19.8%) and anchor (8.5%) teasers exactly. See ch2_doc
                    # par_model / archetype definitions.
                    if not wide and not noball:  # a legal delivery == a ball faced
                        legal_seq.append((ph, total))
                        cum_legal += 1
                        par_team_runs[(league, season, ph)] += total
                        par_team_balls[(league, season, ph)] += 1
                        band_legal[bk] += 1
                        faced_seq[striker].append(rb)
                        phase_counts[striker][ph] += 1
                        if rb >= 4:
                            boundary_balls[striker] += 1
                        else:
                            band_nonboundary[bk] += 1
                            if rb == 2:
                                band_twos[bk] += 1
                        n = len(faced_seq[striker])
                        par_bat_runs[(league, season, ph)] += rb
                        par_bat_balls[(league, season, ph)] += 1
                        faced_runs[(league, season)][n] += rb
                        faced_count[(league, season)][n] += 1
                    for w in dl.get("wickets", []):
                        if w["kind"] in RETIRED_KINDS:
                            continue  # censored, not a dismissal
                        dismissal_L.append(cum_legal)
                        dis_total[(league, season)] += 1
                        if w["kind"] == "run out":
                            runout_total[(league, season)] += 1
                            band_runouts[bk] += 1
                            if w.get("player_out") == striker:
                                runout_striker[bk] += 1
                            else:
                                runout_nonstriker[bk] += 1
            for batter, seq in faced_seq.items():
                balls = len(seq)
                runs = sum(seq)
                bseason[(league, season, batter)][0] += balls
                bseason[(league, season, batter)][1] += runs
                innings_recs.append(
                    {
                        "league": league,
                        "season": season,
                        "batter": batter,
                        "team": team,
                        "match_index": match_index,
                        "innings_key": (match_index, innings_no),
                        "balls": balls,
                        "runs": runs,
                        "boundary": boundary_balls[batter],
                        "phase_counts": list(phase_counts[batter]),
                        "position": position[batter],
                        "seq": seq,
                    }
                )
                if position[batter] >= INCOMING_MIN_POS:
                    first = seq[:INCOMING_FIRST_N]
                    incoming[bk][0] += len(first)
                    incoming[bk][1] += sum(first)
            for L in dismissal_L:  # full 10-legal-ball windows only (trims innings end)
                if len(legal_seq) - L >= TAX_WINDOW:
                    tax_windows.append((league, season, legal_seq[L : L + TAX_WINDOW]))

    return {
        "par_bat_runs": par_bat_runs,
        "par_bat_balls": par_bat_balls,
        "par_team_runs": par_team_runs,
        "par_team_balls": par_team_balls,
        "faced_runs": faced_runs,
        "faced_count": faced_count,
        "bseason": bseason,
        "innings_recs": innings_recs,
        "teaminn": teaminn,
        "tax_windows": tax_windows,
        "incoming": incoming,
        "dis_total": dis_total,
        "runout_total": runout_total,
        "runout_striker": runout_striker,
        "runout_nonstriker": runout_nonstriker,
        "band_legal": band_legal,
        "band_runouts": band_runouts,
        "band_twos": band_twos,
        "band_nonboundary": band_nonboundary,
        "matches": matches,
    }


def _par_bat_rpb(acc, key):
    b = acc["par_bat_balls"][key]
    return acc["par_bat_runs"][key] / b if b else 0.0


def _par_team_rpb(acc, key):
    b = acc["par_team_balls"][key]
    return acc["par_team_runs"][key] / b if b else 0.0


def classify_anchors(acc) -> list:
    """Mark each batter-innings with sr / par_sr / is_anchor and flag the
    team-innings that carried a top-4 anchor. Mutates acc in place."""
    for r in acc["innings_recs"]:
        lg, ss, balls = r["league"], r["season"], r["balls"]
        exp = sum(
            _par_bat_rpb(acc, (lg, ss, ph)) * r["phase_counts"][ph] for ph in range(3)
        )
        par_rpb = exp / balls if balls else 0.0
        r["par_sr"] = 100.0 * par_rpb
        r["sr"] = 100.0 * r["runs"] / balls if balls else 0.0
        r["is_anchor"] = bool(
            balls >= ANCHOR_MIN_BALLS
            and par_rpb > 0
            and (r["runs"] / balls) < ANCHOR_SR_FACTOR * par_rpb
            and (r["boundary"] / balls) < ANCHOR_BOUNDARY_MAX
        )
        if r["is_anchor"] and r["position"] <= 4:
            acc["teaminn"][r["innings_key"]]["has_top4_anchor"] = True
    return acc["innings_recs"]


SEASON_KEYS = [("ipl", s) for s in canon.IPL_SEASONS] + [
    ("wpl", s) for s in canon.WPL_SEASONS
]


def anchor_section(acc) -> dict:
    recs = acc["innings_recs"]
    all_balls = defaultdict(int)
    anchor_balls = defaultdict(int)
    anchor_innings = defaultdict(int)  # (lg, ss, batter) -> anchor innings
    band_all = defaultdict(int)
    band_anchor = defaultdict(int)
    for r in recs:
        key = (r["league"], r["season"])
        bk = band_key(*key)
        all_balls[key] += r["balls"]
        band_all[bk] += r["balls"]
        if r["is_anchor"]:
            anchor_balls[key] += r["balls"]
            band_anchor[bk] += r["balls"]
            anchor_innings[(r["league"], r["season"], r["batter"])] += 1
    prolific = defaultdict(int)
    for (lg, ss, _b), c in anchor_innings.items():
        if c >= ANCHOR_PROLIFIC_MIN:
            prolific[(lg, ss)] += 1
    seasons = {"ipl": [], "wpl": []}
    for lg, ss in SEASON_KEYS:
        a, t = anchor_balls[(lg, ss)], all_balls[(lg, ss)]
        seasons[lg].append(
            {
                "season": ss,
                "anchor_ball_share_pct": r1(100.0 * a / t) if t else None,
                "anchor_balls": a,
                "total_balls": t,
                "prolific_players": prolific[(lg, ss)],
            }
        )
    bands = {
        bk: {
            "anchor_ball_share_pct": r1(100.0 * band_anchor[bk] / band_all[bk])
            if band_all[bk]
            else None,
            "anchor_balls": band_anchor[bk],
            "total_balls": band_all[bk],
        }
        for bk in BAND_KEYS
    }
    # Anchor "penalty": batting-team match win-rate with vs without a top-4
    # anchor innings (decided matches only — ties / no-results excluded).
    pen = defaultdict(lambda: {"with_w": 0, "with_n": 0, "wo_w": 0, "wo_n": 0})
    for ti in acc["teaminn"].values():
        if ti["won"] is None:
            continue
        d = pen[band_key(ti["league"], ti["season"])]
        pre = "with" if ti["has_top4_anchor"] else "wo"
        d[f"{pre}_n"] += 1
        if ti["won"]:
            d[f"{pre}_w"] += 1
    penalty = {}
    for bk in BAND_KEYS:
        d = pen[bk]
        penalty[bk] = {
            "with_anchor": {
                "win_pct": r1(100.0 * d["with_w"] / d["with_n"]) if d["with_n"] else None,
                "n": d["with_n"],
            },
            "without_anchor": {
                "win_pct": r1(100.0 * d["wo_w"] / d["wo_n"]) if d["wo_n"] else None,
                "n": d["wo_n"],
            },
        }
    return {
        "seasons": seasons,
        "bands": bands,
        "penalty": penalty,
        "definition": (
            "Anchor innings = balls faced >= 15, strike rate < 0.85 x the "
            "innings' phase-mix-weighted par SR (local season x phase par, "
            "each league against its own baseline), and boundary balls "
            "(runs.batter >= 4) < 12% of balls faced. anchor_ball_share_pct = "
            "balls consumed by anchor innings / all balls faced that season. "
            "prolific_players = batters with >= 5 anchor innings that season. "
            "penalty = the batting team's match win-rate (decided matches "
            "only) in team-innings that carried a top-4 (position 1-4) anchor "
            "innings vs those that did not."
        ),
    }


def runout_section(acc) -> dict:
    seasons = {"ipl": [], "wpl": []}
    for lg, ss in SEASON_KEYS:
        tot = acc["dis_total"][(lg, ss)]
        ro = acc["runout_total"][(lg, ss)]
        seasons[lg].append(
            {
                "season": ss,
                "runout_share_pct": r1(100.0 * ro / tot) if tot else None,
                "run_outs": ro,
                "dismissals": tot,
            }
        )
    striker_split = {}
    for bk in BAND_KEYS:
        s, n = acc["runout_striker"][bk], acc["runout_nonstriker"][bk]
        tot = s + n
        striker_split[bk] = {
            "striker": s,
            "non_striker": n,
            "non_striker_pct": r1(100.0 * n / tot) if tot else None,
        }
    # Break-Even Running (Ch 2 footnote): run-outs per 1,000 legal balls and
    # the twos rate held flat while running got safer.
    break_even = {}
    for bk in BAND_KEYS:
        legal = acc["band_legal"][bk]
        nonb = acc["band_nonboundary"][bk]
        break_even[bk] = {
            "runouts_per_1000_legal": r2(1000.0 * acc["band_runouts"][bk] / legal)
            if legal
            else None,
            "twos_per_100_nonboundary": r2(100.0 * acc["band_twos"][bk] / nonb)
            if nonb
            else None,
        }
    return {
        "seasons": seasons,
        "striker_split": striker_split,
        "break_even_running": break_even,
        "definition": (
            "runout_share_pct = wickets of kind 'run out' / all non-retired "
            "dismissals that season (retired hurt/out censored, never events). "
            "striker_split decomposes run-outs by which end was given out. "
            "break_even_running (footnote): runouts_per_1000_legal = run-outs "
            "per 1,000 legal balls; twos_per_100_nonboundary = balls the "
            "batter ran two off, per 100 faced balls that were not boundaries "
            "(runs.batter < 4) — running got safer at constant aggression."
        ),
    }


def archetype_section(acc) -> dict:
    per_season = defaultdict(lambda: [0, 0])  # (lg, ss) -> [qualifiers, sub120]
    band_q = defaultdict(int)
    band_u = defaultdict(int)
    for (lg, ss, _b), (balls, runs) in acc["bseason"].items():
        if balls < ARCHETYPE_MIN_BALLS:
            continue
        bk = band_key(lg, ss)
        per_season[(lg, ss)][0] += 1
        band_q[bk] += 1
        if (100.0 * runs / balls) < ARCHETYPE_SR_CEIL:
            per_season[(lg, ss)][1] += 1
            band_u[bk] += 1
    seasons = {"ipl": [], "wpl": []}
    for lg, ss in SEASON_KEYS:
        q, u = per_season[(lg, ss)]
        seasons[lg].append(
            {
                "season": ss,
                "qualifiers": q,
                "sub120": u,
                "sub120_share_pct": r1(100.0 * u / q) if q else None,
            }
        )
    bands = {
        bk: {
            "qualifiers": band_q[bk],
            "sub120": band_u[bk],
            "sub120_share_pct": r1(100.0 * band_u[bk] / band_q[bk]) if band_q[bk] else None,
        }
        for bk in BAND_KEYS
    }
    return {
        "seasons": seasons,
        "bands": bands,
        "definition": (
            "Ball-by-Ball DNA / archetype occupancy: among batter-seasons of "
            ">= 100 legal balls faced (wides and no-balls excluded), the share "
            "whose whole-season strike rate is under 120. Catalog: 38.7% (IPL "
            "2008-10) -> 2.4% (2023-26); WPL 19.8%. Qualifier counts reconcile "
            "the catalog's 150 / 249 / 81; the 2008-10 share lands at ~39% "
            "(one borderline batter-season off the catalog's 38.7% under the "
            "SR<120.0 cut)."
        ),
    }


def gearshift_section(acc) -> dict:
    band_tot = defaultdict(int)
    band_two = defaultdict(int)
    band_three = defaultdict(int)
    band_flat = defaultdict(int)
    per_season = defaultdict(lambda: [0, 0])  # (lg, ss) -> [total, two_act]
    for r in acc["innings_recs"]:
        n = r["balls"]
        if n < GEAR_MIN_BALLS:
            continue
        seq = r["seq"]
        bk = band_key(r["league"], r["season"])
        band_tot[bk] += 1
        per_season[(r["league"], r["season"])][0] += 1
        # Two-act (the reconciled headline): split by balls faced into halves.
        h = n // 2
        first, second = seq[:h], seq[h:]
        sr1 = sum(first) / len(first)
        sr2 = sum(second) / len(second)
        if sr1 > 0 and sr2 >= GEAR_TWO_ACT_FACTOR * sr1:
            band_two[bk] += 1
            per_season[(r["league"], r["season"])][1] += 1
        # Companion lens: a thirds shape taxonomy (see-off -> consolidate ->
        # launch = three-act; near-constant gear = flat-max).
        t = n // 3
        a, b, c = seq[:t], seq[t : 2 * t], seq[2 * t :]
        sa, sb, sc = sum(a) / len(a), sum(b) / len(b), sum(c) / len(c)
        if sa > 0 and sc >= GEAR_THREE_ACT_FACTOR * sa and sb >= sa and sc >= sb:
            band_three[bk] += 1
        lo = min(sa, sb, sc)
        hi = max(sa, sb, sc)
        if lo > 0 and hi <= GEAR_FLAT_TOL * lo:
            band_flat[bk] += 1
    seasons = {"ipl": [], "wpl": []}
    for lg, ss in SEASON_KEYS:
        tot, two = per_season[(lg, ss)]
        seasons[lg].append(
            {
                "season": ss,
                "innings": tot,
                "two_act": two,
                "two_act_share_pct": r1(100.0 * two / tot) if tot else None,
            }
        )
    bands = {}
    for bk in BAND_KEYS:
        tot = band_tot[bk]
        bands[bk] = {
            "innings": tot,
            "two_act_share_pct": r1(100.0 * band_two[bk] / tot) if tot else None,
            "three_act_share_pct": r1(100.0 * band_three[bk] / tot) if tot else None,
            "flat_max_share_pct": r1(100.0 * band_flat[bk] / tot) if tot else None,
        }
    return {
        "seasons": seasons,
        "bands": bands,
        "definition": (
            "Among innings of >= 25 balls faced. two_act (the reconciled "
            "headline): the batter's 2nd-half SR >= 1.5x the 1st-half SR, "
            "split by balls faced (catalog 33.5% -> 24.5%). Companion thirds "
            "lens: three_act = SR rising across thirds with the last third "
            ">= 1.5x the first (see-off -> consolidate -> launch); flat_max = "
            "the three thirds' SRs within 1.25x of each other (one gear held "
            "the whole way) — now the modal long innings."
        ),
    }


def newbatter_section(acc) -> dict:
    exp = defaultdict(float)
    act = defaultdict(float)
    balls = defaultdict(int)
    for lg, ss, window in acc["tax_windows"]:
        bk = band_key(lg, ss)
        for ph, total in window:
            act[bk] += total
            exp[bk] += _par_team_rpb(acc, (lg, ss, ph))
            balls[bk] += 1
    tax = {}
    for bk in BAND_KEYS:
        nb = balls[bk]
        if not nb:
            tax[bk] = {"tax_rpo_below_par": None, "window_balls": 0}
            continue
        tax[bk] = {
            "tax_rpo_below_par": r2(6.0 * (exp[bk] - act[bk]) / nb),
            "actual_rpo": r2(6.0 * act[bk] / nb),
            "par_rpo": r2(6.0 * exp[bk] / nb),
            "window_balls": nb,
        }
    incoming = {}
    for bk in BAND_KEYS:
        b, rn = acc["incoming"][bk]
        incoming[bk] = {"first5_sr": r1(100.0 * rn / b) if b else None, "balls": b}
    return {
        "tax": tax,
        "incoming_first5_sr": incoming,
        "definition": (
            "New-Batter Tax: over the 10 legal balls after each dismissal "
            "(full windows only — dismissals within 10 legal balls of the "
            "innings end are trimmed), the team's runs-per-over shortfall "
            "against its season x phase par (par_rpo - actual_rpo; positive = "
            "below par). incoming_first5_sr = strike rate on the first 5 legal "
            "balls faced by batters who entered at position >= 3 (i.e. after a "
            "wicket). Reconciliation: the STORY reproduces the catalog coda — "
            "the tax persists and slightly deepens (here ~1.1 -> ~1.3 RPO "
            "below par) while incoming first-5 SR jumps ~25% (here ~95 -> "
            "~119); the tax is structural, not behavioural. The absolute tax "
            "magnitude tracks the par baseline: the catalog's 1.22 -> 1.40 "
            "used a wickets-in-hand-conditioned par (engine #1), so the exact "
            "level converges when engine #1's table replaces this season x "
            "phase stand-in (par_model.integration_note). The catalog's 101 -> "
            "127 incoming SR uses a slightly narrower incoming population; the "
            "~25% jump is reproduced."
        ),
    }


def worm_section(acc) -> dict:
    recs = acc["innings_recs"]
    seasons = []
    for ss in WORM_SEASONS:
        anchors = [
            r for r in recs if r["league"] == "ipl" and r["season"] == ss and r["is_anchor"]
        ]
        anchors.sort(key=lambda r: (-r["balls"], r["runs"], r["batter"]))
        exemplars = []
        for r in anchors[:WORM_EXEMPLARS_PER_SEASON]:
            cum = []
            s = 0
            for rb in r["seq"][:WORM_MAX_BALLS]:
                s += rb
                cum.append(s)
            m = acc["matches"][r["match_index"]]
            opp = [t for t in m["teams"] if t != r["team"]]
            exemplars.append(
                {
                    "batter": r["batter"],
                    "team": r["team"],
                    "opponent": opp[0] if opp else None,
                    "season": ss,
                    "date": m["date"],
                    "balls": r["balls"],
                    "runs": r["runs"],
                    "sr": r1(r["sr"]),
                    "boundary_pct": r1(100.0 * r["boundary"] / r["balls"]),
                    "par_sr": r1(r["par_sr"]),
                    "cum_runs": cum,
                }
            )
        fr = acc["faced_runs"][("ipl", ss)]
        fc = acc["faced_count"][("ipl", ss)]
        maxlen = min(max([len(e["cum_runs"]) for e in exemplars] + [30]), WORM_MAX_BALLS)
        par_worm = []
        s = 0.0
        for n in range(1, maxlen + 1):
            if fc.get(n):
                s += fr[n] / fc[n]
            par_worm.append(r1(s))
        seasons.append(
            {"season": ss, "exemplars": exemplars, "par_worm": par_worm}
        )
    return {
        "seasons": seasons,
        "definition": (
            "For each exemplar IPL season, the longest real anchor innings "
            "(qualifying anchors, ranked by balls faced then slowness) as "
            "ball-by-ball cumulative batter runs (cum_runs), against the "
            "season par worm — the mean cumulative runs of an average batter "
            "by ball faced (sum over n of that season's mean runs at faced-"
            "index n). Recent seasons carry fewer worms by design — the "
            "species is thinning."
        ),
    }


def wpl_beat_ch2_section(acc, anchor, runout) -> dict:
    wpl_band = "wpl " + WPL_BAND[1]
    anchor_share = anchor["bands"][wpl_band]["anchor_ball_share_pct"]
    ipl_modern_anchor = anchor["bands"]["ipl 2023-2026"]["anchor_ball_share_pct"]
    wpl_runout = {
        r["season"]: r["runout_share_pct"] for r in runout["seasons"]["wpl"]
    }
    # Pooled WPL run-out share (all four WPL seasons).
    wpl_ro_tot = sum(acc["runout_total"][("wpl", s)] for s in canon.WPL_SEASONS)
    wpl_dis_tot = sum(acc["dis_total"][("wpl", s)] for s in canon.WPL_SEASONS)
    wpl_ro_pooled = r1(100.0 * wpl_ro_tot / wpl_dis_tot) if wpl_dis_tot else None
    ipl_ro = {r["season"]: r["runout_share_pct"] for r in runout["seasons"]["ipl"]}
    ipl_2008_ro = ipl_ro[2008]  # where the IPL started (12.3%)
    ipl_modern_ro = ipl_ro[2026]  # where the IPL has arrived (4.7%)
    return {
        # The dialect clock: batting archetypes already modern (born post-anchor).
        "anchor_ball_share_pct": anchor_share,
        "anchor_ball_share_by_season": {
            str(r["season"]): r["anchor_ball_share_pct"]
            for r in anchor["seasons"]["wpl"]
        },
        "ipl_modern_anchor_ball_share_pct": ipl_modern_anchor,
        # The timeline clock: running risk still mid-revolution (well above the
        # IPL's modern floor). Placement is left to authored copy — the full IPL
        # run-out series (runout.seasons.ipl) ships so the frontend can position
        # the WPL on the decline curve; here we ship the two endpoints only,
        # never a single contested "nearest season".
        "runout_share_pct": wpl_ro_pooled,
        "runout_share_by_season": {str(k): v for k, v in wpl_runout.items()},
        "ipl_start_runout_share_pct": ipl_2008_ro,
        "ipl_modern_runout_share_pct": ipl_modern_ro,
        "two_clocks_note": (
            "Two clocks in one beat (house rule): the WPL's anchor-ball share "
            f"(~{anchor_share}%) is already at modern-IPL levels ({ipl_modern_anchor}%) "
            "— born post-anchor, a modern batting dialect — while its run-out "
            f"share (~{wpl_ro_pooled}%) is still mid-revolution, partway down "
            f"the IPL's own decline from {ipl_2008_ro}% (2008) to "
            f"{ipl_modern_ro}% (2026): the risky single has not yet died in the "
            "WPL. Batting archetypes modern, running risk mid-clock — one "
            "league, two clocks at once."
        ),
    }


ANCHOR_EMPTY_HEADLINE = (
    "{team} was born post-anchor — there is no qualifying anchor innings in "
    "its history to mourn. That absence is the point."
)


def _anchor_card(acc, best_key, best, matches, team, league, neutral=False, counts=None):
    r = best.get(best_key)
    if r is None:
        return {
            "team": team,
            "league": league,
            "empty_state": True,
            "batter": None,
            "season": None,
            "date": None,
            "opponent": None,
            "venue": None,
            "balls": None,
            "runs": None,
            "sr": None,
            "boundary_pct": None,
            "par_sr": None,
            "cum_runs": None,
            "season_anchor_innings": None,
            "headline": ANCHOR_EMPTY_HEADLINE.format(team=team),
        }
    m = matches[r["match_index"]]
    opp = [t for t in m["teams"] if t != r["team"]]
    sr = r1(r["sr"])
    par = r1(r["par_sr"])
    boundary_pct = r1(100.0 * r["boundary"] / r["balls"])
    cum = []  # the innings' ball-by-ball cumulative runs (replayable worm)
    s = 0
    for rb in r["seq"][:WORM_MAX_BALLS]:
        s += rb
        cum.append(s)
    if neutral:
        headline = (
            f"The last anchor the IPL has seen: {r['batter']}, {r['season']} — "
            f"{r['runs']} off {r['balls']} (strike rate {sr}), against "
            f"{opp[0] if opp else 'the field'}, on a day the league expected "
            f"about {round(par)}."
        )
    else:
        headline = (
            f"{team}'s last anchor: {r['batter']}, {r['season']} — {r['runs']} "
            f"off {r['balls']} (strike rate {sr}, {boundary_pct}% boundaries), "
            f"while par was about {round(par)}."
        )
    return {
        "team": team,
        "league": league,
        "empty_state": False,
        "batter": r["batter"],
        "season": r["season"],
        "date": m["date"],
        "opponent": opp[0] if opp else None,
        "venue": m["venue"],
        "balls": r["balls"],
        "runs": r["runs"],
        "sr": sr,
        "boundary_pct": boundary_pct,
        "par_sr": par,
        "cum_runs": cum,
        # rarity signal (storyboard C2-8 audit fix): how many TOP-ORDER qualifying
        # anchor innings the SAME LEAGUE produced in this innings' season. It
        # reframes "last anchor" as "increasingly rare" (one of only N that whole
        # season) rather than "literally last year" — the datum is often the
        # current season, so absolute-extinction wording would misread.
        "season_anchor_innings": (counts or {}).get((r["league"], r["season"]), 0),
        "headline": headline,
    }


def payoff_section(acc) -> dict:
    """The 16 'Your last anchor' team-picker variants (10 IPL + 5 WPL +
    neutral). Strictly template + per-team numbers; born-post-anchor sides get
    the designed empty state."""
    matches = acc["matches"]
    best = {}  # (league, team) -> the most recent qualifying anchor innings
    ipl_best = None  # the most recent IPL anchor overall (the neutral card)
    # league-season count of TOP-ORDER qualifying anchor innings — the payoff's
    # rarity signal (how few the archetype produced each season).
    counts = defaultdict(int)
    for r in acc["innings_recs"]:
        # "Your last anchor" is the archetype who HELD THE INNINGS TOGETHER —
        # a top-order (position 1-4) qualifying anchor, not a tail-end block.
        if not r["is_anchor"] or r["position"] > 4:
            continue
        counts[(r["league"], r["season"])] += 1
        key = (r["league"], r["team"])
        cur = best.get(key)
        stamp = (r["season"], r["match_index"])
        if cur is None or stamp > (cur["season"], cur["match_index"]):
            best[key] = r
        if r["league"] == "ipl" and (
            ipl_best is None
            or stamp > (ipl_best["season"], ipl_best["match_index"])
        ):
            ipl_best = r
    variants = []
    for t in canon.CURRENT_IPL_FRANCHISES:
        variants.append(_anchor_card(acc, ("ipl", t), best, matches, t, "ipl", counts=counts))
    for t in canon.WPL_FRANCHISES:
        variants.append(_anchor_card(acc, ("wpl", t), best, matches, t, "wpl", counts=counts))
    neutral = _anchor_card(
        acc, "__neutral__", {"__neutral__": ipl_best}, matches, "Neutral", "ipl", neutral=True, counts=counts
    )
    variants.append(neutral)
    return {
        "card": "your-last-anchor",
        "variants": variants,
        "definition": (
            "Per franchise (10 IPL + 5 WPL + neutral): the LAST (most recent "
            "season, then latest in the point stream) qualifying TOP-ORDER "
            "(position 1-4) anchor innings in that franchise's history — the "
            "batter who held the innings together — with batter, season, balls, "
            "strike rate, boundary %, and what par was that day. Franchises born "
            "post-anchor with no qualifying top-order anchor get the designed "
            "empty state (authored copy, never a blank card). Neutral = the most "
            "recent top-order IPL anchor overall. season_anchor_innings = how many "
            "top-order qualifying anchor innings the SAME league produced in that "
            "innings' season (the rarity signal — one of only N that season). "
            "Strictly template + per-team numbers — nothing hand-authored per team."
        ),
    }


def ch2_doc(acc) -> dict:
    anchor = anchor_section(acc)
    runout = runout_section(acc)
    return {
        "chapter": 2,
        "title": "The Last of the Anchors",
        "register": "elegy",
        "era_bands": band_meta(),
        "par_model": {
            "definition": (
                "Local season x phase par baseline (engine #1 stand-in), each "
                "league priced against its own baseline. par_bat_rpb = batter "
                "runs / legal balls faced (a ball faced = a legal delivery; "
                "wides AND no-balls excluded, a scorecard strike rate); "
                "par_team_rpb = total runs / legal balls; phases = powerplay "
                "(overs 1-6), middle (7-15), death (16-20)."
            ),
            "integration_note": (
                "engines/par.json (engine #1) has landed, BUT it prices balls "
                "faced with NO-BALLS COUNTED (its phasepar denominator), which "
                "does NOT reproduce the blueprint's Ch 2 teasers: it yields "
                "anchor 14.75% -> 8.35% and sub-120 qualifiers=250 / WPL 20.99%, "
                "whereas the blueprint teasers are 14.8% -> 8.5% and WPL 19.8% / "
                "249 recent qualifiers. This scene therefore prices balls faced "
                "as LEGAL deliveries (wides AND no-balls excluded — a scorecard "
                "strike rate), the convention that reconciles those teasers "
                "EXACTLY (anchor 14.8/8.5; archetype 249/2.4/19.8). RESOLUTION "
                "NEEDED (owner): pick one no-ball convention across catalog, "
                "engine #1, and this scene. Until then ch2.json (not par.json's "
                "anchor_extinction / sub120_occupancy blocks, which disagree) is "
                "the on-screen source for Ch 2's anchor and archetype numbers. "
                "If engine #1 adopts the legal-ball convention, swap "
                "_par_bat_rpb / _par_team_rpb for a phasepar.json (league, "
                "season, phase) lookup — the anchor/tax definitions are "
                "unchanged; only the baseline source moves."
            ),
            "phases": list(PHASE_LABELS),
        },
        "anchor": anchor,
        "runout": runout,
        "archetype": archetype_section(acc),
        "gearshift": gearshift_section(acc),
        "newbatter": newbatter_section(acc),
        "worms": worm_section(acc),
        "wpl_beat": wpl_beat_ch2_section(acc, anchor, runout),
        "payoff": payoff_section(acc),
    }


# ---------------------------------------------------------------------------
# R2b — Chapter 3 "The Counterrevolution" (scenes/ch3.json)
# ---------------------------------------------------------------------------
#
# Bowling's answer to the batting explosion. Reuses the SR+/par engine (#1)
# family: the era-honest currency here is True Economy (economy vs its era's
# phase par), the bowling mirror of SR+. Two authoritative passes:
#
#   * bowlerplane.build() — the bowler-season economy x strike-rate plane (also
#     the source of the bowlerplane.u8 per-point buffer, so the JSON frontier
#     and the buffer coordinates are the SAME numbers by construction).
#   * build_ch3() — the season/era aggregates that are NOT bowler-season-keyed:
#     dot rate, Dismissal DNA, the Death-Wide Tax, the middle-overs crack ratio,
#     the two dot-grid finals, and the Phase Fingerprint footnote.
#
# CONVENTIONS (documented project-wide; match the metrics-catalog recipes):
#   economy = (batter runs + wides + no-balls) per 6 LEGAL balls, byes/legbyes
#     excluded; strike rate = legal balls per bowler-credited wicket; a legal
#     ball = not a wide and not a no-ball; dot = legal ball with runs.total==0.
#   Dismissal DNA shares are over BOWLER-CREDITED dismissals (run outs and
#   retirements excluded from the denominator), "caught" excludes caught-and-
#   bowled — the exact cut that reproduces the catalog's 27.4/65.2/4.2.
#
# ENGINE #1 CONSUMPTION: True Economy's par is engine #1's phase-par family,
# flipped to the bowler-charged convention. build_ch3 recomputes the batting
# marginal (batter runs per ball faced, wides excluded / no-balls counted —
# engine #1's exact denominator) and tests/test_r2b.py asserts it reconciles
# byte-for-byte with engines/phasepar.json, so Ch 3 can never drift from
# engine #1.

CH3_FINGERPRINT_MIN_BALLS = 60      # min legal balls to classify a bowler-season phase
CH3_FINGERPRINT_RATIO = 2.0         # death share / league death availability >= 2x => specialist
CH3_CRACK_K = 3                     # k >= 3 consecutive dots = "under pressure"
# The two dot-grid exemplar innings (each season's Final, first innings). Chosen so
# each Final's first-innings dot rate sits NEAR its era's pooled mean (early 37.6,
# modern 33.0), keeping the visual gap honest: the 2010 Final (36.7%) replaces the
# 2009 Final (39.2%, a 7.5pp gap vs 2026's 31.7% — 63% larger than the honest 4.6pp
# league shift the scene cites); 2010 vs 2026 is a ~5pp gap, close to the real shift.
CH3_DOTGRID_FINALS = (("ipl", 2010), ("ipl", 2026))
CH3_DOTPLUS_TOP = 12                # Dot+ leaderboard length
# Bowler-credited dismissal kinds (shared with bowlerplane).
CH3_BOWLER_WKT = bowlerplane.BOWLER_WICKET_KINDS


def _pearson(xs, ys) -> float:
    n = len(xs)
    if n < 2:
        return 0.0
    mx = sum(xs) / n
    my = sum(ys) / n
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sx = (sum((x - mx) ** 2 for x in xs)) ** 0.5
    sy = (sum((y - my) ** 2 for y in ys)) ** 0.5
    return cov / (sx * sy) if sx and sy else 0.0


def _pareto_hull(points: list) -> list:
    """Pareto-efficient set for MINIMIZING both economy and strike rate (the
    lower-left staircase — the best economy achievable at each strike rate).
    points = [(econ, sr, bowler, wkts, balls)]; ties broken deterministically.
    """
    pts = sorted(points, key=lambda p: (p[0], p[1], p[2]))  # econ asc, then sr, then name
    hull = []
    best_sr = float("inf")
    for p in pts:
        # scanning by ascending economy: p is efficient iff no earlier (lower or
        # equal economy) point had a strictly lower strike rate.
        if p[1] < best_sr:
            hull.append(p)
            best_sr = p[1]
    return sorted(hull, key=lambda p: (p[1], p[0]))  # emit sorted by strike rate


def build_ch3(data_root: Path = canon.DATA_ROOT) -> dict:
    """The season/era corpus pass for Chapter 3 (separate from build()/build_ch2
    so R1/R2a scene bytes stay byte-identical)."""
    season_dot = defaultdict(lambda: [0, 0])          # (lg, ss) -> [dots, legal]
    dna_season = defaultdict(lambda: defaultdict(int))  # (lg, ss) -> {kind: count}
    death = defaultdict(lambda: [0, 0])               # (lg, ss) -> [wide deliveries, death legal]
    crack = defaultdict(lambda: [0, 0, 0, 0])         # bandkey -> [k0 balls, k0 wkts, k>=3 balls, k>=3 wkts]
    wpl_stumped = defaultdict(lambda: [0, 0])         # ss -> [stumped, bowler-credited total]
    fp_bowler = defaultdict(lambda: [0, 0])           # (lg, ss, bowler) -> [death legal, total legal]
    fp_league = defaultdict(lambda: [0, 0])           # (lg, ss) -> [death legal, total legal]
    dotgrid = {}                                      # (lg, ss) -> innings record (first innings of the Final)

    for match_index, (_date, _mid, league, path) in enumerate(
        flatten.sorted_match_files(data_root)
    ):
        with open(path) as fh:
            match = json.load(fh)
        info = match["info"]
        season = canon.canon_season(info)
        bk = band_key(league, season)
        is_final = flatten.match_stage(info) == "Final"
        want_grid = (league, season) in CH3_DOTGRID_FINALS and is_final
        teams = [canon.canon_team(t) for t in info["teams"]]
        venue = canon.canon_venue(info["venue"])

        innings_no = 0
        for innings in match.get("innings", []):
            if canon.is_super_over(innings):
                continue
            innings_no += 1
            bat = canon.canon_team(innings["team"])
            others = [t for t in teams if t != bat]
            opponent = others[0] if len(others) == 1 else "?"
            run_dots = 0  # consecutive legal-ball dots so far in this innings
            grid_outcomes, grid_wickets = [], []
            grab = want_grid and innings_no == 1
            for over in innings["overs"]:
                ph = phase_of(over["over"])  # 0 pp / 1 middle / 2 death
                for dl in over["deliveries"]:
                    ex = dl.get("extras", {})
                    wide = "wides" in ex
                    noball = "noballs" in ex
                    legal = not (wide or noball)
                    total = dl["runs"]["total"]
                    is_wkt = bool(dl.get("wickets"))
                    if legal:
                        season_dot[(league, season)][1] += 1
                        if total == 0:
                            season_dot[(league, season)][0] += 1
                        fp_bowler[(league, season, dl["bowler"])][1] += 1
                        fp_league[(league, season)][1] += 1
                        if ph == 2:
                            death[(league, season)][1] += 1
                            fp_bowler[(league, season, dl["bowler"])][0] += 1
                            fp_league[(league, season)][0] += 1
                        if ph == 1:  # crack ratio: middle overs only
                            c = crack[bk]
                            if run_dots == 0:
                                c[0] += 1
                                if is_wkt:
                                    c[1] += 1
                            elif run_dots >= CH3_CRACK_K:
                                c[2] += 1
                                if is_wkt:
                                    c[3] += 1
                        if grab:
                            grid_outcomes.append(flatten.outcome_class(dl))
                            grid_wickets.append(1 if is_wkt else 0)
                        run_dots = run_dots + 1 if total == 0 else 0
                    if ph == 2 and wide:
                        death[(league, season)][0] += 1
                    for w in dl.get("wickets", []):
                        k = w["kind"]
                        if k in RETIRED_KINDS:
                            continue
                        dna_season[(league, season)][k] += 1
                        if league == "wpl":
                            wpl_stumped[season][1] += 1
                            if k == "stumped":
                                wpl_stumped[season][0] += 1
            if grab:
                dots = grid_outcomes.count(flatten.OUT_DOT)
                dotgrid[(league, season)] = {
                    "match_index": match_index,
                    "batting_team": bat,
                    "opponent": opponent,
                    "season": season,
                    "date": str(info["dates"][0]),
                    "venue": venue,
                    "city": canon.GROUND_CITY[venue],
                    "stage": "Final",
                    "legal_balls": len(grid_outcomes),
                    "dots": dots,
                    "dot_pct": r1(100.0 * dots / len(grid_outcomes)) if grid_outcomes else None,
                    "outcomes": grid_outcomes,
                    "wickets": grid_wickets,
                }

    return {
        "season_dot": season_dot,
        "dna_season": dna_season,
        "death": death,
        "crack": crack,
        "wpl_stumped": wpl_stumped,
        "fp_bowler": fp_bowler,
        "fp_league": fp_league,
        "dotgrid": dotgrid,
        "bp": bowlerplane.build(data_root),
    }


# --- Chapter 3 sections ---------------------------------------------------


def _qualifying_bowler_seasons(bp):
    """[(league, season, bowler, econ, sr, wkts, balls)] with >= 90 legal balls."""
    out = []
    for (lg, ss, bowler), rec in bp["bowler_seasons"].items():
        if rec.legal < bowlerplane.MIN_LEGAL_BALLS:
            continue
        out.append((lg, ss, bowler, bowlerplane.economy(rec),
                    bowlerplane.strike_rate(rec), rec.wkts, rec.legal))
    return out


def frontier_section(bp) -> dict:
    qual = _qualifying_bowler_seasons(bp)

    # (a) economy-under-7 share per era band + per season
    era = {k: [0, 0] for k in BAND_KEYS}
    per_season = defaultdict(lambda: [0, 0])
    for lg, ss, _b, econ, _sr, _w, _n in qual:
        bk = band_key(lg, ss)
        era[bk][1] += 1
        per_season[(lg, ss)][1] += 1
        if econ < 7.0:
            era[bk][0] += 1
            per_season[(lg, ss)][0] += 1
    under7 = {
        "definition": "share of bowler-seasons (>= 90 legal balls) with economy under 7.0 runs per over",
        "era_bands": {
            k: {"under7": era[k][0], "qualifiers": era[k][1],
                "pct": r1(100.0 * era[k][0] / era[k][1]) if era[k][1] else None}
            for k in BAND_KEYS
        },
        "per_season": [
            {"league": lg, "season": ss, "under7": v[0], "qualifiers": v[1],
             "pct": r1(100.0 * v[0] / v[1]) if v[1] else None}
            for (lg, ss), v in sorted(per_season.items())
        ],
    }

    # (b) Pareto hull per league-season (drop 0-wicket seasons — no SR axis)
    by_ls = defaultdict(list)
    for lg, ss, b, econ, sr, w, n in qual:
        if sr is not None:
            by_ls[(lg, ss)].append((econ, sr, b, w, n))
    hull_seasons = []
    for (lg, ss), pts in sorted(by_ls.items()):
        hull = _pareto_hull(pts)
        hull_seasons.append({
            "league": lg, "season": ss,
            "points": [
                {"economy": r2(e), "strike_rate": r1(s), "bowler": b,
                 "wickets": w, "balls": n}
                for e, s, b, w, n in hull
            ],
        })

    # (c) ghost trail — one great across every frontier
    gl, gb = bowlerplane.GHOST_BOWLER
    trail = []
    for lg, ss, b, econ, sr, w, n in sorted(qual, key=lambda q: q[1]):
        if lg == gl and b == gb:
            trail.append({"season": ss, "economy": r2(econ),
                          "strike_rate": r1(sr) if sr is not None else None,
                          "wickets": w, "balls": n})

    # (d) the refuted econ~SR correlation, per era
    corr = {}
    pair = defaultdict(lambda: ([], []))
    for lg, ss, _b, econ, sr, _w, _n in qual:
        if sr is not None:
            pair[band_key(lg, ss)][0].append(econ)
            pair[band_key(lg, ss)][1].append(sr)
    for k in BAND_KEYS:
        e, s = pair[k]
        corr[k] = {"r": round(_pearson(e, s), 2), "n": len(e)}

    return {
        "definition": (
            "Every bowler-season (>= 90 legal balls) is a point on the economy x "
            "strike-rate plane. Economy = (batter runs + wides + no-balls) per 6 "
            "legal balls (byes/legbyes excluded). Strike rate = legal balls per "
            "bowler-credited wicket. Both are better when LOWER, so the Pareto "
            "hull is the lower-left edge and the containment corner (economy < 7) "
            "is the left edge. The hull retreats season by season."
        ),
        "axis": {
            "economy": {"lo": bowlerplane.ECON_LO, "hi": bowlerplane.ECON_HI,
                        "unit": "runs per over", "better": "lower"},
            "strike_rate": {"lo": bowlerplane.SR_LO, "hi": bowlerplane.SR_HI,
                            "unit": "legal balls per wicket", "better": "lower",
                            "sentinel": bowlerplane.SENTINEL,
                            "sentinel_meaning": "bowler-season took no bowler-credited wicket"},
            "buffer": "bowlerplane.u8 — byte 0 = economy, byte 1 = strike rate; see bowlerplane_buffer",
        },
        "under7": under7,
        "hull": {
            "note": "Pareto-efficient bowler-seasons (best economy for each strike rate), per league-season, sorted by strike rate.",
            "seasons": hull_seasons,
        },
        "ghost_trail": {
            "bowler": gb, "league": gl,
            "note": "one great bowler's drift across every frontier — even elite economy rises with the tide",
            "points": trail,
        },
        "correlation": {
            "definition": "Pearson r between economy and strike rate across qualifying bowler-seasons — the refuted sub-claim (weakly positive, not negative); the hull carries the story, not the correlation.",
            "era_bands": corr,
        },
    }


def dot_plus_section(acc3) -> dict:
    bp = acc3["bp"]
    season_dot = acc3["season_dot"]

    def dot_pct(lg, ss):
        d, l = season_dot[(lg, ss)]
        return r1(100.0 * d / l) if l else None

    def era_dot(lg, lo, hi):
        d = sum(season_dot[(lg, s)][0] for s in range(lo, hi + 1))
        l = sum(season_dot[(lg, s)][1] for s in range(lo, hi + 1))
        return r1(100.0 * d / l) if l else None

    per_season = [
        {"league": lg, "season": ss,
         "dot_pct": dot_pct(lg, ss), "legal_balls": season_dot[(lg, ss)][1]}
        for lg in ("ipl", "wpl")
        for ss in (canon.IPL_SEASONS if lg == "ipl" else canon.WPL_SEASONS)
    ]

    # Dot+ leaderboard (era-normalized dot manufacturing, >= 200 legal balls)
    rows = []
    for (lg, ss, bowler), rec in bp["bowler_seasons"].items():
        if rec.legal < bowlerplane.DOTPLUS_MIN_BALLS:
            continue
        dp = bowlerplane.dot_plus(rec, bp["so_dot"])
        if dp is None:
            continue
        rows.append({"dot_plus": r1(dp), "league": lg, "season": ss,
                     "bowler": bowler, "dots": rec.dots,
                     "expected_dots": r1(bowlerplane.expected_dots(rec, bp["so_dot"])),
                     "balls": rec.legal})
    rows.sort(key=lambda r: (-r["dot_plus"], r["league"], r["season"], r["bowler"]))

    ref = era_dot("ipl", 2008, 2010)
    scarcity = [
        {"league": lg, "season": ss,
         "dot_scarcity_index": r1(100.0 * ref / dot_pct(lg, ss))
         if dot_pct(lg, ss) else None}
        for lg in ("ipl", "wpl")
        for ss in (canon.IPL_SEASONS if lg == "ipl" else canon.WPL_SEASONS)
    ]

    return {
        "definition": (
            "Dot = legal ball with no run at all (runs.total == 0). Dot+ = 100 x "
            "actual dots / dots an average bowler would make with the same season "
            "x over-number mix (>= 200 legal balls). 100 = league average of its "
            "own time; dots are a deflating currency, so a high 2026 Dot+ is a "
            "harder achievement than the same rate in 2009."
        ),
        "era_headline": {
            "ipl_2008_2010": ref,
            "ipl_2023_2026": era_dot("ipl", 2023, 2026),
            "wpl_2023_2026": era_dot("wpl", 2023, 2026),
        },
        "per_season": per_season,
        "dot_scarcity": {
            "reference": "IPL 2008-2010 dot rate = index 100; higher = a dot is scarcer (more valuable) than the early IPL",
            "per_season": scarcity,
        },
        "leaderboard": rows[:CH3_DOTPLUS_TOP],
    }


def dismissal_dna_section(acc3) -> dict:
    dna_season = acc3["dna_season"]

    def era_kinds(lg, lo, hi):
        agg = defaultdict(int)
        for s in range(lo, hi + 1):
            for k, v in dna_season[(lg, s)].items():
                agg[k] += v
        return agg

    def shares(agg):
        denom = sum(v for k, v in agg.items() if k != "run out")  # bowler-credited
        if not denom:
            return None
        caught = agg.get("caught", 0)  # excludes caught and bowled
        cb = agg.get("caught and bowled", 0)
        bl = agg.get("bowled", 0) + agg.get("lbw", 0)
        st = agg.get("stumped", 0)
        return {
            "bowler_credited": denom,
            "bowled_lbw_pct": r1(100.0 * bl / denom),
            "caught_pct": r1(100.0 * caught / denom),
            "caught_and_bowled_pct": r1(100.0 * cb / denom),
            "stumped_pct": r1(100.0 * st / denom),
            "run_outs": agg.get("run out", 0),
            "kinds": {k: agg[k] for k in sorted(agg)},
        }

    era = {
        "ipl 2008-2010": shares(era_kinds("ipl", 2008, 2010)),
        "ipl 2011-2015": shares(era_kinds("ipl", 2011, 2015)),
        "ipl 2016-2019": shares(era_kinds("ipl", 2016, 2019)),
        "ipl 2020-2022": shares(era_kinds("ipl", 2020, 2022)),
        "ipl 2023-2026": shares(era_kinds("ipl", 2023, 2026)),
        "wpl 2023-2026": shares(era_kinds("wpl", 2023, 2026)),
    }
    rivers = [
        {"league": lg, "season": ss,
         "kinds": {k: dna_season[(lg, ss)][k] for k in sorted(dna_season[(lg, ss)])}}
        for lg in ("ipl", "wpl")
        for ss in (canon.IPL_SEASONS if lg == "ipl" else canon.WPL_SEASONS)
    ]
    return {
        "definition": (
            "How wickets fall. Shares are over BOWLER-CREDITED dismissals (run "
            "outs and retirements excluded from the denominator); 'caught' "
            "excludes caught-and-bowled (kept separate). Bowlers stopped "
            "attacking stumps and started attacking the long boundary."
        ),
        "era_bands": era,
        "rivers": {
            "note": "per-kind counts per league-season for the dismissal-kind streamgraph (the actual wicket balls).",
            "per_season": rivers,
        },
    }


def death_wide_tax_section(acc3) -> dict:
    death = acc3["death"]

    def rate(lg, ss):
        w, l = death[(lg, ss)]
        return r2(100.0 * w / l) if l else None

    def era_rate(lg, lo, hi):
        w = sum(death[(lg, s)][0] for s in range(lo, hi + 1))
        l = sum(death[(lg, s)][1] for s in range(lo, hi + 1))
        return r2(100.0 * w / l) if l else None

    per_season = [
        {"league": lg, "season": ss, "wides_per_100_legal": rate(lg, ss),
         "wide_deliveries": death[(lg, ss)][0], "death_legal_balls": death[(lg, ss)][1]}
        for lg in ("ipl", "wpl")
        for ss in (canon.IPL_SEASONS if lg == "ipl" else canon.WPL_SEASONS)
    ]
    early = era_rate("ipl", 2008, 2010)
    recent = era_rate("ipl", 2023, 2026)
    return {
        "definition": (
            "Death overs = overs 16-20. Wides per 100 legal balls in the death "
            "overs (count of wide deliveries; byes/legbyes irrelevant). The arms "
            "race made flesh: bowlers chasing wide-yorker extremes leak more free "
            "runs than ever."
        ),
        "era_headline": {
            "ipl_2008_2010": early,
            "ipl_2023_2026": recent,
            "wpl_2023_2026": era_rate("wpl", 2023, 2026),
            "doubling_factor": round(recent / early, 2) if early else None,
        },
        "per_season": per_season,
    }


def dot_grid_section(acc3) -> dict:
    dg = acc3["dotgrid"]
    innings = []
    for lg, ss in CH3_DOTGRID_FINALS:
        rec = dg.get((lg, ss))
        if rec is None:
            continue
        innings.append({
            "label": f"{ss} IPL Final",
            "league": lg,
            **rec,
        })
    return {
        "definition": (
            "Each cell is one legal ball of a real innings, read left to right, "
            "top to bottom (120 cells = a full 20 overs). Outcome code: 0 = dot "
            "(no run), 1 = single, 2 = two or three, 3 = four, 4 = six, 5 = other "
            "(byes/leg-byes off a legal ball). A separate wickets array flags the "
            "ball a wicket fell. Both innings are their season's Final, first "
            "innings — dot rates sit at each season's average, so the erosion of "
            "the dark cells is honest, not cherry-picked."
        ),
        "outcome_legend": {"0": "dot", "1": "single", "2": "two or three",
                           "3": "four", "4": "six", "5": "other (byes/leg-byes)"},
        "innings": innings,
    }


def crack_ratio_section(acc3) -> dict:
    crack = acc3["crack"]

    def ratio(bk):
        c = crack[bk]
        p0 = c[1] / c[0] if c[0] else None
        p3 = c[3] / c[2] if c[2] else None
        if not p0:
            return None
        return {
            "p_wicket_k0": round(p0, 4),
            "p_wicket_kge3": round(p3, 4) if p3 is not None else None,
            "crack_ratio": round(p3 / p0, 2) if p3 is not None else None,
            "n_k0": c[0], "n_kge3": c[2],
        }

    return {
        "definition": (
            "Middle overs (7-15). Crack ratio = P(wicket next ball after 3+ "
            "straight dots) / P(wicket next ball after a scoring ball). Above 1, "
            "dot pressure still buys wickets; below 1, batters have defused it. "
            "This is why IPL bowling economies inflated even as bowler skill grew."
        ),
        "era_bands": {
            "ipl 2008-2010": ratio("ipl 2008-2010"),
            "ipl 2023-2026": ratio("ipl 2023-2026"),
            "wpl 2023-2026": ratio("wpl 2023-2026"),
        },
        "headline": "Dots still kill in the WPL (crack ratio above 1); the modern IPL defused them (below 1).",
    }


def wpl_beat3_section(acc3) -> dict:
    season_dot = acc3["season_dot"]
    wpl_stumped = acc3["wpl_stumped"]
    death = acc3["death"]
    crack = acc3["crack"]

    d = sum(season_dot[("wpl", s)][0] for s in canon.WPL_SEASONS)
    l = sum(season_dot[("wpl", s)][1] for s in canon.WPL_SEASONS)
    dw = sum(death[("wpl", s)][0] for s in canon.WPL_SEASONS)
    dl = sum(death[("wpl", s)][1] for s in canon.WPL_SEASONS)
    st = sum(wpl_stumped[s][0] for s in canon.WPL_SEASONS)
    stt = sum(wpl_stumped[s][1] for s in canon.WPL_SEASONS)
    per_season_stumped = [
        {"season": s, "stumped": wpl_stumped[s][0], "bowler_credited": wpl_stumped[s][1],
         "pct": r1(100.0 * wpl_stumped[s][0] / wpl_stumped[s][1]) if wpl_stumped[s][1] else None}
        for s in canon.WPL_SEASONS
    ]
    cw = crack["wpl 2023-2026"]
    ci = crack["ipl 2023-2026"]
    crack_w = round((cw[3] / cw[2]) / (cw[1] / cw[0]), 2) if cw[0] and cw[2] else None
    crack_i = round((ci[3] / ci[2]) / (ci[1] / ci[0]), 2) if ci[0] and ci[2] else None
    return {
        "note": (
            "Two clocks in the same breath. On the calendar clock the WPL sits "
            "where the IPL did in 2009 (dot rate). In the same beat, the stats "
            "that refuse the timeline: it is a spinner's league (stumpings), the "
            "wide-yorker arms race is a men's-league thing (low death wides), and "
            "dot pressure still buys wickets there. A different ecosystem, not an "
            "earlier one."
        ),
        "dot_rate_pct": r1(100.0 * d / l) if l else None,
        "dot_rate_matches": "IPL 2009",
        "stumped": {
            "pooled_pct": r1(100.0 * st / stt) if stt else None,
            "per_season": per_season_stumped,
            "ipl_2023_2026_pct": None,  # filled from dismissal_dna in ch3_doc
        },
        "death_wides_per_100_legal": r2(100.0 * dw / dl) if dl else None,
        "crack_ratio_wpl": crack_w,
        "crack_ratio_ipl_2023_2026": crack_i,
    }


def gravity_defiers_section(acc3) -> dict:
    bp = acc3["bp"]
    phase_eco = bp["phase_eco"]
    best = {}  # (league, franchise) -> record
    for rec in bp["bowler_seasons"].values():
        if rec.legal < bowlerplane.MIN_LEGAL_BALLS:
            continue
        te = bowlerplane.true_economy(rec, phase_eco)
        fr = bowlerplane.franchise(rec)
        if te is None or fr is None:
            continue
        e = bowlerplane.economy(rec)
        par = bowlerplane.par_economy(rec, phase_eco)
        cur = best.get((rec.league, fr))
        cand = (te, {
            "league": rec.league,
            "franchise": fr,
            "franchise_id": canon.team_id(rec.league, fr),
            "bowler": rec.bowler,
            "season": rec.season,
            "economy": r2(e),
            "par_economy": r2(par),
            "true_economy": r2(te),
            "wickets": rec.wkts,
            "balls": rec.legal,
            "small_sample": rec.league == "wpl" or rec.legal < 150,
        })
        if cur is None or cand[0] > cur[0] or (
            cand[0] == cur[0] and cand[1]["bowler"] < cur[1]["bowler"]
        ):
            best[(rec.league, fr)] = cand

    variants = [v[1] for v in best.values()]
    variants.sort(key=lambda v: v["franchise_id"])
    return {
        "definition": (
            "Your franchise's gravity-defier: the bowler-season that beat its "
            "era's tide by the most. True Economy = par economy - actual economy, "
            "where par is the league-season economy for the exact phase mix the "
            "bowler bowled (a death specialist is priced against death par). "
            "Positive = leaks fewer runs than its era should. This is engine #1's "
            "par family, flipped from batting to bowling."
        ),
        "wpl_note": "WPL cards carry a short-sample flag by design — four seasons is not nineteen.",
        "variants": variants,
    }


def _batting_par(bp):
    """Batting par SR per era from the phasepar-convention marginal (batter runs
    per ball faced x 100). Reconciles byte-for-byte with engines/phasepar.json —
    asserted in tests/test_r2b.py (the engine #1 consumption gate)."""
    bm = bp["batter_marginal"]

    def era_sr(lg, lo, hi):
        runs = sum(bm[(lg, s, ph)][0] for s in range(lo, hi + 1) for ph in bowlerplane.PHASES
                   if (lg, s, ph) in bm)
        balls = sum(bm[(lg, s, ph)][1] for s in range(lo, hi + 1) for ph in bowlerplane.PHASES
                    if (lg, s, ph) in bm)
        return r1(100.0 * runs / balls) if balls else None

    return {
        "ipl_2008_2010": era_sr("ipl", 2008, 2010),
        "ipl_2023_2026": era_sr("ipl", 2023, 2026),
        "wpl_2023_2026": era_sr("wpl", 2023, 2026),
    }


def phase_fingerprint(acc3) -> dict:
    """Death-specialist emergence footnote — share of death balls delivered by
    bowler-seasons over-indexed to the death (death share / league death
    availability >= 2x, min 60 legal balls), per IPL season."""
    fp_bowler = acc3["fp_bowler"]
    fp_league = acc3["fp_league"]
    rows = []
    for ss in canon.IPL_SEASONS:
        dl, tl = fp_league[("ipl", ss)]
        avail = dl / tl if tl else 0.0
        spec = 0
        for (lg, s, _b), (db, tb) in fp_bowler.items():
            if lg != "ipl" or s != ss or tb < CH3_FINGERPRINT_MIN_BALLS:
                continue
            if avail > 0 and (db / tb) / avail >= CH3_FINGERPRINT_RATIO:
                spec += db
        rows.append({"season": ss,
                     "specialist_death_share_pct": r1(100.0 * spec / dl) if dl else None})
    peak = max((r for r in rows if r["specialist_death_share_pct"] is not None),
               key=lambda r: r["specialist_death_share_pct"], default=None)
    return {
        "definition": (
            "Death balls delivered by 2x-death-over-indexed bowler-seasons "
            "(death share of a bowler's legal balls >= 2x the league's death "
            "availability, min 60 legal balls). The death specialist rose then "
            "eroded (Impact Player flexibility?)."
        ),
        "per_season": rows,
        "start_2008_pct": rows[0]["specialist_death_share_pct"],
        "end_2026_pct": rows[-1]["specialist_death_share_pct"],
        "peak": peak,
        "catalog_reference": {
            "note": "The catalog reports 0.0% (2008) -> 17.3% (2023), peak 20.6% (2021) under its own availability recipe; this recompute is definition-sensitive and lands lower, but the shape (emergence then a 2026 slump) is the same.",
            "start_pct": 0.0, "recent_pct": 17.3, "peak_pct": 20.6, "peak_season": 2021,
        },
    }


def footnotes3_section(acc3) -> dict:
    bp = acc3["bp"]
    phase_eco = bp["phase_eco"]
    dna_season = acc3["dna_season"]

    # True Economy headline: league bowler-charged economy per era
    def league_econ(lg, lo, hi):
        num = 0.0
        den = 0
        for s in range(lo, hi + 1):
            for ph in range(3):
                cell = phase_eco.get((lg, s, ph))
                if cell:
                    num += cell[0]
                    den += cell[1]
        return r2(6.0 * num / den) if den else None

    # FIB — caught & run-out share over ALL dismissals, per era
    def fib(lg, lo, hi):
        agg = defaultdict(int)
        for s in range(lo, hi + 1):
            for k, v in dna_season[(lg, s)].items():
                agg[k] += v
        tot = sum(agg.values())
        caught = agg.get("caught", 0) + agg.get("caught and bowled", 0)
        return {"caught_pct": r1(100.0 * caught / tot) if tot else None,
                "run_out_pct": r1(100.0 * agg.get("run out", 0) / tot) if tot else None}

    corr = frontier_section(bp)["correlation"]["era_bands"]
    return {
        "economy_convention": (
            "Economy is bowler-charged: batter runs + wides + no-balls per 6 "
            "legal balls. Byes and leg-byes are excluded everywhere in this piece "
            "(they are not the bowler's fault) — this shifts league RPO ~0.15 vs "
            "an all-extras economy."
        ),
        "true_economy": {
            "definition": "TrueEcon = par economy - conceded economy for the exact phase mix bowled (engine #1's par family, flipped to bowling).",
            "league_charged_economy": {
                "ipl_2008_2010": league_econ("ipl", 2008, 2010),
                "ipl_2023_2026": league_econ("ipl", 2023, 2026),
            },
            "headline": "League bowler-charged economy rose from 7.79 to 9.38 RPO — a 7.5 economy went from league-par to nearly 2 runs an over better than par.",
            "batting_par_sr_reference": _batting_par(bp),
            "engine1_note": "The batting par SR reference is engine #1's phase-par (engines/phasepar.json); the reconciliation is asserted in tests.",
        },
        "true_wickets_per_24": (
            "TrueW24 = (actual - expected wickets) per 24 balls, expected from the "
            "same league-season baseline. The bowling mirror of the SR+ family; "
            "who actually took more wickets than their era should."
        ),
        "phase_fingerprint": phase_fingerprint(acc3),
        "fib": {
            "definition": "Field-Independent Bowling strips fielder-dependent luck. Caught rose and run-outs collapsed, so raw bowler stats are less skill-reflective now than in 2008 — exactly the drift FIB removes.",
            "ipl_2008_2010": fib("ipl", 2008, 2010),
            "ipl_2023_2026": fib("ipl", 2023, 2026),
        },
        "refuted_correlation": {
            "note": "The cross-bowler economy~strike-rate correlation is weakly POSITIVE, not negative — pitch the hull's retreat, not the correlation.",
            "ipl_2008_2010_r": corr["ipl 2008-2010"]["r"],
            "ipl_2023_2026_r": corr["ipl 2023-2026"]["r"],
            "wpl_2023_2026_r": corr["wpl 2023-2026"]["r"],
        },
        "crack_ratio_construction": (
            "Raw release ratios are always below 1 (pressure states coincide with "
            "good bowlers), so the crack ratio is the honest read: P(wicket after "
            "3+ dots) / P(wicket after a scoring ball), middle overs, run outs "
            "included as pressure dismissals."
        ),
    }


def ch3_doc(acc3) -> dict:
    dna = dismissal_dna_section(acc3)
    wpl = wpl_beat3_section(acc3)
    # cross-link the IPL modern stumped share into the WPL two-clocks beat
    ipl_recent = dna["era_bands"].get("ipl 2023-2026")
    if ipl_recent is not None:
        wpl["stumped"]["ipl_2023_2026_pct"] = ipl_recent["stumped_pct"]
    return {
        "chapter": 3,
        "title": "The Counterrevolution",
        "register": "the resistance mutates",
        "era_bands": band_meta(),
        "frontier": frontier_section(acc3["bp"]),
        "dot_plus": dot_plus_section(acc3),
        "dismissal_dna": dna,
        "death_wide_tax": death_wide_tax_section(acc3),
        "dot_grid": dot_grid_section(acc3),
        "crack_ratio": crack_ratio_section(acc3),
        "wpl_beat": wpl,
        "gravity_defiers": gravity_defiers_section(acc3),
        "footnotes": footnotes3_section(acc3),
        "bowlerplane_buffer": {
            "file": "bowlerplane.u8",
            "bytes_per_point": 2,
            "point_order": flatten.POINT_ORDER,
            "byte0": "bowler-season economy",
            "byte1": "bowler-season bowling strike rate",
            "economy": {"lo": bowlerplane.ECON_LO, "hi": bowlerplane.ECON_HI,
                        "decode": "economy = lo + byte0/254 * (hi - lo)"},
            "strike_rate": {"lo": bowlerplane.SR_LO, "hi": bowlerplane.SR_HI,
                            "sentinel": bowlerplane.SENTINEL,
                            "sentinel_meaning": "no bowler-credited wicket (strike rate undefined)",
                            "decode": "strike_rate = lo + byte1/254 * (hi - lo), for byte1 < 255"},
            "wides_noballs": "carry their bowler-season coordinate like any delivery (they belong to that bowler-season and count toward its economy)",
            "qualifier_note": "every delivery is encoded; frontier plotting uses only bowler-seasons with >= 90 legal balls (derivable: economy byte, or the frontier.hull list).",
        },
    }


# ---------------------------------------------------------------------------
# Chapter 4 — The Rising Tide (R3a). Engine-light: it REUSES engine #1
# (par/phasepar) as the era-honest scoring baseline and builds NO new engine.
# Everything here is a per-season / per-era aggregate of first-innings scoring:
# the 200 Club (threshold exceedance), the win-half-the-time par total, the
# powerplay premium at equal wicket cost, venue divergence, the CPI callback,
# the record ticker, and the waterline-morph column table. Separate corpus pass
# so R1/R2 scene bytes stay byte-identical.
# ---------------------------------------------------------------------------

# Milestone ridgeline light beams + the 200 Club. First-innings totals only,
# under the full-first-innings filter (no D/L, no no-result, chase target not
# set under 20 overs) — the same filter the cold open uses for avg first
# innings, stated in every definition (200+ counts shift +-1 with it).
CH4_THRESHOLDS = (180, 200, 220, 250)
CH4_DEFENDED_FLOOR = 230        # the "big total" bar for the defended-record beat
CH4_VENUE_MIN_SEASON = 3        # min first innings at a venue in a season to enter the ANOVA
CH4_VENUE_MIN_ERA = 6           # min first innings at a venue in an era for a cone / payoff strand
CH4_PAR_MIN_N = 8               # min decided-full first innings to fit a logistic par
CH4_HIST_LO, CH4_HIST_HI, CH4_HIST_W = 60, 300, 10  # ridgeline histogram bins
CH4_PP_LAST_OVER = 5            # powerplay = overs 1-6 -> 0-based over index 0..5

# Franchise home grounds (canonical). The five WPL franchises tour rotating
# neutral venues (no fixed home ground yet) and get the designed rotating-home
# payoff instead of a home-tide card — itself the chapter's WPL point.
FRANCHISE_HOME_GROUND = {
    "Chennai Super Kings": "MA Chidambaram Stadium, Chennai",
    "Delhi Capitals": "Arun Jaitley Stadium, Delhi",
    "Gujarat Titans": "Narendra Modi Stadium, Ahmedabad",
    "Kolkata Knight Riders": "Eden Gardens, Kolkata",
    "Lucknow Super Giants": "Ekana Cricket Stadium, Lucknow",
    "Mumbai Indians": "Wankhede Stadium, Mumbai",
    "Punjab Kings": "Maharaja Yadavindra Singh Stadium, Mullanpur",
    "Rajasthan Royals": "Sawai Mansingh Stadium, Jaipur",
    "Royal Challengers Bengaluru": "M Chinnaswamy Stadium, Bengaluru",
    "Sunrisers Hyderabad": "Rajiv Gandhi International Stadium, Hyderabad",
}

# Authored, illustrative "typical reader sketch" of 200+ totals per season — the
# no-sketch fallback for the cold-open callback (a reader who skipped drawing,
# arrived by shared link, or returned in a later session sees "here is roughly
# what most readers drew"). 2008-2012 are the cold open's PRE-DRAWN anchor
# (the real counts, per the You-Draw-It device); 2013-2026 is a documented
# gentle ramp off the 2012 anchor (about +1.6 a season), the shape a weak fan
# intuition produces — deliberately far under the real explosion to 65. Clearly
# labelled authored; never presented as data about reality.
AUTHORED_READER_SKETCH_200S = {
    2008: 11, 2009: 1, 2010: 9, 2011: 5, 2012: 5,
    2013: 7, 2014: 8, 2015: 10, 2016: 11, 2017: 13, 2018: 15,
    2019: 16, 2020: 18, 2021: 20, 2022: 21, 2023: 23, 2024: 24,
    2025: 26, 2026: 27,
}


def build_ch4(data_root: Path = canon.DATA_ROOT) -> dict:
    """The one corpus pass for Chapter 4's scoring-environment aggregates."""
    first_full = defaultdict(list)          # (lg, ss) -> [full first-innings totals]
    first_decided = defaultdict(list)       # (lg, ss) -> [(total, batfirst_win, season)]
    first_rpo = defaultdict(lambda: [0, 0])  # (lg, ss) -> [first-innings runs, legal balls]
    any200 = defaultdict(int)               # (lg, ss) -> innings (either) totalling >= 200
    pp_era = {k: [0, 0, 0] for k in BAND_KEYS}   # era -> [pp runs, pp legal balls, pp wickets]
    pp_season = defaultdict(lambda: [0, 0, 0])   # (lg, ss) -> [pp runs, pp legal, pp wickets]
    over_rpo = defaultdict(lambda: [0, 0])  # (lg, ss, over 1..20) -> [runs, legal balls]
    venue_season = defaultdict(list)        # (lg, venue, ss) -> [full first-innings totals]
    record_events = {"ipl": [], "wpl": []}  # league -> chronological record dicts
    running_max = {"ipl": 0, "wpl": 0}

    for _date, _mid, league, path in flatten.sorted_match_files(data_root):
        with open(path) as fh:
            match = json.load(fh)
        info = match["info"]
        season = canon.canon_season(info)
        venue = canon.canon_venue(info["venue"])
        outcome = info.get("outcome", {})
        winner = outcome.get("winner")
        winner_canon = canon.canon_team(winner) if winner else None
        result = outcome.get("result")
        decided = bool(winner) and result not in ("tie", "no result")
        teams = [canon.canon_team(t) for t in info["teams"]]

        innings_no = 0
        first_total = first_bat = None
        second_target_lt20 = False
        for innings in match.get("innings", []):
            if canon.is_super_over(innings):
                continue
            innings_no += 1
            if innings_no == 2:
                tgt = innings.get("target") or {}
                ov = tgt.get("overs")
                if ov is not None and float(ov) < 20:
                    second_target_lt20 = True
            bat = canon.canon_team(innings["team"])
            pp_overs = set()
            for pp in innings.get("powerplays", []):
                if pp.get("type") == "mandatory":
                    pp_overs.update(
                        range(int(math.floor(pp["from"])), int(math.floor(pp["to"])) + 1)
                    )
            runs_total = 0
            for over in innings["overs"]:
                ono = over["over"]  # 0-based over index
                in_pp = (ono in pp_overs) if pp_overs else (ono <= CH4_PP_LAST_OVER)
                for dl in over["deliveries"]:
                    ex = dl.get("extras", {})
                    legal = not ("wides" in ex or "noballs" in ex)
                    rt = dl["runs"]["total"]
                    runs_total += rt
                    n_wkts = sum(
                        1 for w in dl.get("wickets", []) if w["kind"] not in RETIRED_KINDS
                    )
                    if ono < 20:
                        cell = over_rpo[(league, season, ono + 1)]
                        cell[0] += rt
                        if legal:
                            cell[1] += 1
                    if innings_no == 1:
                        first_rpo[(league, season)][0] += rt
                        if legal:
                            first_rpo[(league, season)][1] += 1
                    if in_pp:
                        e = band_key(league, season)
                        ps = pp_season[(league, season)]
                        pp_era[e][0] += rt
                        ps[0] += rt
                        if legal:
                            pp_era[e][1] += 1
                            ps[1] += 1
                        pp_era[e][2] += n_wkts
                        ps[2] += n_wkts
            if runs_total >= 200:
                any200[(league, season)] += 1
            if innings_no == 1:
                first_total = runs_total
                first_bat = bat

        full = (
            not canon.is_dl(info)
            and result != "no result"
            and not second_target_lt20
            and first_total is not None
        )
        if full:
            first_full[(league, season)].append(first_total)
            venue_season[(league, venue, season)].append(first_total)
            if decided:
                first_decided[(league, season)].append(
                    (first_total, 1 if winner_canon == first_bat else 0, season)
                )
            if first_total > running_max[league]:
                running_max[league] = first_total
                opponent = next((t for t in teams if t != first_bat), "?")
                record_events[league].append(
                    {
                        "date": str(info["dates"][0]),
                        "season": season,
                        "total": first_total,
                        "team": first_bat,
                        "opponent": opponent,
                        "venue": venue,
                        "city": canon.GROUND_CITY[venue],
                    }
                )

    return {
        "first_full": first_full,
        "first_decided": first_decided,
        "first_rpo": first_rpo,
        "any200": any200,
        "pp_era": pp_era,
        "pp_season": pp_season,
        "over_rpo": over_rpo,
        "venue_season": venue_season,
        "record_events": record_events,
    }


# --- Chapter 4 sections ---------------------------------------------------


def _exceedance_curve(totals) -> dict:
    n = len(totals)
    return {
        "n": n,
        "max": max(totals) if totals else None,
        "exceedance_pct": {
            str(t): round(100.0 * sum(1 for x in totals if x >= t) / n, 1)
            for t in CH4_THRESHOLDS
        }
        if n
        else {},
        "exceedance_count": {
            str(t): sum(1 for x in totals if x >= t) for t in CH4_THRESHOLDS
        },
    }


def exceedance_section(first_full) -> dict:
    by_season = {"ipl": {}, "wpl": {}}
    for (lg, ss), totals in first_full.items():
        by_season[lg][str(ss)] = _exceedance_curve(totals)
    by_era = {}
    for lg, label, lo, hi in ERA_BANDS:
        pooled = [x for s in range(lo, hi + 1) for x in first_full.get((lg, s), [])]
        by_era[f"{lg} {label}"] = _exceedance_curve(pooled)
    return {
        "definition": (
            "P(first innings >= X), full-first-innings filter (no D/L, no "
            "no-result, chase target not set under 20 overs). The 200 Club is "
            "X = 200; 180 / 220 / 250 are the ridgeline's other light beams."
        ),
        "thresholds": list(CH4_THRESHOLDS),
        "by_season": by_season,
        "by_era": by_era,
        "cliff": {
            "before": {
                "season": 2022,
                "p200": by_season["ipl"]["2022"]["exceedance_pct"]["200"],
            },
            "after": {
                "season": 2023,
                "p200": by_season["ipl"]["2023"]["exceedance_pct"]["200"],
            },
            "era_before": {
                "era": "ipl 2020-2022",
                "p200": by_era["ipl 2020-2022"]["exceedance_pct"]["200"],
            },
            "era_after": {
                "era": "ipl 2023-2026",
                "p200": by_era["ipl 2023-2026"]["exceedance_pct"]["200"],
            },
            "note": (
                "For fifteen years about one first innings in ten passed 200. "
                "In 2023 it jumped to two in five, and it has stayed there."
            ),
        },
    }


def _fit_logistic(rows):
    """Newton-Raphson fit of P(bat-first win) ~ total, centred. Returns
    (intercept, slope, mean_total) or None (too few rows, or slope <= 0)."""
    if len(rows) < CH4_PAR_MIN_N:
        return None
    xs = [r[0] for r in rows]
    ys = [r[1] for r in rows]
    mx = sum(xs) / len(xs)
    X = [x - mx for x in xs]
    a = b = 0.0
    for _ in range(100):
        g0 = g1 = h00 = h01 = h11 = 0.0
        for xi, yi in zip(X, ys):
            z = max(-30.0, min(30.0, a + b * xi))
            p = 1.0 / (1.0 + math.exp(-z))
            w = max(p * (1.0 - p), 1e-9)
            g0 += p - yi
            g1 += (p - yi) * xi
            h00 += w
            h01 += w * xi
            h11 += w * xi * xi
        det = h00 * h11 - h01 * h01
        if abs(det) < 1e-12:
            break
        da = (h11 * g0 - h01 * g1) / det
        db = (h00 * g1 - h01 * g0) / det
        a -= da
        b -= db
        if abs(da) < 1e-10 and abs(db) < 1e-10:
            break
    if b <= 0:
        return None
    return (a, b, mx)


def _par_at(fit, q):
    a, b, mx = fit
    return mx + (math.log(q / (1.0 - q)) - a) / b


def par_drift_section(first_decided) -> dict:
    by_era = {}
    for lg, label, lo, hi in ERA_BANDS:
        rows = [r for s in range(lo, hi + 1) for r in first_decided.get((lg, s), [])]
        fit = _fit_logistic(rows)
        by_era[f"{lg} {label}"] = {
            "n": len(rows),
            "par": r1(_par_at(fit, 0.50)) if fit else None,
            "safe": r1(_par_at(fit, 0.75)) if fit else None,
            "dead": r1(_par_at(fit, 0.25)) if fit else None,
        }
    # Per-season par for the waterline: a 3-season centred-window logistic (the
    # honest lookup form of the catalog's season spline; single-season fits are
    # too noisy). Edge seasons pool the neighbours that exist.
    by_season_windowed = {"ipl": {}, "wpl": {}}
    for lg in ("ipl", "wpl"):
        seasons = canon.IPL_SEASONS if lg == "ipl" else canon.WPL_SEASONS
        for s in seasons:
            rows = []
            for ss in (s - 1, s, s + 1):
                rows += first_decided.get((lg, ss), [])
            fit = _fit_logistic(rows)
            if fit:
                by_season_windowed[lg][str(s)] = r1(_par_at(fit, 0.50))
    # The big-total defended record (2023-26). The old "230+ = 11/11" claim is
    # stale: 230+ is now routine, and even 230+ gets chased. Emit the true
    # record so the scene never shows a number the pixels contradict.
    big = [
        r
        for s in range(2023, 2027)
        for r in first_decided.get(("ipl", s), [])
        if r[0] >= CH4_DEFENDED_FLOOR
    ]
    posted = len(big)
    defended = sum(r[1] for r in big)
    chased = sorted(
        ({"season": r[2], "total": r[0]} for r in big if r[1] == 0),
        key=lambda d: (d["season"], d["total"]),
    )
    return {
        "definition": (
            "Par = the first-innings total that wins exactly half the time — "
            "the score a good team would be on. Logistic P(bat-first win) ~ "
            "total, fit per era on decided full-first-innings matches; par is "
            "the total at P = 0.5, safe at 0.75, dead at 0.25."
        ),
        "by_era": by_era,
        "by_season_windowed": by_season_windowed,
        "totals_230plus": {
            "floor": CH4_DEFENDED_FLOOR,
            "era": "ipl 2023-2026",
            "posted": posted,
            "defended": defended,
            "chased_down": posted - defended,
            "defended_pct": round(100.0 * defended / posted, 1) if posted else None,
            "chased_list": chased,
            "note": (
                "A score of 230 used to be almost unheard of. In 2023 to 2026 "
                "teams posted it {p} times and still lost {c} of them."
            ).format(p=posted, c=posted - defended),
        },
    }


def record_halflife_section(record_events) -> dict:
    from datetime import date

    def progression(events):
        out = []
        for i, e in enumerate(events):
            nxt = events[i + 1]["date"] if i + 1 < len(events) else None
            span = (
                (date.fromisoformat(nxt) - date.fromisoformat(e["date"])).days
                if nxt
                else None
            )
            out.append({**e, "stood_days": span, "standing": span is None})
        return out

    ipl = progression(record_events["ipl"])
    wpl = progression(record_events["wpl"])
    ticker = {"ipl": {}, "wpl": {}}
    for lg, evs in (("ipl", record_events["ipl"]), ("wpl", record_events["wpl"])):
        seasons = canon.IPL_SEASONS if lg == "ipl" else canon.WPL_SEASONS
        for s in seasons:
            standing = None
            for e in evs:
                if e["season"] <= s:
                    standing = e
            if standing:
                ticker[lg][str(s)] = {
                    "total": standing["total"],
                    "team": standing["team"],
                    "since_season": standing["season"],
                }
    return {
        "definition": (
            "The standing highest first-innings total, replayed match by match; "
            "each record's lifespan is the days until the next one broke it."
        ),
        "ipl_progression": ipl,
        "wpl_progression": wpl,
        "ticker": ticker,
        "stationary_environment_null": (
            "Records get monotonically harder to break, so in a still, "
            "unchanging scoring world each new record should stand LONGER than "
            "the last. The opposite happened: the highest-total record stood "
            "3,991 days and then fell twice in 19 days. Falling records that "
            "speed up instead of slowing down are direct evidence the water "
            "level itself moved."
        ),
    }


def _pp_rates(rec):
    runs, legal, wk = rec
    return {
        "run_rate": round(6.0 * runs / legal, 2) if legal else None,
        "wickets_per_36": round(36.0 * wk / legal, 2) if legal else None,
        "legal_balls": legal,
    }


def powerplay_section(pp_era, pp_season) -> dict:
    by_era = {k: _pp_rates(v) for k, v in pp_era.items()}
    by_season = {"ipl": {}, "wpl": {}}
    for (lg, ss), rec in pp_season.items():
        by_season[lg][str(ss)] = _pp_rates(rec)
    early = by_era["ipl 2008-2010"]
    late = by_era["ipl 2023-2026"]
    return {
        "definition": (
            "The powerplay is the first six overs, when only two fielders may "
            "stand out deep. Run rate and wickets lost per 36 balls, per "
            "season and per era."
        ),
        "by_era": by_era,
        "by_season": by_season,
        "equal_wicket_cost": {
            "early_rr": early["run_rate"],
            "late_rr": late["run_rate"],
            "early_wickets_per_36": early["wickets_per_36"],
            "late_wickets_per_36": late["wickets_per_36"],
            "note": (
                "Powerplay scoring climbed from {er} to {lr} runs an over. "
                "Teams paid the same in wickets: {ew} then {lw} per 36 balls. "
                "The extra runs came free."
            ).format(
                er=early["run_rate"],
                lr=late["run_rate"],
                ew=early["wickets_per_36"],
                lw=late["wickets_per_36"],
            ),
        },
    }


def _venue_era_totals(venue_season):
    """(league, venue) -> era key -> [full first-innings totals]."""
    out = defaultdict(lambda: defaultdict(list))
    for (lg, v, ss), totals in venue_season.items():
        for lg2, label, lo, hi in ERA_BANDS:
            if lg2 == lg and lo <= ss <= hi:
                out[(lg, v)][f"{lg2} {label}"].extend(totals)
                break
    return out


def venue_section(venue_season) -> dict:
    # Between-venue variance share: per season, the one-way ANOVA share of
    # first-innings-total variance explained by which ground it was, then
    # averaged over the era's seasons (per-season controls for the year's
    # scoring inflation; pooling a whole era instead lets 2009's South-Africa
    # exile and neutral seasons masquerade as venue effect).
    variance = {}
    for lg, label, lo, hi in IPL_ERA_BANDS:
        shares = []
        for s in range(lo, hi + 1):
            byv = {
                v: totals
                for (l, v, ss), totals in venue_season.items()
                if l == lg and ss == s and len(totals) >= CH4_VENUE_MIN_SEASON
            }
            allv = [x for t in byv.values() for x in t]
            if len(byv) >= 3 and len(allv) >= 2:
                gm = sum(allv) / len(allv)
                sst = sum((x - gm) ** 2 for x in allv)
                if sst > 0:
                    ssb = sum(
                        len(t) * ((sum(t) / len(t)) - gm) ** 2 for t in byv.values()
                    )
                    shares.append(100.0 * ssb / sst)
        variance[f"{lg} {label}"] = {
            "between_venue_share_pct": round(sum(shares) / len(shares), 1)
            if shares
            else None,
            "seasons": len(shares),
        }
    # Per-venue typical first-innings total by era: the divergence-cone strands
    # and the home-ground payoff (Chinnaswamy the flood plain vs Chepauk holding
    # its character). Only cells with enough matches ship.
    vet = _venue_era_totals(venue_season)
    strands = []
    for (lg, v), eras in vet.items():
        by_era = {
            e: {"avg_first_innings": r1(sum(t) / len(t)), "n": len(t)}
            for e, t in eras.items()
            if len(t) >= CH4_VENUE_MIN_ERA
        }
        if by_era:
            strands.append(
                {
                    "league": lg,
                    "venue": v,
                    "city": canon.GROUND_CITY[v],
                    "by_era": by_era,
                }
            )
    strands.sort(key=lambda d: (d["league"], d["venue"]))

    def latest(vname):
        cell = vet.get(("ipl", vname), {}).get("ipl 2023-2026", [])
        return r1(sum(cell) / len(cell)) if cell else None

    return {
        "definition": (
            "Between-venue share = how much of a season's spread in first-"
            "innings totals is explained by which ground it was (one-way "
            "ANOVA), averaged across the era. A venue's tide = its typical "
            "first-innings total (mean, full first innings)."
        ),
        "between_venue_variance": variance,
        "strands": strands,
        "fingerprint_2023_2026": {
            "chinnaswamy": latest("M Chinnaswamy Stadium, Bengaluru"),
            "chepauk": latest("MA Chidambaram Stadium, Chennai"),
            "note": (
                "The flat-pitch era did not flatten the country. Grounds are "
                "pulling apart, not together."
            ),
        },
    }


def phase_heatmap_section(over_rpo) -> dict:
    grid = {"ipl": {}, "wpl": {}}
    for (lg, ss, ovr), (runs, legal) in over_rpo.items():
        row = grid[lg].setdefault(str(ss), [None] * 20)
        row[ovr - 1] = round(6.0 * runs / legal, 2) if legal else None
    # Per-era phase RPO (pp = overs 1-6, middle 7-15, death 16-20) and the
    # death-minus-powerplay spread (the demoted Phase Economy Map footnote).
    phase = {}
    for lg, label, lo, hi in ERA_BANDS:
        acc = {"pp": [0, 0], "middle": [0, 0], "death": [0, 0]}
        for (l, ss, ovr), (runs, legal) in over_rpo.items():
            if l != lg or not (lo <= ss <= hi):
                continue
            ph = "pp" if ovr <= 6 else ("middle" if ovr <= 15 else "death")
            acc[ph][0] += runs
            acc[ph][1] += legal
        rr = {
            ph: round(6.0 * r / b, 2) if b else None for ph, (r, b) in acc.items()
        }
        spread = (
            round(rr["death"] - rr["pp"], 2)
            if rr["death"] is not None and rr["pp"] is not None
            else None
        )
        phase[f"{lg} {label}"] = {**rr, "death_minus_pp": spread}
    return {
        "definition": (
            "Run rate over by over (1 to 20), per season. Watch the powerplay "
            "corner, overs 1 to 6, catch fire decade by decade."
        ),
        "by_over": grid,
        "phase_rpo_by_era": phase,
    }


def cpi_section(first_rpo, any200) -> dict:
    rpo_season = {"ipl": {}, "wpl": {}}
    for (lg, ss), (runs, legal) in first_rpo.items():
        rpo_season[lg][str(ss)] = round(6.0 * runs / legal, 2) if legal else None

    def era_rpo(lg, lo, hi):
        r = b = 0
        for s in range(lo, hi + 1):
            rr, bb = first_rpo.get((lg, s), [0, 0])
            r += rr
            b += bb
        return (6.0 * r / b) if b else None

    base = era_rpo("ipl", 2008, 2010)
    by_era = {}
    for lg, label, lo, hi in ERA_BANDS:
        val = era_rpo(lg, lo, hi)
        by_era[f"{lg} {label}"] = {
            "first_innings_rpo": round(val, 2) if val else None,
            "index": round(100.0 * val / base) if val else None,
        }
    truth = {str(s): any200.get(("ipl", s), 0) for s in canon.IPL_SEASONS}
    return {
        "definition": (
            "First-innings run rate per season (runs an over, wides and "
            "no-balls out of the denominator), indexed to a 2008-2010 base "
            "of 100 — the site-wide deflator that turns 'is 180 good?' into a "
            "real question."
        ),
        "first_innings_rpo_by_season": rpo_season,
        "by_era": by_era,
        "index_base": "ipl 2008-2010",
        "callback_sketch": {
            "definition": (
                "The cold open asked you to draw 200-run innings per season. "
                "This brings your line back. truth = the real count (either "
                "innings passing 200, the cold-open definition); "
                "authored_typical = the no-sketch fallback line, an "
                "illustrative 'here is roughly what most readers drew', not "
                "data about reality."
            ),
            "truth_200s_by_season": truth,
            "authored_typical_200s_by_season": {
                str(s): AUTHORED_READER_SKETCH_200S[s] for s in canon.IPL_SEASONS
            },
        },
    }


def columns_section(first_full, par_waterline) -> dict:
    bins = list(range(CH4_HIST_LO, CH4_HIST_HI, CH4_HIST_W))
    hist = {"ipl": {}, "wpl": {}}
    dist = {"ipl": {}, "wpl": {}}
    for (lg, ss), totals in first_full.items():
        counts = [0] * len(bins)
        for x in totals:
            idx = min(max((x - CH4_HIST_LO) // CH4_HIST_W, 0), len(bins) - 1)
            counts[idx] += 1
        hist[lg][str(ss)] = counts
        s = sorted(totals)
        dist[lg][str(ss)] = {
            "n": len(s),
            "mean": r1(sum(s) / len(s)),
            "median": s[len(s) // 2],
            "min": s[0],
            "max": s[-1],
        }
    return {
        "definition": (
            "The waterline morph: every ball stacks into its innings-total "
            "column (from innings_total.u8), rows are seasons (group_ids), and "
            "the par waterline climbs the wall, drowning totals that used to be "
            "safe. The histogram is the milestone ridgeline; par_waterline is "
            "the per-season climbing line (3-season-window logistic par)."
        ),
        "histogram": {"bin_lo": CH4_HIST_LO, "bin_width": CH4_HIST_W, "bins": bins, "counts": hist},
        "distribution": dist,
        "par_waterline": par_waterline,
    }


def wpl_beat_ch4_section(first_full, any200, exceedance) -> dict:
    avg_first = {}
    for s in canon.WPL_SEASONS:
        totals = first_full.get(("wpl", s), [])
        if totals:
            avg_first[str(s)] = r1(sum(totals) / len(totals))
    wpl_200s = {str(s): any200.get(("wpl", s), 0) for s in canon.WPL_SEASONS}
    # Where the WPL 200 Club sits on the IPL calendar (two-clock beat). The
    # catalog's anchors are IPL 2008 and 2015 (the early-era band); the WPL's
    # pooled P(200) lands between them.
    wpl_p200 = exceedance["by_era"]["wpl 2023-2026"]["exceedance_pct"].get("200")
    ipl_p200 = {
        s: exceedance["by_season"]["ipl"][str(s)]["exceedance_pct"]["200"]
        for s in canon.IPL_SEASONS
    }
    reference = {str(s): ipl_p200[s] for s in (2008, 2015)}

    def league_year_avg(lg, founding):
        out = {}
        seasons = canon.IPL_SEASONS if lg == "ipl" else canon.WPL_SEASONS
        for s in seasons:
            totals = first_full.get((lg, s), [])
            if totals:
                out[str(s - founding + 1)] = r1(sum(totals) / len(totals))
        return out

    return {
        "framing": (
            "Beside the path, not behind it. On the calendar clock the WPL's "
            "200 Club sits between IPL 2008 and 2015. On the league-age clock "
            "its tide is rising faster than the IPL's did, and rising along "
            "the ground, four-led, not over the rope."
        ),
        "avg_first_innings_by_season": avg_first,
        "totals_200_by_season": wpl_200s,
        "exceedance_p200": wpl_p200,
        "sits_between_ipl_seasons": {
            "seasons": [2015, 2008],
            "ipl_p200": reference,
            "wpl_p200": wpl_p200,
        },
        "maturity_clock": {
            "definition": "Average first innings by league year (season 1 = founding).",
            "ipl_by_league_year": league_year_avg("ipl", 2008),
            "wpl_by_league_year": league_year_avg("wpl", 2023),
        },
    }


def _venue_home_card(team, league, vet, league_era_avg):
    venue = FRANCHISE_HOME_GROUND[team]
    eras = vet.get(("ipl", venue), {})
    by_era = []
    for lg, label, lo, hi in IPL_ERA_BANDS:
        totals = eras.get(f"{lg} {label}", [])
        by_era.append(
            {
                "era": label,
                "avg_first_innings": r1(sum(totals) / len(totals))
                if len(totals) >= CH4_VENUE_MIN_ERA
                else None,
                "n": len(totals),
            }
        )
    available = [row for row in by_era if row["avg_first_innings"] is not None]
    latest_era = by_era[-1]["avg_first_innings"]  # the 2023-26 tide (or None)
    league_latest = league_era_avg["ipl 2023-2026"]
    city = canon.GROUND_CITY[venue]
    # Fingerprint = did the water rise HERE? Chepauk barely moved (holds its
    # character); Chinnaswamy, Wankhede, Eden climbed 25-50 runs (flood plains).
    rise = (
        available[-1]["avg_first_innings"] - available[0]["avg_first_innings"]
        if len(available) >= 2
        else None
    )
    if not available:
        fingerprint = "empty"
    elif latest_era is None:
        fingerprint = "gone_quiet"
    elif len(available) == 1:
        fingerprint = "new_ground"
    elif rise >= 15:
        fingerprint = "flood_plain"
    elif rise <= 8:
        fingerprint = "holds_character"
    else:
        fingerprint = "in_the_pack"
    fp_copy = {
        "flood_plain": "Your home ground is the flood plain. The water rose here more than almost anywhere.",
        "holds_character": "Your home ground keeps its character while the rest inflate.",
        "in_the_pack": "Your home ground rode the tide up with the pack.",
        "new_ground": "A new home, still writing its story. Here is what it reads now.",
        "gone_quiet": "Your old fortress has gone quiet in the flood era. The team moved on.",
        "empty": "Not enough games at this ground yet.",
    }[fingerprint]
    if latest_era is not None:
        headline = (
            "{team} at home in {city}: a typical first innings of {latest} in "
            "2023 to 2026, against a league average of {lg}."
        ).format(team=team, city=city, latest=latest_era, lg=league_latest)
    else:
        headline = (
            "{team}'s home in {city} has thin recent data. Here is its tide "
            "through the eras it did host."
        ).format(team=team, city=city)
    return {
        "team": team,
        "league": league,
        "empty_state": latest_era is None,
        "home_ground": venue,
        "home_city": city,
        "par_by_era": by_era,
        "latest_avg_first_innings": latest_era,
        "league_latest_avg_first_innings": league_latest,
        "rise_first_to_latest": r1(rise) if rise is not None else None,
        "fingerprint": fingerprint,
        "headline": headline,
        "fingerprint_copy": fp_copy,
    }


def ch4_payoff_section(venue_season, first_full) -> dict:
    vet = _venue_era_totals(venue_season)
    league_era_avg = {}
    for lg, label, lo, hi in ERA_BANDS:
        pooled = [x for s in range(lo, hi + 1) for x in first_full.get((lg, s), [])]
        league_era_avg[f"{lg} {label}"] = r1(sum(pooled) / len(pooled)) if pooled else None

    variants = []
    for team in canon.CURRENT_IPL_FRANCHISES:
        variants.append(_venue_home_card(team, "ipl", vet, league_era_avg))

    wpl_avg = {}
    for s in canon.WPL_SEASONS:
        totals = first_full.get(("wpl", s), [])
        if totals:
            wpl_avg[str(s)] = r1(sum(totals) / len(totals))
    for team in canon.WPL_FRANCHISES:
        variants.append(
            {
                "team": team,
                "league": "wpl",
                "empty_state": True,
                "home_ground": None,
                "rotating_home": True,
                "league_avg_first_innings_by_season": wpl_avg,
                "headline": (
                    "The WPL has no home ground yet. It tours. But the tide is "
                    "already rising under it: your league's first innings went "
                    "from 157 to 169 in four seasons."
                ),
                "fingerprint_copy": (
                    "A young league, still finding its grounds. Its flood is "
                    "along the ground, four-led, not over the rope."
                ),
            }
        )

    # Neutral: the all-India map summary — every franchise home ground's current
    # tide, sorted highest first.
    india_map = []
    for team in canon.CURRENT_IPL_FRANCHISES:
        venue = FRANCHISE_HOME_GROUND[team]
        cell = vet.get(("ipl", venue), {}).get("ipl 2023-2026", [])
        india_map.append(
            {
                "team": team,
                "venue": venue,
                "city": canon.GROUND_CITY[venue],
                "avg_first_innings": r1(sum(cell) / len(cell)) if cell else None,
                "n": len(cell),
            }
        )
    india_map.sort(
        key=lambda d: (-(d["avg_first_innings"] or -1), d["venue"])
    )
    variants.append(
        {
            "team": "neutral",
            "league": "neutral",
            "empty_state": False,
            "home_ground": None,
            "india_map": india_map,
            "headline": (
                "The whole map of India. Some grounds are flood plains now, "
                "some hold the line. Tap a ground to feel its tide."
            ),
        }
    )
    return {
        "card": "your-home-grounds-tide",
        "eras": {"ipl": [f"{lo}-{hi}" for _lg, _l, lo, hi in IPL_ERA_BANDS]},
        "variants": variants,
    }


def footnotes4_section() -> dict:
    return {
        "par_model": (
            "Par is a logistic fit of P(the team batting first wins) against "
            "their total, on decided matches with a full first innings (no "
            "D/L, no no-result, chase not curtailed under 20 overs). Par is the "
            "total at 50%, safe at 75%, dead at 25%. Per-season par uses a "
            "3-season window so small samples borrow strength."
        ),
        "full_first_innings_filter": (
            "First-innings scoring stats use full innings only. The 200-plus "
            "count shifts by about one either way depending on exactly where "
            "you draw that line."
        ),
        "venue_canonicalization": (
            "About sixty raw ground spellings collapse to their real venue "
            "before any venue stat (Chinnaswamy appears under three spellings; "
            "Chepauk under three). Rebuilt stadiums keep one identity."
        ),
        "record_null": (
            "Record lifespans need a stationary-environment yardstick because "
            "records get harder to break over time on their own. See "
            "record_halflife.stationary_environment_null."
        ),
        "phase_economy_map": (
            "Demoted from the main flow: the innings went phase-agnostic. The "
            "gap between death-over and powerplay run rates compressed as the "
            "powerplay caught up. See phase_heatmap.phase_rpo_by_era."
        ),
    }


def ch4_doc(acc4) -> dict:
    first_full = acc4["first_full"]
    first_decided = acc4["first_decided"]
    exceedance = exceedance_section(first_full)
    par = par_drift_section(first_decided)
    columns = columns_section(first_full, par["by_season_windowed"]["ipl"])
    return {
        "chapter": 4,
        "title": "The Rising Tide",
        "register": "the ground itself moves",
        "era_bands": band_meta(),
        "mystery": {
            "hold": (
                "Something snapped in 2023. Hold that thought. The answer is "
                "three chapters away."
            ),
            "note": (
                "The chapter shows the 2023 cliff in full and refuses to "
                "explain it here. Chapter 7 gives the partial answer, Chapter "
                "10 the verdict."
            ),
        },
        "exceedance": exceedance,
        "par_drift": par,
        "record_halflife": record_halflife_section(acc4["record_events"]),
        "powerplay": powerplay_section(acc4["pp_era"], acc4["pp_season"]),
        "venues": venue_section(acc4["venue_season"]),
        "phase_heatmap": phase_heatmap_section(acc4["over_rpo"]),
        "cpi": cpi_section(acc4["first_rpo"], acc4["any200"]),
        "columns": columns,
        "wpl_beat": wpl_beat_ch4_section(first_full, acc4["any200"], exceedance),
        "payoff": ch4_payoff_section(acc4["venue_season"], first_full),
        "footnotes": footnotes4_section(),
        "innings_total_buffer": {
            "file": "innings_total.u8",
            "bytes_per_point": 1,
            "point_order": flatten.POINT_ORDER,
            "byte0": "innings total (quantized) of the innings this ball is in",
            "scale": flatten.INNINGS_TOTAL_SCALE,
            "decode": "innings_total ~= byte * 2 (floor(total/2); 2-run resolution)",
            "note": (
                "Every ball of an innings carries the same byte. Season comes "
                "from group_ids.u16; the par waterline per season is "
                "columns.par_waterline. First-innings identification, if a "
                "subset-highlight needs it, comes from the columnar innings "
                "array — attrs.u8 is untouched, so R1 and R2 stay byte-"
                "identical."
            ),
        },
    }


# ---------------------------------------------------------------------------
# Emission
# ---------------------------------------------------------------------------


def main(out_root: Path = canon.OUT_ROOT) -> dict:
    bands, seasons, players, n_matches, superover_balls = build()
    coldopen = coldopen_doc(seasons, players, n_matches, superover_balls)
    ch1 = ch1_doc(bands, seasons)
    sandbox = sandbox_doc()

    acc2 = build_ch2()
    classify_anchors(acc2)
    ch2 = ch2_doc(acc2)

    acc3 = build_ch3()
    ch3 = ch3_doc(acc3)

    acc4 = build_ch4()
    ch4 = ch4_doc(acc4)

    scenes_dir = out_root / "scenes"
    scenes_dir.mkdir(parents=True, exist_ok=True)
    sizes = {}
    for name, doc in (
        ("coldopen.json", coldopen),
        ("ch1.json", ch1),
        ("sandbox.json", sandbox),
        ("ch2.json", ch2),
        ("ch3.json", ch3),
        ("ch4.json", ch4),
    ):
        raw = flatten.compact_json(doc, sort_keys=True)
        (scenes_dir / name).write_bytes(raw)
        sizes[f"scenes/{name}"] = {
            "bytes_raw": len(raw),
            "bytes_gz": len(flatten.gz_bytes(raw)),
        }

    meta_path = out_root / "meta.json"
    if meta_path.exists():
        meta = json.loads(meta_path.read_text())
        meta["files"].update(sizes)
        # meta.json v2 (storyboard CO-3 count traceability): every title-card
        # count traces to an artifact — n_players (faced-or-bowled registry
        # ids) and per-league match counts, consistent by construction with
        # scenes/coldopen.json's corpus block (same pass, same definitions).
        meta["n_players"] = len(players)
        n_ipl = sum(seasons[("ipl", s)].matches for s in canon.IPL_SEASONS)
        n_wpl = sum(seasons[("wpl", s)].matches for s in canon.WPL_SEASONS)
        meta["n_matches"] = {"ipl": n_ipl, "wpl": n_wpl, "total": n_ipl + n_wpl}
        meta_path.write_bytes(flatten.compact_json(meta))

    for name, s in sizes.items():
        print(f"  {name:22s} raw={s['bytes_raw']:>9,}  gz={s['bytes_gz']:>8,}")
    co = coldopen["corpus"]
    print(
        f"coldopen: points={co['points_rendered']:,} corpus={co['corpus_total']:,} "
        f"players={co['players']} matches={co['matches']}"
    )
    f10 = ch1["outrate"]["first10"]
    print(
        "ch1 first10 hazard: ipl 2008-2010 "
        f"{f10['ipl 2008-2010']['hazard_pct']}% -> ipl 2023-2026 "
        f"{f10['ipl 2023-2026']['hazard_pct']}%"
    )
    p = sandbox["preset"]
    print(f"sandbox preset: match_index={p['match_index']} — {p['label']}")
    tf = sandbox["tourFlags"]
    print(
        f"sandbox tourFlags: {len(tf)} flags, counts "
        + "/".join(str(f["count"]) for f in tf)
    )
    ab = ch2["anchor"]["bands"]
    ar = ch2["archetype"]["bands"]
    n_empty = sum(1 for v in ch2["payoff"]["variants"] if v["empty_state"])
    print(
        "ch2 anchor-ball share: ipl 2008-2010 "
        f"{ab['ipl 2008-2010']['anchor_ball_share_pct']}% -> ipl 2023-2026 "
        f"{ab['ipl 2023-2026']['anchor_ball_share_pct']}% (wpl "
        f"{ab['wpl 2023-2026']['anchor_ball_share_pct']}%)"
    )
    print(
        "ch2 sub-120 batter-seasons: ipl 2008-2010 "
        f"{ar['ipl 2008-2010']['sub120_share_pct']}% -> ipl 2023-2026 "
        f"{ar['ipl 2023-2026']['sub120_share_pct']}% (wpl "
        f"{ar['wpl 2023-2026']['sub120_share_pct']}%)"
    )
    print(f"ch2 payoff: 16 variants, {n_empty} designed empty state(s)")
    u7 = ch3["frontier"]["under7"]["era_bands"]
    dna = ch3["dismissal_dna"]["era_bands"]
    dw = ch3["death_wide_tax"]["era_headline"]
    print(
        "ch3 economy under 7: ipl 2008-2010 "
        f"{u7['ipl 2008-2010']['pct']}% ({u7['ipl 2008-2010']['under7']}/"
        f"{u7['ipl 2008-2010']['qualifiers']}) -> ipl 2023-2026 "
        f"{u7['ipl 2023-2026']['pct']}% ({u7['ipl 2023-2026']['under7']}/"
        f"{u7['ipl 2023-2026']['qualifiers']})"
    )
    print(
        "ch3 dismissal DNA (bowled+lbw / caught / stumped): ipl 2008-2010 "
        f"{dna['ipl 2008-2010']['bowled_lbw_pct']}/{dna['ipl 2008-2010']['caught_pct']}/"
        f"{dna['ipl 2008-2010']['stumped_pct']} -> ipl 2023-2026 "
        f"{dna['ipl 2023-2026']['bowled_lbw_pct']}/{dna['ipl 2023-2026']['caught_pct']}/"
        f"{dna['ipl 2023-2026']['stumped_pct']}"
    )
    print(
        f"ch3 death wides/100: ipl {dw['ipl_2008_2010']} -> {dw['ipl_2023_2026']} "
        f"(x{dw['doubling_factor']}), wpl {dw['wpl_2023_2026']}"
    )
    cr = ch3["crack_ratio"]["era_bands"]
    print(
        f"ch3 crack ratio: wpl {cr['wpl 2023-2026']['crack_ratio']} vs "
        f"ipl 2023-2026 {cr['ipl 2023-2026']['crack_ratio']}"
    )
    gd = ch3["gravity_defiers"]["variants"]
    print(f"ch3 gravity-defiers: {len(gd)} franchise cards")
    ex = ch4["exceedance"]["by_era"]
    pd = ch4["par_drift"]["by_era"]
    pp = ch4["powerplay"]["equal_wicket_cost"]
    vv = ch4["venues"]["between_venue_variance"]
    d230 = ch4["par_drift"]["totals_230plus"]
    n_pay = len(ch4["payoff"]["variants"])
    print(
        "ch4 P(200+): ipl 2008-2010 "
        f"{ex['ipl 2008-2010']['exceedance_pct']['200']}% -> ipl 2023-2026 "
        f"{ex['ipl 2023-2026']['exceedance_pct']['200']}% (2026 "
        f"{ch4['exceedance']['by_season']['ipl']['2026']['exceedance_pct']['200']}%)"
    )
    print(
        "ch4 par: ipl 2008-2010 "
        f"{pd['ipl 2008-2010']['par']} -> ipl 2023-2026 {pd['ipl 2023-2026']['par']}"
    )
    print(
        f"ch4 powerplay: RR {pp['early_rr']} -> {pp['late_rr']} at wickets/36 "
        f"{pp['early_wickets_per_36']} vs {pp['late_wickets_per_36']}"
    )
    print(
        "ch4 between-venue share: ipl 2008-2010 "
        f"{vv['ipl 2008-2010']['between_venue_share_pct']}% -> ipl 2023-2026 "
        f"{vv['ipl 2023-2026']['between_venue_share_pct']}%"
    )
    print(
        f"ch4 230+ defended (2023-26): {d230['defended']}/{d230['posted']} "
        f"({d230['defended_pct']}%); {n_pay} payoff variants"
    )
    return {
        "coldopen": coldopen, "ch1": ch1, "sandbox": sandbox,
        "ch2": ch2, "ch3": ch3, "ch4": ch4,
    }


if __name__ == "__main__":
    main()
