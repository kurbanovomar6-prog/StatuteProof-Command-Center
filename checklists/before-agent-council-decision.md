# Checklist: Before Agent Council Decision

Complete all items before triggering a seven-stage agent council review. The council takes time — confirm that the decision warrants it.

## Decision Qualification

- [ ] This decision has real consequences (legal, evidence-integrity, trust, or customer impact)
- [ ] A wrong decision cannot be easily reversed
- [ ] At least one of: legal language risk, evidence completeness risk, source feasibility risk, or customer-facing output is involved
- [ ] This cannot be resolved with a single-agent review or a simple checklist

If none of the above are true: do not use Workflow 07. Use the appropriate single-agent or skill-based review instead.

## Decision Statement

- [ ] Decision statement is written (one paragraph: what, options, stakes)
- [ ] Options are clearly labeled A / B / C
- [ ] The stakes of each option are stated
- [ ] Relevant context is included (current pipeline status, evidence record status, customer relationship status)

## Context for Stage 2 (Source Monitor)

- [ ] Source URL(s) involved in the decision are known and named
- [ ] URL verification status is known (verified / unverified / VERIFY BEFORE PRODUCTION)
- [ ] Any known fetch failures or quality drops are documented

## Context for Stage 3 (Evidence Trail)

- [ ] Evidence record ID is known (if a brief is involved)
- [ ] evidence_record_status is known (complete / pending / none)
- [ ] proof_quality is known (GOOD / LIMITED / INCOMPLETE)

## Context for Stage 5 (Legal Language)

- [ ] Any customer-facing language involved in the decision has been drafted
- [ ] The draft has been read once for obvious forbidden claims before the council review

## After the Council

- [ ] Output will be recorded as a dated note
- [ ] If EXECUTE: owner is named and 3 actions are assigned
- [ ] If EXECUTE_WITH_CONDITIONS: conditions are logged with owner and deadline
- [ ] If HOLD: date for re-review is set
