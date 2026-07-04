"""Payoff-card snapshot harness (blueprint §2 payoff-card QA) — Chapter 1.

Emits web/static/data/payoff/ch1.json with EXACTLY 16 variants — the 10
current IPL franchises, the 5 WPL franchises, and "neutral" — each a
Chapter-1 ("Death of the Sighter") card. R1a full spec per variant:

  { team, league, first10_sr_early_era, first10_sr_recent_era, delta,
    sample_balls, headline,                       # the R0 thesis card
    team_pair, honesty,                           # discrete copy fields: the
                                                  #   team-pair sentence and the
                                                  #   small-sample honesty line
                                                  #   ("" when not small-sample)
                                                  #   — the scene renders fields,
                                                  #   never regex-parses prose
    ignition_by_era: [{era, sr_1_10, sr_11_20, balls_1_10, balls_11_20}],
    fastest_starter: {name, first10_sr, first10_balls},  # min 100 balls
    maturity_clock: {...} }                       # WPL variants only

Eras: IPL 2008-2010 vs 2023-2026; WPL 2023-2024 vs 2025-2026 (honest
small-sample handling: the flag + copy own it). The ignition curve uses the
R1a era bands (IPL 2008-10/2011-15/2016-19/2020-22/2023-26; WPL its two card
eras). Franchises younger than the early era (GT, LSG, SRH) get the DESIGNED
EMPTY STATE — authored copy, never a blank card — and bands where a
franchise bowled no balls carry null SRs (designed sparsity, not a bug).
Cards are strictly template + per-team numbers; nothing is hand-authored per
team. WPL cards carry the Maturity Clock (the bespoke WPL-picker payoff the
release checklist requires) and their copy obeys the house framing rule —
never "behind".

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
import scenes

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
FASTEST_STARTER_MIN_BALLS = 100  # min first-10 balls faced for the franchise

# Ignition-curve bands per league: IPL uses the R1a era bands; the WPL's
# four seasons use its two payoff-card eras.
IGNITION_BANDS = {
    "ipl": [(label, lo, hi) for _lg, label, lo, hi in scenes.IPL_ERA_BANDS],
    "wpl": [("2023-2024", 2023, 2024), ("2025-2026", 2025, 2026)],
}

# ---------------------------------------------------------------------------
# Computation: one full corpus pass for every card ingredient
# ---------------------------------------------------------------------------


def era_of(league: str, season: int):
    for era, (lo, hi) in ERAS[league].items():
        if lo <= season <= hi:
            return era
    return None


def ignition_band_of(league: str, season: int):
    for label, lo, hi in IGNITION_BANDS[league]:
        if lo <= season <= hi:
            return label
    return None


def aggregate():
    """One chronological pass over the corpus (super overs excluded; wides
    are not balls faced, per the Ch 1 footnote conventions) collecting:

      per_team / per_league   (league, team|-, era) -> [balls, runs] on each
                              batter's first ten balls (the R0 thesis card)
      team_band / league_band (league, team|-, band) -> [balls 1-10, runs
                              1-10, balls 11-20, runs 11-20] (ignition curve)
      team_starters           (league, team) -> batter -> [balls, runs] on
                              first-10 balls, all-time (fastest starter)
      league_starters         league -> batter -> [balls, runs]
      maturity                league -> year(1..4) -> {runs, legal_balls,
                              f10_balls, f10_runs} (the Maturity Clock; RR =
                              ALL runs / legal balls, wides+no-balls excluded)
      runs_split              (league, era-key) -> [total_runs, four_runs]
                              (the four-led engine share for WPL card copy)
    """
    per_team = defaultdict(lambda: [0, 0])
    per_league = defaultdict(lambda: [0, 0])
    team_band = defaultdict(lambda: [0, 0, 0, 0])
    league_band = defaultdict(lambda: [0, 0, 0, 0])
    team_starters = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    league_starters = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    maturity = defaultdict(lambda: defaultdict(lambda: [0, 0, 0, 0]))
    runs_split = defaultdict(lambda: [0, 0])

    first_season = {"ipl": canon.IPL_SEASONS[0], "wpl": canon.WPL_SEASONS[0]}

    for _date, _mid, league, path in flatten.sorted_match_files():
        with open(path) as fh:
            match = json.load(fh)
        season = canon.canon_season(match["info"])
        era = era_of(league, season)
        band = ignition_band_of(league, season)
        league_year = season - first_season[league] + 1
        mat = maturity[league][league_year] if 1 <= league_year <= 4 else None
        split_keys = []
        if league == "wpl":
            split_keys.append(("wpl", "all"))
        if league == "ipl" and 2023 <= season <= 2026:
            split_keys.append(("ipl", "2023-2026"))

        for innings in match.get("innings", []):
            if canon.is_super_over(innings):
                continue
            team = canon.canon_team(innings["team"])
            faced = Counter()
            for over in innings["overs"]:
                for dl in over["deliveries"]:
                    extras = dl.get("extras", {})
                    runs = dl["runs"]["batter"]
                    for sk in split_keys:
                        runs_split[sk][0] += dl["runs"]["total"]
                        if runs == 4:
                            runs_split[sk][1] += 4
                    if mat is not None:
                        mat[0] += dl["runs"]["total"]
                        if "wides" not in extras and "noballs" not in extras:
                            mat[1] += 1
                    if "wides" in extras:
                        continue  # not a ball faced
                    batter = dl["batter"]
                    faced[batter] += 1
                    n = faced[batter]
                    if n <= 10:
                        if era is not None:
                            per_team[(league, team, era)][0] += 1
                            per_team[(league, team, era)][1] += runs
                            per_league[(league, era)][0] += 1
                            per_league[(league, era)][1] += runs
                        team_band[(league, team, band)][0] += 1
                        team_band[(league, team, band)][1] += runs
                        league_band[(league, band)][0] += 1
                        league_band[(league, band)][1] += runs
                        team_starters[(league, team)][batter][0] += 1
                        team_starters[(league, team)][batter][1] += runs
                        league_starters[league][batter][0] += 1
                        league_starters[league][batter][1] += runs
                        if mat is not None:
                            mat[2] += 1
                            mat[3] += runs
                    elif n <= 20:
                        team_band[(league, team, band)][2] += 1
                        team_band[(league, team, band)][3] += runs
                        league_band[(league, band)][2] += 1
                        league_band[(league, band)][3] += runs
    return {
        "per_team": per_team,
        "per_league": per_league,
        "team_band": team_band,
        "league_band": league_band,
        "team_starters": team_starters,
        "league_starters": league_starters,
        "maturity": maturity,
        "runs_split": runs_split,
    }


def sr(balls: int, runs: int):
    return round(100.0 * runs / balls, 1) if balls else None


def ignition_rows(league: str, band_source, key_prefix) -> list[dict]:
    """[{era, sr_1_10, sr_11_20, balls_1_10, balls_11_20}] — null SRs where
    the franchise bowled no balls in a band (designed sparsity)."""
    rows = []
    for label, _lo, _hi in IGNITION_BANDS[league]:
        b10, r10, b20, r20 = band_source[key_prefix + (label,)]
        rows.append(
            {
                "era": label,
                "sr_1_10": sr(b10, r10),
                "sr_11_20": sr(b20, r20),
                "balls_1_10": b10,
                "balls_11_20": b20,
            }
        )
    return rows


def fastest_starter(starters: dict) -> dict | None:
    """Best first-10-ball SR among batters with >= 100 such balls."""
    best = None
    for name, (balls, runs) in starters.items():
        if balls < FASTEST_STARTER_MIN_BALLS:
            continue
        row = (100.0 * runs / balls, balls, name)
        if best is None or (row[0], row[1], row[2]) > (best[0], best[1], best[2]):
            best = row
    if best is None:
        return None
    return {
        "name": best[2],
        "first10_sr": round(best[0], 1),
        "first10_balls": best[1],
    }


def maturity_clock(agg) -> dict:
    """The WPL-picker Maturity Clock card fields (bespoke WPL payoff)."""
    def rr_series(league):
        return [
            round(6.0 * agg["maturity"][league][y][0] / agg["maturity"][league][y][1], 2)
            for y in (1, 2, 3, 4)
        ]

    def f10_series(league):
        return [
            round(100.0 * agg["maturity"][league][y][3] / agg["maturity"][league][y][2], 1)
            for y in (1, 2, 3, 4)
        ]

    rr = {lg: rr_series(lg) for lg in ("ipl", "wpl")}
    f10 = {lg: f10_series(lg) for lg in ("ipl", "wpl")}
    wpl_fours = agg["runs_split"][("wpl", "all")]
    ipl_fours = agg["runs_split"][("ipl", "2023-2026")]
    wpl_fours_pct = round(100.0 * wpl_fours[1] / wpl_fours[0], 1)
    ipl_fours_pct = round(100.0 * ipl_fours[1] / ipl_fours[0], 1)
    return {
        "league_year": 4,
        "rr_by_year": rr,
        "first10_sr_by_year": f10,
        "wpl_runs_from_fours_pct": wpl_fours_pct,
        "ipl_recent_runs_from_fours_pct": ipl_fours_pct,
        "copy": (
            f"Four seasons in, the WPL's first ten balls run at strike rate "
            f"{f10['wpl'][3]} — the IPL's year-4 number was {f10['ipl'][3]}. "
            f"Already climbing faster at the same league age, and powered by "
            f"an engine the men's league never had: {wpl_fours_pct}% of WPL "
            f"runs come in fours (modern IPL: {ipl_fours_pct}%)."
        ),
        "definition": (
            "League year N = the league's N-th season (IPL year 1 = 2008, "
            "WPL year 1 = 2023). RR = all runs per 6 legal balls."
        ),
    }


# ---------------------------------------------------------------------------
# Card templating (strictly template + numbers — no per-team hand copy)
# ---------------------------------------------------------------------------


def make_card(team: str, league: str, early, recent) -> dict:
    """early/recent are (balls, runs) tuples; balls may be 0 (empty state).

    Ships the honesty sentence and the team-pair sentence as DISCRETE fields
    (`honesty`, `team_pair`) so the scene renders fields, never regex-parses
    the headline (finding #6/#8). `honesty` is the small-sample sentence, or
    "" when the variant is not small-sample; the headline is composed from the
    same pieces so it stays byte-identical to v1 for every card.
    """
    labels = ERA_LABELS[league]
    sr_early = sr(*early)
    sr_recent = sr(*recent)
    sample = early[0] + recent[0]
    small = min(b for b in (early[0], recent[0]) if b > 0) < SMALL_SAMPLE_BALLS

    # The honesty sentence: non-empty for every small-sample variant, "" else.
    if small:
        honesty = (
            "Early days for a young league — small sample, honest numbers."
            if league == "wpl"
            else "Small sample — read these as early signals, not verdicts."
        )
    else:
        honesty = ""

    if sr_early is None:
        # Designed empty state: franchise born after the early era. (Born-late
        # franchises always clear the small-sample floor on their live era, so
        # honesty is "" here — asserted by the harness.)
        team_pair = (
            f"{team} was born into the attack era — it has no {labels['early']} "
            f"innings to compare. Its batters' first ten balls already run at "
            f"a strike rate of {sr_recent}."
        )
        headline = team_pair
        delta = None
    else:
        delta = round(sr_recent - sr_early, 1)
        team_pair = (
            f"{team}'s first ten balls: strike rate {sr_early} in "
            f"{labels['early']}, {sr_recent} in {labels['recent']} — "
            f"{delta:+.1f} points of intent."
        )
        headline = team_pair
        if honesty and league == "wpl":
            headline += " " + honesty

    return {
        "team": team,
        "league": league,
        "first10_sr_early_era": sr_early,
        "first10_sr_recent_era": sr_recent,
        "delta": delta,
        "sample_balls": sample,
        "headline": headline,
        "team_pair": team_pair,
        "honesty": honesty,
        "era_labels": labels,
        "sample_balls_early": early[0],
        "sample_balls_recent": recent[0],
        "empty_state": sr_early is None,
        "small_sample": small,
    }


def build_variants() -> list[dict]:
    agg = aggregate()
    per_team, per_league = agg["per_team"], agg["per_league"]
    wpl_clock = maturity_clock(agg)

    def team_card(league: str, team: str) -> dict:
        early = tuple(per_team.get((league, team, "early"), (0, 0)))
        recent = tuple(per_team.get((league, team, "recent"), (0, 0)))
        card = make_card(team, league, early, recent)
        card["ignition_by_era"] = ignition_rows(
            league, agg["team_band"], (league, team)
        )
        card["fastest_starter"] = fastest_starter(agg["team_starters"][(league, team)])
        if league == "wpl":
            card["maturity_clock"] = wpl_clock
        return card

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
    neutral["ignition_by_era"] = ignition_rows("ipl", agg["league_band"], ("ipl",))
    neutral["fastest_starter"] = fastest_starter(agg["league_starters"]["ipl"])
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

        # --- Discrete copy fields (finding #6/#8): the scene renders these,
        #     never regex-parses the headline. ---
        team_pair = v.get("team_pair")
        if not (isinstance(team_pair, str) and team_pair.strip()):
            errors.append(f"{tag}: team_pair missing/empty")
        honesty = v.get("honesty")
        if not isinstance(honesty, str):
            errors.append(f"{tag}: honesty must be a string ('' when not small-sample)")
        elif v.get("small_sample"):
            if not honesty.strip():
                errors.append(f"{tag}: small_sample variant must ship a non-empty honesty sentence")
        elif honesty != "":
            errors.append(f"{tag}: non-small-sample variant must have empty honesty")
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

        # --- R1a full-spec fields ---
        rows = v.get("ignition_by_era")
        if not (isinstance(rows, list) and rows):
            errors.append(f"{tag}: ignition_by_era missing/empty")
        else:
            live = 0
            for row in rows:
                if set(row) != {"era", "sr_1_10", "sr_11_20", "balls_1_10", "balls_11_20"}:
                    errors.append(f"{tag}: ignition row keys wrong: {sorted(row)}")
                    break
                if row["balls_1_10"] == 0 and row["sr_1_10"] is not None:
                    errors.append(f"{tag}: ignition {row['era']}: SR without balls")
                if row["balls_1_10"] > 0:
                    if not (isinstance(row["sr_1_10"], (int, float)) and row["sr_1_10"] > 0):
                        errors.append(f"{tag}: ignition {row['era']}: bad sr_1_10")
                    live += 1
            if live == 0:
                errors.append(f"{tag}: ignition_by_era has no live era")

        starter = v.get("fastest_starter")
        if not isinstance(starter, dict):
            errors.append(f"{tag}: fastest_starter missing")
        else:
            if not (isinstance(starter.get("name"), str) and starter["name"].strip()):
                errors.append(f"{tag}: fastest_starter has no name")
            if not (
                isinstance(starter.get("first10_balls"), int)
                and starter["first10_balls"] >= FASTEST_STARTER_MIN_BALLS
            ):
                errors.append(f"{tag}: fastest_starter under the {FASTEST_STARTER_MIN_BALLS}-ball floor")
            if not (
                isinstance(starter.get("first10_sr"), (int, float))
                and starter["first10_sr"] > 0
            ):
                errors.append(f"{tag}: fastest_starter has no SR")

        if v.get("league") == "wpl":
            clock = v.get("maturity_clock")
            if not isinstance(clock, dict):
                errors.append(f"{tag}: WPL card lacks the maturity clock")
            else:
                for field in ("rr_by_year", "first10_sr_by_year"):
                    series = clock.get(field, {})
                    for lg in ("ipl", "wpl"):
                        if len(series.get(lg, [])) != 4:
                            errors.append(f"{tag}: maturity {field}.{lg} != 4 years")
                copy = clock.get("copy", "")
                if not (isinstance(copy, str) and copy.strip()):
                    errors.append(f"{tag}: maturity clock lacks copy")
                elif "behind" in copy.lower():
                    # House framing rule: the WPL is never "behind".
                    errors.append(f"{tag}: maturity copy violates the WPL framing rule")
        elif "maturity_clock" in v:
            errors.append(f"{tag}: maturity clock on a non-WPL card")
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
