"""R2b Chapter 3 "The Counterrevolution" snapshot tests.

scenes/ch3.json and the bowlerplane.u8 per-point buffer are checked against a
fully independent recount straight from the raw corpus (its own season-blocked
pass, its own economy/strike-rate/dismissal classifiers), and the catalog's
verified teasers are asserted as reconciliation anchors:

  * economy under 7.0: 49 of 169 bowler-seasons (29.0%) in IPL 2008-10 -> 4 of
    267 (1.5%) in 2023-26 (the frontier's retreat);
  * league dot rate 37.6% -> 33.0%, WPL 38.5% (~= IPL 2009);
  * Dismissal DNA (bowler-credited denom, caught excl c&b): bowled+lbw
    27.4% -> 21.3%, caught 65.2% -> 74.0%, stumped 4.2% -> 1.9%, WPL stumped 6.8%;
  * death-over wides per 100 legal balls doubled 3.13 -> 6.45, WPL just 2.69;
  * middle-overs crack ratio above 1 in the WPL, below 1 in the modern IPL;
  * the refuted econ~SR correlation +0.12 -> +0.03, WPL +0.34.

Buffer contract: bowlerplane.u8 is 2 bytes/point in field point order, byte 0 =
bowler-season economy, byte 1 = strike rate; length == 2 x n_points; 255 = the
"no strike rate" sentinel for 0-wicket bowler-seasons.

Engine #1 gate: Ch 3's batter marginal reconciles byte-for-byte with
engines/phasepar.json (True Economy's par is engine #1's phase-par flipped to
the bowling side).

Determinism: the on-disk artifacts equal a fresh recompute byte-for-byte.
"""

from __future__ import annotations

import json
import sys
import unittest
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bowlerplane
import canon
import flatten
import scenes

CH3 = None
BUF = None
BUILD = None

BWK = bowlerplane.BOWLER_WICKET_KINDS
RETIRED = {"retired hurt", "retired out"}


def setUpModule():
    global CH3, BUF, BUILD
    out = canon.OUT_ROOT
    if not (out / "scenes" / "ch3.json").exists():
        scenes.main()
    if not (out / "bowlerplane.u8").exists():
        bowlerplane.main()
    CH3 = json.loads((out / "scenes" / "ch3.json").read_text())
    BUF = (out / "bowlerplane.u8").read_bytes()
    BUILD = bowlerplane.build()


def phase_idx(over: int) -> int:
    return 0 if over <= 5 else (1 if over <= 14 else 2)


def band(league: str, season: int) -> str:
    if league == "wpl":
        return "wpl 2023-2026"
    for lo, hi, lab in ((2008, 2010, "2008-2010"), (2011, 2015, "2011-2015"),
                        (2016, 2019, "2016-2019"), (2020, 2022, "2020-2022"),
                        (2023, 2026, "2023-2026")):
        if lo <= season <= hi:
            return "ipl " + lab
    raise KeyError(season)


def recount():
    """One independent season-blocked pass over the raw corpus."""
    bs = defaultdict(lambda: {"legal": 0, "charged": 0, "wkts": 0})
    season_dot = defaultdict(lambda: [0, 0])
    dna = defaultdict(lambda: defaultdict(int))  # (league, season) -> {kind: n}
    death = defaultdict(lambda: [0, 0])          # (league, season) -> [wides, death legal]
    crack = defaultdict(lambda: [0, 0, 0, 0])    # bandkey -> [k0 b, k0 w, k3 b, k3 w]

    for _d, _m, league, path in flatten.sorted_match_files():
        with open(path) as fh:
            match = json.load(fh)
        season = canon.canon_season(match["info"])
        bk = band(league, season)
        for inn in match.get("innings", []):
            if inn.get("super_over"):
                continue
            run_dots = 0
            for over in inn["overs"]:
                ph = phase_idx(over["over"])
                for dl in over["deliveries"]:
                    ex = dl.get("extras", {})
                    wide = "wides" in ex
                    noball = "noballs" in ex
                    legal = not (wide or noball)
                    total = dl["runs"]["total"]
                    is_wkt = bool(dl.get("wickets"))
                    key = (league, season, dl["bowler"])
                    bs[key]["charged"] += (dl["runs"]["batter"]
                                           + ex.get("wides", 0) + ex.get("noballs", 0))
                    if legal:
                        bs[key]["legal"] += 1
                        season_dot[(league, season)][1] += 1
                        if total == 0:
                            season_dot[(league, season)][0] += 1
                        if ph == 2:
                            death[(league, season)][1] += 1
                        if ph == 1:
                            c = crack[bk]
                            if run_dots == 0:
                                c[0] += 1
                                c[1] += 1 if is_wkt else 0
                            elif run_dots >= 3:
                                c[2] += 1
                                c[3] += 1 if is_wkt else 0
                        run_dots = run_dots + 1 if total == 0 else 0
                    if ph == 2 and wide:
                        death[(league, season)][0] += 1
                    for w in dl.get("wickets", []):
                        if w["kind"] in RETIRED:
                            continue
                        dna[(league, season)][w["kind"]] += 1
                        if w["kind"] in BWK:
                            bs[key]["wkts"] += 1
    return bs, season_dot, dna, death, crack


class TestFrontier(unittest.TestCase):
    def test_under7_shares_reproduce_catalog(self):
        u = CH3["frontier"]["under7"]["era_bands"]
        self.assertEqual((u["ipl 2008-2010"]["under7"], u["ipl 2008-2010"]["qualifiers"]),
                         (49, 169))
        self.assertEqual(u["ipl 2008-2010"]["pct"], 29.0)
        self.assertEqual((u["ipl 2023-2026"]["under7"], u["ipl 2023-2026"]["qualifiers"]),
                         (4, 267))
        self.assertEqual(u["ipl 2023-2026"]["pct"], 1.5)

    def test_under7_matches_independent_recount(self):
        bs, *_ = recount()
        era = defaultdict(lambda: [0, 0])
        for (lg, ss, _b), r in bs.items():
            if r["legal"] < bowlerplane.MIN_LEGAL_BALLS:
                continue
            econ = 6.0 * r["charged"] / r["legal"]
            era[band(lg, ss)][1] += 1
            if econ < 7.0:
                era[band(lg, ss)][0] += 1
        u = CH3["frontier"]["under7"]["era_bands"]
        for k, (under7, total) in era.items():
            self.assertEqual((u[k]["under7"], u[k]["qualifiers"]), (under7, total), k)

    def test_correlation_refuted_positive(self):
        c = CH3["frontier"]["correlation"]["era_bands"]
        self.assertEqual(c["ipl 2008-2010"]["r"], 0.12)
        self.assertEqual(c["ipl 2023-2026"]["r"], 0.03)
        self.assertEqual(c["wpl 2023-2026"]["r"], 0.34)

    def test_hull_is_pareto_efficient(self):
        # every hull point: no other hull point dominates it (both lower)
        for s in CH3["frontier"]["hull"]["seasons"]:
            pts = [(p["economy"], p["strike_rate"]) for p in s["points"]]
            self.assertTrue(pts, s)
            # A lower-left Pareto staircase sorted by strike rate: economy
            # strictly decreases (raw strike rates are distinct — two points at
            # the same strike rate can't both be efficient — but DISPLAY strike
            # rate can tie after rounding to 1 dp, so allow s0 <= s1).
            for (e0, s0), (e1, s1) in zip(pts, pts[1:]):
                self.assertLessEqual(s0, s1, s)   # sorted by strike rate (weak: rounding ties)
                self.assertLess(e1, e0, s)        # economy strictly descends

    def test_ghost_trail_ashwin_every_frontier(self):
        t = CH3["frontier"]["ghost_trail"]
        self.assertEqual(t["bowler"], "R Ashwin")
        seasons = [p["season"] for p in t["points"]]
        self.assertGreaterEqual(len(seasons), 12)
        self.assertEqual(seasons, sorted(seasons))
        # the tide rises even for a great: economy generally climbs across the trail
        self.assertLess(t["points"][0]["economy"], t["points"][-1]["economy"])


class TestDotPlus(unittest.TestCase):
    def test_dot_rate_reproduces_catalog(self):
        h = CH3["dot_plus"]["era_headline"]
        self.assertEqual(h["ipl_2008_2010"], 37.6)
        self.assertEqual(h["ipl_2023_2026"], 33.0)
        self.assertEqual(h["wpl_2023_2026"], 38.5)

    def test_dot_rate_matches_recount(self):
        _bs, season_dot, *_ = recount()

        def era(lg, lo, hi):
            d = sum(season_dot[(lg, s)][0] for s in range(lo, hi + 1))
            l = sum(season_dot[(lg, s)][1] for s in range(lo, hi + 1))
            return round(100.0 * d / l, 1)

        self.assertEqual(CH3["dot_plus"]["era_headline"]["ipl_2008_2010"], era("ipl", 2008, 2010))
        self.assertEqual(CH3["dot_plus"]["era_headline"]["ipl_2023_2026"], era("ipl", 2023, 2026))

    def test_dot_plus_leaderboard_well_formed(self):
        lb = CH3["dot_plus"]["leaderboard"]
        self.assertEqual(len(lb), 12)
        # descending, elite dot manufacture (Dot+ 130+ leads)
        vals = [r["dot_plus"] for r in lb]
        self.assertEqual(vals, sorted(vals, reverse=True))
        self.assertGreater(vals[0], 130)
        for r in lb:
            self.assertGreaterEqual(r["balls"], bowlerplane.DOTPLUS_MIN_BALLS)


class TestDismissalDNA(unittest.TestCase):
    def test_dna_reproduces_catalog(self):
        e = CH3["dismissal_dna"]["era_bands"]
        self.assertEqual((e["ipl 2008-2010"]["bowled_lbw_pct"],
                          e["ipl 2008-2010"]["caught_pct"],
                          e["ipl 2008-2010"]["stumped_pct"]), (27.4, 65.2, 4.2))
        self.assertEqual((e["ipl 2023-2026"]["bowled_lbw_pct"],
                          e["ipl 2023-2026"]["caught_pct"],
                          e["ipl 2023-2026"]["stumped_pct"]), (21.3, 74.0, 1.9))
        self.assertEqual(e["wpl 2023-2026"]["stumped_pct"], 6.8)

    def test_dna_matches_recount(self):
        _bs, _sd, dna, *_ = recount()

        def era_shares(lg, lo, hi):
            agg = defaultdict(int)
            for s in range(lo, hi + 1):
                for k, v in dna[(lg, s)].items():
                    agg[k] += v
            denom = sum(v for k, v in agg.items() if k != "run out")
            return (round(100.0 * (agg["bowled"] + agg["lbw"]) / denom, 1),
                    round(100.0 * agg["caught"] / denom, 1),
                    round(100.0 * agg["stumped"] / denom, 1))

        e = CH3["dismissal_dna"]["era_bands"]
        self.assertEqual((e["ipl 2008-2010"]["bowled_lbw_pct"],
                          e["ipl 2008-2010"]["caught_pct"],
                          e["ipl 2008-2010"]["stumped_pct"]), era_shares("ipl", 2008, 2010))


class TestDeathWideTax(unittest.TestCase):
    def test_doubling(self):
        h = CH3["death_wide_tax"]["era_headline"]
        self.assertEqual(h["ipl_2008_2010"], 3.13)
        self.assertEqual(h["ipl_2023_2026"], 6.45)
        self.assertEqual(h["wpl_2023_2026"], 2.69)
        self.assertGreaterEqual(h["doubling_factor"], 2.0)

    def test_matches_recount(self):
        _bs, _sd, _dna, death, _c = recount()

        def era(lg, lo, hi):
            w = sum(death[(lg, s)][0] for s in range(lo, hi + 1))
            l = sum(death[(lg, s)][1] for s in range(lo, hi + 1))
            return round(100.0 * w / l, 2)

        self.assertEqual(CH3["death_wide_tax"]["era_headline"]["ipl_2023_2026"], era("ipl", 2023, 2026))


class TestCrackRatio(unittest.TestCase):
    def test_wpl_above_one_ipl_below(self):
        e = CH3["crack_ratio"]["era_bands"]
        self.assertGreater(e["wpl 2023-2026"]["crack_ratio"], 1.0)
        self.assertLess(e["ipl 2023-2026"]["crack_ratio"], 1.0)

    def test_matches_recount(self):
        *_, crack = recount()
        e = CH3["crack_ratio"]["era_bands"]
        for bk in ("ipl 2008-2010", "ipl 2023-2026", "wpl 2023-2026"):
            c = crack[bk]
            expect = round((c[3] / c[2]) / (c[1] / c[0]), 2)
            self.assertEqual(e[bk]["crack_ratio"], expect, bk)


class TestDotGrid(unittest.TestCase):
    def test_two_finals_120_cells(self):
        inns = CH3["dot_grid"]["innings"]
        self.assertEqual(len(inns), 2)
        seasons = {i["season"] for i in inns}
        # one exemplar from the early era, one from the modern era (each a Final)
        self.assertEqual(len(seasons & {2008, 2009, 2010}), 1)
        self.assertEqual(len(seasons & {2023, 2024, 2025, 2026}), 1)
        for i in inns:
            self.assertEqual(i["league"], "ipl")
            self.assertEqual(i["stage"], "Final")
            self.assertEqual(len(i["outcomes"]), 120)
            self.assertEqual(len(i["wickets"]), 120)
            self.assertEqual(i["legal_balls"], 120)
            # dot% == count of outcome-0 cells / 120
            dots = i["outcomes"].count(0)
            self.assertEqual(i["dots"], dots)
            self.assertEqual(i["dot_pct"], round(100.0 * dots / 120, 1))
            self.assertTrue(all(0 <= o <= 5 for o in i["outcomes"]))
            self.assertTrue(all(w in (0, 1) for w in i["wickets"]))

    def test_exemplars_near_era_means(self):
        # the exemplar Finals must sit NEAR their era's pooled dot rate so the
        # visual dark-cell gap approximates the honest league shift (37.6 -> 33.0),
        # not a cherry-picked extreme (design-audit fix: the 2009 Final at 39.2%
        # overstated the gap by 63%)
        head = CH3["dot_plus"]["era_headline"]
        by_season = {i["season"]: i for i in CH3["dot_grid"]["innings"]}
        early = next(i for s, i in by_season.items() if s <= 2010)
        modern = next(i for s, i in by_season.items() if s >= 2023)
        self.assertLessEqual(abs(early["dot_pct"] - head["ipl_2008_2010"]), 2.5)
        self.assertLessEqual(abs(modern["dot_pct"] - head["ipl_2023_2026"]), 2.5)
        # erosion still reads in the exemplars, but at an honest magnitude (<= ~5.5pp)
        self.assertGreater(early["dot_pct"], modern["dot_pct"])
        self.assertLessEqual(early["dot_pct"] - modern["dot_pct"], 5.5)


class TestGravityDefiers(unittest.TestCase):
    def test_all_20_franchises(self):
        v = CH3["gravity_defiers"]["variants"]
        self.assertEqual(len(v), 20)
        self.assertEqual(sorted(x["franchise_id"] for x in v), list(range(20)))

    def test_wpl_small_sample_flagged(self):
        for x in CH3["gravity_defiers"]["variants"]:
            if x["league"] == "wpl":
                self.assertTrue(x["small_sample"])
            self.assertGreater(x["true_economy"], 0)      # a defier beats par
            self.assertGreaterEqual(x["balls"], bowlerplane.MIN_LEGAL_BALLS)
            # true_economy == par - actual (true_economy is rounded from full
            # precision; par_economy and economy are each independently rounded,
            # so allow the combined 0.02 rounding slack)
            self.assertLessEqual(abs(x["true_economy"] - (x["par_economy"] - x["economy"])), 0.02)

    def test_headline_defiers_present(self):
        by_fr = {(x["league"], x["franchise"]): x for x in CH3["gravity_defiers"]["variants"]}
        self.assertEqual(by_fr[("ipl", "Mumbai Indians")]["bowler"], "JJ Bumrah")
        self.assertEqual(by_fr[("ipl", "Sunrisers Hyderabad")]["bowler"], "Rashid Khan")


class TestFootnotes(unittest.TestCase):
    def test_true_economy_headline(self):
        le = CH3["footnotes"]["true_economy"]["league_charged_economy"]
        self.assertEqual(le["ipl_2008_2010"], 7.79)
        self.assertEqual(le["ipl_2023_2026"], 9.38)

    def test_fib_drift(self):
        f = CH3["footnotes"]["fib"]
        self.assertEqual(f["ipl_2008_2010"]["caught_pct"], 60.0)
        self.assertEqual(f["ipl_2023_2026"]["caught_pct"], 72.6)
        self.assertEqual(f["ipl_2008_2010"]["run_out_pct"], 12.1)
        self.assertEqual(f["ipl_2023_2026"]["run_out_pct"], 5.2)

    def test_phase_fingerprint_story(self):
        pf = CH3["footnotes"]["phase_fingerprint"]
        # emergence then a 2026 slump (definition-sensitive; recompute shipped)
        self.assertEqual(pf["end_2026_pct"], 0.0)
        self.assertGreater(pf["peak"]["specialist_death_share_pct"], pf["start_2008_pct"])


class TestBowlerplaneBuffer(unittest.TestCase):
    def test_length_two_bytes_per_point(self):
        meta = json.loads((canon.OUT_ROOT / "meta.json").read_text())
        n = meta["n_points"]
        self.assertEqual(n, 316199)
        self.assertEqual(len(BUF), 2 * n)

    def test_deterministic_encode(self):
        fresh = bowlerplane.encode(BUILD["bowler_seasons"], BUILD["ball_keys"])
        self.assertEqual(fresh, BUF)

    def test_sentinel_only_for_zero_wicket_seasons(self):
        # SR sentinel count must equal the number of balls in 0-wicket bowler-seasons
        no_sr = 0
        for key in BUILD["ball_keys"]:
            if BUILD["bowler_seasons"][key].wkts == 0:
                no_sr += 1
        got = sum(1 for i in range(1, len(BUF), 2) if BUF[i] == bowlerplane.SENTINEL)
        self.assertEqual(got, no_sr)
        # economy byte is always defined (no legal==0 bowler-season) -> never sentinel
        self.assertEqual(sum(1 for i in range(0, len(BUF), 2) if BUF[i] == bowlerplane.SENTINEL), 0)

    def test_coordinate_round_trips_for_a_known_bowler_season(self):
        # find the first ball of MI Bumrah 2024 in field order; its bytes must
        # decode to his 2024 economy & strike rate.
        key = ("ipl", 2024, "JJ Bumrah")
        idx = BUILD["ball_keys"].index(key)
        rec = BUILD["bowler_seasons"][key]
        self.assertEqual(BUF[2 * idx], bowlerplane.quantize_econ(bowlerplane.economy(rec)))
        self.assertEqual(BUF[2 * idx + 1], bowlerplane.quantize_sr(bowlerplane.strike_rate(rec)))
        # decode economy byte back to ~his economy
        e = bowlerplane.ECON_LO + BUF[2 * idx] / 254 * (bowlerplane.ECON_HI - bowlerplane.ECON_LO)
        self.assertAlmostEqual(e, bowlerplane.economy(rec), delta=0.06)

    def test_axis_bounds_in_ch3_json(self):
        b = CH3["bowlerplane_buffer"]
        self.assertEqual(b["bytes_per_point"], 2)
        self.assertEqual(b["economy"]["lo"], bowlerplane.ECON_LO)
        self.assertEqual(b["economy"]["hi"], bowlerplane.ECON_HI)
        self.assertEqual(b["strike_rate"]["sentinel"], bowlerplane.SENTINEL)


class TestEngineOneConsumption(unittest.TestCase):
    def test_batter_marginal_reconciles_with_phasepar(self):
        pp_path = canon.OUT_ROOT / "engines" / "phasepar.json"
        if not pp_path.exists():
            import par
            par.main()
        phasepar = json.loads(pp_path.read_text())
        # phasepar.json: seasons[].{pp,middle,death}.expected_runs_per_ball
        pp = {}
        for row in phasepar["seasons"]:
            for ph in ("pp", "middle", "death"):
                v = row[ph]["expected_runs_per_ball"]
                if v is not None:
                    pp[(row["league"], row["season"], ph)] = v
        bm = BUILD["batter_marginal"]
        checked = 0
        for (lg, ss, ph), (runs, balls) in bm.items():
            if balls == 0:
                continue
            self.assertAlmostEqual(round(runs / balls, 5), pp[(lg, ss, ph)], places=5,
                                   msg=f"{lg} {ss} {ph}")
            checked += 1
        self.assertGreater(checked, 60)


class TestDeterminism(unittest.TestCase):
    def test_ch3_on_disk_equals_fresh_build(self):
        fresh = scenes.ch3_doc(scenes.build_ch3())
        raw = flatten.compact_json(fresh, sort_keys=True)
        self.assertEqual(raw, (canon.OUT_ROOT / "scenes" / "ch3.json").read_bytes())


if __name__ == "__main__":
    unittest.main()
