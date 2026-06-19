# Agent Council Handoff Rules

Date: 2026-06-19

## Core Rule

Agents may propose tasks to each other, but no source activation, customer claim, or brief can bypass Source Monitor, Evidence Trail, QA / Critic, Legal Language, and Product Manager gates when those gates apply.

## Source Activation

1. Source Monitor confirms official/public status, buyer relevance, source health, noise risk, and fetch/extraction blocker.
2. Code Architect implements or adjusts adapter/config only after Source Monitor defines the blocker.
3. Source Monitor reviews no-save output.
4. Evidence Trail reviews saved proof, normalized text, hashes, baselines, and run status.
5. QA / Critic red-teams false readiness, stale notes, validator gaps, and regression risk.
6. Legal Language reviews any customer-facing source status wording.
7. Product Manager decides if the source family claim or pilot scope changes.

## Adapter Implementation

- Starts only after Source Monitor defines source/fetch blocker.
- Code Architect owns design and file scope.
- Adapter Worker may implement bounded files only when assigned.
- Test Fixture Worker provides local fixtures before or with adapter tests.
- No adapter result can activate a source without Evidence Trail.

## Evidence and Briefs

- Evidence Trail reviews only after proof/evidence exists.
- Risk + Brief Pipeline cannot draft a customer brief without `evidence_record_status=complete`.
- If evidence is missing, the output is `BLOCK`, not a risk score.
- QA / Critic reviews brief eligibility before delivery.
- Legal Language reviews customer-facing summary language.

## Customer Copy

- Product Manager frames value and sellability.
- Legal Language reviews wording.
- QA / Critic checks source-truth consistency.
- Outreach Writer drafts only after ICP + Product + Legal approval.
- No one may say complete UAE coverage, complete family coverage, legal advice, guaranteed compliance, perfect parsing, regulator certification, all-source coverage, or never-miss updates.

## Tooling

- Security/Tooling Auditor reviews external tools first.
- Chief of Staff can accept tooling tasks but cannot override a Security/Tooling Auditor block.
- Full Ruflo mode, daemon, hooks, MCP memory auto-sync, and broad agent imports require explicit founder approval.

## Chief of Staff Authority

Chief of Staff may:

- reorder tasks;
- assign owners;
- request review;
- mark a task blocked when a gate fails.

Chief of Staff may not:

- override Evidence Trail on incomplete evidence;
- override QA on no-ship findings;
- override Legal Language on unsafe claims;
- override Product Manager on sellability.
