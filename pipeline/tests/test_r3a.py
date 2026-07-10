"""R3a Chapter 4 "The Rising Tide" snapshot tests.

scenes/ch4.json and the innings_total.u8 per-point buffer are checked against a
fully independent recount straight from the raw corpus (its own season-blocked
pass, its own full-first-innings filter, its own powerplay tagging), and the
catalog's verified teasers are asserted as reconciliation anchors:

  * P(first innings >= 200): 7.7% (2008-10) -> ~42% (2023-26); 52% in 2026 —
    and the 2023 discontinuity (a cliff from the 2020-22 era);
  * Par (the total that wins exactly half the time): 165 (2008-10) -> 195
    (2023-26), logistic P(bat-first win) = 0.5;
  * the big-total defended record is the TRUE 2023-26 figure (33 posted, 29
    defended), not the stale "11/11" claim — some 230+ totals were chased down;
  * Powerplay run rate 7.60 -> 9.48 at essentially identical wicket cost
    (1.54 vs 1.52 wickets per 36 balls) — the extra runs came free;
  * between-venue variance share RISES (venues diverging), not falls;
  * the highest-first-innings record RCB 263 (2013) stood 3,991 days, then fell
    twice in 19 days in 2024 (277 then 287);
  * WPL avg first innings 157 -> 169 over four seasons; five 200s in 2026.

Buffer contract: innings_total.u8 is 1 byte/point in field point order, byte =
floor(innings_total / 2); length == n_points; every ball of an innings shares
the byte. Verified against the shipped columnar arrays (match_index, innings,
runs_total), which are an independent per-delivery source of truth.

Engine-light gate: Chapter 4 emits NO new engine file (no engines/ delta beyond
what R2/R3b already ship); it reuses engine #1 (par/phasepar).

Determinism: the on-disk artifacts equal a fresh recompute byte-for-byte.
"""

from __future__ import annotations

import json
import math
import sys
import unittest
from collections import defaultdict
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import canon
import flatten
import scenes

CH4 = None
BUF = None
RECOUNT = None

ERAS = (
    ("2008-2010", 2008, 2010),
    ("2011-2015", 2011, 2015),
    ("2016-2019", 2016, 2019),
    ("2020-2022", 2020, 2022),
    ("2023-2026", 2023, 2026),
)
RETIRED = {"retired hurt", "retired out"}


def era_of(season):
    for label, lo, hi in ERAS:
        if lo <= season <= hi:
            return label
    return None


def recount(data_root=canon.DATA_ROOT):
    """A second, independent corpus pass for Chapter 4's aggregates."""
    era_first = defaultdict(list)        # (league, era) -> [full first-innings totals]
    season_first = defaultdict(list)     # (league, season) -> [full first-innings totals]
    era_decided = defaultdict(list)      # (league, era) -> [(total, batfirst_win)]
    pp = defaultdict(lambda: [0, 0, 0])  # (league, era) -> [runs, legal, wickets]
    any200 = defaultdict(int)            # (league, season) -> either-innings >= 200
    records = {"ipl": [], "wpl": []}
    running = {"ipl": 0, "wpl": 0}

    for date0, _mid, league, path in flatten.sorted_match_files(data_root):
        with open(path) as fh:
            match = json.load(fh)
        info = match["info"]
        season = canon.canon_season(info)
        outcome = info.get("outcome", {})
        winner = outcome.get("winner")
        winner_c = canon.canon_team(winner) if winner else None
        result = outcome.get("result")
        decided = bool(winner) and result not in ("tie", "no result")
        teams = [canon.canon_team(t) for t in info["teams"]]
        venue = canon.canon_venue(info["venue"])

        innings_no = 0
        first_total = first_bat = None
        target_lt20 = False
        for innings in match.get("innings", []):
            if canon.is_super_over(innings):
                continue
            innings_no += 1
            if innings_no == 2:
                tgt = innings.get("target") or {}
                ov = tgt.get("overs")
                if ov is not None and float(ov) < 20:
                    target_lt20 = True
            bat = canon.canon_team(innings["team"])
            pp_overs = set()
            for p in innings.get("powerplays", []):
                if p.get("type") == "mandatory":
                    pp_overs.update(
                        range(int(math.floor(p["from"])), int(math.floor(p["to"])) + 1)
                    )
            runs_total = 0
            e = era_of(season)
            for over in innings["overs"]:
                ono = over["over"]
                in_pp = (ono in pp_overs) if pp_overs else (ono <= 5)
                for dl in over["deliveries"]:
                    ex = dl.get("extras", {})
                    legal = not ("wides" in ex or "noballs" in ex)
                    rt = dl["runs"]["total"]
                    runs_total += rt
                    nwk = sum(1 for w in dl.get("wickets", []) if w["kind"] not in RETIRED)
                    if in_pp and e:
                        pp[(league, e)][0] += rt
                        if legal:
                            pp[(league, e)][1] += 1
                        pp[(league, e)][2] += nwk
            if runs_total >= 200:
                any200[(league, season)] += 1
            if innings_no == 1:
                first_total = runs_total
                first_bat = bat

        full = (
            not canon.is_dl(info)
            and result != "no result"
            and not target_lt20
            and first_total is not None
        )
        if full:
            e = era_of(season)
            season_first[(league, season)].append(first_total)
            if e:
                era_first[(league, e)].append(first_total)
                if decided:
                    era_decided[(league, e)].append(
                        (first_total, 1 if winner_c == first_bat else 0)
                    )
            if first_total > running[league]:
                running[league] = first_total
                records[league].append(
                    {"date": date0, "total": first_total, "team": first_bat, "venue": venue}
                )
    return {
        "era_first": era_first,
        "season_first": season_first,
        "era_decided": era_decided,
        "pp": pp,
        "any200": any200,
        "records": records,
    }


def setUpModule():
    global CH4, BUF, RECOUNT
    out = canon.OUT_ROOT
    if not (out / "scenes" / "ch4.json").exists():
        scenes.main()
    if not (out / "innings_total.u8").exists():
        flatten.main()
    CH4 = json.loads((out / "scenes" / "ch4.json").read_text())
    BUF = (out / "innings_total.u8").read_bytes()
    RECOUNT = recount()


class TestExceedance(unittest.TestCase):
    def test_p200_headline(self):
        ex = CH4["exceedance"]["by_era"]
        self.assertAlmostEqual(
            ex["ipl 2008-2010"]["exceedance_pct"]["200"], 7.7, delta=0.5
        )
        self.assertGreaterEqual(ex["ipl 2023-2026"]["exceedance_pct"]["200"], 40.0)
        self.assertLessEqual(ex["ipl 2023-2026"]["exceedance_pct"]["200"], 44.0)
        self.assertAlmostEqual(
            CH4["exceedance"]["by_season"]["ipl"]["2026"]["exceedance_pct"]["200"],
            52.0,
            delta=1.5,
        )

    def test_exceedance_counts_match_recount(self):
        # the scene's own exceedance counts equal the independent recount's
        for label, lo, hi in ERAS:
            totals = RECOUNT["era_first"][("ipl", label)]
            got = CH4["exceedance"]["by_era"][f"ipl {label}"]["exceedance_count"]["200"]
            self.assertEqual(got, sum(1 for x in totals if x >= 200))

    def test_2023_cliff(self):
        # the discontinuity: 2023 P(200) is far above the 2020-22 era
        cliff = CH4["exceedance"]["cliff"]
        self.assertGreater(cliff["after"]["p200"], 2.0 * cliff["era_before"]["p200"])


class TestParDrift(unittest.TestCase):
    def test_par_headline(self):
        by_era = CH4["par_drift"]["by_era"]
        self.assertGreaterEqual(by_era["ipl 2008-2010"]["par"], 162.0)
        self.assertLessEqual(by_era["ipl 2008-2010"]["par"], 168.0)
        self.assertGreaterEqual(by_era["ipl 2023-2026"]["par"], 192.0)
        self.assertLessEqual(by_era["ipl 2023-2026"]["par"], 198.0)

    def test_par_ordering(self):
        by_era = CH4["par_drift"]["by_era"]
        self.assertLess(by_era["ipl 2008-2010"]["par"], by_era["ipl 2023-2026"]["par"])
        # safe > par > dead within an era
        recent = by_era["ipl 2023-2026"]
        self.assertGreater(recent["safe"], recent["par"])
        self.assertGreater(recent["par"], recent["dead"])

    def test_par_win_calibration(self):
        # empirical: 2023-26 first innings at/above the fitted par win >= half
        par = CH4["par_drift"]["by_era"]["ipl 2023-2026"]["par"]
        rows = RECOUNT["era_decided"][("ipl", "2023-2026")]
        at_or_above = [bf for (t, bf) in rows if t >= par]
        self.assertGreaterEqual(sum(at_or_above) / len(at_or_above), 0.5)

    def test_230plus_defended_is_true_record_not_11_of_11(self):
        rec = CH4["par_drift"]["totals_230plus"]
        # independent recount of 230+ decided full first innings, 2023-26
        big = [
            (t, bf)
            for (t, bf) in RECOUNT["era_decided"][("ipl", "2023-2026")]
            if t >= 230
        ]
        self.assertEqual(rec["posted"], len(big))
        self.assertEqual(rec["defended"], sum(bf for _, bf in big))
        # the stale claim was "11/11"; the truth is more posted, some chased
        self.assertGreater(rec["posted"], 11)
        self.assertGreater(rec["chased_down"], 0)
        self.assertEqual(rec["posted"] - rec["defended"], len(rec["chased_list"]))


class TestPowerplay(unittest.TestCase):
    def test_run_rate_and_equal_wicket_cost(self):
        eq = CH4["powerplay"]["equal_wicket_cost"]
        self.assertAlmostEqual(eq["early_rr"], 7.60, delta=0.05)
        self.assertAlmostEqual(eq["late_rr"], 9.48, delta=0.05)
        # the punchline: the extra ~1.9 RPO came at essentially no extra wickets
        self.assertAlmostEqual(eq["early_wickets_per_36"], 1.54, delta=0.05)
        self.assertAlmostEqual(eq["late_wickets_per_36"], 1.52, delta=0.05)
        self.assertLess(
            abs(eq["late_wickets_per_36"] - eq["early_wickets_per_36"]), 0.1
        )

    def test_matches_recount(self):
        for e in ("ipl 2008-2010", "ipl 2023-2026"):
            label = e.split(" ", 1)[1]
            runs, legal, wk = RECOUNT["pp"][("ipl", label)]
            got = CH4["powerplay"]["by_era"][e]
            self.assertEqual(got["legal_balls"], legal)
            self.assertAlmostEqual(got["run_rate"], 6.0 * runs / legal, places=2)
            self.assertAlmostEqual(got["wickets_per_36"], 36.0 * wk / legal, places=2)


class TestBetweenVenueVariance(unittest.TestCase):
    def test_venues_diverge(self):
        v = CH4["venues"]["between_venue_variance"]
        early = v["ipl 2008-2010"]["between_venue_share_pct"]
        late = v["ipl 2023-2026"]["between_venue_share_pct"]
        self.assertIsNotNone(early)
        self.assertIsNotNone(late)
        # the contrarian finding: venue identity is GROWING, not homogenizing
        self.assertGreater(late, early)

    def test_chinnaswamy_above_chepauk(self):
        fp = CH4["venues"]["fingerprint_2023_2026"]
        self.assertGreater(fp["chinnaswamy"], fp["chepauk"])
        self.assertGreater(fp["chinnaswamy"] - fp["chepauk"], 15.0)


class TestRecordHalfLife(unittest.TestCase):
    def test_rcb_263_and_2024_collapse(self):
        prog = CH4["record_halflife"]["ipl_progression"]
        by_total = {e["total"]: e for e in prog}
        self.assertIn(263, by_total)
        self.assertEqual(by_total[263]["stood_days"], 3991)
        self.assertIn(277, by_total)
        self.assertEqual(by_total[277]["stood_days"], 19)
        self.assertIn(287, by_total)
        self.assertTrue(by_total[287]["standing"])

    def test_progression_matches_recount(self):
        got = [(e["total"], e["team"]) for e in CH4["record_halflife"]["ipl_progression"]]
        exp = [(e["total"], e["team"]) for e in RECOUNT["records"]["ipl"]]
        self.assertEqual(got, exp)

    def test_stationary_null_note_present(self):
        self.assertIn(
            "3,991", CH4["record_halflife"]["stationary_environment_null"]
        )


class TestWPLBeat(unittest.TestCase):
    def test_avg_first_innings_rise(self):
        avg = CH4["wpl_beat"]["avg_first_innings_by_season"]
        self.assertAlmostEqual(avg["2023"], 157.0, delta=2.0)
        self.assertAlmostEqual(avg["2026"], 169.0, delta=2.0)
        self.assertGreater(avg["2026"], avg["2023"])

    def test_five_200s_in_2026(self):
        self.assertEqual(CH4["wpl_beat"]["totals_200_by_season"]["2026"], 5)
        self.assertEqual(RECOUNT["any200"][("wpl", 2026)], 5)

    def test_sits_between_ipl_2008_and_2015(self):
        sb = CH4["wpl_beat"]["sits_between_ipl_seasons"]
        self.assertEqual(sb["seasons"], [2015, 2008])
        self.assertGreaterEqual(sb["wpl_p200"], sb["ipl_p200"]["2015"])
        self.assertLessEqual(sb["wpl_p200"], sb["ipl_p200"]["2008"])


class TestPayoff(unittest.TestCase):
    def test_sixteen_variants(self):
        variants = CH4["payoff"]["variants"]
        self.assertEqual(len(variants), 16)
        leagues = [v["league"] for v in variants]
        self.assertEqual(leagues.count("ipl"), 10)
        self.assertEqual(leagues.count("wpl"), 5)
        self.assertEqual(leagues.count("neutral"), 1)

    def test_wpl_variants_are_designed_rotating_home(self):
        wpl = [v for v in CH4["payoff"]["variants"] if v["league"] == "wpl"]
        self.assertEqual(len(wpl), 5)
        for v in wpl:
            self.assertTrue(v["empty_state"])
            self.assertTrue(v.get("rotating_home"))
            self.assertIsNone(v["home_ground"])

    def test_chepauk_holds_character_something_floods(self):
        ipl = {
            v["team"]: v for v in CH4["payoff"]["variants"] if v["league"] == "ipl"
        }
        self.assertEqual(
            ipl["Chennai Super Kings"]["fingerprint"], "holds_character"
        )
        self.assertIn(
            "flood_plain", [v["fingerprint"] for v in ipl.values()]
        )

    def test_neutral_has_india_map(self):
        neutral = [v for v in CH4["payoff"]["variants"] if v["league"] == "neutral"][0]
        self.assertEqual(len(neutral["india_map"]), 10)
        avgs = [x["avg_first_innings"] for x in neutral["india_map"] if x["avg_first_innings"]]
        self.assertEqual(avgs, sorted(avgs, reverse=True))


class TestInningsTotalBuffer(unittest.TestCase):
    def test_length_one_byte_per_point(self):
        meta = json.loads((canon.OUT_ROOT / "meta.json").read_text())
        self.assertEqual(len(BUF), meta["n_points"])

    def test_decode_matches_columnar(self):
        # the shipped columnar arrays are an independent per-delivery source:
        # recompute each innings total from (match_index, innings, runs_total)
        # and confirm every buffer byte == floor(total / 2), capped at 255.
        import gzip

        col = json.loads(
            gzip.decompress((canon.OUT_ROOT / "columnar.json.gz").read_bytes())
        )
        arrays = col["arrays"]
        mi, inn, rt = arrays["match_index"], arrays["innings"], arrays["runs_total"]
        self.assertEqual(len(mi), len(BUF))
        totals = defaultdict(int)
        for i in range(len(mi)):
            totals[(mi[i], inn[i])] += rt[i]
        for i in range(len(mi)):
            self.assertEqual(BUF[i], min(totals[(mi[i], inn[i])] // 2, 255))

    def test_buffer_descriptor(self):
        b = CH4["innings_total_buffer"]
        self.assertEqual(b["bytes_per_point"], 1)
        self.assertEqual(b["scale"], 2)
        self.assertEqual(b["file"], "innings_total.u8")


class TestEngineLight(unittest.TestCase):
    def test_no_new_engine_file(self):
        # Chapter 4 is engine-light: it reuses engine #1 and ships no engine of
        # its own. The engines/ directory carries the R2/R3b set; R7b later added
        # the credibility engines (stabilization/half_life/truetalent/trueecon),
        # which are not Ch4's and are listed here so the snapshot stays exact.
        engines = {p.name for p in (canon.OUT_ROOT / "engines").glob("*.json")}
        self.assertEqual(
            engines,
            {"par.json", "phasepar.json", "entry.json", "re288.json",
             "srplus.json", "wp_grid.json",
             "stabilization.json", "half_life.json", "truetalent.json",
             "trueecon.json"},
        )


class TestDeterminism(unittest.TestCase):
    def test_ch4_json_deterministic(self):
        doc = scenes.ch4_doc(scenes.build_ch4())
        raw = flatten.compact_json(doc, sort_keys=True)
        self.assertEqual(raw, (canon.OUT_ROOT / "scenes" / "ch4.json").read_bytes())

    def test_innings_total_buffer_deterministic(self):
        _g, _gi, _a, col, _d, _bf, _cr, _t, _m = flatten.build_stream()
        self.assertEqual(bytes(flatten.innings_totals(col)), BUF)


if __name__ == "__main__":
    unittest.main()
