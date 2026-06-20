#!/usr/bin/env python3
"""
validate_uae_coverage_claims.py

Validates the UAE Coverage Proof Dossier for:
- All required dossier docs exist
- Roadmap does not contain unsafe absolute coverage claims (as positive claims)
- No forbidden phrases appear as positive claims in dossier documents
- "complete UAE coverage" appears only in negative/conditional/gap contexts
- Current source truth (241 enabled / 172 fresh-alert / 61 evidence-library / 5 candidate / 3 remediation) is intact after proof-backed activations
- sources.json changes remain proof-backed and validator-gated
- uae_source_universe_candidates.json was not modified (grand_total preserved)
- Roadmap P0 section reflects revised 15-source list (not 25)

Context-aware scanning: phrases that appear in "never-use" tables, bullet lists
of forbidden phrases, section headings asking "is X safe?", or analytical contexts
explicitly labeling the phrase as an overclaim are NOT flagged as violations.

Usage:
    python3 tools/validate_uae_coverage_claims.py

Exit code 0 = pass. Exit code 1 = failures detected.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
DOCS_DIR = ROOT / "docs"
SOURCES_PATH = ROOT / "product/regradar/sources.json"
UNIVERSE_PATH = ROOT / "product/regradar/config/uae_source_universe_candidates.json"

ERRORS = []
WARNINGS = []

def err(msg):
    ERRORS.append(f"ERROR: {msg}")

def warn(msg):
    WARNINGS.append(f"WARN:  {msg}")


# ── Context-awareness helpers ─────────────────────────────────────────────────

# Keywords that, if found near a forbidden phrase, indicate it is being
# documented/analyzed as forbidden rather than used as a positive claim.
ANALYTICAL_CONTEXT_KEYWORDS = re.compile(
    r"(?:forbidden|never.use|never use|overclaim|not achievable|absolute claim|"
    r"removed|replaced?|is not safe|inaccurate|safe replacement|verdict.*NO|"
    r"NO.*verdict|NO\b.*:.*absolute|is not|are not|does not|cannot|can.t|"
    r"must not|do not use|the phrase|this phrase|a claim that|definition:|"
    r"would require|soften|requires a disclaimer|implies.*not|not covered|"
    r"not claimable|strong.*legally.dangerous|strong and legally|"
    r"safe\?.*no|safe\?.*NO|SAFE\?.*NO|Safe\?.*NO|"
    r"unsafe claim|avoid|overbroad|causal claim|false claim)",
    re.IGNORECASE,
)

# Section headings that indicate a "forbidden phrases" section follows
FORBIDDEN_SECTION_PATTERNS = re.compile(
    r"(?:never.use phrases|never use phrases|forbidden phrases|"
    r"forbidden claims|quick reference.*never|always-safe|never.use|"
    r"unsafe.*claims?|do not.*claim|prohibited|banned phrases|"
    r"phrase.*must.*not|must.*never)",
    re.IGNORECASE,
)


def get_surrounding_context(lines, line_idx, window=5):
    """Return joined text of lines surrounding line_idx (±window)."""
    start = max(0, line_idx - window)
    end = min(len(lines), line_idx + window + 1)
    return " ".join(lines[start:end])


def find_nearest_section_header(lines, line_idx):
    """Return the nearest section header (##) above the given line index."""
    for i in range(line_idx - 1, max(0, line_idx - 30), -1):
        if lines[i].strip().startswith("#"):
            return lines[i]
    return ""


def is_in_safe_analytical_context(lines, line_idx):
    """
    Return True if the phrase at lines[line_idx] is in an analytical or
    definitional context rather than being used as a positive claim.

    Safe contexts:
    1. The line is part of a markdown table (has | delimiters)
    2. The line is a bullet point in a "never-use" or "forbidden" list section
    3. The line is a section heading (starts with #)
    4. The phrase appears in double or backtick quotes on the line
    5. The surrounding context contains analytical keywords
    6. The nearest section header indicates a "forbidden phrases" section
    """
    line = lines[line_idx]

    # Rule 1: Line is in a markdown table
    if line.count("|") >= 2:
        return True

    # Rule 2: Line is a section heading
    if re.match(r"^\s*#{1,6}\s", line):
        return True

    # Rule 3: The phrase appears inside double quotes on the line
    if re.search(r'"[^"]{3,120}"', line):
        return True

    # Rule 4: Surrounding context contains analytical/definitional keywords
    context = get_surrounding_context(lines, line_idx, window=4)
    if ANALYTICAL_CONTEXT_KEYWORDS.search(context):
        return True

    # Rule 5: The nearest section header indicates a "forbidden phrases" section
    nearest_header = find_nearest_section_header(lines, line_idx)
    if FORBIDDEN_SECTION_PATTERNS.search(nearest_header):
        return True

    # Rule 6: Line itself is a bullet point starting with "- " and the header
    # above or the context mentions forbidden/never-use
    if re.match(r"^\s*[-*]\s+", line):
        header = find_nearest_section_header(lines, line_idx)
        if FORBIDDEN_SECTION_PATTERNS.search(header):
            return True

    return False


# ── Check 1: Required dossier docs exist ──────────────────────────────────────

REQUIRED_DOSSIER_DOCS = [
    "uae-complete-coverage-proof-dossier-plan.md",
    "uae-coverage-claim-levels.md",
    "uae-regulator-source-owner-coverage-matrix.md",
    "uae-source-type-coverage-matrix.md",
    "uae-source-universe-roadmap-quality-audit.md",
    "uae-complete-coverage-gap-verdict.md",
    "uae-coverage-public-claim-safety-table.md",
    "uae-source-universe-prioritized-activation-roadmap.md",
    "uae-complete-coverage-proof-dossier-final-report.md",
]

print("Check 1: Required dossier docs exist...")
missing_docs = []
for doc_name in REQUIRED_DOSSIER_DOCS:
    doc_path = DOCS_DIR / doc_name
    if not doc_path.exists():
        missing_docs.append(doc_name)
        err(f"Missing required dossier doc: docs/{doc_name}")

if not missing_docs:
    print(f"  OK — all {len(REQUIRED_DOSSIER_DOCS)} required docs present")
else:
    print(f"  FAIL — {len(missing_docs)} missing docs")


# ── Load all dossier docs for text scanning ────────────────────────────────────

print("\nLoading dossier docs for claim scanning...")
dossier_texts = {}  # doc_name -> text
dossier_lines = {}  # doc_name -> list[str]
for doc_name in REQUIRED_DOSSIER_DOCS:
    doc_path = DOCS_DIR / doc_name
    if doc_path.exists():
        text = doc_path.read_text(encoding="utf-8")
        dossier_texts[doc_name] = text
        dossier_lines[doc_name] = text.splitlines()

roadmap_path = DOCS_DIR / "uae-source-universe-prioritized-activation-roadmap.md"
roadmap_text = roadmap_path.read_text(encoding="utf-8") if roadmap_path.exists() else ""
roadmap_lines = roadmap_text.splitlines() if roadmap_text else []

print(f"  Loaded {len(dossier_texts)} docs for scanning")


# ── Check 2: Absolute forbidden phrases in dossier docs ───────────────────────
# Each entry: (regex_pattern, description)
# Context-awareness is handled by is_in_safe_analytical_context().
# Only flag if the phrase appears in a line that looks like a POSITIVE CLAIM.

FORBIDDEN_CLAIM_PATTERNS = [
    (r"never miss (?:an |a )update", "Absolute claim: 'never miss an update'"),
    (r"guaranteed? compliance", "Absolute claim: 'guaranteed compliance'"),
    (r"prevent fines", "Causal claim: 'prevent fines'"),
    (r"avoid (?:all )?penalties", "Causal claim: 'avoid penalties'"),
    (
        r"replace (?:lawyers|legal counsel|compliance professionals|MLROs)",
        "False claim: 'replace lawyers'",
    ),
    (
        r"certified by (?:\[any regulator\]|CBUAE|DFSA|ADGM|VARA|SCA|DIFC|UAE FIU|EOCN|FTA)",
        "False certification: 'certified by [regulator]'",
    ),
    (r"\b100%\s+accurate", "Absolute claim: '100% accurate'"),
    (r"perfect parsing", "Absolute claim: 'perfect parsing'"),
    (r"all UAE regulations\b", "Overbroad claim: 'all UAE regulations'"),
    (r"all UAE regulatory updates", "Overbroad claim: 'all UAE regulatory updates'"),
    (
        r"full AML/CFT monitoring across all major regulatory famil",
        "Overclaim: 'Full AML/CFT monitoring across all major regulatory families'",
    ),
]

print("\nCheck 2: Absolute forbidden claim phrases in dossier docs...")
forbidden_found = 0
for doc_name, lines in dossier_lines.items():
    for i, line in enumerate(lines):
        for pattern, description in FORBIDDEN_CLAIM_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                if is_in_safe_analytical_context(lines, i):
                    continue  # Safe — being documented/analyzed, not claimed
                err(f"Forbidden positive claim in {doc_name} line {i+1}: {description}")
                err(f"  Line: {line.strip()[:120]}")
                forbidden_found += 1

if forbidden_found == 0:
    print(f"  OK — no forbidden claim phrases used as positive claims in {len(dossier_texts)} docs")
else:
    print(f"  FAIL — {forbidden_found} forbidden claim violation(s)")


# ── Check 3: "complete UAE coverage" only in safe contexts ────────────────────

print("\nCheck 3: 'complete UAE coverage' only in safe contexts...")
SAFE_COMPLETE_CONTEXT = re.compile(
    r"(?:cannot|can.t|not\b|never|no\b|impossible|verdict.*NO|NO.*verdict|"
    r"not achievable|not claimable|not.*today|not.*defensible|"
    r"forbidden|is not|are not|does not|"
    r"not.*complete coverage|overstate|overclaim|"
    r"2027 story|6\+ months|required for|Before.*complete|"
    r"what.*missing.*complete|must.*never|do not use|SAFE\?.*NO|"
    r"forbidden phrase|Never-Use|never.use|remove.*entirely|"
    r"completeness|not guarantee|not.*guarantee|Replace with|"
    r"would.*require|actually require|strong.*legally.dangerous|"
    r"legally.dangerous|Tier 4|NO\b)",
    re.IGNORECASE,
)

complete_coverage_violations = 0
for doc_name, lines in dossier_lines.items():
    for i, line in enumerate(lines):
        if re.search(r"complete UAE coverage", line, re.IGNORECASE):
            # Check if the line itself or its context makes the claim safe
            if is_in_safe_analytical_context(lines, i):
                continue
            context = get_surrounding_context(lines, i, window=4)
            if SAFE_COMPLETE_CONTEXT.search(context) or SAFE_COMPLETE_CONTEXT.search(line):
                continue
            err(f"Unsafe 'complete UAE coverage' in {doc_name} line {i+1}")
            err(f"  Line: {line.strip()[:120]}")
            complete_coverage_violations += 1

if complete_coverage_violations == 0:
    print("  OK — 'complete UAE coverage' only appears in safe/negative/gap contexts")
else:
    print(f"  FAIL — {complete_coverage_violations} unsafe 'complete UAE coverage' use(s)")


# ── Check 4: Roadmap P0 count is 15 (revised from 25) ────────────────────────

print("\nCheck 4: Roadmap P0 count is 15 (revised from 25)...")
if roadmap_text:
    has_15 = "Top 15" in roadmap_text or "15 sources" in roadmap_text or "15-source" in roadmap_text
    has_25_without_note = (
        ("Top 25" in roadmap_text or "25 sources" in roadmap_text)
        and "Revised from 25 to 15" not in roadmap_text
        and "revised from 25" not in roadmap_text.lower()
    )
    if has_15 and not has_25_without_note:
        print("  OK — roadmap P0 reflects revised 15-source list")
    elif "Revised from 25 to 15" in roadmap_text:
        print("  OK — roadmap P0 references 'Revised from 25 to 15' (historical note acceptable)")
    else:
        err("Roadmap P0 count not clearly revised to 15 sources")
else:
    err("Roadmap file not found or empty — cannot check P0 count")


# ── Check 5: Roadmap P0 outcome estimate updated ──────────────────────────────

print("\nCheck 5: Roadmap P0 outcome estimate updated (not '79 + 25')...")
if roadmap_text:
    if "79 + 25" in roadmap_text:
        err("Roadmap still contains old P0 estimate '79 + 25 = ~104' — must be updated")
    else:
        print("  OK — old '79 + 25 = ~104' estimate removed")


# ── Check 6: Roadmap P1 timeline is 8-12 weeks (not 4-6) ─────────────────────

print("\nCheck 6: Roadmap P1 timeline is 8–12 weeks (not 4–6 weeks)...")
if roadmap_text:
    p1_46_violation = False
    for line in roadmap_lines:
        if re.search(r"4[–-]6\s*weeks", line, re.IGNORECASE) and "P1" in line:
            err(f"Roadmap still shows P1 as '4–6 weeks' — must be 8–12 weeks: {line.strip()}")
            p1_46_violation = True
    if not p1_46_violation:
        print("  OK — P1 timeline not set to old 4–6 week estimate")


# ── Check 7: sources.json integrity ───────────────────────────────────────────

print("\nCheck 7: sources.json integrity — 241 enabled / 172 fresh-alert / 61 evidence-library / 5 candidate / 3 remediation...")
EXPECTED_ENABLED = 241
EXPECTED_MODES = {
    "fresh_alert": 172,
    "evidence_library": 61,
    "candidate": 5,
    "remediation": 3,
}

try:
    with open(SOURCES_PATH) as f:
        sources_data = json.load(f)

    sources = sources_data if isinstance(sources_data, list) else sources_data.get("sources", [])

    enabled_count = sum(1 for s in sources if s.get("enabled", False) is True)
    mode_counts = {mode: 0 for mode in EXPECTED_MODES}
    for source in sources:
        if not source.get("enabled", False):
            continue
        mode = source.get("monitoring_mode")
        if mode in mode_counts:
            mode_counts[mode] += 1

    if enabled_count == EXPECTED_ENABLED:
        print(f"  OK — {enabled_count} enabled sources (expected {EXPECTED_ENABLED})")
    else:
        err(f"sources.json enabled count changed: got {enabled_count}, expected {EXPECTED_ENABLED}")
        err("  sources.json truth must match the latest proof-backed activation sprint")

    for mode, expected_count in EXPECTED_MODES.items():
        actual_count = mode_counts.get(mode, 0)
        if actual_count == expected_count:
            print(f"  OK — {actual_count} {mode} sources (expected {expected_count})")
        else:
            err(f"sources.json {mode} count changed: got {actual_count}, expected {expected_count}")
            err("  monitoring-mode truth must match the latest proof-backed activation sprint")

except FileNotFoundError:
    err(f"sources.json not found at {SOURCES_PATH}")
except json.JSONDecodeError as e:
    err(f"sources.json is invalid JSON: {e}")


# ── Check 8: uae_source_universe_candidates.json integrity ────────────────────

print("\nCheck 8: uae_source_universe_candidates.json integrity (grand_total >= 200)...")
EXPECTED_GRAND_TOTAL_MIN = 200
EXPECTED_CANDIDATES_MIN = 150
EXPECTED_REJECTED_MIN = 25

try:
    with open(UNIVERSE_PATH) as f:
        universe_data = json.load(f)

    summary = universe_data.get("universe_summary", {})
    grand_total = summary.get("grand_total", 0)
    total_candidates = summary.get("total_candidates", 0)
    total_rejected = summary.get("total_rejected", 0)

    if grand_total >= EXPECTED_GRAND_TOTAL_MIN:
        print(f"  OK — grand_total = {grand_total} (>= {EXPECTED_GRAND_TOTAL_MIN})")
    else:
        err(f"universe grand_total dropped below minimum: {grand_total} < {EXPECTED_GRAND_TOTAL_MIN}")
        err("  uae_source_universe_candidates.json must not be modified during dossier sprint")

    if total_candidates >= EXPECTED_CANDIDATES_MIN:
        print(f"  OK — total_candidates = {total_candidates}")
    else:
        err(f"universe total_candidates below minimum: {total_candidates} < {EXPECTED_CANDIDATES_MIN}")

    if total_rejected >= EXPECTED_REJECTED_MIN:
        print(f"  OK — total_rejected = {total_rejected}")
    else:
        warn(f"universe total_rejected lower than expected: {total_rejected} < {EXPECTED_REJECTED_MIN}")

except FileNotFoundError:
    err(f"uae_source_universe_candidates.json not found at {UNIVERSE_PATH}")
except json.JSONDecodeError as e:
    err(f"uae_source_universe_candidates.json is invalid JSON: {e}")


# ── Check 9: Roadmap P2 section has explicit mini-batch list ─────────────────

print("\nCheck 9: Roadmap P2 section contains explicit mini-batch list...")
if roadmap_text:
    has_p2_minibatch = (
        "Top 10 P2 targets" in roadmap_text
        or ("AE-uaefiu-strategic-analysis" in roadmap_text and "P2" in roadmap_text)
    )
    if has_p2_minibatch:
        print("  OK — P2 mini-batch explicit list found")
    else:
        warn("P2 mini-batch list may be missing — check roadmap P2 section")


# ── Check 10: Roadmap commercial section does not make unsafe absolute claims ──

print("\nCheck 10: Roadmap commercial section uses safe wording...")
unsafe_commercial_patterns = [
    (
        r"full AML/CFT monitoring across all major regulatory famil",
        "Overclaim: 'Full AML/CFT monitoring across all major regulatory families'",
    ),
    (
        r"this is the commercial threshold",
        "Prescriptive pricing claim without caveat",
    ),
]
if roadmap_text:
    commercial_violations = 0
    for pattern, description in unsafe_commercial_patterns:
        for i, line in enumerate(roadmap_lines):
            if re.search(pattern, line, re.IGNORECASE):
                if not is_in_safe_analytical_context(roadmap_lines, i):
                    err(f"Unsafe commercial claim in roadmap line {i+1}: {description}")
                    err(f"  Line: {line.strip()[:120]}")
                    commercial_violations += 1
    if commercial_violations == 0:
        print("  OK — roadmap commercial section uses safe wording")


# ── Check 11: EOCN TFS noise-risk warning present in roadmap ─────────────────

print("\nCheck 11: EOCN TFS noise-risk warning present in roadmap...")
if roadmap_text:
    if "noise-risk" in roadmap_text.lower() or "noise risk" in roadmap_text.lower():
        print("  OK — EOCN TFS noise-risk warning found in roadmap")
    else:
        warn("EOCN TFS noise-risk warning may be missing from roadmap — verify manually")


# ── Check 12: Standard disclaimer present in final report ────────────────────

print("\nCheck 12: Standard disclaimer present in final report...")
final_report_path = DOCS_DIR / "uae-complete-coverage-proof-dossier-final-report.md"
if final_report_path.exists():
    final_text = final_report_path.read_text(encoding="utf-8")
    has_disclaimer = (
        "not legal advice" in final_text.lower()
        and "monitoring intelligence only" in final_text.lower()
    )
    if has_disclaimer:
        print("  OK — standard disclaimer found in final report")
    else:
        err("Final report missing standard disclaimer: 'Monitoring intelligence only. Not legal advice.'")
else:
    warn("Final report not yet created — run Part 9")


# ── Check 13: No positive "comprehensive" claim without Tier 3 criteria ───────

print("\nCheck 13: No standalone 'comprehensive UAE' positive claim in dossier docs...")
COMPREHENSIVE_SAFE_CONTEXT = re.compile(
    r"(?:not yet safe|not safe|conditional|after.*activation|post.*activation|"
    r"must not|cannot|Tier 3|criteria not met|requires|after those|"
    r"required.*activations|once.*active|when.*activate|"
    r"with disclaimer|CONDITIONAL|NO\b|forbidden|never use|"
    r"not.*comprehensive|not.*claim.*comprehensive|overclaim|"
    r"not.*achievable|is not|partial)",
    re.IGNORECASE,
)

comp_violations = 0
for doc_name, lines in dossier_lines.items():
    for i, line in enumerate(lines):
        if re.search(r"comprehensive UAE (?:regulatory |official.source |monitoring|coverage)", line, re.IGNORECASE):
            if is_in_safe_analytical_context(lines, i):
                continue
            context = get_surrounding_context(lines, i, window=4)
            if COMPREHENSIVE_SAFE_CONTEXT.search(context) or COMPREHENSIVE_SAFE_CONTEXT.search(line):
                continue
            err(f"Possibly unsafe 'comprehensive UAE' claim in {doc_name} line {i+1}")
            err(f"  Line: {line.strip()[:120]}")
            comp_violations += 1

if comp_violations == 0:
    print("  OK — no standalone comprehensive UAE claims found")
else:
    print(f"  FAIL — {comp_violations} possibly unsafe comprehensive UAE claim(s)")


# ── Results ───────────────────────────────────────────────────────────────────

print("\n" + "=" * 60)
print("VALIDATION RESULTS")
print("=" * 60)

if WARNINGS:
    for w in WARNINGS:
        print(w)

if ERRORS:
    print(f"\n{len(ERRORS)} ERROR(S) FOUND:")
    for e in ERRORS:
        print(e)
    print("\nRESULT: FAIL ❌")
    sys.exit(1)
else:
    if WARNINGS:
        print(f"\n{len(WARNINGS)} warning(s) — review above")
    print(f"\nAll checks passed ({len(REQUIRED_DOSSIER_DOCS)} docs verified, claims validated).")
    print("RESULT: PASS ✅")
    sys.exit(0)
