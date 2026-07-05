#!/usr/bin/env python3
"""Generate an operator-only verified monitoring digest from saved alerts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = ROOT / "product" / "regradar"
sys.path.insert(0, str(APP_ROOT))

from app.verified_monitoring_digest import build_verified_monitoring_digest, render_verified_monitoring_digest_markdown


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a StatuteProof monitoring digest.")
    parser.add_argument("--base-dir", type=Path, default=APP_ROOT, help="Regradar base directory.")
    parser.add_argument(
        "--output",
        type=Path,
        default=APP_ROOT / "reports" / "verified_monitoring_digest_latest.md",
        help="Markdown output path.",
    )
    parser.add_argument("--stdout", action="store_true", help="Print markdown to stdout instead of writing a file.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    digest = build_verified_monitoring_digest(base_dir=args.base_dir)
    markdown = render_verified_monitoring_digest_markdown(digest)
    if args.stdout:
        print(markdown)
        return 0

    output = args.output
    if not output.is_absolute():
        output = ROOT / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(markdown, encoding="utf-8")
    print("Verified monitoring digest generated")
    print(f"- output={_rel(output)}")
    print(f"- alerts_total={digest['summary']['alerts_total']}")
    print(f"- pending_review={digest['summary']['pending_review']}")
    print(f"- customer_delivery={digest['customer_delivery']}")
    return 0


def _rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


if __name__ == "__main__":
    raise SystemExit(main())
