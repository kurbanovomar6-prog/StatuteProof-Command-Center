# Workflow 08 — Parser Source Intake Review

Use this workflow for one source URL, one built-in remediation source, or one Source Lab result.

Do not use this workflow to run all sources, broad monitoring, deployment, outreach, or customer delivery.

## Stage 1 — Source Monitor URL/Spec Review

Owner: Source Monitor Agent

Inputs:
- URL
- source_id if existing
- source owner/regulator context
- intended source type

Checks:
- public http(s) URL only
- no credentials in URL
- no localhost/private IP/file URL
- no login, CAPTCHA, paywall, private portal, or access-control bypass
- source_id stability
- expected selector/fetch/PDF mode

Output: BLOCK / TEST_ALLOWED / NEEDS_SPEC_REVIEW.

## Stage 2 — Source Intake Engine Test

Owner: Source Intake Engine, reviewed by Source Monitor

Rules:
- Run only the approved single-source test.
- No-save means preview only.
- Do not write evidence unless explicitly requested.
- Do not send Telegram/email/customer messages.
- Do not use LLMs to decide whether content changed.

Required fields:
- provider_used
- extraction_method
- normalized_length
- normalized_hash
- quality_score
- quality_label
- readiness_status
- evidence_level
- activation_readiness
- nav_shell_detected
- hash_collision
- warnings
- failure_reason
- remediation_hint
- normalized_preview

## Stage 3 — Evidence Trail Verification

Owner: Evidence Trail Agent

Checks:
- no-save result remains PREVIEW_ONLY
- proof paths exist before evidence-backed claims
- raw/normalized/metadata/proof paths are present when saved
- normalized hash exists and is unique
- baseline_runs_completed and baseline_runs_required are clear

Output: PREVIEW_ONLY / EVIDENCE_CONFIRMED / BASELINE_PENDING / EVIDENCE_BLOCKED.

## Stage 4 — QA / Critic Gate

Owner: QA / Critic

Blocks:
- false ready/confirmed status
- nav-shell content marked ready
- hash collision marked ready
- selector timeout marked ready
- shallow/PDF-thin content marked ready
- no-save result shown as evidence confirmed
- one successful test shown as monitoring-ready

Output: PASS / BLOCK with exact blocker.

## Stage 5 — Legal Language Gate

Owner: Legal Language Agent

Checks customer-facing status copy:
- monitoring intelligence only
- not legal advice
- no guaranteed parsing
- no guarantee compliance
- no regulator certification or partnership
- no "any website can be parsed"

Output: SAFE / HOLD with replacement wording.

## Stage 6 — Founder Approval

Founder approval is required before a remediation source becomes customer-visible ready when live verification is incomplete or evidence/baseline history is partial.

Approval packet:
- Source Monitor verdict
- Source Intake JSON
- Evidence Trail verdict
- QA/Critic verdict
- Legal-safe customer wording
- remaining limitations

## Final Verdict Vocabulary

- BLOCKED
- NEEDS_REMEDIATION
- CAN_SAVE_FOR_VALIDATION
- EVIDENCE_CONFIRMED
- BASELINE_PENDING
- MONITORING_READY
