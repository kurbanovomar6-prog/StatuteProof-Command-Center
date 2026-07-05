# StatuteProof Weak Family Proof Recovery Final Report

Date: 2026-06-21

## 1. Chosen Family

UAE FIU.

## 2. Why Chosen

UAE FIU is directly relevant to MLRO buyers, already has proof-backed selected
sources, and had a high-value typology-report alert without canonical evidence.
That made it the best family for a narrow proof-backed improvement.

## 3. Rejected Families And Why

- DIFC: useful, but the fastest improvement would likely require legal database
  endpoint research and parser work.
- ADGM/FSRA: useful, but unresolved candidate rows need source-specific research.
- SCA: commercially important, but the main blocker is parser review on a large
  AML/CFT diff, not an easy proof/evidence lift.
- DFSA: stronger than FIU already; better next target for canonical evidence
  after FIU.
- MoJ/Gazette: still remediation/access constrained and not suitable for this
  sprint unless a safe official public alternative is found.

## 4. Methods Attempted

1. Ran clean-gate validators and preflight.
2. Attempted to launch four council agents; all failed with thread limit.
3. Audited UAE FIU source rows in `sources.json`.
4. Audited UAE FIU saved source runs in `source_runs.jsonl`.
5. Audited UAE FIU alert queue entries.
6. Audited existing UAE FIU canonical evidence records.
7. Ran canonical evidence dry-run for `AE-uaefiu-typology-reports`.
8. Created one canonical evidence record for `intake-20260619T150224Z`.
9. Linked the matching alert queue file to the new evidence record.
10. Regenerated and validated the verified monitoring digest.
11. Checked the risk brief gate and confirmed the new record remains blocked
    while review is pending.

## 5. Unsafe Methods Rejected

- No broad crawl.
- No access-control bypass.
- No activation of `AE-uaefiu-circulars` from no-save/old evidence.
- No fake `MONITOR_OK`.
- No customer delivery approval.
- No claim of FIU circular monitoring.
- No claim of complete FIU or UAE coverage.

## 6. Source IDs Inspected

- `AE-uae-financial-intelligence-unit-uaefiu`
- `AE-uaefiu-circulars`
- `AE-uaefiu-typology-reports`
- `AE-uaefiu-aml-cft-laws`
- `AE-uaefiu-publications-hub`
- `AE-uaefiu-annual-reports`
- `AE-uaefiu-press-releases`
- `AE-uaefiu-system-guides`

## 7. Source IDs Added

None.

## 8. Source IDs Changed

None. No monitoring mode, status, baseline, or `MONITOR_OK` value was changed.

## 9. Source IDs Held

All UAE FIU source rows remain in their prior monitoring modes.

## 10. Source IDs Downgraded

None.

## 11. Parser / Adapter Changes

None.

Reason: this sprint found a safe evidence-readiness improvement using an
existing eligible source run. Parser or adapter changes were not required.

## 12. Proof Artifacts Created

Yes, locally in the canonical evidence tree.

- Record path: `product/regradar/evidence/uae-fiu/AE-uaefiu-typology-reports/intake-20260619T150224Z/evidence-record.json`
- The evidence tree is runtime/gitignored and must not be staged without an
  explicit evidence backup policy.

## 13. Canonical Evidence Created

Yes.

- `evr_AE-uaefiu-typology-reports_intake-20260619T150224Z`
- Record status: complete
- Integrity status: VERIFIED
- Hash verified: true
- Review status: pending

## 14. Alert Linked

Yes, locally.

- Alert file: `product/regradar/data/alert_queue/20260619T150224-AE-uaefiu-typology-reports-intake-2-d3a0.json`
- Evidence link: `evr_AE-uaefiu-typology-reports_intake-20260619T150224Z`
- Delivery remains blocked.
- This runtime alert queue file must not be staged.

## 15. Internal Brief / Digest Generated

Digest regenerated: yes.

Internal non-customer brief generated: no. The new FIU evidence remains pending
review and is intentionally not brief-input eligible.

## 16. Source Audit Changed

No source count/status audit changed in this sprint.

Reason: no source rows were added, activated, downgraded, or reclassified.

## 17. Family Score Before

UAE FIU: 5.8/10.

## 18. Family Score After

UAE FIU: 6.2/10.

This is a narrow score increase for evidence readiness only. It is not a source
breadth or customer-delivery upgrade.

## 19. Overall Source-Monitoring Score Before

67/100.

## 20. Overall Source-Monitoring Score After

68/100.

Reason: one commercially important family now has a stronger canonical evidence
example, but source breadth, parser confidence, and customer proof are mostly
unchanged.

## 21. Customer-Delivery Trust Before

4.5/10.

## 22. Customer-Delivery Trust After

4.5/10.

No customer delivery gate was approved. No founder-approved FIU brief cycle was
created.

## 23. Apollo Readiness Impact

Apollo is slightly safer for selected-source AML/FIU-adjacent outreach, but only
with caveats.

Safe framing:

> selected UAE FIU publications and typology-report monitoring, with evidence
> gates and disclosed FIU circular limitations.

Unsafe framing:

> UAE FIU circular monitoring.

> Complete UAE FIU coverage.

> Evidence-backed customer delivery is live.

## 24. Safe ICPs After This Sprint

- UAE MLROs evaluating selected-source AML/FIU publication monitoring.
- DNFBP/AML compliance teams that accept explicit FIU circular limitations.
- VARA/VASP teams where FIU typology awareness is a supporting signal, not the
  whole product claim.

## 25. ICPs Still Unsafe

- Buyers needing complete UAE FIU circular/notice monitoring.
- Buyers needing complete UAE regulatory coverage.
- Buyers expecting production delivery or uptime SLA proof.
- MoJ/Gazette-heavy legal update buyers.

## 26. Validators Run

- `python3 tools/run_statuteproof_preflight.py`
- `python3 tools/validate_fresh_signal_sources.py`
- `python3 tools/validate_source_monitoring_modes.py`
- `python3 tools/validate_verified_monitoring_digest.py`
- `python3 product/regradar/reports/validate_audit.py`
- `python3 tools/validate_fresh_signal_25_per_family.py`
- `python3 tools/validate_canonical_evidence_records.py`
- `python3 tools/generate_verified_monitoring_digest.py`

## 27. Tests Added

0.

No code behavior changed. Existing validators covered the generated canonical
evidence and digest.

## 28. Preflight Result

PASS.

Latest observed full preflight:

- Python tests: 399 passed, 5 warnings
- Canonical evidence records: 12 validated
- Verified monitoring digest: PASS, 39 alerts, 2 canonical evidence linked,
  customer_delivery=false
- Frontend build/lint/routes: PASS with one existing TanStack warning

## 29. Exact Next Family To Fix

DIFC, unless founder wants to continue UAE FIU circulars.

Recommended next source task:

Investigate `AE-uaefiu-circulars` with a bounded public-source proof run. Keep it
candidate unless an official public endpoint produces meaningful extraction,
proof artifacts, hash, repeat baseline, and validators pass.

## 30. Exact Next Evidence Task

Founder/operator review of:

- `evr_AE-uaefiu-typology-reports_intake-20260619T150224Z`

Review must decide whether the removed item in the typology-report list is real,
parser noise, template reflow, or an access/state artifact.

## 31. Exact Next Sales Task

Update Apollo copy to say:

> selected UAE official-source monitoring for AML/FIU-adjacent signals, with
> hash-verifiable evidence records and disclosed source limitations.

Do not mention FIU circular monitoring until `AE-uaefiu-circulars` passes proof
and baseline.
