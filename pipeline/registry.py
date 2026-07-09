"""R7a — the canonical PLAYER REGISTRY (correctness + honesty foundation).

One authoritative corpus pass that resolves every delivery's batter and bowler to
its stable registry person-id (info.registry.people, via h2h.resolve) and emits the
join key every player card and the search box keys on. Stdlib only, no numpy,
byte-deterministic (compact JSON, sorted keys; no randomness, so two runs emit
identical bytes).

The universe is every registry pid who FACED or BOWLED at least one ball in the
corpus (IPL 2008-2026 + WPL 2023-2026, super overs excluded). A pid is one real
person, and a pid may carry MULTIPLE display spellings (aliases: e.g. "NA Saini" and
"Navdeep Saini" are one pid, one card). Folding spellings by pid is what stops a
spelling change from ever becoming a second player.

The reverse is NOT a clean function: the corpus holds genuine NAMESAKES, one written
name shared by two different people (two IPL bowlers both scored "Harmeet Singh"; a
men's IPL "S Rana" and a women's WPL "S Rana"). The registry keeps them as separate
pids, exactly as it should. So name -> pid is one-to-MANY at the namesakes and the
search index resolves a spelling to a LIST of candidate pids (a singleton for all but
the namesakes), disambiguated downstream by role / league / seasons. Silently
collapsing a namesake to one pid would merge two people, which this module refuses.

Emits ONE artifact and corrects one number:

  players.json   { players: [ {pid, name (canonical = last-seen display spelling),
                   aliases (all distinct spellings, sorted), leagues (["ipl"] or
                   ["wpl"] — one league family per pid, asserted), seasons (sorted
                   ints), teams (sorted short codes), role ("bat"|"bowl"|"all"),
                   balls_faced, balls_bowled} ...sorted by pid ],
                   name_to_pids: {spelling: [pid, ...] sorted, for EVERY spelling},
                   namesakes: {name: [pid, ...] for the names shared by >1 person},
                   count: <int> }

  meta.json      n_players corrected to the REAL registry pid count (the len of
                 players). The shipped value was NAME-based and over-counted: a
                 spelling change was silently a second player. Cards resolve by pid,
                 so this count is now the honest one. Written in place, byte-stable.

HONESTY GUARDRAILS:
  * one league family per pid: no pid appears in both IPL and WPL (men's / women's
    are disjoint person spaces; a shared pid would be a data-integrity break). Hard
    assert; a violation raises with the offending pids named.
  * two people are never merged: cards key on pid, aliases are per-pid, and namesakes
    stay distinct pids. Namesakes are surfaced as a first-class artifact fact (the
    namesakes block) rather than silently resolved to one person.
  * the search index covers exactly the universe: every emitted pid is reachable by
    at least one spelling, and every spelling maps only to universe pids. Asserted.

Conventions match the rest of the pipeline (ch10.py / methods page): a wide is not a
ball faced (SR convention); a legal ball bowled excludes wides and no-balls.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import canon
import flatten
import h2h                        # Engine #6: person_registry / resolve (pid lookup)

# Every non-super-over delivery in the corpus (incl. wides / no-balls), asserted
# against the well-known total so a changed corpus fails loudly (matches ch10).
TOTAL_POINTS_EXPECT = 316199

# Balls needed in a discipline for it to count toward an "all-rounder" label. A
# batter who bowled a few part-time overs (or a No. 11 who faced a handful) is a
# specialist, not an all-rounder; ~300 balls is roughly a season of real duty.
ROLE_MIN_BALLS = 300

# (league, canonical franchise name) -> short code (league-scoped; the WPL's DC / MI
# / RCB carry the "-W" shorts, distinct from their IPL namesakes).
SHORT_BY = {(t["league"], t["name"]): t["short"] for t in canon.TEAMS}


# ---------------------------------------------------------------------------
# The one corpus pass (registry-resolved pids for the whole player universe)
# ---------------------------------------------------------------------------


def build(data_root: Path = canon.DATA_ROOT) -> dict:
    faced: dict = defaultdict(int)              # pid -> balls faced (wides excluded)
    bowled: dict = defaultdict(int)             # pid -> legal balls bowled
    name_of: dict = {}                          # pid -> last-seen display spelling
    aliases: dict = defaultdict(set)            # pid -> {all display spellings}
    leagues: dict = defaultdict(set)            # pid -> {"ipl"|"wpl"}
    seasons: dict = defaultdict(set)            # pid -> {season int}
    teams: dict = defaultdict(set)              # pid -> {short code}
    npoints = 0

    for _date, _mid, league, path in flatten.sorted_match_files(data_root):
        with open(path) as fh:
            match = json.load(fh)
        info = match["info"]
        season = canon.canon_season(info)
        reg = h2h.person_registry(info)
        match_teams = info.get("teams", [])
        for innings in match.get("innings", []):
            if canon.is_super_over(innings):
                continue
            bat_raw = innings["team"]
            others = [t for t in match_teams if t != bat_raw]
            bowl_raw = others[0] if len(others) == 1 else None
            bat_short = SHORT_BY.get((league, canon.canon_team(bat_raw)))
            bowl_short = (
                SHORT_BY.get((league, canon.canon_team(bowl_raw)))
                if bowl_raw is not None
                else None
            )
            for over in innings["overs"]:
                for dl in over["deliveries"]:
                    npoints += 1
                    ex = dl.get("extras", {})
                    is_wide = "wides" in ex
                    is_noball = "noballs" in ex

                    # Batter side: team membership + spelling on every occurrence;
                    # a wide is not a ball faced (SR convention).
                    bpid = h2h.resolve(reg, dl["batter"])
                    name_of[bpid] = dl["batter"]
                    aliases[bpid].add(dl["batter"])
                    leagues[bpid].add(league)
                    seasons[bpid].add(season)
                    if bat_short is not None:
                        teams[bpid].add(bat_short)
                    if not is_wide:
                        faced[bpid] += 1

                    # Bowler side: team membership + spelling on every occurrence; a
                    # legal ball bowled excludes wides and no-balls.
                    wpid = h2h.resolve(reg, dl["bowler"])
                    name_of[wpid] = dl["bowler"]
                    aliases[wpid].add(dl["bowler"])
                    leagues[wpid].add(league)
                    seasons[wpid].add(season)
                    if bowl_short is not None:
                        teams[wpid].add(bowl_short)
                    if not is_wide and not is_noball:
                        bowled[wpid] += 1

    assert npoints == TOTAL_POINTS_EXPECT, (npoints, TOTAL_POINTS_EXPECT)
    return {
        "faced": dict(faced),
        "bowled": dict(bowled),
        "name_of": name_of,
        "aliases": {k: v for k, v in aliases.items()},
        "leagues": {k: v for k, v in leagues.items()},
        "seasons": {k: v for k, v in seasons.items()},
        "teams": {k: v for k, v in teams.items()},
        "npoints": npoints,
    }


# ---------------------------------------------------------------------------
# Emission (registry doc + the two honesty asserts)
# ---------------------------------------------------------------------------


def registry_doc(agg: dict) -> dict:
    faced = agg["faced"]
    bowled = agg["bowled"]
    name_of = agg["name_of"]
    aliases = agg["aliases"]
    leagues = agg["leagues"]
    seasons = agg["seasons"]
    teams = agg["teams"]

    # Universe = faced OR bowled at least one ball.
    universe = sorted(
        pid for pid in set(faced) | set(bowled)
        if faced.get(pid, 0) > 0 or bowled.get(pid, 0) > 0
    )

    # GUARDRAIL 1: one league family per pid (men's IPL / women's WPL are disjoint
    # person spaces; a shared pid would be a merge of two people).
    cross_league = sorted(
        pid for pid in universe if len(leagues[pid]) != 1
    )
    assert not cross_league, (
        "pid(s) appear in more than one league family (IPL and WPL must never "
        f"share a pid): {[(pid, sorted(leagues[pid])) for pid in cross_league]}"
    )

    players = []
    for pid in universe:
        bf = faced.get(pid, 0)
        bb = bowled.get(pid, 0)
        # "all-rounder" needs a MEANINGFUL contribution in both disciplines, not any
        # tail-end bat or part-time over. Below the bar, classify by the bigger role.
        # (A pure specialist has 0 in one column and lands in bat/bowl either way.)
        role = (
            "all" if (bf >= ROLE_MIN_BALLS and bb >= ROLE_MIN_BALLS)
            else ("bat" if bf >= bb else "bowl")
        )
        players.append({
            "pid": pid,
            "name": name_of[pid],
            "aliases": sorted(aliases[pid]),
            "leagues": sorted(leagues[pid]),
            "seasons": sorted(seasons[pid]),
            "teams": sorted(teams[pid]),
            "role": role,
            "balls_faced": bf,
            "balls_bowled": bb,
        })

    # The search index: every spelling -> the sorted list of pids that wrote it. A
    # singleton for all but the genuine namesakes (one written name, two people); the
    # list form is what keeps a namesake from silently merging into one person. Built
    # from the per-pid alias sets, so two people are never folded under one pid.
    name_to_pids: dict = defaultdict(set)
    for pid in universe:
        for alias in aliases[pid]:
            name_to_pids[alias].add(pid)
    name_to_pids = {name: sorted(pids) for name, pids in name_to_pids.items()}
    namesakes = {name: pids for name, pids in name_to_pids.items() if len(pids) > 1}

    # COVERAGE: the index spans exactly the universe (no unreachable pid, no phantom).
    covered = {pid for pids in name_to_pids.values() for pid in pids}
    assert covered == set(universe), (
        "search index does not cover the universe exactly: "
        f"missing={sorted(set(universe) - covered)} extra={sorted(covered - set(universe))}"
    )

    return {
        "players": players,
        "name_to_pids": name_to_pids,
        "namesakes": namesakes,
        "count": len(players),
    }


# ---------------------------------------------------------------------------
# Entry point (write players.json + correct meta.n_players; print a summary)
# ---------------------------------------------------------------------------


def _update_meta(out_root: Path, n_players: int) -> tuple[int, int]:
    """Correct meta.n_players in place, byte-stable. Returns (old, new)."""
    meta_path = out_root / "meta.json"
    meta = json.loads(meta_path.read_text())
    old = meta.get("n_players")
    meta["n_players"] = n_players
    meta_path.write_bytes(flatten.compact_json(meta))
    return old, n_players


def main(out_root: Path = canon.OUT_ROOT) -> dict:
    agg = build()
    doc = registry_doc(agg)

    raw = flatten.compact_json(doc, sort_keys=True)
    out_path = out_root / "players.json"
    out_path.write_bytes(raw)
    gz = len(flatten.gz_bytes(raw))

    old, new = _update_meta(out_root, doc["count"])

    players = doc["players"]
    batted = sum(1 for p in players if p["balls_faced"] > 0)
    bowled = sum(1 for p in players if p["balls_bowled"] > 0)
    allround = sum(1 for p in players if p["role"] == "all")
    splits = [p for p in players if len(p["aliases"]) > 1]

    print(f"  players.json           raw={len(raw):>9,}  gz={gz:>8,}")
    print(
        f"registry: pids={doc['count']:,}  batted={batted:,}  bowled={bowled:,}  "
        f"all-rounders={allround:,}"
    )
    print(f"alias-splits (one person, >1 spelling): {len(splits)}")
    for p in splits:
        print(f"    split: pid={p['pid']!r} canonical={p['name']!r} aliases={p['aliases']}")
    print(f"namesakes (one name, >1 person): {len(doc['namesakes'])}")
    for name, pids in sorted(doc["namesakes"].items()):
        print(f"    namesake: {name!r} -> {pids}")
    print(f"meta.n_players: {old} -> {new}")
    kohli_pids = doc["name_to_pids"].get("V Kohli", [])
    if kohli_pids:
        k = next(p for p in players if p["pid"] == kohli_pids[0])
        print(
            f"V Kohli: pid={k['pid']!r} teams={k['teams']} "
            f"seasons={k['seasons'][0]}-{k['seasons'][-1]} "
            f"balls_faced={k['balls_faced']:,} balls_bowled={k['balls_bowled']:,} role={k['role']}"
        )
    return doc


if __name__ == "__main__":
    main()
