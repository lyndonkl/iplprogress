"""R4a — Chapter 6 "Two Dialects" (scenes/ch6.json).

The Season Constellation Map is a precomputed embedding, so these tests protect
both the numbers and the geometry:

  * LINEAR ALGEBRA — the pure-Python Jacobi eigensolver reconstructs a known
    symmetric matrix with orthonormal eigenvectors; classical MDS recovers a
    known 2D point cloud's inter-point distances; orthogonal Procrustes
    (reflection + scale allowed) drives a rotated/reflected/scaled/translated
    copy back onto its target to ~zero disparity.
  * CONSTELLATION FIDELITY — the emitted all-phase star layout reconstructs the
    independently recomputed 23x23 Jensen-Shannon distance matrix within a
    stress tolerance; every per-phase layout's Procrustes disparity to the
    master is strictly below its raw (unaligned) disparity; the stars sit in a
    stable [-1, 1] box; the 7 outcome categories partition every delivery.
  * THE HEADLINE GEOMETRY — every WPL season-star's nearest IPL neighbour by
    all-phase outcome mix is IPL 2008, while its run-rate twin is a mid-era IPL
    season (WPL 2026 -> mix 2008, rate 2022): beside the path, not on it.
  * VALIDATED NUMBERS — maturity clock (WPL yr4 8.54 == IPL yr15), Run DNA
    (four 46.8 vs 33.9, six 15.5 vs 29.0), Stumping Signature (WPL 5.2-7.9 vs
    IPL 2026 1.4), Photo-Finish (WPL 24.1 vs IPL 17.3/16.0), batting depth
    (WPL 2025 pos-7+ 15.3) — each against an INDEPENDENT recount.
  * PAYOFF — 16 sister-franchise variants (10 IPL + 5 WPL + neutral), the four
    designated sister pairs, seven designed empty states, five shared grounds.
  * DETERMINISM — a fresh recompute equals itself and the on-disk bytes.
"""

from __future__ import annotations

import json
import math
import sys
import unittest
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import canon
import flatten
import ch6

DOC = None
ACC = None
DISK_BYTES = None


def setUpModule():
    global DOC, ACC, DISK_BYTES
    out = canon.OUT_ROOT
    path = out / "scenes" / "ch6.json"
    if not path.exists():
        ch6.main()
    DISK_BYTES = path.read_bytes()
    ACC = ch6.build_ch6()
    DOC = ch6.ch6_doc(ACC)


# ===========================================================================
# Independent recount (its own corpus pass, its own category logic)
# ===========================================================================

RECOUNT = None


def _recount():
    """A fully independent pass: category counts per group, per-season run/ball
    tallies, dismissal-kind tallies, and closeness records — none of it sharing
    ch6.build_ch6's accumulators."""
    groups = [("ipl", s) for s in canon.IPL_SEASONS] + [
        ("wpl", s) for s in canon.WPL_SEASONS
    ]
    gi_of = {k: i for i, k in enumerate(groups)}
    catcount = [[0] * 7 for _ in range(23)]  # all-phase only, for JS check
    runs_total = defaultdict(int)
    legal = defaultdict(int)
    four = defaultdict(int)
    six = defaultdict(int)
    one = defaultdict(int)
    two = defaultdict(int)
    three = defaultdict(int)
    dismiss = defaultdict(int)
    stump = defaultdict(int)
    pos_runs = defaultdict(int)
    close = []
    for _d, _m, league, p in flatten.sorted_match_files():
        with open(p) as fh:
            match = json.load(fh)
        info = match["info"]
        season = canon.canon_season(info)
        gi = gi_of[(league, season)]
        key = (league, season)
        outcome = info.get("outcome", {})
        by = outcome.get("by", {})
        innings_no = 0
        chase_win_balls = None
        for innings in match.get("innings", []):
            if canon.is_super_over(innings):
                continue
            innings_no += 1
            pos = {}
            nextpos = 1
            crun = 0
            cum = 0
            won = None
            target = (
                (innings.get("target") or {}).get("runs") if innings_no == 2 else None
            )
            for over in innings["overs"]:
                for dl in over["deliveries"]:
                    ex = dl.get("extras", {})
                    wide = "wides" in ex
                    nb = "noballs" in ex
                    tot = dl["runs"]["total"]
                    rb = dl["runs"]["batter"]
                    st = dl["batter"]
                    ns = dl["non_striker"]
                    if st not in pos:
                        pos[st] = nextpos
                        nextpos += 1
                    if ns not in pos:
                        pos[ns] = nextpos
                        nextpos += 1
                    # independent 7-way category (wicket precedence)
                    if dl.get("wickets"):
                        c = 5
                    elif rb == 0 and tot == 0:
                        c = 0
                    elif rb == 1:
                        c = 1
                    elif rb in (2, 3):
                        c = 2
                    elif rb == 4:
                        c = 3
                    elif rb == 6:
                        c = 4
                    else:
                        c = 6
                    catcount[gi][c] += 1
                    runs_total[key] += tot
                    pos_runs[(league, season, pos[st])] += rb
                    if not wide and not nb:
                        legal[key] += 1
                        cum += 1
                    if rb == 4:
                        four[key] += 4
                    elif rb == 6:
                        six[key] += 6
                    elif rb == 1:
                        one[key] += 1
                    elif rb == 2:
                        two[key] += 2
                    elif rb == 3:
                        three[key] += 3
                    crun += tot
                    if target is not None and crun >= target and won is None:
                        won = cum
                    for w in dl.get("wickets", []):
                        if w["kind"] in ("retired hurt", "retired out"):
                            continue
                        dismiss[key] += 1
                        if w["kind"] == "stumped":
                            stump[key] += 1
            if innings_no == 2:
                chase_win_balls = won
        close.append(
            {
                "league": league,
                "season": season,
                "dl": canon.is_dl(info),
                "result": outcome.get("result"),
                "by": dict(by),
                "chase_win_balls": chase_win_balls,
            }
        )
    return {
        "groups": groups,
        "gi_of": gi_of,
        "catcount": catcount,
        "runs_total": runs_total,
        "legal": legal,
        "four": four,
        "six": six,
        "one": one,
        "two": two,
        "three": three,
        "dismiss": dismiss,
        "stump": stump,
        "pos_runs": pos_runs,
        "close": close,
    }


def recount():
    global RECOUNT
    if RECOUNT is None:
        RECOUNT = _recount()
    return RECOUNT


# ===========================================================================
# Pure-Python linear algebra
# ===========================================================================


class LinAlgTest(unittest.TestCase):
    def test_jacobi_reconstructs_symmetric(self):
        a = [
            [4.0, 1.0, 0.5, 0.2],
            [1.0, 3.0, 0.3, 0.1],
            [0.5, 0.3, 2.0, 0.4],
            [0.2, 0.1, 0.4, 1.0],
        ]
        vals, vecs = ch6.jacobi_eigen(a)
        n = len(a)
        # V orthonormal
        for i in range(n):
            for j in range(n):
                dot = sum(vecs[k][i] * vecs[k][j] for k in range(n))
                self.assertAlmostEqual(dot, 1.0 if i == j else 0.0, places=9)
        # A == V diag(vals) V^T
        for i in range(n):
            for j in range(n):
                recon = sum(vals[k] * vecs[i][k] * vecs[j][k] for k in range(n))
                self.assertAlmostEqual(recon, a[i][j], places=9)

    def test_mds_recovers_known_distances(self):
        pts = [[0.0, 0.0], [1.0, 0.0], [0.0, 2.0], [3.0, 1.0], [-1.0, -1.0]]
        n = len(pts)
        d = [
            [math.hypot(pts[i][0] - pts[j][0], pts[i][1] - pts[j][1]) for j in range(n)]
            for i in range(n)
        ]
        coords, _ev = ch6.classical_mds_2d(d)
        for i in range(n):
            for j in range(i + 1, n):
                dhat = math.hypot(
                    coords[i][0] - coords[j][0], coords[i][1] - coords[j][1]
                )
                self.assertAlmostEqual(dhat, d[i][j], places=6)

    def test_procrustes_recovers_rigid_transform(self):
        src = [[0.0, 0.0], [1.0, 0.0], [0.0, 1.0], [2.0, 3.0], [-1.0, 2.0]]
        # rotate 40deg, reflect x, scale 1.7, translate — Procrustes must undo it
        th = math.radians(40.0)
        c, s = math.cos(th), math.sin(th)
        tgt = []
        for x, y in src:
            rx = 1.7 * (c * (-x) - s * y) + 5.0
            ry = 1.7 * (s * (-x) + c * y) - 2.0
            tgt.append([rx, ry])
        aligned, disparity, disparity_raw = ch6.procrustes_align(src, tgt)
        self.assertLess(disparity, 1e-12)
        self.assertLess(disparity, disparity_raw)
        for a, t in zip(aligned, tgt):
            self.assertAlmostEqual(a[0], t[0], places=6)
            self.assertAlmostEqual(a[1], t[1], places=6)

    def test_js_distance_is_metric_like(self):
        p = [0.5, 0.5, 0, 0, 0, 0, 0]
        q = [0.0, 0.0, 0, 0, 0.5, 0.5, 0]
        self.assertAlmostEqual(ch6.js_distance(p, p), 0.0, places=12)
        self.assertGreater(ch6.js_distance(p, q), 0.0)
        # base-2 JS divergence is bounded by 1
        self.assertLessEqual(ch6.js_divergence(p, q), 1.0 + 1e-9)


# ===========================================================================
# Constellation fidelity + the headline geometry
# ===========================================================================


class ConstellationTest(unittest.TestCase):
    def setUp(self):
        self.con = DOC["constellation"]
        self.rc = recount()

    def test_distributions_match_independent_recount(self):
        # emitted all-phase distributions == independently recounted, normalised
        for gi in range(23):
            tot = sum(self.rc["catcount"][gi])
            for c in range(7):
                self.assertAlmostEqual(
                    self.con["distributions"]["all"][gi][c],
                    self.rc["catcount"][gi][c] / tot,
                    places=5,
                )

    def test_categories_partition_every_delivery(self):
        # the 7 buckets partition every delivery: each group's independently
        # counted all-phase deliveries equal ch6's own all-phase count, and the
        # emitted distribution sums to 1
        self.assertEqual(len(self.con["categories"]), 7)
        for gi in range(23):
            self.assertEqual(sum(self.rc["catcount"][gi]), sum(ACC["dist"][gi][0]))
            self.assertAlmostEqual(sum(self.con["distributions"]["all"][gi]), 1.0, places=4)

    def test_mds_reconstructs_distance_matrix(self):
        # rebuild the JS distance matrix independently, compare to the emitted
        # star layout's pairwise euclidean distances (Kruskal stress)
        norm = [
            [v / sum(self.rc["catcount"][gi]) for v in self.rc["catcount"][gi]]
            for gi in range(23)
        ]
        d = [[0.0] * 23 for _ in range(23)]
        for i in range(23):
            for j in range(i + 1, 23):
                d[i][j] = d[j][i] = ch6.js_distance(norm[i], norm[j])
        stars = self.con["stars"]["all"]
        num = den = 0.0
        for i in range(23):
            for j in range(i + 1, 23):
                dhat = math.hypot(stars[i][0] - stars[j][0], stars[i][1] - stars[j][1])
                # stars are normalised by a global scale; compare shapes via a
                # single best-fit scale factor
                num += dhat
                den += d[i][j]
        scale = num / den
        stress_num = stress_den = 0.0
        for i in range(23):
            for j in range(i + 1, 23):
                dhat = math.hypot(stars[i][0] - stars[j][0], stars[i][1] - stars[j][1])
                stress_num += (dhat - scale * d[i][j]) ** 2
                stress_den += (scale * d[i][j]) ** 2
        stress = math.sqrt(stress_num / stress_den)
        # the emitted validation stress agrees with the module's own report
        self.assertLess(self.con["validation"]["mds_stress"]["all"], 0.15)
        self.assertLess(stress, 0.16)

    def test_procrustes_reduces_disparity_every_phase(self):
        v = self.con["validation"]
        for phase in ("powerplay", "middle", "death"):
            self.assertLess(
                v["procrustes_disparity"][phase],
                v["procrustes_disparity_raw"][phase],
                f"{phase} alignment did not reduce disparity",
            )

    def test_stars_in_stable_box(self):
        for view, rows in self.con["stars"].items():
            self.assertEqual(len(rows), 23)
            for x, y in rows:
                self.assertLessEqual(abs(x), 1.0 + 1e-9)
                self.assertLessEqual(abs(y), 1.0 + 1e-9)

    def test_every_wpl_star_nearest_ipl_2008(self):
        # the house framing, recomputed independently from the recount
        norm = {}
        for gi, (lg, ss) in enumerate(self.rc["groups"]):
            tot = sum(self.rc["catcount"][gi])
            norm[gi] = [v / tot for v in self.rc["catcount"][gi]]
        ipl_gis = [i for i, (lg, _s) in enumerate(self.rc["groups"]) if lg == "ipl"]
        wpl_gis = [i for i, (lg, _s) in enumerate(self.rc["groups"]) if lg == "wpl"]
        for wg in wpl_gis:
            best = min(ipl_gis, key=lambda ig: ch6.js_distance(norm[wg], norm[ig]))
            self.assertEqual(
                self.rc["groups"][best][1],
                2008,
                f"WPL {self.rc['groups'][wg][1]} nearest IPL is not 2008",
            )
        self.assertTrue(self.con["validation"]["all_wpl_nearest_is_2008"])

    def test_wpl_threads_all_phase_are_2008(self):
        for row in self.con["wpl_threads"]["all"]:
            self.assertEqual(row["nearest_ipl_season"], 2008)

    def test_two_truths_2026_mix_2008_rate_2022(self):
        row = next(t for t in self.con["two_truths"] if t["wpl_season"] == 2026)
        self.assertEqual(row["outcome_mix_twin"]["ipl_season"], 2008)
        self.assertEqual(row["run_rate_twin"]["ipl_season"], 2022)
        self.assertEqual(row["wpl_rr"], 8.54)
        self.assertEqual(row["run_rate_twin"]["ipl_rr"], 8.54)

    def test_ipl_worm_is_chronological(self):
        worm = self.con["ipl_worm"]
        seasons = [self.con["groups"][gi]["season"] for gi in worm]
        self.assertEqual(seasons, list(canon.IPL_SEASONS))


# ===========================================================================
# Validated numbers (independent recount)
# ===========================================================================


class NumbersTest(unittest.TestCase):
    def setUp(self):
        self.rc = recount()

    def _rr(self, lg, s):
        return round(6.0 * self.rc["runs_total"][(lg, s)] / self.rc["legal"][(lg, s)], 2)

    def test_maturity_clock(self):
        m = DOC["maturity_clock"]
        self.assertEqual(m["ipl"]["rr"], [self._rr("ipl", s) for s in canon.IPL_SEASONS])
        self.assertEqual(m["wpl"]["rr"], [self._rr("wpl", s) for s in canon.WPL_SEASONS])
        self.assertEqual(m["headline"]["wpl_year4_rr"], 8.54)
        self.assertEqual(m["headline"]["ipl_year15_rr"], 8.54)
        self.assertTrue(m["headline"]["equal"])

    def test_run_dna(self):
        def share(keys, field):
            tot = sum(self.rc["runs_total"][k] for k in keys)
            part = sum(self.rc[field][k] for k in keys)
            return round(100.0 * part / tot, 1)

        wpl = [("wpl", s) for s in range(2023, 2027)]
        ipl = [("ipl", s) for s in range(2023, 2027)]
        h = DOC["run_dna"]["headline"]
        self.assertEqual(h["four_share"]["wpl"], share(wpl, "four"))
        self.assertEqual(h["four_share"]["ipl_modern"], share(ipl, "four"))
        self.assertEqual(h["four_share"]["wpl"], 46.8)
        self.assertEqual(h["four_share"]["ipl_modern"], 33.9)
        self.assertEqual(h["six_share"]["wpl"], 15.5)
        self.assertEqual(h["six_share"]["ipl_modern"], 29.0)

    def test_stumping(self):
        wpl_rows = DOC["stumping"]["wpl"]
        for row in wpl_rows:
            key = ("wpl", row["season"])
            exp = round(100.0 * self.rc["stump"][key] / self.rc["dismiss"][key], 1)
            self.assertEqual(row["stumped_pct"], exp)
        vals = [r["stumped_pct"] for r in wpl_rows]
        self.assertEqual([min(vals), max(vals)], [5.2, 7.9])
        ipl_2026 = next(r for r in DOC["stumping"]["ipl"] if r["season"] == 2026)
        self.assertEqual(ipl_2026["stumped_pct"], 1.4)

    def test_photo_finish(self):
        def verdict(m):
            if m["dl"] or m["result"] in ("no result", "tie"):
                return None
            by = m["by"]
            if "runs" in by:
                return by["runs"] <= 5
            if "wickets" in by:
                wb = m["chase_win_balls"]
                return None if wb is None else (120 - wb) <= 3
            return None

        def rate(keys):
            ks = set(keys)
            dec = [
                m
                for m in self.rc["close"]
                if (m["league"], m["season"]) in ks and verdict(m) is not None
            ]
            pf = [m for m in dec if verdict(m)]
            return round(100.0 * len(pf) / len(dec), 1)

        wpl = rate([("wpl", s) for s in canon.WPL_SEASONS])
        early = rate([("ipl", s) for s in (2008, 2009, 2010)])
        modern = rate([("ipl", s) for s in range(2023, 2027)])
        h = DOC["photo_finish"]["headline"]
        self.assertEqual(h["wpl"], wpl)
        self.assertEqual(h["ipl_early"], early)
        self.assertEqual(h["ipl_modern"], modern)
        self.assertEqual(h["wpl"], 24.1)
        self.assertEqual(h["ipl_early"], 17.3)
        self.assertEqual(h["ipl_modern"], 16.0)

    def test_batting_depth(self):
        def depth(keys):
            tot = sum(
                r for (lg, ss, _p), r in self.rc["pos_runs"].items() if (lg, ss) in keys
            )
            tail = sum(
                r
                for (lg, ss, p), r in self.rc["pos_runs"].items()
                if (lg, ss) in keys and p >= 7
            )
            return round(100.0 * tail / tot, 1)

        self.assertEqual(
            DOC["batting_ladder"]["depth"]["headline"]["wpl_2025_pos7plus"],
            depth({("wpl", 2025)}),
        )
        self.assertEqual(
            DOC["batting_ladder"]["depth"]["headline"]["wpl_2025_pos7plus"], 15.3
        )

    def test_batting_ladder_rows_sum_to_100(self):
        for band, rungs in DOC["batting_ladder"]["bands"].items():
            self.assertEqual(len(rungs), 11)
            self.assertAlmostEqual(sum(rungs), 100.0, places=0)


# ===========================================================================
# Sister-franchise payoff
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

    def test_four_sister_pairs(self):
        self.assertEqual(len(self.pay["sister_pairs"]), 4)
        by_ipl = {p["ipl"]: p for p in self.pay["sister_pairs"]}
        self.assertEqual(by_ipl["Gujarat Titans"]["wpl"], "Gujarat Giants")
        self.assertEqual(by_ipl["Mumbai Indians"]["wpl"], "Mumbai Indians")
        # every sister pair id resolves through canon
        for p in self.pay["sister_pairs"]:
            self.assertEqual(canon.team_id("ipl", p["ipl"]), p["ipl_id"])
            self.assertEqual(canon.team_id("wpl", p["wpl"]), p["wpl_id"])

    def test_seven_designed_empty_states(self):
        empties = [v for v in self.variants if v.get("empty_state")]
        # six sisterless IPL franchises + UP Warriorz
        self.assertEqual(len(empties), 7)
        wpl_empty = [v for v in empties if v["league"] == "wpl"]
        self.assertEqual(len(wpl_empty), 1)
        self.assertEqual(wpl_empty[0]["team"], "UP Warriorz")

    def test_wpl_variants_carry_nearest_style(self):
        for v in self.variants:
            if v["league"] == "wpl":
                star = v["nearest_ipl_star_by_style"]
                self.assertIn("ipl_season", star)
                self.assertIn(star["ipl_season"], set(canon.IPL_SEASONS))

    def test_five_shared_grounds(self):
        self.assertEqual(len(self.pay["shared_grounds"]), 5)
        for g in self.pay["shared_grounds"]:
            self.assertGreater(g["ipl_matches"], 0)
            self.assertGreater(g["wpl_matches"], 0)


# ===========================================================================
# Determinism
# ===========================================================================


class DeterminismTest(unittest.TestCase):
    def test_fresh_recompute_is_byte_identical(self):
        acc2 = ch6.build_ch6()
        doc2 = ch6.ch6_doc(acc2)
        b1 = flatten.compact_json(DOC, sort_keys=True)
        b2 = flatten.compact_json(doc2, sort_keys=True)
        self.assertEqual(b1, b2, "two fresh builds diverged")
        self.assertEqual(b2, DISK_BYTES, "on-disk ch6.json != fresh recompute")


if __name__ == "__main__":
    unittest.main()
