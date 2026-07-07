"""R3b-2 — Chapter 5 "What a Ball Is Worth" (WPA / repricing) data module.

Consumes the GATE-VALIDATED engines (engines/wp_grid.json win grids +
engines/re288.json run-expectancy surfaces — tests/test_engines.py owns their
correctness; this module never rebuilds or edits them) and emits everything
Chapter 5 needs:

  wpa.u8            per-point buffer: the ball's Win Probability Added, signed,
                    from the BATTING team's perspective, quantized to one byte
                    (byte = 127 + round(wpa*127), clamped 0..254; decode
                    wpa = (byte-127)/127; byte 255 = sentinel "no WPA" — the
                    ball belongs to a D/L match, a no-result, or a chase whose
                    target was not a full 20 overs, exactly the matches the
                    gate-validated grids exclude). Field point order
                    (season-blocked, super overs excluded).
  restate.u8        per-point buffer: the ball's RE-grid state cell packed as
                    over*10 + wickets_down (0..199). over = the delivery's over
                    index 0..19 (wides/no-balls carry the over they were bowled
                    in); wickets_down = wickets fallen in the innings BEFORE
                    this delivery (0..9 — a 10th wicket ends the innings, so a
                    delivery is never bowled 10 down). Both innings are packed;
                    the columnar `innings` array filters if a scene needs
                    first innings only. Drives the controlling RE-surface morph.
  scenes/ch5.json   the chapter scene doc: the defended-band contrast, the
                    RE-surface drift exhibit + third-wicket validation, linear
                    weights per era + the per-season price board, the Wicket
                    Value Index, the finisher table + the moving fatal-RRR
                    cliff, the 2019-final scrub over with its WP worm, the
                    league WPA headlines, the 20 franchise payoff cards, the
                    WPL beats (mask + observed dots + finisher cohort), the
                    footnote layer, and both buffer decode specs.

Derived state views (documented, never an engine rebuild — each one reads the
same underlying corpus with the same era windows as the engines):

  * MID-FIRST-INNINGS WP — the view wp.py explicitly designates for R3b: the
    batting-first team's P(win) = the era defend curve read at a PROJECTED
    final total (runs so far + the era RE surface's runs-to-come at the ball's
    state). The defend curve is interpolated piecewise-linearly between its
    total-bucket midpoints (anchors 110 and 235 for the open end buckets); the
    RE surface is interpolated linearly across the over axis so every legal
    ball, not just over starts, has a state value.
  * SECOND-INNINGS WP — the engine grid verbatim at (overs_left = ceil(balls
    left / 6), wickets in hand, required-rate bucket), the exact wp.py state
    math. Terminal balls resolve to the actual result (ties by the super-over
    winner, wp.chaser_won), which is what makes per-innings WPA telescope
    exactly: sum(WPA over innings 2) == outcome − first-state WP.
  * RAW STATE CELLS for the validations (third-wicket cost, Wicket Value
    Index, defended band, finisher, endgame dots) — raw observed runs-to-come
    / win frequencies recounted from the corpus, non-D/L, super overs
    excluded, with n shipped for every quoted number. Raw recounts are the
    honest local numbers; the engine's smoothed surfaces spread thin-cell
    evidence to neighbours by design, so both are quoted where they differ.

Stdlib only. Byte-deterministic (key-sorted compact JSON; fixed quantizer).
Run AFTER flatten + scenes + re288 + wp (README order): it merges its three
artifacts into meta.json's manifest like bowlerplane.py does. Writes only
wpa.u8, restate.u8 and scenes/ch5.json — no R1/R2/R3a artifact and no engine
is ever touched, so every earlier scene renders byte-identically.
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
import wp as wpmod

SCENES_DIR = canon.OUT_ROOT / "scenes"
ENGINES_DIR = canon.OUT_ROOT / "engines"

IPL_ERA_BANDS = wpmod.IPL_ERA_BANDS  # the engines' five IPL bands
WPL_KEY = "wpl 2023-2026"
BAND_ORDER = tuple(f"ipl {label}" for label, _l, _h in IPL_ERA_BANDS) + (WPL_KEY,)
EARLY, RECENT = "ipl 2008-2010", "ipl 2023-2026"

# --- wpa.u8 encoding -------------------------------------------------------
WPA_SENTINEL = 255      # no WPA: D/L match, no result, or non-20-over target
WPA_SCALE = 127         # byte = 127 + round(wpa * 127), clamped to 0..254

# --- defend-curve interpolation anchors (derived first-innings WP view) ----
# Bucket midpoints for 120-129 .. 220-229; the open ends anchor at 110 / 235.
DEFEND_ANCHOR_LO = 110.0
DEFEND_ANCHOR_HI = 235.0
DEFEND_X = (DEFEND_ANCHOR_LO,) + tuple(
    120 + 10 * i + 4.5 for i in range(11)
) + (DEFEND_ANCHOR_HI,)

# --- validation recipes (pinned; every number ships with its n) ------------
DEFENDED_LO, DEFENDED_HI = 170, 189   # the repriced-scoreboard band
DRIFT_OVER = 6                        # start of the 7th over (o = overs bowled)
DRIFT_WINDOWS = (("2008-2010", 2008, 2010), ("2023-2026", 2023, 2026),
                 ("2024-2026", 2024, 2026))  # last = the catalog teaser window
FINISHER_BALLS_LEFT = 30              # "5 overs left": state at 30 balls left
FINISHER_BANDS = (("6-8", 6.0, 8.0), ("8-10", 8.0, 10.0),
                  ("10-12", 10.0, 12.0), ("12+", 12.0, math.inf))
CHASE_DIFF_BALLS_LEFT = 24            # footnote exhibit: last 24 balls
CHASE_DIFF_NEEDED = (30, 42)          # needing 30-42
CHASE_DIFF_MIN_WIH = 5                # with 5+ wickets in hand
ENDGAME_MAX_BALLS_LEFT = 12           # observed endgame dots (scrub overlay)
ENDGAME_MAX_NEEDED = 36
BOWLER_CREDITED = ("caught", "bowled", "lbw", "stumped",
                   "caught and bowled", "hit wicket")

# --- demoted era-swap exhibit (footnote layer) ------------------------------
# Resolved by identity: the 2008 IPL chase in which this batter made 100+.
ERA_SWAP_BATTER = "AC Gilchrist"

# --- payoff ---------------------------------------------------------------
PAYOFF_TOP_N = 5                      # 1 most-valuable + 4 runners-up
PAYOFF_MIN_SWING = 0.05               # candidate floor (top balls are >> this)
TOP_SWINGS_N = 10                     # league-wide gallery


# ---------------------------------------------------------------------------
# Engine loading (bootstrap like interlude.py — never a rebuild)
# ---------------------------------------------------------------------------


def load_engines():
    wp_path = ENGINES_DIR / "wp_grid.json"
    re_path = ENGINES_DIR / "re288.json"
    if not wp_path.exists():
        wpmod.main()
    if not re_path.exists():
        re288.main()
    wpdoc = json.loads(wp_path.read_text())
    redoc = json.loads(re_path.read_text())
    return {
        "wp": {k: v["wp"] for k, v in wpdoc["second_innings"]["surfaces"].items()},
        "defend": wpdoc["first_innings_defend"]["surfaces"],
        "re": {k: v["re"] for k, v in redoc["surfaces"].items()},
        "re_n": {k: v["n"] for k, v in redoc["surfaces"].items()},
        "re_mask": redoc["surfaces"][WPL_KEY]["masked"],
        "re_mask_min_n": redoc["surfaces"][WPL_KEY]["mask_min_n"],
        "calibration_ece": wpdoc["calibration"]["ece"],
        "rrr_edges": tuple(wpdoc["second_innings"]["rrr_edges"]),
    }


def band_key(league: str, season: int) -> str | None:
    if league == "wpl":
        return WPL_KEY
    for label, lo, hi in IPL_ERA_BANDS:
        if lo <= season <= hi:
            return f"ipl {label}"
    return None


# ---------------------------------------------------------------------------
# WP readouts (grid + derived first-innings view)
# ---------------------------------------------------------------------------


def defend_p(engines: dict, era: str, total: float) -> float:
    """P(bat-first team wins | final total), interpolated piecewise-linearly
    between the defend curve's bucket midpoints (open ends clamp)."""
    p = engines["defend"][era]["p_batfirst_win"]
    if total <= DEFEND_X[0]:
        return p[0]
    if total >= DEFEND_X[-1]:
        return p[-1]
    for i in range(len(DEFEND_X) - 1):
        if DEFEND_X[i] <= total < DEFEND_X[i + 1]:
            f = (total - DEFEND_X[i]) / (DEFEND_X[i + 1] - DEFEND_X[i])
            return p[i] + f * (p[i + 1] - p[i])
    return p[-1]


def re_at(engines: dict, era: str, legal: int, wkts: int) -> float:
    """Era RE runs-to-come at a per-ball state: the 20x10 over-start surface
    interpolated linearly across the over axis (RE at 20 overs == 0)."""
    if wkts >= 10 or legal >= 120:
        return 0.0
    surf = engines["re"][era]
    o = legal / 6.0
    lo = int(o)
    frac = o - lo
    v0 = surf[lo][wkts]
    v1 = surf[lo + 1][wkts] if lo + 1 < 20 else 0.0
    return v0 + frac * (v1 - v0)


def wp_first(engines: dict, era: str, legal: int, wkts: int, runs: int) -> float:
    """Derived mid-first-innings WP: defend curve at the projected total."""
    return defend_p(engines, era, runs + re_at(engines, era, legal, wkts))


def wp_chase(engines: dict, era: str, legal: int, wkts: int, score: int,
             target_runs: int) -> float:
    """Engine-grid P(chasing team wins) at the ball's state (wp.py math)."""
    needed = target_runs - score
    if needed <= 0:
        return 1.0
    if wkts >= 10:
        return 0.0
    balls_left = 120 - legal
    if balls_left <= 0:
        return 0.0
    ol = math.ceil(balls_left / 6) - 1
    wih = (10 - wkts) - 1
    rb = wpmod.rrr_bucket(needed * 6.0 / balls_left)
    return engines["wp"][era][ol][wih][rb]


def encode_wpa(w: float | None) -> int:
    if w is None:
        return WPA_SENTINEL
    b = 127 + round(w * WPA_SCALE)
    return min(max(b, 0), 254)


def _is_legal(dl: dict) -> bool:
    extras = dl.get("extras", {})
    return "wides" not in extras and "noballs" not in extras


def _kind_text(kind: str) -> str:
    return {"caught and bowled": "caught and bowled",
            "hit wicket": "out hit wicket",
            "obstructing the field": "given out obstructing the field",
            "retired out": "retired out"}.get(kind, kind)


def _tally(d: dict, key, won: int):
    c = d.setdefault(key, [0, 0])
    c[0] += won
    c[1] += 1


def _acc(d: dict, key, v: float):
    c = d.setdefault(key, [0.0, 0])
    c[0] += v
    c[1] += 1


# ---------------------------------------------------------------------------
# The corpus pass
# ---------------------------------------------------------------------------


def build(data_root: Path = canon.DATA_ROOT) -> dict:
    engines = load_engines()
    files = flatten.sorted_match_files(data_root)

    wpa_bytes = bytearray()
    restate = bytearray()
    n_sentinel = 0
    sentinel_matches = {"dl": 0, "no_result_or_undecided": 0, "short_target": 0}

    lw = {}            # (band, cls) -> [sum, n]        first innings, non-D/L
    board = {}         # (league, season, cls) -> [sum, n]
    ball_cells = {}    # band -> {(legal, wkts): [sum, n]}  both innings, non-D/L
    wicket_events = [] # (band, legal_before, wkts_before, kind)
    rr_band = {}       # band -> [runs_total, legal]        same WVI universe
    over_cells = {}    # window -> {(o, w): [sum, n]}       IPL first inns raw
    wpl_re_obs = {}    # (o, w) -> [observed runs-to-come]  WPL first inns raw
    defended = {}      # band -> [defended, n]
    finisher = {}      # (band, rrr_band) -> [wins, n]
    chase_diff = {}    # band -> [wins, n]
    endgame = {}       # (needed, balls_left) -> [wins, n]  IPL pooled
    per_band_wpa = {}  # band -> [sum |wpa|, n]
    team_cands = {t["id"]: [] for t in canon.TEAMS}
    league_cands = []
    closure_max = 0.0

    scrub = None
    scrub_match_index = None
    gil = None
    gil_match_index = None

    point_index = -1
    for match_index, (_date, _mid, league, path) in enumerate(files):
        with open(path) as fh:
            match = json.load(fh)
        info = match["info"]
        season = canon.canon_season(info)
        band = band_key(league, season)
        dl = canon.is_dl(info)
        inns = [i for i in match.get("innings", []) if not canon.is_super_over(i)]
        teams_c = [canon.canon_team(t) for t in info["teams"]]
        target = inns[1].get("target") if len(inns) > 1 else None
        chaser_result = (wpmod.chaser_won(info, inns[1]["team"])
                         if len(inns) > 1 else None)
        usable = (not dl and chaser_result is not None
                  and bool(target) and target.get("overs") == 20)
        if not usable:
            if dl:
                sentinel_matches["dl"] += 1
            elif chaser_result is None:
                sentinel_matches["no_result_or_undecided"] += 1
            else:
                sentinel_matches["short_target"] += 1
        target_runs = target["runs"] if usable else None

        # scrub set-piece resolution BY IDENTITY (never a hard-coded index):
        # the 2019 IPL Final, MI beat CSK by 1 run.
        if (league == "ipl" and season == 2019
                and flatten.match_stage(info) == "Final"
                and set(teams_c) == {"Mumbai Indians", "Chennai Super Kings"}
                and flatten.match_result_text(info) == "Mumbai Indians won by 1 run"):
            assert scrub_match_index is None, "scrub match must be unique"
            scrub_match_index = match_index
            scrub = {"record": flatten.match_record(info, league),
                     "era": band, "target": target_runs, "balls": []}

        # first-innings full/total facts (defended band)
        first_total = first_legal = first_wkts = 0
        if inns:
            for over in inns[0]["overs"]:
                for dl_ in over["deliveries"]:
                    first_total += dl_["runs"]["total"]
                    if _is_legal(dl_):
                        first_legal += 1
                    if "wickets" in dl_:
                        first_wkts += len(dl_["wickets"])
        first_full = first_legal >= 120 or first_wkts >= 10
        if (not dl and chaser_result is not None and first_full
                and DEFENDED_LO <= first_total <= DEFENDED_HI and band):
            _tally(defended, band, 1 - chaser_result)

        gil_tally = {}  # 2008 hundred detection (era-swap footnote)

        for iidx, innings in enumerate(inns):
            bat_team = canon.canon_team(innings["team"])
            bat_tid = canon.team_id(league, bat_team)
            others = [t for t in teams_c if t != bat_team]
            bowl_tid = canon.team_id(league, others[0]) if others else None
            deliveries = [(over["over"], bi, dl_)
                          for over in innings["overs"]
                          for bi, dl_ in enumerate(over["deliveries"])]
            n_del = len(deliveries)
            last_over_no = deliveries[-1][0] if deliveries else None
            legal = wkts = runs = 0
            over_start = {}  # over_no -> (runs, wkts) at its start
            seen_over = -1
            inn2_first_wp = None
            inn2_sum = 0.0

            for k, (over_no, bi, dl_) in enumerate(deliveries):
                point_index += 1
                assert 0 <= over_no <= 19, f"over {over_no} out of range"
                assert wkts <= 9, "a delivery bowled with 10 down"
                if over_no != seen_over:
                    over_start[over_no] = (runs, wkts)
                    seen_over = over_no
                restate.append(over_no * 10 + wkts)

                islegal = _is_legal(dl_)
                nw = len(dl_.get("wickets", []))
                rt = dl_["runs"]["total"]
                rb_ = dl_["runs"]["batter"]
                legal2 = legal + (1 if islegal else 0)
                wkts2 = wkts + nw
                runs2 = runs + rt

                # ---- WPA (batting-team perspective) ----
                wpa = None
                if usable and iidx <= 1 and band:
                    if iidx == 0:
                        b_wp = wp_first(engines, band, legal, wkts, runs)
                        a_wp = (defend_p(engines, band, runs2)
                                if k == n_del - 1
                                else wp_first(engines, band, legal2, wkts2, runs2))
                    else:
                        b_wp = wp_chase(engines, band, legal, wkts, runs,
                                        target_runs)
                        if k == n_del - 1:
                            a_wp = (1.0 if chaser_result == 1 else 0.0)
                        else:
                            a_wp = wp_chase(engines, band, legal2, wkts2, runs2,
                                            target_runs)
                        if inn2_first_wp is None:
                            inn2_first_wp = b_wp
                        inn2_sum += a_wp - b_wp
                    wpa = a_wp - b_wp
                    _acc(per_band_wpa, band, abs(wpa))
                    if abs(wpa) >= PAYOFF_MIN_SWING:
                        for tid, sw in ((bat_tid, wpa), (bowl_tid, -wpa)):
                            if tid is not None and sw >= PAYOFF_MIN_SWING:
                                team_cands[tid].append(
                                    (round(sw, 6), match_index, point_index,
                                     iidx, over_no, bi))
                    if abs(wpa) >= 0.3:
                        league_cands.append(
                            (round(wpa, 6), match_index, point_index,
                             iidx, over_no, bi))
                else:
                    n_sentinel += 1
                wpa_bytes.append(encode_wpa(wpa))

                # ---- scrub capture (final over of innings 2) ----
                if (scrub_match_index == match_index and iidx == 1
                        and over_no == last_over_no):
                    wk = dl_.get("wickets", [])
                    scrub["balls"].append({
                        "over": over_no,
                        "ball": len(scrub["balls"]) + 1,
                        # the ball's index in the shared field point order, so
                        # the scene's over-rail lift never has to derive it
                        # from the columnar corpus at runtime (CONTRACT §20:
                        # "a tiny index set from scenes/ch5.json, never
                        # client-derived")
                        "point_index": point_index,
                        "label": f"{over_no}.{bi + 1}",
                        "batter": dl_["batter"],
                        "bowler": dl_["bowler"],
                        "runs_batter": rb_,
                        "runs_total": rt,
                        "extras": sorted(dl_.get("extras", {})) or None,
                        "wicket": ({"kind": wk[0]["kind"],
                                    "player_out": wk[0]["player_out"]}
                                   if wk else None),
                        "needed_before": target_runs - runs,
                        "balls_left_before": 120 - legal,
                        "wickets_in_hand_before": 10 - wkts,
                        "wp_before": round(b_wp, 4),
                        "wp_after": round(a_wp, 4),
                        "wpa": round(wpa, 4),
                    })

                # ---- linear weights + price board (first innings, non-D/L) ----
                if iidx == 0 and not dl and band:
                    weight = (re_at(engines, band, legal2, wkts2)
                              - re_at(engines, band, legal, wkts) + rt)
                    if nw:
                        cls = "wicket"
                    elif islegal and rt == 0:
                        cls = "dot"
                    elif rb_ == 1:
                        cls = "single"
                    elif rb_ == 2:
                        cls = "two"
                    elif rb_ == 3:
                        cls = "three"
                    elif rb_ == 4:
                        cls = "four"
                    elif rb_ == 6:
                        cls = "six"
                    elif "wides" in dl_.get("extras", {}):
                        cls = "wide"
                    else:
                        cls = "other"
                    _acc(lw, (band, cls), weight)
                    _acc(board, (league, season, cls), weight)

                # ---- WVI wicket events (both innings, non-D/L; the raw
                # state cells they price against are filled after the innings,
                # once its final total is known) ----
                if iidx <= 1 and not dl and band:
                    for w_ev in dl_.get("wickets", []):
                        wicket_events.append((band, legal, wkts, w_ev["kind"]))

                # ---- second-innings validation states ----
                if usable and iidx == 1 and islegal and wkts < 10:
                    needed = target_runs - runs
                    balls_left = 120 - legal
                    if needed > 0:
                        if balls_left == FINISHER_BALLS_LEFT:
                            rrr = needed * 6.0 / balls_left
                            for fb, lo_, hi_ in FINISHER_BANDS:
                                if lo_ <= rrr < hi_:
                                    _tally(finisher, (band, fb), chaser_result)
                        if (balls_left == CHASE_DIFF_BALLS_LEFT
                                and CHASE_DIFF_NEEDED[0] <= needed
                                <= CHASE_DIFF_NEEDED[1]
                                and (10 - wkts) >= CHASE_DIFF_MIN_WIH):
                            _tally(chase_diff, band, chaser_result)
                        if (league == "ipl"
                                and balls_left <= ENDGAME_MAX_BALLS_LEFT
                                and needed <= ENDGAME_MAX_NEEDED):
                            _tally(endgame, (needed, balls_left), chaser_result)

                legal, wkts, runs = legal2, wkts2, runs2
                if (iidx == 1 and league == "ipl" and season == 2008
                        and dl_["batter"] == ERA_SWAP_BATTER):
                    gil_tally[dl_["batter"]] = (
                        gil_tally.get(dl_["batter"], 0) + rb_)

            # ---- per-innings post work ----
            if usable and iidx == 1 and inn2_first_wp is not None:
                gap = abs(inn2_first_wp + inn2_sum
                          - (1.0 if chaser_result == 1 else 0.0))
                closure_max = max(closure_max, gap)
            if iidx <= 1 and not dl and band:
                total = runs
                cells = ball_cells.setdefault(band, {})
                rr = rr_band.setdefault(band, [0, 0])
                # replay the innings once more, cheaply, for state cells
                lg = wk = rs = 0
                for _ono, _bi, dl_ in deliveries:
                    rr[0] += dl_["runs"]["total"]
                    if _is_legal(dl_):
                        rr[1] += 1
                        if wk < 10:
                            c = cells.setdefault((lg, wk), [0.0, 0])
                            c[0] += total - rs
                            c[1] += 1
                        lg += 1
                    rs += dl_["runs"]["total"]
                    if "wickets" in dl_:
                        wk += len(dl_["wickets"])
            if iidx == 0 and not dl:
                total = runs
                if league == "ipl":
                    for wlab, lo_, hi_ in DRIFT_WINDOWS:
                        if lo_ <= season <= hi_:
                            oc = over_cells.setdefault(wlab, {})
                            for o, (rs, wk) in over_start.items():
                                if wk < 10:
                                    c = oc.setdefault((o, wk), [0.0, 0])
                                    c[0] += total - rs
                                    c[1] += 1
                else:
                    for o, (rs, wk) in over_start.items():
                        if wk < 10:
                            wpl_re_obs.setdefault((o, wk), []).append(total - rs)

        # ---- Gilchrist 2008 hundred (era-swap footnote), by identity ----
        hundreds = {b: r for b, r in gil_tally.items() if r >= 100}
        if hundreds:
            assert gil_match_index is None, \
                "era-swap exhibit expects exactly one 2008 Gilchrist chase hundred"
            batter, runs_scored = next(iter(hundreds.items()))
            gil_match_index = match_index
            balls_faced = sum(
                1 for over in inns[1]["overs"] for dl_ in over["deliveries"]
                if dl_["batter"] == batter and "wides" not in dl_.get("extras", {}))
            gil = {
                "record": flatten.match_record(info, league),
                "match_index": match_index,
                "batter": batter,
                "runs": runs_scored,
                "balls_faced": balls_faced,
                "target": target["runs"] if target else None,
            }

    n_points = point_index + 1
    assert len(wpa_bytes) == n_points
    assert len(restate) == n_points
    assert scrub is not None, "scrub match not found"
    assert gil is not None, "era-swap exhibit match not found"
    scrub["match_index"] = scrub_match_index

    return {
        "engines": engines,
        "files": files,
        "n_points": n_points,
        "wpa_bytes": bytes(wpa_bytes),
        "restate_bytes": bytes(restate),
        "n_sentinel": n_sentinel,
        "sentinel_matches": sentinel_matches,
        "lw": lw,
        "board": board,
        "ball_cells": ball_cells,
        "wicket_events": wicket_events,
        "rr_band": rr_band,
        "over_cells": over_cells,
        "wpl_re_obs": wpl_re_obs,
        "defended": defended,
        "finisher": finisher,
        "chase_diff": chase_diff,
        "endgame": endgame,
        "per_band_wpa": per_band_wpa,
        "team_cands": team_cands,
        "league_cands": league_cands,
        "closure_max": closure_max,
        "scrub": scrub,
        "gil": gil,
    }


# ---------------------------------------------------------------------------
# Wicket Value Index (raw ball-level state cells, both innings)
# ---------------------------------------------------------------------------


def wicket_value_by_band(acc: dict) -> dict:
    """Mean expected runs removed per bowler-credited wicket, per band:
    value = R(state, w) - R(state, w+1) at the ball's exact (legal-balls, w)
    raw cell pair (both innings, non-D/L). Events whose neighbour cell was
    never observed are skipped (counted)."""
    out = {}
    for band in BAND_ORDER:
        cells = acc["ball_cells"].get(band, {})
        vals = []
        skipped = 0
        for b, lb, w, kind in acc["wicket_events"]:
            if b != band or kind not in BOWLER_CREDITED or w >= 9:
                continue
            a = cells.get((lb, w))
            c = cells.get((lb, w + 1))
            if not a or not c or not a[1] or not c[1]:
                skipped += 1
                continue
            vals.append(a[0] / a[1] - c[0] / c[1])
        out[band] = {
            "expected_runs_removed": round(sum(vals) / len(vals), 3) if vals else None,
            "n_wickets": len(vals),
            "skipped_thin_states": skipped,
        }
    return out


def wicket_value_window(acc: dict, engines: dict, data_root: Path) -> dict:
    """The catalog teaser's sharper window (IPL 2024-2026) needs its own raw
    cell table; recount it from the same corpus, same recipe."""
    cells = {}
    events = []
    for _date, _mid, league, path in flatten.sorted_match_files(data_root):
        if league != "ipl":
            continue
        with open(path) as fh:
            m = json.load(fh)
        info = m["info"]
        if canon.is_dl(info):
            continue
        if not (2024 <= canon.canon_season(info) <= 2026):
            continue
        inns = [i for i in m.get("innings", []) if not canon.is_super_over(i)]
        for innings in inns[:2]:
            total = sum(dl_["runs"]["total"] for over in innings["overs"]
                        for dl_ in over["deliveries"])
            lg = wk = rs = 0
            for over in innings["overs"]:
                for dl_ in over["deliveries"]:
                    if _is_legal(dl_):
                        if wk < 10:
                            c = cells.setdefault((lg, wk), [0.0, 0])
                            c[0] += total - rs
                            c[1] += 1
                    for w_ev in dl_.get("wickets", []):
                        events.append((lg, wk, w_ev["kind"]))
                    if _is_legal(dl_):
                        lg += 1
                    rs += dl_["runs"]["total"]
                    if "wickets" in dl_:
                        wk += len(dl_["wickets"])
    vals = []
    for lb, w, kind in events:
        if kind not in BOWLER_CREDITED or w >= 9:
            continue
        a = cells.get((lb, w))
        c = cells.get((lb, w + 1))
        if a and c and a[1] and c[1]:
            vals.append(a[0] / a[1] - c[0] / c[1])
    return {
        "window": "ipl 2024-2026",
        "expected_runs_removed": round(sum(vals) / len(vals), 3) if vals else None,
        "n_wickets": len(vals),
    }


# ---------------------------------------------------------------------------
# Payoff cards
# ---------------------------------------------------------------------------


def _describe(ball: dict, innings: int) -> str:
    """Plain one-liner for a card. No em dashes (voice guide)."""
    chase = innings == 2 and ball.get("needed_before") is not None
    prefix = (f"Needing {ball['needed_before']} off "
              f"{ball['balls_left_before']}, " if chase else "")
    wk = ball.get("wicket")
    if wk:
        if wk["kind"] == "run out":
            body = f"{wk['player_out']} was run out"
        else:
            body = f"{wk['player_out']} was {_kind_text(wk['kind'])}"
            if wk["kind"] in ("caught", "bowled", "lbw", "stumped"):
                body += f" off {ball['bowler']}"
    else:
        rt = ball["runs_total"]
        if ball["runs_batter"] == 6:
            body = f"{ball['batter']} hit {ball['bowler']} for six"
        elif ball["runs_batter"] == 4:
            body = f"{ball['batter']} hit {ball['bowler']} for four"
        elif rt == 0:
            body = f"{ball['batter']} played out a dot from {ball['bowler']}"
        else:
            body = (f"{ball['batter']} took {rt} off {ball['bowler']}")
    text = prefix + body + "."
    return text[0].upper() + text[1:]


def _over_replay(acc: dict, match_index: int, innings_no: int, over_no: int,
                 franchise_batting: bool) -> list:
    """Re-derive one over's per-ball WP arc (franchise perspective) from the
    raw match file, with the exact per-ball state math of the main pass."""
    engines = acc["engines"]
    _date, _mid, league, path = acc["files"][match_index]
    with open(path) as fh:
        match = json.load(fh)
    info = match["info"]
    season = canon.canon_season(info)
    band = band_key(league, season)
    inns = [i for i in match.get("innings", []) if not canon.is_super_over(i)]
    innings = inns[innings_no - 1]
    target = inns[1].get("target") if len(inns) > 1 else None
    target_runs = target["runs"] if target else None
    chaser_result = wpmod.chaser_won(info, inns[1]["team"]) if len(inns) > 1 else None
    deliveries = [(over["over"], bi, dl_) for over in innings["overs"]
                  for bi, dl_ in enumerate(over["deliveries"])]
    n_del = len(deliveries)
    legal = wkts = runs = 0
    out = []
    for k, (ono, bi, dl_) in enumerate(deliveries):
        islegal = _is_legal(dl_)
        nw = len(dl_.get("wickets", []))
        rt = dl_["runs"]["total"]
        legal2, wkts2, runs2 = legal + (1 if islegal else 0), wkts + nw, runs + rt
        if ono == over_no:
            if innings_no == 1:
                b_wp = wp_first(engines, band, legal, wkts, runs)
                a_wp = (defend_p(engines, band, runs2) if k == n_del - 1
                        else wp_first(engines, band, legal2, wkts2, runs2))
            else:
                b_wp = wp_chase(engines, band, legal, wkts, runs, target_runs)
                a_wp = ((1.0 if chaser_result == 1 else 0.0) if k == n_del - 1
                        else wp_chase(engines, band, legal2, wkts2, runs2,
                                      target_runs))
            if not franchise_batting:
                b_wp, a_wp = 1.0 - b_wp, 1.0 - a_wp
            wk_list = dl_.get("wickets", [])
            row = {
                "label": f"{ono}.{bi + 1}",
                "batter": dl_["batter"],
                "bowler": dl_["bowler"],
                "runs_batter": dl_["runs"]["batter"],
                "runs_total": rt,
                "extras": sorted(dl_.get("extras", {})) or None,
                "wicket": ({"kind": wk_list[0]["kind"],
                            "player_out": wk_list[0]["player_out"]}
                           if wk_list else None),
                "wp_team_before": round(b_wp, 4),
                "wp_team_after": round(a_wp, 4),
                "swing_team": round(a_wp - b_wp, 4),
            }
            if innings_no == 2:
                row["needed_before"] = target_runs - runs
                row["balls_left_before"] = 120 - legal
            out.append(row)
        legal, wkts, runs = legal2, wkts2, runs2
    return out


def _ball_facts(acc: dict, match_index: int, over_no: int, bi: int,
                innings_no: int) -> dict:
    """Raw facts for one identified delivery."""
    _date, _mid, league, path = acc["files"][match_index]
    with open(path) as fh:
        match = json.load(fh)
    inns = [i for i in match.get("innings", []) if not canon.is_super_over(i)]
    innings = inns[innings_no - 1]
    target = inns[1].get("target") if len(inns) > 1 else None
    legal = wkts = runs = 0
    for over in innings["overs"]:
        for b_i, dl_ in enumerate(over["deliveries"]):
            if over["over"] == over_no and b_i == bi:
                wk_list = dl_.get("wickets", [])
                facts = {
                    "batter": dl_["batter"],
                    "bowler": dl_["bowler"],
                    "runs_batter": dl_["runs"]["batter"],
                    "runs_total": dl_["runs"]["total"],
                    "extras": sorted(dl_.get("extras", {})) or None,
                    "wicket": ({"kind": wk_list[0]["kind"],
                                "player_out": wk_list[0]["player_out"]}
                               if wk_list else None),
                    "batting_team": canon.canon_team(innings["team"]),
                    # the ball's restate.u8 cell (over*10 + wickets down
                    # BEFORE the delivery) — lets the payoff scene register
                    # its single-point ignite to the exact worth-grid cell
                    "state_cell": over_no * 10 + min(wkts, 9),
                }
                if innings_no == 2 and target:
                    facts["needed_before"] = target["runs"] - runs
                    facts["balls_left_before"] = 120 - legal
                return facts
            if _is_legal(dl_):
                legal += 1
            runs += dl_["runs"]["total"]
            if "wickets" in dl_:
                wkts += len(dl_["wickets"])
    raise KeyError(f"delivery not found: m{match_index} {over_no}.{bi}")


def payoff_section(acc: dict, matches: list) -> dict:
    variants = []
    for team in canon.TEAMS:
        tid = team["id"]
        cands = sorted(acc["team_cands"][tid],
                       key=lambda r: (-r[0], r[1], r[2]))
        picked = []
        seen_matches = set()
        for sw, mi, pi, iidx, ono, bi in cands:
            if mi in seen_matches:
                continue
            seen_matches.add(mi)
            picked.append((sw, mi, pi, iidx, ono, bi))
            if len(picked) == PAYOFF_TOP_N:
                break
        rows = []
        for sw, mi, pi, iidx, ono, bi in picked:
            rec = matches[mi]
            facts = _ball_facts(acc, mi, ono, bi, iidx + 1)
            batting = facts["batting_team"] == team["name"] and \
                rec["league"] == team["league"]
            opponent = [t for t in rec["teams"] if t != team["name"]]
            rows.append({
                "swing": round(sw, 4),
                "match_index": mi,
                "point_index": pi,
                "season": rec["season"],
                "date": rec["date"],
                "stage": rec["stage"],
                "venue": rec["venue"],
                "result_text": rec["result_text"],
                "opponent": opponent[0] if opponent else None,
                "innings": iidx + 1,
                "over": ono,
                "label": f"{ono}.{bi + 1}",
                "batting": batting,
                "what_happened": _describe(facts, iidx + 1),
                **{k: facts[k] for k in ("batter", "bowler", "runs_batter",
                                         "runs_total", "extras", "wicket",
                                         "state_cell")},
                **({"needed_before": facts["needed_before"],
                    "balls_left_before": facts["balls_left_before"]}
                   if "needed_before" in facts else {}),
            })
        top = rows[0] if rows else None
        replay = None
        if top:
            replay = {
                "innings": top["innings"],
                "over": top["over"],
                "balls": _over_replay(acc, top["match_index"], top["innings"],
                                      top["over"], top["batting"]),
            }
            wp_arc = replay["balls"]
            # the card quotes the team-perspective WP around its top ball
            tb = next(b for b in wp_arc if b["label"] == top["label"])
            top["wp_team_before"] = tb["wp_team_before"]
            top["wp_team_after"] = tb["wp_team_after"]
        variants.append({
            "team_id": tid,
            "team": team["name"],
            "short": team["short"],
            "league": team["league"],
            "active": team["active"],
            "short_history": team["league"] == "wpl",
            "honesty": ("Four seasons of WPL cricket so far. This is the most "
                        "valuable ball of a short history, and the list will "
                        "be fought over for years."
                        if team["league"] == "wpl" else ""),
            "most_valuable": top,
            "replay": replay,
            "runners_up": rows[1:],
            "empty_state": top is None,
        })
    return {
        "note": (
            "One card per franchise (league-scoped ids from teams.json; "
            "renames collapse, so Delhi Daredevils balls count for Delhi "
            "Capitals). The most valuable ball is the biggest single-ball win "
            "probability swing TOWARD the franchise in its history, batting "
            "or bowling; swings are read from the same per-ball WPA that "
            "fills wpa.u8. The replay is the full over around that ball with "
            "the team-perspective worm. Runners-up come from distinct "
            "matches so the list reads as five nights, not one over."
        ),
        "min_swing_considered": PAYOFF_MIN_SWING,
        "variants": variants,
    }


# ---------------------------------------------------------------------------
# Scene-doc sections
# ---------------------------------------------------------------------------


def r3(x):
    return round(x, 3) if x is not None else None


def defended_section(acc: dict) -> dict:
    engines = acc["engines"]
    rows = {}
    for band in BAND_ORDER:
        d = acc["defended"].get(band, [0, 0])
        rows[band] = {
            "defended": d[0],
            "n": d[1],
            "pct": round(100.0 * d[0] / d[1], 1) if d[1] else None,
        }
    fitted = {}
    labels = engines["defend"][EARLY]["bucket_labels"]
    i170, i180 = labels.index("170-179"), labels.index("180-189")
    for band in (EARLY, RECENT):
        row = engines["defend"][band]
        n = row["n"][i170] + row["n"][i180]
        p = ((row["p_batfirst_win"][i170] * row["n"][i170]
              + row["p_batfirst_win"][i180] * row["n"][i180]) / n) if n else None
        fitted[band] = {"p_batfirst_win": r3(p), "n": n}
    return {
        "band": f"{DEFENDED_LO}-{DEFENDED_HI}",
        "definition": (
            "First-innings totals of 170 to 189 in full first innings (20 "
            "overs bowled or all out), decided matches only (ties count for "
            "the super-over winner), D/L excluded. 'Defended' means the team "
            "batting first won."
        ),
        "raw": rows,
        "fitted_curve_170_189": fitted,
        "headline": {
            "early_pct": rows[EARLY]["pct"],
            "recent_pct": rows[RECENT]["pct"],
            "delta_points": round(rows[EARLY]["pct"] - rows[RECENT]["pct"], 1),
        },
        "validation": (
            "Catalog teaser: 74% (2008-10) vs 38% (2023-26) on an earlier "
            "corpus snapshot. This recount is authoritative: "
            f"{acc['defended'][EARLY][0]}/{acc['defended'][EARLY][1]} vs "
            f"{acc['defended'][RECENT][0]}/{acc['defended'][RECENT][1]}."
        ),
    }


def re_drift_section(acc: dict) -> dict:
    engines = acc["engines"]
    re_a = engines["re"][EARLY]
    re_b = engines["re"][RECENT]
    diff = [[round(re_b[o][w] - re_a[o][w], 1) for w in range(10)]
            for o in range(20)]

    def phase_mean(rows):
        cells = [diff[o][w] for o in rows for w in range(10)]
        return round(sum(cells) / len(cells), 1)

    def raw_cost(window):
        oc = acc["over_cells"].get(window, {})
        a = oc.get((DRIFT_OVER, 2))
        b = oc.get((DRIFT_OVER, 3))
        if not a or not b or not a[1] or not b[1]:
            return None
        return {
            "re_2_down": round(a[0] / a[1], 1),
            "re_3_down": round(b[0] / b[1], 1),
            "n_2_down": a[1],
            "n_3_down": b[1],
            "third_wicket_cost": round(a[0] / a[1] - b[0] / b[1], 2),
        }

    return {
        "era_a": EARLY,
        "era_b": RECENT,
        "re_a": re_a,
        "re_b": re_b,
        "n_a": engines["re_n"][EARLY],
        "n_b": engines["re_n"][RECENT],
        "diff": diff,
        "diff_by_phase": {
            "powerplay_overs_1_6": phase_mean(range(0, 6)),
            "middle_overs_7_15": phase_mean(range(6, 15)),
            "death_overs_16_20": phase_mean(range(15, 20)),
        },
        "grid_note": (
            "Cells are the gate-validated engine surfaces verbatim "
            "(engines/re288.json): expected first-innings runs still to come "
            "from (overs bowled, wickets down), smoothed monotone. diff = "
            "recent minus early. The morph colors every ball by its "
            "restate.u8 cell on these surfaces."
        ),
        "third_wicket": {
            "state": ("start of the 7th over (6 overs bowled), 2 down versus "
                      "3 down; raw observed runs-to-come, first innings, "
                      "IPL, non-D/L"),
            "raw": {w: raw_cost(w) for w, _l, _h in DRIFT_WINDOWS},
            "engine_fitted": {
                EARLY: round(re_a[DRIFT_OVER][2] - re_a[DRIFT_OVER][3], 2),
                RECENT: round(re_b[DRIFT_OVER][2] - re_b[DRIFT_OVER][3], 2),
            },
            "validation": (
                "Catalog teaser: ~12 expected runs (2008-10) to ~0.4 "
                "(2024-26, earlier snapshot). This recount is authoritative: "
                "the raw third-wicket cost at the same state is ~11.8 then "
                "and ~1.0 in 2024-2026 (~3.5 across the full 2023-2026 "
                "band). The smoothed engine surface spreads thin-cell "
                "evidence to neighbours, so its fitted gap reads higher; "
                "both are shown."
            ),
        },
    }


def linear_weights_section(acc: dict) -> dict:
    classes = ("dot", "single", "two", "three", "four", "six", "wide", "wicket")
    bands = {}
    for band in BAND_ORDER:
        row = {}
        for cls in classes:
            c = acc["lw"].get((band, cls))
            row[cls] = ({"value": r3(c[0] / c[1]), "n": c[1]} if c else None)
        two, three = acc["lw"].get((band, "two")), acc["lw"].get((band, "three"))
        if two and three:
            row["two_or_three"] = {
                "value": r3((two[0] + three[0]) / (two[1] + three[1])),
                "n": two[1] + three[1],
            }
        bands[band] = row
    early, recent = bands[EARLY], bands[RECENT]
    return {
        "method": (
            "weight(outcome) = RE(after state) - RE(before state) + runs "
            "scored on the ball, priced on the era's gate-validated RE "
            "surface (interpolated across the over axis), first innings "
            "only, non-D/L. Wicket balls are priced as one wicket event "
            "(their runs included) and excluded from the run classes. This "
            "is the wOBA derivation, translated."
        ),
        "era_bands": bands,
        "headline": {
            "dot": {"early": early["dot"]["value"],
                    "recent": recent["dot"]["value"]},
            "single": {"early": early["single"]["value"],
                       "recent": recent["single"]["value"]},
            "six": {"early": early["six"]["value"],
                    "recent": recent["six"]["value"]},
            "wicket_event": {"early": early["wicket"]["value"],
                             "recent": recent["wicket"]["value"]},
        },
        "validation": (
            "Catalog teasers: the dot deepened -0.85 to -1.12 and the single "
            "flipped -0.01 to -0.27. This recount is authoritative: dot "
            f"{early['dot']['value']} to {recent['dot']['value']}, single "
            f"{early['single']['value']} to {recent['single']['value']}. The "
            "single flipped from value-neutral to value-losing; rotating "
            "strike now loses expected runs. Sixes hold near +4.6."
        ),
    }


def price_board_section(acc: dict) -> dict:
    seasons = []
    keys = sorted({(lg, s) for (lg, s, _c) in acc["board"]},
                  key=lambda k: (k[0], k[1]))
    for lg, s in keys:
        row = {"league": lg, "season": s}
        for cls in ("dot", "single", "four", "six", "wicket"):
            c = acc["board"].get((lg, s, cls))
            row[cls] = r3(c[0] / c[1]) if c else None
        two, three = (acc["board"].get((lg, s, "two")),
                      acc["board"].get((lg, s, "three")))
        n2 = (two[1] if two else 0) + (three[1] if three else 0)
        row["two_or_three"] = (
            r3(((two[0] if two else 0.0) + (three[0] if three else 0.0)) / n2)
            if n2 else None)
        row["n_balls"] = sum(acc["board"][(lg, s, c)][1]
                             for c in ("dot", "single", "two", "three", "four",
                                       "six", "wide", "wicket", "other")
                             if (lg, s, c) in acc["board"])
        seasons.append(row)
    return {
        "note": (
            "The outcome price board: each season's balls priced on its own "
            "era band's RE surface (surfaces are per era band, so within a "
            "band the season-to-season movement comes from where in the "
            "innings the outcomes actually happened). First innings, "
            "non-D/L. Values are expected runs, ready for the ticker."
        ),
        "seasons": seasons,
    }


def wicket_value_section(acc: dict, wvi_window: dict) -> dict:
    by_band = wicket_value_by_band(acc)
    early = by_band[EARLY]["expected_runs_removed"]
    recent = by_band[RECENT]["expected_runs_removed"]
    rr = {}
    for band in (EARLY, RECENT):
        runs, legal = acc["rr_band"][band]
        rr[band] = round(runs * 6.0 / legal, 3)
    infl = round(100.0 * (rr[RECENT] / rr[EARLY] - 1.0), 1)
    appr = round(100.0 * (recent / early - 1.0), 1)
    return {
        "method": (
            "Each bowler-credited wicket (caught, bowled, lbw, stumped, "
            "caught and bowled, hit wicket) priced as R(state, w) minus "
            "R(state, w+1) at its exact (legal balls bowled, wickets) state, "
            "using raw observed runs-to-come cells over both innings, "
            "non-D/L (a chase that ends early is real evidence that runs "
            "stopped coming). Run outs are excluded from bowler credit."
        ),
        "by_band": by_band,
        "window_2024_2026": wvi_window,
        "run_rate_context": {
            "rr_early": rr[EARLY],
            "rr_recent": rr[RECENT],
            "run_inflation_pct": infl,
            "wicket_appreciation_pct": appr,
        },
        "headline": {
            "early": early,
            "recent": recent,
            "appreciation_pct": appr,
        },
        "validation": (
            "Catalog teaser: 3.99 to 5.30 (+33%) with the recent window "
            "read as 2024-26 on an earlier snapshot. This recount is "
            f"authoritative: {early} to {recent} across the chapter's era "
            f"bands (+{appr}%), and {wvi_window['expected_runs_removed']} "
            "on the 2024-2026 window (+"
            f"{round(100.0 * (wvi_window['expected_runs_removed'] / early - 1.0), 1)}"
            "%). Wicket appreciation outpaces run inflation "
            f"(+{infl}%) on both readings."
        ),
    }


def finisher_section(acc: dict) -> dict:
    table = {}
    for band in BAND_ORDER:
        row = {}
        for fb, _lo, _hi in FINISHER_BANDS:
            c = acc["finisher"].get((band, fb), [0, 0])
            row[fb] = {"wins": c[0], "n": c[1],
                       "win_pct": round(100.0 * c[0] / c[1], 1) if c[1] else None}
        table[band] = row
    e, r = table[EARLY], table[RECENT]
    return {
        "state": (
            "Chases read at exactly 30 balls left (the start of the final "
            "five overs), 20-over targets, non-D/L, decided (ties count for "
            "the super-over winner). Bands are the required rate at that "
            "moment."
        ),
        "table": table,
        "headline": {
            "band": "8-10",
            "early": e["8-10"],
            "recent": r["8-10"],
        },
        "fatal_rrr": {
            "note": (
                "The fatal required rate is where a chase becomes a loser "
                "more often than not. In 2008-10 the coin flip died between "
                "8-10 (won 54.8%) and 10-12 (won 34.6%): fatal near 10. In "
                "2023-26 the 10-12 band is a genuine contest and only 12+ "
                "collapses: fatal near 12."
            ),
            "early_10_12_pct": e["10-12"]["win_pct"],
            "recent_10_12_pct": r["10-12"]["win_pct"],
            "early_12_plus_pct": e["12+"]["win_pct"],
            "recent_12_plus_pct": r["12+"]["win_pct"],
        },
        "validation": (
            "Catalog teasers: 54.8% then, 85.0% now for the 8-10 band; at "
            "10-12 the jump was 34.6% to 51.4%. This recount is "
            f"authoritative: {e['8-10']['wins']}/{e['8-10']['n']} "
            f"({e['8-10']['win_pct']}%) to {r['8-10']['wins']}/"
            f"{r['8-10']['n']} ({r['8-10']['win_pct']}%); 10-12 "
            f"{e['10-12']['win_pct']}% to {r['10-12']['win_pct']}%."
        ),
    }


def scrub_section(acc: dict) -> dict:
    scrub = acc["scrub"]
    balls = scrub["balls"]
    entering = {
        "score": scrub["target"] - balls[0]["needed_before"],
        "needed": balls[0]["needed_before"],
        "balls_left": balls[0]["balls_left_before"],
        "wickets_down": 10 - balls[0]["wickets_in_hand_before"],
        "bowler": balls[0]["bowler"],
    }
    for b in balls:
        c = acc["endgame"].get((b["needed_before"], b["balls_left_before"]),
                               [0, 0])
        b["observed"] = {"wins": c[0], "n": c[1],
                         "win_pct": round(100.0 * c[0] / c[1], 1) if c[1] else None}
    return {
        "match_index": scrub["match_index"],
        "match": scrub["record"],
        "era_surface": scrub["era"],
        "target": scrub["target"],
        "entering": entering,
        "balls": balls,
        # the six field point indices in bowling order — the over-rail lift
        # reads THESE (CONTRACT §20), never a runtime columnar derivation
        "point_indices": [b["point_index"] for b in balls],
        "perspective": (
            "wp_before / wp_after are P(the chasing team, Chennai Super "
            "Kings, wins) from the era grid; Mumbai's number is one minus "
            "that. The final ball resolves to the actual result."
        ),
        "worm_note": (
            "The grid buckets required rate, so consecutive balls can share "
            "a cell and the grid worm holds flat across them (balls 1, 3 "
            "and 5 here). Each ball also carries `observed`: the raw all-IPL "
            "win count from that exact (needed, balls left) state, honest "
            "pub-fact texture the scene may draw as dots beside the worm."
        ),
        "validation": (
            "Extracted from the raw 2019 final (resolved by identity, never "
            "a hard-coded index): Malinga bowled all six, Chennai needed 9, "
            "Watson was run out on ball 4, Thakur was lbw on the last ball, "
            "Mumbai won by 1 run."
        ),
    }


def wpa_section(acc: dict, matches: list) -> dict:
    def swing_row(w, mi, pi, iidx, ono, bi):
        rec = matches[mi]
        facts = _ball_facts(acc, mi, ono, bi, iidx + 1)
        return {
            "wpa": round(w, 4),
            "match_index": mi,
            "point_index": pi,
            "state_cell": facts["state_cell"],
            "league": rec["league"],
            "season": rec["season"],
            "teams": rec["teams"],
            "stage": rec["stage"],
            "result_text": rec["result_text"],
            "innings": iidx + 1,
            "label": f"{ono}.{bi + 1}",
            "batter": facts["batter"],
            "bowler": facts["bowler"],
            "what_happened": _describe(facts, iidx + 1),
        }

    ranked = sorted(acc["league_cands"], key=lambda r: (-abs(r[0]), r[1], r[2]))
    league_rows = []
    seen = set()
    for w, mi, pi, iidx, ono, bi in ranked:
        if mi in seen:
            continue
        seen.add(mi)
        league_rows.append(swing_row(w, mi, pi, iidx, ono, bi))
        if len(league_rows) == TOP_SWINGS_N:
            break

    # the neutral payoff gallery: ONE ball per (league, season) — the biggest
    # single-ball swing that season, ordered ipl-then-wpl by season (storyboard
    # §4 payoff QA: "the neutral gallery lists one ball per season")
    best_by_season = {}
    for cand in ranked:
        rec = matches[cand[1]]
        key = (rec["league"], rec["season"])
        if key not in best_by_season:
            best_by_season[key] = cand
    season_gallery = [
        swing_row(*best_by_season[key])
        for key in sorted(best_by_season,
                          key=lambda k: (k[0] != "ipl", k[0], k[1]))
    ]
    per_band = {}
    for band in BAND_ORDER:
        s, n = acc["per_band_wpa"].get(band, (0.0, 0))
        per_band[band] = {"mean_abs_wpa": round(s / n, 4) if n else None, "n": n}
    return {
        "perspective": (
            "WPA is the ball's change in the BATTING team's win probability. "
            "First innings uses the derived projected-total view; second "
            "innings reads the era grid; terminal balls resolve to the "
            "result (ties to the super-over winner)."
        ),
        "per_band": per_band,
        "swinginess_note": (
            "Mean absolute WPA per ball is roughly flat across eras (about "
            "0.013 to 0.016). Modern matches are not measurably swingier "
            "ball for ball; what changed is the price of the outcomes, not "
            "the volatility of the scoreboard."
        ),
        "top_swings": league_rows,
        "season_gallery": season_gallery,
        "closure": {
            "max_abs_gap": acc["closure_max"],
            "note": (
                "For every scored chase, first-state WP plus the sum of its "
                "per-ball WPA equals the result exactly (the states chain, "
                "so the sum telescopes). The max gap is floating-point "
                "noise."
            ),
        },
        "coverage": {
            "balls_scored": acc["n_points"] - acc["n_sentinel"],
            "balls_sentinel": acc["n_sentinel"],
            "sentinel_matches": acc["sentinel_matches"],
        },
    }


def wpl_section(acc: dict) -> dict:
    engines = acc["engines"]
    mask = engines["re_mask"]
    masked_cells = [[o, w] for o in range(20) for w in range(10)
                    if mask[o][w]]
    dots = []
    for o in range(20):
        for w in range(10):
            if mask[o][w]:
                obs = sorted(acc["wpl_re_obs"].get((o, w), []))
                if obs:
                    dots.append({
                        "o": o, "w": w, "n": len(obs),
                        "observed_runs_to_come": obs,
                        "mean": round(sum(obs) / len(obs), 1),
                    })
    fin = acc["finisher"].get((WPL_KEY, "8-10"), [0, 0])
    dfd = acc["defended"].get(WPL_KEY, [0, 0])
    n_wpl = sum(1 for _d, _m, lg, _p in acc["files"] if lg == "wpl")
    return {
        # counted from the corpus, never typed — the C5-10 step-1 literals
        # ("88 matches, not 1,331") trace to these fields (storyboard §3)
        "match_counts": {
            "ipl": len(acc["files"]) - n_wpl,
            "wpl": n_wpl,
            "total": len(acc["files"]),
        },
        "mask": {
            "min_n": engines["re_mask_min_n"],
            "masked_cells": masked_cells,
            "cells_masked": len(masked_cells),
            "cells_evidenced": 200 - len(masked_cells),
            "note": (
                "The same minimum-evidence mask as the interlude: a WPL RE "
                "cell under n renders hatched, 'not enough WPL cricket "
                "yet', never a fitted value presented as a finding."
            ),
        },
        "observed_dots": {
            "note": (
                "Where the mask bites and any cricket has been played, the "
                "honest alternative to a fake surface: every raw observed "
                "runs-to-come outcome from that state, drawn as dots on the "
                "IPL grid."
            ),
            "cells": dots,
        },
        "re_surface": engines["re"][WPL_KEY],
        "re_n": engines["re_n"][WPL_KEY],
        "finisher_8_10": {
            "wins": fin[0], "n": fin[1],
            "win_pct": round(100.0 * fin[0] / fin[1], 1) if fin[1] else None,
            "note": (
                "The WPL finisher cohort is forming live. Chases needing "
                "8-10 an over with five overs left sit between the IPL's "
                "two eras on a tiny sample; the catalog read ~75% on an "
                "earlier snapshot."
            ),
        },
        "defended_170_189": {
            "defended": dfd[0], "n": dfd[1],
            "pct": round(100.0 * dfd[0] / dfd[1], 1) if dfd[1] else None,
        },
    }


def footnotes_section(acc: dict) -> dict:
    engines = acc["engines"]
    gil = acc["gil"]
    wp08 = wp_chase(engines, EARLY, 0, 0, 0, gil["target"])
    wp23 = wp_chase(engines, RECENT, 0, 0, 0, gil["target"])
    cd = {}
    for band in BAND_ORDER:
        c = acc["chase_diff"].get(band, [0, 0])
        cd[band] = {"wins": c[0], "n": c[1],
                    "win_pct": round(100.0 * c[0] / c[1], 1) if c[1] else None}
    return {
        "crediting": (
            "wpa.u8 carries the ball's swing for the BATTING team; a "
            "bowling-side reading is its negation, which is how the payoff "
            "cards credit defensive balls. Striker/bowler player crediting "
            "(baseball's split) is a sandbox-era concern and is not encoded "
            "in the buffer."
        ),
        "tie_rule": (
            "Ties resolve to the super-over winner (outcome.eliminator), "
            "matching the win-probability engine. Super-over balls "
            "themselves are not in the point stream."
        ),
        "first_innings_wp": {
            "method": (
                "Mid-first-innings win probability is a derived view, the "
                "one the engine module designates for R3b: P(bat-first "
                "wins) read from the era defend curve at a projected total "
                "of runs so far plus the era RE surface's runs-to-come at "
                "the ball's state. The defend curve interpolates "
                "piecewise-linearly between bucket midpoints."
            ),
            "defend_anchor_totals": list(DEFEND_X),
            "honesty": (
                "The full catalog method is P(defend t) x P(reach t | "
                "state) over all t; projecting the expected total is the "
                "documented simplification, and second-innings WPA (where "
                "every headline lives) uses the grid exactly."
            ),
        },
        "smoothing": {
            "wp_grid_calibration_ece": engines["calibration_ece"],
            "note": (
                "Both engines are gate-validated lookups: the WP grid's "
                "reliability check holds ECE under 0.03 and the RE "
                "surfaces are weighted-isotonic smoothed, monotone in both "
                "axes. Raw recounts back every validation number in this "
                "chapter; where a raw cell and the smoothed surface "
                "disagree, both are shown."
            ),
        },
        "chase_difficulty": {
            "definition": (
                "Chases needing 30 to 42 off the last 24 balls with at "
                "least 5 wickets in hand, read at exactly 24 balls left."
            ),
            "by_band": cd,
            "validation": (
                "Catalog teaser 69% to 88%; this recount is authoritative: "
                f"{cd[EARLY]['win_pct']}% (2008-10) to "
                f"{cd[RECENT]['win_pct']}% (2023-26)."
            ),
        },
        "era_swap": {
            "note": (
                "The demoted counterfactual, one click deep: the same "
                "scoreboard priced under two eras' physics. Gilchrist's "
                "2008 hundred won a chase whose failure chance at ball one "
                "was 29 in 100 on the 2008-10 grid; the identical target "
                "carries 16 in 100 on the 2023-26 grid. The doubt his "
                "innings erased has nearly halved since."
            ),
            "match_index": gil["match_index"],
            "match": gil["record"],
            "batter": gil["batter"],
            "runs": gil["runs"],
            "balls_faced": gil["balls_faced"],
            "target": gil["target"],
            "chase_start_wp_2008_2010": round(wp08, 3),
            "chase_start_wp_2023_2026": round(wp23, 3),
        },
    }


# ---------------------------------------------------------------------------
# Doc assembly + emission
# ---------------------------------------------------------------------------


def build_doc(data_root: Path = canon.DATA_ROOT):
    acc = build(data_root)
    matches = [flatten.match_record(json.load(open(p))["info"], lg)
               for _d, _m, lg, p in acc["files"]]
    wvi_window = wicket_value_window(acc, acc["engines"], data_root)
    doc = {
        "chapter": 5,
        "title": "What a Ball Is Worth",
        "register": "everything gets repriced",
        "era_bands": {
            "ipl": [f"ipl {label}" for label, _l, _h in IPL_ERA_BANDS],
            "wpl": WPL_KEY,
        },
        "engines_consumed": {
            "win": "engines/wp_grid.json",
            "runs": "engines/re288.json",
            "note": (
                "Gate-validated lookups, consumed verbatim; this chapter "
                "adds derived views only (documented in footnotes)."
            ),
        },
        "defended_band": defended_section(acc),
        "re_drift": re_drift_section(acc),
        "linear_weights": linear_weights_section(acc),
        "price_board": price_board_section(acc),
        "wicket_value": wicket_value_section(acc, wvi_window),
        "finisher": finisher_section(acc),
        "scrub": scrub_section(acc),
        "wpa": wpa_section(acc, matches),
        "payoff": payoff_section(acc, matches),
        "wpl_beat": wpl_section(acc),
        "footnotes": footnotes_section(acc),
        "wpa_buffer": {
            "file": "wpa.u8",
            "bytes_per_point": 1,
            "point_order": flatten.POINT_ORDER,
            "encoding": "byte = 127 + round(wpa * 127), clamped to 0..254",
            "decode": "wpa = (byte - 127) / 127",
            "lo": -1.0,
            "hi": 1.0,
            "zero_byte": 127,
            "sentinel": WPA_SENTINEL,
            "sentinel_meaning": (
                "no WPA for this ball: its match is D/L, had no decided "
                "result, or set a chase target other than a full 20 overs "
                "(exactly the matches the win grids exclude)"
            ),
            "sentinel_count": acc["n_sentinel"],
            "perspective": "batting team",
        },
        "restate_buffer": {
            "file": "restate.u8",
            "bytes_per_point": 1,
            "point_order": flatten.POINT_ORDER,
            "encoding": "byte = over * 10 + wickets_down (0..199)",
            "decode": "over = byte // 10; wickets_down = byte % 10",
            "conventions": (
                "over is the delivery's over index 0..19; wides and "
                "no-balls carry the over they were bowled in. wickets_down "
                "counts dismissals before this delivery (0..9). Both "
                "innings are packed; filter with the columnar innings "
                "array when a scene wants first innings only. attrs.u8 is "
                "untouched, so every earlier scene renders byte-identically."
            ),
        },
    }
    return doc, acc


def main(out_root: Path = canon.OUT_ROOT) -> dict:
    doc, acc = build_doc()
    out_root.mkdir(parents=True, exist_ok=True)
    scenes_dir = out_root / "scenes"
    scenes_dir.mkdir(parents=True, exist_ok=True)

    sizes = {}
    (out_root / "wpa.u8").write_bytes(acc["wpa_bytes"])
    sizes["wpa.u8"] = {
        "bytes_raw": len(acc["wpa_bytes"]),
        "bytes_gz": len(flatten.gz_bytes(acc["wpa_bytes"])),
    }
    (out_root / "restate.u8").write_bytes(acc["restate_bytes"])
    sizes["restate.u8"] = {
        "bytes_raw": len(acc["restate_bytes"]),
        "bytes_gz": len(flatten.gz_bytes(acc["restate_bytes"])),
    }
    raw = flatten.compact_json(doc, sort_keys=True)
    (scenes_dir / "ch5.json").write_bytes(raw)
    sizes["scenes/ch5.json"] = {
        "bytes_raw": len(raw),
        "bytes_gz": len(flatten.gz_bytes(raw)),
    }

    # Register in meta.json's manifest (merge, like bowlerplane.py). Run
    # AFTER flatten + scenes per the README order so the insertion order,
    # and therefore meta.json, stays byte-deterministic.
    meta_path = out_root / "meta.json"
    if meta_path.exists():
        meta = json.loads(meta_path.read_text())
        meta.setdefault("files", {}).update(sizes)
        meta_path.write_bytes(flatten.compact_json(meta))

    for name, s in sizes.items():
        print(f"  {name:18s} raw={s['bytes_raw']:>9,}  gz={s['bytes_gz']:>8,}")
    d = doc["defended_band"]["headline"]
    print(f"ch5 defended 170-189: {d['early_pct']}% -> {d['recent_pct']}%")
    tw = doc["re_drift"]["third_wicket"]["raw"]
    print(f"ch5 3rd wicket at over 7: {tw['2008-2010']['third_wicket_cost']}"
          f" -> {tw['2023-2026']['third_wicket_cost']} (2023-26), "
          f"{tw['2024-2026']['third_wicket_cost']} (2024-26)")
    lwh = doc["linear_weights"]["headline"]
    print(f"ch5 linear weights: dot {lwh['dot']['early']} -> {lwh['dot']['recent']}, "
          f"single {lwh['single']['early']} -> {lwh['single']['recent']}")
    wv = doc["wicket_value"]["headline"]
    print(f"ch5 wicket value: {wv['early']} -> {wv['recent']} (+{wv['appreciation_pct']}%)")
    fh = doc["finisher"]["headline"]
    print(f"ch5 finisher 8-10 @ 5 overs left: {fh['early']['win_pct']}% -> "
          f"{fh['recent']['win_pct']}%")
    sc = doc["scrub"]
    print(f"ch5 scrub: match_index={sc['match_index']} "
          f"({sc['match']['result_text']}), {len(sc['balls'])} balls, "
          f"era={sc['era_surface']}")
    cov = doc["wpa"]["coverage"]
    print(f"ch5 wpa buffer: {cov['balls_scored']:,} scored, "
          f"{cov['balls_sentinel']:,} sentinel; closure gap "
          f"{doc['wpa']['closure']['max_abs_gap']:.2e}")
    n_pay = len(doc["payoff"]["variants"])
    print(f"ch5 payoff: {n_pay} franchise cards")
    return doc


if __name__ == "__main__":
    main()
