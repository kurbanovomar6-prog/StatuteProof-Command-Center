# StatuteProof 8/10 Delivery Readiness Agent Council Prompt

## Mission

Drive StatuteProof/Regradar from the current honest trust/delivery readiness level toward 8/10 by proving the monitoring-to-brief path with real saved artifacts, not claims.

8/10 means:
- source monitoring changes are triaged, not merely counted;
- parser noise is separated from useful regulatory signals;
- canonical evidence links exist for material alerts;
- human review is explicit;
- customer delivery stays blocked unless evidence, review, legal, and brief gates pass;
- source-health failures are visible and documented;
- the product can be shown to a qualified design-partner prospect without pretending production readiness.

8/10 does not mean:
- complete UAE coverage;
- complete family coverage;
- legal advice;
- guaranteed compliance;
- perfect parsing;
- never-miss monitoring;
- real customer proof;
- production SLA.

## Hard Rules

- Work only inside `/Users/kurbnovomar/StatuteProof-Command-Center`.
- Do not deploy.
- Do not touch Cloudflare/DigitalOcean.
- Do not print `.env`.
- Do not print, expose, or commit secrets.
- Do not send emails.
- Do not create fake users, fake customers, fake evidence, fake briefs, or fake source results.
- Do not fake `MONITOR_OK`.
- Do not activate no-save-only or one-run-only sources.
- Do not weaken validators.
- Do not claim complete UAE coverage.
- Do not claim legal advice, guaranteed compliance, regulator certification, perfect parsing, never-miss updates, or all-source coverage.
- Do not stage runtime DB files, raw evidence, source snapshots, alert queue runtime files, secrets, screenshots, or unrelated files.
- Exactly 10 active agent roles only. Modes are allowed; no 11th active agent.

## Agent Roster

1. Chief of Staff - Council Router / Orchestrator
2. Product Manager - Pilot/Beta/Production Readiness Gate
3. Code Architect - Implementation Owner
4. QA / Critic - External CTO Scorer
5. Legal Language - Claims Gate
6. Source Monitor - Source Truth Gate
7. Evidence Trail - Evidence Corpus Auditor
8. Risk + Brief Pipeline - Customer Delivery Gate
9. ICP Lead Research - Market/GTM Scorer
10. Outreach Writer - Prompt Router / Handoff Scribe

## Agent Runtime Truth Rule

If fresh agents cannot launch because of runtime limits, stop agent claims immediately.

Allowed fallback:
- continue as Codex local execution;
- label every packet as `Codex local fallback`;
- record the agent launch failure;
- do not count fallback notes as real agent packets.

## Required Packet Fields

Every real agent packet or Codex fallback packet must include:

- verdict: PASS / HOLD / FAIL
- task_score: 1-100 and 1-10
- evidence found
- exact files inspected
- exact commands run
- bugs or blockers found
- methods attempted
- safe alternatives remaining
- legal/claim risk
- prompt for next agent
- questions the next agent must answer
- stop/continue recommendation

## Phase 0 - Clean Gate

Run:

```bash
git status --short
git log --oneline -8
python3 tools/run_statuteproof_preflight.py
```

If dirty:
- inspect dirty files;
- do not revert user changes blindly;
- leave unrelated untracked runtime files alone;
- stop if uncertain.

Read:
- `docs/statuteproof-10-out-of-10-readiness-report.md`
- `docs/statuteproof-90-plus-recovery-report.md`
- `product/regradar/app/evidence_records.py`
- `product/regradar/app/weekly_brief.py`
- `product/regradar/app/alert_drafts.py`
- `product/regradar/app/source_health_timeline.py`
- `product/regradar/app/verified_monitoring_digest.py`
- `product/regradar/data/alert_queue/`
- `product/regradar/sources.json`

## Phase 1 - Honest Baseline

Launch at most 4 fresh agents.

Agent A - QA / Critic:
- score current product 1-100 and 1-10;
- list blockers to 8/10;
- define what cannot be solved without real customer proof.

Agent B - Source Monitor:
- inspect source runs and source-health report;
- list repeated-failure sources;
- decide which source families are safe to mention in outreach and which need caveats.

Agent C - Evidence Trail:
- inspect canonical evidence records;
- count linked vs unlinked alert queue items;
- verify which records are brief-input eligible.

Agent D - Risk + Brief Pipeline:
- inspect pending alerts;
- identify material review candidates vs parser noise;
- decide whether a non-customer digest or brief can be generated safely.

Coordinator:
- merge packets;
- if agents fail, document the runtime blocker and continue only as Codex fallback.

## Phase 2 - Verified Monitoring Digest

Build or run the operator-only digest:

```bash
python3 tools/generate_verified_monitoring_digest.py
python3 tools/validate_verified_monitoring_digest.py
```

The digest must classify every queued alert into:
- `HOLD` - blocked by missing evidence, pending evidence, source-health issue, or brief gate;
- `REVIEW_READY` - evidence gate passes and human review can evaluate the change;
- `NEEDS_PARSER_REVIEW` - diff may be meaningful but has parser/reflow/locale noise indicators;
- `LIKELY_NOISE` - non-meaningful diff, limited diff, counters, boilerplate, locale/hash-only changes.

The digest must include:
- total pending alerts;
- canonical evidence linked count;
- brief-input eligible count;
- source-health blockers;
- likely-noise count;
- top review candidates;
- exact next actions;
- `operator_only=true`;
- `customer_delivery=false`;
- `external_send=false`.

## Phase 3 - Alert Triage

For each pending alert:
- inspect diff metadata;
- inspect source family;
- inspect evidence link;
- inspect source-health status;
- label company use case;
- do not call a signal useful until human review can see what changed.

Reject as customer-ready:
- unlinked alert;
- pending/rejected/blocked evidence;
- limited or non-meaningful diff;
- repeated-failure source;
- source with no safe customer wording;
- forbidden legal claim.

## Phase 4 - Canonical Evidence Link Plan

For material alerts:
- find matching source run;
- generate canonical evidence if eligible;
- do not approve automatically;
- link `evidence_record_id` only when the record matches the alert run;
- verify `build_risk_brief_inputs()` before brief use.

Stop if:
- source run lacks proof path;
- normalized hash mismatches;
- diff artifact is missing;
- evidence record is pending/rejected/blocked;
- alert cannot be tied to a saved run.

## Phase 5 - Internal Non-Customer Brief/Digest

Only after at least one alert is evidence-linked and review-approved:
- build an internal non-customer draft;
- label it `INTERNAL SAMPLE - NOT CUSTOMER DELIVERY`;
- run forbidden phrase scan;
- keep `delivery_approved=false`;
- keep `customer_delivery=false`;
- document the exact chain:
  source run -> canonical evidence -> human review -> alert -> draft -> legal scan -> delivery blocked.

## Phase 6 - Source Health Remediation

For every source with 3+ consecutive `FAILED` or `QUALITY_DROP` runs:
- inspect latest runs;
- inspect source config;
- inspect whether failure is WAF/login/CAPTCHA/private access;
- try safe public alternatives only;
- fix adapter if safe and small;
- otherwise downgrade/document remediation.

Do not bypass access controls.
Do not fake recovery.

## Phase 7 - Legal and Claim Safety

Legal Language + QA must scan any report, website, outreach, or dashboard copy.

Reject:
- complete UAE coverage;
- complete family coverage;
- legal advice;
- guaranteed compliance;
- regulator certification;
- perfect parsing;
- never-miss monitoring;
- all-source coverage;
- customer-ready evidence-backed briefs without a completed approved path.

## Phase 8 - Validation

Run:

```bash
python3 -m compileall -q product/regradar tools
python3 -m pytest product/regradar/tests -q
python3 tools/validate_verified_monitoring_digest.py
python3 tools/run_statuteproof_preflight.py
git diff --check
```

If frontend touched:

```bash
cd product/regradar/web
npm run build
npm run lint
node scripts/validate-routes.mjs
```

Do not claim clean if anything fails.

## Phase 9 - 8/10 Acceptance Criteria

The project may be called 8/10 for internal delivery readiness only when:

- one verified monitoring digest is generated from real saved alerts;
- all pending alerts are classified honestly;
- at least one material alert has canonical evidence linked;
- at least one canonical evidence record is founder/operator approved;
- at least one internal non-customer draft/digest is generated through gates;
- source-health blockers are visible and documented;
- validators reproduce the safety boundaries;
- no customer delivery is implied;
- no coverage/legal overclaim is present.

Without a real pilot customer, payment, and uptime history, the product cannot honestly be 8/10 for production SaaS readiness.

## Final Output Required

1. Worktree clean before start yes/no
2. Agents launched count
3. Agent launch failures count
4. Fallback used yes/no
5. Starting honest score
6. Ending honest score
7. Did it reach 8/10 yes/no
8. If not, exact blockers
9. Alerts classified count
10. Likely noise count
11. Source-health blockers count
12. Canonical evidence linked alerts count
13. Brief-input eligible alerts count
14. Internal non-customer digest generated yes/no
15. Customer delivery approved yes/no
16. Validators added count
17. Tests added count
18. Tests passed yes/no
19. Preflight result
20. Next exact engineering task
21. Next exact evidence task
22. Next exact source task
23. Next exact sales task
