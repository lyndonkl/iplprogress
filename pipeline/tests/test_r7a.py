"""Snapshot + honesty tests for R7a's player registry (pipeline/registry.py).

The registry is the join key every player card and the search box resolve through,
so its whole job is correctness and honesty: fold a person's spellings under one pid
(so a spelling change is never a second player), and keep genuine namesakes distinct
(so two people who share a written name are never merged into one).

  count      937 registry pids faced or bowled a ball (NOT the 938 name-based count)
  partition  859 batted, 672 bowled, 594 did both (inclusion-exclusion == 937)
  splits     3 pids carry >1 display spelling (one person, many spellings)
  namesakes  2 written names are shared by 2 different people each (name -> pids)
  merge      the ONLY cross-pid shared spellings are the two namesakes; no other
             spelling bridges two pids, so aliases never merge two people
  determ     registry_doc emits byte-identical bytes across independent builds, and
             those bytes are exactly the shipped players.json
  guard      the naive name-union over-counts (938 > 937): pid-keying is the fix

Recounted on the real corpus 2026-07-09; constants are dated so a corpus drop that
moves them fails loudly rather than drifting.
"""

from __future__ import annotations

import hashlib
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import canon
import flatten
import h2h
import player_tables
import registry

# Corpus-wide snapshot constants (recounted 2026-07-09).
REGISTRY_COUNT = 937
N_BATTED = 859                  # faced >= 1 ball (a raw ball-count, not the role)
N_BOWLED = 672                  # bowled >= 1 legal ball
# role="all" needs a MEANINGFUL contribution in BOTH disciplines (ROLE_MIN_BALLS=300
# each), so a tail-end bat or a part-time over does not make an all-rounder. Recounted
# 2026-07-09: 64 genuine all-rounders (Jadeja/Axar/Narine), not the 594 any-of-both.
N_ROLE_BAT = 396
N_ROLE_BOWL = 477
N_ROLE_ALL = 64
NAIVE_NAME_COUNT = 938          # the old NAME-based over-count (860 bat + 672 bowl, union)

# One person, many spellings: pid -> the sorted spellings folded onto that one card.
ALIAS_SPLITS = {
    "12314277": ["Arshad Khan", "Arshad Khan (2)"],
    "21d4e29b": ["NA Saini", "Navdeep Saini"],
    "d7423da1": ["S Arora", "Salil Arora"],
}
# One written name, two different people: name -> the two distinct pids it resolves to.
NAMESAKES = {
    "Harmeet Singh": ["0bf15e52", "2a72fd4f"],
    "S Rana": ["90edaaa9", "c4c374d9"],
}

# V Kohli spot-check (RCB; 251 balls bowled is below the all-rounder bar, so "bat").
KOHLI_PID = "ba607b88"
KOHLI_TEAMS = ["RCB"]
KOHLI_SEASON_SPAN = (2008, 2026)
KOHLI_BALLS_FACED = 6926
KOHLI_ROLE = "bat"


# ---------------------------------------------------------------------------
# Shared single-build fixtures (parse the corpus as few times as possible)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def doc():
    """The registry document built from one corpus pass."""
    return registry.registry_doc(registry.build())


@pytest.fixture(scope="module")
def by_pid(doc):
    return {p["pid"]: p for p in doc["players"]}


def _naive_name_union():
    """The old name-based universe: distinct batter faced-names + bowler legal-names."""
    bat, bowl = set(), set()
    for _date, _mid, _lg, path in flatten.sorted_match_files():
        match = json.load(open(path))
        for innings in match.get("innings", []):
            if canon.is_super_over(innings):
                continue
            for over in innings["overs"]:
                for dl in over["deliveries"]:
                    ex = dl.get("extras", {})
                    if "wides" not in ex:
                        bat.add(dl["batter"])
                    if "wides" not in ex and "noballs" not in ex:
                        bowl.add(dl["bowler"])
    return bat | bowl


# ---------------------------------------------------------------------------
# Count + role partition
# ---------------------------------------------------------------------------


def test_registry_count(doc):
    assert doc["count"] == REGISTRY_COUNT
    assert len(doc["players"]) == REGISTRY_COUNT


def test_role_partition(doc):
    # raw ball-count sets (who faced / bowled at all) — unchanged by the role rule.
    batted = sum(1 for p in doc["players"] if p["balls_faced"] > 0)
    bowled = sum(1 for p in doc["players"] if p["balls_bowled"] > 0)
    both = sum(1 for p in doc["players"] if p["balls_faced"] > 0 and p["balls_bowled"] > 0)
    assert (batted, bowled) == (N_BATTED, N_BOWLED)
    # inclusion-exclusion on the RAW sets: |bat ∪ bowl| == |bat| + |bowl| - |both|
    assert batted + bowled - both == REGISTRY_COUNT
    # the role LABEL partition (bat / bowl / all) is a threshold on those counts.
    roles = [p["role"] for p in doc["players"]]
    assert (roles.count("bat"), roles.count("bowl"), roles.count("all")) == (
        N_ROLE_BAT, N_ROLE_BOWL, N_ROLE_ALL
    )
    assert N_ROLE_BAT + N_ROLE_BOWL + N_ROLE_ALL == REGISTRY_COUNT


def test_role_matches_ball_counts(doc):
    for p in doc["players"]:
        bf, bb = p["balls_faced"], p["balls_bowled"]
        assert bf > 0 or bb > 0                       # in the universe for a reason
        expected = (
            "all" if (bf >= registry.ROLE_MIN_BALLS and bb >= registry.ROLE_MIN_BALLS)
            else ("bat" if bf >= bb else "bowl")
        )
        assert p["role"] == expected, p


def test_players_sorted_by_pid(doc):
    pids = [p["pid"] for p in doc["players"]]
    assert pids == sorted(pids)


# ---------------------------------------------------------------------------
# Aliases fold one person; namesakes keep two people apart
# ---------------------------------------------------------------------------


def test_alias_splits(doc):
    splits = {p["pid"]: p["aliases"] for p in doc["players"] if len(p["aliases"]) > 1}
    assert splits == ALIAS_SPLITS


def test_canonical_is_a_recorded_alias(doc):
    # the canonical name is always one of the player's own spellings
    for p in doc["players"]:
        assert p["name"] in p["aliases"]


def test_namesakes_are_two_distinct_people(doc, by_pid):
    assert doc["namesakes"] == NAMESAKES
    for name, pids in doc["namesakes"].items():
        assert len(pids) == len(set(pids)) >= 2       # genuinely distinct pids
        for pid in pids:
            assert pid in by_pid                       # each is a real card
            assert name in by_pid[pid]["aliases"]      # and each wrote that name
        # the search index must resolve the shared name to BOTH people, never one
        assert doc["name_to_pids"][name] == pids


def test_name_to_pids_is_function_except_namesakes(doc):
    multi = {n: pids for n, pids in doc["name_to_pids"].items() if len(pids) > 1}
    assert multi == NAMESAKES                          # only namesakes are one-to-many


def test_search_index_covers_universe_exactly(doc):
    covered = {pid for pids in doc["name_to_pids"].values() for pid in pids}
    assert covered == {p["pid"] for p in doc["players"]}
    for name, pids in doc["name_to_pids"].items():
        assert pids == sorted(pids) and len(pids) >= 1


def test_no_spelling_merges_two_people(doc):
    """The ONLY spellings shared across two pids are the two namesakes; every other
    spelling belongs to exactly one pid, so aliases can never merge two players."""
    name_to_pids = defaultdict(set)
    for p in doc["players"]:
        for alias in p["aliases"]:
            name_to_pids[alias].add(p["pid"])
    shared = {n for n, pids in name_to_pids.items() if len(pids) > 1}
    assert shared == set(NAMESAKES)


# ---------------------------------------------------------------------------
# League family + honesty guardrails
# ---------------------------------------------------------------------------


def test_one_league_family_per_pid(doc):
    for p in doc["players"]:
        assert len(p["leagues"]) == 1, p              # no pid spans IPL and WPL
        assert p["leagues"][0] in ("ipl", "wpl")


def test_s_rana_namesake_spans_leagues_as_two_people(doc, by_pid):
    # the two "S Rana"s are a men's IPL and a women's WPL player: distinct pids,
    # each single-league, never a cross-league merge
    ipl_pid, wpl_pid = NAMESAKES["S Rana"]
    assert by_pid[ipl_pid]["leagues"] == ["ipl"]
    assert by_pid[wpl_pid]["leagues"] == ["wpl"]


# ---------------------------------------------------------------------------
# V Kohli spot-check
# ---------------------------------------------------------------------------


def test_kohli_record(doc, by_pid):
    assert doc["name_to_pids"]["V Kohli"] == [KOHLI_PID]
    k = by_pid[KOHLI_PID]
    assert k["teams"] == KOHLI_TEAMS
    assert (k["seasons"][0], k["seasons"][-1]) == KOHLI_SEASON_SPAN
    assert k["balls_faced"] == KOHLI_BALLS_FACED
    assert k["role"] == KOHLI_ROLE                     # part-time bowler -> all-rounder
    assert k["balls_bowled"] > 0


# ---------------------------------------------------------------------------
# Byte determinism + meta consistency + the over-count mutation guard
# ---------------------------------------------------------------------------


def test_byte_deterministic_and_matches_shipped(doc):
    again = registry.registry_doc(registry.build())
    a = flatten.compact_json(doc, sort_keys=True)
    b = flatten.compact_json(again, sort_keys=True)
    assert a == b                                      # two builds, identical bytes
    shipped = (canon.OUT_ROOT / "players.json").read_bytes()
    assert hashlib.sha256(a).hexdigest() == hashlib.sha256(shipped).hexdigest()


def test_meta_n_players_matches_registry(doc):
    meta = json.loads((canon.OUT_ROOT / "meta.json").read_text())
    assert meta["n_players"] == doc["count"] == REGISTRY_COUNT


def test_name_count_overcounts_pid_count(doc):
    """Mutation guard: counting by NAME (the shipped-then-fixed 938) over-counts the
    honest pid universe (937). Folding spellings by pid is what removes the phantom."""
    naive = _naive_name_union()
    assert len(naive) == NAIVE_NAME_COUNT
    assert doc["count"] < len(naive)                   # pid-keying is strictly honester
    assert len(naive) - doc["count"] == 1


# ===========================================================================
# Phase 2 — the two client-assembly card tables (pipeline/player_tables.py)
#
#   duels        players/duels_by_player.json: top-12 EB-shrunk duels per pid per
#                side, every row >= 6 balls, ranked by balls (Panel C)
#   teleporter   players/teleporter_lookup.json: per league/season sorted SR list,
#                the client's percentile_of / sr_at_pct read off it (Panel D)
#
# Recounted on the real corpus 2026-07-09; the srplus row count, the pair count, the
# pids-with-duels count and a famous duel are dated so a corpus drop fails loudly.
# ===========================================================================

# Corpus-wide snapshot constants (recounted 2026-07-09).
SRPLUS_ROW_COUNT = 1117          # engines/srplus.json batter_seasons, all >= 100 balls
COUNT_PAIRS = 33772              # distinct (batter, bowler) duel pairs (== h2h N_PAIRS)
PIDS_WITH_DUELS = 876            # pids with >= 1 duel (>= 6 balls) on either side
MIN_DUEL_BALLS = 6               # the on-card duel floor (a shorter pair is noise)
TOP_N = 12                       # at most this many duels per side per player
TARGET_SEASON = 2026             # the modern era the teleporter re-prices into

# V Kohli batting vs RA Jadeja — the published Engine #6 worked example (the same
# 160 / 179 / 3 the h2h tests pin), now surfaced as a card duel row.
JADEJA_PID = "fe93fd9d"
KOHLI_JADEJA = (160, 179, 3)     # (balls, runs, dismissals), Kohli on strike

# ipl 2016 season SR distribution spot-check (52 qualifying batter-seasons).
IPL2016_N = 52
IPL2016_MIN = 98.55
IPL2016_MAX = 191.13
IPL2016_MEDIAN = 129.07


@pytest.fixture(scope="module")
def table_eb():
    """One h2h table + one EB fit, shared by every duel test (corpus parsed once
    for the table, once for the constants — never once per player)."""
    return h2h.build_table(), h2h.eb_constants()


@pytest.fixture(scope="module")
def name_of():
    """pid -> canonical spelling, off the shipped registry (what the emitter joins on)."""
    return player_tables._load_name_of(canon.OUT_ROOT)


@pytest.fixture(scope="module")
def duels(table_eb, name_of):
    table, eb = table_eb
    return player_tables.build_duels(table=table, eb=eb, name_of=name_of)


@pytest.fixture(scope="module")
def srplus():
    return player_tables._load_srplus(canon.OUT_ROOT)


@pytest.fixture(scope="module")
def teleporter(srplus):
    return player_tables.build_teleporter(srplus)


# ---------------------------------------------------------------------------
# srplus row count (the river source the client reuses by name-union)
# ---------------------------------------------------------------------------


def test_srplus_row_count(srplus):
    assert srplus["min_balls"] == 100
    assert srplus["count"] == SRPLUS_ROW_COUNT
    assert len(srplus["batter_seasons"]) == SRPLUS_ROW_COUNT


# ---------------------------------------------------------------------------
# Duels — structure, counts, ranking, and the EB-shrunk dominance
# ---------------------------------------------------------------------------


def test_duels_shape_and_counts(duels):
    assert set(duels) == {"by_pid", "eb", "count_pairs"}
    assert duels["count_pairs"] == COUNT_PAIRS
    assert len(duels["by_pid"]) == PIDS_WITH_DUELS
    assert duels["eb"]["mu"] == pytest.approx(1.3322, abs=5e-4)
    assert duels["eb"]["k"] == pytest.approx(51.2, abs=0.1)


def test_every_duel_is_well_formed(duels):
    """Every row on every card: >= 6 balls, a present dom, a canonical opp name, and
    each side capped at TOP_N and ranked by balls descending (no cherry-pick sort)."""
    for pid, rec in duels["by_pid"].items():
        assert set(rec) == {"as_batter", "as_bowler"}
        assert rec["as_batter"] or rec["as_bowler"]        # in the table for a reason
        for side in ("as_batter", "as_bowler"):
            lst = rec[side]
            assert len(lst) <= TOP_N
            balls = [d["balls"] for d in lst]
            assert balls == sorted(balls, reverse=True)     # ranked by balls desc
            for d in lst:
                assert set(d) == {"opp_pid", "opp_name", "balls", "runs",
                                  "dismissals", "dom"}
                assert d["balls"] >= MIN_DUEL_BALLS
                assert d["runs"] >= 0 and d["dismissals"] >= 0
                assert isinstance(d["dom"], float)          # EB-shrunk runs/ball
                assert d["opp_name"] and isinstance(d["opp_name"], str)


def test_dom_is_eb_shrunk_runs_per_ball(duels, table_eb):
    _table, eb = table_eb
    checked = 0
    for rec in duels["by_pid"].values():
        for d in rec["as_batter"]:
            assert d["dom"] == round(eb.shrunk(d["balls"], d["runs"]), player_tables.DOM_DP)
            checked += 1
    assert checked > 0


def test_kohli_jadeja_duel_row(duels, table_eb, name_of):
    """The famous duel lands on Kohli's card as a batter row and on Jadeja's card as a
    bowler row, both carrying the exact corpus 160 / 179 / 3 and one shared dom."""
    table, eb = table_eb
    assert table.get(KOHLI_PID, JADEJA_PID) == KOHLI_JADEJA   # corpus ground truth
    balls, runs, dismissals = KOHLI_JADEJA
    dom = round(eb.shrunk(balls, runs), player_tables.DOM_DP)

    kohli_row = next(d for d in duels["by_pid"][KOHLI_PID]["as_batter"]
                     if d["opp_pid"] == JADEJA_PID)
    assert (kohli_row["balls"], kohli_row["runs"], kohli_row["dismissals"]) == KOHLI_JADEJA
    assert kohli_row["opp_name"] == name_of[JADEJA_PID] == "RA Jadeja"
    assert kohli_row["dom"] == dom

    jadeja_row = next(d for d in duels["by_pid"][JADEJA_PID]["as_bowler"]
                      if d["opp_pid"] == KOHLI_PID)
    assert (jadeja_row["balls"], jadeja_row["runs"], jadeja_row["dismissals"]) == KOHLI_JADEJA
    assert jadeja_row["opp_name"] == name_of[KOHLI_PID] == "V Kohli"
    assert jadeja_row["dom"] == dom                            # a pair property, not a viewpoint


def test_duels_byte_identical_and_matches_shipped(table_eb, name_of):
    table, eb = table_eb
    a = flatten.compact_json(
        player_tables.build_duels(table=table, eb=eb, name_of=name_of), sort_keys=True)
    b = flatten.compact_json(
        player_tables.build_duels(table=table, eb=eb, name_of=name_of), sort_keys=True)
    assert a == b                                             # two builds, identical bytes
    shipped = (canon.OUT_ROOT / "players" / "duels_by_player.json").read_bytes()
    assert hashlib.sha256(a).hexdigest() == hashlib.sha256(shipped).hexdigest()


# ---------------------------------------------------------------------------
# Teleporter lookup — both leagues, the target season, and a sorted distribution
# ---------------------------------------------------------------------------


def test_teleporter_has_both_leagues_and_target(teleporter):
    assert set(teleporter) == {"by_league_season", "target_season"}
    assert teleporter["target_season"] == TARGET_SEASON
    bls = teleporter["by_league_season"]
    assert set(bls) == {"ipl", "wpl"}
    assert str(TARGET_SEASON) in bls["ipl"]                   # 2026 present in ipl
    assert str(TARGET_SEASON) in bls["wpl"]                   # and re-priceable in wpl
    for lg, by_season in bls.items():
        for s, srs in by_season.items():
            assert srs == sorted(srs)                         # ascending distribution
            assert len(srs) >= 1 and all(isinstance(x, float) for x in srs)


def test_teleporter_ipl2016_distribution(teleporter):
    srs = teleporter["by_league_season"]["ipl"]["2016"]
    assert len(srs) == IPL2016_N
    assert srs[0] == IPL2016_MIN
    assert srs[-1] == IPL2016_MAX
    assert statistics.median(srs) == pytest.approx(IPL2016_MEDIAN)


def test_teleporter_percentile_self_consistency(teleporter):
    """The client recipe (ch10.py:214-241) reads percentiles straight off these
    sorted lists: the min sits at ~0%, the median at ~50%, ordering is monotone."""
    srs = teleporter["by_league_season"]["ipl"]["2016"]

    def percentile_of(sr):                                   # mirrors ch10 percentile_of
        return 100.0 * sum(1 for x in srs if x < sr) / len(srs)

    assert percentile_of(srs[0]) == pytest.approx(0.0)
    assert percentile_of(srs[-1] + 1) == pytest.approx(100.0)
    assert percentile_of(statistics.median(srs)) == pytest.approx(50.0, abs=2.0)


def test_teleporter_byte_identical_and_matches_shipped(srplus):
    a = flatten.compact_json(player_tables.build_teleporter(srplus), sort_keys=True)
    b = flatten.compact_json(player_tables.build_teleporter(srplus), sort_keys=True)
    assert a == b
    shipped = (canon.OUT_ROOT / "players" / "teleporter_lookup.json").read_bytes()
    assert hashlib.sha256(a).hexdigest() == hashlib.sha256(shipped).hexdigest()


# ---------------------------------------------------------------------------
# Mutation guard — the >= 6-ball duel floor is load-bearing
# ---------------------------------------------------------------------------


def test_mutation_dropping_the_ball_floor_admits_noise(table_eb, name_of, monkeypatch):
    """Deliberately break the invariant: with the floor lowered to 1 ball, the duel
    table admits sub-6-ball noise rows (which the real >= 6 floor keeps off every
    card). The shipped floor has ZERO such rows; the mutation has some, proving the
    floor does real work rather than being vacuous."""
    table, eb = table_eb

    honest = player_tables.build_duels(table=table, eb=eb, name_of=name_of)
    honest_min = min(d["balls"] for rec in honest["by_pid"].values()
                     for side in rec.values() for d in side)
    assert honest_min >= MIN_DUEL_BALLS                       # nothing under 6 ships

    monkeypatch.setattr(player_tables, "MIN_DUEL_BALLS", 1)
    mutated = player_tables.build_duels(table=table, eb=eb, name_of=name_of)
    mutated_min = min(d["balls"] for rec in mutated["by_pid"].values()
                      for side in rec.values() for d in side)
    assert mutated_min < MIN_DUEL_BALLS                       # the guard is not vacuous
    assert len(mutated["by_pid"]) > len(honest["by_pid"])     # more pids clear a 1-ball floor
