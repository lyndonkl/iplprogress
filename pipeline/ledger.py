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
