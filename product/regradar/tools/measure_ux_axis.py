"""Reproducible measurement for the UX axis.

    python3 tools/measure_ux_axis.py
    python3 tools/measure_ux_axis.py --json

web/testing.md REQUIRES automated accessibility checks and visual regression at
320 / 768 / 1024 / 1440. Until this file existed the axis had no measurement at
all, so its score was whatever the last person felt — which is precisely how a
composite reaches 88 and then collapses.

What it counts, and why each thing is counted the way it is:

* **axe coverage** is counted as SCREENS COVERED / SCREENS THAT EXIST, not as
  "there is an accessibility test file". Four public screens under axe while
  thirty-six authenticated app screens have none is 10% coverage, not a tick.
* **contrast** is reported separately because jsdom cannot compute it. A suite
  that runs axe under jsdom and reports zero violations has NOT checked colour
  contrast, and counting it would be counting a check that never ran.
* **visual regression** requires an actual harness producing artifacts at the
  required widths. A Playwright config that exists but renders nothing is not
  coverage, so the breakpoints are read out of the config/spec files.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web" / "src"
REQUIRED_BREAKPOINTS = (320, 768, 1024, 1440)


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _screens() -> tuple[list[str], list[str]]:
    """(public screens, authenticated app screens).

    SCREENS, not components. Counting every .jsx would put Footer, Hero and each
    panel in the denominator and drive the coverage number to noise — axe runs
    against a rendered screen, and a screen pulls its components in with it.
    Everything under auth/ is a screen; elsewhere the project marks them by
    name, so *Page.jsx is the honest denominator.
    """
    public = sorted(p.name for p in (WEB / "components").glob("*Page.jsx"))
    public += sorted(p.name for p in (WEB / "components" / "auth").glob("*.jsx"))
    app = sorted(p.name for p in (WEB / "components" / "app").glob("*Page.jsx"))
    return public, app


def _axe_covered() -> set[str]:
    """Component names rendered inside a test that asserts no axe violations."""
    covered: set[str] = set()
    test_dir = WEB / "test"
    if not test_dir.exists():
        return covered
    for path in test_dir.glob("*.jsx"):
        text = _read(path)
        if "axe(" not in text:
            continue
        # The imports of a file that calls axe() are the screens it covers.
        for match in re.finditer(r"import\s+(\w+)\s+from\s+'[^']*/([\w.]+)'", text):
            covered.add(match.group(1))
    return covered


def _visual_regression() -> dict:
    """Is there a harness, and which widths does it actually render at?"""
    candidates = list(ROOT.glob("web/**/*playwright*")) + list(
        ROOT.glob("web/**/*.spec.[jt]s")
    ) + list(ROOT.glob("web/**/visual*"))
    candidates = [p for p in candidates if "node_modules" not in str(p)]
    widths: set[int] = set()
    screenshots = False
    for path in candidates:
        if not path.is_file():
            continue
        text = _read(path)
        if "screenshot" in text or "toHaveScreenshot" in text:
            screenshots = True
        for match in re.finditer(r"width\s*:\s*(\d{3,4})", text):
            widths.add(int(match.group(1)))
    return {
        "harness_files": [str(p.relative_to(ROOT)) for p in candidates if p.is_file()],
        "takes_screenshots": screenshots,
        "widths_covered": sorted(widths),
        "required_widths": list(REQUIRED_BREAKPOINTS),
        "missing_widths": [w for w in REQUIRED_BREAKPOINTS if w not in widths],
    }


def _dead_tokens() -> dict:
    """Design tokens defined but never used, and used but never defined."""
    css = _read(WEB / "index.css")
    defined = set(re.findall(r"(--[a-z0-9-]+)\s*:", css))
    used: set[str] = set()
    for path in list(WEB.rglob("*.jsx")) + list(WEB.rglob("*.js")) + [WEB / "index.css"]:
        if "node_modules" in str(path):
            continue
        used |= set(re.findall(r"var\((--[a-z0-9-]+)", _read(path)))
    return {
        "defined": len(defined),
        "used": len(used & defined),
        "defined_never_used": sorted(defined - used),
        "used_never_defined": sorted(used - defined),
        "guard_test_present": (WEB / "test" / "designTokens.test.js").exists(),
    }


def measure() -> dict:
    public, app = _screens()
    covered = _axe_covered()
    public_covered = [s for s in public if Path(s).stem in covered]
    app_covered = [s for s in app if Path(s).stem in covered]
    total = len(public) + len(app)
    total_covered = len(public_covered) + len(app_covered)

    visual = _visual_regression()
    tokens = _dead_tokens()

    a11y_setup = _read(WEB / "test" / "accessibility.test.jsx")
    return {
        "axe": {
            "public_screens": len(public),
            "public_screens_covered": len(public_covered),
            "app_screens": len(app),
            "app_screens_covered": len(app_covered),
            "total_screens": total,
            "total_covered": total_covered,
            "coverage_pct": round(100.0 * total_covered / total, 1) if total else 0.0,
            # jsdom cannot compute colour contrast, so a green axe run here is
            # silent about it. Reported, never counted as covered.
            "contrast_actually_checked": "jsdom" not in a11y_setup.lower()
            and bool(a11y_setup)
            and "browser" in a11y_setup.lower(),
        },
        "visual_regression": visual,
        "design_tokens": tokens,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = measure()

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0

    a = report["axe"]
    print("accessibility (axe)")
    print(f"  public screens covered             {a['public_screens_covered']}/{a['public_screens']}")
    print(f"  authenticated app screens covered  {a['app_screens_covered']}/{a['app_screens']}")
    print(f"  overall screen coverage            {a['coverage_pct']}%")
    print(f"  colour contrast actually checked   {a['contrast_actually_checked']}")
    v = report["visual_regression"]
    print("\nvisual regression")
    print(f"  harness files                      {len(v['harness_files'])}")
    print(f"  takes screenshots                  {v['takes_screenshots']}")
    print(f"  widths covered                     {v['widths_covered']}")
    print(f"  required widths missing            {v['missing_widths']}")
    t = report["design_tokens"]
    print("\ndesign tokens")
    print(f"  defined / used                     {t['defined']} / {t['used']}")
    print(f"  defined but never used             {len(t['defined_never_used'])}")
    print(f"  used but never defined             {len(t['used_never_defined'])}")
    print(f"  drift guard test present           {t['guard_test_present']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
