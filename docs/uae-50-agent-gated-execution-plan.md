# UAE 50 Agent-Gated Execution Plan

## 1. Current State

Latest verified commit before this sprint: `30764fa`.

Public customer-facing source truth remains:

**13 enabled UAE sources / 9 readiness-supported / 4 under extraction remediation.**

The candidate map contains 63 UAE official-source candidates in `product/regradar/config/uae_source_candidates.json`. Prior work mapped 60 official-source candidates, tested the top 40 without saving evidence, remediated ADGM/FSRA and SCA selectors, and saved local baseline evidence for three ADGM/SCA candidates. The project has not activated an expanded default pack in `product/regradar/sources.json`.

## 2. Agent And Skill Use

This sprint uses the existing StatuteProof 10-agent roster from `AGENTS.md`. No 11th active agent is added.

Subagent execution tools are not exposed in this Codex session, so the gates are applied manually and recorded in structured source queue fields. The review logic is grounded in these repo-scoped skills:

- `source-monitoring-review`
- `evidence-readiness-review`
- `custom-source-parser`
- `legal-safe-copy-review`
- `verification-before-completion`
- `test-driven-development`

## 3. Agent Gate Ownership

| Agent | Gate Owned | Can Block When |
|---|---|---|
| Chief of Staff | Scope control and sequencing | Work expands into deployment, broad monitoring, or an 11th agent. |
| Product Manager | Buyer value and pack relevance | Source is vanity padding or not useful to MLRO/CCO/compliance teams. |
| Code Architect | Parser/adapter/source-registry architecture | Fix requires a broad rewrite, unsafe dependency, or evidence-pipeline risk. |
| QA / Critic | False-ready prevention | Nav-shell, duplicate hash, shallow text, stale count, or fake-ready wording appears. |
| Legal Language | Customer-facing claim safety | Copy implies legal advice, guaranteed compliance, regulator certification, or "validated" without proof. |
| Source Monitor | Officialness, URL correctness, selector quality, source health | URL is wrong, blocked, unstable, private, irrelevant, or selector extracts shell/chrome. |
| Evidence Trail | Proof paths, hashes, source runs, baseline count | Proof is missing, baseline is incomplete, hashes are not verifiable, or evidence level is overstated. |
| Risk + Brief Pipeline | Future brief eligibility after evidence | Source has no evidence record or cannot support human-reviewed brief workflow. |
| ICP Lead Research | UAE MLRO/CCO relevance | Source does not solve a real regulated-firm monitoring need. |
| Outreach Writer | Only customer-facing source-pack wording | Copy is generic, salesy, or not legal-safe after review. |

## 4. Required Per-Source Gate Fields

Every entry in `product/regradar/config/uae_source_work_queue.json` must include:

- `source_monitor_gate`
- `evidence_trail_gate`
- `qa_critic_gate`
- `legal_language_gate`
- `code_architect_gate`
- `product_manager_gate`
- `final_activation_gate`

Gate statuses must be one of `pass`, `hold`, or `fail`, except `final_activation_gate.status`, which must be one of:

- `activation_ready`
- `baseline_pending`
- `remediation`
- `blocked`
- `rejected`
- `candidate`

## 5. What Each Gate Blocks

- Source Monitor blocks non-official sources, wrong-country sources, private/paywalled/login/CAPTCHA sources, wrong final URLs, nav-shell selectors, and source-health risks with no remediation note.
- Evidence Trail blocks proof-free evidence claims, missing proof paths, missing normalized text paths, duplicate shell hashes, and baseline counts below the required rule.
- QA / Critic blocks customer-visible readiness when quality is `POOR`, output is shallow, hash collisions are unresolved, or no-save preview is treated as evidence.
- Legal Language blocks `validated`, `certified`, `guaranteed`, `perfect`, `any website`, legal advice, regulator partnership, and complete-coverage claims.
- Code Architect blocks risky parser rewrites, large dependency installs, third-party vendoring, or adapters that bypass the existing evidence pipeline.
- Product Manager blocks sources that pad count without clear buyer relevance.

## 6. Gate Recording Rules

- `activation_ready` requires all major gates to pass and baseline requirements to be met.
- `proof_saved` without enough baselines remains `baseline_pending`.
- No-save success remains `no_save_passed` and cannot become evidence-confirmed.
- `sources.json` must not be expanded with active sources until the activation decision report proves the gates.
- Ignored local evidence artifacts may be referenced by path in reports, but must not be force-added without an explicit evidence artifact policy.

## 7. Files To Use

- `product/regradar/config/uae_source_candidates.json`
- `product/regradar/sources.json`
- `docs/top-40-source-no-save-validation-report.md`
- `docs/top-40-alert-fatigue-risk-report.md`
- `docs/top-40-source-health-risk-report.md`
- `docs/adgm-fsra-sca-saved-evidence-baseline-report.md`
- `docs/adgm-fsra-sca-source-activation-decision.md`
- `docs/no-garbage-source-policy.md`
- `docs/parser-quality-gates.md`

## 8. Validation Plan

Run:

- `python3 -m compileall product/regradar`
- `python3 -m pytest product/regradar/tests/test_parser_benchmark_suite.py -q`
- `python3 tools/validate_uae_source_pack.py`
- `python3 tools/validate_uae_50_working_sources.py`
- `python3 tools/validate_parser_quality.py`
- `python3 tools/validate_workspace.py`
- `python3 tools/validate_codex_skills.py`
- `git diff --check`

## 9. Commit Plan

If fewer than 50 sources reach the full working-source gate, commit truthful infrastructure and progress with:

`test: advance UAE source pack toward 50 working sources`

If at least 50 sources genuinely pass proof, baseline, and agent gates, commit with:

`feat: build proof-backed UAE 50-source working pack`

## 10. What This Sprint Will Not Touch

- No deployment.
- No Cloudflare or DigitalOcean changes.
- No customer delivery.
- No broad all-source monitor run.
- No legal advice or compliance guarantee.
- No fake source-readiness expansion.
- No active `sources.json` expansion unless evidence and gates justify it.
