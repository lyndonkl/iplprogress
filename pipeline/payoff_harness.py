"""Payoff-card snapshot harness (blueprint §2 payoff-card QA) — Chapter 1.

Emits web/static/data/payoff/ch1.json with EXACTLY 16 variants — the 10
current IPL franchises, the 5 WPL franchises, and "neutral" — each a
Chapter-1 ("Death of the Sighter") card:

  { team, league, first10_sr_early_era, first10_sr_recent_era, delta,
    sample_balls, headline, ... }

Eras: IPL 2008-2010 vs 2023-2026; WPL 2023-2024 vs 2025-2026 (honest
small-sample handling: the flag + copy own it). Franchises younger than the
early era (GT, LSG, SRH) get the DESIGNED EMPTY STATE — authored copy, never
a blank card. Cards are strictly template + per-team numbers; nothing is
hand-authored per team.

The harness then ASSERTS all 16 variants exist and are non-degenerate and
exits non-zero on any failure. Run after flatten.py (it updates meta.json's
file ledger with the card's sizes).
"""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import canon
import flatten

CH1_PATH = canon.OUT_ROOT / "payoff" / "ch1.json"

ERAS = {
    "ipl": {"early": (2008, 2010), "recent": (2023, 2026)},
    "wpl": {"early": (2023, 2024), "recent": (2025, 2026)},
}
ERA_LABELS = {
    "ipl": {"early": "2008-2010", "recent": "2023-2026"},
    "wpl": {"early": "2023-2024", "recent": "2025-2026"},
}
SMALL_SAMPLE_BALLS = 1500  # per-era first-10 balls under this -> honesty flag

# ---------------------------------------------------------------------------
# Computation: first-10-ball strike rate per (league, team, era)
# ---------------------------------------------------------------------------


def era_of(league: str, season: int):
    for era, (lo, hi) in ERAS[league].items():
        if lo <= season <= hi:
            return era
    return None


def aggregate():
    """(league, team, era) and (league, era) -> [balls, batter_runs] over each
    batter's first ten balls faced of an innings (wides don't count as a
    ball faced, per the Ch 1 footnote conventions; super overs excluded)."""
    per_team = defaultdict(lambda: [0, 0])
    per_league = defaultdict(lambda: [0, 0])
    for _date, _mid, league, path in flatten.sorted_match_files():
        with open(path) as fh:
            match = json.load(fh)
        season = canon.canon_season(match["info"])
        era = era_of(league, season)
        if era is None:
            continue
        for innings in match.get("innings", []):
            if canon.is_super_over(innings):
                continue
            team = canon.canon_team(innings["team"])
            faced = Counter()
            for over in innings["overs"]:
                for dl in over["deliveries"]:
                    if "wides" in dl.get("extras", {}):
                        continue  # not a ball faced
                    batter = dl["batter"]
                    if faced[batter] < 10:
                        runs = dl["runs"]["batter"]
                        per_team[(league, team, era)][0] += 1
                        per_team[(league, team, era)][1] += runs
                        per_league[(league, era)][0] += 1
                        per_league[(league, era)][1] += runs
                    faced[batter] += 1
    return per_team, per_league


def sr(balls: int, runs: int):
    return round(100.0 * runs / balls, 1) if balls else None


# ---------------------------------------------------------------------------
# Card templating (strictly template + numbers — no per-team hand copy)
# ---------------------------------------------------------------------------


def make_card(team: str, league: str, early, recent) -> dict:
    """early/recent are (balls, runs) tuples; balls may be 0 (empty state)."""
    labels = ERA_LABELS[league]
    sr_early = sr(*early)
    sr_recent = sr(*recent)
    sample = early[0] + recent[0]
    small = min(b for b in (early[0], recent[0]) if b > 0) < SMALL_SAMPLE_BALLS

    if sr_early is None:
        # Designed empty state: franchise born after the early era.
        headline = (
            f"{team} was born into the attack era — it has no {labels['early']} "
            f"innings to compare. Its batters' first ten balls already run at "
            f"a strike rate of {sr_recent}."
        )
        delta = None
    else:
        delta = round(sr_recent - sr_early, 1)
        headline = (
            f"{team}'s first ten balls: strike rate {sr_early} in "
            f"{labels['early']}, {sr_recent} in {labels['recent']} — "
            f"{delta:+.1f} points of intent."
        )
        if small and league == "wpl":
            headline += " Early days for a young league — small sample, honest numbers."

    return {
        "team": team,
        "league": league,
        "first10_sr_early_era": sr_early,
        "first10_sr_recent_era": sr_recent,
        "delta": delta,
        "sample_balls": sample,
        "headline": headline,
        "era_labels": labels,
        "sample_balls_early": early[0],
        "sample_balls_recent": recent[0],
        "empty_state": sr_early is None,
        "small_sample": small,
    }


def build_variants() -> list[dict]:
    per_team, per_league = aggregate()

    def team_card(league: str, team: str) -> dict:
        early = tuple(per_team.get((league, team, "early"), (0, 0)))
        recent = tuple(per_team.get((league, team, "recent"), (0, 0)))
        return make_card(team, league, early, recent)

    variants = [team_card("ipl", t) for t in canon.CURRENT_IPL_FRANCHISES]
    variants += [team_card("wpl", t) for t in canon.WPL_FRANCHISES]

    # Neutral: the league-wide thesis numbers (all IPL innings pooled).
    ne, nr = per_league[("ipl", "early")], per_league[("ipl", "recent")]
    neutral = make_card("Neutral", "ipl", tuple(ne), tuple(nr))
    neutral["headline"] = (
        f"Across every IPL innings ever bowled, a batter's first ten balls ran at "
        f"strike rate {neutral['first10_sr_early_era']} in 2008-2010 and "
        f"{neutral['first10_sr_recent_era']} in 2023-2026 — "
        f"{neutral['delta']:+.1f}. The sighter is dead."
    )
    variants.append(neutral)
    return variants


# ---------------------------------------------------------------------------
# Snapshot assertions (non-zero exit on any failure)
# ---------------------------------------------------------------------------


def assert_non_degenerate(doc: dict) -> list[str]:
    errors = []
    variants = doc.get("variants", [])
    if len(variants) != 16:
        errors.append(f"expected exactly 16 variants, got {len(variants)}")

    expected = (
        {("ipl", t) for t in canon.CURRENT_IPL_FRANCHISES}
        | {("wpl", t) for t in canon.WPL_FRANCHISES}
        | {("ipl", "Neutral")}
    )
    got = {(v.get("league"), v.get("team")) for v in variants}
    if got != expected:
        errors.append(f"variant set mismatch: missing={expected - got} extra={got - expected}")

    for v in variants:
        tag = f"{v.get('league')}/{v.get('team')}"
        if not (isinstance(v.get("sample_balls"), int) and v["sample_balls"] > 0):
            errors.append(f"{tag}: sample_balls must be > 0")
        headline = v.get("headline")
        if not (isinstance(headline, str) and headline.strip()):
            errors.append(f"{tag}: headline missing/empty")
        recent = v.get("first10_sr_recent_era")
        if not (isinstance(recent, (int, float)) and recent > 0):
            errors.append(f"{tag}: first10_sr_recent_era missing")
        if v.get("empty_state"):
            # A designed empty state is non-degenerate ONLY with authored copy.
            if v.get("first10_sr_early_era") is not None:
                errors.append(f"{tag}: empty_state with an early-era number")
            if not (headline and "born into the attack era" in headline):
                errors.append(f"{tag}: empty_state lacks authored copy")
        else:
            early, delta = v.get("first10_sr_early_era"), v.get("delta")
            if not (isinstance(early, (int, float)) and early > 0):
                errors.append(f"{tag}: first10_sr_early_era missing")
            elif not (
                isinstance(delta, (int, float))
                and abs(delta - round(recent - early, 1)) < 1e-9
            ):
                errors.append(f"{tag}: delta {delta} != recent-early")
    return errors


def main() -> int:
    doc = {
        "chapter": 1,
        "card": "death-of-the-sighter",
        "eras": ERA_LABELS,
        "variants": build_variants(),
    }
    CH1_PATH.parent.mkdir(parents=True, exist_ok=True)
    raw = flatten.compact_json(doc)
    CH1_PATH.write_bytes(raw)

    # Assert against what actually landed on disk, not the in-memory object.
    errors = assert_non_degenerate(json.loads(CH1_PATH.read_text()))
    if errors:
        print("PAYOFF HARNESS FAILED:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    # Record the card in meta.json's file ledger (flatten owns the rest).
    meta_path = canon.OUT_ROOT / "meta.json"
    if meta_path.exists():
        meta = json.loads(meta_path.read_text())
        meta["files"]["payoff/ch1.json"] = {
            "bytes_raw": len(raw),
            "bytes_gz": len(flatten.gz_bytes(raw)),
        }
        meta_path.write_bytes(flatten.compact_json(meta))

    n_empty = sum(1 for v in doc["variants"] if v["empty_state"])
    print(
        f"16/16 payoff variants pass ({n_empty} designed empty states) "
        f"-> {CH1_PATH.relative_to(canon.REPO_ROOT)} ({len(raw):,} bytes raw)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
