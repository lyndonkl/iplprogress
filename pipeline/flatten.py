"""Flatten Cricsheet ball-by-ball JSON into the R0 data-contract artifacts.

One pass over data/ipl_json + data/wpl_json in SEASON-BLOCKED order — the
calendar year of play, then IPL before WPL WITHIN a shared year, then
chronological (match date, match_id, innings index, over, delivery index),
super-over innings excluded, emitting into web/static/data/:

The stream stays strictly chronological ACROSS seasons, but assembles "season
by season": within 2023 every IPL-2023 delivery precedes every WPL-2023
delivery (the WPL's March-2023 matches would otherwise interleave ahead of
IPL 2023). This restores the authored cold-open caption sequence — CO-3's
"2023: the year the ceiling broke" fires a beat BEFORE the WPL constellation
starts — with no scene change (the assembly scene measures its stops from the
actual point buffer, so the order in these buffers IS the assembly order).

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
                      bit 6     (0x40) the wicket that fell on this ball was a
                                RUN OUT — the Ch 2 run-out cascade flag (0 on
                                every non-run-out delivery). A pure re-encode of
                                a spare bit: R1 masks bits 0-4 only, so its
                                rendering is byte-identical (ledger delta 0).
  ballsfaced.u8     per delivery: the striker's 1-based ball-faced index
                    within their innings AT this delivery (wides = 0 — the
                    batter doesn't face them; no-balls count; capped at 255).
                    Powers the Ch 1 ignition-wall layout.
  cumruns.u8        per delivery: the striker's CUMULATIVE off-the-bat runs in
                    this innings so far, inclusive of this ball (capped at 255 —
                    an innings rarely exceeds ~175, so almost never clamped;
                    wides carry the unchanged running total since a wide scores
                    the batter nothing). Same point order as ballsfaced.u8.
                    Powers the Ch 2 worm-space y axis (runs climbing with balls
                    faced); a no-op for R1 layouts.
  team.u8           per delivery: canonical batting-franchise id (league-
                    scoped; renames collapse — Delhi Daredevils deliveries
                    carry the Delhi Capitals id). Ids defined in teams.json.
  wallheat.u8       per delivery: era-relative intent for the Ch 1 ignition-
                    wall thesis beat — a diverging byte for how much hotter
                    this ball's (league, season, clamped ball-index) cell
                    strike rate is than the pooled IPL 2008-2010 batter at the
                    same ball-index (neutral = the 2008-10 batter; wides carry
                    the neutral byte). Scale/legend live in scenes/ch1.json
                    (ignition.wallheat); see wallheat.py.
  innings_total.u8  per delivery: the FINAL total of the innings this delivery
                    belongs to (runs.total summed over the whole innings),
                    quantized to one byte as floor(total / 2) — decode
                    total ~= byte * 2 (2-run resolution, invisible in a
                    field morph; 255 == totals >= 510, which never occurs, the
                    corpus max innings total being 287). Constant within an
                    innings (every ball of an innings carries the same byte, so
                    it gzips to almost nothing). Powers the Chapter 4 waterline
                    morph: each ball stacks into its innings-total column while
                    the per-season par waterline (scenes/ch4.json) climbs the
                    wall. A no-op for R1/R2 layouts. Derived from the columnar
                    match_index/innings/runs_total arrays this same pass builds,
                    so it needs no extra corpus read; see innings_totals().
  teams.json        the 20-franchise table: [{id, name, short, league,
                    color, active}] (canon.TEAMS verbatim).
  matches.json      R1b sandbox: array indexed by match_index (== point-stream
                    order), each {teams:[a,b] (canonical), season, date, stage
                    ("Final"/"Qualifier 1"/"Eliminator"/"Match N"), venue,
                    city, result_text ("Mumbai Indians won by 1 run"), league}.
                    1,331 rows. A tapped ball's match_index -> its match; the
                    opponent is the team in `teams` that is not batting_team.
  columnar.json.gz  sandbox dataset: 14 parallel arrays + name dictionaries
                    (adds match_index -> matches.json, and wicket_kind, dict-
                    encoded, code 0 = "" for non-wicket balls)

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
import wallheat

# ---------------------------------------------------------------------------
# Outcome classes (contract values — also mirrored in attrs.u8 bits 0-2)
# ---------------------------------------------------------------------------

# Point-stream ordering label recorded in meta.json / columnar.json.gz.
# Not "chronological": across seasons it is, but within a shared calendar year
# IPL is deliberately placed before WPL (see sorted_match_files / the module
# docstring / R1a MF3).
POINT_ORDER = "season-blocked"

OUT_DOT = 0
OUT_SINGLE = 1
OUT_TWO_OR_THREE = 2
OUT_FOUR = 3
OUT_SIX = 4
OUT_OTHER_SCORING = 5

ATTR_WICKET_BIT = 1 << 3
ATTR_WPL_BIT = 1 << 4
# bit 5 stays reserved/zero; bit 6 (0x40) flags a run-out dismissal on this ball
# (Ch 2 run-out cascade). A spare-bit re-encode — R1 reads bits 0-4 only.
ATTR_RUNOUT_BIT = 1 << 6


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
    wkts = delivery.get("wickets")
    if wkts:
        byte |= ATTR_WICKET_BIT
        if any(w.get("kind") == "run out" for w in wkts):
            byte |= ATTR_RUNOUT_BIT  # Ch 2 run-out cascade flag (bit 6)
    if wpl:
        byte |= ATTR_WPL_BIT
    return byte


# ---------------------------------------------------------------------------
# Corpus iteration in contract order
# ---------------------------------------------------------------------------


def sorted_match_files(data_root: Path = canon.DATA_ROOT):
    """[(date0, match_id, league, path)] in season-blocked order.

    Sort key: (year of play, league rank [IPL 0 / WPL 1], date, match_id).
    Grouping by the year first, then IPL-before-WPL within the year, keeps the
    stream strictly chronological ACROSS seasons while assembling season by
    season — so within 2023 all IPL-2023 matches precede all WPL-2023 matches
    (R1a MF3 / storyboard CO-3). The year of play equals dates[0][:4] for every
    match in the corpus (canon guarantees canon_season == dates[0] year), so the
    string prefix is a safe primary key without re-deriving the season here.

    Cheap first pass: parse each file once just for its sort key, then the
    caller re-parses in order (memory stays flat; the corpus parses in <1s).
    """
    entries = []
    for league, dirname in canon.LEAGUE_DIRS:
        for path in sorted((data_root / dirname).glob("*.json")):
            with open(path) as fh:
                info = json.load(fh)["info"]
            entries.append((str(info["dates"][0]), int(path.stem), league, path))
    entries.sort(key=lambda e: (e[0][:4], 0 if e[2] == "ipl" else 1, e[0], e[1]))
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


# ---------------------------------------------------------------------------
# Matches table (R1b sandbox: tap-a-ball -> the exact match)
# ---------------------------------------------------------------------------


def match_stage(info: dict) -> str:
    """Human stage label for a match: playoff name, else 'Match N'.

    Cricsheet's event block carries a `stage` on the 82 playoff matches
    ('Final', 'Qualifier 1/2', 'Eliminator', 'Semi Final', 'Elimination
    Final', '3rd Place Play-Off') and a `match_number` on the 1,249 league
    games; the two are mutually exclusive over the corpus (82 + 1,249 =
    1,331). Stage wins when present so a tapped final reads 'Final', not a
    number.
    """
    ev = info.get("event", {})
    stage = ev.get("stage")
    if stage:
        return str(stage)
    number = ev.get("match_number")
    if number is not None:
        return f"Match {number}"
    return "Match"


def match_result_text(info: dict) -> str:
    """A one-line result sentence for the tooltip (canonical team names).

    Wins read 'Team won by N run(s)/wicket(s)'; the 23 D/L results append
    ' (D/L)'; the 17 ties name the Super-Over winner from outcome.eliminator;
    the 9 no-results read 'No result'. Team names are canonicalized so a
    tooltip's winner string matches the batting_team dictionary.
    """
    outcome = info.get("outcome", {})
    result = outcome.get("result")
    if result == "no result":
        return "No result"
    if result == "tie":
        elim = outcome.get("eliminator")
        if elim:
            return f"Match tied — {canon.canon_team(elim)} won the Super Over"
        return "Match tied"
    dl = " (D/L)" if "D/L" in (outcome.get("method") or "") else ""
    winner = outcome.get("winner")
    by = outcome.get("by", {})
    if winner and "runs" in by:
        r = by["runs"]
        return f"{canon.canon_team(winner)} won by {r} run{'' if r == 1 else 's'}{dl}"
    if winner and "wickets" in by:
        w = by["wickets"]
        return f"{canon.canon_team(winner)} won by {w} wicket{'' if w == 1 else 's'}{dl}"
    return "Result unavailable"


def match_record(info: dict, league: str) -> dict:
    """One matches.json row (fields fixed by the R1b tooltip contract).

    teams are canonical (so opponent = the team in `teams` that is not the
    tapped ball's batting_team resolves by name); city comes from the
    canonical-ground gazetteer (canon.GROUND_CITY) rather than the raw,
    sometimes-absent info.city, keeping it exhaustive and deterministic.
    """
    venue = canon.canon_venue(info["venue"])
    return {
        "teams": [canon.canon_team(t) for t in info["teams"]],
        "season": canon.canon_season(info),
        "date": str(info["dates"][0]),
        "stage": match_stage(info),
        "venue": venue,
        "city": canon.GROUND_CITY[venue],
        "result_text": match_result_text(info),
        "league": league,
    }


def build_matches(data_root: Path = canon.DATA_ROOT) -> list:
    """The matches table; matches[i] is the match whose deliveries carry
    match_index == i in the point stream.

    A light pass over info blocks only, in the SAME season-blocked order as
    build_stream (both iterate sorted_match_files), so scenes.py can resolve
    the sandbox preset's match_index without re-flattening the ball stream.
    build_stream builds the identical list inline via match_record; the tests
    assert the two agree.
    """
    matches = []
    for _date, _mid, league, path in sorted_match_files(data_root):
        with open(path) as fh:
            info = json.load(fh)["info"]
        matches.append(match_record(info, league))
    return matches


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
    cumruns = bytearray()
    team_u8 = bytearray()

    batters, bowlers, teams = DictEncoder(), DictEncoder(), DictEncoder()
    # Seed code 0 = "" so every NON-wicket ball's wicket_kind is 0 (the vast
    # majority, and it gzips to ~nothing); wicket balls carry the real kind.
    wicket_kinds = DictEncoder()
    wicket_kinds.code("")
    matches = []  # matches[match_index] == this match's record
    col = {
        "season": [], "league": [], "innings": [], "over": [],
        "ball_index_in_over": [], "batter": [], "bowler": [],
        "batting_team": [], "runs_batter": [], "runs_total": [],
        "outcome": [], "wicket": [], "wicket_kind": [], "match_index": [],
    }

    for match_index, (_date, _mid, league, path) in enumerate(
        sorted_match_files(data_root)
    ):
        with open(path) as fh:
            match = json.load(fh)
        info = match["info"]
        season = canon.canon_season(info)
        gi = gi_of[(league, season)]
        wpl = league == "wpl"
        canon.canon_venue(info["venue"])  # exhaustiveness enforced at build time
        canon.is_dl(info)
        matches.append(match_record(info, league))

        innings_no = 0
        for innings in match.get("innings", []):
            if canon.is_super_over(innings):
                continue  # standing rule: super overs never enter the stream
            innings_no += 1
            canonical_team = canon.canon_team(innings["team"])
            team_code = teams.code(canonical_team)
            franchise_id = canon.team_id(league, canonical_team)
            faced: dict[str, int] = {}
            batruns: dict[str, int] = {}  # striker -> cumulative off-the-bat runs
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
                    # Cumulative off-the-bat runs for the striker, inclusive of
                    # this ball (wides add 0 — the batter scores nothing off
                    # them, so the running total carries unchanged); cap 255.
                    r = batruns.get(dl["batter"], 0) + dl["runs"]["batter"]
                    batruns[dl["batter"]] = r
                    cumruns.append(min(r, 255))
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
                    wkts = dl.get("wickets")
                    col["wicket"].append(1 if wkts else 0)
                    col["wicket_kind"].append(
                        wicket_kinds.code(wkts[0]["kind"]) if wkts else 0
                    )
                    col["match_index"].append(match_index)

    dicts = {
        "batter": batters.names,
        "bowler": bowlers.names,
        "batting_team": teams.names,
        "wicket_kind": wicket_kinds.names,
    }
    return groups, group_ids, attrs, col, dicts, ballsfaced, cumruns, team_u8, matches


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


INNINGS_TOTAL_SCALE = 2  # byte = floor(innings_total / 2); decode total ~= byte*2


def innings_totals(col: dict) -> bytearray:
    """Per-point innings-total buffer for the Chapter 4 waterline morph.

    byte[i] = floor(T / INNINGS_TOTAL_SCALE), clamped to 255, where T is the
    final total (sum of runs.total) of the innings point i belongs to. Derived
    entirely from the columnar arrays already built this pass — no extra corpus
    read — keyed by (match_index, innings). Constant within an innings, so the
    2-run quantization is invisible in the morph and the buffer gzips small.
    """
    mi = col["match_index"]
    inn = col["innings"]
    rt = col["runs_total"]
    totals: dict[tuple[int, int], int] = {}
    for i in range(len(mi)):
        key = (mi[i], inn[i])
        totals[key] = totals.get(key, 0) + rt[i]
    buf = bytearray(len(mi))
    for i in range(len(mi)):
        buf[i] = min(totals[(mi[i], inn[i])] // INNINGS_TOTAL_SCALE, 255)
    return buf


def main(out_root: Path = canon.OUT_ROOT) -> dict:
    groups, group_ids, attrs, col, dicts, ballsfaced, cumruns, team_u8, matches = (
        build_stream()
    )
    n_points = len(attrs)
    assert len(group_ids) == n_points
    assert all(len(v) == n_points for v in col.values())
    assert sum(g["count"] for g in groups) == n_points
    assert len(ballsfaced) == n_points
    assert len(cumruns) == n_points
    assert len(team_u8) == n_points
    # Every match_index indexes a real match (0 <= mi < |matches|); the table
    # spans the whole corpus. The stronger "inline table == build_matches()"
    # equivalence and the 1,331 count are asserted in tests/test_r1b.py.
    assert 0 <= min(col["match_index"])
    assert max(col["match_index"]) < len(matches)

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

    # Ch 1 ignition-wall era-relative-intent buffer (thesis-beat recolour).
    # Computed off the arrays this pass already built — no re-read (see
    # wallheat.py); scenes.py emits the matching scale/legend into ch1.json.
    wallheat_bytes, _wallheat_cfg = wallheat.compute(
        col["league"], col["season"], ballsfaced, col["runs_batter"]
    )
    assert len(wallheat_bytes) == n_points

    # Ch 4 waterline morph coordinate: each ball's innings total (quantized).
    # Built from this pass's columnar arrays; no extra corpus read.
    innings_total_bytes = innings_totals(col)
    assert len(innings_total_bytes) == n_points

    emit("groups.json", compact_json(groups))
    emit("group_ids.u16", group_ids.tobytes())
    emit("attrs.u8", bytes(attrs))
    emit("ballsfaced.u8", bytes(ballsfaced))
    emit("cumruns.u8", bytes(cumruns))
    emit("team.u8", bytes(team_u8))
    emit("wallheat.u8", bytes(wallheat_bytes))
    emit("innings_total.u8", bytes(innings_total_bytes))
    emit("teams.json", compact_json(list(canon.TEAMS), sort_keys=True))
    # matches[match_index] -> the exact match a tapped ball belongs to (R1b
    # tooltip). List order IS match_index, so the list is never re-sorted;
    # sort_keys only orders each record's keys for byte-determinism.
    emit("matches.json", compact_json(matches, sort_keys=True))
    emit(
        "columnar.json.gz",
        compact_json(
            {
                "n_points": n_points,
                "point_order": POINT_ORDER,
                "arrays": col,
                "dicts": dicts,
            }
        ),
        pregzipped=True,
    )

    meta = {
        "n_points": n_points,
        "built_at": "unknown",
        "point_order": POINT_ORDER,
        "files": files,
    }
    (out_root / "meta.json").write_bytes(compact_json(meta))

    print(f"n_points={n_points}  groups={len(groups)}")
    for name, sizes in files.items():
        print(f"  {name:18s} raw={sizes['bytes_raw']:>10,}  gz={sizes['bytes_gz']:>9,}")
    return meta


if __name__ == "__main__":
    main()
