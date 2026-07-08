"""Payload ledger (blueprint §2) — every emitted artifact vs the budgets.

Measures raw + gzipped size of every artifact in web/static/data/ and checks
them against the standing budgets:

  * Cold-open critical set (R1a): everything that must arrive before the
    cold-open can play — the R0 spike set (meta.json + groups.json +
    group_ids.u16 + attrs.u8) plus the R1a addendum per-point attributes
    (ballsfaced.u8 + wallheat.u8 for the ignition wall, team.u8 + teams.json
    for the picker ignition) and scenes/coldopen.json (the You-Draw-It truth
    data) — <= 3 MB gz.
  * Per-chapter incremental payloads <= 2 MB gz each (here: Chapter 1 =
    scenes/ch1.json + payoff/ch1.json; the R1b sandbox dataset —
    columnar.json.gz + matches.json + scenes/sandbox.json — held to the same
    bar, and lazy-loaded, never in the cold-open critical set).
  * Full read-through <= 25 MB gz.

Writes web/static/data/ledger.json, prints the table, exits non-zero if any
budget fails (the cold-open critical-set check is the release gate).

Sizes use decimal megabytes (1 MB = 1,000,000 bytes) — the conservative
reading of the blueprint's "3MB".
"""

from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import canon

MB = 1_000_000
BUDGET_SPIKE_GZ = 3 * MB
BUDGET_CHAPTER_GZ = 2 * MB
BUDGET_FULL_READ_GZ = 25 * MB

SPIKE_SET = ("meta.json", "groups.json", "group_ids.u16", "attrs.u8")
COLD_OPEN_SET = SPIKE_SET + (
    "ballsfaced.u8",  # R1a: the Ch 1 ignition-wall per-point attribute
    "wallheat.u8",  # R1a refinement: ignition-wall era-relative-intent recolour
    "team.u8",  # R1a: batting-franchise id per point (picker ignition)
    "teams.json",  # R1a: the 20-franchise id/color table
    "scenes/coldopen.json",  # R1a: You-Draw-It truth series + corpus facts
)
CH1_SET_PREFIXES = ("payoff/",)  # chapter payloads by prefix ...
CH1_SET_FILES = ("scenes/ch1.json",)  # ... plus the chapter scene JSON
# R1b sandbox dataset: the lazy-loaded columnar arrays + the matches table a
# tapped ball resolves through + the sandbox descriptor. Held to the per-
# chapter budget (it is not in the cold-open critical set).
SANDBOX_SET = ("columnar.json.gz", "matches.json", "scenes/sandbox.json")
# R2a Chapter 2 "The Last of the Anchors": the whole chapter — anchor /
# run-out / archetype / gear-shift / new-batter-tax series, worm exemplars,
# WPL two-clocks beat, and the 16 team-payoff "Your last anchor" variants —
# ships in one scene doc (scenes/ch2.json), plus the worm-space per-point
# attribute cumruns.u8 (the y axis; attrs.u8 bit 6 carries the run-out flag at
# zero extra bytes). All lazy-loaded at Ch 2 entry; held to the per-chapter
# budget.
CH2_SET_FILES = ("scenes/ch2.json", "cumruns.u8")
# R2b Chapter 3 "The Counterrevolution": the whole chapter — the Attack-
# Containment frontier + hull + ghost trail, Dot+, Dismissal DNA rivers, the
# Death-Wide Tax, the two dot-grid finals, the middle-overs crack ratio, the WPL
# two-clocks beat, the 20 gravity-defier payoff cards, and the footnote layer —
# ships in one scene doc (scenes/ch3.json), plus the bowler-season economy x
# strike-rate per-point buffer bowlerplane.u8 (the controlling-morph coordinate,
# 2 bytes/point). Lazy-loaded at Ch 3 entry; held to the per-chapter budget.
CH3_SET_FILES = ("scenes/ch3.json", "bowlerplane.u8")
# R3a Chapter 4 "The Rising Tide": the whole chapter — the 200 Club threshold
# exceedance, the win-half-the-time par drift, the record ticker, the powerplay
# premium at equal wicket cost, venue divergence + the 16 home-ground-tide
# payoff variants, the CPI callback, the WPL two-clock beat, and the ridgeline /
# waterline column tables — ships in one scene doc (scenes/ch4.json), plus the
# waterline-morph per-point buffer innings_total.u8 (1 byte/point, each ball's
# quantized innings total). Engine-light: it reuses engine #1 (par/phasepar) and
# adds no engine. Lazy-loaded at Ch 4 entry; held to the per-chapter budget.
CH4_SET_FILES = ("scenes/ch4.json", "innings_total.u8")
# R3b Net Session interlude: the two-dial teaching widget between Ch 4 and Ch 5.
# It ships one self-contained scene doc (scenes/interlude.json) that re-projects
# the gate-validated engine grids (engines/wp_grid.json win + engines/re288.json
# runs) into the widget coordinate, plus the three resolved presets, the WPL
# evidence mask, the validated era anchor, and the footnote numbers. The engine
# tables it reads are counted in the engines check, not here. Lazy-loaded at the
# interlude; held to the per-chapter budget.
INTERLUDE_SET_FILES = ("scenes/interlude.json",)
# R3b-2 Chapter 5 "What a Ball Is Worth": the whole chapter — the defended-band
# contrast, RE-surface drift + third-wicket validation, linear weights + the
# per-season price board, the Wicket Value Index, the finisher cliff, the 2019
# final scrub over + WP worm, league WPA headlines, the 20 franchise payoff
# cards, the WPL beats and the footnote layer — ships in one scene doc
# (scenes/ch5.json), plus two per-point buffers: wpa.u8 (signed-quantized WPA,
# batting-team perspective, 1 byte/point) and restate.u8 (the RE-grid state
# cell over*10+wickets, 1 byte/point, the controlling-morph coordinate). The
# engine grids it reads are counted in the engines check, not here. All
# lazy-loaded at Ch 5 entry; held to the per-chapter budget.
CH5_SET_FILES = ("scenes/ch5.json", "wpa.u8", "restate.u8")
# R4a Chapter 6 "Two Dialects": the whole chapter — the Season Constellation
# Map (per-phase Procrustes-aligned star tables + IPL worm + WPL nearest-
# neighbour dotted threads + the two-truths-at-once pairing), the League
# Maturity Clock, Run DNA (the helix), the Stumping Signature, the Photo-Finish
# rate, the batting ladder + depth, the sister-franchise payoff (16 variants),
# and the footnote layer (Star Gravity / Gini, Competitive Balance, Powerplay
# Fear, Twos Culture) — all ship in one scene doc (scenes/ch6.json). Engine-
# and buffer-free: the controlling morph reuses the existing per-point
# group_ids.u16 (already in the cold-open set), so Ch 6 adds no per-point
# buffer. Lazy-loaded at Ch 6 entry; held to the per-chapter budget.
CH6_SET_FILES = ("scenes/ch6.json",)
# R4b Chapter 7 "The Twelfth Man": the whole chapter — the Impact Player natural
# experiment (IPL vs the rule-free WPL diff-in-diff), the License Index at
# identical match states, the Rule-Change event-study placebo grid, the Playbook
# Decoder, the honest null (batting-order fluidity), the 16 team-playbook payoff
# variants, and the footnote layer — all ship in one scene doc (scenes/ch7.json),
# INCLUDING the impact-sub spark index list (the render's subset-highlight
# membership, ~517 field point indices) inline. Engine- and buffer-free: the
# twin-rivers controlling morph reuses the existing group_ids.u16 + attrs.u8
# (already in the cold-open set), so Ch 7 adds no per-point buffer. Lazy-loaded
# at Ch 7 entry; held to the per-chapter budget.
CH7_SET_FILES = ("scenes/ch7.json",)
# R5a Chapter 8 "The Captain's Brain": the whole belief-audit chapter — the
# match-dots controlling-morph table (1,331 centroids + the match_bounds block-
# start indices the field binary-searches in-shader) + the 988 review-chip subset
# (point indices / team / outcome), the toss crossover, the spell strips + cold-
# return tax, the precomputed momentum shuffle nulls, the required-rate curve, the
# WPL adoption curve, the 16 team-payoff variants, and the footnote layer — all
# ship in one scene doc (scenes/ch8.json). Engine- and buffer-free: the match-dots
# add NO per-point attribute (they binary-search the inline match_bounds data
# texture, holding the field at 14 attributes) and the review chips reuse
# aDismissal/aTeam/aRiverPos (Ch 8 never coexists with Ch 3), so Ch 8 ships no
# per-point buffer (pairing.u16 belongs to Ch 9). Lazy-loaded at Ch 8 entry; held
# to the per-chapter budget.
CH8_SET_FILES = ("scenes/ch8.json",)
# Engine tables under engines/: R2a's engine #1 (par/SR+) + engine #5 (entry
# states) consumed by Chapter 2, plus the parallel-track engine #2 (re288) +
# engine #3 (wp_grid) built during R2/R3a and consumed in R3b. All lazy-loaded
# and held to the per-chapter budget. By prefix so new engine files are counted
# automatically.
ENGINES_PREFIXES = ("engines/",)


def measure(path: Path) -> dict:
    data = path.read_bytes()
    if path.name.endswith(".gz"):
        return {
            "bytes_raw": len(gzip.decompress(data)),
            "bytes_gz": len(data),
        }
    return {
        "bytes_raw": len(data),
        "bytes_gz": len(gzip.compress(data, compresslevel=9, mtime=0)),
    }


def collect(out_root: Path = canon.OUT_ROOT) -> dict:
    artifacts = {}
    for path in sorted(out_root.rglob("*")):
        if path.is_dir() or path.name == "ledger.json":
            continue  # the ledger is a build report, not shipped payload
        artifacts[str(path.relative_to(out_root)).replace("\\", "/")] = measure(path)
    return artifacts


def build_ledger(out_root: Path = canon.OUT_ROOT) -> dict:
    artifacts = collect(out_root)

    def gz_sum(names) -> int:
        return sum(artifacts[n]["bytes_gz"] for n in names if n in artifacts)

    missing_cold_open = [n for n in COLD_OPEN_SET if n not in artifacts]
    chapter_files = sorted(
        [n for n in artifacts if n.startswith(CH1_SET_PREFIXES)]
        + [n for n in CH1_SET_FILES if n in artifacts]
    )
    sandbox_files = [n for n in SANDBOX_SET if n in artifacts]
    ch2_files = [n for n in CH2_SET_FILES if n in artifacts]
    ch3_files = [n for n in CH3_SET_FILES if n in artifacts]
    ch4_files = [n for n in CH4_SET_FILES if n in artifacts]
    interlude_files = [n for n in INTERLUDE_SET_FILES if n in artifacts]
    ch5_files = [n for n in CH5_SET_FILES if n in artifacts]
    ch6_files = [n for n in CH6_SET_FILES if n in artifacts]
    ch7_files = [n for n in CH7_SET_FILES if n in artifacts]
    ch8_files = [n for n in CH8_SET_FILES if n in artifacts]
    engine_files = sorted(n for n in artifacts if n.startswith(ENGINES_PREFIXES))

    checks = [
        {
            "name": "cold_open_critical_set (pre-assembly)",
            "files": list(COLD_OPEN_SET),
            "budget_gz": BUDGET_SPIKE_GZ,
            "actual_gz": gz_sum(COLD_OPEN_SET),
            "pass": not missing_cold_open
            and gz_sum(COLD_OPEN_SET) <= BUDGET_SPIKE_GZ,
        },
        {
            "name": "chapter ch1 (scene + payoff)",
            "files": chapter_files,
            "budget_gz": BUDGET_CHAPTER_GZ,
            "actual_gz": gz_sum(chapter_files),
            "pass": bool(chapter_files) and gz_sum(chapter_files) <= BUDGET_CHAPTER_GZ,
        },
        {
            "name": "sandbox dataset (columnar + matches + descriptor)",
            "files": sandbox_files,
            "budget_gz": BUDGET_CHAPTER_GZ,
            "actual_gz": gz_sum(sandbox_files),
            "pass": bool(sandbox_files) and gz_sum(sandbox_files) <= BUDGET_CHAPTER_GZ,
        },
        {
            "name": "chapter ch2 (scene + payoff)",
            "files": ch2_files,
            "budget_gz": BUDGET_CHAPTER_GZ,
            "actual_gz": gz_sum(ch2_files),
            "pass": bool(ch2_files) and gz_sum(ch2_files) <= BUDGET_CHAPTER_GZ,
        },
        {
            "name": "chapter ch3 (scene + bowlerplane buffer)",
            "files": ch3_files,
            "budget_gz": BUDGET_CHAPTER_GZ,
            "actual_gz": gz_sum(ch3_files),
            "pass": bool(ch3_files) and gz_sum(ch3_files) <= BUDGET_CHAPTER_GZ,
        },
        {
            "name": "chapter ch4 (scene + innings_total buffer)",
            "files": ch4_files,
            "budget_gz": BUDGET_CHAPTER_GZ,
            "actual_gz": gz_sum(ch4_files),
            "pass": bool(ch4_files) and gz_sum(ch4_files) <= BUDGET_CHAPTER_GZ,
        },
        {
            "name": "interlude (Net Session scene doc)",
            "files": interlude_files,
            "budget_gz": BUDGET_CHAPTER_GZ,
            "actual_gz": gz_sum(INTERLUDE_SET_FILES),
            "pass": bool(interlude_files)
            and gz_sum(INTERLUDE_SET_FILES) <= BUDGET_CHAPTER_GZ,
        },
        {
            "name": "chapter ch5 (scene + wpa/restate buffers)",
            "files": ch5_files,
            "budget_gz": BUDGET_CHAPTER_GZ,
            "actual_gz": gz_sum(ch5_files),
            "pass": bool(ch5_files) and gz_sum(ch5_files) <= BUDGET_CHAPTER_GZ,
        },
        {
            "name": "chapter ch6 (Two Dialects scene doc)",
            "files": ch6_files,
            "budget_gz": BUDGET_CHAPTER_GZ,
            "actual_gz": gz_sum(ch6_files),
            "pass": bool(ch6_files) and gz_sum(ch6_files) <= BUDGET_CHAPTER_GZ,
        },
        {
            "name": "chapter ch7 (Twelfth Man scene doc + spark indices)",
            "files": ch7_files,
            "budget_gz": BUDGET_CHAPTER_GZ,
            "actual_gz": gz_sum(ch7_files),
            "pass": bool(ch7_files) and gz_sum(ch7_files) <= BUDGET_CHAPTER_GZ,
        },
        {
            "name": "chapter ch8 (Captain's Brain scene doc + match-dots/review subset)",
            "files": ch8_files,
            "budget_gz": BUDGET_CHAPTER_GZ,
            "actual_gz": gz_sum(ch8_files),
            "pass": bool(ch8_files) and gz_sum(ch8_files) <= BUDGET_CHAPTER_GZ,
        },
        {
            "name": "engines (ch2 par/entry + R3b parallel-track re288/wp_grid)",
            "files": engine_files,
            "budget_gz": BUDGET_CHAPTER_GZ,
            "actual_gz": gz_sum(engine_files),
            "pass": bool(engine_files) and gz_sum(engine_files) <= BUDGET_CHAPTER_GZ,
        },
        {
            "name": "full read-through (all artifacts)",
            "files": sorted(artifacts),
            "budget_gz": BUDGET_FULL_READ_GZ,
            "actual_gz": gz_sum(artifacts),
            "pass": gz_sum(artifacts) <= BUDGET_FULL_READ_GZ,
        },
    ]
    if missing_cold_open:
        checks[0]["missing"] = missing_cold_open

    return {
        "budgets": {
            "cold_open_set_gz": BUDGET_SPIKE_GZ,
            "per_chapter_gz": BUDGET_CHAPTER_GZ,
            "full_read_gz": BUDGET_FULL_READ_GZ,
            "mb_definition": "1 MB = 1,000,000 bytes",
        },
        "artifacts": artifacts,
        "checks": checks,
        "pass": all(c["pass"] for c in checks),
    }


def print_table(ledger: dict) -> None:
    print(f"{'artifact':<24} {'raw bytes':>12} {'gz bytes':>12}")
    print("-" * 50)
    for name, sizes in ledger["artifacts"].items():
        print(f"{name:<24} {sizes['bytes_raw']:>12,} {sizes['bytes_gz']:>12,}")
    print()
    print(f"{'budget check':<40} {'gz actual':>12} {'gz budget':>12}  verdict")
    print("-" * 76)
    for c in ledger["checks"]:
        verdict = "PASS" if c["pass"] else "FAIL"
        print(f"{c['name']:<40} {c['actual_gz']:>12,} {c['budget_gz']:>12,}  {verdict}")
        if c.get("missing"):
            print(f"  !! missing artifacts: {', '.join(c['missing'])}")


def main() -> int:
    ledger = build_ledger()
    out = canon.OUT_ROOT / "ledger.json"
    out.write_bytes(
        json.dumps(ledger, indent=1, separators=(",", ": ")).encode("utf-8")
    )
    print_table(ledger)
    print(f"\nledger -> {out.relative_to(canon.REPO_ROOT)}")
    if not ledger["pass"]:
        print("PAYLOAD LEDGER FAILED — budget exceeded or artifact missing", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
