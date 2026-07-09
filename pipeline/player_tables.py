"""R7a Phase 2 — the two small per-player card tables (hybrid client-assembly).

The player cards at /players are assembled CLIENT-SIDE (storyboard §9.10): the SR+
river reuses the already-shipped engines/srplus.json and the entry map reuses
engines/entry.json, both joined by name-union off the registry (players.json). This
module emits ONLY what does not already exist on the client:

  players/duels_by_player.json   Panel C (Top Duels). PID-keyed. Per player, up to
                                 the top 12 duels AS BATTER (bowlers faced) and up to
                                 the top 12 AS BOWLER (batters faced), each duel with
                                 the ball count (so the client can hollow a duel under
                                 30 balls, "too few to call" — storyboard §9.4) and the
                                 Engine #6 empirical-Bayes-shrunk runs/ball so a 12-ball
                                 fluke can never draw a long dominance bar. Built from
                                 ONE h2h.build_table() pass (not one pass per player);
                                 dominance is EBConstants.shrunk(balls, runs) per pair.

  players/teleporter_lookup.json Panel D (Teleporter). Per (league, season) the SORTED
                                 list of qualifying batter-season strike rates, so the
                                 client can run percentile_of(sr, league, season) and
                                 sr_at_pct(pct, league, target) exactly like
                                 ch10.py:214-241 with NO new corpus pass. Sourced from
                                 the shipped engines/srplus.json batter_seasons (already
                                 >= 100 balls, the SR+ qualifier), field "sr".

Stdlib only, no numpy, byte-deterministic (compact JSON, sorted keys; ranked lists
break every tie deterministically; the h2h table + EB constants are pure functions of
the corpus, so two runs emit identical bytes).

The opponent's display name is the registry CANONICAL spelling (players.json), so two
people who share a written name are never folded onto one duel row (the registry keys
on pid; verified: all 937 h2h-table pids resolve into players.json exactly).
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import canon
import flatten
import h2h                        # Engine #6: build_table / eb_constants / EBConstants

# A duel needs at least this many faced balls to appear on a card at all (a shorter
# pair is noise; the client further hollows anything under ~30 as "too few to call").
MIN_DUEL_BALLS = 6
# At most this many duels per side per player (ranked by balls; no cherry-pick sort).
TOP_N = 12
# Storyboard §9.4 dominance shrink display constants come straight from Engine #6.
DOM_DP = 4                        # runs/ball, rounded for a compact, stable payload


# ---------------------------------------------------------------------------
# Panel C — the per-player duel table (one h2h pass, EB-shrunk dominance)
# ---------------------------------------------------------------------------


def build_duels(
    table: h2h.H2HTable = None,
    eb: h2h.EBConstants = None,
    name_of: dict = None,
    data_root: Path = canon.DATA_ROOT,
) -> dict:
    """{"by_pid": {pid: {"as_batter": [...], "as_bowler": [...]}}, "eb": {mu, k},
    "count_pairs": N}. ``name_of`` maps every registry pid to its canonical spelling
    (players.json); ``table`` / ``eb`` are reused if passed (one corpus pass total)."""
    if table is None:
        table = h2h.build_table(data_root)
    if eb is None:
        eb = h2h.eb_constants(data_root)
    if name_of is None:
        name_of = _load_name_of(canon.OUT_ROOT)

    # Bucket every >= MIN_DUEL_BALLS pair onto BOTH players: the batter sees the bowler
    # in as_batter, the bowler sees the batter in as_bowler. dom is the same shrunk
    # runs/ball from either side (it is a property of the pair, not the viewpoint).
    as_batter: dict = defaultdict(list)
    as_bowler: dict = defaultdict(list)
    for (bat_pid, bowl_pid), (balls, runs, dismissals) in table.items():
        if balls < MIN_DUEL_BALLS:
            continue
        dom = round(eb.shrunk(balls, runs), DOM_DP)
        as_batter[bat_pid].append(_duel(bowl_pid, name_of, balls, runs, dismissals, dom))
        as_bowler[bowl_pid].append(_duel(bat_pid, name_of, balls, runs, dismissals, dom))

    by_pid: dict = {}
    for pid in set(as_batter) | set(as_bowler):
        by_pid[pid] = {
            "as_batter": _rank(as_batter.get(pid, [])),
            "as_bowler": _rank(as_bowler.get(pid, [])),
        }
    return {
        "by_pid": by_pid,
        "eb": {"mu": round(eb.mu, 6), "k": round(eb.k, 4)},
        "count_pairs": len(table),
    }


def _duel(opp_pid, name_of, balls, runs, dismissals, dom) -> dict:
    return {
        "opp_pid": opp_pid,
        "opp_name": name_of.get(opp_pid, opp_pid),
        "balls": balls,
        "runs": runs,
        "dismissals": dismissals,
        "dom": dom,
    }


def _rank(duels: list) -> list:
    """Top TOP_N by balls desc; every tie broken deterministically (more runs, then
    more dismissals, then opp_pid) so the bytes are stable and the sort is honest
    (ranked by balls faced, never by who 'won')."""
    ordered = sorted(
        duels,
        key=lambda d: (-d["balls"], -d["runs"], -d["dismissals"], d["opp_pid"]),
    )
    return ordered[:TOP_N]


# ---------------------------------------------------------------------------
# Panel D — the teleporter percentile lookup (per league/season sorted SR list)
# ---------------------------------------------------------------------------


def build_teleporter(srplus: dict) -> dict:
    """{"by_league_season": {"ipl": {"2008": [sr,...], ...}, "wpl": {...}},
    "target_season": <int>}. The sorted SR list per (league, season) IS the season
    distribution ch10's season_srs builds; the client's percentile_of / sr_at_pct read
    off it directly. Only rows at or above the SR+ qualifier (already the whole file)."""
    min_balls = srplus.get("min_balls", 100)
    buckets: dict = defaultdict(lambda: defaultdict(list))
    seasons_seen = set()
    for row in srplus["batter_seasons"]:
        if row["balls"] < min_balls:
            continue
        buckets[row["league"]][str(row["season"])].append(row["sr"])
        seasons_seen.add(row["season"])

    by_league_season = {
        lg: {s: sorted(srs) for s, srs in sorted(by_season.items())}
        for lg, by_season in sorted(buckets.items())
    }
    # The modern era every player re-prices INTO (both leagues run through it).
    target_season = max(seasons_seen)
    return {"by_league_season": by_league_season, "target_season": target_season}


# ---------------------------------------------------------------------------
# Entry point (write both tables under players/; print a summary)
# ---------------------------------------------------------------------------


def _load_name_of(out_root: Path) -> dict:
    players = json.loads((out_root / "players.json").read_text())
    return {p["pid"]: p["name"] for p in players["players"]}


def _load_srplus(out_root: Path) -> dict:
    return json.loads((out_root / "engines" / "srplus.json").read_text())


def main(out_root: Path = canon.OUT_ROOT) -> dict:
    name_of = _load_name_of(out_root)
    srplus = _load_srplus(out_root)

    table = h2h.build_table()
    eb = h2h.eb_constants()

    duels = build_duels(table=table, eb=eb, name_of=name_of)
    teleporter = build_teleporter(srplus)

    players_dir = out_root / "players"
    players_dir.mkdir(parents=True, exist_ok=True)

    outputs = {
        "players/duels_by_player.json": duels,
        "players/teleporter_lookup.json": teleporter,
    }
    sizes = {}
    for rel, doc in outputs.items():
        raw = flatten.compact_json(doc, sort_keys=True)
        (out_root / rel).write_bytes(raw)
        sizes[rel] = (len(raw), len(flatten.gz_bytes(raw)))
        print(f"  {rel:<34} raw={len(raw):>9,}  gz={sizes[rel][1]:>8,}")

    n_with_duels = len(duels["by_pid"])
    print(
        f"duels: count_pairs={duels['count_pairs']:,}  pids_with_duels={n_with_duels:,}  "
        f"eb.mu={duels['eb']['mu']}  eb.k={duels['eb']['k']}"
    )
    tls = teleporter["by_league_season"]
    ipl2016 = tls["ipl"]["2016"]
    print(
        f"teleporter: leagues={sorted(tls)}  target_season={teleporter['target_season']}  "
        f"ipl2016 n={len(ipl2016)} min={ipl2016[0]} max={ipl2016[-1]}"
    )
    return {"duels": duels, "teleporter": teleporter, "sizes": sizes}


if __name__ == "__main__":
    main()
