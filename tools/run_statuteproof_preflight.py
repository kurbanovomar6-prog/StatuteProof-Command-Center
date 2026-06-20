#!/usr/bin/env python3
"""Run the StatuteProof local preflight suite without deploying anything."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

COMMANDS: tuple[tuple[str, ...], ...] = (
    ("python3", "-m", "compileall", "-q", "product/regradar", "tools"),
    ("python3", "-m", "pytest", "product/regradar/tests", "-q"),
    ("python3", "tools/validate_fresh_signal_sources.py"),
    ("python3", "tools/validate_source_monitoring_modes.py"),
    ("python3", "tools/validate_daily_checkable_sources.py"),
    ("python3", "tools/validate_uae_coverage_claims.py"),
    ("python3", "tools/validate_plan_pricing_consistency.py"),
    ("python3", "product/regradar/reports/validate_audit.py"),
    ("python3", "tools/validate_parser_quality.py"),
    ("python3", "tools/validate_no_static_sources_as_alerts.py"),
    ("python3", "tools/validate_no_unvalidated_active_sources.py"),
    ("python3", "tools/validate_uae_source_pack.py"),
    ("python3", "tools/validate_fresh_signal_25_per_family.py"),
    ("python3", "tools/agent_council.py", "list"),
    ("git", "diff", "--check"),
)

FRONTEND_COMMANDS: tuple[tuple[str, ...], ...] = (
    ("npm", "run", "build"),
    ("npm", "run", "lint"),
    ("node", "scripts/validate-routes.mjs"),
)


def _run(command: tuple[str, ...], *, cwd: Path = ROOT) -> int:
    print("\n$ " + " ".join(command), flush=True)
    completed = subprocess.run(command, cwd=cwd, check=False)
    return int(completed.returncode)


def main() -> int:
    for command in COMMANDS:
        code = _run(command)
        if code != 0:
            print(f"\npreflight failed: {' '.join(command)}", file=sys.stderr)
            return code

    web_dir = ROOT / "product" / "regradar" / "web"
    if web_dir.exists():
        for command in FRONTEND_COMMANDS:
            code = _run(command, cwd=web_dir)
            if code != 0:
                print(f"\nfrontend preflight failed: {' '.join(command)}", file=sys.stderr)
                return code

    print("\nStatuteProof preflight passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
