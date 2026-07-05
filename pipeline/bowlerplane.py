"""Ch 3 (R2b) — the bowler-season economy x strike-rate plane.

Two jobs, one authoritative corpus pass so the numbers can never drift:

  1. A per-point field buffer **bowlerplane.u8** (2 bytes per delivery, in the
     exact field point order — season-blocked, super overs excluded, identical
     to flatten.py). Byte 0 is the delivery's bowler-season ECONOMY, byte 1 its
     bowling STRIKE RATE, both quantized to the fixed axes below. This lets the
     field condense every ball toward its bowler-season's coordinate on the
     economy x strike-rate plane (Chapter 3's controlling morph): all of a
     bowler-season's balls collapse to one (economy, strike-rate) point, and the
     season clouds/Pareto hull retreat as the reader scrubs the years.

  2. The bowler-season aggregates Chapter 3's scene JSON is built from
     (scenes.build_ch3 imports build() here): the Attack-Containment frontier +
     hull, the ghost trail, True Economy (the gravity-defier payoff), Dot+, and
     the econ~SR correlation. Kept here — not duplicated in scenes.py — so the
     buffer's coordinates and the JSON's frontier are the SAME numbers by
     construction.

Conventions (documented project-wide; the economy/SR conventions match the
metrics-catalog Attack-Containment recipe):

  * ECONOMY = (batter runs + wides + no-balls) per 6 LEGAL balls. Byes and
    leg-byes are excluded (they are not charged to the bowler). "Legal" = not a
    wide and not a no-ball.
  * STRIKE RATE = legal balls per BOWLER-CREDITED wicket (caught, bowled, lbw,
    stumped, caught and bowled, hit wicket — run outs and retirements are NOT
    the bowler's wicket). Undefined for a bowler-season with zero such wickets.
  * A bowler-season qualifies for the frontier at >= MIN_LEGAL_BALLS legal balls
    (the catalog's 90-ball floor: reproduces "49 of 169" and "4 of 267").

Buffer encoding (also documented in scenes/ch3.json for the render agent):

  * byte 0 = economy, linear over [ECON_LO, ECON_HI] RPO -> 0..254 (clamped).
  * byte 1 = strike rate, linear over [SR_LO, SR_HI] balls/wicket -> 0..254
    (clamped); 255 = SENTINEL "no strike rate" (the bowler-season took no
    bowler-credited wicket). Economy is always defined, so byte 0 never uses the
    sentinel in this corpus (it is reserved for the legal==0 impossibility).
  * decode: economy = ECON_LO + b0/254*(ECON_HI-ECON_LO);
            strike_rate = SR_LO + b1/254*(SR_HI-SR_LO)  (b1 < 255).
  * lower economy AND lower strike rate are both BETTER, so the Pareto hull is
    the lower-left staircase; the "containment corner" (economy < 7) sits at the
    left edge.

Wides / no-balls carry their bowler-season's coordinate like any other
delivery (they belong to that bowler-season and count toward its economy). Every
delivery in the corpus has a bowler, so there are no non-bowler deliveries.

Stdlib only. Byte-deterministic (banker's rounding is deterministic; the buffer
is a fixed function of the corpus).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import canon
import flatten

# --- axes (shared by the buffer and scenes/ch3.json's frontier) ---
ECON_LO, ECON_HI = 4.0, 16.0     # RPO
SR_LO, SR_HI = 8.0, 60.0         # legal balls per wicket
SENTINEL = 255                    # byte value = "no coordinate on this axis"

MIN_LEGAL_BALLS = 90              # frontier qualifier (catalog 90-ball floor)
DOTPLUS_MIN_BALLS = 200           # Dot+ leaderboard qualifier

# Bowler-credited dismissal kinds (the wicket goes to the bowler's strike rate).
BOWLER_WICKET_KINDS = frozenset(
    {"caught", "bowled", "lbw", "stumped", "caught and bowled", "hit wicket"}
)

# The single ghost-trail bowler followed across every frontier (catalog: Ashwin).
GHOST_BOWLER = ("ipl", "R Ashwin")

PHASES = ("pp", "middle", "death")


def phase_of(over: int) -> int:
    """0 = powerplay (overs 1-6), 1 = middle (7-15), 2 = death (16-20)."""
    if over <= 5:
        return 0
    if over <= 14:
        return 1
    return 2


class BowlerSeason:
    __slots__ = (
        "league", "season", "bowler",
        "legal", "charged", "wkts", "dots",
        "phase_legal", "over_legal", "team_balls",
    )

    def __init__(self, league, season, bowler):
        self.league = league
        self.season = season
        self.bowler = bowler
        self.legal = 0            # legal balls bowled
        self.charged = 0          # batter runs + wides + no-balls (bowler-charged)
        self.wkts = 0             # bowler-credited wickets
        self.dots = 0             # legal balls with runs.total == 0
        self.phase_legal = [0, 0, 0]   # legal balls per phase (pp/middle/death)
        self.over_legal = [0] * 20     # legal balls per 0-based over (Dot+ baseline)
        self.team_balls = {}      # bowling franchise (canonical) -> legal balls


def build(data_root: Path = canon.DATA_ROOT):
    """One field-ordered corpus pass. Returns the bowler-season aggregates plus
    the side tables the frontier / True Economy / Dot+ / phasepar-reconciliation
    need, and the per-delivery bowler-season key stream (field point order) the
    buffer is encoded from."""
    bs: dict = {}                                   # (league,season,bowler) -> BowlerSeason
    phase_eco: dict = {}                            # (league,season,phase) -> [charged, legal]
    so_dot: dict = {}                               # (league,season,over) -> [dots, legal]
    batter_marginal: dict = {}                      # (league,season,phase) -> [batter_runs, balls_faced]
    ball_keys: list = []                            # (league,season,bowler) per delivery, field order

    def bump(table, key, i, v):
        cell = table.get(key)
        if cell is None:
            cell = table[key] = [0, 0]
        cell[i] += v

    for _date, _mid, league, path in flatten.sorted_match_files(data_root):
        with open(path) as fh:
            match = flatten.json.load(fh)
        info = match["info"]
        season = canon.canon_season(info)
        teams = [canon.canon_team(t) for t in info["teams"]]

        for innings in match.get("innings", []):
            if canon.is_super_over(innings):
                continue  # standing rule: super overs never enter the stream
            bat = canon.canon_team(innings["team"])
            others = [t for t in teams if t != bat]
            bowling_team = others[0] if len(others) == 1 else None
            for over in innings["overs"]:
                ov = over["over"]
                ph = phase_of(ov)
                for dl in over["deliveries"]:
                    ex = dl.get("extras", {})
                    wide = "wides" in ex
                    noball = "noballs" in ex
                    legal = not (wide or noball)
                    rb = dl["runs"]["batter"]
                    charged = rb + ex.get("wides", 0) + ex.get("noballs", 0)
                    bowler = dl["bowler"]
                    key = (league, season, bowler)
                    ball_keys.append(key)

                    rec = bs.get(key)
                    if rec is None:
                        rec = bs[key] = BowlerSeason(league, season, bowler)
                    rec.charged += charged
                    bump(phase_eco, (league, season, ph), 0, charged)

                    if legal:
                        rec.legal += 1
                        rec.phase_legal[ph] += 1
                        if ov < 20:
                            rec.over_legal[ov] += 1
                        if bowling_team is not None:
                            rec.team_balls[bowling_team] = (
                                rec.team_balls.get(bowling_team, 0) + 1
                            )
                        bump(phase_eco, (league, season, ph), 1, 1)
                        bump(so_dot, (league, season, ov), 1, 1)
                        if dl["runs"]["total"] == 0:
                            rec.dots += 1
                            bump(so_dot, (league, season, ov), 0, 1)

                    # phasepar reconciliation: batter runs per ball FACED (wides
                    # excluded, no-balls COUNTED — engine #1's convention).
                    if not wide:
                        bump(batter_marginal, (league, season, PHASES[ph]), 0, rb)
                        bump(batter_marginal, (league, season, PHASES[ph]), 1, 1)

                    for w in dl.get("wickets", []):
                        if w["kind"] in BOWLER_WICKET_KINDS:
                            rec.wkts += 1

    return {
        "bowler_seasons": bs,
        "phase_eco": phase_eco,
        "so_dot": so_dot,
        "batter_marginal": batter_marginal,
        "ball_keys": ball_keys,
    }


# ---------------------------------------------------------------------------
# Derived bowler-season metrics
# ---------------------------------------------------------------------------


def economy(rec: BowlerSeason):
    return 6.0 * rec.charged / rec.legal if rec.legal else None


def strike_rate(rec: BowlerSeason):
    return rec.legal / rec.wkts if rec.wkts else None


def phase_par_econ(phase_eco, league, season, phase_idx):
    cell = phase_eco.get((league, season, phase_idx))
    if not cell or cell[1] == 0:
        return None
    return 6.0 * cell[0] / cell[1]


def par_economy(rec: BowlerSeason, phase_eco):
    """League-season phase-weighted economy for this bowler-season's exact
    legal-ball phase mix (the bowler priced against its own season's phases)."""
    num = 0.0
    den = 0
    for ph in range(3):
        n = rec.phase_legal[ph]
        if n:
            pe = phase_par_econ(phase_eco, rec.league, rec.season, ph)
            if pe is not None:
                num += pe * n
                den += n
    return num / den if den else None


def true_economy(rec: BowlerSeason, phase_eco):
    """par - actual (positive = leaks fewer runs than its era's phase par)."""
    par = par_economy(rec, phase_eco)
    e = economy(rec)
    if par is None or e is None:
        return None
    return par - e


def expected_dots(rec: BowlerSeason, so_dot):
    """Season x over-number baseline dots for this bowler-season's over mix."""
    exp = 0.0
    for ov in range(20):
        n = rec.over_legal[ov]
        if n:
            cell = so_dot.get((rec.league, rec.season, ov))
            if cell and cell[1]:
                exp += n * (cell[0] / cell[1])
    return exp


def dot_plus(rec: BowlerSeason, so_dot):
    exp = expected_dots(rec, so_dot)
    return 100.0 * rec.dots / exp if exp > 0 else None


def franchise(rec: BowlerSeason):
    """Canonical bowling franchise the bowler-season is attributed to (the team
    it bowled the most legal balls for that season)."""
    if not rec.team_balls:
        return None
    return max(rec.team_balls.items(), key=lambda kv: (kv[1], kv[0]))[0]


# ---------------------------------------------------------------------------
# Buffer encoding
# ---------------------------------------------------------------------------


def _q(value, lo, hi):
    """Quantize a value on [lo, hi] to 0..254 (clamped)."""
    if value <= lo:
        return 0
    if value >= hi:
        return 254
    return round((value - lo) / (hi - lo) * 254)


def quantize_econ(e):
    return SENTINEL if e is None else _q(e, ECON_LO, ECON_HI)


def quantize_sr(s):
    return SENTINEL if s is None else _q(s, SR_LO, SR_HI)


def encode(bowler_seasons: dict, ball_keys: list) -> bytes:
    """2 bytes per delivery in field point order: [econ_byte, sr_byte]."""
    coord: dict = {}
    for key, rec in bowler_seasons.items():
        coord[key] = (quantize_econ(economy(rec)), quantize_sr(strike_rate(rec)))
    out = bytearray(len(ball_keys) * 2)
    for i, key in enumerate(ball_keys):
        e, s = coord[key]
        out[2 * i] = e
        out[2 * i + 1] = s
    return bytes(out)


def main(out_root: Path = canon.OUT_ROOT) -> dict:
    data = build()
    buf = encode(data["bowler_seasons"], data["ball_keys"])
    out_root.mkdir(parents=True, exist_ok=True)
    path = out_root / "bowlerplane.u8"
    path.write_bytes(buf)
    n_points = len(data["ball_keys"])
    assert len(buf) == 2 * n_points
    gz = len(flatten.gz_bytes(buf))

    # Register the buffer in meta.json's file manifest (merge, like scenes.py) so
    # the manifest stays complete. Run AFTER flatten + scenes in the canonical
    # order (README) — the files dict is insertion-ordered, so a fixed order
    # keeps meta.json byte-deterministic.
    import json as _json
    meta_path = out_root / "meta.json"
    if meta_path.exists():
        meta = _json.loads(meta_path.read_text())
        meta.setdefault("files", {})["bowlerplane.u8"] = {
            "bytes_raw": len(buf), "bytes_gz": gz,
        }
        meta_path.write_bytes(flatten.compact_json(meta))

    # frontier sanity: reproduce "49 of 169" -> "4 of 267"
    qual_early = [economy(r) for r in data["bowler_seasons"].values()
                  if r.league == "ipl" and 2008 <= r.season <= 2010 and r.legal >= MIN_LEGAL_BALLS]
    qual_recent = [economy(r) for r in data["bowler_seasons"].values()
                   if r.league == "ipl" and 2023 <= r.season <= 2026 and r.legal >= MIN_LEGAL_BALLS]
    print(f"bowlerplane.u8  points={n_points:,}  raw={len(buf):,}  gz={gz:,}")
    print(
        f"  economy under 7: {sum(e < 7.0 for e in qual_early)}/{len(qual_early)} (2008-10)"
        f" -> {sum(e < 7.0 for e in qual_recent)}/{len(qual_recent)} (2023-26)"
    )
    return {"n_points": n_points, "bytes": len(buf), "bytes_gz": gz}


if __name__ == "__main__":
    main()
