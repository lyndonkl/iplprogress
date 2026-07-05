"""Engine #5 (full) — entry states / derived batting positions (R2a, Ch 2).

For every batter-innings the entry EVENT is the batter's first delivery as
striker OR non_striker. At that moment we record the entry STATE:

  * entry_ball   — legal-ball index of the innings when the batter walked in
                   (legal ball = not a wide and not a no-ball, matching the
                   over structure and target.overs x 6; openers enter at 0).
  * wickets      — wickets fallen before the batter entered (0 for openers).
  * innings      — 1 or 2 (super-over innings excluded, standing rule).
  * position     — derived batting position = order of entry (the two openers
                   are positions 1 and 2, striker first, then 3, 4, ...).
  * rrr          — required run rate at entry, CHASES ONLY (innings 2 with a
                   target): (target.runs - score) x 6 / (balls remaining),
                   where balls remaining = target.overs x 6 - entry_ball. null
                   for first innings and the rare chase with no target field.

Plus the batter-innings outcome so the table is self-sufficient for the
"performance conditional on entry" surfaces (Ch 2 archetypes, Ch 5 finisher
supply, the sandbox entry map): balls_faced (SR convention: wides excluded,
no-balls counted), runs (runs.batter), and dismissed (a real dismissal of this
batter fell — retired hurt/out are NOT dismissals).

Emitted compact + columnar to engines/entry.json. Stdlib only.
Byte-deterministic. Writes only under web/static/data/engines/.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import canon
import flatten

ENGINES_DIR = canon.OUT_ROOT / "engines"

RETIRED_KINDS = frozenset({"retired hurt", "retired out"})  # not dismissals


def is_legal(dl: dict) -> bool:
    """A ball that counts toward the over (wides and no-balls do not)."""
    extras = dl.get("extras", {})
    return "wides" not in extras and "noballs" not in extras


def build(data_root: Path = canon.DATA_ROOT):
    """One chronological pass emitting one record per batter-innings, in the
    same match order as flatten (so match_index aligns with matches.json)."""
    records = []
    for match_index, (_d, _m, league, path) in enumerate(
        flatten.sorted_match_files(data_root)
    ):
        with open(path) as fh:
            match = json.load(fh)
        info = match["info"]
        season = canon.canon_season(info)

        innings_no = 0
        for innings in match.get("innings", []):
            if canon.is_super_over(innings):
                continue
            innings_no += 1
            target = innings.get("target") or {}
            target_runs = target.get("runs")
            target_overs = target.get("overs")

            entries: dict = {}       # batter -> its record (entry state + tally)
            order: list = []         # batters in entry order (position)
            legal = 0                # legal balls bowled so far
            wickets = 0              # wickets fallen so far
            score = 0                # team total runs so far

            for over in innings["overs"]:
                for dl in over["deliveries"]:
                    # Entry event: first appearance as striker or non_striker,
                    # priced by the state BEFORE this delivery is played.
                    for who in (dl["batter"], dl["non_striker"]):
                        if who in entries:
                            continue
                        position = len(order) + 1
                        order.append(who)
                        rrr = None
                        if (innings_no == 2 and target_runs is not None
                                and target_overs is not None):
                            balls_remaining = int(round(float(target_overs) * 6)) - legal
                            if balls_remaining > 0:
                                rrr = (target_runs - score) * 6.0 / balls_remaining
                        entries[who] = {
                            "batter": who,
                            "position": position,
                            "entry_ball": legal,
                            "wickets": wickets,
                            "rrr": rrr,
                            "balls_faced": 0,
                            "runs": 0,
                            "dismissed": 0,
                        }

                    # The striker faces the ball (SR convention: wides are not
                    # faced, no-balls are).
                    if "wides" not in dl.get("extras", {}):
                        rec = entries[dl["batter"]]
                        rec["balls_faced"] += 1
                        rec["runs"] += dl["runs"]["batter"]

                    # Advance the innings state.
                    score += dl["runs"]["total"]
                    if is_legal(dl):
                        legal += 1
                    for w in dl.get("wickets", []):
                        if w["kind"] in RETIRED_KINDS:
                            continue
                        wickets += 1
                        po = w.get("player_out")
                        if po in entries:
                            entries[po]["dismissed"] = 1

            for who in order:
                rec = entries[who]
                records.append((league, season, match_index, innings_no, rec))
    return records


# ---------------------------------------------------------------------------
# Emission
# ---------------------------------------------------------------------------


def entry_doc(records) -> dict:
    batters = flatten.DictEncoder()
    cols = {
        "league": [], "season": [], "match_index": [], "innings": [],
        "batter": [], "position": [], "entry_ball": [], "wickets": [],
        "rrr": [], "balls_faced": [], "runs": [], "dismissed": [],
    }
    for league, season, match_index, innings_no, rec in records:
        cols["league"].append(1 if league == "wpl" else 0)
        cols["season"].append(season)
        cols["match_index"].append(match_index)
        cols["innings"].append(innings_no)
        cols["batter"].append(batters.code(rec["batter"]))
        cols["position"].append(rec["position"])
        cols["entry_ball"].append(rec["entry_ball"])
        cols["wickets"].append(rec["wickets"])
        cols["rrr"].append(round(rec["rrr"], 3) if rec["rrr"] is not None else None)
        cols["balls_faced"].append(rec["balls_faced"])
        cols["runs"].append(rec["runs"])
        cols["dismissed"].append(rec["dismissed"])
    return {
        "engine": "5 (full) — entry states / derived batting positions",
        "definition": {
            "entry_event": "first delivery as striker or non_striker",
            "entry_ball": (
                "legal-ball index of the innings at entry (wides and no-balls "
                "excluded); openers enter at 0"
            ),
            "wickets": "wickets fallen before entry (retired hurt/out not counted)",
            "position": "derived batting position = order of entry (openers 1,2 striker-first)",
            "rrr": (
                "required run rate at entry, chases only (innings 2 with a "
                "target): (target.runs - score) x 6 / (target.overs x 6 - "
                "entry_ball); null otherwise"
            ),
            "balls_faced": "balls faced by the batter in the innings (wides excluded, no-balls counted)",
            "runs": "runs.batter scored by the batter in the innings",
            "dismissed": "1 if a real dismissal of this batter fell (retired hurt/out excluded)",
            "league_code": "0 = ipl, 1 = wpl",
            "match_index": "row into matches.json (== point-stream match order)",
        },
        "count": len(records),
        "dicts": {"batter": batters.names},
        "arrays": cols,
    }


def main(out_root: Path = canon.OUT_ROOT) -> dict:
    records = build()
    doc = entry_doc(records)
    engines_dir = out_root / "engines"
    engines_dir.mkdir(parents=True, exist_ok=True)
    raw = flatten.compact_json(doc, sort_keys=True)
    (engines_dir / "entry.json").write_bytes(raw)
    gz = len(flatten.gz_bytes(raw))
    print(f"  engines/entry.json     raw={len(raw):>9,}  gz={gz:>8,}")

    a = doc["arrays"]
    openers = sum(1 for p in a["position"] if p in (1, 2))
    chases = sum(1 for r in a["rrr"] if r is not None)
    print(
        f"entry batter-innings: {doc['count']:,}  openers(pos 1-2)={openers:,}  "
        f"chase-entries(rrr set)={chases:,}  batters={len(doc['dicts']['batter']):,}"
    )
    return doc


if __name__ == "__main__":
    main()
