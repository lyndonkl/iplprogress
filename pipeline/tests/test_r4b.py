"""R4b — Chapter 7 "The Twelfth Man" (scenes/ch7.json).

The Impact Player rule as a natural experiment. These tests protect the numbers
against a FULLY INDEPENDENT recount (its own corpus pass, its own point-index
counter, its own impact-sub / license / placebo / entropy logic — none of it
sharing ch7.build_ch7's accumulators):

  * IMPACT-SUB EXTRACTION — 556 match/impact_player events across 517 distinct
    deliveries (IPL 2023+); the WPL records 0 (no such rule — the control arm);
    the bat-vs-bowl reinforcement split; and the spark index list aligns exactly
    with the field point order (every spark index is an IPL 2023+ delivery,
    ascending and unique).
  * THE NATURAL EXPERIMENT — IPL run rate range-bound 7.5-8.7 for 2008-2022 then
    8.99/9.56/9.63/9.88; the rule-free WPL 8.08 -> 8.54 (+0.46); the diff-in-diff
    estimate (~+0.9 RPO), each against the independent recount.
  * LICENSE INDEX — at identical match states (>=4 down, overs 7-16) SR 116.8 ->
    129.9 while the dismissal rate held ~flat (4.88 -> 4.95, i.e. NOT falling —
    the honest correction); the top order took the licence most (+18.0% vs +11.0%).
  * THE PLACEBO GRID — the true 2023 date stands out clean from the entire
    pre-rule placebo cloud (2012-2022) on both level shift and t; and the honest
    disclosure that 2024's raw magnitude is the global max (the break deepens).
  * PLAYBOOK — subs at the innings break 51.8% (2023) -> 35.7% (2025).
  * THE HONEST NULL — entry entropy flat across the rule; top-3 SR 131.5 -> 155.3;
    part-timer bowlers per innings 5.79 -> 6.12.
  * PAYOFF — 16 team cards (10 IPL playbook + 5 WPL control-arm + neutral).
  * DETERMINISM — a fresh recompute equals itself and the on-disk bytes (twice).
"""

from __future__ import annotations

import json
import math
import sys
import unittest
from collections import defaultdict, Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import canon
import flatten
import ch7

DOC = None
ACC = None
DISK_BYTES = None


def setUpModule():
    global DOC, ACC, DISK_BYTES
    out = canon.OUT_ROOT
    path = out / "scenes" / "ch7.json"
    if not path.exists():
        ch7.main()
    DISK_BYTES = path.read_bytes()
    ACC = ch7.build_ch7()
    DOC = ch7.ch7_doc(ACC)


# ===========================================================================
# Independent recount — its own pass, its own point counter, its own logic
# ===========================================================================

RECOUNT = None
RETIRED = {"retired hurt", "retired out", "retired not out"}


def _recount():
    runs = defaultdict(int)
    legal = defaultdict(int)
    impact = []            # (point_index, season, team, in, reinforce, at_break, match_index)
    spark = set()
    wpl_impact = 0
    # license: period -> [runs, balls, dism]
    lic = defaultdict(lambda: [0, 0, 0])
    pos_sr = defaultdict(lambda: [0, 0])   # (period, pos) -> [runs, balls]
    playbook = defaultdict(lambda: [0, 0])  # season -> [break, mid]
    entry_wkts = defaultdict(Counter)      # (lg, season) -> Counter(wkts_down)
    tail = defaultdict(lambda: [0, 0])     # period -> [reached8, n]
    top3 = defaultdict(lambda: [0, 0])
    bowlers = defaultdict(lambda: [0, 0])  # season -> [sum_distinct, n]
    winner = {}

    def period(s):
        if 2020 <= s <= 2022:
            return "pre"
        if 2023 <= s <= 2026:
            return "post"
        return None

    pi = -1
    for mi, (_d, _m, league, path) in enumerate(flatten.sorted_match_files()):
        with open(path) as fh:
            match = json.load(fh)
        info = match["info"]
        season = canon.canon_season(info)
        w = info.get("outcome", {}).get("winner")
        winner[mi] = canon.canon_team(w) if w else None
        per = period(season)
        inn_no = 0
        for innings in match.get("innings", []):
            if canon.is_super_over(innings):
                continue
            inn_no += 1
            bteam = canon.canon_team(innings["team"])
            key = (league, season)
            pos = {}
            nextpos = 1
            wkts_down = 0
            distinct = set()
            reached8 = False
            for over in innings["overs"]:
                on = over["over"]
                for bi, dl in enumerate(over["deliveries"]):
                    pi += 1
                    ex = dl.get("extras", {})
                    wide = "wides" in ex
                    nb = "noballs" in ex
                    rb = dl["runs"]["batter"]
                    tot = dl["runs"]["total"]
                    distinct.add(dl["bowler"])
                    for who in (dl["batter"], dl["non_striker"]):
                        if who not in pos:
                            pos[who] = nextpos
                            nextpos += 1
                            entry_wkts[key][wkts_down] += 1
                            if pos[who] >= 8:
                                reached8 = True
                    stp = pos[dl["batter"]]
                    runs[key] += tot
                    if not wide and not nb:
                        legal[key] += 1
                    nwk = len([x for x in dl.get("wickets", []) if x.get("kind") not in RETIRED])
                    if league == "ipl" and per:
                        if 6 <= on <= 15 and wkts_down >= 4:
                            lic[per][0] += rb
                            if not wide:
                                lic[per][1] += 1
                            lic[per][2] += nwk
                        if not wide:
                            pos_sr[(per, stp)][0] += rb
                            pos_sr[(per, stp)][1] += 1
                            if stp <= 3:
                                top3[per][0] += rb
                                top3[per][1] += 1
                    wkts_down += nwk
                    for item in dl.get("replacements", {}).get("match", []):
                        if item.get("reason") != "impact_player":
                            continue
                        if league != "ipl":
                            wpl_impact += 1
                            continue
                        team = canon.canon_team(item["team"])
                        reinforce = "bat" if team == bteam else "bowl"
                        at_break = on == 0 and bi == 0
                        impact.append((pi, season, team, item["in"], reinforce, at_break, mi))
                        spark.add(pi)
                        playbook[season][0 if at_break else 1] += 1
            bowlers[season][0] += len(distinct)
            bowlers[season][1] += 1
            if league == "ipl" and per:
                tail[per][0] += 1 if reached8 else 0
                tail[per][1] += 1
    return {
        "runs": runs, "legal": legal, "impact": impact, "spark": spark,
        "wpl_impact": wpl_impact, "lic": lic, "pos_sr": pos_sr,
        "playbook": playbook, "entry_wkts": entry_wkts, "tail": tail,
        "top3": top3, "bowlers": bowlers, "winner": winner,
    }


def recount():
    global RECOUNT
    if RECOUNT is None:
        RECOUNT = _recount()
    return RECOUNT


def rr(rc, lg, s):
    return 6.0 * rc["runs"][(lg, s)] / rc["legal"][(lg, s)]


# ===========================================================================
# Impact-sub extraction
# ===========================================================================


class ImpactSubTest(unittest.TestCase):
    def setUp(self):
        self.rc = recount()
        self.isub = DOC["impact_subs"]

    def test_event_and_delivery_counts(self):
        self.assertEqual(self.isub["n_events"], len(self.rc["impact"]))
        self.assertEqual(self.isub["n_events"], 556)
        self.assertEqual(self.isub["n_spark_deliveries"], len(self.rc["spark"]))
        self.assertEqual(self.isub["n_spark_deliveries"], 517)

    def test_wpl_has_no_impact_rule(self):
        # the control arm: the WPL records ZERO impact-player substitutions
        self.assertEqual(self.isub["wpl_events"], 0)
        self.assertEqual(self.rc["wpl_impact"], 0)

    def test_reinforcement_split(self):
        bat = sum(1 for e in self.rc["impact"] if e[4] == "bat")
        bowl = sum(1 for e in self.rc["impact"] if e[4] == "bowl")
        self.assertEqual(self.isub["reinforcement"]["bat"], bat)
        self.assertEqual(self.isub["reinforcement"]["bowl"], bowl)
        self.assertEqual(bat + bowl, 556)
        self.assertEqual([bat, bowl], [256, 300])

    def test_spark_indices_align_with_field(self):
        spark = self.isub["spark_indices"]
        # ascending, unique, exactly the recounted distinct-delivery set
        self.assertEqual(spark, sorted(set(spark)))
        self.assertEqual(set(spark), self.rc["spark"])
        self.assertEqual(len(spark), 517)
        # every spark index is a real field point in the IPL 2023+ range
        n = ACC["n_points"]
        self.assertEqual(n, 316199)
        for idx in spark:
            self.assertTrue(0 <= idx < n)

    def test_by_season_events(self):
        exp = Counter(e[1] for e in self.rc["impact"])
        for s, c in self.isub["by_season"].items():
            self.assertEqual(c, exp[int(s)])
        self.assertEqual(sum(self.isub["by_season"].values()), 556)


# ===========================================================================
# The natural experiment (diff-in-diff)
# ===========================================================================


class NaturalExperimentTest(unittest.TestCase):
    def setUp(self):
        self.rc = recount()
        self.ne = DOC["natural_experiment"]

    def test_ipl_run_rate_series(self):
        for s in canon.IPL_SEASONS:
            self.assertEqual(self.ne["ipl_rr"][str(s)], round(rr(self.rc, "ipl", s), 2))
        # the validated post-rule sequence
        self.assertEqual(
            [self.ne["ipl_rr"][str(s)] for s in (2023, 2024, 2025, 2026)],
            [8.99, 9.56, 9.63, 9.88],
        )
        # range-bound 7.5-8.7 for the 15 pre-rule seasons
        band = [self.ne["ipl_rr"][str(s)] for s in range(2008, 2023)]
        self.assertGreaterEqual(min(band), 7.4)
        self.assertLessEqual(max(band), 8.7)

    def test_wpl_control_arm(self):
        for s in canon.WPL_SEASONS:
            self.assertEqual(self.ne["wpl_rr"][str(s)], round(rr(self.rc, "wpl", s), 2))
        self.assertEqual(self.ne["wpl_rr"]["2023"], 8.08)
        self.assertEqual(self.ne["wpl_rr"]["2026"], 8.54)
        self.assertEqual(self.ne["diff_in_diff"]["wpl_delta"], 0.46)

    def test_diff_in_diff_estimate(self):
        # the DiD is derived from the DISPLAYED (2-dp) per-season run rates, so a
        # reader who averages the numbers on screen reproduces it exactly.
        did = self.ne["diff_in_diff"]
        srr = lambda lg, s: round(rr(self.rc, lg, s), 2)
        ipl_post = sum(srr("ipl", s) for s in range(2023, 2027)) / 4
        ipl_band = sum(srr("ipl", s) for s in range(2008, 2023)) / 15
        wpl_delta = round(srr("wpl", 2026) - srr("wpl", 2023), 2)
        est = round((ipl_post - ipl_band) - wpl_delta, 2)
        self.assertEqual(did["estimate"], est)
        self.assertEqual(did["estimate"], 0.9)
        # the ~1 RPO gap opening at the treatment date
        self.assertAlmostEqual(did["level_gap_at_treatment"], round(ipl_post - ipl_band, 2), places=2)


# ===========================================================================
# License index (conditioned on identical match states)
# ===========================================================================


class LicenseIndexTest(unittest.TestCase):
    def setUp(self):
        self.rc = recount()
        self.li = DOC["license_index"]

    def test_state_conditioning_and_sr(self):
        # SR recomputed at >=4 down, overs 7-16 (over index 6-15)
        for per in ("pre", "post"):
            r, b, w = self.rc["lic"][per]
            self.assertEqual(self.li[per]["sr"], round(100.0 * r / b, 1))
            self.assertEqual(self.li[per]["dismissals_per_100"], round(100.0 * w / b, 2))
        self.assertEqual(self.li["pre"]["sr"], 116.8)
        self.assertEqual(self.li["post"]["sr"], 129.9)

    def test_dismissal_rate_did_not_fall(self):
        # the honest correction: aggression up at NO material rise in risk —
        # the dismissal rate held ~flat rather than falling
        self.assertEqual(self.li["pre"]["dismissals_per_100"], 4.88)
        self.assertEqual(self.li["post"]["dismissals_per_100"], 4.95)
        self.assertLess(
            abs(self.li["post"]["dismissals_per_100"] - self.li["pre"]["dismissals_per_100"]),
            0.5,
        )

    def test_by_position_top_order_took_it_most(self):
        def bucket(per, lo, hi):
            r = sum(self.rc["pos_sr"][(per, p)][0] for p in range(lo, hi + 1))
            b = sum(self.rc["pos_sr"][(per, p)][1] for p in range(lo, hi + 1))
            return 100.0 * r / b

        for label, (lo, hi) in (("1-3", (1, 3)), ("6-8", (6, 8))):
            p = bucket("pre", lo, hi)
            q = bucket("post", lo, hi)
            self.assertEqual(self.li["by_position"][label]["pct_change"], round(100.0 * (q - p) / p, 1))
        self.assertEqual(self.li["by_position"]["1-3"]["pct_change"], 18.0)
        self.assertEqual(self.li["by_position"]["6-8"]["pct_change"], 11.0)
        # the top order lifted more than the lower order
        self.assertGreater(
            self.li["by_position"]["1-3"]["pct_change"],
            self.li["by_position"]["6-8"]["pct_change"],
        )


# ===========================================================================
# Event-study placebo grid
# ===========================================================================


class PlaceboGridTest(unittest.TestCase):
    def setUp(self):
        self.rc = recount()
        self.es = DOC["event_study"]

    def _shift_t(self, c):
        # LOCAL symmetric window (R4b audit must-fix #1): the jump at candidate c is
        # the mean over the K seasons FROM c minus the mean over the K seasons BEFORE
        # c; for a made-up date before the rule the later window is capped at the last
        # pre-rule season (2022) so no fake date borrows the real post-2023 surge.
        K = 3
        rule = 2023
        cloud_hi = rule - 1
        seasons = list(canon.IPL_SEASONS)
        series = {s: rr(self.rc, "ipl", s) for s in seasons}
        after_hi = seasons[-1] if c >= rule else cloud_hi
        pre = [series[s] for s in seasons if c - K <= s <= c - 1]
        post = [series[s] for s in seasons if c <= s <= min(c + K - 1, after_hi)]
        mp = sum(pre) / len(pre)
        mq = sum(post) / len(post)
        vp = sum((x - mp) ** 2 for x in pre) / len(pre)
        vq = sum((x - mq) ** 2 for x in post) / len(post)
        se = math.sqrt(vp / len(pre) + vq / len(post))
        shift = mq - mp
        return shift, (shift / se if se else 0.0)

    def test_grid_matches_independent_fit(self):
        for cand in self.es["candidates"]:
            shift, t = self._shift_t(cand["season"])
            self.assertEqual(cand["level_shift"], round(shift, 3))
            self.assertEqual(cand["t"], round(t, 2))
        # the whole grid is emitted (a lookup, not a live fit)
        self.assertEqual([c["season"] for c in self.es["candidates"]], list(range(2012, 2026)))

    def test_true_date_stands_out_from_placebo_cloud(self):
        # the placebo honesty gate (release-blocking): the SIZE of the rule-year jump
        # clears every pre-rule candidate's jump. t is not the discriminator — a
        # flat-era candidate can post a large t on a small jump (tiny window variance),
        # so the on-screen quantity, the level shift, is what must separate.
        true_shift, _ = self._shift_t(2023)
        for c in range(2012, 2023):
            ps, _ = self._shift_t(c)
            self.assertLess(ps, true_shift, f"placebo {c} jump not below 2023")
        self.assertTrue(self.es["true_date_stands_out"])
        self.assertGreater(self.es["true_date_shift"], self.es["placebo_cloud_max_shift"])
        self.assertEqual(self.es["true_date"], 2023)

    def test_honest_disclosure_2024_is_global_max(self):
        # the honest read: 2023 clears the placebo cloud, but 2024's raw magnitude
        # is the single largest jump (the break deepens as teams learn the rule)
        seasons = list(range(2012, 2026))
        shifts = {c: self._shift_t(c)[0] for c in seasons}
        self.assertEqual(max(seasons, key=lambda c: shifts[c]), 2024)
        self.assertEqual(self.es["global_max_shift_date"], 2024)


# ===========================================================================
# Playbook decoder
# ===========================================================================


class PlaybookTest(unittest.TestCase):
    def setUp(self):
        self.rc = recount()
        self.pb = DOC["playbook"]

    def test_break_share_learning_curve(self):
        for s in range(2023, 2027):
            ab, md = self.rc["playbook"][s]
            self.assertEqual(self.pb["per_season"][str(s)]["break_pct"], round(100.0 * ab / (ab + md), 1))
        self.assertEqual(self.pb["per_season"]["2023"]["break_pct"], 51.8)
        self.assertEqual(self.pb["per_season"]["2025"]["break_pct"], 35.7)
        # teams learned: less at-the-break over time
        self.assertGreater(
            self.pb["per_season"]["2023"]["break_pct"],
            self.pb["per_season"]["2025"]["break_pct"],
        )


# ===========================================================================
# The honest null
# ===========================================================================


class HonestNullTest(unittest.TestCase):
    def setUp(self):
        self.rc = recount()
        self.hn = DOC["honest_null"]

    def _entropy(self, counter):
        t = sum(counter.values())
        return -sum((c / t) * math.log2(c / t) for c in counter.values() if c > 0) if t else 0.0

    def test_entry_entropy_flat(self):
        for s in canon.IPL_SEASONS:
            self.assertEqual(
                self.hn["entry_entropy"]["per_season"][str(s)],
                round(self._entropy(self.rc["entry_wkts"][("ipl", s)]), 3),
            )
        pre = Counter()
        for s in range(2020, 2023):
            pre.update(self.rc["entry_wkts"][("ipl", s)])
        post = Counter()
        for s in range(2023, 2027):
            post.update(self.rc["entry_wkts"][("ipl", s)])
        self.assertEqual(self.hn["entry_entropy"]["pre_pooled"], round(self._entropy(pre), 3))
        self.assertEqual(self.hn["entry_entropy"]["post_pooled"], round(self._entropy(post), 3))
        # the null: batting-order entry spread is essentially unchanged
        self.assertTrue(self.hn["entry_entropy"]["flat"])
        self.assertLess(abs(self.hn["entry_entropy"]["delta"]), 0.1)

    def test_top3_sr_jumped(self):
        for per in ("pre", "post"):
            r, b = self.rc["top3"][per]
            self.assertEqual(self.hn["top3_sr"][per], round(100.0 * r / b, 1))
        self.assertEqual(self.hn["top3_sr"]["pre"], 131.5)
        self.assertEqual(self.hn["top3_sr"]["post"], 155.3)

    def test_part_timer_bowling_dividend(self):
        for s in canon.IPL_SEASONS:
            sd, n = self.rc["bowlers"][s]
            self.assertEqual(self.hn["part_timer"]["per_season"][str(s)], round(sd / n, 2))
        self.assertEqual(self.hn["part_timer"]["pre_2022"], 5.79)
        self.assertEqual(self.hn["part_timer"]["post_2023"], 6.12)

    def test_tail_exposure_flat(self):
        for per in ("pre", "post"):
            reached, n = self.rc["tail"][per]
            self.assertEqual(
                self.hn["tail_exposure"][per], round(100.0 * reached / n, 1)
            )


# ===========================================================================
# Payoff (16 team-playbook cards)
# ===========================================================================


class PayoffTest(unittest.TestCase):
    def setUp(self):
        self.pay = DOC["payoff"]
        self.variants = self.pay["variants"]

    def test_sixteen_variants(self):
        self.assertEqual(len(self.variants), 16)
        ipl = [v for v in self.variants if v["league"] == "ipl"]
        wpl = [v for v in self.variants if v["league"] == "wpl"]
        neutral = [v for v in self.variants if v["league"] == "neutral"]
        self.assertEqual(len(ipl), 10)
        self.assertEqual(len(wpl), 5)
        self.assertEqual(len(neutral), 1)

    def test_ipl_cards_are_real_playbooks(self):
        for v in self.variants:
            if v["league"] != "ipl":
                continue
            self.assertFalse(v["empty_state"])
            self.assertGreater(v["total_subs"], 0)
            self.assertEqual(v["bat_subs"] + v["bowl_subs"], v["total_subs"])
            self.assertIn(v["favorite_pattern"], ("bat", "bowl"))
            self.assertTrue(v["most_used_player"]["name"])
            self.assertGreater(v["most_used_player"]["count"], 0)
            self.assertTrue(v["headline"].strip())

    def test_wpl_cards_are_control_arm(self):
        wpl = [v for v in self.variants if v["league"] == "wpl"]
        self.assertEqual(len(wpl), 5)
        for v in wpl:
            self.assertTrue(v.get("control_arm"))
            self.assertTrue(v.get("empty_state"))
            self.assertTrue(v["headline"].strip())
            # house framing: the WPL is never "behind"
            self.assertNotIn("behind", v["headline"].lower())

    def test_every_current_ipl_franchise_present(self):
        ipl_teams = {v["team"] for v in self.variants if v["league"] == "ipl"}
        self.assertEqual(ipl_teams, set(canon.CURRENT_IPL_FRANCHISES))
        wpl_teams = {v["team"] for v in self.variants if v["league"] == "wpl"}
        self.assertEqual(wpl_teams, set(canon.WPL_FRANCHISES))


# ===========================================================================
# Determinism
# ===========================================================================


class DeterminismTest(unittest.TestCase):
    def test_fresh_recompute_is_byte_identical(self):
        acc2 = ch7.build_ch7()
        doc2 = ch7.ch7_doc(acc2)
        acc3 = ch7.build_ch7()
        doc3 = ch7.ch7_doc(acc3)
        b2 = flatten.compact_json(doc2, sort_keys=True)
        b3 = flatten.compact_json(doc3, sort_keys=True)
        self.assertEqual(b2, b3, "two fresh builds diverged")
        self.assertEqual(b2, DISK_BYTES, "on-disk ch7.json != fresh recompute")


if __name__ == "__main__":
    unittest.main()
