# Agent Parser System Audit

Date: 2026-06-14

Scope: StatuteProof agent roster, tool router, Codex skills, Claude-style skills, workflows, prompts, and source-intake routing. No parser implementation or live source checks were run for this audit.

## Executive Score

Current agent/skill score: **7.4/10**

The operating system is useful and safer than before: it has exactly 10 active StatuteProof agents, clear Source Monitor / Evidence Trail / QA / Legal boundaries, and repo-scoped Codex skills. The biggest gap is that parser/source-intake has guidance spread across several files rather than one tight workflow and one first-class Codex custom-source-parser skill.

## Useful Agents And Skills

| Area | Useful files | Verdict |
|---|---|---|
| Agent roster | `AGENTS.md`, `.codex/agents/*.toml`, `agents/*.md` | Useful. Exactly 10 active roles; no 11th agent. |
| Task routing | `TOOL_ROUTER.md` | Useful. Routes Source Lab no-save and activation readiness separately. Needs one parser workflow link. |
| Source monitoring | `.agents/skills/source-monitoring-review/SKILL.md` | Useful, but should explicitly separate no-save preview, evidence confirmed, and monitoring-ready. |
| Evidence readiness | `.agents/skills/evidence-readiness-review/SKILL.md`, `.agents/skills/evidence-audit/SKILL.md` | Useful. Needs stronger activation/baseline language. |
| Custom source monitoring | `.agents/skills/custom-source-monitoring-spec/SKILL.md`, `skills/custom-source-parser/SKILL.md` | Useful but split. Missing `.agents/skills/custom-source-parser/SKILL.md`. |
| Legal safety | `.agents/skills/legal-safe-copy-review/SKILL.md`, `docs/forbidden-phrases-reference.md` | Strong enough for customer-facing claim gates. |
| Verification/test discipline | `.agents/skills/verification-before-completion/SKILL.md`, `.agents/skills/test-driven-development/SKILL.md`, `.agents/skills/systematic-debugging/SKILL.md` | Useful for parser changes and regression tests. |
| Prompt injection safety | `.agents/skills/prompt-injection-review/SKILL.md` | Useful for external repo and skill review. |
| Browser/UI QA | `.agents/skills/webapp-testing/SKILL.md` | Useful for Source Lab and dashboard verification. |

## Stale, Weak, Or Conflicting Items

| File/path | Issue | Risk |
|---|---|---|
| `STATUTEPROOF_CONTEXT.md` | Stale context says this Command Center folder does not contain pipeline code, says 9 active sources, and lists DFSA as verified active. Current product code is under `product/regradar`, and source readiness is stricter. | Agents may overclaim source readiness or look in the wrong path. |
| `.agents/skills/source-monitoring-review/SKILL.md` | Good audit skeleton, but does not explicitly require activation readiness, proof/baseline, policy blocked-source checks, or no-save distinction. | Source Monitor could approve a one-off extraction too strongly. |
| `.agents/skills/evidence-readiness-review/SKILL.md` | Checks proof artifacts, but does not explicitly block monitoring-ready without baseline history. | Evidence confirmed and activation readiness may blur. |
| `.agents/skills/custom-source-monitoring-spec/SKILL.md` | Strong source-type boundary, but does not define the precise Source Lab API response fields or UI wording gates. | Source Lab may show optimistic labels. |
| `skills/custom-source-parser/SKILL.md` | Good staged review protocol, but uses `CONFIRMED_ACCESSIBLE -> recommend activate`, which is too strong without proof/baseline. | Could imply one successful test equals activation. |
| `workflows/` | No `08-parser-source-intake-review.md` workflow exists. | Source URL -> Source Intake -> Evidence Trail -> QA -> Legal path is not first-class. |

## Routing Answers

1. Does `AGENTS.md` route parser/source work to Source Monitor, Evidence Trail, Code Architect, QA, Legal? **Mostly yes.** It routes custom parser/intake to Source Monitor + Code Architect + Evidence Trail, with QA and Legal handoff rules.
2. Does `TOOL_ROUTER.md` route custom source parser tasks correctly? **Mostly yes.** It has Source Lab no-save and activation readiness rows. It needs a workflow file reference.
3. Is there a clear Source URL -> Source Monitor -> Source Intake -> Evidence Trail -> QA/Critic -> Legal-safe wording workflow? **Not yet.** It exists conceptually, but not as a workflow document.
4. Are custom-source-parser skills strong enough? **Partially.** `skills/custom-source-parser` exists but `.agents/skills/custom-source-parser` is missing and wording is too activation-friendly.
5. Are Codex skills duplicated, stale, or conflicting? **Some overlap, no blocker.** Source monitoring, evidence readiness, and custom-source monitoring overlap but have distinct scopes.
6. Do any skills overclaim “any website” or “certified”? **No broad “any website” promise found in parser skills.** `skills/custom-source-parser` uses an activation phrase too strongly.
7. Do agents know not to claim legal advice or guaranteed parsing? **Yes in roster/router; stale context should be updated.**
8. Do agents know confirmed/evidence/activation readiness distinctions? **Partly.** Roster/router know it; parser skills need stronger output gates.
9. Do agents know not to activate sources without proof/baseline? **Partly.** Roster/router state it; custom parser skill needs correction.
10. Do agents have useful output formats? **Yes.** Source/evidence/legal skills provide verdict formats, but parser-specific workflow should standardize required fields.

## P0 Fixes

- Add `workflows/08-parser-source-intake-review.md`.
- Add `.agents/skills/custom-source-parser/SKILL.md` or update existing `skills/custom-source-parser/SKILL.md` and route it clearly.
- Update `skills/custom-source-parser/SKILL.md` to say `CONFIRMED_ACCESSIBLE` means readiness threshold met, not activation.
- Update source/evidence skills to separate no-save preview, saved evidence, evidence confirmed, baseline pending, and monitoring-ready.
- Update `STATUTEPROOF_CONTEXT.md` stale path/source/readiness language.

## P1 Fixes

- Add an explicit parser QA gate document and validator.
- Add prompt examples for future parser tasks.
- Add a Source Monitor / Evidence Trail / QA / Legal status-copy checklist.

## P2 Fixes

- Reduce overlap between broad project-review skills over time.
- Add examples of source-lab JSON outputs after DFSA live verification.

## Exact Files To Improve

- `AGENTS.md`
- `TOOL_ROUTER.md`
- `STATUTEPROOF_CONTEXT.md`
- `.agents/skills/source-monitoring-review/SKILL.md`
- `.agents/skills/evidence-readiness-review/SKILL.md`
- `.agents/skills/custom-source-monitoring-spec/SKILL.md`
- `.agents/skills/custom-source-parser/SKILL.md` if created
- `skills/custom-source-parser/SKILL.md`
- `workflows/08-parser-source-intake-review.md`
- `docs/parser-quality-gates.md`
