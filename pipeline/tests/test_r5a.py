"""R5a — Chapter 8 "The Captain's Brain" (scenes/ch8.json) + Engine #6 (h2h.py).

The belief audit: five beliefs graded against the whole record, report-card shape
FAIL / FAIL / FAIL / FAIL-with-an-honest-residual / PASS (the pass saved for last).
Every on-screen number is asserted against the EMITTED scenes/ch8.json (loaded from
disk, the artifact that ships), cross-checked by a FULLY INDEPENDENT recount that
shares none of ch8.build_ch8's accumulators, and pinned to the grounded numbers in
r5a-scout-digest.md. Where the recount differs from the older blueprint teaser the
recount ships (ARTIFACT WINS); three honest deltas ride straight and are asserted as
deltas, never fudged toward the teaser:

  * TOSS (Belief 1, FAIL): field-first 42.9 -> 77.1 while the chase never paid any
    better (54.3 up to a 59.6 hump, back to 52.8); the two belief-vs-outcome lines
    actually CROSS; winning the toss itself is ~50/50 every era.
  * REVIEWS (Belief 2, FAIL): 988 reviews / 29.6% upheld; the 2022 doubling raised
    volume (1.26 -> 1.87 a match) while accuracy got WORSE (32.8 -> 28.1, delta),
    sliding to 16.9 by 2026; the 988-delivery chip subset carries team + outcome.
  * SPELL (Belief 3, FAIL): one-and-done overs 54.7 -> 64.1, WPL 75.3; the cold-
    return tax GREW +0.16 -> +0.30 (delta: the teaser's "stable ~0.2" is wrong).
  * MOMENTUM (Belief 4, FAIL + honest residual): a wicket-brings-a-wicket never
    clears the plain shuffle and turns anti (0.93) today; hitting-begets-hitting's
    batter-held residual is FLAT ~1.07 (NOT fading — the raw edge fades, the real
    part does not); all nulls precomputed.
  * REQUIRED RATE (Belief 5, PASS): the powerplay ask jumped 7.62 -> 9.19 above the
    middle overs and teams get ahead earlier, 31.7 -> 37.5 at halfway.
  * WPL: a two-season adoption curve 54.5 -> ~100% (not "born fully formed"), reviews
    calibrated like the men's game, out-fragments it; NEVER "behind".
  * PAYOFF: 16 report-card variants (10 IPL + 5 WPL + neutral), >=1 bespoke WPL card.
  * MATCH-DOTS: 1,331 centroids + a monotone 1,331-entry match_bounds (the buffer-
    free controlling morph); zero em dashes anywhere in the on-screen copy.
  * ENGINE #6 (h2h.py): the no-lookahead h2h table's three snapshot invariants hold
    with zero violations, confirmed here and in pipeline/tests/test_h2h.py.
  * DETERMINISM: a fresh build equals itself and the on-disk bytes (twice).
"""

from __future__ import annotations

import json
import sys
import unittest
from collections import defaultdict, Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import canon
import flatten
import ch8
import h2h

TESTS_DIR = Path(__file__).resolve().parent

DOC = None
DISK_BYTES = None


def setUpModule():
    global DOC, DISK_BYTES
    path = canon.OUT_ROOT / "scenes" / "ch8.json"
    if not path.exists():
        ch8.main()
    DISK_BYTES = path.read_bytes()
    DOC = json.loads(DISK_BYTES)  # the emitted artifact, exactly as it ships


# ===========================================================================
# Independent recount — its own corpus pass, its own point counter, its own
# logic; shares NONE of ch8.build_ch8's accumulators.
# ===========================================================================

RECOUNT = None
IPL_ERAS = ("2008-10", "2011-15", "2016-19", "2020-22", "2023-26")


def _era_of(s):
    if 2008 <= s <= 2010:
        return "2008-10"
    if 2011 <= s <= 2015:
        return "2011-15"
    if 2016 <= s <= 2019:
        return "2016-19"
    if 2020 <= s <= 2022:
        return "2020-22"
    if 2023 <= s <= 2026:
        return "2023-26"
    return None


def _phase_of(ov):
    return "pp" if ov <= 5 else ("mid" if ov <= 14 else "death")


def _recount():
    """One strict season-blocked point-order pass (identical order to flatten's
    stream), maintaining an independent point index so every review index lines up
    with the field's per-point buffers."""
    toss = defaultdict(lambda: {"n": 0, "field": 0, "decided": 0,
                                "chase_win": 0, "twm": 0})
    drs = defaultdict(lambda: {"rev": 0, "upheld": 0})
    matches_per = defaultdict(int)
    drs_by_team = defaultdict(lambda: [0, 0])
    review_idx, review_team, review_out = [], [], []
    spell = defaultdict(lambda: [0, 0])
    reentry = defaultdict(lambda: defaultdict(
        lambda: {"p1": [0, 0], "re": [0, 0], "cont": [0, 0]}))
    chasepace = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    ahead10 = defaultdict(lambda: [0, 0])
    fr_venue = defaultdict(Counter)
    match_rows = []
    n_matches = 0

    pi = -1
    for _mi, (_d, _m, league, path) in enumerate(flatten.sorted_match_files()):
        with open(path) as fh:
            match = json.load(fh)
        info = match["info"]
        season = canon.canon_season(info)
        era = _era_of(season)
        key = (league, season)
        matches_per[key] += 1
        n_matches += 1
        venue = info["venue"]
        tinfo = info["toss"]
        decision = tinfo["decision"]
        tw = canon.canon_team(tinfo["winner"])
        teams = [canon.canon_team(t) for t in info["teams"]]
        other = next((t for t in teams if t != tw), tw)
        winner = info.get("outcome", {}).get("winner")
        winner = canon.canon_team(winner) if winner else None
        chase = other if decision == "bat" else tw
        T = toss[key]
        T["n"] += 1
        if decision == "field":
            T["field"] += 1
        if winner is not None:
            T["decided"] += 1
            if winner == chase:
                T["chase_win"] += 1
            if winner == tw:
                T["twm"] += 1
        for t in teams:
            fr_venue[(league, t)][venue] += 1
        match_rows.append({"league": league, "venue": venue, "teams": teams,
                           "chase": chase, "toss_winner": tw,
                           "decision": decision, "winner": winner})

        innings = [i for i in match.get("innings", []) if not canon.is_super_over(i)]
        first_total = None
        for ii, inn in enumerate(innings):
            over_seq = []
            over_runs = {}
            for over in inn["overs"]:
                ov = over["over"]
                over_seq.append((ov, over["deliveries"][0]["bowler"]))
                over_runs[ov] = 0
                for dl in over["deliveries"]:
                    pi += 1
                    over_runs[ov] += dl["runs"]["total"]
                    rv = dl.get("review")
                    if rv:
                        drs[key]["rev"] += 1
                        up = rv.get("decision") == "upheld"
                        if up:
                            drs[key]["upheld"] += 1
                        by = rv.get("by")
                        bt = None
                        if by:
                            try:
                                bt = canon.canon_team(by)
                            except KeyError:
                                bt = None
                        if bt:
                            drs_by_team[(league, bt)][0] += 1
                            if up:
                                drs_by_team[(league, bt)][1] += 1
                        if league == "ipl":
                            review_idx.append(pi)
                            review_team.append(
                                canon.team_id("ipl", bt) if bt else -1)
                            review_out.append(1 if up else 0)
            # spells: maximal same-end (over-parity) consecutive-over runs
            ends = {0: [], 1: []}
            for ov, bw in over_seq:
                ends[ov % 2].append((ov, bw))
            spell_pos = {}
            is_re = {}
            for par in (0, 1):
                seq = ends[par]
                seen = set()
                i = 0
                while i < len(seq):
                    ov, bw = seq[i]
                    j = i
                    while j + 1 < len(seq) and seq[j + 1][1] == bw:
                        j += 1
                    length = j - i + 1
                    spell[key][0] += 1
                    if length == 1:
                        spell[key][1] += 1
                    reent = bw in seen
                    for pos, (o2, _b) in enumerate(seq[i:j + 1]):
                        spell_pos[o2] = pos + 1
                        is_re[o2] = (pos == 0 and reent)
                    seen.add(bw)
                    i = j + 1
            etag = ("wpl" if league == "wpl" else "ipl") + ":" + (era or "na")
            for ov, runs in over_runs.items():
                pos = spell_pos.get(ov, 1)
                bk = reentry[etag][ov]
                if pos == 1:
                    bk["p1"][0] += runs
                    bk["p1"][1] += 1
                    if is_re.get(ov):
                        bk["re"][0] += runs
                        bk["re"][1] += 1
                else:
                    bk["cont"][0] += runs
                    bk["cont"][1] += 1
            # required rate (2nd innings, non-D/L, full 20-over target)
            if ii == 0:
                first_total = sum(dl["runs"]["total"] for o in inn["overs"]
                                  for dl in o["deliveries"])
            if ii == 1 and era is not None and not canon.is_dl(info):
                tgt = inn.get("target", {})
                tov = tgt.get("overs")
                tr = tgt.get("runs",
                             (first_total + 1) if first_total is not None else None)
                if tov == 20 and tr:
                    over_cum = {}
                    cum = 0
                    for over in inn["overs"]:
                        ov = over["over"]
                        ph = _phase_of(ov)
                        cp = chasepace[era][ph]
                        for dl in over["deliveries"]:
                            ex = dl.get("extras", {})
                            legal = not ("wides" in ex or "noballs" in ex)
                            cum += dl["runs"]["total"]
                            cp[0] += dl["runs"]["total"]
                            if legal:
                                cp[1] += 1
                        over_cum[ov] = cum
                    r10 = over_cum.get(9)
                    if r10 is not None:
                        ahead10[era][1] += 1
                        if r10 > tr / 2.0:
                            ahead10[era][0] += 1

    return {
        "toss": toss, "drs": drs, "matches_per": matches_per,
        "drs_by_team": drs_by_team, "review_idx": review_idx,
        "review_team": review_team, "review_out": review_out, "spell": spell,
        "reentry": reentry, "chasepace": chasepace, "ahead10": ahead10,
        "fr_venue": fr_venue, "match_rows": match_rows, "n_matches": n_matches,
    }


def recount():
    global RECOUNT
    if RECOUNT is None:
        RECOUNT = _recount()
    return RECOUNT


def pct(a, b):
    return 100.0 * a / b if b else None


def r1(x):
    return round(x, 1) if x is not None else None


def r2(x):
    return round(x, 2) if x is not None else None


def era_pool(rc, league, band, field):
    seasons = canon.IPL_SEASONS if league == "ipl" else canon.WPL_SEASONS
    return sum(field((league, s)) for s in seasons if _era_of(s) == band)


def matched_tax(buckets, kind):
    num = 0.0
    w = 0
    for ov in sorted(buckets):
        a = buckets[ov][kind]
        c = buckets[ov]["cont"]
        if a[1] >= 5 and c[1] >= 5:
            num += a[1] * (a[0] / a[1] - c[0] / c[1])
            w += a[1]
    return (num / w) if w else None


# ===========================================================================
# Belief 0 — the match-dots (THE controlling morph, buffer-free)
# ===========================================================================


class MatchDotsTest(unittest.TestCase):
    def setUp(self):
        self.md = DOC["match_dots"]

    def test_1331_matches_over_316199_balls(self):
        self.assertEqual(self.md["count"], 1331)
        self.assertEqual(self.md["n_points"], 316199)
        self.assertEqual(len(self.md["centroids"]), 1331)
        self.assertEqual(len(self.md["season"]), 1331)
        self.assertEqual(len(self.md["league"]), 1331)
        self.assertEqual(self.md["ipl_matches"] + self.md["wpl_matches"], 1331)
        # both leagues present in the cloud from the first frame
        self.assertGreater(self.md["ipl_matches"], 0)
        self.assertGreater(self.md["wpl_matches"], 0)

    def test_centroid_encoding(self):
        toss_classes = set()
        result_codes = set()
        for x, y, tc, rc in self.md["centroids"]:
            self.assertTrue(0.0 <= x <= 1.0)
            self.assertTrue(0.0 <= y <= 1.0)
            toss_classes.add(tc)
            result_codes.add(rc)
        # 0 = bat-first (upper lane) / 1 = field-first (lower lane)
        self.assertEqual(toss_classes, {0, 1})
        # 1 chase won / 0 bat-first won / -1 undecided
        self.assertTrue(result_codes <= {-1, 0, 1})

    def test_match_bounds_monotone_1331(self):
        b = self.md["bounds"]
        self.assertEqual(len(b), 1331)
        self.assertEqual(b[0], 0)  # first match starts at point 0
        # monotone non-decreasing block-start indices (the in-shader binary-search
        # target); every start is a real field point index
        self.assertEqual(b, sorted(b))
        self.assertLess(b[-1], self.md["n_points"])
        self.assertTrue(all(0 <= s < self.md["n_points"] for s in b))

    def test_buffer_free_morph(self):
        # the match-dots add NO new per-point attribute (14-attribute ceiling)
        cm = DOC["controlling_morph"]
        self.assertEqual(cm["name"], "match-dots")
        self.assertIn("no new per-point", cm["note"].lower())
        self.assertIn("data texture", cm["reuses_buffer"].lower())


# ===========================================================================
# Belief 1 — the toss revolution (HERO, FAIL)
# ===========================================================================


class TossTest(unittest.TestCase):
    def setUp(self):
        self.rc = recount()
        self.toss = DOC["toss"]

    def test_grade_fail(self):
        self.assertEqual(self.toss["grade"], "fail")

    def test_era_field_first_and_chase_win_vs_recount(self):
        rc = self.rc
        for row in self.toss["eras"]:
            b = row["era"]
            self.assertEqual(
                r1(pct(era_pool(rc, "ipl", b, lambda k: rc["toss"][k]["field"]),
                       era_pool(rc, "ipl", b, lambda k: rc["toss"][k]["n"]))),
                row["field_first"], f"field-first {b}")
            self.assertEqual(
                r1(pct(era_pool(rc, "ipl", b, lambda k: rc["toss"][k]["chase_win"]),
                       era_pool(rc, "ipl", b, lambda k: rc["toss"][k]["decided"]))),
                row["chase_win"], f"chase-win {b}")
            self.assertEqual(
                era_pool(rc, "ipl", b, lambda k: rc["toss"][k]["n"]), row["n"])
            self.assertEqual(
                era_pool(rc, "ipl", b, lambda k: rc["toss"][k]["decided"]),
                row["decided"])

    def test_the_belief_hardened_the_result_did_not(self):
        eras = self.toss["eras"]
        # doctrine hardened: field-first 42.9 -> 77.1 (+34pts)
        self.assertEqual(eras[0]["field_first"], 42.9)
        self.assertEqual(eras[-1]["field_first"], 77.1)
        self.assertGreater(eras[-1]["field_first"] - eras[0]["field_first"], 30)
        # the chase never paid better: 54.3 up to a 59.6 hump (2016-19), back to 52.8
        self.assertEqual(eras[0]["chase_win"], 54.3)
        self.assertEqual(eras[2]["chase_win"], 59.6)
        self.assertEqual(eras[-1]["chase_win"], 52.8)
        self.assertLess(eras[-1]["chase_win"], eras[0]["chase_win"])  # flat/down

    def test_winning_the_toss_is_a_coin_flip_every_era(self):
        for row in self.toss["eras"]:
            self.assertTrue(45.0 <= row["tosswin_matchwin"] <= 58.0,
                            f"{row['era']} toss-to-win {row['tosswin_matchwin']}")

    def test_the_two_lines_actually_cross(self):
        cr = self.toss["crossover"]
        ff = cr["field_first_line"]
        cw = cr["chase_win_line"]
        self.assertEqual(len(ff), 5)
        self.assertEqual(len(cw), 5)
        # a choice-line and a result-line, drawn as the real data draws them: the
        # choice starts BELOW the result and ends far ABOVE it -> they cross
        self.assertLess(ff[0][1], cw[0][1])   # 42.9 < 54.3
        self.assertGreater(ff[-1][1], cw[-1][1])  # 77.1 > 52.8
        self.assertIsNotNone(cr["crossing_point"])
        self.assertEqual(len(cr["crossing_point"]["between"]), 2)
        # no misleading shaded wedge between two crossing lines
        self.assertIn("no shaded area", cr["note"].lower())

    def test_headline_numbers_are_bound_to_the_eras(self):
        h = self.toss["headline"]
        eras = self.toss["eras"]
        self.assertEqual(h["field_first_start"], eras[0]["field_first"])
        self.assertEqual(h["field_first_end"], eras[-1]["field_first"])
        self.assertEqual(h["chase_win_hump"], eras[2]["chase_win"])


# ===========================================================================
# Belief 2 — the review economics (HERO, FAIL): accuracy got WORSE
# ===========================================================================


class ReviewTest(unittest.TestCase):
    def setUp(self):
        self.rc = recount()
        self.rv = DOC["review"]

    def test_grade_fail(self):
        self.assertEqual(self.rv["grade"], "fail")

    def test_totals_vs_recount(self):
        rc = self.rc
        tot_rev = sum(rc["drs"][("ipl", s)]["rev"] for s in canon.IPL_SEASONS)
        tot_up = sum(rc["drs"][("ipl", s)]["upheld"] for s in canon.IPL_SEASONS)
        self.assertEqual(self.rv["total"], tot_rev)
        self.assertEqual(self.rv["total"], 988)
        self.assertEqual(self.rv["upheld"], tot_up)
        self.assertEqual(self.rv["upheld"], 292)
        self.assertEqual(self.rv["upheld_pct"], r1(pct(tot_up, tot_rev)))
        self.assertEqual(self.rv["upheld_pct"], 29.6)

    def test_more_reviews_worse_accuracy_the_honest_delta(self):
        rc = self.rc

        def window(lo, hi):
            r = u = m = 0
            for s in canon.IPL_SEASONS:
                if lo <= s <= hi:
                    r += rc["drs"][("ipl", s)]["rev"]
                    u += rc["drs"][("ipl", s)]["upheld"]
                    m += rc["matches_per"][("ipl", s)]
            return r, u, m

        pr, pu, pm = window(2018, 2021)
        qr, qu, qm = window(2022, 2026)
        pre = self.rv["windows"]["pre"]
        post = self.rv["windows"]["post"]
        # volume UP (the 2022 doubling)
        self.assertEqual(pre["per_match"], r2(pr / pm))
        self.assertEqual(post["per_match"], r2(qr / qm))
        self.assertEqual(pre["per_match"], 1.26)
        self.assertEqual(post["per_match"], 1.87)
        self.assertGreater(post["per_match"], pre["per_match"])
        # accuracy DOWN — 32.8 -> 28.1: the belief FAILS harder than the teaser
        self.assertEqual(pre["upheld_pct"], r1(pct(pu, pr)))
        self.assertEqual(post["upheld_pct"], r1(pct(qu, qr)))
        self.assertEqual(pre["upheld_pct"], 32.8)
        self.assertEqual(post["upheld_pct"], 28.1)
        self.assertLess(post["upheld_pct"], pre["upheld_pct"])
        # and the slide continues to 16.9 by 2026
        self.assertEqual(self.rv["per_season"]["2026"]["upheld_pct"], 16.9)
        # the copy ships "got worse", scoped honestly (never "the reviewing got dumber")
        self.assertIn("worse", self.rv["honesty"].lower())
        self.assertIn("dumber", self.rv["honesty"].lower())

    def test_leaderboard_vs_recount(self):
        rc = self.rc
        for lb in self.rv["leaderboard"]:
            rev, up = rc["drs_by_team"][("ipl", lb["team"])]
            self.assertEqual(lb["reviews"], rev, lb["short"])
            self.assertEqual(lb["upheld"], up, lb["short"])
            self.assertEqual(lb["struck"], rev - up, lb["short"])
            self.assertEqual(lb["upheld_pct"], r1(pct(up, rev)), lb["short"])
            self.assertGreaterEqual(lb["reviews"], 20)  # leaderboard threshold
        # RCB best, DC last (the digest's discipline leaderboard)
        self.assertEqual(self.rv["leaderboard"][0]["short"], "RCB")
        self.assertEqual(self.rv["leaderboard"][-1]["short"], "DC")


class ReviewSubsetTest(unittest.TestCase):
    def setUp(self):
        self.rc = recount()
        self.sub = DOC["review_subset"]

    def test_988_chip_deliveries_with_team_and_outcome(self):
        self.assertEqual(self.sub["count"], 988)
        self.assertEqual(len(self.sub["indices"]), 988)
        self.assertEqual(len(self.sub["team"]), 988)
        self.assertEqual(len(self.sub["outcome"]), 988)

    def test_indices_align_with_the_field_point_order(self):
        idx = self.sub["indices"]
        # ascending, unique, every one a real field point in range
        self.assertEqual(idx, sorted(set(idx)))
        n = DOC["match_dots"]["n_points"]
        self.assertTrue(all(0 <= i < n for i in idx))
        # and they match the independent recount's IPL review indices exactly
        self.assertEqual(idx, self.rc["review_idx"])

    def test_team_and_outcome_channels(self):
        # outcome 0 = struck down (the call stood) / 1 = upheld (paid off)
        self.assertTrue(set(self.sub["outcome"]) <= {0, 1})
        self.assertEqual(sum(self.sub["outcome"]), DOC["review"]["upheld"])
        self.assertEqual(sum(self.sub["outcome"]), 292)
        # the "mostly red" read: far more struck-down than paid-off
        self.assertGreater(len(self.sub["outcome"]) - sum(self.sub["outcome"]),
                           sum(self.sub["outcome"]))
        # team = reviewing IPL franchise id (or -1 unknown); all valid
        for t in self.sub["team"]:
            self.assertTrue(t == -1 or 0 <= t < len(canon.TEAMS))
        self.assertEqual(self.sub["team"], self.rc["review_team"])
        self.assertEqual(self.sub["outcome"], self.rc["review_out"])


# ===========================================================================
# Belief 3 — spell fragmentation + the cold-return tax (SUPPORTING, FAIL)
# ===========================================================================


class SpellTest(unittest.TestCase):
    def setUp(self):
        self.rc = recount()
        self.sp = DOC["spell"]

    def test_grade_fail(self):
        self.assertEqual(self.sp["grade"], "fail")

    def test_one_over_share_vs_recount(self):
        rc = self.rc
        for b in IPL_ERAS:
            one = era_pool(rc, "ipl", b, lambda k: rc["spell"][k][1])
            tot = era_pool(rc, "ipl", b, lambda k: rc["spell"][k][0])
            self.assertEqual(self.sp["per_era"][b]["one_over_share"],
                             r1(pct(one, tot)), b)
        # fragmentation 54.7 -> 64.1
        self.assertEqual(self.sp["per_era"]["2008-10"]["one_over_share"], 54.7)
        self.assertEqual(self.sp["per_era"]["2023-26"]["one_over_share"], 64.1)
        self.assertGreater(self.sp["per_era"]["2023-26"]["one_over_share"],
                           self.sp["per_era"]["2008-10"]["one_over_share"])

    def test_wpl_out_fragments_the_modern_mens_game(self):
        rc = self.rc
        one = era_pool(rc, "wpl", "2023-26", lambda k: rc["spell"][k][1])
        tot = era_pool(rc, "wpl", "2023-26", lambda k: rc["spell"][k][0])
        self.assertEqual(self.sp["wpl"]["one_over_share"], r1(pct(one, tot)))
        self.assertEqual(self.sp["wpl"]["one_over_share"], 75.3)
        self.assertGreater(self.sp["wpl"]["one_over_share"],
                           self.sp["per_era"]["2023-26"]["one_over_share"])

    def test_the_cold_return_tax_GREW_not_stable(self):
        rc = self.rc
        tax = self.sp["cold_return_tax"]
        for b in ("2008-10", "2016-19", "2023-26"):
            self.assertEqual(tax[b]["matched"],
                             r2(matched_tax(rc["reentry"]["ipl:" + b], "p1")), b)
            self.assertEqual(tax[b]["strict"],
                             r2(matched_tax(rc["reentry"]["ipl:" + b], "re")), b)
        # the honest delta: the tax roughly DOUBLED, +0.16 -> +0.30 (not "stable ~0.2")
        self.assertEqual(tax["2008-10"]["matched"], 0.16)
        self.assertEqual(tax["2023-26"]["matched"], 0.30)
        self.assertLess(tax["2008-10"]["matched"], tax["2016-19"]["matched"])
        self.assertLess(tax["2016-19"]["matched"], tax["2023-26"]["matched"])
        self.assertGreater(tax["2023-26"]["matched"],
                           tax["2008-10"]["matched"] * 1.5)
        # the WPL tax is dropped on screen (too thin)
        self.assertNotIn("WPL", tax)


# ===========================================================================
# Belief 4 — momentum (SUPPORTING, FAIL with an honest residual)
# ===========================================================================


class MomentumTest(unittest.TestCase):
    def setUp(self):
        self.mom = DOC["momentum"]

    def test_grade_fail(self):
        self.assertEqual(self.mom["grade"], "fail")

    def test_menu_of_seven_claims(self):
        self.assertEqual(len(self.mom["menu"]), 7)
        claims = [m["claim"] for m in self.mom["menu"]]
        self.assertIn("wkt|wkt", claims)
        self.assertIn("bnd|bnd", claims)
        # every menu item carries a fan-language gloss (no term of art on screen)
        for m in self.mom["menu"]:
            self.assertTrue(m["fan"].strip())

    def _row(self, era, claim):
        return next(r for r in self.mom["claims_by_era"][era] if r["claim"] == claim)

    def test_a_wicket_brings_a_wicket_does_not_clear_the_null(self):
        # the load-bearing pundit belief never clears the plain shuffle in any era,
        # and turns the WRONG way (anti, < 1.0) in today's game
        for era in ("2008-10", "2016-19", "2023-26"):
            self.assertFalse(self._row(era, "wkt|wkt")["plain_null"]["clears"],
                             f"wkt|wkt cleared plain null in {era}")
        modern = self._row("2023-26", "wkt|wkt")
        self.assertEqual(modern["lift"], 0.926)
        self.assertLess(modern["lift"], 1.0)  # anti
        self.assertFalse(modern["batter_null"]["clears"])
        self.assertEqual(self.mom["summary"]["wicket_plain_lifts"]["2023-26"], 0.926)

    def test_hitting_residual_is_FLAT_not_fading(self):
        resid = self.mom["summary"]["boundary_residuals"]
        vals = [resid["2008-10"], resid["2016-19"], resid["2023-26"]]
        # the batter-held residual sits at ~1.07 and holds steady, era to era
        for v in vals:
            self.assertAlmostEqual(v, 1.07, delta=0.03)
        self.assertLessEqual(max(vals) - min(vals), 0.03)
        # NOT fading: the last era is not materially below the first
        self.assertGreaterEqual(resid["2023-26"], resid["2008-10"] - 0.02)
        # meanwhile the RAW edge genuinely fades (1.21 -> 1.159): the real part
        # holds while the big number shrinks
        raw = self.mom["summary"]["boundary_raw_lifts"]
        self.assertGreater(raw["2008-10"], raw["2023-26"])
        raw_drop = raw["2008-10"] - raw["2023-26"]
        resid_drop = resid["2008-10"] - resid["2023-26"]
        self.assertGreater(raw_drop, resid_drop)
        # the six residual is a larger but still-real sliver (> 1.0 every era)
        for v in self.mom["summary"]["six_residuals"].values():
            self.assertGreater(v, 1.0)
        # the copy frames it as steady/flat, never as fading
        txt = self.mom["summary"]["text"].lower()
        self.assertIn("flat", txt)
        self.assertIn("steady", txt)
        self.assertNotIn("fad", txt)  # not "fade" / "fading"

    def test_nulls_are_precomputed(self):
        self.assertIn("precomputed", self.mom["definition"].lower())
        CLAIMS4 = {"bnd|bnd", "dot|dot", "six|six", "wkt|wkt"}
        for era in ("2008-10", "2016-19", "2023-26"):
            for row in self.mom["claims_by_era"][era]:
                # the plain shuffle histogram is baked at build time (a lookup)
                self.assertIn("plain_null", row)
                self.assertTrue(sum(row["plain_null"]["counts"]) > 0)
                # the fuller batter-held shuffle rides the four core claims
                if row["claim"] in CLAIMS4:
                    self.assertIn("batter_null", row)
                    self.assertTrue(sum(row["batter_null"]["counts"]) > 0)
                else:
                    self.assertNotIn("batter_null", row)

    def test_scripted_beats(self):
        self.assertEqual(self.mom["scripted"]["wicket_myth"], "wkt|wkt")
        self.assertEqual(self.mom["scripted"]["hitting_sliver"], "bnd|bnd")


# ===========================================================================
# Belief 5 — required-rate responsiveness (SUPPORTING, PASS, saved for last)
# ===========================================================================


class RequiredRateTest(unittest.TestCase):
    def setUp(self):
        self.rc = recount()
        self.req = DOC["required_rate"]

    def test_grade_pass(self):
        self.assertEqual(self.req["grade"], "pass")

    def test_chase_pace_by_phase_vs_recount(self):
        rc = self.rc
        for era in ("2008-10", "2023-26"):
            for ph in ("pp", "mid", "death"):
                r, b = rc["chasepace"][era][ph]
                self.assertEqual(self.req["by_era"][era][ph],
                                 r2(6.0 * r / b) if b else None, f"{era} {ph}")

    def test_the_chase_front_loaded(self):
        by = self.req["by_era"]
        # the powerplay ask jumped 7.62 -> 9.19 (+1.57)
        self.assertEqual(by["2008-10"]["pp"], 7.62)
        self.assertEqual(by["2023-26"]["pp"], 9.19)
        self.assertEqual(self.req["pp_jump"], 1.57)
        # and now sits ABOVE the middle overs (the shape flipped)
        self.assertGreater(by["2023-26"]["pp"], by["2023-26"]["mid"])
        # 2008 was up-sloping: powerplay below the death overs
        self.assertLess(by["2008-10"]["pp"], by["2008-10"]["death"])

    def test_ahead_at_halfway_rose_vs_recount(self):
        rc = self.rc
        for era in ("2008-10", "2023-26"):
            self.assertEqual(self.req["ahead_halfway"][era],
                             r1(pct(rc["ahead10"][era][0], rc["ahead10"][era][1])))
        self.assertEqual(self.req["ahead_halfway"]["2008-10"], 31.7)
        self.assertEqual(self.req["ahead_halfway"]["2023-26"], 37.5)
        self.assertGreater(self.req["ahead_halfway"]["2023-26"],
                           self.req["ahead_halfway"]["2008-10"])

    def test_pass_is_on_pacing_not_on_winning(self):
        # the honest caveat: the pass is the pacing SHAPE, NOT that chasing wins more
        cav = self.req["caveat"].lower()
        self.assertIn("shape", cav)
        self.assertIn("not", cav)
        self.assertIn("wins more", cav)


# ===========================================================================
# WPL doctrine transmission — analytics-native, a 2-season curve, never behind
# ===========================================================================


class WplTest(unittest.TestCase):
    def setUp(self):
        self.rc = recount()
        self.wpl = DOC["wpl"]

    def test_adoption_curve_vs_recount(self):
        rc = self.rc
        for s in canon.WPL_SEASONS:
            t = rc["toss"][("wpl", s)]
            if t["n"]:
                got = self.wpl["field_first_by_season"][str(s)]
                self.assertEqual(got["field_first"], r1(pct(t["field"], t["n"])))
                self.assertEqual(got["matches"], t["n"])  # counts carried

    def test_two_season_curve_not_born_fully_formed(self):
        ff = self.wpl["field_first_by_season"]
        # season one splits the toss like the men's game did in 2008, ~54.5
        self.assertEqual(ff["2023"]["field_first"], 54.5)
        # then ramps hard to ~100% two seasons later
        self.assertEqual(ff["2025"]["field_first"], 100.0)
        self.assertGreater(ff["2025"]["field_first"], ff["2023"]["field_first"])
        # the curve is emitted for the annotation plane
        self.assertEqual(len(self.wpl["adoption_curve"]), len(ff))

    def test_calibrated_reviews_and_pooled_share(self):
        rc = self.rc
        wf = sum(rc["toss"][("wpl", s)]["field"] for s in canon.WPL_SEASONS)
        wn = sum(rc["toss"][("wpl", s)]["n"] for s in canon.WPL_SEASONS)
        self.assertEqual(self.wpl["field_first_pooled"], r1(pct(wf, wn)))
        self.assertEqual(self.wpl["field_first_pooled"], 77.3)
        wrev = sum(rc["drs"][("wpl", s)]["rev"] for s in canon.WPL_SEASONS)
        wup = sum(rc["drs"][("wpl", s)]["upheld"] for s in canon.WPL_SEASONS)
        self.assertEqual(self.wpl["review"]["reviews"], wrev)
        self.assertEqual(self.wpl["review"]["upheld_pct"], r1(pct(wup, wrev)))
        self.assertEqual(self.wpl["review"]["upheld_pct"], 30.5)
        self.assertEqual(self.wpl["one_over_share"], 75.3)

    def test_never_behind(self):
        # the house framing rule: the WPL is analytics-native, never "behind"
        self.assertIn("analytics-native", self.wpl["framing"].lower())

        def strings(o):
            if isinstance(o, dict):
                for v in o.values():
                    yield from strings(v)
            elif isinstance(o, list):
                for v in o:
                    yield from strings(v)
            elif isinstance(o, str):
                yield o

        for s in strings(self.wpl):
            self.assertNotIn("behind", s.lower())


# ===========================================================================
# Payoff — 16 report-card variants (10 IPL + 5 WPL + neutral)
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

    def test_every_franchise_present(self):
        ipl = {v["team"] for v in self.variants if v["league"] == "ipl"}
        wpl = {v["team"] for v in self.variants if v["league"] == "wpl"}
        self.assertEqual(ipl, set(canon.CURRENT_IPL_FRANCHISES))
        self.assertEqual(wpl, set(canon.WPL_FRANCHISES))

    def test_ipl_cards_non_degenerate(self):
        for v in self.variants:
            if v["league"] != "ipl":
                continue
            self.assertFalse(v["empty_state"])
            self.assertTrue(v["headline"].strip())
            self.assertTrue(v["home_ground"])
            self.assertIsNotNone(v["field_first_at_home"]["pct"])
            self.assertIsNotNone(v["chase_win_at_home"]["pct"])
            self.assertIsNotNone(v["review_rank"])

    def test_at_least_one_bespoke_wpl_card(self):
        wpl = [v for v in self.variants if v["league"] == "wpl"]
        bespoke = [v for v in wpl if v.get("bespoke")]
        self.assertGreaterEqual(len(bespoke), 1)
        for v in wpl:
            # the analytics-native transmission beat made personal, never a deficit card
            self.assertTrue(v.get("bespoke"))
            self.assertTrue(v.get("wpl_transmission"))
            self.assertTrue(v["headline"].strip())
            self.assertIn("transmission", v)
            self.assertNotIn("behind", v["headline"].lower())

    def test_neutral_card_is_the_live_league_report(self):
        neu = next(v for v in self.variants if v["league"] == "neutral")
        self.assertIsNotNone(neu["league_field_first"])
        self.assertIsNotNone(neu["league_chase_win"])
        self.assertIsNotNone(neu["league_review_upheld"])
        self.assertTrue(neu["headline"].strip())


# ===========================================================================
# Report card + voice (zero em dashes, never "behind")
# ===========================================================================


class ReportCardTest(unittest.TestCase):
    def test_four_fails_one_pass_the_pass_last(self):
        rcd = DOC["report_card"]
        self.assertEqual(rcd["shape"], "four fails, one pass")
        grades = [b["grade"] for b in sorted(rcd["beliefs"], key=lambda b: b["slot"])]
        self.assertEqual(grades, ["fail", "fail", "fail", "fail", "pass"])
        # the graded sections agree with the rail
        self.assertEqual(DOC["toss"]["grade"], "fail")
        self.assertEqual(DOC["review"]["grade"], "fail")
        self.assertEqual(DOC["spell"]["grade"], "fail")
        self.assertEqual(DOC["momentum"]["grade"], "fail")
        self.assertEqual(DOC["required_rate"]["grade"], "pass")


def _iter_onscreen_strings(obj, key=None):
    """Every reader-facing string in the doc. The buffer-layout `encoding` notes are
    engineering documentation of the data channels (not shown to the reader), so they
    are skipped; everything else — captions, headlines, footnotes, glosses, flavor —
    is on-screen copy and is checked."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from _iter_onscreen_strings(v, k)
    elif isinstance(obj, list):
        for v in obj:
            yield from _iter_onscreen_strings(v, key)
    elif isinstance(obj, str):
        if key != "encoding":
            yield obj


class VoiceTest(unittest.TestCase):
    def test_zero_em_dashes_in_onscreen_copy(self):
        offenders = [s for s in _iter_onscreen_strings(DOC) if "—" in s]
        self.assertEqual(offenders, [], f"em dash in on-screen copy: {offenders[:3]}")

    def test_never_behind_anywhere_in_ch8_copy(self):
        offenders = [s for s in _iter_onscreen_strings(DOC) if "behind" in s.lower()]
        self.assertEqual(offenders, [], f"'behind' in ch8 copy: {offenders[:3]}")

    def test_footnotes_carry_the_grounded_numbers(self):
        # numbers in footnote prose must trace to the artifact / recount
        fns = DOC["footnotes"]
        # the Engine #6 footnote leads with the usable-history growth, not the score
        usable = fns["ch8-matchup"]["usable_by_season"]
        self.assertEqual(usable["2009"], 12.4)
        self.assertEqual(usable["2019"], 42.1)


# ===========================================================================
# Engine #6 — the no-lookahead h2h table (pipeline/h2h.py); 3 snapshot invariants
# ===========================================================================

N_PAIRS = 33772
N_BALLS = 305738
H2H_PAIRS = None


def h2h_pairs():
    """One strict-date corpus pass -> per-pair ordered BallEvent sequences."""
    global H2H_PAIRS
    if H2H_PAIRS is None:
        per_pair = defaultdict(list)
        for ev in h2h.iter_deliveries():
            per_pair[(ev.batter, ev.bowler)].append(ev)
        H2H_PAIRS = dict(per_pair)
    return H2H_PAIRS


class EngineSixTest(unittest.TestCase):
    def test_the_engine6_suite_exists(self):
        src = (TESTS_DIR / "test_h2h.py")
        self.assertTrue(src.exists(), "pipeline/tests/test_h2h.py is missing")
        body = src.read_text()
        for fn in ("test_inv1_first_meeting_exposes_zero_prior",
                   "test_inv2_snapshot_equals_independent_rollup",
                   "test_inv3_pair_dates_non_decreasing"):
            self.assertIn(fn, body, f"{fn} missing from test_h2h.py")

    def test_inv1_first_meeting_exposes_zero_prior(self):
        pairs = h2h_pairs()
        violations = sum(
            1 for seq in pairs.values()
            if (seq[0].prior_balls, seq[0].prior_runs, seq[0].prior_dismissals)
            != (0, 0, 0))
        self.assertEqual(violations, 0)
        self.assertEqual(len(pairs), N_PAIRS)

    def test_inv2_snapshot_equals_independent_rollup(self):
        pairs = h2h_pairs()
        violations = checked = 0
        for seq in pairs.values():
            balls = runs = dis = 0  # independent replay; the engine is never consulted
            for ev in seq:
                checked += 1
                if (ev.prior_balls, ev.prior_runs, ev.prior_dismissals) != (
                        balls, runs, dis):
                    violations += 1
                balls += 1
                runs += ev.runs
                dis += 1 if ev.dismissed else 0
        self.assertEqual(violations, 0)
        self.assertEqual(checked, N_BALLS)

    def test_inv3_pair_dates_non_decreasing(self):
        pairs = h2h_pairs()
        violations = sum(
            1 for seq in pairs.values()
            if [ev.date for ev in seq] != sorted(ev.date for ev in seq))
        self.assertEqual(violations, 0)


# ===========================================================================
# Determinism — a fresh build equals itself and the on-disk bytes (twice)
# ===========================================================================


class DeterminismTest(unittest.TestCase):
    def test_fresh_recompute_is_byte_identical(self):
        b2 = flatten.compact_json(ch8.build_doc(), sort_keys=True)
        b3 = flatten.compact_json(ch8.build_doc(), sort_keys=True)
        self.assertEqual(b2, b3, "two fresh builds diverged")
        self.assertEqual(b2, DISK_BYTES, "on-disk ch8.json != fresh recompute")


if __name__ == "__main__":
    unittest.main()
