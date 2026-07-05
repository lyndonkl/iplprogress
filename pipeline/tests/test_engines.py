"""Engine #2 (RE288) + #3 (WP grid + LI) validation gate — the BINDING §5 gate.

Per the blueprint: engines #2 and #3 must clear calibration + monotonicity
sanity checks BEFORE any Chapter-5 / interlude choreography is authored, so
model rework can never invalidate finished scene work. This module IS that gate:

  * RE-surface monotonicity (runs-to-come non-increasing in both wickets fallen
    and overs bowled, every surface), calibration (pooled predicted runs-to-come
    == pooled actual), and the era-drift anchor (RE at "10 overs, 3 down" rose
    88->97 across eras — the catalog's 90.6 -> 98.3 teaser).
  * WP CALIBRATION (predicted vs actual chase-win rate in predicted-WP deciles,
    independently recomputed from the emitted grid over the whole corpus and
    asserted within tolerance) + WP monotonicity (non-increasing in required
    rate, non-decreasing in wickets in hand) + the era anchor (a 9+ RPO chase
    with ~60 balls left won ~23% in 2008-12 vs ~31% in 2023-26) + the defend
    curve (170-189 defended ~70% then, ~40% now).

Determinism: the on-disk files equal a fresh recompute byte-for-byte. Both
engines write only under web/static/data/engines/ and are NOT consumed by any
R2a scene — these tests protect R3b, not the shipping R2a build.
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
import re288
import wp

ART = None


def setUpModule():
    global ART
    out = canon.OUT_ROOT / "engines"
    if not (out / "re288.json").exists():
        re288.main()
    if not (out / "wp_grid.json").exists():
        wp.main()
    ART = {
        "re288": json.loads((out / "re288.json").read_text()),
        "wp": json.loads((out / "wp_grid.json").read_text()),
    }


# ===========================================================================
# Engine #2 — RE288
# ===========================================================================


class TestRE288Monotonicity(unittest.TestCase):
    """The binding RE sanity check: runs-to-come falls as wickets fall and as
    overs are bowled, for EVERY surface (no exceptions)."""

    def test_non_increasing_in_wickets(self):
        for key, s in ART["re288"]["surfaces"].items():
            re = s["re"]
            for o in range(re288.N_OVERS):
                for w in range(re288.N_WKTS - 1):
                    self.assertGreaterEqual(
                        re[o][w] + 1e-6, re[o][w + 1],
                        msg=f"{key} o={o} w={w}: {re[o][w]} < {re[o][w+1]}")

    def test_non_increasing_in_overs(self):
        for key, s in ART["re288"]["surfaces"].items():
            re = s["re"]
            for o in range(re288.N_OVERS - 1):
                for w in range(re288.N_WKTS):
                    self.assertGreaterEqual(
                        re[o][w] + 1e-6, re[o + 1][w],
                        msg=f"{key} o={o} w={w}: {re[o][w]} < {re[o+1][w]}")


class TestRE288Calibration(unittest.TestCase):
    def test_pooled_prediction_matches_actual(self):
        # weighted PAV preserves block means -> pooled predicted RTC == actual.
        for key, s in ART["re288"]["surfaces"].items():
            cal = s["calibration"]
            self.assertIsNotNone(cal["pooled_abs_dev"])
            self.assertLess(cal["pooled_abs_dev"], 1.0,
                            msg=f"{key} pooled |pred-actual|={cal['pooled_abs_dev']}")

    def test_re_00_equals_era_average_total(self):
        # RE(0 overs, 0 down) is by definition the average first-innings total.
        for key in ("ipl 2008-2010", "ipl 2023-2026"):
            re00 = ART["re288"]["surfaces"][key]["re"][0][0]
            # profile: ~159 (2008-10), ~188 (2023-26)
            self.assertGreater(re00, 140)
            self.assertLess(re00, 210)
        early = ART["re288"]["surfaces"]["ipl 2008-2010"]["re"][0][0]
        recent = ART["re288"]["surfaces"]["ipl 2023-2026"]["re"][0][0]
        self.assertGreater(recent, early + 15)  # the scoring explosion


class TestRE288EraDrift(unittest.TestCase):
    def test_ten_overs_three_down_rose(self):
        early = ART["re288"]["surfaces"]["ipl 2008-2010"]["re"][10][3]
        recent = ART["re288"]["surfaces"]["ipl 2023-2026"]["re"][10][3]
        # catalog teaser: 90.6 -> 98.3 (our over-start sampling lands 88 -> 97).
        self.assertAlmostEqual(early, 88.4, delta=4.0)
        self.assertAlmostEqual(recent, 96.9, delta=4.0)
        self.assertGreater(recent, early + 4.0)

    def test_matches_independent_raw_cell(self):
        # Independent raw recompute of the (10, 3) cell mean; the emitted
        # (post-isotonic) value should sit within a few runs of it.
        raw = _re_raw_cell("ipl 2023-2026", 10, 3)
        emitted = ART["re288"]["surfaces"]["ipl 2023-2026"]["re"][10][3]
        self.assertAlmostEqual(emitted, raw, delta=3.0)


class TestRE288WPLMask(unittest.TestCase):
    def test_wpl_surface_present_and_masked(self):
        wpl = ART["re288"]["surfaces"]["wpl 2023-2026"]
        self.assertIn("masked", wpl)
        n_masked = sum(sum(row) for row in wpl["masked"])
        # young league: many corner cells are thin -> masked, but not all.
        self.assertGreater(n_masked, 0)
        self.assertLess(n_masked, re288.N_OVERS * re288.N_WKTS)
        # a masked cell must be a thin cell.
        for o in range(re288.N_OVERS):
            for w in range(re288.N_WKTS):
                if wpl["masked"][o][w]:
                    self.assertLess(wpl["n"][o][w], re288.MASK_MIN_N)


def _re_raw_cell(surface_key, over, wkts):
    """Independent raw mean runs-to-come at (over-start, wkts) for a surface."""
    lo_hi = {"ipl 2008-2010": (2008, 2010), "ipl 2023-2026": (2023, 2026)}[surface_key]
    total = 0.0
    n = 0
    for _d, _m, league, path in flatten.sorted_match_files():
        if league != "ipl":
            continue
        with open(path) as fh:
            m = json.load(fh)
        info = m["info"]
        if canon.is_dl(info):
            continue
        s = canon.canon_season(info)
        if not (lo_hi[0] <= s <= lo_hi[1]):
            continue
        inns = [i for i in m.get("innings", []) if not canon.is_super_over(i)]
        if not inns:
            continue
        runs = 0
        wk = 0
        state = None
        final = 0
        for over_obj in inns[0]["overs"]:
            if over_obj["over"] == over:
                state = (runs, wk)
            for dl in over_obj["deliveries"]:
                runs += dl["runs"]["total"]
                if "wickets" in dl:
                    wk += len(dl["wickets"])
        final = runs
        if state is not None and state[1] == wkts:
            total += final - state[0]
            n += 1
    return total / n if n else None


# ===========================================================================
# Engine #3 — WP grid + LI
# ===========================================================================


class TestWPMonotonicity(unittest.TestCase):
    def test_non_increasing_in_required_rate(self):
        for key, s in ART["wp"]["second_innings"]["surfaces"].items():
            grid = s["wp"]
            for ol in range(wp.N_OVERS_LEFT):
                for wih in range(wp.N_WKTS_IN_HAND):
                    for rb in range(wp.N_RRR - 1):
                        self.assertGreaterEqual(
                            grid[ol][wih][rb] + 1e-6, grid[ol][wih][rb + 1],
                            msg=f"{key} ol={ol} wih={wih} rb={rb}")

    def test_non_decreasing_in_wickets(self):
        for key, s in ART["wp"]["second_innings"]["surfaces"].items():
            grid = s["wp"]
            for ol in range(wp.N_OVERS_LEFT):
                for rb in range(wp.N_RRR):
                    for wih in range(wp.N_WKTS_IN_HAND - 1):
                        self.assertLessEqual(
                            grid[ol][wih][rb], grid[ol][wih + 1][rb] + 1e-6,
                            msg=f"{key} ol={ol} rb={rb} wih={wih}")


class TestWPCalibration(unittest.TestCase):
    """The BINDING calibration gate: independently score every second-innings
    state from the emitted era grids and bin by predicted WP."""

    @classmethod
    def setUpClass(cls):
        cls.innings, _defend = wp.build()
        cls.era_grids = {
            label: ART["wp"]["second_innings"]["surfaces"][f"ipl {label}"]["wp"]
            for label, _l, _h in wp.IPL_ERA_BANDS
        }
        cls.era_grids["wpl"] = ART["wp"]["second_innings"]["surfaces"]["wpl 2023-2026"]["wp"]

    def test_reliability_within_tolerance(self):
        bins = [[0.0, 0.0, 0] for _ in range(10)]
        for rec in self.innings:
            grid = self.era_grids.get(rec.era)
            if grid is None:
                continue
            for (ol, wih, rb) in rec.states:
                p = grid[ol][wih][rb]
                b = min(9, int(p * 10))
                bins[b][0] += p
                bins[b][1] += rec.outcome
                bins[b][2] += 1
        wdev = 0.0
        tot = 0
        for b in range(10):
            s_pred, s_act, n = bins[b]
            if not n:
                continue
            pred, act = s_pred / n, s_act / n
            wdev += abs(pred - act) * n
            tot += n
            if n >= 500:  # well-populated bins must track the diagonal closely
                self.assertLess(abs(pred - act), 0.06,
                                msg=f"bin {b}: pred={pred:.3f} act={act:.3f} n={n}")
        weighted = wdev / tot
        # the gate's headline number
        self.assertLess(weighted, 0.03, msg=f"weighted mean |pred-actual|={weighted:.4f}")

    def test_emitted_calibration_table_agrees(self):
        # the doc's own calibration table must report the same gate number.
        self.assertLess(ART["wp"]["calibration"]["weighted_mean_abs_dev"], 0.03)


class TestWPEraAnchor(unittest.TestCase):
    def test_hard_chase_win_rate_rose(self):
        anc = ART["wp"]["calibration"]["era_anchor"]
        early = anc["ipl_2008_2012"]["win_rate"]
        recent = anc["ipl_2023_2026"]["win_rate"]
        # blueprint interlude: 24.3% -> 31.8% (we land 23% -> 31%).
        self.assertAlmostEqual(early, 0.243, delta=0.05)
        self.assertAlmostEqual(recent, 0.318, delta=0.05)
        self.assertGreater(recent, early)

    def test_anchor_reproducible_from_raw(self):
        fresh = wp._era_anchor()
        self.assertEqual(fresh["ipl_2008_2012"]["n"],
                         ART["wp"]["calibration"]["era_anchor"]["ipl_2008_2012"]["n"])
        self.assertAlmostEqual(
            fresh["ipl_2023_2026"]["win_rate"],
            ART["wp"]["calibration"]["era_anchor"]["ipl_2023_2026"]["win_rate"],
            places=4)


class TestWPDefendCurve(unittest.TestCase):
    def test_monotone_increasing_in_total(self):
        for key, s in ART["wp"]["first_innings_defend"]["surfaces"].items():
            p = s["p_batfirst_win"]
            for i in range(len(p) - 1):
                self.assertLessEqual(p[i], p[i + 1] + 1e-6, msg=f"{key} bucket {i}")

    def test_170_189_repriced_across_eras(self):
        dfd = ART["wp"]["first_innings_defend"]["surfaces"]
        labels = dfd["ipl 2008-2010"]["bucket_labels"]
        i170, i180 = labels.index("170-179"), labels.index("180-189")

        def defend_pct(era):
            row = dfd[era]
            n = row["n"][i170] + row["n"][i180]
            return (row["p_batfirst_win"][i170] * row["n"][i170]
                    + row["p_batfirst_win"][i180] * row["n"][i180]) / n if n else None

        early = defend_pct("ipl 2008-2010")
        recent = defend_pct("ipl 2023-2026")
        # catalog: ~74% defended then, ~38% now — a large downward reprice.
        self.assertGreater(early, 0.60)
        self.assertLess(recent, 0.52)
        self.assertGreater(early - recent, 0.18)


class TestLeverageIndex(unittest.TestCase):
    def test_present_and_sane(self):
        pooled = ART["wp"]["second_innings"]["surfaces"]["ipl pooled"]
        self.assertIn("leverage_index", pooled)
        li = pooled["leverage_index"]
        vals = [li[o][w][r] for o in range(wp.N_OVERS_LEFT)
                for w in range(wp.N_WKTS_IN_HAND) for r in range(wp.N_RRR)
                if li[o][w][r] is not None]
        self.assertGreater(len(vals), 200)
        self.assertTrue(all(v >= 0 for v in vals))
        # a tight endgame cell should carry well-above-average leverage.
        self.assertGreater(max(vals), 3.0)
        # the corpus mean is the normalizer, so the n-weighted average is ~1.
        self.assertGreater(ART["wp"]["leverage_index"]["corpus_mean_abs_dwp"], 0)


# ===========================================================================
# Determinism
# ===========================================================================


class TestDeterminism(unittest.TestCase):
    def test_re288_on_disk_equals_fresh(self):
        fresh = flatten.compact_json(re288.build_doc(), sort_keys=True)
        self.assertEqual((canon.OUT_ROOT / "engines" / "re288.json").read_bytes(),
                         fresh)

    def test_wp_on_disk_equals_fresh(self):
        fresh = flatten.compact_json(wp.build_doc(), sort_keys=True)
        self.assertEqual((canon.OUT_ROOT / "engines" / "wp_grid.json").read_bytes(),
                         fresh)


if __name__ == "__main__":
    unittest.main()
