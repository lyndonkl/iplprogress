"""R3b — the Net Session interlude scene (scenes/interlude.json).

The interlude is the two-dial teaching widget between Ch 4 and Ch 5. It does not
build a model; it re-projects the GATE-VALIDATED engine grids (whose correctness
tests/test_engines.py owns) into the widget coordinate and resolves the presets.
These tests protect that re-projection:

  * FIDELITY — the embedded win surfaces are the engine grid verbatim; the runs
    surfaces are engine #2 re-indexed to (overs_left, wickets_in_hand); the
    derived pooled-runs default is monotone and bracketed by the era surfaces.
  * PRESET INTEGRITY — every preset's quoted win% / expected runs is the exact
    grid readout at its cell (the copy can never contradict the meter), preset 1
    is a REAL Dhoni CHASE finish read from the corpus whose state exists and is
    evidenced in the second-innings grid (never the 2011 defend, §9.2), and the
    same-chase pair shares one scoreboard on two era surfaces (win + runs both
    rise 2010 -> 2025).
  * EVIDENCE PARITY — every surface ships a per-cell n (win + runs, both leagues)
    at one threshold (win n<12, runs n<15); masked WPL cells are genuinely thin;
    the counts are consistent; never all, never none.
  * ERA ANCHOR — the validated "same chase, two eras" headline (~23% -> ~31%).
  * DETERMINISM — the on-disk file equals a fresh recompute byte-for-byte.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import canon
import flatten
import interlude
import re288
import wp

DOC = None
WPG = None
RE = None


def setUpModule():
    global DOC, WPG, RE
    out = canon.OUT_ROOT
    if not (out / "scenes" / "interlude.json").exists():
        interlude.main()
    DOC = json.loads((out / "scenes" / "interlude.json").read_text())
    WPG = json.loads((out / "engines" / "wp_grid.json").read_text())
    RE = json.loads((out / "engines" / "re288.json").read_text())


NOL = interlude.N_OVERS_LEFT      # 20
NWH = interlude.N_WKTS_IN_HAND    # 10
NRB = interlude.N_RRR             # 10


def _rrr_bucket(runs_needed, overs_left, edges):
    rrr = runs_needed * 6.0 / (overs_left * 6)
    for i, e in enumerate(edges):
        if rrr < e:
            return i
    return len(edges)


# ===========================================================================
# Surface fidelity
# ===========================================================================


class TestSurfaceFidelity(unittest.TestCase):
    def test_win_surfaces_are_engine_grid_verbatim(self):
        for era in DOC["surfaces"]["win"]:
            self.assertEqual(
                DOC["surfaces"]["win"][era],
                WPG["second_innings"]["surfaces"][era]["wp"],
                msg=f"win surface {era} diverged from engine #3",
            )

    def test_runs_surfaces_are_engine_reindexed(self):
        # every era except the derived pooled default is engine #2 mirrored
        for era in DOC["surfaces"]["runs"]:
            if era == "ipl pooled":
                continue  # derived, checked separately
            src = RE["surfaces"][era]["re"]
            got = DOC["surfaces"]["runs"][era]
            for ol in range(1, NOL + 1):
                for wih in range(1, NWH + 1):
                    self.assertAlmostEqual(
                        got[ol - 1][wih - 1],
                        src[NOL - ol][NWH - wih],
                        places=9,
                        msg=f"runs {era} ({ol},{wih}) re-index broken",
                    )

    def test_pooled_runs_derived_and_bracketed(self):
        # RE288 ships no IPL-pooled runs surface; the default is derived and must
        # sit inside the range of the era surfaces it pools.
        self.assertNotIn(
            "ipl pooled", RE["surfaces"],
            msg="engine gained a pooled runs surface — revisit the derivation",
        )
        fresh = DOC["surfaces"]["runs"]["ipl pooled"][NOL - 1][NWH - 1]  # re[0][0]
        era00 = [RE["surfaces"][f"ipl {b}"]["re"][0][0]
                 for b, _l, _h in re288.IPL_ERA_BANDS]
        self.assertGreaterEqual(fresh, min(era00) - 1e-6)
        self.assertLessEqual(fresh, max(era00) + 1e-6)

    def test_all_declared_eras_present_both_dials(self):
        keys = [e["key"] for e in DOC["eras"]]
        self.assertIn(DOC["default_era"], keys)
        for k in keys:
            self.assertIn(k, DOC["surfaces"]["win"])
            self.assertIn(k, DOC["surfaces"]["runs"])
            # evidence parity: every surface ships a per-cell n for both dials
            self.assertIn(k, DOC["surfaces"]["win_n"])
            self.assertIn(k, DOC["surfaces"]["runs_n"])

    def test_win_n_is_engine_grid_verbatim(self):
        for era in DOC["surfaces"]["win_n"]:
            self.assertEqual(
                DOC["surfaces"]["win_n"][era],
                WPG["second_innings"]["surfaces"][era]["n"],
                msg=f"win_n {era} diverged from engine #3",
            )

    def test_runs_n_is_engine_reindexed(self):
        for era in DOC["surfaces"]["runs_n"]:
            if era == "ipl pooled":
                continue  # derived (sum of era n), checked below
            src = RE["surfaces"][era]["n"]
            got = DOC["surfaces"]["runs_n"][era]
            for ol in range(1, NOL + 1):
                for wih in range(1, NWH + 1):
                    self.assertEqual(got[ol - 1][wih - 1],
                                     src[NOL - ol][NWH - wih],
                                     msg=f"runs_n {era} ({ol},{wih}) re-index broken")

    def test_evidence_parity_both_leagues(self):
        # honesty parity (§0.1/§8): the same thresholds gate BOTH leagues, and
        # the IPL free-play grid is genuinely thin over much of the board (so the
        # gate has real work to do — this is the asymmetry the audit fixed).
        self.assertEqual(DOC["evidence"]["win_min_n"], wp.WPL_MASK_MIN_N)
        self.assertEqual(DOC["evidence"]["runs_min_n"], re288.MASK_MIN_N)
        pooled_n = DOC["surfaces"]["win_n"]["ipl pooled"]
        thin = sum(1 for ol in range(NOL) for w in range(NWH) for r in range(NRB)
                   if pooled_n[ol][w][r] < DOC["evidence"]["win_min_n"])
        self.assertGreater(thin, 0, msg="IPL pooled grid has no thin cells?")
        self.assertLess(thin, NOL * NWH * NRB, msg="IPL pooled grid is ALL thin?")
        # the default spot is evidenced, so the common path shows a real number
        self.assertGreaterEqual(pooled_n[9][5][4], DOC["evidence"]["win_min_n"])

    def test_corpus_counts_bound(self):
        c = DOC["corpus"]
        self.assertEqual(c["matches"], c["ipl_matches"] + c["wpl_matches"])
        self.assertEqual(c["matches"], 1331)
        self.assertEqual(c["wpl_matches"], 88)


# ===========================================================================
# Monotonicity in the widget coordinate
# ===========================================================================


class TestWidgetMonotonicity(unittest.TestCase):
    def test_runs_rise_with_resources(self):
        # more overs left -> more runs to come; more wickets in hand -> more runs
        for era, surf in DOC["surfaces"]["runs"].items():
            for ol in range(NOL - 1):
                for w in range(NWH):
                    self.assertLessEqual(surf[ol][w], surf[ol + 1][w] + 1e-6,
                                         msg=f"{era} runs fell with more overs")
            for ol in range(NOL):
                for w in range(NWH - 1):
                    self.assertLessEqual(surf[ol][w], surf[ol][w + 1] + 1e-6,
                                         msg=f"{era} runs fell with more wickets")

    def test_win_falls_with_rate_rises_with_wickets(self):
        for era, W in DOC["surfaces"]["win"].items():
            for ol in range(NOL):
                for w in range(NWH):
                    for r in range(NRB - 1):
                        self.assertGreaterEqual(
                            W[ol][w][r] + 1e-6, W[ol][w][r + 1],
                            msg=f"{era} win rose with a harder rate")
                for w in range(NWH - 1):
                    for r in range(NRB):
                        self.assertLessEqual(
                            W[ol][w][r], W[ol][w + 1][r] + 1e-6,
                            msg=f"{era} win fell with more wickets")


# ===========================================================================
# Preset integrity — the copy can never contradict the meter
# ===========================================================================


class TestPresets(unittest.TestCase):
    def _preset(self, pid):
        return next(p for p in DOC["presets"] if p["id"] == pid)

    def test_three_presets_present(self):
        ids = {p["id"] for p in DOC["presets"]}
        self.assertEqual(
            ids, {"dhoni_2018_chase", "halfway_2010", "same_chase_2025"})

    def test_no_preset_carries_a_defend_currency(self):
        # §9.2: the interlude is two-currency; no preset may reach for the defend
        # complement (the third currency the 2011-final preset introduced).
        for p in DOC["presets"]:
            self.assertNotIn("defend_pct", p, msg=f"{p['id']} still defends")
            self.assertNotIn("defend_display", p, msg=f"{p['id']} still defends")
            self.assertNotIn("first_innings_total", p.get("match", {}))

    def test_every_preset_matches_its_grid_cell(self):
        edges = DOC["state_space"]["rrr_edges"]
        for p in DOC["presets"]:
            era, s = p["era"], p["state"]
            rb = _rrr_bucket(s["runs_needed"], s["overs_left"], edges)
            win = DOC["surfaces"]["win"][era][s["overs_left"] - 1][
                s["wickets_in_hand"] - 1][rb]
            runs = DOC["surfaces"]["runs"][era][s["overs_left"] - 1][
                s["wickets_in_hand"] - 1]
            self.assertEqual(p["win_pct"], win, msg=f"{p['id']} win vs meter")
            self.assertEqual(p["expected_runs"], runs,
                             msg=f"{p['id']} runs vs meter")
            # display rounding is consistent with the raw value
            self.assertEqual(p["win_display"], round(win * 100))
            self.assertEqual(p["expected_runs_display"], round(runs))

    def test_dhoni_is_a_real_evidenced_chase(self):
        p = self._preset("dhoni_2018_chase")
        # rebuilt independently from the corpus
        state = interlude.dhoni_chase_state()
        self.assertEqual(p["state"], {
            "overs_left": state["overs_left"],
            "wickets_in_hand": state["wickets_in_hand"],
            "runs_needed": state["runs_needed"],
        })
        # the 2018 chase: Bangalore set the target, DHONI'S Chennai chased it down
        self.assertEqual(p["match"]["chasing"], "Chennai Super Kings")
        self.assertEqual(p["match"]["batting_first"],
                         "Royal Challengers Bengaluru")
        self.assertEqual(p["match"]["season"], 2018)
        self.assertEqual(p["match"]["target"], 206)
        self.assertEqual(p["match"]["result"]["winner"], "Chennai Super Kings")
        self.assertEqual(p["era"], "ipl 2016-2019")  # 2018 era band
        # a genuine chase state, not ball-one and not an imputed corner
        self.assertLess(p["state"]["overs_left"], NOL)
        # BLOCKING (§9.2): the state exists AND is evidenced in the win grid —
        # not an imputed cell dressed as an observed finding.
        s = p["state"]
        rb = _rrr_bucket(s["runs_needed"], s["overs_left"],
                         DOC["state_space"]["rrr_edges"])
        n = WPG["second_innings"]["surfaces"][p["era"]]["n"][
            s["overs_left"] - 1][s["wickets_in_hand"] - 1][rb]
        self.assertGreaterEqual(n, DOC["evidence"]["win_min_n"],
                                msg="Dhoni preset lands on a thin (unevidenced) cell")

    def test_same_chase_pair_shares_one_scoreboard(self):
        early = self._preset("halfway_2010")
        late = self._preset("same_chase_2025")
        # identical sliders — only the era differs (the whole point)
        self.assertEqual(early["state"], late["state"])
        self.assertNotEqual(early["era"], late["era"])
        self.assertEqual(early["era"], "ipl 2008-2010")
        self.assertEqual(late["era"], "ipl 2023-2026")
        # 10 overs left, needing 100 == exactly 10 an over
        self.assertEqual(early["state"]["overs_left"], 10)
        self.assertEqual(early["state"]["runs_needed"], 100)
        self.assertEqual(early["required_rate"], 10.0)
        # the interlude's punchline: same spot, the chase got easier
        self.assertGreater(late["win_pct"], early["win_pct"])
        self.assertGreater(late["expected_runs"], early["expected_runs"])
        # both cells carry real evidence (not a smoothing artifact)
        s = early["state"]
        for era in (early["era"], late["era"]):
            n = WPG["second_innings"]["surfaces"][era]["n"][
                s["overs_left"] - 1][s["wickets_in_hand"] - 1][
                _rrr_bucket(s["runs_needed"], s["overs_left"],
                            DOC["state_space"]["rrr_edges"])]
            self.assertGreaterEqual(n, 20, msg=f"{era} same-chase cell too thin")

    def test_presets_quote_both_currencies(self):
        for p in DOC["presets"]:
            self.assertIn("win_display", p)
            self.assertIn("expected_runs_display", p)
            self.assertIn("orient", p["copy"])
            self.assertIn("reveal", p["copy"])


# ===========================================================================
# The validated era anchor (same chase, two eras)
# ===========================================================================


class TestEraAnchor(unittest.TestCase):
    def test_anchor_is_the_gate_validated_number(self):
        anc = DOC["era_anchor"]
        # carried straight from the gate-validated grid
        self.assertEqual(anc["ipl_2008_2012"],
                         WPG["calibration"]["era_anchor"]["ipl_2008_2012"])
        self.assertEqual(anc["ipl_2023_2026"],
                         WPG["calibration"]["era_anchor"]["ipl_2023_2026"])
        early = anc["ipl_2008_2012"]["win_rate"]
        recent = anc["ipl_2023_2026"]["win_rate"]
        # blueprint draft prose: 24.3% -> 31.8%; validated grid: ~23% -> ~31%
        self.assertAlmostEqual(early, 0.243, delta=0.05)
        self.assertAlmostEqual(recent, 0.318, delta=0.05)
        self.assertGreater(recent, early)
        self.assertAlmostEqual(anc["delta_points"],
                               round((recent - early) * 100, 1), places=6)


# ===========================================================================
# WPL evidence mask
# ===========================================================================


class TestWPLMask(unittest.TestCase):
    def test_win_mask_flags_only_thin_cells(self):
        wpl = DOC["wpl"]
        self.assertEqual(wpl["win_mask_min_n"], wp.WPL_MASK_MIN_N)
        src = WPG["second_innings"]["surfaces"]["wpl 2023-2026"]
        masked = 0
        for ol in range(NOL):
            for w in range(NWH):
                for r in range(NRB):
                    if wpl["win_mask"][ol][w][r]:
                        masked += 1
                        self.assertLess(src["n"][ol][w][r], wp.WPL_MASK_MIN_N)
        self.assertEqual(masked, wpl["win_cells"]["masked"])
        self.assertEqual(wpl["win_cells"]["masked"] + wpl["win_cells"]["evidenced"],
                         wpl["win_cells"]["total"])
        # a young league: most cells masked, but a real core survives
        self.assertGreater(wpl["win_cells"]["masked"], 0)
        self.assertGreater(wpl["win_cells"]["evidenced"], 0)

    def test_runs_mask_flags_only_thin_cells(self):
        wpl = DOC["wpl"]
        self.assertEqual(wpl["runs_mask_min_n"], re288.MASK_MIN_N)
        src = RE["surfaces"]["wpl 2023-2026"]
        masked = 0
        for ol in range(1, NOL + 1):
            for wih in range(1, NWH + 1):
                if wpl["runs_mask"][ol - 1][wih - 1]:
                    masked += 1
                    self.assertLess(src["n"][NOL - ol][NWH - wih],
                                    re288.MASK_MIN_N)
        self.assertEqual(masked, wpl["runs_cells"]["masked"])
        self.assertGreater(wpl["runs_cells"]["masked"], 0)
        self.assertGreater(wpl["runs_cells"]["evidenced"], 0)


# ===========================================================================
# Footnotes — data-bound, recomputed
# ===========================================================================


class TestFootnotes(unittest.TestCase):
    def test_calibration_summary_matches_engine(self):
        fn = DOC["footnotes"]["calibration"]
        self.assertEqual(fn["win_ece"], WPG["calibration"]["ece"])
        self.assertEqual(fn["win_worst_populated_bin_abs_dev"],
                         WPG["calibration"]["worst_populated_bin_abs_dev"])
        self.assertEqual(fn["win_calibration_n"], WPG["calibration"]["n"])

    def test_wicket_lever_early_beats_late(self):
        # the footnote's claim must be true in the emitted grid: wickets are a
        # big lever early and (near) none late.
        fn = DOC["footnotes"]["wickets_early_rate_late"]
        self.assertGreater(fn["early_wicket_lever"], 0.15)
        self.assertLess(fn["late_wicket_lever"], 0.05)
        self.assertGreater(fn["early_wicket_lever"], fn["late_wicket_lever"])
        # and each number is the pooled grid readout it claims to be
        pooled = DOC["surfaces"]["win"]["ipl pooled"]
        rb = wp.rrr_bucket(11.5)
        self.assertEqual(
            fn["early_win_10_wkts"], pooled[fn["early_overs_left"] - 1][9][rb])
        self.assertEqual(
            fn["late_win_5_wkts"], pooled[fn["late_overs_left"] - 1][4][rb])

    def test_mask_thresholds_reported(self):
        fn = DOC["footnotes"]["evidence_mask"]
        self.assertEqual(fn["win_mask_min_n"], wp.WPL_MASK_MIN_N)
        self.assertEqual(fn["runs_mask_min_n"], re288.MASK_MIN_N)


# ===========================================================================
# Payload + determinism
# ===========================================================================


class TestPayloadAndDeterminism(unittest.TestCase):
    def test_within_chapter_budget(self):
        raw = (canon.OUT_ROOT / "scenes" / "interlude.json").read_bytes()
        gz = len(flatten.gz_bytes(raw))
        self.assertLess(gz, 2_000_000, msg="interlude scene over the 2MB budget")

    def test_on_disk_equals_fresh_recompute(self):
        on_disk = (canon.OUT_ROOT / "scenes" / "interlude.json").read_bytes()
        fresh = flatten.compact_json(interlude.build_doc(), sort_keys=True)
        self.assertEqual(on_disk, fresh,
                         msg="interlude.json is not byte-deterministic")


if __name__ == "__main__":
    unittest.main()
