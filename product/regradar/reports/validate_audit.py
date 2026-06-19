#!/usr/bin/env python3
"""
StatuteProof Source Signal Quality Audit Validator
Validates source_signal_quality_audit.json for schema correctness and business rule compliance.
"""

import json
import sys
import os

AUDIT_FILE = os.path.join(os.path.dirname(__file__), 'source_signal_quality_audit.json')

REQUIRED_TOP_LEVEL_FIELDS = ['audit_date', 'auditor', 'total_enabled', 'summary', 'by_family', 'sources']
REQUIRED_SUMMARY_FIELDS = ['tier_A', 'tier_B', 'tier_C', 'remediation', 'exclude_review', 'commercially_meaningful']
REQUIRED_SOURCE_FIELDS = [
    'source_id', 'url', 'jurisdiction', 'category', 'enabled', 'status',
    'source_legitimacy', 'content_type', 'commercial_signal_tier', 'tier_reason',
    'client_relevance', 'extraction_quality', 'diff_quality', 'evidence_readiness',
    'monitoring_history', 'notes'
]
REQUIRED_HISTORY_FIELDS = [
    'last_successful_run', 'last_failed_run', 'last_changed_event',
    'last_change_meaningful', 'success_count_7d', 'success_count_30d', 'success_count_90d'
]
VALID_TIERS = {'A', 'B', 'C', 'remediation', 'exclude_review'}
VALID_LEGITIMACY = {
    'official_authority', 'official_document_endpoint', 'official_low_signal',
    'supporting_context', 'duplicate_near_duplicate', 'weak_static_marketing',
    'blocked_limited', 'unknown'
}
VALID_CONTENT_TYPES = {
    'rulebook', 'regulation', 'circular', 'guidance', 'consultation',
    'aml_cft', 'sanctions_tfs', 'tax_guide_clarification',
    'licensing_supervision', 'enforcement_penalties', 'gazette_law_amendment',
    'news_announcement', 'static_reference', 'marketing_generic',
    'duplicate', 'unknown'
}
VALID_EXTRACTION_QUALITY = {
    'stable_text', 'stable_pdf', 'partial', 'noisy', 'blocked',
    'remediation_needed', 'unknown'
}
VALID_DIFF_QUALITY = {
    'meaningful_text_diff', 'meaningful_document_diff', 'noisy_layout_diff',
    'hash_only', 'no_reliable_diff', 'unknown'
}

results = []

def check(name, passed, detail=''):
    status = 'PASS' if passed else 'FAIL'
    results.append((name, status, detail))
    print(f"  [{status}] {name}" + (f": {detail}" if detail else ''))


def main():
    print(f"\nStatuteProof Source Signal Quality Audit Validator")
    print(f"File: {AUDIT_FILE}")
    print("=" * 70)

    # Load file
    try:
        with open(AUDIT_FILE) as f:
            audit = json.load(f)
        print(f"\n[LOAD] File loaded successfully.\n")
    except FileNotFoundError:
        print(f"[FAIL] File not found: {AUDIT_FILE}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"[FAIL] JSON parse error: {e}")
        sys.exit(1)

    print("--- Schema Checks ---")

    # Check 1: Required top-level fields
    missing_top = [f for f in REQUIRED_TOP_LEVEL_FIELDS if f not in audit]
    check("Top-level required fields present", len(missing_top) == 0,
          f"Missing: {missing_top}" if missing_top else "")

    # Check 2: Summary fields
    summary = audit.get('summary', {})
    missing_summary = [f for f in REQUIRED_SUMMARY_FIELDS if f not in summary]
    check("Summary required fields present", len(missing_summary) == 0,
          f"Missing: {missing_summary}" if missing_summary else "")

    # Check 3: Sources is a list
    sources = audit.get('sources', [])
    check("sources is a non-empty list", isinstance(sources, list) and len(sources) > 0,
          f"Got {type(sources).__name__} with {len(sources) if isinstance(sources, list) else 'N/A'} items")

    # Check 4: Every source has required fields
    sources_missing_fields = []
    for s in sources:
        missing = [f for f in REQUIRED_SOURCE_FIELDS if f not in s]
        if missing:
            sources_missing_fields.append((s.get('source_id', 'unknown'), missing))
    check("All sources have required fields", len(sources_missing_fields) == 0,
          f"{len(sources_missing_fields)} sources missing fields" if sources_missing_fields else "")

    # Check 5: Every source has required history fields
    sources_missing_history = []
    for s in sources:
        hist = s.get('monitoring_history', {})
        missing = [f for f in REQUIRED_HISTORY_FIELDS if f not in hist]
        if missing:
            sources_missing_history.append((s.get('source_id', 'unknown'), missing))
    check("All sources have required monitoring_history fields", len(sources_missing_history) == 0,
          f"{len(sources_missing_history)} sources with incomplete history" if sources_missing_history else "")

    # Check 6: All tiers are valid values
    invalid_tiers = [(s.get('source_id','?'), s.get('commercial_signal_tier'))
                     for s in sources if s.get('commercial_signal_tier') not in VALID_TIERS]
    check("All sources have valid commercial_signal_tier", len(invalid_tiers) == 0,
          f"Invalid: {invalid_tiers[:5]}" if invalid_tiers else "")

    # Check 7: All legitimacy values are valid
    invalid_legit = [(s.get('source_id','?'), s.get('source_legitimacy'))
                     for s in sources if s.get('source_legitimacy') not in VALID_LEGITIMACY]
    check("All sources have valid source_legitimacy", len(invalid_legit) == 0,
          f"Invalid: {invalid_legit[:5]}" if invalid_legit else "")

    # Check 8: All enabled=True (since we only audit enabled sources)
    not_enabled = [s.get('source_id','?') for s in sources if not s.get('enabled', True)]
    check("All classified sources are enabled=True", len(not_enabled) == 0,
          f"{len(not_enabled)} disabled sources found" if not_enabled else "")

    print("\n--- Business Rule Checks ---")

    # Check 9: No Tier A source with source_legitimacy weak_static_marketing or duplicate_near_duplicate
    tier_a_weak = [s.get('source_id','?') for s in sources
                   if s.get('commercial_signal_tier') == 'A'
                   and s.get('source_legitimacy') in ('weak_static_marketing', 'duplicate_near_duplicate')]
    check("No Tier A source has weak_static_marketing or duplicate legitimacy", len(tier_a_weak) == 0,
          f"Violations: {tier_a_weak}" if tier_a_weak else "")

    # Check 10: Blocked/remediation sources not counted as Tier A
    remediation_as_a = [s.get('source_id','?') for s in sources
                        if s.get('commercial_signal_tier') == 'A'
                        and (s.get('status') in ('remediation', 'limited', 'disabled_external_access')
                             or s.get('extraction_quality') in ('blocked', 'remediation_needed'))]
    check("No blocked/remediation source is classified Tier A", len(remediation_as_a) == 0,
          f"Violations: {remediation_as_a}" if remediation_as_a else "")

    # Check 11: enabled=False sources cannot be Tier A
    disabled_tier_a = [s.get('source_id','?') for s in sources
                       if s.get('commercial_signal_tier') == 'A' and not s.get('enabled', True)]
    check("No disabled source has tier A", len(disabled_tier_a) == 0,
          f"Violations: {disabled_tier_a}" if disabled_tier_a else "")

    # Check 12: Sources with status replaced cannot be Tier A
    replaced_tier_a = [s.get('source_id','?') for s in sources
                       if s.get('commercial_signal_tier') == 'A' and s.get('status') == 'replaced']
    check("No source with status=replaced has tier A", len(replaced_tier_a) == 0,
          f"Violations: {replaced_tier_a}" if replaced_tier_a else "")

    # Check 13: Tier counts add up to total_enabled
    tier_a = summary.get('tier_A', 0)
    tier_b = summary.get('tier_B', 0)
    tier_c = summary.get('tier_C', 0)
    rem = summary.get('remediation', 0)
    excl = summary.get('exclude_review', 0)
    total_claimed = audit.get('total_enabled', 0)
    tier_sum = tier_a + tier_b + tier_c + rem + excl
    check("Tier counts sum to total_enabled", tier_sum == total_claimed,
          f"Sum={tier_sum} but total_enabled={total_claimed}" if tier_sum != total_claimed else "")

    # Check 14: sources array length matches total_enabled
    check("sources array length matches total_enabled", len(sources) == total_claimed,
          f"sources={len(sources)} but total_enabled={total_claimed}" if len(sources) != total_claimed else "")

    # Check 15: commercially_meaningful = tier_A + tier_B
    cm = summary.get('commercially_meaningful', 0)
    expected_cm = tier_a + tier_b
    check("commercially_meaningful = tier_A + tier_B", cm == expected_cm,
          f"commercially_meaningful={cm} but tier_A+tier_B={expected_cm}" if cm != expected_cm else "")

    # Check 16: Actual tier counts from sources match summary
    actual_tier_counts = {}
    for s in sources:
        t = s.get('commercial_signal_tier', 'unknown')
        actual_tier_counts[t] = actual_tier_counts.get(t, 0) + 1
    actual_a = actual_tier_counts.get('A', 0)
    actual_b = actual_tier_counts.get('B', 0)
    actual_c = actual_tier_counts.get('C', 0)
    actual_rem = actual_tier_counts.get('remediation', 0)
    actual_excl = actual_tier_counts.get('exclude_review', 0)
    tier_match = (actual_a == tier_a and actual_b == tier_b and actual_c == tier_c
                  and actual_rem == rem and actual_excl == excl)
    check("Actual tier counts from sources match summary",
          tier_match,
          f"Summary: A={tier_a} B={tier_b} C={tier_c} rem={rem} excl={excl} | "
          f"Actual: A={actual_a} B={actual_b} C={actual_c} rem={actual_rem} excl={actual_excl}"
          if not tier_match else "")

    # Check 17: No Tier A source has content_type marketing_generic
    tier_a_marketing = [s.get('source_id','?') for s in sources
                        if s.get('commercial_signal_tier') == 'A'
                        and s.get('content_type') == 'marketing_generic']
    check("No Tier A source has content_type marketing_generic", len(tier_a_marketing) == 0,
          f"Violations: {tier_a_marketing}" if tier_a_marketing else "")

    # Check 18: All sources with diff_quality=no_reliable_diff are not Tier A
    no_diff_tier_a = [s.get('source_id','?') for s in sources
                      if s.get('commercial_signal_tier') == 'A'
                      and s.get('diff_quality') == 'no_reliable_diff']
    check("No Tier A source has diff_quality=no_reliable_diff", len(no_diff_tier_a) == 0,
          f"Violations: {no_diff_tier_a[:5]}" if no_diff_tier_a else "")

    # Check 19: Every source URL is non-empty
    empty_urls = [s.get('source_id','?') for s in sources if not s.get('url','').strip()]
    check("All sources have non-empty URLs", len(empty_urls) == 0,
          f"{len(empty_urls)} sources with empty URLs" if empty_urls else "")

    # Check 20: client_relevance is a list on all sources
    bad_relevance = [s.get('source_id','?') for s in sources
                     if not isinstance(s.get('client_relevance'), list)]
    check("All sources have client_relevance as list", len(bad_relevance) == 0,
          f"{len(bad_relevance)} sources with non-list client_relevance" if bad_relevance else "")

    print("\n--- Results Summary ---")
    passed = sum(1 for _, s, _ in results if s == 'PASS')
    failed = sum(1 for _, s, _ in results if s == 'FAIL')
    total = len(results)
    print(f"  Total checks: {total}")
    print(f"  PASS: {passed}")
    print(f"  FAIL: {failed}")

    if failed == 0:
        print(f"\n  ALL CHECKS PASSED")
    else:
        print(f"\n  {failed} CHECKS FAILED")
        print("\n  Failed checks:")
        for name, status, detail in results:
            if status == 'FAIL':
                print(f"    - {name}: {detail}")

    print("=" * 70 + "\n")
    sys.exit(0 if failed == 0 else 1)


if __name__ == '__main__':
    main()
