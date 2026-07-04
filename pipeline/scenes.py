"""R1a scene aggregates — scenes/coldopen.json + scenes/ch1.json.

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
              5/10/15/20 (min 300 balls in band); (d) six democratization
              per season (>=10-six players; top-10 share over >=30-ball
              qualifiers — the catalog's 35.9% -> 28.1%); (e) the Aerial
              Risk Ledger (attempt proxy = sixes + caught excl. caught-and-
              bowled, per 100 balls faced, with the catalog's caveat text);
              (f) the WPL beat (first-10 SR, four-led run DNA, and the
              League Maturity Clock: RR = ALL runs / legal balls — wides
              AND no-balls excluded from the denominator).

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

SCENES_DIR = canon.OUT_ROOT / "scenes"

MAX_BALL_INDEX = 30  # ignition + out-rate curves cover balls-faced 1..30
DEFIER_INDICES = (5, 10, 15, 20)
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
    return {
        "sr_by_ball_index": sr_by_ball,
        "balls_by_ball_index": balls_by_ball,
        "first10_sr_by_season": first10,
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
            "For each ball index n: the batters (min 300 balls faced in the "
            "era band) who most defied the era's out-rate — score = "
            "(share of innings surviving to ball n / era survival) + "
            "(SR through balls 1..n / era SR through n) - 2. Top 5 per index."
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
            "catalog's Gini uses."
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


def ch1_doc(bands, seasons) -> dict:
    return {
        "era_bands": band_meta(),
        "ignition": ignition_section(bands, seasons),
        "outrate": outrate_section(bands),
        "defiers": defiers_section(bands),
        "sixes": sixes_section(seasons),
        "aerial": aerial_section(bands),
        "wpl_beat": wpl_beat_section(bands, seasons),
    }


# ---------------------------------------------------------------------------
# Emission
# ---------------------------------------------------------------------------


def main(out_root: Path = canon.OUT_ROOT) -> dict:
    bands, seasons, players, n_matches, superover_balls = build()
    coldopen = coldopen_doc(seasons, players, n_matches, superover_balls)
    ch1 = ch1_doc(bands, seasons)

    scenes_dir = out_root / "scenes"
    scenes_dir.mkdir(parents=True, exist_ok=True)
    sizes = {}
    for name, doc in (("coldopen.json", coldopen), ("ch1.json", ch1)):
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
        meta["n_matches"] = {
            "ipl": sum(seasons[("ipl", s)].matches for s in canon.IPL_SEASONS),
            "wpl": sum(seasons[("wpl", s)].matches for s in canon.WPL_SEASONS),
        }
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
    return {"coldopen": coldopen, "ch1": ch1}


if __name__ == "__main__":
    main()
