"""Engine #1 — par baselines / SR+ family (R2a, first needed by Chapter 2).

Builds the expected-runs-per-ball-faced model the piece uses as its era-honest
currency, and the season × over-phase par table Chapter 2's anchor definition
is measured against.

The model
---------
For every ball FACED (wides excluded, no-balls counted — the SR convention,
identical to scenes.py / ballsfaced.u8) we hold an expected batter-runs value

    E[runs.batter | league, season, over-phase, venue, innings]

built in two tiers so small cells borrow strength from a large parent:

  * phase-par (the marginal, EXACT, no shrinkage): per (league, season,
    over-phase) the raw mean batter-runs per ball faced. Over-phases are
    powerplay = overs 1-6 (0-based 0..5), middle = overs 7-15 (6..14), death =
    overs 16-20 (15..19). This is the table Chapter 2 renders (the par worm)
    and the anchor definition's "season-phase par SR" — kept raw on purpose so
    the anchor share reproduces the catalog. Emitted compact to
    engines/phasepar.json.

  * conditional cells (venue × innings, SHRUNK): per (league, season, phase,
    venue, innings) the raw cell mean is empirical-Bayes shrunk toward its
    season-phase parent with a pseudo-count of SHRINK_K balls faced, then each
    league-season's cells are rescaled so the pooled expected total equals the
    pooled actual total (calibration: pooled SR+ over a whole league-season is
    exactly 100 — "100 = league-average-of-own-time"). Emitted to
    engines/par.json.

SR+
---
    SR+(batter) = 100 x sum(actual runs.batter) / sum(E[runs.batter])
over the EXACT balls the batter faced (each ball priced by its conditional
cell). 100 = an average batter of the same league/era/phases/venues. Emitted
per batter-season (>= SRPLUS_MIN_BALLS balls) to engines/srplus.json.

Validation (asserted in tests/test_par.py, printed by main)
-----------------------------------------------------------
  * Anchor innings (catalog Anchor Extinction Index): balls faced >= 15 AND
    innings runs < 0.85 x phase-weighted par (SR < 0.85 x contemporaneous
    phase-weighted par SR) AND boundary balls (runs.batter >= 4) < 12% of balls
    faced. Anchor-ball share per season = balls consumed by anchor innings /
    all balls faced. Lands ~14.8% (IPL 2008-10) -> ~8.5% (2023-26); WPL ~9%.
  * Sub-120-SR occupancy (catalog Ball-by-Ball DNA): share of qualifying
    batter-seasons (>= 100 balls faced) striking under 120. ~38.7% (2008-10)
    -> ~2.4% (2023-26).

Stdlib only. Byte-deterministic (compact JSON, key-sorted). Writes only under
web/static/data/engines/ — it never touches an R1 artifact.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import canon
import flatten

ENGINES_DIR = canon.OUT_ROOT / "engines"

# Over-phase boundaries (0-based over index). PP overs 1-6 -> 0..5; middle
# 7-15 -> 6..14; death 16-20 -> 15..19.
PHASES = ("pp", "middle", "death")
PP_LAST_OVER = 5      # last 0-based over of the powerplay
MIDDLE_LAST_OVER = 14  # last 0-based over of the middle


def phase_of(over: int) -> str:
    if over <= PP_LAST_OVER:
        return "pp"
    if over <= MIDDLE_LAST_OVER:
        return "middle"
    return "death"


# Empirical-Bayes pseudo-count (balls faced) pulling a venue x innings cell
# toward its season-phase parent. Small relative to a typical cell so
# well-populated cells stay near their own mean; large relative to a thin
# (single-match) cell so it borrows the parent.
SHRINK_K = 50.0

# Anchor thresholds (catalog Anchor Extinction Index recipe).
ANCHOR_MIN_BALLS = 15
ANCHOR_SR_RATIO = 0.85          # innings SR < 0.85 x phase-weighted par SR
ANCHOR_MAX_BOUNDARY_SHARE = 0.12  # boundary balls (runs.batter >= 4) < 12%

# Ball-by-Ball DNA / sub-120 occupancy qualifier.
BATTER_SEASON_MIN_BALLS = 100
SUB120_SR = 120.0

# SR+ leaderboard qualifier (balls faced in the season).
SRPLUS_MIN_BALLS = 100

# Era bands for the validation roll-ups (same as scenes.py Ch 1 bands).
IPL_ERA_BANDS = (
    ("2008-2010", 2008, 2010),
    ("2011-2015", 2011, 2015),
    ("2016-2019", 2016, 2019),
    ("2020-2022", 2020, 2022),
    ("2023-2026", 2023, 2026),
)


# ---------------------------------------------------------------------------
# Corpus pass
# ---------------------------------------------------------------------------


class Innings:
    """One batter-innings: the balls-per-phase, runs and boundaries needed to
    price the innings (SR+) and classify it (anchor)."""

    __slots__ = (
        "league", "season", "venue", "innings_no", "batter",
        "balls", "runs", "boundary_balls", "phase_balls",
    )

    def __init__(self, league, season, venue, innings_no, batter):
        self.league = league
        self.season = season
        self.venue = venue
        self.innings_no = innings_no
        self.batter = batter
        self.balls = 0
        self.runs = 0
        self.boundary_balls = 0
        self.phase_balls = {"pp": 0, "middle": 0, "death": 0}


def build(data_root: Path = canon.DATA_ROOT):
    """One chronological pass collecting the raw cell sums (for the model) and
    every batter-innings (for SR+ and the anchor / occupancy validation)."""
    # raw[(league, season, phase, venue, innings_no)] = [runs, balls]
    raw_cells: dict = defaultdict(lambda: [0, 0])
    # phase-par marginal raw[(league, season, phase)] = [runs, balls]
    raw_phase: dict = defaultdict(lambda: [0, 0])
    # per (league, season) pooled actual runs faced / balls faced (calibration)
    season_totals: dict = defaultdict(lambda: [0, 0])
    innings_records: list = []

    for _date, _mid, league, path in flatten.sorted_match_files(data_root):
        with open(path) as fh:
            match = json.load(fh)
        info = match["info"]
        season = canon.canon_season(info)
        venue = canon.canon_venue(info["venue"])

        innings_no = 0
        for innings in match.get("innings", []):
            if canon.is_super_over(innings):
                continue
            innings_no += 1
            per_batter: dict = {}
            for over in innings["overs"]:
                phase = phase_of(over["over"])
                for dl in over["deliveries"]:
                    if "wides" in dl.get("extras", {}):
                        continue  # a wide is not a ball faced
                    striker = dl["batter"]
                    rb = dl["runs"]["batter"]
                    key = (league, season, phase, venue, innings_no)
                    cell = raw_cells[key]
                    cell[0] += rb
                    cell[1] += 1
                    pm = raw_phase[(league, season, phase)]
                    pm[0] += rb
                    pm[1] += 1
                    st = season_totals[(league, season)]
                    st[0] += rb
                    st[1] += 1
                    rec = per_batter.get(striker)
                    if rec is None:
                        rec = per_batter[striker] = Innings(
                            league, season, venue, innings_no, striker
                        )
                    rec.balls += 1
                    rec.runs += rb
                    rec.phase_balls[phase] += 1
                    if rb >= 4:
                        rec.boundary_balls += 1
            innings_records.extend(per_batter.values())

    return raw_cells, raw_phase, season_totals, innings_records


# ---------------------------------------------------------------------------
# The model: phase-par marginal + shrunk, calibrated conditional cells
# ---------------------------------------------------------------------------


def phase_par(raw_phase: dict) -> dict:
    """Exact season-phase mean batter-runs per ball faced (no shrinkage).

    phase_par[(league, season, phase)] = runs / balls. This is the anchor
    definition's baseline and Chapter 2's par worm.
    """
    return {
        k: (v[0] / v[1] if v[1] else 0.0)
        for k, v in raw_phase.items()
    }


def conditional_cells(raw_cells, phasepar, season_totals) -> dict:
    """Shrunk + calibrated E[runs.batter] per (league, season, phase, venue,
    innings). Shrink each raw cell toward its season-phase parent, then rescale
    every league-season so pooled expected == pooled actual (SR+ centered 100).
    """
    shrunk: dict = {}
    exp_by_season: dict = defaultdict(float)  # sum expected*balls before rescale
    for key, (runs, balls) in raw_cells.items():
        league, season, phase, _venue, _inn = key
        parent = phasepar[(league, season, phase)]
        e = (runs + SHRINK_K * parent) / (balls + SHRINK_K)
        shrunk[key] = e
        exp_by_season[(league, season)] += e * balls

    scale: dict = {}
    for ls, (actual_runs, _balls) in season_totals.items():
        expected = exp_by_season[ls]
        scale[ls] = (actual_runs / expected) if expected else 1.0

    cells: dict = {}
    for key, e in shrunk.items():
        league, season, phase, venue, inn = key
        cells[key] = e * scale[(league, season)]
    return cells, scale


# ---------------------------------------------------------------------------
# SR+ (per batter-season) + the validation roll-ups
# ---------------------------------------------------------------------------


def innings_expected(rec: "Innings", cells: dict) -> float:
    """Expected batter-runs over the exact balls this batter faced, priced by
    the conditional cell of each (phase, venue, innings)."""
    total = 0.0
    for phase, nballs in rec.phase_balls.items():
        if nballs:
            e = cells[(rec.league, rec.season, phase, rec.venue, rec.innings_no)]
            total += e * nballs
    return total


def innings_par_runs(rec: "Innings", phasepar: dict) -> float:
    """Phase-weighted par runs for the innings (anchor baseline), using the
    EXACT (raw) season-phase marginal — not the shrunk cells."""
    total = 0.0
    for phase, nballs in rec.phase_balls.items():
        if nballs:
            total += phasepar[(rec.league, rec.season, phase)] * nballs
    return total


def is_anchor(rec: "Innings", phasepar: dict) -> bool:
    if rec.balls < ANCHOR_MIN_BALLS:
        return False
    if rec.boundary_balls >= ANCHOR_MAX_BOUNDARY_SHARE * rec.balls:
        return False
    par_runs = innings_par_runs(rec, phasepar)
    # innings SR < 0.85 x par SR  <=>  runs < 0.85 x par_runs (same denominator)
    return rec.runs < ANCHOR_SR_RATIO * par_runs


def batter_season_srplus(innings_records, cells) -> dict:
    """Aggregate per (league, season, batter): balls, runs, expected."""
    agg: dict = defaultdict(lambda: [0, 0, 0.0])  # balls, runs, expected
    for rec in innings_records:
        a = agg[(rec.league, rec.season, rec.batter)]
        a[0] += rec.balls
        a[1] += rec.runs
        a[2] += innings_expected(rec, cells)
    return agg


def anchor_validation(innings_records, phasepar) -> dict:
    """Anchor-ball share per season and per era band."""
    per_season: dict = defaultdict(lambda: [0, 0])  # anchor_balls, all_balls
    for rec in innings_records:
        s = per_season[(rec.league, rec.season)]
        s[1] += rec.balls
        if is_anchor(rec, phasepar):
            s[0] += rec.balls

    seasons = []
    for (league, season), (anchor_balls, all_balls) in sorted(per_season.items()):
        seasons.append({
            "league": league,
            "season": season,
            "anchor_balls": anchor_balls,
            "balls": all_balls,
            "anchor_ball_share_pct": round(100.0 * anchor_balls / all_balls, 2)
            if all_balls else None,
        })

    def band(league, lo, hi):
        a = sum(per_season[(league, s)][0] for s in range(lo, hi + 1))
        b = sum(per_season[(league, s)][1] for s in range(lo, hi + 1))
        return {"anchor_balls": a, "balls": b,
                "anchor_ball_share_pct": round(100.0 * a / b, 2) if b else None}

    era = {f"ipl {label}": band("ipl", lo, hi) for label, lo, hi in IPL_ERA_BANDS}
    era["wpl 2023-2026"] = band("wpl", 2023, 2026)
    return {"per_season": seasons, "era_bands": era}


def occupancy_validation(srplus_agg) -> dict:
    """Sub-120-SR batter-season occupancy per season + era band (>= 100 balls)."""
    per_season: dict = defaultdict(lambda: [0, 0])  # sub120, qualifiers
    for (league, season, _batter), (balls, runs, _exp) in srplus_agg.items():
        if balls < BATTER_SEASON_MIN_BALLS:
            continue
        q = per_season[(league, season)]
        q[1] += 1
        if 100.0 * runs / balls < SUB120_SR:
            q[0] += 1

    seasons = []
    for (league, season), (sub120, qual) in sorted(per_season.items()):
        seasons.append({
            "league": league, "season": season,
            "qualifiers": qual, "sub120": sub120,
            "sub120_share_pct": round(100.0 * sub120 / qual, 2) if qual else None,
        })

    def band(league, lo, hi):
        s = sum(per_season[(league, x)][0] for x in range(lo, hi + 1))
        q = sum(per_season[(league, x)][1] for x in range(lo, hi + 1))
        return {"qualifiers": q, "sub120": s,
                "sub120_share_pct": round(100.0 * s / q, 2) if q else None}

    era = {f"ipl {label}": band("ipl", lo, hi) for label, lo, hi in IPL_ERA_BANDS}
    era["wpl 2023-2026"] = band("wpl", 2023, 2026)
    return {"per_season": seasons, "era_bands": era, "min_balls": BATTER_SEASON_MIN_BALLS}


def srplus_calibration(srplus_agg) -> dict:
    """Pooled SR+ over each league-season should be 100 by construction (the
    calibration check). Report the max deviation from 100."""
    per_season: dict = defaultdict(lambda: [0, 0.0])  # runs, expected
    for (league, season, _b), (balls, runs, exp) in srplus_agg.items():
        p = per_season[(league, season)]
        p[0] += runs
        p[1] += exp
    rows = []
    worst = 0.0
    for (league, season), (runs, exp) in sorted(per_season.items()):
        pooled = 100.0 * runs / exp if exp else None
        if pooled is not None:
            worst = max(worst, abs(pooled - 100.0))
        rows.append({"league": league, "season": season,
                     "pooled_srplus": round(pooled, 4) if pooled is not None else None})
    return {"per_league_season": rows, "max_abs_dev_from_100": round(worst, 6)}


# ---------------------------------------------------------------------------
# Emission
# ---------------------------------------------------------------------------


def phasepar_doc(phasepar: dict, raw_phase: dict) -> dict:
    rows = []
    keys = ([("ipl", s) for s in canon.IPL_SEASONS]
            + [("wpl", s) for s in canon.WPL_SEASONS])
    for league, season in keys:
        entry = {"league": league, "season": season}
        for phase in PHASES:
            k = (league, season, phase)
            runs, balls = raw_phase.get(k, (0, 0))
            e = phasepar.get(k)
            entry[phase] = {
                "expected_runs_per_ball": round(e, 5) if e is not None else None,
                "par_sr": round(100.0 * e, 2) if e is not None else None,
                "balls": balls,
            }
        rows.append(entry)
    return {
        "phase_definitions": {
            "pp": "overs 1-6 (0-based over index 0-5)",
            "middle": "overs 7-15 (over index 6-14)",
            "death": "overs 16-20 (over index 15-19)",
        },
        "definition": (
            "Season-phase par = raw mean batter runs per ball faced (wides "
            "excluded, no-balls counted), per (league, season, over-phase). "
            "par_sr = 100 x expected_runs_per_ball. This exact marginal is the "
            "Chapter 2 anchor baseline (SR < 0.85 x phase-weighted par SR) and "
            "the par worm; no shrinkage is applied here on purpose."
        ),
        "seasons": rows,
    }


def par_doc(cells, phasepar, raw_cells, scale, anchors, occupancy, calib) -> dict:
    # Conditional cells as sorted parallel arrays (compact, deterministic).
    keys = sorted(cells)
    leagues, seasonsL, phasesL, venuesL, inningsL = [], [], [], [], []
    e_vals, n_vals = [], []
    for k in keys:
        league, season, phase, venue, inn = k
        leagues.append(league)
        seasonsL.append(season)
        phasesL.append(phase)
        venuesL.append(venue)
        inningsL.append(inn)
        e_vals.append(round(cells[k], 5))
        n_vals.append(raw_cells[k][1])
    return {
        "engine": "1 — par baselines / SR+ family",
        "phase_definitions": {
            "pp": "overs 1-6 (0-based over index 0-5)",
            "middle": "overs 7-15 (over index 6-14)",
            "death": "overs 16-20 (over index 15-19)",
        },
        "method": (
            "E[runs.batter | league, season, over-phase, venue, innings]. "
            "Each raw cell mean is empirical-Bayes shrunk toward its "
            f"season-phase parent with pseudo-count {SHRINK_K} balls faced, "
            "then every league-season is rescaled so pooled expected == pooled "
            "actual (pooled SR+ over a whole league-season is exactly 100 — "
            "'100 = league-average-of-own-time'). Balls faced exclude wides, "
            "count no-balls (the SR convention). SR+ = 100 x sum(actual "
            "runs.batter) / sum(E[runs.batter]) over the exact balls faced."
        ),
        "shrinkage": {"pseudo_count_balls": SHRINK_K, "parent": "season-phase marginal"},
        "conditional_cells": {
            "note": (
                "Parallel arrays; cell c = (league[c], season[c], phase[c], "
                "venue[c], innings[c]) -> expected_runs_per_ball[c], with n[c] "
                "raw balls faced. Rescaled/calibrated per league-season."
            ),
            "count": len(keys),
            "league": leagues,
            "season": seasonsL,
            "phase": phasesL,
            "venue": venuesL,
            "innings": inningsL,
            "expected_runs_per_ball": e_vals,
            "n": n_vals,
        },
        "calibration_scale": {
            f"{lg} {s}": round(v, 6) for (lg, s), v in sorted(scale.items())
        },
        "srplus_calibration": calib,
        "anchor_definition": {
            "min_balls": ANCHOR_MIN_BALLS,
            "sr_ratio": ANCHOR_SR_RATIO,
            "max_boundary_share": ANCHOR_MAX_BOUNDARY_SHARE,
            "text": (
                "An anchor innings has balls faced >= 15 AND innings runs < "
                "0.85 x phase-weighted par runs (i.e. SR < 0.85 x "
                "contemporaneous phase-weighted par SR) AND boundary balls "
                "(runs.batter >= 4) < 12% of balls faced."
            ),
        },
        "anchor_extinction": anchors,
        "sub120_occupancy": occupancy,
    }


def srplus_doc(srplus_agg) -> dict:
    rows = []
    for (league, season, batter), (balls, runs, exp) in sorted(srplus_agg.items()):
        if balls < SRPLUS_MIN_BALLS:
            continue
        rows.append({
            "league": league,
            "season": season,
            "batter": batter,
            "balls": balls,
            "runs": runs,
            "sr": round(100.0 * runs / balls, 2),
            "expected_runs": round(exp, 3),
            "srplus": round(100.0 * runs / exp, 2) if exp else None,
        })
    return {
        "engine": "1 — SR+ (per batter-season)",
        "definition": (
            "SR+ = 100 x sum(actual runs.batter) / sum(E[runs.batter]) over the "
            "exact balls faced, priced by the engines/par.json conditional "
            "cells. 100 = an average batter of the same league / season / "
            "phases / venues. Qualifier: >= "
            f"{SRPLUS_MIN_BALLS} balls faced in the (league, season)."
        ),
        "min_balls": SRPLUS_MIN_BALLS,
        "count": len(rows),
        "batter_seasons": rows,
    }


def build_docs(data_root: Path = canon.DATA_ROOT):
    raw_cells, raw_phase, season_totals, innings_records = build(data_root)
    phasepar = phase_par(raw_phase)
    cells, scale = conditional_cells(raw_cells, phasepar, season_totals)
    srplus_agg = batter_season_srplus(innings_records, cells)

    anchors = anchor_validation(innings_records, phasepar)
    occupancy = occupancy_validation(srplus_agg)
    calib = srplus_calibration(srplus_agg)

    return {
        "phasepar": phasepar_doc(phasepar, raw_phase),
        "par": par_doc(cells, phasepar, raw_cells, scale, anchors, occupancy, calib),
        "srplus": srplus_doc(srplus_agg),
    }


def main(out_root: Path = canon.OUT_ROOT) -> dict:
    docs = build_docs()
    engines_dir = out_root / "engines"
    engines_dir.mkdir(parents=True, exist_ok=True)
    sizes = {}
    for name, doc in (
        ("phasepar.json", docs["phasepar"]),
        ("par.json", docs["par"]),
        ("srplus.json", docs["srplus"]),
    ):
        raw = flatten.compact_json(doc, sort_keys=True)
        (engines_dir / name).write_bytes(raw)
        sizes[f"engines/{name}"] = {
            "bytes_raw": len(raw),
            "bytes_gz": len(flatten.gz_bytes(raw)),
        }

    era = docs["par"]["anchor_extinction"]["era_bands"]
    occ = docs["par"]["sub120_occupancy"]["era_bands"]
    for name, s in sizes.items():
        print(f"  {name:22s} raw={s['bytes_raw']:>9,}  gz={s['bytes_gz']:>8,}")
    print(
        "anchor-ball share: ipl 2008-2010 "
        f"{era['ipl 2008-2010']['anchor_ball_share_pct']}% -> ipl 2023-2026 "
        f"{era['ipl 2023-2026']['anchor_ball_share_pct']}% "
        f"(wpl {era['wpl 2023-2026']['anchor_ball_share_pct']}%)"
    )
    print(
        "sub-120 occupancy: ipl 2008-2010 "
        f"{occ['ipl 2008-2010']['sub120_share_pct']}% -> ipl 2023-2026 "
        f"{occ['ipl 2023-2026']['sub120_share_pct']}%"
    )
    print(
        "srplus calibration max |dev-100| = "
        f"{docs['par']['srplus_calibration']['max_abs_dev_from_100']}  "
        f"(srplus batter-seasons: {docs['srplus']['count']})"
    )
    return docs


if __name__ == "__main__":
    main()
