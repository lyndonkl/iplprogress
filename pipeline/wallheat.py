"""Chapter-1 ignition-wall ERA-RELATIVE INTENT buffer (R1a refinement).

The wall (storyboard C1-2) places every ball by (balls-faced -> x, season ->
y) and, in the establishing shot, colours it by OUTCOME. That establishing
shot has a strong left->right gradient (strike rate climbs ~74 -> 140 over a
batter's first 20 balls in EVERY era) which drowns out the chapter's actual
thesis: the early-ball corner got hotter over the YEARS. This module emits the
extra per-point buffer that powers the THESIS BEAT recolour.

wallheat.u8 -- one byte per delivery, in the same point order as attrs.u8 /
ballsfaced.u8 / team.u8 -- encodes how much hotter a ball's (league, season,
clamped ball-index) cell strike rate is than the pooled IPL 2008-2010 batter
at the SAME ball-index. Baselining each ball-index COLUMN to its own 2008-10
value removes the horizontal (set-in) gradient, so the wall's bottom-left
corner ignites bottom->top: recent seasons glow hot exactly where they most
exceed 2008.

Encoding (diverging, robust):
  n           = clamp(ballsfaced, 1, 30)            # the wall's 30+ column caps
  cellSR[L,S,n]   = 100 * mean(runs_batter) over deliveries in that cell
  baselineSR[n]   = pooled IPL 2008,2009,2010 cellSR at ball-index n
  delta (runs/ball) = cellSR/100 - baselineSR/100   # vs the 2008-10 batter
  byte        = clamp(round((delta - LO)/(HI - LO) * 255), 0, 255)
  ballsfaced == 0 (a wide -- not faced) -> NEUTRAL_BYTE (= byte at delta 0)

LO/HI are fixed clean values chosen as the rounded ~2nd/98th percentile of the
per-delivery delta distribution (p2 ~= -0.16, p98 ~= +0.43 runs/ball): a delta
of +0.5 runs/ball is +50 strike-rate points over the 2008-10 batter, -0.2 is
-20. The neutral pivot sits at delta 0 (byte 73) -- the establishing outcome
shot and the six-fireworks two-tone are unchanged; this buffer only feeds the
separate thesis-beat blend.

Stdlib only; byte-deterministic. `compute()` runs off the flatten pass's
already-materialised per-delivery arrays (no re-read); `build()` does its own
season-blocked pass for callers that only need the config (scenes.py) or an
independent recompute (tests). Both funnel through the same core, so the
emitted buffer and the ch1.json config are consistent by construction.
"""

from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import canon

# ---------------------------------------------------------------------------
# Diverging-scale contract (see module docstring)
# ---------------------------------------------------------------------------

MAX_BALL_INDEX = 30  # matches ballsfaced.u8 wall cap (the "30+" right column)
IPL, WPL = 0, 1  # league codes (== flatten col["league"])
BASELINE_LEAGUE = IPL
BASELINE_SEASONS = (2008, 2009, 2010)  # the 2008-10 batter, per ball-index

# delta (runs per ball vs the 2008-10 batter at the same ball-count) window.
# Rounded ~2nd/98th percentiles of the per-delivery delta distribution
# (p2 ~= -0.16, p98 ~= +0.43); clips ~1.4% cool / ~0.7% hot. delta 0 = the
# 2008-10 batter exactly.
LO = -0.2  # -20 strike-rate points
HI = 0.5  # +50 strike-rate points


def clamp_n(ballsfaced: int) -> int:
    """Ball-index a delivery lands on in the wall (>= 30 folds into 30+)."""
    return MAX_BALL_INDEX if ballsfaced > MAX_BALL_INDEX else (1 if ballsfaced < 1 else ballsfaced)


def quantize(delta: float) -> int:
    """Diverging delta (runs/ball) -> 0..255, neutral (delta 0) fixed."""
    v = round((delta - LO) / (HI - LO) * 255)
    return 0 if v < 0 else 255 if v > 255 else v


NEUTRAL_BYTE = quantize(0.0)  # 73 — the pivot and the wide/never-faced value


# ---------------------------------------------------------------------------
# Core: per-delivery arrays -> (buffer bytes, config)
# ---------------------------------------------------------------------------


def compute(league_seq, season_seq, ballsfaced, runs_batter) -> tuple[bytearray, dict]:
    """Build wallheat.u8 + the ch1.json config from parallel per-delivery
    arrays (point order). `league_seq`/`season_seq`/`runs_batter` are int
    sequences; `ballsfaced` is the emitted ballsfaced.u8 (0 == a wide)."""
    n = len(ballsfaced)
    assert len(league_seq) == n and len(season_seq) == n and len(runs_batter) == n

    # Pass 1: cell (league, season, clamped ball-index) run/ball sums.
    cell_runs: dict = defaultdict(int)
    cell_balls: dict = defaultdict(int)
    for i in range(n):
        bf = ballsfaced[i]
        if bf == 0:
            continue  # a wide is not a ball faced — no cell, gets NEUTRAL
        key = (league_seq[i], season_seq[i], clamp_n(bf))
        cell_runs[key] += runs_batter[i]
        cell_balls[key] += 1

    # baselineSR[n] — pooled 2008-10 IPL batter at ball-index n (runs/ball).
    base_runs = [0] * (MAX_BALL_INDEX + 1)
    base_balls = [0] * (MAX_BALL_INDEX + 1)
    for (lg, se, nn), balls in cell_balls.items():
        if lg == BASELINE_LEAGUE and se in BASELINE_SEASONS:
            base_runs[nn] += cell_runs[(lg, se, nn)]
            base_balls[nn] += balls
    baseline_rpb = [
        (base_runs[nn] / base_balls[nn]) if base_balls[nn] else None
        for nn in range(MAX_BALL_INDEX + 1)
    ]

    # Per-cell delta = cell runs/ball - baseline runs/ball at that ball-index.
    # A cell whose ball-index has no 2008-10 baseline (never happens in the
    # corpus — 2008-10 reaches every index 1..30) falls back to neutral.
    cell_delta = {}
    for key in cell_balls:
        b = baseline_rpb[key[2]]
        cell_delta[key] = (cell_runs[key] / cell_balls[key] - b) if b is not None else 0.0

    # Pass 2: emit one byte per delivery in point order.
    out = bytearray(n)
    for i in range(n):
        bf = ballsfaced[i]
        if bf == 0:
            out[i] = NEUTRAL_BYTE
        else:
            out[i] = quantize(cell_delta[(league_seq[i], season_seq[i], clamp_n(bf))])

    config = _config(cell_delta, cell_balls, baseline_rpb)
    return out, config


def _weighted_percentile(items, total, p) -> float:
    """Nearest-rank weighted percentile over sorted (delta, weight) pairs."""
    target = p / 100.0 * (total - 1)
    cum = 0
    for d, w in items:
        if cum + w > target:
            return d
        cum += w
    return items[-1][0]


def _config(cell_delta, cell_balls, baseline_rpb) -> dict:
    """The scenes/ch1.json ignition.wallheat block (traceability + legend)."""
    items = sorted((cell_delta[k], cell_balls[k]) for k in cell_balls)
    total = sum(w for _, w in items)
    p2 = _weighted_percentile(items, total, 2)
    p98 = _weighted_percentile(items, total, 98)

    baseline_sr = [
        round(baseline_rpb[nn] * 100.0, 1) if baseline_rpb[nn] is not None else None
        for nn in range(1, MAX_BALL_INDEX + 1)
    ]

    legend = [
        {
            "key": "cool",
            "label": "Below the 2008-10 batter",
            "byte": quantize(LO),
            "sr_delta": round(LO * 100.0, 1),
        },
        {
            "key": "neutral",
            "label": "Like the 2008-10 batter",
            "byte": NEUTRAL_BYTE,
            "sr_delta": 0.0,
        },
        {
            "key": "hot",
            "label": "Hotter than the 2008-10 batter",
            "byte": quantize(HI),
            "sr_delta": round(HI * 100.0, 1),
        },
    ]

    return {
        "buffer": "wallheat.u8",
        "bytes_per_point": 1,
        "encoding": "diverging",
        "clamp_ball_index": MAX_BALL_INDEX,
        "baseline_league": "ipl",
        "baseline_seasons": list(BASELINE_SEASONS),
        "lo": LO,
        "hi": HI,
        "neutral_byte": NEUTRAL_BYTE,
        "lo_sr_delta": round(LO * 100.0, 1),
        "hi_sr_delta": round(HI * 100.0, 1),
        "baseline_sr": baseline_sr,
        "delta_percentiles": {"p2": round(p2, 3), "p98": round(p98, 3)},
        "legend": legend,
        "legend_labels": [row["label"] for row in legend],
        "definition": (
            "Era-relative intent for the ignition-wall thesis beat. Each ball "
            "is recoloured by how much hotter its (league, season, clamped "
            "ball-index) cell strike rate is than the pooled IPL 2008-2010 "
            "batter at the SAME ball-index (baseline_sr[n], the 2008-10 SR at "
            "ball n). delta = cellSR/100 - baseline_sr[n]/100 (runs per ball "
            "above/below the 2008-10 batter); byte = clamp(round((delta - lo)/"
            "(hi - lo) * 255), 0, 255). The neutral pivot is delta 0 (byte "
            f"{NEUTRAL_BYTE} = the 2008-10 batter); cool = below it, hot = "
            "well above. lo/hi are the rounded ~2nd/98th delta percentiles. "
            "Ball-index is clamped to 30 to match the wall's 30+ column, so "
            "baseline_sr[30] pools every 30th-and-later ball (it is NOT the "
            "exact-ball-30 figure in ignition.sr_by_ball_index). A wide "
            "(ballsfaced 0 — not a ball faced) carries the neutral byte. This "
            "buffer feeds ONLY the thesis-beat blend; the establishing "
            "outcome-colour shot and the six two-tone are unchanged."
        ),
    }


# ---------------------------------------------------------------------------
# Standalone build: own season-blocked pass (scenes.py / tests)
# ---------------------------------------------------------------------------


def build(data_root: Path = canon.DATA_ROOT) -> tuple[bytearray, dict]:
    """One season-blocked corpus pass -> (wallheat bytes, config). Reproduces
    flatten's point order via flatten.sorted_match_files, so this recompute is
    byte-identical to the buffer flatten emits from its own arrays."""
    import json

    import flatten  # local import avoids a flatten<->wallheat import cycle

    league_seq: list = []
    season_seq: list = []
    runs_batter: list = []
    ballsfaced = bytearray()

    for _date, _mid, league, path in flatten.sorted_match_files(data_root):
        with open(path) as fh:
            match = json.load(fh)
        season = canon.canon_season(match["info"])
        lg = WPL if league == "wpl" else IPL
        for innings in match.get("innings", []):
            if canon.is_super_over(innings):
                continue  # standing rule: super overs never enter the stream
            faced: dict = {}
            for over in innings["overs"]:
                for dl in over["deliveries"]:
                    league_seq.append(lg)
                    season_seq.append(season)
                    runs_batter.append(dl["runs"]["batter"])
                    if "wides" in dl.get("extras", {}):
                        ballsfaced.append(0)
                    else:
                        c = faced.get(dl["batter"], 0) + 1
                        faced[dl["batter"]] = c
                        ballsfaced.append(min(c, 255))

    return compute(league_seq, season_seq, ballsfaced, runs_batter)


if __name__ == "__main__":
    _bytes, _cfg = build()
    print(
        f"wallheat.u8: n={len(_bytes)} neutral={NEUTRAL_BYTE} "
        f"lo={LO} hi={HI} p2/98={_cfg['delta_percentiles']}"
    )
