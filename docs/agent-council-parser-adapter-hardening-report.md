# Agent Council Parser Adapter Hardening Report

Date: 2026-06-20

## 1. Starting Source Truth

- Starting commit: `ad009dc feat: harden SCA monitoring truth gates`.
- Starting source truth: 238 enabled UAE sources, 169 fresh-alert eligible, 61 evidence-library, 5 candidate, 3 remediation.
- This was not a source-volume sprint.

## 2. Ending Source Truth

- Ending source truth: 238 enabled UAE sources, 169 fresh-alert eligible, 61 evidence-library, 5 candidate, 3 remediation.
- Sources activated: 0.
- MONITOR_OK added: 0.
- Source snapshot proof runs saved: 0.
- Canonical evidence records added: 0.

## 3. Agents Launched

- `multi_agent_v1` Source Monitor spawn was attempted first and failed with `agent thread limit reached`; no old stuck agents were resumed or closed.
- Fresh one-shot CLI Source Monitor returned a usable Phase 1 packet.
- Fresh one-shot CLI Evidence Trail returned a usable Phase 1 packet and a Phase 4 PASS review.
- Fresh one-shot CLI QA / Critic returned a usable Phase 1 packet and a usable Phase 2 critique packet.
- Fresh one-shot CLI Code Architect returned a usable Phase 2 design packet.
- Fresh one-shot CLI QA Phase 4 review timed out without output.
- Usable handoff packets: 5.

## 4. Usable Handoff Packets

- Source Monitor: identified the confirmed SCA-class adapter failure fallback path, nav-shell large-page risks, duplicate-hash no-save risks, and JSON/API shallow validation risks.
- Evidence Trail: confirmed canonical evidence-record gates are strong but record generation remains blocked by missing canonical writer and hash-prefix standardization work.
- QA / Critic: identified a default-open `build_source_lab_contract` save gate, focus-keyword/nav-shell risks, collision-check visibility gaps, and staleness gaps.
- Code Architect: designed a minimal adapter fallback truth gate using `NEEDS_SELECTOR_REVIEW` rather than adding a new status.
- Evidence Trail final review: PASS for chain-of-custody impact of the adapter fallback fix.

## 5. Weaknesses Found

- Structured adapter failure could fall back to generic extraction and still reach `CONFIRMED_ACCESSIBLE`.
- Failed adapter provenance could leave `extraction_strategy` looking like the adapter succeeded.
- `build_source_lab_contract` defaulted missing `can_save_evidence` to open.
- Larger nav-shell pages can still bypass the 10,000-character nav-shell shortcut.
- Collision checks are skipped when `all_sources` is not provided and this is not surfaced as a separate result field.
- Readiness summary still lacks a staleness threshold.
- Canonical `evidence-record.json` generation remains missing.

## 6. Weaknesses Fixed

- Structured declared-adapter fallback now becomes `NEEDS_SELECTOR_REVIEW` unless the adapter family is explicitly fallback-safe.
- Adapter fallback results now expose `adapter_declared_and_failed`, `adapter_fallback_used`, and `adapter_failure_reason`.
- Fallback extraction now records `extraction_strategy=generic_fallback:<method>` instead of preserving a failed adapter strategy.
- `build_source_lab_contract` now defaults missing `can_save_evidence` closed.

## 7. Weaknesses Blocked

- Nav-shell sampling for large pages: blocked for a separate scoped sprint because it needs fixture coverage across large legitimate regulator pages.
- Collision-check visibility: blocked for a separate validator/API contract task.
- Readiness staleness: blocked for a separate source-runs/readiness-summary design task.
- Canonical evidence-record writer: still accepted but not implemented in this sprint.

## 8. Exact Blockers

- Canonical customer evidence remains blocked without a production evidence-record writer that emits append-only, hash-verifiable `evidence-record.json`.
- Risk briefs remain blocked unless `build_risk_brief_inputs` validates a complete canonical evidence record.
- SCA open-data expansion remains blocked until no-save tests produce real structured rows with `adapter_used=true`, proof, baselines, and MONITOR_OK.

## 9. Tests Added

- `test_structured_adapter_failure_cannot_confirm_via_generic_fallback`.
- `test_source_lab_contract_defaults_missing_save_gate_closed`.

## 10. Validators Improved

- No validator files were changed.
- Existing validators were re-run and passed after parser/source-intake hardening.

## 11. Adapter/Source-Intake Behavior Changed

- `source_intake.py` now treats structured adapter failure plus generic fallback as review-only, not confirmed-ready.
- Fallback-safe families are `static_html`, `custom_element`, `playwright_selector`, and `rendered_dom_evidence`.
- Generic fallback is still allowed for sources with no declared adapter.

## 12. Evidence Behavior Changed

- Evidence write remains blocked unless the result is `CONFIRMED_ACCESSIBLE`.
- Provider reports now include adapter fallback provenance fields when evidence is written.
- No source snapshot proof was written in this sprint.

## 13. Sources Activated

- 0.

## 14. Evidence Saved

- 0 source snapshot proof runs.
- 0 canonical evidence records.

## 15. MONITOR_OK Added

- 0.

## 16. Customer Claims Changed

- No customer-facing UI or copy files changed.
- No fresh-alert counts changed.

## 17. Claims Explicitly Not Made

- No complete UAE coverage claim.
- No complete family coverage claim.
- No legal advice claim.
- No guaranteed compliance claim.
- No regulator certification claim.
- No perfect parsing claim.
- No never-miss-updates claim.
- No all-source coverage claim.

## 18. Full Validation Results

- `python3 -m compileall -q product/regradar tools`: pass.
- `python3 -m pytest product/regradar/tests -q`: 338 passed, 5 warnings.
- `python3 tools/validate_fresh_signal_sources.py`: pass, fresh_alert_count=169.
- `python3 tools/validate_source_monitoring_modes.py`: pass, enabled_ae=238, modes fresh_alert=169, evidence_library=61, candidate=5, remediation=3.
- `python3 tools/validate_daily_checkable_sources.py`: pass, daily_checkable_fresh_alert=169.
- `python3 tools/validate_uae_coverage_claims.py`: pass.
- `python3 tools/validate_plan_pricing_consistency.py`: pass.
- `python3 product/regradar/reports/validate_audit.py`: pass.
- `python3 tools/agent_council.py list`: pass.
- `git diff --check`: pass.
- `python3 tools/validate_parser_quality.py`: pass.
- `python3 tools/validate_no_static_sources_as_alerts.py`: pass.
- `python3 tools/validate_no_unvalidated_active_sources.py`: pass.
- `python3 tools/validate_uae_source_pack.py`: pass.
- `python3 tools/validate_fresh_signal_25_per_family.py`: pass.

## 19. Frontend Validation

- Frontend files were not touched; frontend validation was not run.

## 20. Next Exact Parser Task

- Add a large-page nav-shell sampling gate that does not simply skip pages above 10,000 characters. Start with fixtures for a legitimate large regulator listing and a large service/filter shell.

## 21. Next Exact Evidence Task

- Implement the canonical evidence-record writer for completed source runs, including `sha256:`-prefixed hashes, recomputed normalized hash checks, append-only storage, and validator coverage.

## 22. Next Exact Source Task

- Continue SCA open-data row extraction only after identifying a public same-domain row source or stable rendered selector that produces real structured items with `adapter_used=true`.

## 23. Next Exact Product Task

- Add operator-visible wording for adapter fallback states in Source Lab: "Declared adapter failed; generic fallback preview only."

## 24. Next Exact Sales Task

- Keep sales wording limited to selected proof-backed monitoring intelligence. Do not claim complete UAE coverage, complete SCA coverage, perfect parsing, or customer risk-brief readiness.
