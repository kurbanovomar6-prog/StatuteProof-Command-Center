# Parser Agent System Upgrade Report

Date: 2026-06-14

## Agent / Skill Files Updated

- `AGENTS.md`
- `TOOL_ROUTER.md`
- `STATUTEPROOF_CONTEXT.md`
- `.agents/skills/source-monitoring-review/SKILL.md`
- `.agents/skills/evidence-readiness-review/SKILL.md`
- `.agents/skills/custom-source-monitoring-spec/SKILL.md`
- `.agents/skills/custom-source-parser/SKILL.md`
- `skills/custom-source-parser/SKILL.md`
- `workflows/08-parser-source-intake-review.md`
- `docs/parser-quality-gates.md`

## What Changed

- Parser/source-intake work now routes to Source Monitor, Code Architect, Evidence Trail, QA / Critic, and Legal Language without adding an 11th active agent.
- Source Lab language now separates no-save preview, save-for-validation, evidence confirmation, baseline readiness, and monitoring activation.
- Skills now explicitly block private portals, login/CAPTCHA/paywall bypass, broad crawls, and claims that arbitrary websites can be parsed.
- Evidence review now checks evidence level and activation readiness, not only successful fetches.
- Custom source parser review now outputs BLOCK, NEEDS_REMEDIATION, CAN_SAVE_FOR_VALIDATION, BASELINE_PENDING, or MONITORING_READY.
- The current registry truth is documented as 13 enabled UAE sources, 9 readiness-supported, and 4 under extraction remediation.

## How To Use Agents Now

Parser task flow:

1. Chief of Staff coordinates only when the task is multi-step.
2. Product Manager defines customer-facing readiness and activation wording.
3. Code Architect scopes parser/API implementation.
4. Source Monitor owns source/fetch/extraction status.
5. Source Intake Engine runs the exact allowed test.
6. Evidence Trail verifies proof paths, hashes, diffs, and evidence level.
7. QA / Critic blocks false ready states and broken UI/API mappings.
8. Legal Language reviews customer-facing labels and claims.
9. Risk + Brief Pipeline is used only after evidence exists.

## Future Prompt Patterns

Use this for a single source test:

```text
Use source-monitoring-review and custom-source-parser on this one public source.
Run no-save Source Lab only. Return provider_used, extraction_method,
normalized_length, normalized_hash, quality_score, readiness_status,
activation_readiness, evidence_level, warnings, failure_reason, remediation_hint,
and the first 500 characters of normalized_preview. Do not save evidence or
activate monitoring.
```

Use this before moving a source out of remediation:

```text
Use Source Monitor, Evidence Trail, QA / Critic, and Legal Language gates.
Confirm the source has meaningful non-nav-shell content, unique hash,
complete proof artifacts if evidence is claimed, and baseline requirements
before any customer-visible ready label. Founder approval required if live
verification is incomplete.
```

Use this for a Source Lab UI/API change:

```text
Keep no-save, evidence confirmed, and monitoring-ready states separate.
The API must return can_save_for_validation and can_activate_monitoring.
The UI may let users save for validation after a passing preview test, but
must keep monitoring activation disabled until proof and baseline gates pass.
```

## Remaining Agent Gaps

- The agent system is documentation/routing, not a runtime orchestration framework.
- Agent gates still depend on Codex/Claude actually invoking the right skill and reporting the result.
- No automated review agent currently reads rendered browser screenshots for the parser UI.
- DFSA remediation still requires live Playwright verification and Source Monitor/Evidence Trail review before any registry status change.
