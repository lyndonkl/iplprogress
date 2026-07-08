"""R5b — Chapter 9 "The Living League" (scenes/ch9.json + pairing.u16).

The single point: institutions churn, the human fabric persists. Two heroes (the
duel web of decade-long rivalries, the auction heartbeat of five synchronized
mega-auction flatlines) and one supporting beat (the loyalty spectrum). Every
on-screen number is asserted against the EMITTED scenes/ch9.json (loaded from disk,
the artifact that ships) and the per-point pairing.u16 buffer, and pinned to the
digest's verified numbers. Where a strict recount differs from an older blueprint
teaser the recount ships (ARTIFACT WINS); the three honest deltas ride straight and
are asserted as deltas, never fudged toward the teaser:

  * DUELS >= 8 SEASONS: 232 by strict recount (distinct seasons the pair faced a
    ball), NOT the teaser's 235; the footnote ships 232.
  * LOYALTY: one-club share fell from about 27 in 100 (2012) to about 12 (recent),
    NOT the teaser's 28 -> 15; drawn on a 0-based axis.
  * MEGA-AUCTION TROUGH: the five mega years average 0.186, NOT the teaser's 0.185;
    non-mega years rest at 0.461.

Load-bearing exacts pinned: 277 nodes, 1,691 duels, Kohli-Jadeja 160/179/3/14 span
[2009,2025] running bowler-blue, Finch 9 shirts, 16 payoff variants (10 IPL + 5 WPL +
1 neutral), balls-in-duels 79,378 / dust 236,821. VOICE: zero em dashes anywhere and
the WPL is NEVER "behind". DETERMINISM: a fresh build equals itself and the on-disk
bytes (doc and pairing both).
"""

from __future__ import annotations

import json
import sys
import unittest
from array import array
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import canon
import flatten
import ch9

TESTS_DIR = Path(__file__).resolve().parent

DOC = None
DISK_BYTES = None
PAIRING_BYTES = None


def setUpModule():
    global DOC, DISK_BYTES, PAIRING_BYTES
    scene_path = canon.OUT_ROOT / "scenes" / "ch9.json"
    pairing_path = canon.OUT_ROOT / "pairing.u16"
    if not scene_path.exists() or not pairing_path.exists():
        ch9.main()
    DISK_BYTES = scene_path.read_bytes()
    DOC = json.loads(DISK_BYTES)  # the emitted artifact, exactly as it ships
    PAIRING_BYTES = pairing_path.read_bytes()


def read_pairing(raw: bytes):
    """Decode pairing.u16 to native ints (the build_pairing byteorder convention:
    the on-disk buffer is little-endian, byteswapped back on a big-endian host)."""
    a = array("H")
    a.frombytes(raw)
    if sys.byteorder == "big":
        a.byteswap()
    return a


# ===========================================================================
# (1) The duel web — 277 nodes, 1,691 duels, the Kohli-Jadeja hero, positions
#     and dominance color both bounded to [-1, 1]
# ===========================================================================


class DuelWebTest(unittest.TestCase):
    def setUp(self):
        self.dw = DOC["duel_web"]
        self.meta = self.dw["meta"]
        self.nodes = self.dw["nodes"]
        self.duels = self.dw["duels"]

    def test_277_nodes_1691_duels(self):
        self.assertEqual(self.meta["n_nodes"], 277)
        self.assertEqual(self.meta["n_duels"], 1691)
        self.assertEqual(len(self.nodes), 277)
        self.assertEqual(len(self.duels), 1691)
        # 244 men + 33 women, two disjoint components (the leagues share no players)
        self.assertEqual(self.meta["n_men"], 244)
        self.assertEqual(self.meta["n_women"], 33)
        self.assertEqual(self.meta["n_men"] + self.meta["n_women"],
                         self.meta["n_nodes"])
        self.assertEqual(self.meta["components"], [244, 33])
        self.assertEqual(self.meta["duel_min_balls"], 30)

    def test_duel_zero_is_kohli_jadeja(self):
        d0 = self.duels[0]
        self.assertEqual(d0["id"], 0)
        self.assertEqual(d0["bat"], "V Kohli")
        self.assertEqual(d0["bowl"], "RA Jadeja")
        self.assertEqual(d0["balls"], 160)
        self.assertEqual(d0["runs"], 179)
        self.assertEqual(d0["dis"], 3)
        self.assertEqual(d0["seasons"], 14)
        self.assertEqual(d0["span"], [2009, 2025])
        # Jadeja contained him (3 dismissals), so the strand runs bowler-blue: color < 0
        self.assertLess(d0["color"], 0.0, "Kohli-Jadeja must be bowler-blue")
        self.assertTrue(-1.0 <= d0["color"] <= 1.0)

    def test_duels_sorted_by_balls_desc_ids_stable(self):
        balls = [d["balls"] for d in self.duels]
        self.assertEqual(balls, sorted(balls, reverse=True))
        self.assertEqual([d["id"] for d in self.duels], list(range(1691)))
        # every duel meets the >=30-ball threshold
        self.assertGreaterEqual(min(balls), 30)

    def test_node_positions_in_unit_box(self):
        for n in self.nodes:
            self.assertTrue(-1.0 <= n["x"] <= 1.0, f"{n['name']} x={n['x']}")
            self.assertTrue(-1.0 <= n["y"] <= 1.0, f"{n['name']} y={n['y']}")
            self.assertIn(n["league"], ("ipl", "wpl"))
        # node index references inside duels are valid
        for d in self.duels[:200]:
            self.assertTrue(0 <= d["a"] < 277)
            self.assertTrue(0 <= d["b"] < 277)

    def test_dominance_color_bounded(self):
        for d in self.duels:
            self.assertTrue(-1.0 <= d["color"] <= 1.0, f"duel {d['id']} color {d['color']}")
        # the channel actually uses both poles (batter-red and bowler-blue exist)
        cols = [d["color"] for d in self.duels]
        self.assertLess(min(cols), 0.0)
        self.assertGreater(max(cols), 0.0)

    def test_dominance_color_matches_the_emitted_formula(self):
        # color = clamp((dom - center_mu) / half_range, -1, 1), per the emitted meta
        dc = self.meta["dominance_color"]
        mu = dc["center_mu"]
        half = dc["half_range"]
        self.assertGreater(half, 0.0)
        for d in self.duels[:400]:
            expect = max(-1.0, min(1.0, (d["dom"] - mu) / half))
            self.assertAlmostEqual(d["color"], round(expect, 3), places=2,
                                   msg=f"duel {d['id']}")


# ===========================================================================
# (2) The long duels — 232 ran eight seasons or longer (the honest delta, NOT 235)
# ===========================================================================


class LongDuelsTest(unittest.TestCase):
    def setUp(self):
        self.duels = DOC["duel_web"]["duels"]

    def test_232_duels_ran_eight_seasons_or_longer(self):
        n8 = sum(1 for d in self.duels if d["seasons"] >= 8)
        self.assertEqual(n8, 232, "strict recount of 8+-season duels")
        # the honest delta is asserted AS a delta: it is 232, never the teaser's 235
        self.assertNotEqual(n8, 235)
        # sanity: it is close to 232, not wildly off (~1.3% below the old teaser)
        self.assertTrue(228 <= n8 <= 236)

    def test_footnote_ships_232_not_235_as_the_count(self):
        text = DOC["footnotes"]["ch9-duel"]["text"]
        self.assertIn("232 duels have run eight seasons or longer", text)
        # the teaser number may be mentioned honestly ("rather than ... 235"), but
        # 232 is the shipped count and leads the claim
        self.assertLess(text.index("232 duels"), text.find("235"))


# ===========================================================================
# (3) The auction heartbeat — five synchronized mega-auction flatlines
# ===========================================================================


class HeartbeatTest(unittest.TestCase):
    def setUp(self):
        self.hb = DOC["heartbeat"]["ipl"]
        self.series = self.hb["series"]

    def test_mega_years_are_the_five_lowest(self):
        self.assertEqual(set(self.hb["mega_years"]),
                         {2011, 2014, 2018, 2022, 2025})
        by_mean = sorted(self.series, key=lambda s: s["mean"])
        five_lowest = {s["season"] for s in by_mean[:5]}
        self.assertEqual(five_lowest, set(self.hb["mega_years"]))
        # a clean gap: the 6th-lowest year is far above the mega troughs
        sixth = by_mean[5]
        self.assertGreater(sixth["mean"], 0.30)
        self.assertEqual(self.hb["sixth_lowest"]["season"], sixth["season"])

    def test_mega_mean_and_nonmega_mean(self):
        self.assertEqual(self.hb["mega_mean"], 0.186)
        self.assertEqual(self.hb["nonmega_mean"], 0.461)
        # independent recount from the emitted per-season series (ARTIFACT WINS)
        mega = [s["mean"] for s in self.series if s["season"] in self.hb["mega_years"]]
        non = [s["mean"] for s in self.series if s["season"] not in self.hb["mega_years"]]
        self.assertEqual(len(mega), 5)
        self.assertEqual(round(sum(mega) / len(mega), 3), 0.186)
        self.assertEqual(round(sum(non) / len(non), 3), 0.461)
        # the honest delta: 0.186, never the teaser's 0.185
        self.assertNotEqual(self.hb["mega_mean"], 0.185)
        # the resting pulse sits well above the troughs
        self.assertGreater(self.hb["nonmega_mean"], self.hb["mega_mean"] * 2)

    def test_full_ipl_ladder_is_eighteen_seasons(self):
        seasons = [s["season"] for s in self.series]
        self.assertEqual(seasons, sorted(seasons))
        self.assertEqual(seasons[0], 2009)
        self.assertEqual(seasons[-1], 2026)
        for s in self.series:
            self.assertTrue(0.0 <= s["lo"] <= s["mean"] <= s["hi"] <= 1.0)


# ===========================================================================
# (4) The loyalty spectrum — one-club players roughly halved; Finch wore 9 shirts
# ===========================================================================


class LoyaltyTest(unittest.TestCase):
    def setUp(self):
        self.lo = DOC["loyalty"]

    def test_series_falls_from_about_27_to_about_12(self):
        peak = self.lo["peak"]
        trough = self.lo["trough"]
        # peak ~27 in 100 in 2012 (the recount's 26.9, not the teaser's 28)
        self.assertEqual(peak["season"], 2012)
        self.assertTrue(26.0 <= peak["pct"] <= 28.0, f"peak {peak['pct']}")
        # trough ~12 (the recount's 12.5, not the teaser's 15)
        self.assertTrue(11.0 <= trough["pct"] <= 13.0, f"trough {trough['pct']}")
        # roughly halved
        self.assertLess(trough["pct"], peak["pct"] * 0.6)
        # the span carries the 27 -> 12 story straight
        self.assertEqual(self.lo["span"]["start"]["pct"], peak["pct"])
        self.assertEqual(self.lo["span"]["end"]["pct"], trough["pct"])

    def test_y_axis_is_zero_based(self):
        # the drop must fall to visibly half height, so the axis starts at 0
        self.assertEqual(self.lo["y_domain"][0], 0.0)
        self.assertGreaterEqual(self.lo["y_domain"][1], self.lo["peak"]["pct"])

    def test_max_shirts_is_finch_nine(self):
        ms = self.lo["max_shirts"]
        self.assertEqual(ms["name"], "AJ Finch")
        self.assertEqual(ms["n"], 9)
        self.assertEqual(len(ms["shorts"]), 9)
        self.assertEqual(len(set(ms["shorts"])), 9)

    def test_series_is_a_real_per_season_curve(self):
        seasons = [p["season"] for p in self.lo["series"]]
        self.assertEqual(seasons, sorted(seasons))
        self.assertGreaterEqual(len(seasons), 10)
        for p in self.lo["series"]:
            self.assertGreaterEqual(p["one_club"], 0)
            self.assertGreater(p["veterans"], 0)


# ===========================================================================
# (5) The payoff — 16 variants (10 IPL + 5 WPL + 1 neutral), >=1 bespoke WPL card
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
            self.assertTrue(v["rivalry"]["balls"] >= 30, v.get("short"))
            self.assertTrue(v["rivalry"]["bat"].strip())
            self.assertTrue(v["rivalry"]["bowl"].strip())

    def test_ipl_cards_carry_reset_and_loyalist(self):
        for v in self.variants:
            if v["league"] != "ipl":
                continue
            self.assertIn(v["reset"]["year"], DOC["heartbeat"]["ipl"]["mega_years"])
            self.assertGreaterEqual(v["reset"]["out"], 0)
            self.assertGreaterEqual(v["reset"]["in"], 0)
            self.assertTrue(v["loyalist"]["name"].strip())
            self.assertGreater(v["loyalist"]["seasons"], 0)

    def test_at_least_one_bespoke_wpl_card_never_a_deficit(self):
        wpl = [v for v in self.variants if v["league"] == "wpl"]
        self.assertEqual(len(wpl), 5)
        bespoke = [v for v in wpl if v.get("bespoke")]
        self.assertGreaterEqual(len(bespoke), 1)
        for v in wpl:
            # the forming-fast beat made personal, never a deficit card
            self.assertTrue(v.get("forming_fast"))
            self.assertGreater(v.get("duel_count", 0), 0)
            self.assertNotIn("behind", v["headline"].lower())
            for row in ("row1", "row2", "row3"):
                self.assertNotIn("behind", v[row].lower())

    def test_neutral_card_is_the_live_league_report(self):
        neu = next(v for v in self.variants if v["league"] == "neutral")
        self.assertEqual(neu["rivalry"]["bat"], "V Kohli")
        self.assertEqual(neu["rivalry"]["bowl"], "RA Jadeja")
        self.assertEqual(set(neu["mega_years"]),
                         set(DOC["heartbeat"]["ipl"]["mega_years"]))
        self.assertEqual(neu["loyalty_start"], DOC["loyalty"]["peak"]["pct"])
        self.assertEqual(neu["loyalty_end"], DOC["loyalty"]["trough"]["pct"])


# ===========================================================================
# (6) The pairing buffer — one duel id (or the 0xFFFF dust sentinel) per point
# ===========================================================================


class PairingTest(unittest.TestCase):
    def setUp(self):
        self.split = DOC["duel_web"]["meta"]["balls_split"]
        self.pairing = read_pairing(PAIRING_BYTES)

    def test_length_equals_total_points(self):
        self.assertEqual(len(self.pairing), self.split["total_points"])
        self.assertEqual(len(self.pairing), 316199)
        # two bytes per point
        self.assertEqual(len(PAIRING_BYTES), 2 * self.split["total_points"])

    def test_values_are_valid_duel_ids_or_the_dust_sentinel(self):
        n_duels = DOC["duel_web"]["meta"]["n_duels"]
        invalid = sum(1 for v in self.pairing
                      if not (v == 0xFFFF or 0 <= v < n_duels))
        self.assertEqual(invalid, 0)
        self.assertEqual(max(v for v in self.pairing if v != 0xFFFF), n_duels - 1)

    def test_in_duel_and_dust_counts_match_the_split(self):
        dust = sum(1 for v in self.pairing if v == 0xFFFF)
        in_duel = len(self.pairing) - dust
        self.assertEqual(in_duel, self.split["in_duel_points"])
        self.assertEqual(dust, self.split["dust_points"])
        # the digest's verified split (about a quarter in rivalries, three quarters dust)
        self.assertEqual(in_duel, 79378)
        self.assertEqual(dust, 236821)
        self.assertEqual(in_duel + dust, 316199)


# ===========================================================================
# (7) Voice — zero em dashes in the on-screen copy, and never "behind" in Ch 9
# ===========================================================================


def _iter_strings(obj):
    if isinstance(obj, dict):
        for v in obj.values():
            yield from _iter_strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _iter_strings(v)
    elif isinstance(obj, str):
        yield obj


class VoiceTest(unittest.TestCase):
    def test_zero_em_dashes_anywhere_in_ch9_copy(self):
        offenders = [s for s in _iter_strings(DOC) if "—" in s]
        self.assertEqual(offenders, [], f"em dash in ch9 copy: {offenders[:3]}")

    def test_never_behind_anywhere_in_ch9_copy(self):
        offenders = [s for s in _iter_strings(DOC) if "behind" in s.lower()]
        self.assertEqual(offenders, [], f"'behind' in ch9 copy: {offenders[:3]}")

    def test_wpl_is_framed_as_a_young_league_forming_fast(self):
        framing = DOC["wpl"]["framing"].lower()
        self.assertTrue("young" in framing or "forming fast" in framing
                        or "taking shape" in framing)
        self.assertNotIn("behind", framing)
        self.assertEqual(DOC["wpl"]["n_players"], 33)


# ===========================================================================
# Determinism — a fresh build equals itself and the on-disk bytes (doc + pairing)
# ===========================================================================


class DeterminismTest(unittest.TestCase):
    def test_fresh_recompute_is_byte_identical(self):
        doc2, pair2 = ch9.build_doc()
        b2 = flatten.compact_json(doc2, sort_keys=True)
        doc3, pair3 = ch9.build_doc()
        b3 = flatten.compact_json(doc3, sort_keys=True)
        self.assertEqual(b2, b3, "two fresh ch9 builds diverged")
        self.assertEqual(b2, DISK_BYTES, "on-disk ch9.json != fresh recompute")
        self.assertEqual(pair2, pair3, "two fresh pairing buffers diverged")
        self.assertEqual(pair2, PAIRING_BYTES, "on-disk pairing.u16 != fresh recompute")


if __name__ == "__main__":
    unittest.main()
