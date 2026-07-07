"""R3b-2 — Chapter 5 "What a Ball Is Worth" (scenes/ch5.json + wpa.u8 +
restate.u8).

The engines' correctness is tests/test_engines.py's job; these tests protect
what ch5.py builds ON them:

  * BUFFER CONTRACTS — both buffers are n_points long in field point order;
    restate.u8 round-trips against an independent per-delivery recount of a
    known match (the 2019 final) and never packs an impossible state; wpa.u8's
    sentinel set is exactly the balls of D/L / undecided / short-target
    matches; a fresh re-encode equals the bytes on disk.
  * A KNOWN FAMOUS BALL — the last ball of the 2019 final (Malinga to Thakur,
    lbw): the buffer byte decodes to the negative of the era grid's readout at
    (needed 2, 1 ball left, 4 in hand), the exact number the scrub quotes.
  * WPA CONSISTENCY — per-innings-2 WPA telescopes to (result − first-state
    WP) exactly, re-derived independently for a sample of matches.
  * THE SCRUB OVER — matches the raw 2019 final delivery-for-delivery
    (batters, bowler, runs, the Watson run out, the Thakur lbw, needed-before
    countdown 9/8/7/5/4/2), resolves by identity to match_index 755, and its
    worm hits the grid readouts with the final ball resolving to 0.
  * THE VALIDATIONS — defended band (73.2% -> 38.9%), the single flip
    (-0.013 -> -0.248) and dot deepening, the third-wicket collapse, the
    Wicket Value Index appreciation above run inflation, the finisher cliff
    (54.8% -> 85.4% with the fatal band moving 10 -> 12), each against an
    independent recount where the artifact quotes raw numbers.
  * PAYOFF — 20 franchise cards, most-valuable balls verifiable against the
    corpus, replays well-formed, runners-up from distinct matches, the WPL
    short-history state designed in.
  * DETERMINISM + BUDGET — on-disk artifacts equal a fresh build byte-for-
    byte; the chapter set fits the 2 MB gz budget.
"""

from __future__ import annotations

import gzip
import json
import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import canon
import ch5
import flatten
import wp as wpmod

DOC = None
ACC = None
FRESH_DOC = None
WPA = None
RESTATE = None
COLUMNAR = None
MATCHES = None
FILES = None

N_POINTS = 316_199
SCRUB_MATCH_INDEX = 755


def setUpModule():
    global DOC, ACC, FRESH_DOC, WPA, RESTATE, COLUMNAR, MATCHES, FILES
    out = canon.OUT_ROOT
    if not (out / "scenes" / "ch5.json").exists():
        ch5.main()
    DOC = json.loads((out / "scenes" / "ch5.json").read_text())
    WPA = (out / "wpa.u8").read_bytes()
    RESTATE = (out / "restate.u8").read_bytes()
    COLUMNAR = json.loads(gzip.decompress((out / "columnar.json.gz").read_bytes()))
    MATCHES = json.loads((out / "matches.json").read_text())
    FILES = flatten.sorted_match_files()
    # ONE fresh recompute serves both the determinism check and every test
    # that reads the engines / accumulators.
    FRESH_DOC, ACC = ch5.build_doc()


def match_slice(match_index: int):
    """[start, end) of a match's points in the field point order."""
    mi = COLUMNAR["arrays"]["match_index"]
    start = mi.index(match_index)
    end = start
    while end < len(mi) and mi[end] == match_index:
        end += 1
    return start, end


class TestBufferContracts(unittest.TestCase):
    def test_lengths(self):
        self.assertEqual(len(WPA), N_POINTS)
        self.assertEqual(len(RESTATE), N_POINTS)

    def test_restate_range_and_packing(self):
        arr = COLUMNAR["arrays"]
        overs = arr["over"]
        for i in range(0, N_POINTS, 997):  # coarse full-stream sweep
            b = RESTATE[i]
            self.assertLess(b, 200)
            self.assertEqual(b // 10, overs[i])
            self.assertLessEqual(b % 10, 9)

    def test_restate_roundtrip_2019_final(self):
        """Independent recount of the scrub match, delivery for delivery."""
        start, end = match_slice(SCRUB_MATCH_INDEX)
        arr = COLUMNAR["arrays"]
        wkts = 0
        innings = None
        for i in range(start, end):
            if arr["innings"][i] != innings:
                innings = arr["innings"][i]
                wkts = 0
            self.assertEqual(RESTATE[i], arr["over"][i] * 10 + wkts,
                             f"restate mismatch at point {i}")
            wkts += arr["wicket"][i]

    def test_wpa_sentinel_set_is_exact(self):
        """Sentinel bytes are exactly the balls of D/L, undecided and
        short-target matches (independent classification per match)."""
        arr = COLUMNAR["arrays"]
        mi = arr["match_index"]
        sentinel_m = set()
        for match_index, (_d, _m, league, path) in enumerate(FILES):
            with open(path) as fh:
                m = json.load(fh)
            info = m["info"]
            inns = [i for i in m.get("innings", [])
                    if not canon.is_super_over(i)]
            target = inns[1].get("target") if len(inns) > 1 else None
            cw = (wpmod.chaser_won(info, inns[1]["team"])
                  if len(inns) > 1 else None)
            if (canon.is_dl(info) or cw is None or not target
                    or target.get("overs") != 20):
                sentinel_m.add(match_index)
        n_sent = 0
        for i in range(N_POINTS):
            if WPA[i] == ch5.WPA_SENTINEL:
                n_sent += 1
                self.assertIn(mi[i], sentinel_m)
            else:
                self.assertNotIn(mi[i], sentinel_m)
        self.assertEqual(n_sent, DOC["wpa_buffer"]["sentinel_count"])

    def test_buffers_deterministic(self):
        self.assertEqual(WPA, ACC["wpa_bytes"])
        self.assertEqual(RESTATE, ACC["restate_bytes"])


class TestFamousBall(unittest.TestCase):
    def test_malinga_final_ball_sign_and_magnitude(self):
        start, end = match_slice(SCRUB_MATCH_INDEX)
        arr = COLUMNAR["arrays"]
        last = end - 1
        self.assertEqual(arr["wicket"][last], 1)
        # the era grid's readout at (1 ball left, 4 in hand, needed 2)
        grid = ACC["engines"]["wp"]["ipl 2016-2019"]
        rb = wpmod.rrr_bucket(2 * 6.0 / 1)
        expected = -grid[0][3][rb]
        decoded = (WPA[last] - 127) / 127
        self.assertLess(decoded, 0)  # CSK batting, the ball killed the chase
        self.assertAlmostEqual(decoded, expected, delta=1 / 127 + 1e-9)
        # and it is the exact number the scrub quotes
        self.assertAlmostEqual(DOC["scrub"]["balls"][-1]["wpa"],
                               round(expected, 4), places=4)

    def test_smith_2012_last_ball_four(self):
        """MI's most valuable ball ever: DR Smith, needing 4 off 1, 2012."""
        card = [v for v in DOC["payoff"]["variants"] if v["short"] == "MI"][0]
        top = card["most_valuable"]
        self.assertGreater(top["swing"], 0.9)
        self.assertEqual(top["batter"], "DR Smith")
        self.assertEqual(top["runs_batter"], 4)
        self.assertEqual(top["needed_before"], 4)
        self.assertEqual(top["balls_left_before"], 1)
        self.assertEqual(
            MATCHES[top["match_index"]]["result_text"],
            "Mumbai Indians won by 2 wickets")


class TestWpaConsistency(unittest.TestCase):
    def test_innings2_telescopes_to_result(self):
        """Decoded buffer WPA over innings 2 sums to (result − first WP)
        within quantization noise, for a sample of decided matches."""
        self.assertLess(DOC["wpa"]["closure"]["max_abs_gap"], 1e-9)
        arr = COLUMNAR["arrays"]
        checked = 0
        for match_index in range(0, len(MATCHES), 97):
            start, end = match_slice(match_index)
            if WPA[start] == ch5.WPA_SENTINEL:
                continue
            pts = [i for i in range(start, end) if arr["innings"][i] == 2]
            if not pts:
                continue
            s = sum((WPA[i] - 127) / 127 for i in pts)
            # result from the corpus: first-state WP + sum telescopes to it
            _d, _m, league, path = FILES[match_index]
            with open(path) as fh:
                m = json.load(fh)
            inns = [i for i in m.get("innings", [])
                    if not canon.is_super_over(i)]
            cw = wpmod.chaser_won(m["info"], inns[1]["team"])
            era = ch5.band_key(league, canon.canon_season(m["info"]))
            wp0 = ch5.wp_chase(ACC["engines"], era, 0, 0, 0,
                               inns[1]["target"]["runs"])
            self.assertLess(abs((wp0 + s) - cw), 0.004 * len(pts) + 0.01,
                            f"telescoping broke on match {match_index}")
            checked += 1
        self.assertGreater(checked, 5)

    def test_coverage_counts(self):
        cov = DOC["wpa"]["coverage"]
        self.assertEqual(cov["balls_scored"] + cov["balls_sentinel"], N_POINTS)
        sm = cov["sentinel_matches"]
        self.assertEqual(sm["dl"], 23)  # the corpus's 23 D/L results

    def test_top_swings_are_endgame_and_distinct(self):
        rows = DOC["wpa"]["top_swings"]
        self.assertEqual(len(rows), 10)
        self.assertEqual(len({r["match_index"] for r in rows}), 10)
        for r in rows:
            self.assertGreaterEqual(abs(r["wpa"]), 0.3)
            self.assertNotIn("—", r["what_happened"])  # voice guide


class TestScrubOver(unittest.TestCase):
    def test_resolves_by_identity_to_755(self):
        self.assertEqual(DOC["scrub"]["match_index"], SCRUB_MATCH_INDEX)
        rec = MATCHES[SCRUB_MATCH_INDEX]
        self.assertEqual(rec["result_text"], "Mumbai Indians won by 1 run")
        self.assertEqual(rec["stage"], "Final")
        self.assertEqual(rec["season"], 2019)

    def test_ball_by_ball_matches_raw_data(self):
        balls = DOC["scrub"]["balls"]
        self.assertEqual(len(balls), 6)
        expect = [
            ("SR Watson", 1, None), ("RA Jadeja", 1, None),
            ("SR Watson", 2, None), ("SR Watson", 1, "run out"),
            ("SN Thakur", 2, None), ("SN Thakur", 0, "lbw"),
        ]
        for b, (batter, runs, kind) in zip(balls, expect):
            self.assertEqual(b["batter"], batter)
            self.assertEqual(b["runs_total"], runs)
            self.assertEqual(b["bowler"], "SL Malinga")
            self.assertEqual((b["wicket"] or {}).get("kind"), kind)
        self.assertEqual([b["needed_before"] for b in balls],
                         [9, 8, 7, 5, 4, 2])
        self.assertEqual([b["balls_left_before"] for b in balls],
                         [6, 5, 4, 3, 2, 1])
        self.assertEqual(DOC["scrub"]["entering"],
                         {"score": 141, "needed": 9, "balls_left": 6,
                          "wickets_down": 5, "bowler": "SL Malinga"})

    def test_point_indices_are_the_final_over_in_field_order(self):
        """The emitted rail indices (scrub.point_indices) are exactly the
        2019 final's innings-2 over-20 deliveries in the shared field point
        order — the scene lifts THESE, never a runtime columnar derivation."""
        start, end = match_slice(SCRUB_MATCH_INDEX)
        arr = COLUMNAR["arrays"]
        expect = [i for i in range(start, end)
                  if arr["innings"][i] == 2 and arr["over"][i] == 19]
        self.assertEqual(len(expect), 6)
        self.assertEqual(DOC["scrub"]["point_indices"], expect)
        self.assertEqual([b["point_index"] for b in DOC["scrub"]["balls"]],
                         expect)

    def test_worm_reads_the_era_grid_and_resolves(self):
        grid = ACC["engines"]["wp"]["ipl 2016-2019"]
        balls = DOC["scrub"]["balls"]
        for b in balls:
            bl = b["balls_left_before"]
            ol = math.ceil(bl / 6) - 1
            wih = b["wickets_in_hand_before"] - 1
            rb = wpmod.rrr_bucket(b["needed_before"] * 6.0 / bl)
            self.assertAlmostEqual(b["wp_before"],
                                   round(grid[ol][wih][rb], 4), places=4)
            self.assertAlmostEqual(b["wpa"], round(b["wp_after"]
                                                   - b["wp_before"], 4),
                                   places=3)
        self.assertEqual(balls[-1]["wp_after"], 0.0)  # CSK lost
        for b in balls:  # observed dots carry real evidence
            self.assertGreater(b["observed"]["n"], 0)


class TestValidations(unittest.TestCase):
    def test_defended_band(self):
        d = DOC["defended_band"]
        early = d["raw"]["ipl 2008-2010"]
        recent = d["raw"]["ipl 2023-2026"]
        self.assertEqual((early["defended"], early["n"]), (30, 41))
        self.assertEqual((recent["defended"], recent["n"]), (21, 54))
        self.assertAlmostEqual(early["pct"], 73.2)
        self.assertAlmostEqual(recent["pct"], 38.9)
        # the same-scoreboard repricing story: ~34 points of win prob gone
        self.assertGreater(d["headline"]["delta_points"], 30)

    def test_single_flip_and_dot_deepening(self):
        lw = DOC["linear_weights"]["era_bands"]
        early, recent = lw["ipl 2008-2010"], lw["ipl 2023-2026"]
        self.assertAlmostEqual(early["single"]["value"], -0.013, places=3)
        self.assertAlmostEqual(recent["single"]["value"], -0.248, places=3)
        self.assertGreater(early["single"]["value"], -0.05)  # value-neutral
        self.assertLess(recent["single"]["value"], -0.2)     # value-losing
        self.assertAlmostEqual(early["dot"]["value"], -0.898, places=3)
        self.assertAlmostEqual(recent["dot"]["value"], -1.115, places=3)
        self.assertLess(recent["dot"]["value"], early["dot"]["value"])
        # sixes hold near +4.6; the wicket event deepened
        self.assertAlmostEqual(recent["six"]["value"], 4.6, delta=0.15)
        self.assertLess(recent["wicket"]["value"], early["wicket"]["value"])

    def test_third_wicket_collapse(self):
        tw = DOC["re_drift"]["third_wicket"]["raw"]
        self.assertAlmostEqual(tw["2008-2010"]["third_wicket_cost"], 11.81,
                               places=2)
        self.assertLess(tw["2023-2026"]["third_wicket_cost"], 4.5)
        self.assertLess(tw["2024-2026"]["third_wicket_cost"], 1.5)
        self.assertAlmostEqual(tw["2008-2010"]["re_2_down"], 110.3, delta=0.1)
        for w in ("2008-2010", "2023-2026", "2024-2026"):
            self.assertGreater(tw[w]["n_2_down"], 20)

    def test_wicket_value_appreciates_faster_than_runs(self):
        wv = DOC["wicket_value"]
        self.assertAlmostEqual(wv["headline"]["early"], 4.155, places=3)
        self.assertAlmostEqual(wv["headline"]["recent"], 5.113, places=3)
        ctx = wv["run_rate_context"]
        self.assertGreater(ctx["wicket_appreciation_pct"],
                           ctx["run_inflation_pct"])
        self.assertGreater(wv["window_2024_2026"]["expected_runs_removed"],
                           5.4)  # the catalog's sharper window, ~+33%

    def test_finisher_cliff(self):
        f = DOC["finisher"]["table"]
        e, r = f["ipl 2008-2010"], f["ipl 2023-2026"]
        self.assertEqual((e["8-10"]["wins"], e["8-10"]["n"]), (17, 31))
        self.assertEqual((r["8-10"]["wins"], r["8-10"]["n"]), (35, 41))
        self.assertAlmostEqual(e["8-10"]["win_pct"], 54.8)
        self.assertAlmostEqual(r["8-10"]["win_pct"], 85.4)
        # the fatal band moved from ~10 to ~12
        self.assertLess(e["10-12"]["win_pct"], 50)
        self.assertGreaterEqual(r["10-12"]["win_pct"], 45)
        self.assertLess(e["12+"]["win_pct"], 20)
        self.assertLess(r["12+"]["win_pct"], 20)

    def test_chase_difficulty_footnote(self):
        cd = DOC["footnotes"]["chase_difficulty"]["by_band"]
        self.assertEqual((cd["ipl 2008-2010"]["wins"],
                          cd["ipl 2008-2010"]["n"]), (25, 37))
        self.assertEqual((cd["ipl 2023-2026"]["wins"],
                          cd["ipl 2023-2026"]["n"]), (37, 42))

    def test_re_drift_grids_are_engine_verbatim(self):
        re_doc = json.loads((canon.OUT_ROOT / "engines" / "re288.json")
                            .read_text())
        d = DOC["re_drift"]
        self.assertEqual(d["re_a"],
                         re_doc["surfaces"]["ipl 2008-2010"]["re"])
        self.assertEqual(d["re_b"],
                         re_doc["surfaces"]["ipl 2023-2026"]["re"])
        for o in range(20):
            for w in range(10):
                self.assertAlmostEqual(
                    d["diff"][o][w],
                    round(d["re_b"][o][w] - d["re_a"][o][w], 1), places=1)

    def test_rise_lens_caption_claims(self):
        """CAPTION == ARTIFACT (release-blocking, storyboard §3/§4): the
        C5-6a step-3 caption (EraFlip.svelte) reads the rise lens as
        'brightest at the LEFT EDGE, fading toward the death'. This test is
        the QA assertion tying that location clause to the emitted diff
        maxima — if the table's shape moves, the copy must be rewritten."""
        diff = DOC["re_drift"]["diff"]
        maxpos = max(diff[o][w] for o in range(20) for w in range(10))
        # over 1's pooled column (the whole innings still ahead) sits within
        # a whisker of the global maximum — the lens's brightest region
        self.assertGreaterEqual(min(diff[0]), 0.85 * maxpos)
        # ... and the rise fades toward the death in every populated band
        # (0-3 down): the first six overs out-rise the last six
        for w in range(4):
            early = sum(diff[o][w] for o in range(6)) / 6
            late = sum(diff[o][w] for o in range(14, 20)) / 6
            self.assertGreater(early, late,
                               f"rise not front-loaded at {w} down")
        # the storyboard's ORIGINAL middle-overs clause must stay retired:
        # no populated middle-overs cell out-rises the over-1 column
        mid_max = max(diff[o][w] for o in range(6, 15) for w in range(4))
        self.assertLess(mid_max, min(diff[0]))
        # the ch5-drift footnote's phase-mean claim (the middle overs are
        # the only PHASE whose cell-average rose) stays true alongside
        ph = DOC["re_drift"]["diff_by_phase"]
        self.assertGreater(ph["middle_overs_7_15"], 0)
        self.assertLess(ph["powerplay_overs_1_6"], 0)
        self.assertLess(ph["death_overs_16_20"], 0)

    def test_price_board_covers_every_season(self):
        rows = DOC["price_board"]["seasons"]
        self.assertEqual(len(rows), 19 + 4)
        for row in rows:
            for cls in ("dot", "single", "four", "six", "wicket"):
                self.assertIsNotNone(row[cls])
            self.assertLess(row["dot"], 0)
            self.assertGreater(row["four"], 2)
            self.assertLess(row["wicket"], -4)


class TestPayoff(unittest.TestCase):
    def test_twenty_cards_no_empty_states(self):
        variants = DOC["payoff"]["variants"]
        self.assertEqual(len(variants), 20)
        self.assertEqual([v["team_id"] for v in variants], list(range(20)))
        for v in variants:
            self.assertFalse(v["empty_state"])
            self.assertEqual(len(v["runners_up"]), 4)

    def test_most_valuable_balls_are_real_and_positive(self):
        for v in DOC["payoff"]["variants"]:
            top = v["most_valuable"]
            self.assertGreater(top["swing"], ch5.PAYOFF_MIN_SWING)
            rec = MATCHES[top["match_index"]]
            self.assertEqual(rec["league"], v["league"])
            self.assertEqual(rec["season"], top["season"])
            self.assertIn(v["team"], rec["teams"])
            self.assertEqual(top["opponent"],
                             [t for t in rec["teams"] if t != v["team"]][0])
            # the quoted worm endpoints agree with the quoted swing
            self.assertAlmostEqual(
                top["swing"],
                round(top["wp_team_after"] - top["wp_team_before"], 4),
                delta=0.0002)
            self.assertNotIn("—", top["what_happened"])

    def test_replays_contain_their_top_ball(self):
        for v in DOC["payoff"]["variants"]:
            top, replay = v["most_valuable"], v["replay"]
            labels = [b["label"] for b in replay["balls"]]
            self.assertIn(top["label"], labels)
            # an over holds 6 legal balls but can record fewer when the
            # match ends mid-over, or more when extras stretch it
            self.assertGreaterEqual(len(replay["balls"]), 1)
            self.assertLessEqual(len(replay["balls"]), 12)
            for b in replay["balls"]:
                self.assertGreaterEqual(b["wp_team_before"], 0.0)
                self.assertLessEqual(b["wp_team_before"], 1.0)

    def test_point_index_and_state_cell_round_trip(self):
        """Every payoff ball's emitted point_index / state_cell agree with
        the shared buffers — the C5-11 single-point ignite lifts the real
        ball at its real worth-grid cell."""
        for v in DOC["payoff"]["variants"]:
            for r in [v["most_valuable"]] + v["runners_up"]:
                pi = r["point_index"]
                self.assertEqual(COLUMNAR["arrays"]["match_index"][pi],
                                 r["match_index"])
                self.assertEqual(RESTATE[pi], r["state_cell"])
                decoded = (WPA[pi] - 127) / 127
                self.assertAlmostEqual(abs(decoded), r["swing"],
                                       delta=1 / 127 + 1e-3)

    def test_season_gallery_one_ball_per_season(self):
        """The neutral payoff gallery lists ONE ball per season (storyboard
        §4 payoff QA), every season covered, each traceable to the buffers."""
        rows = DOC["wpa"]["season_gallery"]
        keys = [(r["league"], r["season"]) for r in rows]
        self.assertEqual(len(keys), len(set(keys)))
        ipl = [s for lg, s in keys if lg == "ipl"]
        wpl = [s for lg, s in keys if lg == "wpl"]
        self.assertEqual(len(ipl), 19)   # every IPL season 2008-2026
        self.assertEqual(len(wpl), 4)    # every WPL season 2023-2026
        self.assertEqual(ipl, sorted(ipl))
        self.assertEqual(wpl, sorted(wpl))
        for r in rows:
            self.assertGreaterEqual(abs(r["wpa"]), 0.3)
            pi = r["point_index"]
            self.assertEqual(COLUMNAR["arrays"]["match_index"][pi],
                             r["match_index"])
            self.assertEqual(RESTATE[pi], r["state_cell"])

    def test_runners_up_distinct_matches(self):
        for v in DOC["payoff"]["variants"]:
            mis = [v["most_valuable"]["match_index"]] + \
                  [r["match_index"] for r in v["runners_up"]]
            self.assertEqual(len(mis), len(set(mis)))
            swings = [v["most_valuable"]["swing"]] + \
                     [r["swing"] for r in v["runners_up"]]
            self.assertEqual(swings, sorted(swings, reverse=True))

    def test_wpl_short_history_designed_state(self):
        for v in DOC["payoff"]["variants"]:
            if v["league"] == "wpl":
                self.assertTrue(v["short_history"])
                self.assertTrue(v["honesty"])
                self.assertNotIn("behind", v["honesty"].lower())
            else:
                self.assertFalse(v["short_history"])
                self.assertEqual(v["honesty"], "")


class TestWplBeat(unittest.TestCase):
    def test_mask_is_engine_verbatim(self):
        re_doc = json.loads((canon.OUT_ROOT / "engines" / "re288.json")
                            .read_text())
        mask = re_doc["surfaces"]["wpl 2023-2026"]["masked"]
        cells = {(o, w) for o in range(20) for w in range(10) if mask[o][w]}
        got = {tuple(c) for c in DOC["wpl_beat"]["mask"]["masked_cells"]}
        self.assertEqual(got, cells)
        self.assertEqual(DOC["wpl_beat"]["mask"]["cells_masked"], len(cells))
        self.assertGreater(len(cells), 0)
        self.assertLess(len(cells), 200)

    def test_observed_dots_only_on_masked_cells_with_evidence(self):
        masked = {tuple(c) for c in DOC["wpl_beat"]["mask"]["masked_cells"]}
        re_doc = json.loads((canon.OUT_ROOT / "engines" / "re288.json")
                            .read_text())
        n_grid = re_doc["surfaces"]["wpl 2023-2026"]["n"]
        for cell in DOC["wpl_beat"]["observed_dots"]["cells"]:
            self.assertIn((cell["o"], cell["w"]), masked)
            self.assertEqual(cell["n"], len(cell["observed_runs_to_come"]))
            self.assertEqual(cell["n"], n_grid[cell["o"]][cell["w"]])
            self.assertAlmostEqual(
                cell["mean"],
                round(sum(cell["observed_runs_to_come"]) / cell["n"], 1),
                places=1)

    def test_match_counts_from_corpus(self):
        """The C5-10 on-screen literals ('88 matches, not 1,331') trace to
        emitted fields counted from the corpus, never typed."""
        mc = DOC["wpl_beat"]["match_counts"]
        self.assertEqual(mc["total"], len(MATCHES))
        self.assertEqual(mc["wpl"],
                         sum(1 for m in MATCHES if m["league"] == "wpl"))
        self.assertEqual(mc["ipl"] + mc["wpl"], mc["total"])
        self.assertEqual((mc["wpl"], mc["total"]), (88, 1331))

    def test_wpl_finisher_between_the_eras(self):
        f = DOC["wpl_beat"]["finisher_8_10"]
        self.assertEqual((f["wins"], f["n"]), (9, 11))
        e = DOC["finisher"]["table"]["ipl 2008-2010"]["8-10"]["win_pct"]
        r = DOC["finisher"]["table"]["ipl 2023-2026"]["8-10"]["win_pct"]
        self.assertGreater(f["win_pct"], e)
        self.assertLessEqual(f["win_pct"], r)


class TestEraSwapFootnote(unittest.TestCase):
    def test_gilchrist_exhibit(self):
        es = DOC["footnotes"]["era_swap"]
        self.assertEqual(es["batter"], "AC Gilchrist")
        self.assertEqual(es["runs"], 109)
        self.assertEqual(es["match"]["season"], 2008)
        self.assertEqual(es["match"]["result_text"],
                         "Deccan Chargers won by 10 wickets")
        self.assertLess(es["chase_start_wp_2008_2010"],
                        es["chase_start_wp_2023_2026"])


class TestPayloadAndDeterminism(unittest.TestCase):
    def test_within_chapter_budget(self):
        total = 0
        for name in ("scenes/ch5.json", "wpa.u8", "restate.u8"):
            raw = (canon.OUT_ROOT / name).read_bytes()
            total += len(gzip.compress(raw, compresslevel=9, mtime=0))
        self.assertLessEqual(total, 2_000_000)

    def test_on_disk_equals_fresh_recompute(self):
        raw = flatten.compact_json(FRESH_DOC, sort_keys=True)
        self.assertEqual(raw, (canon.OUT_ROOT / "scenes" / "ch5.json")
                         .read_bytes())
        self.assertEqual(ACC["wpa_bytes"], WPA)
        self.assertEqual(ACC["restate_bytes"], RESTATE)

    def test_meta_registers_the_artifacts(self):
        meta = json.loads((canon.OUT_ROOT / "meta.json").read_text())
        for name in ("wpa.u8", "restate.u8", "scenes/ch5.json"):
            self.assertIn(name, meta["files"])
            self.assertEqual(
                meta["files"][name]["bytes_raw"],
                len((canon.OUT_ROOT / name).read_bytes()))


if __name__ == "__main__":
    unittest.main()
