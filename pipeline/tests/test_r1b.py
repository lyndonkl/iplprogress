"""R1b snapshot tests — the minimal sandbox's data contract.

Covers the three new artifacts the tap-a-ball tooltip and its preset depend
on: matches.json (the match table a tapped ball resolves through), the two new
columnar columns (match_index -> matches.json, wicket_kind dict-encoded), and
scenes/sandbox.json (the famous-match preset + facet lists + tooltip roster).

Everything is checked against an independent recount straight from the raw
corpus — the emitted match table is rebuilt a second way, a known ball (the
last delivery of the 2019 IPL Final) is flattened by hand and matched
delivery-for-delivery, and the preset is resolved by identity, never by a
hard-coded index.
"""

from __future__ import annotations

import gzip
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import canon
import flatten
import scenes

EXPECTED_N_POINTS = 316_199
EXPECTED_MATCHES = 1_331  # distinct matches (1,243 IPL + 88 WPL)
EXPECTED_UINT16_CEIL = 1 << 16  # match_index must decode as a Uint16 client-side

# The famous-match preset (owner-resolved): 2019 IPL Final, MI beat CSK by 1.
PRESET_FILE = "1181768.json"
PRESET_TEAMS = {"Mumbai Indians", "Chennai Super Kings"}
PRESET_RESULT = "Mumbai Indians won by 1 run"

ART = None


def setUpModule():
    global ART
    out = canon.OUT_ROOT
    if not (out / "matches.json").exists():
        flatten.main()
    if not (out / "scenes" / "sandbox.json").exists():
        scenes.main()
    columnar = json.loads(gzip.decompress((out / "columnar.json.gz").read_bytes()))
    ART = {
        "matches": json.loads((out / "matches.json").read_text()),
        "columnar": columnar,
        "arrays": columnar["arrays"],
        "dicts": columnar["dicts"],
        "sandbox": json.loads((out / "scenes" / "sandbox.json").read_text()),
    }


def independent_flatten_match(path: Path):
    """Flatten one raw match the tooltip-visible way (super overs excluded)."""
    with open(path) as fh:
        match = json.load(fh)
    rows = []
    innings_no = 0
    for innings in match.get("innings", []):
        if innings.get("super_over"):
            continue
        innings_no += 1
        team = canon.canon_team(innings["team"])
        for over in innings["overs"]:
            for ball_index, dl in enumerate(over["deliveries"]):
                wkts = dl.get("wickets")
                rows.append(
                    {
                        "innings": innings_no,
                        "over": over["over"],
                        "ball_index_in_over": ball_index,
                        "batter": dl["batter"],
                        "bowler": dl["bowler"],
                        "batting_team": team,
                        "runs_batter": dl["runs"]["batter"],
                        "runs_total": dl["runs"]["total"],
                        "wicket": 1 if wkts else 0,
                        "wicket_kind": wkts[0]["kind"] if wkts else "",
                    }
                )
    return match["info"], rows


class TestMatchesTable(unittest.TestCase):
    def test_length_is_distinct_match_count(self):
        self.assertEqual(len(ART["matches"]), EXPECTED_MATCHES)

    def test_inline_table_equals_light_pass(self):
        # flatten builds the table inline in its full ball pass; build_matches
        # rebuilds it from info blocks only — they must be byte-identical.
        self.assertEqual(ART["matches"], flatten.build_matches())

    def test_every_record_is_well_formed(self):
        fields = {"teams", "season", "date", "stage", "venue", "city",
                  "result_text", "league"}
        grounds = set(canon.GROUND_CITY)
        n_ipl = n_wpl = 0
        for m in ART["matches"]:
            self.assertEqual(set(m), fields)
            self.assertEqual(len(m["teams"]), 2)
            for t in m["teams"]:
                self.assertIn(t, canon.KNOWN_TEAMS)
            self.assertNotEqual(m["teams"][0], m["teams"][1])
            self.assertIn(m["season"], range(2008, 2027))
            self.assertEqual(m["date"][:4], str(m["season"]))
            self.assertTrue(m["stage"])
            self.assertIn(m["venue"], grounds)
            self.assertEqual(m["city"], canon.GROUND_CITY[m["venue"]])
            self.assertTrue(m["result_text"])
            self.assertIn(m["league"], ("ipl", "wpl"))
            n_ipl += m["league"] == "ipl"
            n_wpl += m["league"] == "wpl"
        self.assertEqual(n_ipl, 1_243)
        self.assertEqual(n_wpl, 88)

    def test_stage_and_result_vocab(self):
        finals = [m for m in ART["matches"] if m["stage"] == "Final"]
        self.assertEqual(len(finals), 23)  # 19 IPL + 4 WPL seasons
        # every non-playoff game reads "Match N"; result sentences are non-empty
        league_games = [m for m in ART["matches"] if m["stage"].startswith("Match ")]
        self.assertEqual(len(league_games), 1_249)
        ties = [m for m in ART["matches"] if "tied" in m["result_text"]]
        self.assertEqual(len(ties), 17)
        no_results = [m for m in ART["matches"] if m["result_text"] == "No result"]
        self.assertEqual(len(no_results), 9)


class TestMatchIndexColumn(unittest.TestCase):
    def test_length_and_range(self):
        mi = ART["arrays"]["match_index"]
        self.assertEqual(len(mi), EXPECTED_N_POINTS)
        self.assertEqual(min(mi), 0)
        self.assertLess(max(mi), len(ART["matches"]))  # indexes a valid match
        self.assertLess(max(mi), EXPECTED_UINT16_CEIL)  # decodes as Uint16

    def test_monotonic_non_decreasing(self):
        # deliveries of a match are emitted contiguously in season-blocked
        # order, so match_index never goes backwards across the stream.
        mi = ART["arrays"]["match_index"]
        self.assertTrue(all(mi[i] <= mi[i + 1] for i in range(len(mi) - 1)))

    def test_agrees_with_columnar_league_and_season(self):
        a = ART["arrays"]
        matches = ART["matches"]
        for i in range(0, EXPECTED_N_POINTS, 991):  # dense stride
            m = matches[a["match_index"][i]]
            self.assertEqual(m["league"], "wpl" if a["league"][i] == 1 else "ipl", i)
            self.assertEqual(m["season"], a["season"][i], i)
            # the tapped ball's batting_team is one of the match's two teams;
            # the opponent is the other — the tooltip's opponent derivation.
            bt = ART["dicts"]["batting_team"][a["batting_team"][i]]
            self.assertIn(bt, m["teams"], i)
            opp = [t for t in m["teams"] if t != bt]
            self.assertEqual(len(opp), 1, i)


class TestWicketKindColumn(unittest.TestCase):
    def test_dict_and_code_zero_is_empty(self):
        wk = ART["dicts"]["wicket_kind"]
        self.assertEqual(wk[0], "")  # non-wicket balls carry code 0
        self.assertEqual(len(set(wk)), len(wk))  # no dupes
        self.assertLessEqual(
            set(wk),
            {"", "caught", "bowled", "lbw", "run out", "stumped",
             "caught and bowled", "hit wicket", "obstructing the field",
             "retired hurt", "retired out"},
        )

    def test_wicket_bit_iff_kind_present(self):
        a = ART["arrays"]
        wk_col, w_col = a["wicket_kind"], a["wicket"]
        self.assertEqual(len(wk_col), EXPECTED_N_POINTS)
        for i in range(0, EXPECTED_N_POINTS, 337):
            self.assertEqual(bool(wk_col[i]), bool(w_col[i]), i)  # 0 <=> no wicket
        # corpus totals: the wicket column and a non-zero kind agree exactly
        self.assertEqual(sum(1 for v in wk_col if v), sum(w_col))


class TestSpotCheckedKnownBall(unittest.TestCase):
    """The 2019 IPL Final resolved delivery-for-delivery from the raw file."""

    def _preset_index(self):
        hits = [
            i
            for i, m in enumerate(ART["matches"])
            if m["league"] == "ipl"
            and m["season"] == 2019
            and m["stage"] == "Final"
            and set(m["teams"]) == PRESET_TEAMS
        ]
        self.assertEqual(len(hits), 1)
        return hits[0]

    def test_slice_matches_raw_delivery_for_delivery(self):
        idx = self._preset_index()
        info, expected = independent_flatten_match(
            canon.DATA_ROOT / "ipl_json" / PRESET_FILE
        )
        # the raw file really is this match table row
        self.assertEqual(set(info["teams"]), PRESET_TEAMS)
        self.assertEqual(str(info["dates"][0]), ART["matches"][idx]["date"])

        a, dcts = ART["arrays"], ART["dicts"]
        positions = [i for i, v in enumerate(a["match_index"]) if v == idx]
        self.assertEqual(positions, list(range(positions[0], positions[-1] + 1)))
        self.assertEqual(len(positions), len(expected))
        for pos, exp in zip(positions, expected):
            self.assertEqual(
                {
                    "innings": a["innings"][pos],
                    "over": a["over"][pos],
                    "ball_index_in_over": a["ball_index_in_over"][pos],
                    "batter": dcts["batter"][a["batter"][pos]],
                    "bowler": dcts["bowler"][a["bowler"][pos]],
                    "batting_team": dcts["batting_team"][a["batting_team"][pos]],
                    "runs_batter": a["runs_batter"][pos],
                    "runs_total": a["runs_total"][pos],
                    "wicket": a["wicket"][pos],
                    "wicket_kind": dcts["wicket_kind"][a["wicket_kind"][pos]],
                },
                exp,
            )

    def test_last_ball_is_malinga_to_thakur_lbw(self):
        idx = self._preset_index()
        a, dcts = ART["arrays"], ART["dicts"]
        last = max(i for i, v in enumerate(a["match_index"]) if v == idx)
        bt = dcts["batting_team"][a["batting_team"][last]]
        opp = [t for t in ART["matches"][idx]["teams"] if t != bt][0]
        self.assertEqual(bt, "Chennai Super Kings")
        self.assertEqual(opp, "Mumbai Indians")
        self.assertEqual(dcts["bowler"][a["bowler"][last]], "SL Malinga")
        self.assertEqual(dcts["batter"][a["batter"][last]], "SN Thakur")
        self.assertEqual(dcts["wicket_kind"][a["wicket_kind"][last]], "lbw")
        self.assertEqual(ART["matches"][idx]["result_text"], PRESET_RESULT)


class TestSandboxPreset(unittest.TestCase):
    def test_preset_points_at_the_2019_final(self):
        preset = ART["sandbox"]["preset"]
        hits = [
            i
            for i, m in enumerate(ART["matches"])
            if m["league"] == "ipl"
            and m["season"] == 2019
            and m["stage"] == "Final"
            and set(m["teams"]) == PRESET_TEAMS
        ]
        self.assertEqual(len(hits), 1)
        self.assertEqual(preset["match_index"], hits[0])
        m = ART["matches"][preset["match_index"]]
        self.assertEqual(set(m["teams"]), PRESET_TEAMS)
        self.assertEqual(m["result_text"], PRESET_RESULT)  # MI beat CSK by 1
        self.assertEqual(m["stage"], "Final")
        self.assertEqual(m["season"], 2019)
        self.assertTrue(preset["label"])
        self.assertTrue(preset["blurb"])

    def test_facets_are_team_and_season_only(self):
        facets = ART["sandbox"]["facets"]
        self.assertEqual(set(facets), {"team", "season"})  # R1b scope: no more
        self.assertEqual(facets["season"]["ipl"], list(range(2008, 2027)))
        self.assertEqual(facets["season"]["wpl"], list(range(2023, 2027)))
        team_ids = {t["id"] for t in facets["team"]["options"]}
        self.assertEqual(team_ids, {t["id"] for t in canon.TEAMS})

    def test_tooltip_field_roster(self):
        fields = {f["field"] for f in ART["sandbox"]["tooltip"]["fields"]}
        required = {"batter", "bowler", "batting_team", "opponent",
                    "match_label", "over_ball", "runs_off_bat", "runs_total",
                    "wicket", "wicket_kind", "result_text"}
        self.assertLessEqual(required, fields)
        for f in ART["sandbox"]["tooltip"]["fields"]:
            self.assertTrue(f["source"])


if __name__ == "__main__":
    unittest.main()
