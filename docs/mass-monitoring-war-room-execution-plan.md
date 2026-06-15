# Mass Monitoring War-Room Execution Plan

## 1. Current Repo State

- Starting commit: `b3eaf1d feat: add safe batch source activation runner`.
- Clean-state gate at sprint start: passed.
- Product workspace: `/Users/kurbnovomar/StatuteProof-Command-Center/product`.
- Current public source truth remains: `13 enabled UAE sources / 9 readiness-supported / 4 remediation`.

## 2. Current Public Source Truth

The public truth must not change unless the registry, proof artifacts, repeat baselines, agent gates, and validators prove it. A no-save pass is not evidence. One saved run is not monitoring-ready.

## 3. Previous Sprint Completed

- Source Discovery Engine exists.
- Auto DOM Investigator exists.
- Adapter platform exists.
- Source Lab remediation UI exists.
- Mass source activation state machine exists.
- Safe batch activation runner exists.
- Mass source activation queue exists at `product/regradar/config/mass_source_activation_queue.json`.
- Last sprint improved SCA/DFSA/CBUAE discovery and failure classification, but produced `0` strong no-save passes and `0` new activation-ready sources.

## 4. Why Sources Still Do Not Activate

- SCA pages still need stable item-level extraction for listings/tables.
- DFSA endpoints still need exact URL/selector remediation and rulebook/module handling.
- CBUAE blocks some direct pages with HTTP 403, so official alternate endpoints and document listings are needed.
- ADGM/FSRA has near-ready candidates but still needs proof/repeat baseline/gates to become monitoring-ready.
- Mass monitoring needs a runner that only processes activation-ready/enabled sources and records source-health states.

## 5. Exact Goal For This Sprint

1. Remediate SCA, DFSA, and CBUAE toward real strong no-save passes.
2. Move any strong passes through saved evidence and repeat baseline if technically safe.
3. Build a safe mass monitoring runner that never monitors candidate/remediation/blocked/rejected sources by default.
4. Keep source truth unchanged unless strict proof and validators allow a change.
5. Leave exact blockers and next tasks where official sources remain blocked.

## 6. Adapter / Source Groups To Prioritize

- SCA: regulation/listing/table rows, AML/CFT, circulars/rules, market rules.
- DFSA: AML/MLRO notices, rulebook official/official-linked modules, enforcement/consultations if accessible.
- CBUAE: regulations, circulars/notices/publications, AML/CFT, payments/stored value/RPSCS, official PDF/document listings.
- ADGM/FSRA: financial crime and rules/regulations near-ready baseline work.
- VARA and FIU/EOCN: opportunistic official endpoints only if they are clear and technically safe.

## 7. Mass Monitoring Runner Goal

Add or finish a queue-driven runner that:

- defaults to dry-run/no-alerts;
- processes only `activation_ready` queue entries or enabled sources;
- skips candidate/remediation/blocked/rejected sources;
- rate-limits per domain;
- records source-health statuses such as `MONITOR_OK`, `QUALITY_DROP`, `SELECTOR_BROKEN`, `NAV_SHELL_ONLY`, and `REMEDIATION_REQUIRED`;
- never updates `sources.json` or customer-facing truth by itself.

## 8. Agent / Skill Gate Plan

Use or emulate exactly the existing 10 StatuteProof agents. No 11th agent will be added. Relevant repo skills will be used for source monitoring, evidence readiness, custom parser review, legal-safe copy, test-driven development, systematic debugging, prompt-injection review, and verification before completion.

## 9. Files To Inspect

- `AGENTS.md`, `TOOL_ROUTER.md`, `.claude/agents/`, `agents/`, `.agents/skills/`, `skills/`, `workflows/`
- `product/regradar/app/source_discovery.py`
- `product/regradar/app/dom_investigator.py`
- `product/regradar/app/source_intake.py`
- `product/regradar/app/mass_source_activation.py`
- `product/regradar/app/mass_source_activation_runner.py`
- `product/regradar/app/adapters/`
- `product/regradar/app/proof.py`
- `product/regradar/app/source_runs.py`
- `product/regradar/app/diff.py`
- `product/regradar/app/source_quality.py`
- `product/regradar/app/source_certification.py`
- `product/regradar/run.py`
- `product/regradar/sources.json`
- `product/regradar/config/mass_source_activation_queue.json`
- `product/regradar/config/uae_source_candidates.json`
- `product/regradar/config/uae_source_work_queue.json`
- `product/regradar/tests/`
- `tools/`

## 10. Files Likely To Change

- `product/regradar/app/mass_monitoring_runner.py`
- `product/regradar/app/mass_source_activation_runner.py`
- `product/regradar/app/source_discovery.py`
- `product/regradar/app/dom_investigator.py`
- `product/regradar/app/adapters/*`
- `product/regradar/run.py`
- `product/regradar/config/mass_source_activation_queue.json`
- `product/regradar/tests/*`
- `tools/validate_mass_monitoring_runner.py`
- selected validation tools if needed
- task-specific docs and reports

## 11. Live Validation Plan

Run only controlled source checks, starting with no-save. Save evidence only for strong no-save passes. Run repeat baselines only for saved candidates. Run mass-monitor dry-run only for activation-ready/enabled sources. No customer messages, no Telegram/email, no broad monitor, and no all-source run.

## 12. Commit Plan

If validation passes, stage only task-related files. Commit as:

- `feat: build safe mass source monitoring pipeline` when runner and activation improvements are built;
- `feat: activate proof-backed UAE monitoring sources` only if new activation-ready sources are truly added;
- `test: harden mass monitoring activation gates` if mostly tests/docs.

Push to `origin main` only after validation passes.

## 13. What Will Not Be Touched

- Cloudflare
- DigitalOcean
- `.env` or secrets
- customer messaging
- customer-facing claims of 50/60 sources unless proven
- unproven `sources.json` activation
- private/login/CAPTCHA/paywalled sources
- unrelated files
