"""Reproducible measurement for the TEST-ISOLATION axis.

Which test modules mutate the working tree's real artifacts?

    python3 tools/measure_test_isolation.py               # every test module
    python3 tools/measure_test_isolation.py --json
    python3 tools/measure_test_isolation.py tests/test_x.py tests/test_y.py

Method: fingerprint the live artifacts, run ONE test module in its own pytest
process, fingerprint again, and report what moved. A module is only blamed for
what changed while it alone was running, so the result does not depend on test
ordering the way a full-suite diff would.

`regradar.db` is fingerprinted by content hash rather than mtime — SQLite touches
the file on read (WAL/shm), and mtime alone would accuse every module that merely
opens a connection.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# The artifacts a test must never write: the working database, the evidence store,
# the run trail and the source registry.
WATCHED_FILES = ("regradar.db", "sources.json", "data/source_runs/source_runs.jsonl")
WATCHED_TREES = ("evidence", "data/source_snapshots")
PER_MODULE_TIMEOUT_S = 600


def _hash_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _hash_tree(path: Path) -> str | None:
    """Fingerprint a directory by its file names and sizes.

    Sizes rather than contents: the evidence store is large and this runs once per
    test module. A test that writes into it changes the name set or a size, both of
    which this catches; a test that rewrites a file to the identical bytes is not a
    contamination worth chasing.
    """
    if not path.exists():
        return None
    digest = hashlib.sha256()
    for item in sorted(path.rglob("*")):
        if item.is_file():
            digest.update(str(item.relative_to(path)).encode("utf-8"))
            digest.update(str(item.stat().st_size).encode("utf-8"))
    return digest.hexdigest()


def _fingerprint() -> dict[str, str | None]:
    state: dict[str, str | None] = {}
    for rel in WATCHED_FILES:
        state[rel] = _hash_file(ROOT / rel)
    for rel in WATCHED_TREES:
        state[rel + "/"] = _hash_tree(ROOT / rel)
    return state


def _test_modules(explicit: list[str]) -> list[Path]:
    if explicit:
        return [Path(p) if Path(p).is_absolute() else ROOT / p for p in explicit]
    return sorted((ROOT / "tests").glob("test_*.py"))


def _run_module(module: Path) -> str:
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", str(module), "-q", "--tb=no", "-p", "no:randomly"],
            cwd=ROOT, capture_output=True, text=True, timeout=PER_MODULE_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired:
        return "timeout"
    return "ok" if proc.returncode == 0 else f"exit{proc.returncode}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("modules", nargs="*", help="specific test files (default: all)")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    modules = _test_modules(args.modules)
    offenders: list[dict] = []
    checked = 0

    for module in modules:
        if not module.exists():
            continue
        before = _fingerprint()
        outcome = _run_module(module)
        after = _fingerprint()
        checked += 1
        touched = sorted(key for key in before if before[key] != after[key])
        if touched:
            offenders.append({
                "module": str(module.relative_to(ROOT)),
                "outcome": outcome,
                "touched": touched,
            })
            if not args.json:
                print(f"MUTATES  {module.name:52} {', '.join(touched)}")
        elif not args.json:
            print(f"clean    {module.name}")

    report = {
        "modules_checked": checked,
        "modules_mutating_live_artifacts": len(offenders),
        "offenders": offenders,
        "watched": list(WATCHED_FILES) + [t + "/" for t in WATCHED_TREES],
    }
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"\nchecked {checked} modules — {len(offenders)} mutate live artifacts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
