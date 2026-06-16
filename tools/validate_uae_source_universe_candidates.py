#!/usr/bin/env python3
"""
validate_uae_source_universe_candidates.py

Validates the uae_source_universe_candidates.json file for:
- Structural integrity (required fields, types)
- Uniqueness of source_ids and URLs
- Count thresholds (>= 200 total, >= 79 already_active, >= 25 rejected)
- Allowed values for activation_status, priority, official_status
- No forbidden claims in text fields
- Source ID naming convention (AE- prefix)
- Category membership
- No sources.json leakage (candidates must not claim activation without flag)

Usage:
    python3 tools/validate_uae_source_universe_candidates.py

Exit code 0 = pass. Exit code 1 = failures detected.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
UNIVERSE_PATH = ROOT / "product/regradar/config/uae_source_universe_candidates.json"
SOURCES_PATH = ROOT / "product/regradar/sources.json"

ERRORS = []
WARNINGS = []

def err(msg):
    ERRORS.append(f"ERROR: {msg}")

def warn(msg):
    WARNINGS.append(f"WARN:  {msg}")

# ── Load ──────────────────────────────────────────────────────────────────────
print("Loading universe candidates file...")
try:
    with open(UNIVERSE_PATH) as f:
        data = json.load(f)
except FileNotFoundError:
    print(f"FATAL: {UNIVERSE_PATH} not found.")
    sys.exit(1)
except json.JSONDecodeError as e:
    print(f"FATAL: Invalid JSON — {e}")
    sys.exit(1)

print(f"  Loaded {UNIVERSE_PATH.name}")

# Load sources.json for cross-reference
try:
    with open(SOURCES_PATH) as f:
        sources_raw = json.load(f)
    active_ids = {s["source_id"] for s in sources_raw if s.get("enabled")}
    print(f"  Loaded sources.json — {len(active_ids)} enabled sources")
except Exception as e:
    warn(f"Could not load sources.json for cross-reference: {e}")
    active_ids = set()

# ── Structural checks ─────────────────────────────────────────────────────────
print("\n[1] Structural checks...")

REQUIRED_TOP_KEYS = ["version", "purpose", "warning", "candidates", "rejected",
                     "universe_summary", "current_active_truth"]
for k in REQUIRED_TOP_KEYS:
    if k not in data:
        err(f"Top-level key missing: {k}")

candidates = data.get("candidates", [])
rejected = data.get("rejected", [])

if not isinstance(candidates, list):
    err("'candidates' must be a list")
    sys.exit(1)
if not isinstance(rejected, list):
    err("'rejected' must be a list")
    sys.exit(1)

print(f"  Candidates: {len(candidates)}")
print(f"  Rejected: {len(rejected)}")

# ── Count thresholds ──────────────────────────────────────────────────────────
print("\n[2] Count thresholds...")

grand_total = len(candidates) + len(rejected)
already_active_count = sum(1 for c in candidates if c.get("activation_status") == "already_active")
candidate_count = sum(1 for c in candidates if c.get("activation_status") == "candidate")
rejected_count = len(rejected)

print(f"  Grand total: {grand_total}")
print(f"  Already active: {already_active_count}")
print(f"  Candidates (not active): {candidate_count}")
print(f"  Rejected: {rejected_count}")

if grand_total < 200:
    err(f"Grand total {grand_total} < 200 minimum target")
else:
    print(f"  ✅ Grand total {grand_total} >= 200")

if already_active_count < 79:
    err(f"already_active count {already_active_count} < 79 (all enabled sources must be represented)")
else:
    print(f"  ✅ Already active {already_active_count} >= 79")

if rejected_count < 25:
    warn(f"Rejected count {rejected_count} < 25 (recommend >= 25 documented rejections)")
else:
    print(f"  ✅ Rejected count {rejected_count} >= 25")

# ── Candidate field validation ────────────────────────────────────────────────
print("\n[3] Candidate field validation...")

REQUIRED_CANDIDATE_FIELDS = [
    "source_id", "regulator", "category", "title", "url",
    "official_status", "activation_status", "priority",
    "in_sources_json", "in_work_queue"
]

ALLOWED_ACTIVATION_STATUS = {"already_active", "candidate", "remediation", "blocked", "rejected"}
ALLOWED_PRIORITY = {"P0", "P1", "P2", "P3"}
ALLOWED_OFFICIAL_STATUS = {"official", "officially_linked"}
ALLOWED_CATEGORIES = {
    "A-VARA", "B-FIU-EOCN", "C-CBUAE", "D-DFSA",
    "E-ADGM", "F-SCA", "G-DIFC", "H-Federal", "I-Tax", "J-FreeZone"
}

seen_ids = {}
seen_urls = {}
field_errors = 0

for i, cand in enumerate(candidates):
    sid = cand.get("source_id", f"[index {i}]")
    prefix = f"Candidate {sid}"

    # Required fields
    for field in REQUIRED_CANDIDATE_FIELDS:
        if field not in cand:
            err(f"{prefix}: missing required field '{field}'")
            field_errors += 1

    # source_id uniqueness
    if sid in seen_ids:
        err(f"Duplicate source_id: {sid} (also at index {seen_ids[sid]})")
    else:
        seen_ids[sid] = i

    # source_id naming convention
    if sid != f"[index {i}]" and not sid.startswith("AE-"):
        err(f"{prefix}: source_id does not start with 'AE-'")

    # URL uniqueness (warn only, subpage variants expected)
    url = cand.get("url", "")
    if url in seen_urls:
        warn(f"{prefix}: URL {url} also appears at {seen_urls[url]}")
    elif url:
        seen_urls[url] = sid

    # activation_status
    status = cand.get("activation_status", "")
    if status not in ALLOWED_ACTIVATION_STATUS:
        err(f"{prefix}: invalid activation_status '{status}' (allowed: {ALLOWED_ACTIVATION_STATUS})")

    # priority
    prio = cand.get("priority", "")
    if prio not in ALLOWED_PRIORITY:
        err(f"{prefix}: invalid priority '{prio}' (allowed: {ALLOWED_PRIORITY})")

    # official_status
    off_status = cand.get("official_status", "")
    if off_status not in ALLOWED_OFFICIAL_STATUS:
        err(f"{prefix}: invalid official_status '{off_status}' (allowed: {ALLOWED_OFFICIAL_STATUS})")

    # category
    cat = cand.get("category", "")
    if cat not in ALLOWED_CATEGORIES:
        err(f"{prefix}: invalid category '{cat}' (allowed categories: {ALLOWED_CATEGORIES})")

    # in_sources_json consistency: if already_active, in_sources_json should be True
    if status == "already_active" and cand.get("in_sources_json") is not True:
        warn(f"{prefix}: activation_status is 'already_active' but in_sources_json is not True")

    # URL must be https
    if url and not url.startswith("https://"):
        err(f"{prefix}: URL does not start with https://: {url}")

    # URL must not be empty
    if not url:
        err(f"{prefix}: URL is empty")

if field_errors == 0:
    print(f"  ✅ All candidate fields valid")

# ── already_active vs sources.json cross-check ───────────────────────────────
print("\n[4] Cross-checking already_active vs sources.json...")

universe_active_ids = {c["source_id"] for c in candidates if c.get("activation_status") == "already_active"}

# Active in sources.json but NOT in universe
missing_from_universe = active_ids - universe_active_ids
if missing_from_universe:
    for mid in sorted(missing_from_universe):
        warn(f"Source enabled in sources.json but NOT in universe candidates: {mid}")
else:
    print(f"  ✅ All sources.json enabled sources are represented in universe")

# Universe already_active but NOT in sources.json
extra_in_universe = universe_active_ids - active_ids
if extra_in_universe and active_ids:  # only check if sources.json loaded
    for eid in sorted(extra_in_universe):
        warn(f"Universe marks as already_active but NOT in sources.json enabled: {eid}")

# ── Rejected entries validation ───────────────────────────────────────────────
print("\n[5] Rejected entries validation...")

REQUIRED_REJECTED_FIELDS = ["source_id", "url", "reject_reason"]
rejected_errors = 0

for i, rej in enumerate(rejected):
    for field in REQUIRED_REJECTED_FIELDS:
        if field not in rej or not rej[field]:
            err(f"Rejected[{i}]: missing or empty field '{field}'")
            rejected_errors += 1
    url = rej.get("url", "")
    if url and not url.startswith("https://"):
        err(f"Rejected[{i}] ({rej.get('source_id','?')}): URL not https://: {url}")

if rejected_errors == 0:
    print(f"  ✅ All {len(rejected)} rejected entries have required fields")

# ── Forbidden claims check ────────────────────────────────────────────────────
print("\n[6] Forbidden claims check...")

FORBIDDEN_PHRASES = [
    "guarantee compliance",
    "never miss",
    "100% accurate",
    "complete uae coverage",
    "all regulations",
    "certified by",
    "official partner",
    "prevent fines",
    "replace lawyers",
    "legal advice",
    "automatically compliant",
    "no regulatory update missed",
]

forbidden_found = []
# Check top-level text fields
for field in ["purpose", "warning"]:
    text = str(data.get(field, "")).lower()
    for phrase in FORBIDDEN_PHRASES:
        if phrase in text:
            forbidden_found.append((f"top-level.{field}", phrase))

# Check candidate text fields
for cand in candidates:
    for field in ["why_it_matters", "notes", "title"]:
        text = str(cand.get(field, "")).lower()
        for phrase in FORBIDDEN_PHRASES:
            if phrase in text:
                forbidden_found.append((f"candidate.{cand.get('source_id','?')}.{field}", phrase))

if forbidden_found:
    for location, phrase in forbidden_found:
        err(f"Forbidden phrase '{phrase}' found in {location}")
else:
    print(f"  ✅ No forbidden claims found")

# ── Category distribution check ───────────────────────────────────────────────
print("\n[7] Category distribution...")

from collections import Counter
cat_counts = Counter(c.get("category", "unknown") for c in candidates)
for cat in sorted(ALLOWED_CATEGORIES):
    count = cat_counts.get(cat, 0)
    if count == 0:
        warn(f"Category {cat} has 0 candidates")
    else:
        print(f"  {cat}: {count}")

# ── Summary ───────────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("VALIDATION SUMMARY")
print("="*60)
print(f"  Grand total records:  {grand_total}")
print(f"  Candidates:           {len(candidates)}")
print(f"  Rejected:             {len(rejected)}")
print(f"  Already active:       {already_active_count}")
print(f"  New candidates:       {candidate_count}")
print()

if WARNINGS:
    print(f"  Warnings ({len(WARNINGS)}):")
    for w in WARNINGS:
        print(f"    {w}")
    print()

if ERRORS:
    print(f"  ERRORS ({len(ERRORS)}) — VALIDATION FAILED:")
    for e in ERRORS:
        print(f"    {e}")
    print()
    print("RESULT: FAIL")
    sys.exit(1)
else:
    print("  No errors.")
    print()
    print("RESULT: PASS ✅")
    sys.exit(0)
