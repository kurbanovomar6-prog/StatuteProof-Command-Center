# Source Onboarding Pipeline Spec

Date: 2026-06-14

## 1. Purpose

Define the exact pipeline for moving an official public source from candidate to active monitoring without inflating source counts or weakening evidence rules.

## 2. Source Lifecycle

1. Candidate discovery.
2. Official/public/access policy check.
3. MLRO/CCO buyer relevance check.
4. Adapter selection.
5. No-save Source Lab test.
6. Quality/nav-shell/hash/noise/source-health scoring.
7. Evidence save.
8. Repeat baseline.
9. Evidence Trail gate.
10. Source Monitor gate.
11. QA / Critic gate.
12. Legal Language gate.
13. Product Manager gate.
14. Activation decision.
15. `sources.json` update only if all gates pass.
16. Customer-facing source count update only after validator passes.

## 3. Required Source States

- `candidate`: official candidate discovered, not tested enough.
- `no_save_passed`: Source Lab no-save check passed; preview-only.
- `proof_saved`: saved evidence exists, but baseline may be incomplete.
- `baseline_pending`: proof exists but repeat baseline is incomplete.
- `activation_ready`: all evidence, baseline, quality, noise, source-health, and agent gates pass.
- `remediation`: useful source, but extraction/quality/source-health is not ready.
- `blocked`: access, policy, or technical blocking prevents monitoring.
- `rejected`: source fails officialness/relevance/no-garbage policy.

## 4. Adapter Selection

Adapter families:

- `custom_element`: rendered custom-tag content, ADGM-style pages.
- `listing`: notices, circulars, regulations, consultations, decisions, publication lists.
- `table`: registers and official tabular lists.
- future: `pdf_document`, `pdf_listing`, `rulebook_module`, `register`, `feed`, `api_json`, `screenshot_evidence`, `archive`.

Adapter config must be recorded in the work queue before a source can be treated as activation-ready.

## 5. No-Save Test Requirements

No-save can only support:

- source parsing preview
- can-save-for-validation decision
- remediation diagnosis

No-save cannot support:

- evidence-confirmed claims
- monitoring-ready claims
- public count changes

Required output fields:

- source ID
- URL
- adapter family/name/version if used
- normalized length
- normalized hash
- quality score/label
- nav-shell flag
- hash-collision flag
- failure reason
- remediation hint
- noise risk
- source-health risk

## 6. Evidence Save Requirements

Saved evidence requires:

- proof path
- normalized text path
- raw/rendered path if available
- normalized hash
- source run record
- provider/adapter report
- certification report

One saved run is evidence, not monitoring-ready.

## 7. Baseline Requirements

Default:

- two successful baseline runs required.

Activation can only proceed when:

- baseline runs completed >= required
- hashes are not shell collisions
- extraction quality is acceptable or better
- proof paths exist
- agent gates pass

## 8. Agent Gates

Source Monitor gate:
- public, official/officially linked, relevant, stable URL, correct adapter/selector.

Evidence Trail gate:
- proof artifacts exist, hashes match, baseline count complete.

QA / Critic gate:
- no nav-shell, shallow text, duplicate shell hash, false ready state, or stale count.

Legal Language gate:
- customer wording avoids legal advice, guarantees, certification, partnership, and inflated source counts.

Code Architect gate:
- adapter approach is scoped, tested, and does not break the evidence pipeline.

Product Manager gate:
- source belongs in a professional UAE MLRO/CCO monitoring pack, not vanity padding.

## 9. Activation Decision

A source can be `activation_ready` only if:

- Source Monitor gate = pass
- Evidence Trail gate = pass
- QA / Critic gate = pass
- Legal Language gate = pass
- Code Architect gate = pass
- Product Manager gate = pass
- proof exists
- baseline complete
- no nav-shell
- no duplicate shell hash
- no unresolved high noise risk
- no unresolved high source-health risk

## 10. Customer-Facing Wording

Allowed now:

- “13 enabled UAE sources / 9 readiness-supported / 4 under extraction remediation.”
- “UAE source expansion and adapter validation are in progress.”
- “Source Lab can test public official or officially linked sources and explain readiness.”

Not allowed:

- “50 working sources.”
- “60 validated sources.”
- “Comprehensive UAE monitor.”
- “Perfect parsing.”
- “Legal advice.”
- “Guaranteed compliance.”
- “Official regulator certified.”

## 11. MVP Implementation

Implemented now:

- adapter result schema
- custom-element/listing/table adapters
- explicit Source Lab adapter path
- adapter metadata in CLI/API output
- adapter metadata in work queue
- adapter validator checks

Still pending:

- SCA-specific listing adapter
- PDF listing adapter
- rulebook/module adapter
- screenshot/WARC evidence enrichment
- 50-source activation validator reaching pass threshold
