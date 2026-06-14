# Agents and Workflows 10/10 Review

## 1. Current Score

Agents/skills/workflows score: 8.8/10

The 10-agent roster is clear, parser/source/evidence/legal routing is documented, and repo-scoped skills exist for the core StatuteProof workflows. The remaining gap is not more agents; it is tighter execution workflows for pre-demo readiness, paid pilot readiness, source baseline saves, and safe GitHub research adoption.

## 2. Active Agent Constraint

Status: PASS

The system remains at exactly 10 active agent roles:

1. Chief of Staff
2. Product Manager
3. Code Architect
4. QA / Critic
5. Legal Language
6. Source Monitor
7. Evidence Trail
8. Risk + Brief Pipeline
9. ICP Lead Research
10. Outreach Writer

No 11th agent was added.

## 3. Useful Skills

Core skills for 10/10 execution:

- `statuteproof-project-review`
- `source-monitoring-review`
- `evidence-readiness-review`
- `custom-source-monitoring-spec`
- `custom-source-parser`
- `legal-safe-copy-review`
- `risk-brief-review`
- `evidence-audit`
- `webapp-testing`
- `verification-before-completion`
- `test-driven-development`
- `systematic-debugging`
- `prompt-injection-review`
- `anti-slop-b2b-copy`
- `mlro-homepage-review`

## 4. Workflow Gaps Closed In This Run

Added workflow docs:

- `workflows/09-pre-demo-readiness-gate.md`
- `workflows/10-first-paid-pilot-readiness.md`
- `workflows/11-source-baseline-and-evidence-save.md`
- `workflows/12-github-research-and-safe-adoption.md`

These are documentation/routing workflows only. They do not create a runtime swarm or new active agents.

## 5. Required Future Invocation Pattern

For any parser/source readiness task:

1. Product Manager defines the customer-facing readiness question.
2. Source Monitor reviews source IDs, URLs, selectors, failure state, and readiness counts.
3. Code Architect reviews implementation risk.
4. Evidence Trail verifies proof artifacts before any evidence claim.
5. QA / Critic blocks overclaiming, stale labels, and route/button bugs.
6. Legal Language reviews all customer-facing copy.
7. Verification Before Completion requires validation and git state checks.

## 6. Remaining Gaps

- Browser smoke test workflow is documented but should become an automated script.
- Source readiness truth still depends on duplicated UI/doc constants until a canonical generated summary exists.
- Paid pilot readiness needs a real operational activation checklist and owner sign-off process.

## 7. Next Exact Task

Turn the pre-demo readiness workflow into a single validation command that checks routes, source readiness copy, sample labels, proof references, and manual activation wording.
