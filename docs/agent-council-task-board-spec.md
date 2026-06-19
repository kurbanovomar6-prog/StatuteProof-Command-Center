# Agent Council Task Board Spec

Date: 2026-06-19

## Storage

Machine-readable task board:

`product/regradar/config/agent_council_tasks.json`

The task board is a local JSON file. It does not use network services, daemon workers, or hidden background automation.

## Task Fields

Each task is an object with:

- `task_id`: stable kebab-case identifier.
- `title`: short human-readable task title.
- `status`: one of the allowed statuses.
- `owner_agent`: single accountable owner role.
- `reviewer_agents`: list of roles that must review before done.
- `source_family`: source family or `cross_project`.
- `files_allowed_to_touch`: explicit write scope.
- `files_forbidden_to_touch`: files or paths that must not be modified.
- `objective`: concrete outcome.
- `acceptance_criteria`: list of pass conditions.
- `evidence_required`: list of artifacts or proof required.
- `validation_commands`: commands required before completion.
- `blocker`: current blocker or empty string.
- `next_handoff_agent`: next role to receive the task.
- `notes`: append-only operational notes.
- `created_at`: ISO-8601 timestamp.
- `updated_at`: ISO-8601 timestamp.

## Allowed Statuses

- `proposed`
- `accepted`
- `in_progress`
- `blocked`
- `review_source_monitor`
- `review_evidence`
- `review_qa`
- `review_legal`
- `review_product`
- `done`
- `rejected`

## Initial Tasks

The initial board must include:

1. `evidence-validator-hardening`
2. `customer-claim-truth-cleanup`
3. `source-summary-fresh-alert-counting`
4. `vara-final-source-to-25`
5. `dfsa-publication-listing-adapter`
6. `sca-table-download-adapter`
7. `fiu-circulars-public-source-investigation`
8. `difc-consultation-listing-adapter`
9. `mof-document-publication-adapter`
10. `moj-gazette-official-alternative-research`
11. `ruflo-safe-tooling-intake`

## Update Rules

- Chief of Staff owns sequencing.
- The task owner can move a task from `accepted` to `in_progress`.
- Source activation tasks cannot skip `review_source_monitor`.
- Evidence-bearing tasks cannot skip `review_evidence`.
- Customer-facing wording cannot skip `review_legal`.
- No task is `done` until validation commands pass or the blocker is documented and accepted by QA.
- Agent notes must be additive and must not delete prior context.

## Non-Goals

- No automatic code execution.
- No background worker.
- No external database.
- No full Ruflo install.
- No agent self-commit.
