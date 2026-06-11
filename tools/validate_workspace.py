#!/usr/bin/env python3
"""Validate StatuteProof Command Center workspace structure and content."""
import re
import sys
from pathlib import Path

root = Path(__file__).parent.parent
errors = []
warnings = []


def check(condition, message, is_error=True):
    if not condition:
        if is_error:
            errors.append(message)
        else:
            warnings.append(message)


def file_exists(rel_path):
    return (root / rel_path).exists()


def dir_exists(rel_path):
    return (root / rel_path).is_dir()


def read_text(rel_path):
    p = root / rel_path
    if p.exists():
        return p.read_text(errors='ignore')
    return ''


# ── Required directories ──────────────────────────────────────────────────────

REQUIRED_DIRS = [
    '.claude/agents',
    '.claude/skills',
    '.claude/skills/evidence-audit',
    '.claude/skills/risk-brief-review',
    '.claude/skills/weekly-founder-plan',
    'agents',
    'skills/evidence-audit',
    'skills/risk-brief-review',
    'skills/weekly-founder-plan',
    'skills/marketing-outreach-review',
    'skills/anti-slop-writing-review',
    'skills/ui-ux-review',
    'skills/design-polish',
    'skills/design-taste-review',
    'skills/landing-page-conversion-review',
    'skills/agent-council-review',
    'docs',
    'prompts',
    'workflows',
    'examples',
    'checklists',
    'tools',
    'references',
]

for d in REQUIRED_DIRS:
    check(dir_exists(d), f'MISSING DIRECTORY: {d}')

# ── Required root files ───────────────────────────────────────────────────────

REQUIRED_ROOT_FILES = [
    'README.md',
    'START_HERE.md',
    'CLAUDE.md',
    'AGENTS.md',
    'STATUTEPROOF_CONTEXT.md',
    'TOOL_ROUTER.md',
    'THIRD_PARTY_INSPIRATION.md',
    'CHANGELOG.md',
    '.gitignore',
]

for f in REQUIRED_ROOT_FILES:
    check(file_exists(f), f'MISSING ROOT FILE: {f}')

# ── Required agent files ──────────────────────────────────────────────────────

REQUIRED_AGENTS = [
    'agents/source-monitor.md',
    'agents/evidence-trail.md',
    'agents/risk-brief-pipeline.md',
    'agents/legal-language.md',
    'agents/qa-critic.md',
    'agents/product-manager.md',
    'agents/code-architect-dev.md',
    'agents/icp-lead-research.md',
    'agents/outreach-writer.md',
]

for a in REQUIRED_AGENTS:
    check(file_exists(a), f'MISSING AGENT: {a}')

# ── Required skills ───────────────────────────────────────────────────────────

REQUIRED_SKILLS = [
    '.claude/skills/evidence-audit/SKILL.md',
    '.claude/skills/risk-brief-review/SKILL.md',
    '.claude/skills/weekly-founder-plan/SKILL.md',
    'skills/marketing-outreach-review/SKILL.md',
    'skills/anti-slop-writing-review/SKILL.md',
    'skills/ui-ux-review/SKILL.md',
    'skills/design-polish/SKILL.md',
    'skills/design-taste-review/SKILL.md',
    'skills/landing-page-conversion-review/SKILL.md',
    'skills/agent-council-review/SKILL.md',
]

for s in REQUIRED_SKILLS:
    check(file_exists(s), f'MISSING SKILL: {s}')

# ── Required docs ─────────────────────────────────────────────────────────────

REQUIRED_DOCS = [
    'docs/statuteproof-mvp-plan.md',
    'docs/source-monitor-spec-guide.md',
    'docs/evidence-record-spec.md',
    'docs/risk-scoring-guide.md',
    'docs/legal-safety-system.md',
    'docs/forbidden-phrases-reference.md',
    'docs/outreach-strategy.md',
    'docs/landing-page-review.md',
    'docs/github-workflow.md',
    'docs/design-quality-system.md',
    'docs/anti-slop-writing-system.md',
    'docs/agent-council-decision-system.md',
]

for d in REQUIRED_DOCS:
    check(file_exists(d), f'MISSING DOC: {d}')

# ── Required prompts ──────────────────────────────────────────────────────────

REQUIRED_PROMPTS = [
    'prompts/source-spec-prompt.md',
    'prompts/evidence-dry-run-prompt.md',
    'prompts/sample-brief-prompt.md',
    'prompts/legal-safe-copy-review-prompt.md',
    'prompts/outreach-review-prompt.md',
    'prompts/ui-review-prompt.md',
    'prompts/agent-council-prompt.md',
    'prompts/landing-page-conversion-prompt.md',
]

for p in REQUIRED_PROMPTS:
    check(file_exists(p), f'MISSING PROMPT: {p}')

# ── Required workflows ────────────────────────────────────────────────────────

REQUIRED_WORKFLOWS = [
    'workflows/01-weekly-planning.md',
    'workflows/02-first-source-spec.md',
    'workflows/03-evidence-dry-run.md',
    'workflows/04-monitoring-to-brief.md',
    'workflows/05-brief-to-outreach.md',
    'workflows/06-landing-page-review.md',
    'workflows/07-agent-council-review.md',
]

for w in REQUIRED_WORKFLOWS:
    check(file_exists(w), f'MISSING WORKFLOW: {w}')

# ── Required checklists ───────────────────────────────────────────────────────

REQUIRED_CHECKLISTS = [
    'checklists/before-source-spec.md',
    'checklists/before-evidence-brief.md',
    'checklists/before-outreach.md',
    'checklists/before-website-copy.md',
    'checklists/before-github-push.md',
    'checklists/before-agent-council-decision.md',
]

for c in REQUIRED_CHECKLISTS:
    check(file_exists(c), f'MISSING CHECKLIST: {c}')

# ── Max 10 active agents check ───────────────────────────────────────────────

agents_dir = root / '.claude' / 'agents'
if agents_dir.is_dir():
    agent_files = [f for f in agents_dir.iterdir() if f.is_file() and f.suffix == '.md']
    check(len(agent_files) <= 10, f'Too many agents: {len(agent_files)} found in .claude/agents/ — max is 10')

# ── No Ruflo runtime in non-reference files ───────────────────────────────────

RUFLO_RUNTIME_PATTERNS = [
    r'npx ruflo',
    r'npx claude-flow',
    r'ruflo daemon',
    r'ruflo swarm',
    r'mcp__ruflo',
    r'ruv-swarm',
    r'swarm_init\(',
    r'ruflo mcp',
]

for path in root.rglob('*.md'):
    rel = path.relative_to(root)
    parts = rel.parts
    if 'references' in parts:
        continue
    if '.reference_tmp' in str(path):
        continue
    # CLAUDE.md lists what NOT to use — skip runtime check for it
    if rel == Path('CLAUDE.md'):
        continue
    try:
        text = path.read_text(errors='ignore')
    except Exception:
        continue
    for pat in RUFLO_RUNTIME_PATTERNS:
        m = re.search(pat, text)
        if m:
            start = m.start()
            surrounding = text[max(0, start - 150):start + 150].lower()
            is_prohibition = any(w in surrounding for w in ['never', 'do not', "don't", 'inspiration only', 'rejected', 'not relevant'])
            if not is_prohibition:
                errors.append(f'Ruflo runtime reference in non-reference file {rel}: matches "{pat}" — Ruflo is inspiration only')

# ── Secret scan ───────────────────────────────────────────────────────────────

SECRET_PATTERNS = [
    r'sk-ant-[A-Za-z0-9\-_]{20,}',
    r'sk-[A-Za-z0-9]{40,}',
    r'OPENAI_API_KEY\s*=\s*[^\s]+',
    r'ANTHROPIC_API_KEY\s*=\s*[^\s]+',
]

for path in root.rglob('*'):
    if not path.is_file():
        continue
    if any(part.startswith('.reference_') or part == '.reference_tmp' for part in path.parts):
        continue
    if 'node_modules' in path.parts or '__pycache__' in path.parts:
        continue
    if path.suffix in {'.pyc', '.pyo'}:
        continue
    try:
        text = path.read_text(errors='ignore')
    except Exception:
        continue
    for pat in SECRET_PATTERNS:
        if re.search(pat, text):
            errors.append(f'POTENTIAL SECRET in {path.relative_to(root)}: matches {pat}')

# ── node_modules check ────────────────────────────────────────────────────────

check(not dir_exists('node_modules'), 'node_modules/ should not exist in this workspace')

# ── .git inside references check ─────────────────────────────────────────────

for path in root.rglob('.git'):
    if path.is_dir():
        rel = path.relative_to(root)
        parts = rel.parts
        if len(parts) > 1:
            errors.append(f'.git directory found inside references at {rel} — remove it')

# ── Forbidden product claims in CLAUDE.md ─────────────────────────────────────

FORBIDDEN_CLAIM_PHRASES = [
    'guarantee compliance',
    'prevent fines',
    'replace your legal team',
    'never miss an update',
    'official partner of',
    'certified by',
    '100% accurate',
    'AI lawyer',
    'automatic legal advice',
]

claude_md = read_text('CLAUDE.md')
for phrase in FORBIDDEN_CLAIM_PHRASES:
    # Allow the phrase if it appears in a "do not use" context
    idx = claude_md.lower().find(phrase.lower())
    if idx != -1:
        surrounding = claude_md[max(0, idx - 200):idx + len(phrase) + 200].lower()
        is_prohibition = any(
            w in surrounding for w in ['never', 'do not', "don't", 'forbidden', 'prohibited', 'avoid', 'block']
        )
        if not is_prohibition:
            errors.append(f'CLAUDE.md may contain forbidden claim as product claim: "{phrase}"')

# ── SAMPLE / FAKE label check in examples ─────────────────────────────────────

for path in (root / 'examples').rglob('*.md'):
    text = path.read_text(errors='ignore')
    if 'SAMPLE / FAKE' not in text and 'SAMPLE/FAKE' not in text:
        warnings.append(f'examples/{path.name} does not contain SAMPLE / FAKE label')

# ── .env file check ───────────────────────────────────────────────────────────

for path in root.rglob('.env*'):
    if path.is_file() and '.reference_tmp' not in str(path):
        errors.append(f'.env file found: {path.relative_to(root)} — remove before commit')

# ── Print results ─────────────────────────────────────────────────────────────

for e in errors:
    print(f'[ERROR] {e}')
for w in warnings:
    print(f'[WARNING] {w}')

if not errors and not warnings:
    print('Validation PASSED — workspace is clean.')
elif not errors:
    print(f'Validation PASSED with {len(warnings)} warning(s).')
else:
    print(f'Validation FAILED: {len(errors)} error(s), {len(warnings)} warning(s).')
    sys.exit(1)
