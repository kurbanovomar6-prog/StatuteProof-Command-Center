#!/usr/bin/env python3
"""Validate StatuteProof Codex-native repo skills."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = ROOT / ".agents" / "skills"
REQUIRED = [
    "statuteproof-project-review",
    "evidence-readiness-review",
    "source-monitoring-review",
    "legal-safe-copy-review",
    "mlro-homepage-review",
    "custom-source-monitoring-spec",
    "anti-slop-b2b-copy",
    "skill-marketplace-research",
]
FORBIDDEN = [
    "ai lawyer",
    "guarantee compliance",
    "prevent fines",
    "replace lawyers",
    "automatic legal advice",
    "official partner",
    "certified by regulators",
    "100% accurate",
    "never miss an update",
    "always up to date",
]
SAFE_CONTEXT = (
    "forbidden", "block", "blocked", "do not", "do not imply", "reject",
    "not claim", "no ", "avoid", "unsafe", "replacements", "examples",
    "approved framing", "constraints",
)
SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"(?i)(api[_-]?key|token|secret)\s*[:=]\s*['\"][^'\"]{8,}['\"]"),
]
REQUIRED_SECTIONS = [
    "## Purpose",
    "## When to use",
    "## When not to use",
    "## Required inputs",
    "## Step-by-step procedure",
    "## Output format",
    "## Safety rules",
    "## StatuteProof-specific constraints",
    "## Example invocation",
]


def has_frontmatter(text: str) -> bool:
    return text.startswith("---\n") and "\n---\n" in text[4:]


def frontmatter_value(text: str, key: str) -> str | None:
    if not has_frontmatter(text):
        return None
    frontmatter = text.split("\n---\n", 1)[0].splitlines()[1:]
    prefix = key + ":"
    for line in frontmatter:
        if line.startswith(prefix):
            return line[len(prefix):].strip()
    return None


def forbidden_product_claims(text: str) -> list[str]:
    hits: list[str] = []
    for i, line in enumerate(text.splitlines(), start=1):
        lower = line.lower()
        for phrase in FORBIDDEN:
            if phrase in lower and not any(ctx in lower for ctx in SAFE_CONTEXT):
                hits.append(f"line {i}: {phrase}")
    return hits


def main() -> int:
    errors: list[str] = []
    if not SKILLS_DIR.exists():
        errors.append(".agents/skills does not exist")

    for name in REQUIRED:
        path = SKILLS_DIR / name / "SKILL.md"
        if not path.exists():
            errors.append(f"missing skill: {name}/SKILL.md")
            continue
        text = path.read_text(encoding="utf-8")
        if not has_frontmatter(text):
            errors.append(f"{name}: missing YAML frontmatter")
        if not frontmatter_value(text, "name"):
            errors.append(f"{name}: missing frontmatter name")
        if not frontmatter_value(text, "description"):
            errors.append(f"{name}: missing frontmatter description")
        for section in REQUIRED_SECTIONS:
            if section not in text:
                errors.append(f"{name}: missing section {section}")
        for claim in forbidden_product_claims(text):
            errors.append(f"{name}: forbidden product claim: {claim}")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                errors.append(f"{name}: possible secret pattern")

    if SKILLS_DIR.exists():
        for env in SKILLS_DIR.rglob(".env*"):
            errors.append(f"env file under .agents/skills: {env.relative_to(ROOT)}")
        for git_dir in SKILLS_DIR.rglob(".git"):
            errors.append(f"third-party repo dump under .agents/skills: {git_dir.relative_to(ROOT)}")
        for item in SKILLS_DIR.rglob("*"):
            if item.is_file() and item.stat().st_size > 200_000:
                errors.append(f"unexpected large file under .agents/skills: {item.relative_to(ROOT)}")

    for doc in [
        ROOT / "docs" / "codex-skills-marketplace-research.md",
        ROOT / "docs" / "codex-skills-usage-guide.md",
    ]:
        if not doc.exists():
            errors.append(f"missing doc: {doc.relative_to(ROOT)}")

    if errors:
        print("Codex skills validation FAILED")
        for err in errors:
            print(f"- {err}")
        return 1

    print("Codex skills validation PASSED")
    print(f"Validated {len(REQUIRED)} required skills in .agents/skills")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
