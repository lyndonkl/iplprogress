"""R6a — Chapter 10 "The Era Machine", the FINALE (scenes/ch10.json, buffer-free).

The single move of the finale: we stop narrating eras and let the data draw its own
fault lines. One hero (the league-pulse SEISMOGRAPH: staggered cracks fall through the
chronological ribbon, a strictness dial loosens six eras to two) and three supporting
beats (the FAULT MAP subway, the BRIDGE-PLAYER verdict that closes the 2023 mystery,
the PLAYER TELEPORTER), plus the WPL CONVERGENCE clock and a 16-card payoff. Every
on-screen number is asserted against the EMITTED scenes/ch10.json (loaded from disk,
the artifact that ships) and pinned to the digest's verified numbers.

ARTIFACT WINS. Six findings are honest deltas away from an older teaser and ship
straight; they are asserted AS deltas, never fudged toward the teaser:

  * SIXES broke 2014 (primary), then 2018 (station), NOT one clean 2018.
  * TURNOVER was about two-thirds of the 2023-24 jump (67%), NOT three-quarters.
  * The naive era-translation ceiling is about 224 (naive_ceiling), NOT 228.
  * "How far above his own era" ships as a percent-above-par gap (SR+/pct_above_par),
    NEVER a z-score; the blueprint z magnitudes were not reproducible and are dropped.
  * The men's game crosses ten an over about 2028-29 (central 2028.8, band to 2031),
    NOT the optimistic 2027.
  * The WPL is owned as barely foreseeable on four seasons (run rate closes first,
    six-hitting off the clock), and is NEVER "behind".

Load-bearing exacts pinned: strictness sweep 6/4/3/2/1 eras at beta 0.3/0.6/1.0/4.0/14;
Sehwag 2008 SR 184.55; Gayle 2011 SR+ 156.7 > Fraser-McGurk 2024 SR+ 135.4 despite a raw
gap of 50.9; the honest band < the naive-vs-percentile gap for every teleport (the ghost
sits clear of the band); 16 payoff variants (10 IPL + 5 WPL + 1 neutral), all 5 WPL
bespoke. VOICE: zero em dashes anywhere; no z-score and no "behind" in the on-screen copy
(both live only in the one-click-deep honesty footnotes). DETERMINISM: a fresh build
equals itself and the on-disk bytes. The field stays BUFFER-FREE and at 14 attributes.
"""

from __future__ import annotations

import json
import re
import sys
import unittest
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import canon
import flatten
import ch10

TESTS_DIR = Path(__file__).resolve().parent

DOC = None
DISK_BYTES = None


def setUpModule():
    global DOC, DISK_BYTES
    scene_path = canon.OUT_ROOT / "scenes" / "ch10.json"
    if not scene_path.exists():
        ch10.main()
    DISK_BYTES = scene_path.read_bytes()
    DOC = json.loads(DISK_BYTES)  # the emitted artifact, exactly as it ships


# --------------------------------------------------------------------------
# string / key walkers
# --------------------------------------------------------------------------


def _iter_strings(obj):
    if isinstance(obj, dict):
        for v in obj.values():
            yield from _iter_strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _iter_strings(v)
    elif isinstance(obj, str):
        yield obj


def _iter_keys(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k
            yield from _iter_keys(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _iter_keys(v)


def _onscreen(doc):
    """The on-screen copy is everything EXCEPT the footnotes subtree. Footnotes are
    the one-click-deep progressive-disclosure layer where the technical names, the
    z-honesty note, and the 'the WPL is never behind' framing statement legitimately
    live (glossary rule / §0.2). The on-screen copy must carry neither a z-score nor
    'behind'."""
    return {k: v for k, v in doc.items() if k != "footnotes"}


# ===========================================================================
# (1) The seismograph — staggered cracks, the strictness dial (6->2 eras), the
#     fault map break years, posteriors in [0,1], crack point-positions present
# ===========================================================================


class SeismographTest(unittest.TestCase):
    def setUp(self):
        self.seis = DOC["seismograph"]
        self.strict = self.seis["strictness"]
        self.fm = DOC["fault_map"]

    def test_strictness_dial_loosens_six_eras_to_two(self):
        stops = self.strict["stops"]
        betas = [s["beta"] for s in stops]
        n_eras = [s["n_eras"] for s in stops]
        # the penalty sweep: 6/4/3/2/1 eras (digest "6 loose -> 2 strict CONFIRMED")
        self.assertEqual(betas, [0.3, 0.6, 1.0, 4.0, 14.0])
        self.assertEqual(n_eras, [6, 4, 3, 2, 1])
        # each stop's break_years match the verified sweep
        by_beta = {s["beta"]: s["break_years"] for s in stops}
        self.assertEqual(by_beta[0.3], [2009, 2010, 2014, 2023, 2024])
        self.assertEqual(by_beta[0.6], [2014, 2023, 2024])
        self.assertEqual(by_beta[1.0], [2014, 2024])
        self.assertEqual(by_beta[4.0], [2023])   # the one dominant modern fault
        self.assertEqual(by_beta[14.0], [])      # one era, no cracks
        # n_eras is exactly one more than the number of cracks at each stop
        for s in stops:
            self.assertEqual(s["n_eras"], len(s["break_years"]) + 1)
            self.assertEqual(len(s["cracks"]), len(s["break_years"]))
        # the default the dial rests on is the four-era reading
        self.assertEqual(self.strict["default_beta"], 0.6)
        self.assertEqual(self.strict["default_n_eras"], 4)

    def test_fault_map_break_years_per_metric(self):
        by_key = {m["key"]: m for m in self.fm["metrics"]}
        # the three load-bearing primaries (digest FAULT MAP)
        self.assertEqual(by_key["six_rate"]["primary"], 2014)
        self.assertEqual(by_key["run_rate"]["primary"], 2023)
        self.assertEqual(by_key["wide_rate"]["primary"], 2022)
        # the two co-breaking supporters
        self.assertEqual(by_key["dot_rate"]["primary"], 2016)
        self.assertEqual(by_key["boundary_rate"]["primary"], 2023)

    def test_sixes_broke_2014_then_2018_not_a_clean_2018(self):
        six = next(m for m in self.fm["metrics"] if m["key"] == "six_rate")
        years = [st["year"] for st in six["stations"]]
        # the honest delta: 2014 is the dominant fault and 2018 is a real station,
        # so the story ships "2014, then 2018", NEVER a single clean 2018
        self.assertEqual(six["primary"], 2014)
        self.assertNotEqual(six["primary"], 2018)
        self.assertIn(2014, years)
        self.assertIn(2018, years)
        self.assertEqual(years, [2014, 2018, 2022, 2024])

    def test_order_gap_six_preceded_scoring_by_about_five_years(self):
        og = self.fm["order_gap"]
        self.assertEqual(og["six_year"], 2018)
        self.assertEqual(og["scoring_year"], 2023)
        self.assertEqual(og["years"], 5)              # 2018 six vs 2023 run = exactly 5
        self.assertEqual(og["alt_six_year"], 2014)
        self.assertEqual(og["alt_years"], 9)          # 2014 vs 2023 = 9, order unambiguous

    def test_all_posteriors_in_unit_interval(self):
        for metric, rows in self.seis["bayes_posterior"].items():
            for r in rows:
                self.assertTrue(0.0 <= r["posterior"] <= 1.0,
                                f"{metric} {r['break_year']} p={r['posterior']}")
        for c in self.seis["cracks"]:
            self.assertTrue(0.0 <= c["posterior"] <= 1.0, c)
        for s in self.strict["stops"]:
            for c in s["cracks"]:
                self.assertTrue(0.0 <= c["posterior"] <= 1.0, c)
        # the evidence is honestly modest: the declared range and the strongest fault
        self.assertEqual(self.seis["posterior_range"], [0.15, 0.44])
        strongest = self.seis["strongest_faults"][0]
        self.assertEqual(strongest["metric"], "wide_rate")
        self.assertEqual(strongest["year"], 2022)
        self.assertAlmostEqual(strongest["posterior"], 0.4374, places=3)
        # run-rate 2023 is the strongest fault on the composite dial (the mystery year)
        self.assertEqual(self.strict["strongest_fault"]["metric"], "run_rate")
        self.assertEqual(self.strict["strongest_fault"]["year"], 2023)

    def test_crack_point_positions_present_and_valid(self):
        cracks = self.seis["cracks"]
        self.assertGreater(len(cracks), 0)
        total = DOC["ribbon"]["total_points"]
        for c in cracks:
            # every crack sits at an exact ball position on the ribbon, not a round year
            self.assertIn("ball_pos", c)
            self.assertTrue(0 <= c["ball_pos"] < total, c)
            self.assertTrue(0.0 <= c["ribbon_frac"] <= 1.0, c)
            self.assertTrue(0.0 <= c["season_frac"] <= 1.0, c)
            self.assertIn("year", c)
            self.assertIn("metric", c)
        # the digest's verified crack ball-fractions (season_frac) land on the cracks
        by_year = {}
        for c in cracks:
            by_year.setdefault(c["year"], c["season_frac"])
        self.assertAlmostEqual(by_year[2014], 0.320, places=2)
        self.assertAlmostEqual(by_year[2022], 0.703, places=2)
        self.assertAlmostEqual(by_year[2023], 0.764, places=2)
        self.assertAlmostEqual(by_year[2024], 0.824, places=2)

    def test_seismograph_record_and_series(self):
        rec = self.seis["record"]
        self.assertEqual(rec["matches"], 1243)
        self.assertEqual(rec["legal_deliveries"], 295557)
        self.assertEqual(self.seis["seasons"][0], 2008)
        self.assertEqual(self.seis["seasons"][-1], 2026)
        self.assertEqual(len(self.seis["seasons"]), 19)
        # the six-rate ladder genuinely climbs and steps at the mid-2010s
        six = self.seis["series"]["six_rate"]
        self.assertEqual(len(six), 19)
        self.assertAlmostEqual(six[0], 0.047722, places=5)
        self.assertAlmostEqual(six[-1], 0.085514, places=5)
        self.assertGreater(six[-1], six[0])


# ===========================================================================
# (2) The bridge-player verdict — the mystery answer: +8.87 jump, 56 batters,
#     about two-thirds turnover (NOT three-quarters)
# ===========================================================================


class BridgePlayerTest(unittest.TestCase):
    def setUp(self):
        self.br = DOC["bridge"]
        self.ss = self.br["shift_share"]

    def test_league_jump_and_bridge_cohort(self):
        self.assertAlmostEqual(self.br["league_sr_2023"], 141.72, places=2)
        self.assertAlmostEqual(self.br["league_sr_2024"], 150.59, places=2)
        self.assertAlmostEqual(self.br["jump"], 8.87, places=2)
        # the jump is the difference of the two league strike rates
        self.assertAlmostEqual(self.br["jump"],
                               round(self.br["league_sr_2024"] - self.br["league_sr_2023"], 2),
                               places=2)
        self.assertEqual(self.br["n_bridge"], 56)     # >=60 balls in BOTH seasons
        self.assertEqual(self.br["bridge_min_balls"], 60)

    def test_shift_share_within_third_turnover_two_thirds(self):
        within = self.ss["within"]
        turnover = self.ss["turnover"]
        # within about +2.9, turnover about +5.9
        self.assertAlmostEqual(within, 2.93, places=2)
        self.assertAlmostEqual(turnover, 5.94, places=2)
        # the two components reconstruct the +8.87 jump
        self.assertAlmostEqual(within + turnover, self.br["jump"], places=2)
        self.assertAlmostEqual(self.ss["total"], self.br["jump"], places=2)
        # the turnover component is itself entrants + leavers + usage
        comp = self.ss["components"]
        self.assertAlmostEqual(comp["entrants"] + comp["leavers"] + comp["usage"],
                               turnover, places=2)

    def test_turnover_is_two_thirds_not_three_quarters(self):
        turnover_frac = self.ss["turnover"] / self.ss["total"]
        # the honest delta: about two-thirds (0.67), NOT the teaser's three-quarters
        self.assertAlmostEqual(turnover_frac, 0.67, places=2)
        self.assertTrue(0.63 <= turnover_frac <= 0.70, turnover_frac)
        self.assertNotAlmostEqual(turnover_frac, 0.75, places=2)
        self.assertEqual(self.ss["turnover_pct"], 67)
        self.assertEqual(self.ss["within_pct"], 33)
        self.assertEqual(self.ss["turnover_pct"] + self.ss["within_pct"], 100)
        # the shipped copy owns the range honestly
        self.assertEqual(self.br["turnover_range"], "two-thirds to three-quarters")

    def test_verdict_closes_the_case_without_asserting_causation(self):
        v = self.br["verdict"]
        panels = v["panels"]
        self.assertEqual(len(panels), 3)          # three suspects, three co-equal panels
        self.assertEqual({p["chapter"] for p in panels}, {1, 7, 10})
        types = {p["type"] for p in panels}
        self.assertEqual(types, {"enabling condition", "measured share", "long-run trend"})
        # only the middle panel (the measured turnover share) carries a number
        numbered = [p for p in panels if "number" in p]
        self.assertEqual(len(numbered), 1)
        self.assertEqual(numbered[0]["type"], "measured share")
        self.assertEqual(numbered[0]["number"], "about two-thirds")
        # the verdict weighs evidence, it never asserts a cause: no banned causal verb
        blob = " ".join([v["headline"], v["note"]]
                        + [p["text"] for p in panels]).lower()
        self.assertNotIn("inevitable", blob)
        self.assertNotIn("made it inevitable", blob)
        self.assertNotIn("caused", blob)
        self.assertNotIn("drove", blob)
        self.assertNotIn("because of", blob)
        # the note explicitly DISCLAIMS causation (the only 'made' is anti-causal)
        self.assertIn("not one that made it happen", v["note"].lower())


# ===========================================================================
# (3) The player teleporter — Sehwag 184.55, naive ghost overshoots the honest
#     re-quote, the honest band < the gap (ghost outside the band), no z-score
# ===========================================================================


class TeleporterTest(unittest.TestCase):
    def setUp(self):
        self.tp = DOC["teleporter"]
        self.ma = self.tp["machine_a"]
        self.mb = self.tp["machine_b"]
        self.default = self.ma["default"]
        self.trans = {t["year"]: t for t in self.default["translations"]}

    def test_sehwag_2008_strike_rate(self):
        d = self.default
        self.assertEqual(d["name"], "V Sehwag")
        self.assertEqual(d["season"], 2008)
        self.assertEqual(d["balls"], 220)
        self.assertEqual(d["runs"], 406)
        self.assertAlmostEqual(d["sr"], 184.55, places=2)
        self.assertAlmostEqual(d["league_sr_season"], 128.98, places=2)
        self.assertEqual(self.ma["anchor_sr"], 185)   # the axis anchor is his real 185

    def test_naive_overshoots_percentile_by_the_gap(self):
        # naive (league-ratio ghost): about 216 to 2024, about 224 to 2026
        self.assertTrue(214 <= self.trans[2024]["naive"] <= 218, self.trans[2024]["naive"])
        self.assertTrue(222 <= self.trans[2026]["naive"] <= 225, self.trans[2026]["naive"])
        # percentile (honest re-quote): about 200 to 2024, about 214 to 2026
        self.assertTrue(198 <= self.trans[2024]["honest"] <= 202, self.trans[2024]["honest"])
        self.assertTrue(212 <= self.trans[2026]["honest"] <= 215, self.trans[2026]["honest"])
        # the naive ghost always overshoots the honest re-quote (you cannot scale an
        # outlier up), so the gap is positive on the exhibited player-seasons
        for yr in (2024, 2026):
            t = self.trans[yr]
            self.assertGreater(t["naive"], t["honest"])
            self.assertAlmostEqual(t["gap"], round(t["naive"] - t["honest"], 2), places=1)

    def test_naive_ceiling_is_about_224_not_228(self):
        # the honest delta: the corpus league strike rates never rise high enough for
        # 228, so the modern naive ceiling ships as about 224
        self.assertEqual(self.default["naive_ceiling"], 224)
        self.assertNotEqual(self.default["naive_ceiling"], 228)
        self.assertLess(self.trans[2026]["naive"], 228)

    def test_honest_band_is_narrower_than_the_gap_ghost_sits_outside(self):
        # RELEASE-BLOCKING integrity check: the honest re-quote's uncertainty band must
        # NOT reach the naive ghost, i.e. band half-width < the naive-vs-percentile gap,
        # for EVERY teleported player-season, or "overshoot" would be perceptually false
        for yr, t in self.trans.items():
            self.assertTrue(t["band_lt_gap"], f"{yr}: band flag false")
            self.assertLess(t["band_halfwidth"], t["gap"],
                            f"{yr}: band {t['band_halfwidth']} !< gap {t['gap']}")
            # the ghost sits clear ABOVE the top of the honest band
            self.assertLess(t["band_hi"], t["naive"], f"{yr}: ghost inside band")
            self.assertAlmostEqual(t["band_hi"], round(t["honest"] + t["band_halfwidth"], 1),
                                   places=1)
        # the emitted integrity block agrees, checked on 2026 (the shipped exhibit year)
        integ = self.ma["integrity"]
        self.assertTrue(integ["band_lt_gap"])
        self.assertEqual(integ["check_year"], 2026)
        self.assertLess(integ["band_halfwidth"], integ["gap"])
        self.assertAlmostEqual(integ["band_halfwidth"], 5.46, places=2)
        self.assertAlmostEqual(integ["gap"], 10.08, places=2)

    def test_gayle_edges_fraser_mcgurk_on_srplus_never_a_z(self):
        players = {p["name"]: p for p in self.mb["players"]}
        gayle = players["CH Gayle"]
        fm = players["J Fraser-McGurk"]
        self.assertEqual(gayle["season"], 2011)
        self.assertEqual(fm["season"], 2024)
        # raw strike rate: Fraser-McGurk is far higher
        self.assertAlmostEqual(gayle["sr"], 183.13, places=2)
        self.assertAlmostEqual(fm["sr"], 234.04, places=2)
        self.assertGreater(fm["sr"], gayle["sr"])
        self.assertAlmostEqual(self.mb["raw_sr_gap"], 50.9, places=1)
        self.assertAlmostEqual(self.mb["raw_sr_gap"], round(fm["sr"] - gayle["sr"], 1),
                               places=1)
        # measured against his own era (SR+ / percent above par), Gayle EDGES him
        self.assertAlmostEqual(gayle["srplus"], 156.71, places=2)
        self.assertAlmostEqual(fm["srplus"], 135.43, places=2)
        self.assertGreater(gayle["srplus"], fm["srplus"])
        self.assertAlmostEqual(gayle["pct_above_par"], 56.7, places=1)
        self.assertAlmostEqual(fm["pct_above_par"], 35.4, places=1)
        self.assertGreater(gayle["pct_above_par"], fm["pct_above_par"])
        # the era-honest currency is a percent-above-par gap, explicitly not a z-score
        self.assertEqual(self.mb["unit"], "percent above the going rate of his own year")
        for p in self.mb["players"]:
            self.assertNotIn("z", {k.lower() for k in p.keys()})
            self.assertNotIn("zscore", {k.lower() for k in p.keys()})


# ===========================================================================
# (4) The convergence clock — men cross ten an over about 2028-29 (NOT 2027),
#     the band runs to 2031, and the WPL slopes are present
# ===========================================================================


class ConvergenceTest(unittest.TestCase):
    def setUp(self):
        self.cv = DOC["convergence"]
        self.cross = self.cv["mens"]["crosses_ten"]

    def test_men_cross_ten_about_2028_2029_not_2027(self):
        # the honest read: the central crossing is 2028-29, NOT the optimistic 2027
        self.assertGreaterEqual(self.cross["central"], 2027)
        self.assertAlmostEqual(self.cross["central"], 2028.8, places=1)
        self.assertGreater(self.cross["central"], 2027.5)
        # the band is owned wide and its upper edge reaches into the 2030s
        self.assertGreaterEqual(self.cross["band_hi"], 2030)
        self.assertAlmostEqual(self.cross["band_hi"], 2031.3, places=1)
        self.assertEqual(self.cross["band_years"], [2027, 2031])
        self.assertLess(self.cross["band_lo"], self.cross["central"])
        self.assertLess(self.cross["central"], self.cross["band_hi"])
        self.assertEqual(self.cv["mens"]["target"], 10.0)
        # today is already 9.88, one strong season short of ten
        self.assertAlmostEqual(self.cv["mens"]["today"]["rpo"], 9.88, places=2)
        self.assertEqual(self.cv["mens"]["today"]["season"], 2026)

    def test_wpl_slopes_present_run_rate_closes_first(self):
        wpl = self.cv["wpl"]
        rr = wpl["run_rate"]
        six = wpl["six_rate"]
        # both slopes are emitted (rising run rate, near-flat six rate)
        self.assertIn("slope", rr)
        self.assertIn("slope", six)
        self.assertAlmostEqual(rr["slope"], 0.19, places=2)
        self.assertAlmostEqual(six["slope"], 0.01, places=2)
        self.assertGreater(rr["slope"], six["slope"])   # run rate closes first
        # the run rate reaches a FIXED present-day men's level (not a moving target)
        self.assertAlmostEqual(rr["mens_2026_level"], 9.88, places=2)
        self.assertGreaterEqual(rr["reaches_mens_2026_level"], 2030)
        # the six-hitting is honestly off the clock on four seasons
        self.assertTrue(six["off_the_clock"])
        self.assertGreaterEqual(six["reaches_mens_2026_level"], 2050)
        # four WPL seasons of data
        self.assertEqual(rr["seasons"], [2023, 2024, 2025, 2026])
        self.assertEqual(len(rr["rpo"]), 4)


# ===========================================================================
# (5) The payoff — 16 variants (10 IPL + 5 WPL + 1 neutral), non-degenerate,
#     every WPL bespoke and never "behind"
# ===========================================================================


class PayoffTest(unittest.TestCase):
    def setUp(self):
        self.pay = DOC["payoff"]
        self.variants = self.pay["variants"]

    def test_exactly_sixteen_10_5_1(self):
        self.assertEqual(len(self.variants), 16)
        by = Counter(v["league"] for v in self.variants)
        self.assertEqual(by["ipl"], 10)
        self.assertEqual(by["wpl"], 5)
        self.assertEqual(by["neutral"], 1)

    def test_every_variant_non_degenerate(self):
        for v in self.variants:
            self.assertFalse(v["empty_state"], v.get("short"))
            self.assertTrue(v["headline"].strip(), v.get("short"))
            for row in ("row1", "row2", "row3"):
                self.assertTrue(v[row].strip(), f"{v.get('short')} {row}")

    def test_ipl_cards_carry_a_riser_and_a_teleported_legend(self):
        ipl = [v for v in self.variants if v["league"] == "ipl"]
        self.assertEqual(len(ipl), 10)
        for v in ipl:
            self.assertTrue(v["riser"]["name"].strip(), v["short"])
            self.assertGreater(v["riser"]["rise"], 0, v["short"])
            self.assertEqual(v["riser"]["season_from"], 2023)
            self.assertEqual(v["riser"]["season_to"], 2024)
            leg = v["legend"]
            self.assertTrue(leg["name"].strip(), v["short"])
            self.assertGreater(leg["sr"], 0, v["short"])
            # the legend is re-quoted the HONEST way to 2026 (never the naive ghost)
            self.assertIn("honest_2026", leg)
            self.assertGreaterEqual(len(leg["translations"]), 1)
            for t in leg["translations"]:
                self.assertIn("band_halfwidth", t)
                self.assertIn("gap", t)
            # the climb is stated as a position against the league, never a ranking
            self.assertIn(v["climb"]["position"], ("above", "short of", "level with"))

    def test_at_least_one_bespoke_wpl_card_never_behind(self):
        wpl = [v for v in self.variants if v["league"] == "wpl"]
        self.assertEqual(len(wpl), 5)
        bespoke = [v for v in wpl if v.get("bespoke")]
        self.assertGreaterEqual(len(bespoke), 1)
        self.assertEqual(len(bespoke), 5)             # all five are bespoke
        for v in wpl:
            self.assertTrue(v.get("forming_fast"))    # the young-league beat, never a deficit
            self.assertGreater(v["riser"]["rise"], 0, v["short"])
            self.assertNotIn("behind", v["headline"].lower())
            for row in ("row1", "row2", "row3"):
                self.assertNotIn("behind", v[row].lower())
            self.assertIn("young league whose future you can already clock",
                          v["headline"].lower())

    def test_neutral_card_is_the_finale_summary(self):
        neu = next(v for v in self.variants if v["league"] == "neutral")
        self.assertEqual(neu["headline"], "The Era Machine.")
        self.assertIsNone(neu["team_id"])
        # it carries the finale's three verified numbers, drawn straight
        self.assertIn("two-thirds", neu["row2"].lower())
        self.assertAlmostEqual(neu["sehwag_honest_2026"], 213.6, places=1)
        # the same honest 2026 re-quote the teleporter emits for Sehwag's 2008 (the
        # honest re-quote, never the naive ghost)
        t2026 = next(t for t in DOC["teleporter"]["machine_a"]["default"]["translations"]
                     if t["year"] == 2026)
        self.assertEqual(neu["sehwag_honest_2026"], t2026["honest"])
        # the men crossing ten is quoted as 2028 or 2029, not the optimistic 2027
        self.assertIn("2028", neu["row3"])


# ===========================================================================
# (6) The field contract — buffer-free, 14 attributes, the ribbon is a pure
#     function of position.x, the teleporter rides the spare aRunOut bit
# ===========================================================================


class FieldContractTest(unittest.TestCase):
    def setUp(self):
        self.cm = DOC["controlling_morph"]
        self.rb = DOC["ribbon"]

    def test_ribbon_is_buffer_free_layout_12(self):
        self.assertEqual(self.cm["name"], "ribbon")
        self.assertEqual(self.cm["layout_code"], 12)
        self.assertIsNone(self.cm["new_buffer"])       # no new per-point buffer at all
        self.assertEqual(self.cm["teleport_bit"], 4)   # spare bit2 of aRunOut (1<<2)
        # the note commits to the 14-attribute / pure-position.x contract
        note = self.cm["note"].lower()
        self.assertIn("14", note)
        self.assertIn("position.x", note)
        self.assertIn("no 15th", note)
        self.assertIn("byte-identical", note)

    def test_ribbon_holds_every_ball_in_time_order(self):
        self.assertEqual(self.rb["total_points"], 316199)
        self.assertEqual(self.rb["n_matches_ipl"], 1243)
        self.assertEqual(self.rb["legal_deliveries_ipl"], 295557)
        # the time axis runs 2008 to 2026, ticks monotonically increasing in ball_pos
        ticks = self.rb["time_axis_ticks"]
        self.assertEqual(ticks[0]["season"], 2008)
        self.assertEqual(ticks[-1]["season"], 2026)
        positions = [t["ball_pos"] for t in ticks]
        self.assertEqual(positions, sorted(positions))
        self.assertEqual(positions[0], 0)
        fracs = [t["ribbon_frac"] for t in ticks]
        self.assertEqual(fracs, sorted(fracs))
        for f in fracs:
            self.assertTrue(0.0 <= f <= 1.0)


# ===========================================================================
# (7) The micro-era footnote — a strict 2021 break is partly venue-leg composition
# ===========================================================================


class MicroEraTest(unittest.TestCase):
    def test_2021_break_is_partly_the_venue_leg_split(self):
        me = DOC["micro_era_2021"]
        self.assertEqual(me["year"], 2021)
        # the India leg scored faster than the UAE bio-bubble leg
        self.assertAlmostEqual(me["india"]["rr"], 8.41, places=2)
        self.assertAlmostEqual(me["uae"]["rr"], 7.711, places=3)
        self.assertGreater(me["india"]["rr"], me["uae"]["rr"])
        self.assertEqual(me["india"]["runs"], 9499)
        self.assertEqual(me["india"]["legal_balls"], 6777)
        self.assertEqual(me["uae"]["runs"], 9123)
        self.assertEqual(me["uae"]["legal_balls"], 7099)


# ===========================================================================
# (8) Voice / glossary — zero em dashes anywhere; no z-score and no "behind" in
#     the on-screen copy; no z-score field name anywhere in the structure
# ===========================================================================


class VoiceGlossaryTest(unittest.TestCase):
    def test_zero_em_dashes_anywhere_in_ch10(self):
        offenders = [s for s in _iter_strings(DOC) if "—" in s]
        self.assertEqual(offenders, [], f"em dash in ch10 copy: {offenders[:3]}")

    def test_no_z_score_in_on_screen_copy(self):
        # "how far above his own era" ships as SR+/percent-above-par, NEVER a z-score;
        # the on-screen copy (everything but the footnotes) carries no z token at all
        zpat = re.compile(r"\bz\b|z-score|zscore|z score|z-value", re.IGNORECASE)
        offenders = [s for s in _iter_strings(_onscreen(DOC)) if zpat.search(s)]
        self.assertEqual(offenders, [], f"z-score on screen: {offenders[:3]}")

    def test_no_z_score_field_anywhere_in_the_structure(self):
        bad = {"z", "zscore", "z_score", "zval", "z_value", "zscores"}
        offenders = [k for k in _iter_keys(DOC) if k.lower() in bad]
        self.assertEqual(offenders, [], f"z-score field name: {offenders[:3]}")

    def test_never_behind_in_on_screen_copy(self):
        # the WPL is never "behind" on screen; that framing statement lives only in the
        # one-click-deep honesty footnote
        offenders = [s for s in _iter_strings(_onscreen(DOC)) if "behind" in s.lower()]
        self.assertEqual(offenders, [], f"'behind' on screen: {offenders[:3]}")

    def test_footnotes_carry_the_one_click_deep_honesty_notes(self):
        # sanity: the z-honesty note and the never-behind framing DO live in footnotes
        fn = DOC["footnotes"]
        self.assertIn("z-score", fn["ch10-teleporter"]["text"].lower())
        self.assertIn("behind", fn["ch10-convergence"]["text"].lower())
        for key in ("ch10-seismo", "ch10-bridge", "ch10-teleporter",
                    "ch10-convergence", "ch10-microera", "ch10-payoff"):
            self.assertIn(key, fn)
            self.assertTrue(fn[key]["text"].strip())


# ===========================================================================
# (9) Chapter framing — the finale flags and the mystery handoff in from Ch 9
# ===========================================================================


class ChapterFramingTest(unittest.TestCase):
    def test_finale_flags_and_title(self):
        self.assertEqual(DOC["chapter"], 10)
        self.assertEqual(DOC["title"], "The Era Machine")
        self.assertTrue(DOC["finale"])               # there is no Chapter 11
        self.assertEqual(DOC["register"], "the synthesis, case closed honestly")
        # the reverse leg exhales the ribbon back to the cold-open free field
        self.assertIn("free", DOC["controlling_morph"]["reverse"])

    def test_mystery_handoff_in_from_chapter_9(self):
        handoff = DOC["mystery_handoff_in"]
        self.assertIn("2023", handoff)
        self.assertIn("new era", handoff.lower())


# ===========================================================================
# Determinism — a fresh build equals itself and the on-disk bytes (buffer-free)
# ===========================================================================


class DeterminismTest(unittest.TestCase):
    def test_fresh_recompute_is_byte_identical(self):
        b2 = flatten.compact_json(ch10.build_doc(), sort_keys=True)
        b3 = flatten.compact_json(ch10.build_doc(), sort_keys=True)
        self.assertEqual(b2, b3, "two fresh ch10 builds diverged")
        self.assertEqual(b2, DISK_BYTES, "on-disk ch10.json != fresh recompute")


if __name__ == "__main__":
    unittest.main()
