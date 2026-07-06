"""R3b — the Net Session interlude scene (scenes/interlude.json).

The two-dial teaching widget placed between Chapter 4 and Chapter 5. It reads
the GATE-VALIDATED engine grids and re-shapes them for the widget the reader
drives by hand:

  * a WIN meter  — "how often teams win from here" — reads engine #3's
    second-innings P(chase win) grid (engines/wp_grid.json), and
  * an EXPECTED-RUNS meter — "how many runs a team usually still gets" — reads
    engine #2's run-expectancy surface (engines/re288.json).

Both dials read PRECOMPUTED lookups (never a live model — the locked decision).
The widget interpolates client-side; this module only samples, re-indexes to a
single widget-native coordinate, and packages the presets + copy.

This module CONSUMES the engines, it never rebuilds or modifies them — the
§5 engine-validation gate (tests/test_engines.py) owns their correctness, and
this scene's tests only assert the scene faithfully re-projects them. If the
engine JSONs are absent it triggers their builders (re288.main / wp.main), the
same bootstrap the gate uses.

What is emitted (scenes/interlude.json)
---------------------------------------
1. state_space + index — the widget coordinate. Both meters index by
   [overs_left-1][wickets_in_hand-1]; the win meter adds a required-rate bucket
   computed from runs_needed. The win grid is copied native from wp_grid; the
   runs grid is RE-INDEXED from (overs bowled, wickets fallen) into the same
   (overs_left, wickets_in_hand) order so the widget uses one coordinate.

2. surfaces.win / surfaces.runs — per era band, plus a pooled default and the
   WPL surface. win[era] is 20x10x10 (P(chase win)); runs[era] is 20x10
   (expected runs from here). The RE288 engine ships no IPL-pooled runs surface,
   so a pooled default is DERIVED here (evidence-weighted mean of the five era
   surfaces, monotone-repaired with the engine's own isotonic step) and labelled
   as derived.

3. surfaces.win_n / surfaces.runs_n — the per-cell count of real chases/innings
   behind every cell, exposed for BOTH leagues at one threshold (win n<12, runs
   n<15). This is the honesty-parity fix (§0.1): the widget flags a thin IPL
   free-play cell exactly as it hatches a thin WPL one, so a shrinkage artifact
   is never printed as an observed finding in either league.

4. wpl — the league-toggle mask: which (state) cells fall below the minimum-
   evidence threshold and render hatched ("not enough WPL cricket yet").

5. presets — three resolved states with both currencies (runs-to-come + win in
   100), never a third (defend) currency:
     * "Dhoni's 206 chase, 2018" — a REAL, corpus-verified Dhoni CHASE finish
       (Chennai chased 206 vs Bangalore and won), read at the start of the final
       five overs, an evidenced second-innings cell (§9.2, not the 2011 defend).
     * "needing 10 an over at halfway, 2010" and "the same chase, 2025" — one
       exact grid square on two era surfaces, framed as the corroboration, not
       the same-chase headline (that is the window aggregate in era_anchor).
   Every preset's quoted numbers are the exact grid readout at its cell, so the
   copy can never contradict the meter.

5. era_anchor — the validated "same chase, two eras" headline (a 9+ RPO chase
   with ~60 balls left won ~23% in 2008-12 vs ~31% in 2023-26), carried straight
   from the gate-validated grid's calibration block.

6. footnotes — data-bound numbers for the "how we computed this" layer:
   calibration summary, the wicket-lever-early / rate-lever-late demonstration,
   and the two mask thresholds.

Stdlib only. Byte-deterministic (key-sorted compact JSON). Writes only
scenes/interlude.json — it never touches an R1/R2a/R3a artifact or an engine.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import canon
import flatten
import re288
import wp

SCENES_DIR = canon.OUT_ROOT / "scenes"
ENGINES_DIR = canon.OUT_ROOT / "engines"

N_OVERS_LEFT = wp.N_OVERS_LEFT      # 20
N_WKTS_IN_HAND = wp.N_WKTS_IN_HAND  # 10
N_RRR = wp.N_RRR                    # 10

# Widget-native surface order: the five IPL era bands, an all-time IPL pooled
# default, then the evidence-masked WPL surface (the league toggle).
ERA_ORDER = (
    ("ipl 2008-2010", "2008-10", "IPL 2008-2010"),
    ("ipl 2011-2015", "2011-15", "IPL 2011-2015"),
    ("ipl 2016-2019", "2016-19", "IPL 2016-2019"),
    ("ipl 2020-2022", "2020-22", "IPL 2020-2022"),
    ("ipl 2023-2026", "2023-26", "IPL 2023-2026"),
    ("ipl pooled", "all-time", "IPL, all seasons"),
    ("wpl 2023-2026", "WPL", "WPL 2023-2026"),
)
DEFAULT_ERA = "ipl pooled"

# Runs-needed slider bound: the corpus's biggest chase target is ~290; 300 is a
# safe soft cap (only its required rate matters, which saturates at 20+ rpo).
RUNS_NEEDED_MAX = 300

# A representative, well-evidenced "needing 10 an over at halfway" cell: 10 overs
# left, THREE wickets down (7 in hand), needing 100 (exactly 10 an over). Both
# eras have real evidence here (2008-10 n=35, 2023-26 n=63) and the cell tells
# the era story cleanly. This is ONE exact square, framed as such (§2b): the
# default-visible headline is the window aggregate in `era_anchor`, not this cell.
HALFWAY_OVERS_LEFT = 10
HALFWAY_WKTS_IN_HAND = 7
HALFWAY_RUNS_NEEDED = 100  # 100 off 60 balls = 10.0 an over

# Preset 1 — a real, corpus-verified Dhoni CHASE finish (storyboard §9.2, RESOLVED
# blocking): the 2018 game where Chennai chased 206 against Bangalore and got
# there, Dhoni set at the crease. The widget is chase-shaped and reads the
# second-innings grid, so the preset must map to a genuine chase state (NOT the
# 2011 final, which Chennai batted first and DEFENDED — a third currency the
# interlude was scoped to avoid). The spot is the start of the final five overs:
# a real "Dhoni at the death" moment on a well-evidenced cell (n=66), quoting the
# two interlude currencies only (runs-to-come + win in 100).
DHONI_CHASE = {
    "season": 2018,
    "opponent": "Royal Challengers Bengaluru",
    "target": 206,
    "finish_overs_left": 5,  # the state at the start of the final five overs
}


# ---------------------------------------------------------------------------
# Engine loading (consume the gate-validated artifacts)
# ---------------------------------------------------------------------------


def _load_engines(out_root: Path):
    """Read engines/wp_grid.json + engines/re288.json, building them first if
    absent (the same bootstrap tests/test_engines.py uses). This module never
    edits them — it only re-projects them for the widget."""
    engines = out_root / "engines"
    if not (engines / "re288.json").exists():
        re288.main(out_root)
    if not (engines / "wp_grid.json").exists():
        wp.main(out_root)
    wp_doc = json.loads((engines / "wp_grid.json").read_text())
    re_doc = json.loads((engines / "re288.json").read_text())
    return wp_doc, re_doc


# ---------------------------------------------------------------------------
# Surface re-projection
# ---------------------------------------------------------------------------


def _win_surface(wp_doc: dict, era_key: str):
    """P(chase win) grid, native index [overs_left-1][wih-1][rrr_bucket]. This
    is exactly wp_grid's layout, copied without transformation."""
    return wp_doc["second_innings"]["surfaces"][era_key]["wp"]


def _runs_surface(re_doc: dict, era_key: str):
    """Expected-runs-from-here grid re-indexed into the widget coordinate:
    runs[overs_left-1][wih-1] = re[20-overs_left][10-wih]. RE288 is indexed by
    (overs bowled, wickets fallen); the widget thinks in (overs left, wickets in
    hand), so the two axes are mirrored."""
    re = re_doc["surfaces"][era_key]["re"]
    out = [[0.0] * N_WKTS_IN_HAND for _ in range(N_OVERS_LEFT)]
    for ol in range(1, N_OVERS_LEFT + 1):
        for wih in range(1, N_WKTS_IN_HAND + 1):
            out[ol - 1][wih - 1] = re[N_OVERS_LEFT - ol][N_WKTS_IN_HAND - wih]
    return out


def _win_n(wp_doc: dict, era_key: str):
    """Per-cell chase count behind the win grid, native index
    [overs_left-1][wih-1][rrr_bucket] — same coordinate as the win surface. This
    is what the widget's evidence gate reads to flag a thin IPL cell (§0.1)."""
    return wp_doc["second_innings"]["surfaces"][era_key]["n"]


def _runs_n(re_doc: dict, era_key: str):
    """Per-cell innings count behind the runs surface, re-indexed to the widget
    coordinate the same way `_runs_surface` mirrors the values."""
    n = re_doc["surfaces"][era_key]["n"]
    out = [[0] * N_WKTS_IN_HAND for _ in range(N_OVERS_LEFT)]
    for ol in range(1, N_OVERS_LEFT + 1):
        for wih in range(1, N_WKTS_IN_HAND + 1):
            out[ol - 1][wih - 1] = n[N_OVERS_LEFT - ol][N_WKTS_IN_HAND - wih]
    return out


def _runs_mask(re_doc: dict, era_key: str):
    """Re-indexed WPL runs mask (1 = below the min-evidence threshold)."""
    masked = re_doc["surfaces"][era_key]["masked"]
    out = [[0] * N_WKTS_IN_HAND for _ in range(N_OVERS_LEFT)]
    for ol in range(1, N_OVERS_LEFT + 1):
        for wih in range(1, N_WKTS_IN_HAND + 1):
            out[ol - 1][wih - 1] = masked[N_OVERS_LEFT - ol][N_WKTS_IN_HAND - wih]
    return out


def _derived_pooled_runs(re_doc: dict):
    """RE288 emits no IPL-pooled runs surface (unlike wp_grid's win grid), so the
    widget's all-time default is DERIVED here: the evidence-weighted mean of the
    five IPL era surfaces (weight = each cell's real n), monotone-repaired with
    the engine's OWN isotonic step so the default obeys the same physics every
    era surface does. Re-indexed into the widget coordinate. A lookup of lookups,
    fully deterministic, never a live fit."""
    eras = [k for k, _s, _l in ERA_ORDER if k.startswith("ipl") and k != "ipl pooled"]
    # engine-native (o, w) accumulation, then isotonic repair, then re-index.
    seed = [[0.0] * re288.N_WKTS for _ in range(re288.N_OVERS)]
    weight = [[0.0] * re288.N_WKTS for _ in range(re288.N_OVERS)]
    for o in range(re288.N_OVERS):
        for w in range(re288.N_WKTS):
            num = den = 0.0
            for e in eras:
                s = re_doc["surfaces"][e]
                n = s["n"][o][w]
                num += s["re"][o][w] * n
                den += n
            if den:
                seed[o][w] = num / den
                weight[o][w] = den
            else:
                weight[o][w] = re288.EMPTY_W
    # fill empty cells by monotone forward-fill (mirrors re288._surface's seed)
    for o in range(re288.N_OVERS):
        for w in range(re288.N_WKTS):
            if weight[o][w] <= re288.EMPTY_W:
                if w > 0:
                    seed[o][w] = seed[o][w - 1]
                elif o > 0:
                    seed[o][w] = seed[o - 1][w]
    fitted = re288._isotonize(seed, weight)
    # per-cell evidence = pooled real innings behind the cell (sum of era n),
    # so the widget can flag a thin pooled-runs cell exactly as it flags a thin
    # win cell (honesty parity, §0.1). Re-index (o, w) -> (overs_left, wih).
    out = [[0.0] * N_WKTS_IN_HAND for _ in range(N_OVERS_LEFT)]
    n_out = [[0] * N_WKTS_IN_HAND for _ in range(N_OVERS_LEFT)]
    for ol in range(1, N_OVERS_LEFT + 1):
        for wih in range(1, N_WKTS_IN_HAND + 1):
            o, w = N_OVERS_LEFT - ol, N_WKTS_IN_HAND - wih
            out[ol - 1][wih - 1] = round(fitted[o][w], 3)
            den = weight[o][w]
            n_out[ol - 1][wih - 1] = int(round(den)) if den > re288.EMPTY_W else 0
    return out, n_out


# ---------------------------------------------------------------------------
# Lookups (the exact readout the widget shows — presets reuse these)
# ---------------------------------------------------------------------------


def win_lookup(win_surf, overs_left: int, wih: int, runs_needed: int) -> float:
    balls_left = overs_left * 6
    rrr = runs_needed * 6.0 / balls_left
    return win_surf[overs_left - 1][wih - 1][wp.rrr_bucket(rrr)]


def runs_lookup(runs_surf, overs_left: int, wih: int) -> float:
    return runs_surf[overs_left - 1][wih - 1]


# ---------------------------------------------------------------------------
# The Dhoni preset — a REAL Dhoni CHASE finish, read from the corpus (§9.2)
# ---------------------------------------------------------------------------


def _corpus_counts(data_root: Path = canon.DATA_ROOT) -> dict:
    """Match counts behind the grids, so "1,331 matches, 88 of them WPL" binds to
    a field instead of being hand-typed in the copy (§0.2 rule 2, §8)."""
    ipl = wpl = 0
    for _date, _mid, league, _path in flatten.sorted_match_files(data_root):
        if league == "ipl":
            ipl += 1
        elif league == "wpl":
            wpl += 1
    return {"matches": ipl + wpl, "ipl_matches": ipl, "wpl_matches": wpl}


def dhoni_chase_state(data_root: Path = canon.DATA_ROOT) -> dict:
    """The real 2018 IPL chase: Chennai (Dhoni) chased 206 against Bangalore and
    got there. Returns the second-innings state at the start of the final five
    overs, so the win meter reads Dhoni's OWN chasing side and the preset stays
    two-currency and chase-shaped (never the 2011 final defend, §9.2). Read from
    the corpus so the preset stays data-bound; resolved by identity (season,
    teams, Chennai chasing, target, Chennai won) not by a hard-coded index."""
    finish = DHONI_CHASE["finish_overs_left"]
    want_teams = {"Chennai Super Kings", DHONI_CHASE["opponent"]}
    hits = []
    for _date, _mid, league, path in flatten.sorted_match_files(data_root):
        if league != "ipl":
            continue
        with open(path) as fh:
            m = json.load(fh)
        info = m["info"]
        if canon.is_dl(info) or canon.canon_season(info) != DHONI_CHASE["season"]:
            continue
        if {canon.canon_team(t) for t in info["teams"]} != want_teams:
            continue
        inns = [i for i in m["innings"] if not canon.is_super_over(i)]
        if len(inns) < 2:
            continue
        first, second = inns[0], inns[1]
        if canon.canon_team(second["team"]) != "Chennai Super Kings":
            continue
        target_runs = (second.get("target") or {}).get("runs")
        if target_runs != DHONI_CHASE["target"]:
            continue
        winner = info.get("outcome", {}).get("winner")
        if not winner or canon.canon_team(winner) != "Chennai Super Kings":
            continue
        # replay to the exact grid cell at the start of the final `finish` overs
        score = wkts = legal = 0
        state = None
        for over in second["overs"]:
            for dl in over["deliveries"]:
                if wp._is_legal(dl):
                    needed = target_runs - score
                    balls_left = 120 - legal
                    if (state is None and balls_left > 0 and needed > 0
                            and wkts < 10 and math.ceil(balls_left / 6) == finish):
                        state = (finish, 10 - wkts, needed)
                    legal += 1
                score += dl["runs"]["total"]
                if "wickets" in dl:
                    wkts += len(dl["wickets"])
        if state is None:
            raise LookupError("Dhoni chase never reached the final-overs state")
        ol, wih, need = state
        hits.append({
            "match": {
                "batting_first": canon.canon_team(first["team"]),
                "chasing": canon.canon_team(second["team"]),
                "target": target_runs,
                "venue": canon.canon_venue(info["venue"]),
                "season": DHONI_CHASE["season"],
                "result": info["outcome"],
            },
            "overs_left": ol,
            "wickets_in_hand": wih,
            "runs_needed": need,
        })
    if len(hits) != 1:
        raise LookupError(f"Dhoni chase not uniquely resolved: {len(hits)} hits")
    return hits[0]


# ---------------------------------------------------------------------------
# Presets
# ---------------------------------------------------------------------------


def _pct(x: float) -> int:
    return round(x * 100)


def _build_presets(surfaces_win, surfaces_runs, data_root: Path) -> list:
    presets = []

    # --- Preset 1: a real Dhoni CHASE finish (§9.2) — two currencies only ---
    d = dhoni_chase_state(data_root)
    era = "ipl 2016-2019"  # 2018 falls in this era band
    ol, wih, need = d["overs_left"], d["wickets_in_hand"], d["runs_needed"]
    win = win_lookup(surfaces_win[era], ol, wih, need)
    runs = runs_lookup(surfaces_runs[era], ol, wih)
    presets.append({
        "id": "dhoni_2018_chase",
        "label": f"Dhoni's {d['match']['target']} chase, 2018",
        "era": era,
        "state": {"overs_left": ol, "wickets_in_hand": wih, "runs_needed": need},
        "required_rate": round(need * 6.0 / (ol * 6), 2),
        "win_pct": win,               # Dhoni's OWN chasing side
        "win_display": _pct(win),
        "expected_runs": runs,
        "expected_runs_display": round(runs),
        "match": d["match"],
        "copy": {
            "orient": (
                f"Chennai chasing {d['match']['target']}, 2018, Dhoni set at the "
                f"crease. {ol} overs left, {wih} wickets in hand, still {need} to "
                f"get."
            ),
            "reveal": (
                f"From a spot this steep teams usually make about {round(runs)} "
                f"more runs and win about {_pct(win)} in 100. Dhoni got them "
                f"there anyway."
            ),
        },
    })

    # --- Presets 2 & 3: the same ONE square, two eras (option c) ---
    # This is a single exact grid cell you can feel by hand: three down, needing
    # 10 an over at halfway. It is deliberately NOT the same-chase headline (that
    # is the window aggregate in `era_anchor`, default-visible in IN-4); the
    # copy frames it as one square so the two never read as contradictory (§9.1).
    ol, wih, need = HALFWAY_OVERS_LEFT, HALFWAY_WKTS_IN_HAND, HALFWAY_RUNS_NEEDED
    rr = round(need * 6.0 / (ol * 6), 1)
    pair = []
    for pid, label, era, season_word in (
        ("halfway_2010", "needing 10 an over at halfway, 2010",
         "ipl 2008-2010", "2010"),
        ("same_chase_2025", "the same chase, 2025",
         "ipl 2023-2026", "2025"),
    ):
        win = win_lookup(surfaces_win[era], ol, wih, need)
        runs = runs_lookup(surfaces_runs[era], ol, wih)
        pair.append({
            "id": pid,
            "label": label,
            "era": era,
            "state": {"overs_left": ol, "wickets_in_hand": wih,
                      "runs_needed": need},
            "required_rate": rr,
            "win_pct": win,
            "win_display": _pct(win),
            "expected_runs": runs,
            "expected_runs_display": round(runs),
            "season_word": season_word,
        })
    # copy: one exact square, felt in two eras — the corroboration, not the point
    early, late = pair[0], pair[1]
    early["copy"] = {
        "orient": (
            "One exact square, back in 2010. Ten overs left, three down, needing "
            "100. That is 10 an over."
        ),
        "reveal": (
            f"From this one spot teams won about {early['win_display']} in 100 "
            f"and usually made about {early['expected_runs_display']} more. Now "
            f"press the same chase in 2025 and watch only the year change."
        ),
    }
    late["copy"] = {
        "orient": (
            "The same one square, now in 2025. Nothing on the sliders moved. Ten "
            "overs left, three down, needing 100, still 10 an over."
        ),
        "reveal": (
            f"From this exact spot teams now win about {late['win_display']} in "
            f"100 and make about {late['expected_runs_display']} more. Same "
            f"square, later era, and the chase got kinder."
        ),
    }
    # tie the two presets together for the widget
    for p in pair:
        p["pair"] = ["halfway_2010", "same_chase_2025"]
    presets.extend(pair)
    return presets


# ---------------------------------------------------------------------------
# Footnotes (data-bound)
# ---------------------------------------------------------------------------


def _footnotes(wp_doc: dict, re_doc: dict, surfaces_win: dict) -> dict:
    cal = wp_doc["calibration"]
    pooled = surfaces_win["ipl pooled"]

    # The wicket-lever-early / rate-lever-late demonstration, straight off the
    # pooled grid. At a hard ask (11-12 an over -> rrr bucket 6), having ten
    # wickets instead of five is a big lever EARLY (lots of overs to use them)
    # and no lever at all LATE (no time left, the rate decides everything).
    rb = wp.rrr_bucket(11.5)  # 11-12 rpo bucket
    early_ol, late_ol = 16, 2
    early_10 = pooled[early_ol - 1][9][rb]
    early_5 = pooled[early_ol - 1][4][rb]
    late_10 = pooled[late_ol - 1][9][rb]
    late_5 = pooled[late_ol - 1][4][rb]

    re_cal = {
        k: re_doc["surfaces"][k]["calibration"]["pooled_abs_dev"]
        for k in re_doc["surfaces"]
    }

    return {
        "calibration": {
            "text": (
                "Every number here is a lookup, not a guess. We scored each of "
                f"{cal['n']:,} real chase moments with the grid and checked it "
                "against what actually happened. Across the board the grid was "
                f"off by about {round(cal['ece'] * 100, 1)} points of win "
                "probability, and never more than "
                f"{round(cal['worst_populated_bin_abs_dev'] * 100, 1)} points in "
                "any well-stocked band."
            ),
            "win_ece": cal["ece"],
            "win_worst_populated_bin_abs_dev": cal["worst_populated_bin_abs_dev"],
            "win_calibration_n": cal["n"],
            "runs_pooled_abs_dev_by_surface": re_cal,
        },
        "wickets_early_rate_late": {
            "text": (
                "Early on, wickets in hand are everything and the rate is soft. "
                "With 16 overs left and 11 an over to get, ten wickets in hand "
                f"instead of five lifts your odds from {_pct(early_5)}% to "
                f"{_pct(early_10)}%. With two overs left it flips: the same ten "
                f"wickets buy you nothing, {_pct(late_5)}% either way, because "
                "there is no time to use them. Late, only the rate matters."
            ),
            "hard_ask_rpo": "11-12",
            "early_overs_left": early_ol,
            "early_win_5_wkts": early_5,
            "early_win_10_wkts": early_10,
            "early_wicket_lever": round(early_10 - early_5, 4),
            "late_overs_left": late_ol,
            "late_win_5_wkts": late_5,
            "late_win_10_wkts": late_10,
            "late_wicket_lever": round(late_10 - late_5, 4),
        },
        "evidence_mask": {
            "text": (
                "The WPL is only four seasons old, so many spots have too few "
                "games to call honestly. We hatch any win-grid spot built on "
                f"fewer than {wp.WPL_MASK_MIN_N} chases and any runs-grid spot "
                f"built on fewer than {re288.MASK_MIN_N} innings, and label them "
                "plainly: not enough WPL cricket yet."
            ),
            "win_mask_min_n": wp.WPL_MASK_MIN_N,
            "runs_mask_min_n": re288.MASK_MIN_N,
        },
    }


# ---------------------------------------------------------------------------
# Doc assembly + emission
# ---------------------------------------------------------------------------


def build_doc(out_root: Path = canon.OUT_ROOT,
              data_root: Path = canon.DATA_ROOT) -> dict:
    wp_doc, re_doc = _load_engines(out_root)

    win_surfaces = {}
    runs_surfaces = {}
    win_n = {}
    runs_n = {}
    for era_key, _short, _label in ERA_ORDER:
        win_surfaces[era_key] = _win_surface(wp_doc, era_key)
        win_n[era_key] = _win_n(wp_doc, era_key)
        if era_key == "ipl pooled":
            runs_surfaces[era_key], runs_n[era_key] = _derived_pooled_runs(re_doc)
        else:
            runs_surfaces[era_key] = _runs_surface(re_doc, era_key)
            runs_n[era_key] = _runs_n(re_doc, era_key)

    # WPL toggle: masks + evidenced/masked cell counts
    wpl_win_masked = wp_doc["second_innings"]["surfaces"]["wpl 2023-2026"]["masked"]
    wpl_runs_masked = _runs_mask(re_doc, "wpl 2023-2026")
    win_mask_stats = wp_doc["second_innings"]["wpl_mask"]
    n_runs_cells = N_OVERS_LEFT * N_WKTS_IN_HAND
    n_runs_masked = sum(
        wpl_runs_masked[ol][wih]
        for ol in range(N_OVERS_LEFT) for wih in range(N_WKTS_IN_HAND)
    )

    presets = _build_presets(win_surfaces, runs_surfaces, data_root)
    footnotes = _footnotes(wp_doc, re_doc, win_surfaces)
    corpus = _corpus_counts(data_root)

    era_anchor = dict(wp_doc["calibration"]["era_anchor"])
    early = era_anchor["ipl_2008_2012"]["win_rate"]
    recent = era_anchor["ipl_2023_2026"]["win_rate"]
    era_anchor["delta_points"] = round((recent - early) * 100, 1)

    return {
        "scene": "interlude",
        "release": "R3b",
        "title": "The Net Session",
        "engine_sources": {
            "win": "engines/wp_grid.json (engine #3)",
            "runs": "engines/re288.json (engine #2)",
        },
        "note": (
            "Two dials on one lookup. The win meter reads engine #3's chase-win "
            "grid; the runs meter reads engine #2's run-expectancy surface, "
            "re-indexed to the same (overs_left, wickets_in_hand) coordinate. No "
            "live model. The widget interpolates and looks up, never fits."
        ),
        "state_space": {
            "overs_left": {"min": 1, "max": N_OVERS_LEFT},
            "wickets_in_hand": {"min": 1, "max": N_WKTS_IN_HAND},
            "runs_needed": {"min": 1, "max": RUNS_NEEDED_MAX},
            "rrr_edges": list(wp.RRR_EDGES),
            "index": {
                "win": "win[era][overs_left-1][wickets_in_hand-1][rrr_bucket]",
                "runs": "runs[era][overs_left-1][wickets_in_hand-1]",
                "rrr_bucket": (
                    "first i where runs_needed*6/(overs_left*6) < rrr_edges[i], "
                    f"else {N_RRR - 1}"
                ),
            },
        },
        "eras": [
            {"key": k, "short": s, "label": l} for k, s, l in ERA_ORDER
        ],
        "default_era": DEFAULT_ERA,
        "surfaces": {
            "win": win_surfaces,
            "runs": runs_surfaces,
            "win_n": win_n,
            "runs_n": runs_n,
        },
        "corpus": corpus,
        "evidence": {
            "win_min_n": wp.WPL_MASK_MIN_N,
            "runs_min_n": re288.MASK_MIN_N,
            "note": (
                "One minimum-evidence rule for BOTH leagues (§0.1). A win cell "
                f"built on fewer than {wp.WPL_MASK_MIN_N} real chases, or a runs "
                f"cell on fewer than {re288.MASK_MIN_N} real innings, is thin "
                "ground. The WPL renders those as a hole ('not enough WPL cricket "
                "yet'); IPL free-play shows the number but marks it as filled in "
                "by rule, not counted, and hatches its grid square. The default "
                "spot and mainstream chases are well above the threshold, so the "
                "toy's common path shows real numbers."
            ),
        },
        "wpl": {
            "win_mask": wpl_win_masked,
            "runs_mask": wpl_runs_masked,
            "win_mask_min_n": wp.WPL_MASK_MIN_N,
            "runs_mask_min_n": re288.MASK_MIN_N,
            "win_cells": {
                "total": win_mask_stats["cells_total"],
                "masked": win_mask_stats["cells_masked"],
                "evidenced": win_mask_stats["cells_evidenced"],
            },
            "runs_cells": {
                "total": n_runs_cells,
                "masked": n_runs_masked,
                "evidenced": n_runs_cells - n_runs_masked,
            },
            "note": (
                "Flip the toggle to the WPL. It is four seasons old, not "
                "nineteen, so many spots have too few games to read. Those render "
                "hatched: not enough WPL cricket yet. A young league, told "
                "honestly, not a league behind."
            ),
        },
        "presets": presets,
        "era_anchor": era_anchor,
        "meters": {
            "win": {
                "label": "How often teams win from here",
                "gloss": "out of every 100 chases from a spot like this",
                "format": "percent",
            },
            "runs": {
                "label": "Runs a team usually still gets",
                "gloss": "expected runs to come from here",
                "format": "runs",
            },
        },
        "sliders": {
            "overs_left": "Overs left",
            "wickets_in_hand": "Wickets in hand",
            "runs_needed": "Runs needed",
        },
        "intro": {
            "orient": (
                "Set the chase with three sliders: how many overs are left, how "
                "many wickets are still standing, and how many runs the batting "
                "side needs."
            ),
            "reveal": (
                "Two meters answer at once. One is how often teams win from a "
                "spot like this. The other is how many runs they usually still "
                f"get. Every reading is a real count from {corpus['matches']:,} "
                "matches, not a guess."
            ),
        },
        "footnotes": footnotes,
    }


def main(out_root: Path = canon.OUT_ROOT,
         data_root: Path = canon.DATA_ROOT) -> dict:
    doc = build_doc(out_root, data_root)
    SCENES_DIR.mkdir(parents=True, exist_ok=True)
    raw = flatten.compact_json(doc, sort_keys=True)
    out = out_root / "scenes" / "interlude.json"
    out.write_bytes(raw)

    gz = len(flatten.gz_bytes(raw))
    print(f"  scenes/interlude.json   raw={len(raw):>9,}  gz={gz:>8,}")
    for p in doc["presets"]:
        s = p["state"]
        print(f"    preset {p['id']:<18} [{s['overs_left']}ov {s['wickets_in_hand']}w "
              f"{s['runs_needed']}r]  win {p['win_display']:>3} in100  "
              f"runs {p['expected_runs_display']:>3}")
    anc = doc["era_anchor"]
    print(f"    era anchor (9+ RPO, ~60 balls left): "
          f"{anc['ipl_2008_2012']['win_rate']} -> "
          f"{anc['ipl_2023_2026']['win_rate']} (+{anc['delta_points']} pts)")
    wpl = doc["wpl"]
    print(f"    WPL mask: win {wpl['win_cells']['masked']}/"
          f"{wpl['win_cells']['total']} hatched (n<{wpl['win_mask_min_n']}); "
          f"runs {wpl['runs_cells']['masked']}/{wpl['runs_cells']['total']} "
          f"hatched (n<{wpl['runs_mask_min_n']})")
    return doc


if __name__ == "__main__":
    main()
