---
name: statuteproof-project-review
description: Use for broad StatuteProof project audits covering product code, docs, workflows, evidence trail, website, dashboard, and the next safest task.
---

# StatuteProof Project Review

## Purpose
Provide a strict, evidence-backed review of the full StatuteProof workspace without editing product behavior.

## When to use
Use when asked for an overall audit, readiness verdict, project status, roadmap check, investor/customer readiness check, or full workspace review.

## When not to use
Do not use for narrow code fixes, live monitoring, customer delivery, deployment, or legal advice.

## Required inputs
- Workspace root path.
- Scope of review.
- Any specific files or claims to verify.

## Step-by-step procedure
1. Read root guidance: README.md, START_HERE.md, AGENTS.md, TOOL_ROUTER.md, STATUTEPROOF_CONTEXT.md, CHANGELOG.md, SETUP_REPORT.md.
2. Inspect product/ and product/regradar before trusting docs.
3. Verify source registry count, enabled UAE sources, source runs, snapshots, proof files, diff files, tests, frontend, auth, and deployment config.
4. Separate real runtime code from samples, mock data, generated artifacts, and planned docs.
5. Check legal safety: no legal advice, no regulator affiliation, no certainty claims.
6. Produce a readiness score and exactly one next task.

## Output format
- Executive verdict.
- What is real.
- What is mock/planned.
- Readiness scores.
- Blockers ranked CRITICAL/HIGH/MEDIUM/LOW.
- One immediate next task.

## Safety rules
- Do not run broad live monitoring.
- Do not print secrets or .env contents.
- Do not edit files unless explicitly requested.
- Do not create new active agents.

## StatuteProof-specific constraints
The product is official-source UAE regulatory monitoring with evidence-backed compliance briefs. Treat proof discipline as the primary readiness standard.

## Example invocation
"Use statuteproof-project-review to audit the current workspace and tell me what is real now."
