"""Flatten Cricsheet ball-by-ball JSON into the R0 data-contract artifacts.

One pass over data/ipl_json + data/wpl_json in strict chronological order
(match date, match_id, innings index, over, delivery index), super-over
innings excluded, emitting into web/static/data/:

  meta.json         { n_points, built_at: "unknown", point_order, files }
                    (scenes.py augments it to v2: + n_players, per-league
                    n_matches — storyboard CO-3 title-card traceability)
  groups.json       23 ordered groups: IPL 2008..2026 then WPL 2023..2026
  group_ids.u16     little-endian Uint16 per delivery -> gi
  attrs.u8          bit-packed per delivery:
                      bits 0-2  outcome class (0 dot / 1 single / 2 two-or-
                                three / 3 four / 4 six / 5 other scoring
                                ball — extras-only scoring balls and freak
                                batter 5s)
                      bit 3     wicket fell on this ball
                      bit 4     WPL
  ballsfaced.u8     per delivery: the striker's 1-based ball-faced index
                    within their innings AT this delivery (wides = 0 — the
                    batter doesn't face them; no-balls count; capped at 255).
                    Powers the Ch 1 ignition-wall layout.
  team.u8           per delivery: canonical batting-franchise id (league-
                    scoped; renames collapse — Delhi Daredevils deliveries
                    carry the Delhi Capitals id). Ids defined in teams.json.
  teams.json        the 20-franchise table: [{id, name, short, league,
                    color, active}] (canon.TEAMS verbatim).
  columnar.json.gz  sandbox dataset: 12 parallel arrays + name dictionaries

Layouts are procedural / derived client-side — zero position buffers are
shipped (blueprint §2). Stdlib only. Deterministic output (gzip mtime=0).
"""

from __future__ import annotations

import gzip
import json
import sys
from array import array
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import canon

# ---------------------------------------------------------------------------
# Outcome classes (contract values — also mirrored in attrs.u8 bits 0-2)
# ---------------------------------------------------------------------------

OUT_DOT = 0
OUT_SINGLE = 1
OUT_TWO_OR_THREE = 2
OUT_FOUR = 3
OUT_SIX = 4
OUT_OTHER_SCORING = 5

ATTR_WICKET_BIT = 1 << 3
ATTR_WPL_BIT = 1 << 4


def outcome_class(delivery: dict) -> int:
    """Classify a delivery by what came off the bat, else by extras.

    Off-the-bat runs win: 1 -> single, 2/3 -> two-or-three, 4 -> four
    (boundary or all-run), 6 -> six. A ball with zero total runs is a dot.
    Anything else that scored (wides, byes, leg-byes, no-ball extras with
    no bat runs — plus the 78 freak batter-5s in the corpus) is class 5.
    """
    rb = delivery["runs"]["batter"]
    if rb == 1:
        return OUT_SINGLE
    if rb in (2, 3):
        return OUT_TWO_OR_THREE
    if rb == 4:
        return OUT_FOUR
    if rb == 6:
        return OUT_SIX
    if rb == 0 and delivery["runs"]["total"] == 0:
        return OUT_DOT
    return OUT_OTHER_SCORING


def pack_attr(delivery: dict, wpl: bool) -> int:
    byte = outcome_class(delivery)
    if delivery.get("wickets"):
        byte |= ATTR_WICKET_BIT
    if wpl:
        byte |= ATTR_WPL_BIT
    return byte


# ---------------------------------------------------------------------------
# Corpus iteration in contract order
# ---------------------------------------------------------------------------


def sorted_match_files(data_root: Path = canon.DATA_ROOT):
    """[(date0, match_id, league, path)] sorted by (date, match_id).

    Cheap first pass: parse each file once just for its sort key, then the
    caller re-parses in order (memory stays flat; the corpus parses in <1s).
    """
    entries = []
    for league, dirname in canon.LEAGUE_DIRS:
        for path in sorted((data_root / dirname).glob("*.json")):
            with open(path) as fh:
                info = json.load(fh)["info"]
            entries.append((str(info["dates"][0]), int(path.stem), league, path))
    entries.sort(key=lambda e: (e[0], e[1]))
    return entries


class DictEncoder:
    """Name -> stable int code, in first-seen (chronological) order."""

    def __init__(self):
        self.codes = {}
        self.names = []

    def code(self, name: str) -> int:
        c = self.codes.get(name)
        if c is None:
            c = len(self.names)
            self.codes[name] = c
            self.names.append(name)
        return c


def build_stream(data_root: Path = canon.DATA_ROOT):
    """Single chronological pass producing every per-point structure."""
    groups = [
        {"gi": gi, "league": lg, "season": season, "count": 0}
        for gi, (lg, season) in enumerate(
            [("ipl", s) for s in canon.IPL_SEASONS]
            + [("wpl", s) for s in canon.WPL_SEASONS]
        )
    ]
    gi_of = {(g["league"], g["season"]): g["gi"] for g in groups}

    group_ids = array("H")
    attrs = bytearray()
    ballsfaced = bytearray()
    team_u8 = bytearray()

    batters, bowlers, teams = DictEncoder(), DictEncoder(), DictEncoder()
    col = {
        "season": [], "league": [], "innings": [], "over": [],
        "ball_index_in_over": [], "batter": [], "bowler": [],
        "batting_team": [], "runs_batter": [], "runs_total": [],
        "outcome": [], "wicket": [],
    }

    for _date, _mid, league, path in sorted_match_files(data_root):
        with open(path) as fh:
            match = json.load(fh)
        info = match["info"]
        season = canon.canon_season(info)
        gi = gi_of[(league, season)]
        wpl = league == "wpl"
        canon.canon_venue(info["venue"])  # exhaustiveness enforced at build time
        canon.is_dl(info)

        innings_no = 0
        for innings in match.get("innings", []):
            if canon.is_super_over(innings):
                continue  # standing rule: super overs never enter the stream
            innings_no += 1
            canonical_team = canon.canon_team(innings["team"])
            team_code = teams.code(canonical_team)
            franchise_id = canon.team_id(league, canonical_team)
            faced: dict[str, int] = {}
            for over in innings["overs"]:
                over_no = over["over"]
                for ball_index, dl in enumerate(over["deliveries"]):
                    group_ids.append(gi)
                    groups[gi]["count"] += 1
                    attrs.append(pack_attr(dl, wpl))
                    team_u8.append(franchise_id)
                    if "wides" in dl.get("extras", {}):
                        ballsfaced.append(0)  # a wide is not a ball faced
                    else:
                        n = faced.get(dl["batter"], 0) + 1
                        faced[dl["batter"]] = n
                        ballsfaced.append(min(n, 255))
                    col["season"].append(season)
                    col["league"].append(1 if wpl else 0)
                    col["innings"].append(innings_no)
                    col["over"].append(over_no)
                    col["ball_index_in_over"].append(ball_index)
                    col["batter"].append(batters.code(dl["batter"]))
                    col["bowler"].append(bowlers.code(dl["bowler"]))
                    col["batting_team"].append(team_code)
                    col["runs_batter"].append(dl["runs"]["batter"])
                    col["runs_total"].append(dl["runs"]["total"])
                    col["outcome"].append(outcome_class(dl))
                    col["wicket"].append(1 if dl.get("wickets") else 0)

    dicts = {
        "batter": batters.names,
        "bowler": bowlers.names,
        "batting_team": teams.names,
    }
    return groups, group_ids, attrs, col, dicts, ballsfaced, team_u8


# ---------------------------------------------------------------------------
# Emission
# ---------------------------------------------------------------------------


def gz_bytes(raw: bytes) -> bytes:
    """Deterministic gzip (level 9, mtime=0)."""
    return gzip.compress(raw, compresslevel=9, mtime=0)


def compact_json(obj, *, sort_keys: bool = False) -> bytes:
    return json.dumps(
        obj, separators=(",", ":"), ensure_ascii=False, sort_keys=sort_keys
    ).encode("utf-8")


def main(out_root: Path = canon.OUT_ROOT) -> dict:
    groups, group_ids, attrs, col, dicts, ballsfaced, team_u8 = build_stream()
    n_points = len(attrs)
    assert len(group_ids) == n_points
    assert all(len(v) == n_points for v in col.values())
    assert sum(g["count"] for g in groups) == n_points
    assert len(ballsfaced) == n_points
    assert len(team_u8) == n_points

    out_root.mkdir(parents=True, exist_ok=True)
    (out_root / "payoff").mkdir(parents=True, exist_ok=True)

    if sys.byteorder == "big":  # contract: little-endian on the wire
        group_ids = array("H", group_ids)
        group_ids.byteswap()

    files: dict[str, dict] = {}

    def emit(name: str, raw: bytes, *, pregzipped: bool = False):
        path = out_root / name
        if pregzipped:
            gz = gz_bytes(raw)
            path.write_bytes(gz)
            files[name] = {"bytes_raw": len(raw), "bytes_gz": len(gz)}
        else:
            path.write_bytes(raw)
            files[name] = {"bytes_raw": len(raw), "bytes_gz": len(gz_bytes(raw))}

    emit("groups.json", compact_json(groups))
    emit("group_ids.u16", group_ids.tobytes())
    emit("attrs.u8", bytes(attrs))
    emit("ballsfaced.u8", bytes(ballsfaced))
    emit("team.u8", bytes(team_u8))
    emit("teams.json", compact_json(list(canon.TEAMS), sort_keys=True))
    emit(
        "columnar.json.gz",
        compact_json(
            {
                "n_points": n_points,
                "point_order": "chronological",
                "arrays": col,
                "dicts": dicts,
            }
        ),
        pregzipped=True,
    )

    meta = {
        "n_points": n_points,
        "built_at": "unknown",
        "point_order": "chronological",
        "files": files,
    }
    (out_root / "meta.json").write_bytes(compact_json(meta))

    print(f"n_points={n_points}  groups={len(groups)}")
    for name, sizes in files.items():
        print(f"  {name:18s} raw={sizes['bytes_raw']:>10,}  gz={sizes['bytes_gz']:>9,}")
    return meta


if __name__ == "__main__":
    main()
