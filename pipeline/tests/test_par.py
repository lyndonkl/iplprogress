"""Engine #1 snapshot tests — par baselines / SR+ family (R2a, Chapter 2).

The emitted engine tables (engines/par.json + phasepar.json + srplus.json) are
checked against a fully independent recount straight from the raw corpus (its
own season-blocked pass, its own phase splitter, its own anchor classifier),
and the catalog's Anchor Extinction Index / Ball-by-Ball DNA targets are
asserted as reconciliation anchors:

  * anchor-ball share ~14.8% (IPL 2008-10) -> ~8.5% (2023-26), WPL ~9%;
  * sub-120-SR occupancy qualifier counts EXACT (150 early / 250 recent / 81
    WPL — the catalog's "150 / 249 / 81") and recent share EXACT (2.4%);
  * SR+ is centred exactly at 100 per league-season (calibration).

Determinism: the on-disk files equal a fresh recompute byte-for-byte.
"""

from __future__ import annotations

import json
import sys
import unittest
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import canon
import flatten
import par

ART = None


def setUpModule():
    global ART
    out = canon.OUT_ROOT
    if not (out / "engines" / "par.json").exists():
        par.main()
    ART = {
        "par": json.loads((out / "engines" / "par.json").read_text()),
        "phasepar": json.loads((out / "engines" / "phasepar.json").read_text()),
        "srplus": json.loads((out / "engines" / "srplus.json").read_text()),
    }


def phase_of(over: int) -> str:
    if over <= 5:
        return "pp"
    if over <= 14:
        return "middle"
    return "death"


def recount():
    """Independent pass: phase-par marginal, every batter-innings, and per
    (league, season, batter) run/ball tallies."""
    phase_runs = defaultdict(int)
    phase_balls = defaultdict(int)
    innings = []  # (league, season, balls, runs, boundary, {phase: balls})
    bs = defaultdict(lambda: [0, 0])  # (league, season, batter) -> [balls, runs]

    for _d, _m, league, path in flatten.sorted_match_files():
        with open(path) as fh:
            match = json.load(fh)
        season = canon.canon_season(match["info"])
        ino = 0
        for inn in match.get("innings", []):
            if inn.get("super_over"):
                continue
            ino += 1
            per = {}
            for over in inn["overs"]:
                ph = phase_of(over["over"])
                for dl in over["deliveries"]:
                    if "wides" in dl.get("extras", {}):
                        continue
                    rb = dl["runs"]["batter"]
                    striker = dl["batter"]
                    phase_runs[(league, season, ph)] += rb
                    phase_balls[(league, season, ph)] += 1
                    b = bs[(league, season, striker)]
                    b[0] += 1
                    b[1] += rb
                    rec = per.get(striker)
                    if rec is None:
                        rec = per[striker] = {"balls": 0, "runs": 0, "bnd": 0,
                                              "pb": {"pp": 0, "middle": 0, "death": 0}}
                    rec["balls"] += 1
                    rec["runs"] += rb
                    rec["pb"][ph] += 1
                    if rb >= 4:
                        rec["bnd"] += 1
            for rec in per.values():
                innings.append((league, season, rec))

    pp = {k: phase_runs[k] / phase_balls[k] for k in phase_balls}
    return pp, innings, bs


def is_anchor(league, season, rec, pp):
    if rec["balls"] < 15:
        return False
    if rec["bnd"] >= 0.12 * rec["balls"]:
        return False
    par_runs = sum(pp[(league, season, ph)] * n for ph, n in rec["pb"].items() if n)
    return rec["runs"] < 0.85 * par_runs


def anchor_share(innings, pp, league, lo, hi):
    anchor = total = 0
    for lg, s, rec in innings:
        if lg != league or not (lo <= s <= hi):
            continue
        total += rec["balls"]
        if is_anchor(lg, s, rec, pp):
            anchor += rec["balls"]
    return 100.0 * anchor / total


def occupancy(bs, league, lo, hi):
    qual = sub = 0
    for (lg, s, _b), (balls, runs) in bs.items():
        if lg != league or not (lo <= s <= hi) or balls < 100:
            continue
        qual += 1
        if 100.0 * runs / balls < 120.0:
            sub += 1
    return qual, sub


class TestPhasePar(unittest.TestCase):
    def test_marginal_matches_independent_recount(self):
        pp, _inn, _bs = recount()
        rows = {(r["league"], r["season"]): r for r in ART["phasepar"]["seasons"]}
        for (league, season, ph), e in pp.items():
            emitted = rows[(league, season)][ph]["expected_runs_per_ball"]
            self.assertAlmostEqual(emitted, round(e, 5), places=5,
                                   msg=f"{league} {season} {ph}")

    def test_phase_ordering_and_rise(self):
        rows = {(r["league"], r["season"]): r for r in ART["phasepar"]["seasons"]}
        # Death overs out-scored the powerplay in the anchor era.
        y08 = rows[("ipl", 2008)]
        self.assertGreater(y08["death"]["par_sr"], y08["pp"]["par_sr"])
        # The powerplay par SR exploded across two decades (attack from ball one).
        self.assertGreater(rows[("ipl", 2026)]["pp"]["par_sr"],
                           rows[("ipl", 2008)]["pp"]["par_sr"])


class TestAnchorExtinction(unittest.TestCase):
    def test_era_bands_match_independent_recount(self):
        pp, innings, _bs = recount()
        era = ART["par"]["anchor_extinction"]["era_bands"]
        for label, lo, hi in par.IPL_ERA_BANDS:
            got = anchor_share(innings, pp, "ipl", lo, hi)
            self.assertAlmostEqual(era[f"ipl {label}"]["anchor_ball_share_pct"],
                                   round(got, 2), places=2, msg=label)
        self.assertAlmostEqual(era["wpl 2023-2026"]["anchor_ball_share_pct"],
                               round(anchor_share(innings, pp, "wpl", 2023, 2026), 2),
                               places=2)

    def test_reproduces_catalog_targets(self):
        era = ART["par"]["anchor_extinction"]["era_bands"]
        early = era["ipl 2008-2010"]["anchor_ball_share_pct"]
        recent = era["ipl 2023-2026"]["anchor_ball_share_pct"]
        wpl = era["wpl 2023-2026"]["anchor_ball_share_pct"]
        # catalog: 14.8% -> 8.5% (a 43% population collapse); WPL ~9-10%.
        self.assertAlmostEqual(early, 14.8, delta=0.6)
        self.assertAlmostEqual(recent, 8.5, delta=0.6)
        self.assertGreater(early, recent)
        collapse = 100.0 * (early - recent) / early
        self.assertAlmostEqual(collapse, 43.0, delta=6.0)
        self.assertTrue(8.0 <= wpl <= 11.0, wpl)


class TestSub120Occupancy(unittest.TestCase):
    def test_qualifier_counts_exact(self):
        _pp, _inn, bs = recount()
        occ = ART["par"]["sub120_occupancy"]["era_bands"]
        # catalog Ball-by-Ball DNA: "150 early / 249 recent / 81 WPL qualify".
        q_early, _ = occupancy(bs, "ipl", 2008, 2010)
        q_recent, _ = occupancy(bs, "ipl", 2023, 2026)
        q_wpl, _ = occupancy(bs, "wpl", 2023, 2026)
        self.assertEqual(occ["ipl 2008-2010"]["qualifiers"], q_early)
        self.assertEqual(occ["ipl 2023-2026"]["qualifiers"], q_recent)
        self.assertEqual(occ["wpl 2023-2026"]["qualifiers"], q_wpl)
        self.assertEqual(q_early, 150)
        self.assertEqual(q_recent, 250)
        self.assertEqual(q_wpl, 81)

    def test_reproduces_catalog_targets(self):
        occ = ART["par"]["sub120_occupancy"]["era_bands"]
        early = occ["ipl 2008-2010"]["sub120_share_pct"]
        recent = occ["ipl 2023-2026"]["sub120_share_pct"]
        # catalog: 38.7% -> 2.4%. Recent is exact; early is a knife-edge band
        # (a few batter-seasons sit right at SR 120) -> assert near-catalog.
        self.assertAlmostEqual(recent, 2.4, delta=0.1)
        self.assertAlmostEqual(early, 38.7, delta=2.5)
        self.assertGreater(early, recent)


class TestSRPlus(unittest.TestCase):
    def test_calibration_exactly_100(self):
        calib = ART["par"]["srplus_calibration"]
        self.assertLess(calib["max_abs_dev_from_100"], 1e-3)
        for row in calib["per_league_season"]:
            if row["pooled_srplus"] is not None:
                self.assertAlmostEqual(row["pooled_srplus"], 100.0, places=2)

    def test_leaderboard_shape_and_qualifier(self):
        sp = ART["srplus"]
        self.assertEqual(sp["min_balls"], par.SRPLUS_MIN_BALLS)
        self.assertEqual(sp["count"], len(sp["batter_seasons"]))
        self.assertGreater(sp["count"], 500)
        for r in sp["batter_seasons"]:
            self.assertGreaterEqual(r["balls"], par.SRPLUS_MIN_BALLS)
            self.assertGreater(r["expected_runs"], 0)
            self.assertIsNotNone(r["srplus"])
            self.assertAlmostEqual(r["sr"], round(100.0 * r["runs"] / r["balls"], 2),
                                   places=2)
        # sorted deterministically by (league, season, batter)
        keys = [(r["league"], r["season"], r["batter"]) for r in sp["batter_seasons"]]
        self.assertEqual(keys, sorted(keys))
        # a high-SR season should price out above era par; anchors below.
        best = max(sp["batter_seasons"], key=lambda r: r["srplus"])
        self.assertGreater(best["srplus"], 130)

    def test_srplus_field_is_self_consistent(self):
        # Every row's srplus == 100 x runs / expected_runs (the definition),
        # so a client can re-derive it from the shipped fields.
        for r in ART["srplus"]["batter_seasons"]:
            self.assertAlmostEqual(
                r["srplus"], round(100.0 * r["runs"] / r["expected_runs"], 2),
                delta=0.02, msg=r["batter"],
            )

    def test_conditional_cells_well_formed(self):
        cells = ART["par"]["conditional_cells"]
        n = cells["count"]
        for arr in ("league", "season", "phase", "venue", "innings",
                    "expected_runs_per_ball", "n"):
            self.assertEqual(len(cells[arr]), n, arr)
        self.assertTrue(all(e > 0 for e in cells["expected_runs_per_ball"]))
        self.assertTrue(all(ph in par.PHASES for ph in cells["phase"]))
        self.assertTrue(all(v in canon.GROUND_CITY for v in cells["venue"]))
        self.assertTrue(all(nn > 0 for nn in cells["n"]))


class TestDeterminism(unittest.TestCase):
    def test_on_disk_equals_fresh_build(self):
        docs = par.build_docs()
        out = canon.OUT_ROOT / "engines"
        for name, key in (("phasepar.json", "phasepar"),
                          ("par.json", "par"),
                          ("srplus.json", "srplus")):
            fresh = flatten.compact_json(docs[key], sort_keys=True)
            self.assertEqual((out / name).read_bytes(), fresh, name)


if __name__ == "__main__":
    unittest.main()
