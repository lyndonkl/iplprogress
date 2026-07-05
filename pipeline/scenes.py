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

  sandbox     (R1b) the minimal-bowl descriptor: the famous-match preset
              (2019 IPL Final, MI beat CSK by 1 run — resolved by
              league+season+stage+teams+margin, never a hard-coded index),
              the TEAM + SEASON facet lists (teams.json / groups.json), and
              the tap-a-ball tooltip field roster. Team+season facets only,
              per the tightened §3 scope; everything else is R6/R7.

Era bands (R1a data contract): IPL 2008-2010, 2011-2015, 2016-2019,
2020-2022, 2023-2026; WPL pooled 2023-2026.

Stdlib only; byte-deterministic (compact JSON, sorted keys). Run after
flatten.py (updates meta.json's file ledger).
"""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import canon
import flatten
import wallheat

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
                    players.add(striker)
                    players.add(dl["bowler"])
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
PRESET_LABEL = (
    "2019 IPL Final — Mumbai Indians beat Chennai Super Kings by 1 run"
)
PRESET_BLURB = (
    "Mumbai Indians defend nine off Lasith Malinga's final over to beat "
    "Chennai Super Kings by a single run — the closest final in IPL history."
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


def sandbox_doc() -> dict:
    matches = flatten.build_matches()
    preset_index = resolve_preset(matches)
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
            "R1b minimal bowl: TEAM + SEASON facets only, one famous-match "
            "preset, tap-a-ball tooltip. League/phase/player/over/outcome "
            "facets, the linked worm/Manhattan panel, tour flags and "
            "shareable URLs are deferred to R6/R7 (blueprint §3)."
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


def _anchor_card(acc, best_key, best, matches, team, league, neutral=False):
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
        "headline": headline,
    }


def payoff_section(acc) -> dict:
    """The 16 'Your last anchor' team-picker variants (10 IPL + 5 WPL +
    neutral). Strictly template + per-team numbers; born-post-anchor sides get
    the designed empty state."""
    matches = acc["matches"]
    best = {}  # (league, team) -> the most recent qualifying anchor innings
    ipl_best = None  # the most recent IPL anchor overall (the neutral card)
    for r in acc["innings_recs"]:
        # "Your last anchor" is the archetype who HELD THE INNINGS TOGETHER —
        # a top-order (position 1-4) qualifying anchor, not a tail-end block.
        if not r["is_anchor"] or r["position"] > 4:
            continue
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
        variants.append(_anchor_card(acc, ("ipl", t), best, matches, t, "ipl"))
    for t in canon.WPL_FRANCHISES:
        variants.append(_anchor_card(acc, ("wpl", t), best, matches, t, "wpl"))
    neutral = _anchor_card(
        acc, "__neutral__", {"__neutral__": ipl_best}, matches, "Neutral", "ipl", neutral=True
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
            "recent top-order IPL anchor overall. Strictly template + per-team "
            "numbers — nothing hand-authored per team."
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

    scenes_dir = out_root / "scenes"
    scenes_dir.mkdir(parents=True, exist_ok=True)
    sizes = {}
    for name, doc in (
        ("coldopen.json", coldopen),
        ("ch1.json", ch1),
        ("sandbox.json", sandbox),
        ("ch2.json", ch2),
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
    return {"coldopen": coldopen, "ch1": ch1, "sandbox": sandbox, "ch2": ch2}


if __name__ == "__main__":
    main()
