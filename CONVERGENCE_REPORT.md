# CONVERGENCE_REPORT — integrate/converge-2026-07-06

## BEFORE (frozen, all commands run this session 2026-07-06)

### Branch topology (`git fetch --all --prune` done)
| branch | SHA | ahead of main | behind | merge-base |
|---|---|---|---|---|
| main = origin/main | 1e10e9f6 | — | — | — |
| excellence | 8342e9d2 | 11 | 0 | 1e10e9f6 |
| signal-max | 16636580 | 15 | 0 | 1e10e9f6 |
| eval-fixes | 67fc2fb4 | 5 | 0 | 1e10e9f6 |

Overlap (files touched by 2+ branches, `git diff --name-only` intersections):
- excellence ∩ signal-max: **none** (67 vs 46 files, disjoint)
- excellence ∩ eval-fixes: `product/regradar/web/src/components/Hero.jsx`
- signal-max ∩ eval-fixes: `product/regradar/app/source_runs.py`

Merge order: default excellence → signal-max → eval-fixes confirmed optimal
(smallest branch carrying both overlaps lands last).

Primary checkout: 0 modified tracked files, 40 untracked (known dump —
untouched). All integration work in worktree `.claude/worktrees/converge`.

### Defect reproduction ON MAIN (worktree at origin/main, no .env present)
a) **ban ⊂ bank — reproduced**:
```
risk_level: MEDIUM | matched: ['ban']       # bank/banking text, no obligations
HIGH variant: HIGH ['ban', 'license']       # + 'licensed banks' → false HIGH
```
b) **suite red without developer .env — reproduced**:
```
1 failed, 654 passed, 6 warnings in 23.07s
FAILED tests/test_alert_dedup.py::test_pipeline_sends_once_then_suppresses_on_rerun
```
Known-red; fix expected from signal-max 8cc4ce2. Not patched here.
c) **audits — prior claims TRUE**:
```
pip-audit -r requirements.txt : 10 findings
  (pypdf ×5 CVE, deepdiff ×2, pdfminer-six ×2, requests ×1)
npm audit                     : 2 vulnerabilities (1 low, 1 high)
```
d) **CI untracked — TRUE**: `git status --porcelain .github/` → `?? .github/`;
`git ls-files .github/ | wc -l` → 0. File exists on disk only.

Frontend baseline on main: vitest 43/43, build ✓ 334ms, eslint 0 errors / 3 warnings.

No prior-report claim checked in Phase 0 turned out false.

## MERGE TRAIN (Phase 1)

Order: excellence (8342e9d) → signal-max (1663658) → eval-fixes (67fc2fb),
into `integrate/converge-2026-07-06`, each `--no-ff`.

**Manual conflicts: zero.** The two predicted overlap files auto-merged;
both were verified SEMANTICALLY, not trusted:
- `web/src/components/Hero.jsx`: carries excellence's health-driven counts
  (no hardcoded "116"/"every hour"/"60-min" — grep 0 hits) AND eval-fixes'
  `MonitoringStatusBadge` import + usage (lines 2, 335).
- `app/source_runs.py`: carries signal-max's `NORMALIZATION_VERSION` import
  (line 22) AND eval-fixes' cache stamp (`_CACHE_STAMP`, `_file_stamp`,
  lines 50/143/152-174).
No conflict-resolution rules needed to be exercised; nothing was resolved
by deleting a check (verified by adversarial diff pass, below).

### Gate results per train car (all outputs real, this session)
| Gate | backend (no .env) | frontend | build | eslint | pip-audit | npm audit |
|---|---|---|---|---|---|---|
| after excellence | 1 failed / 655 passed (expected red: dedup test, fix on signal-max) | 43/43 | ✓ 402ms | 0 errors/3 warnings | **0 findings** | **0 vulnerabilities** |
| after signal-max | **715 passed / 0 failed** (known-red went green exactly here) | 43/43 | ✓ 335ms | 0 errors | 0 | 0 |
| after eval-fixes | **721 passed / 0 failed** | **47/47** | ✓ 383ms | exit 0 (3 warnings) | 0 | 0 |

Regression probes (explicit): word-boundary rubric + N1 cache freshness +
N2 base-dir + N3 badge = 15 passed. Live probe on merged code:
`'licensed banks rating widget update'` → `MEDIUM ['update']`
(was `HIGH ['ban','license']` on main — pasted in BEFORE).

Evidence integrity: trail 1,406 lines / 0 corrupt.
JSONL/SQLite divergences: **16** — pre-existing documented legacy state on
the REAL trail (auto-heal forbidden by owner decision 2; the deploy docs
expect "~16 legacy divergences"). **Gate criterion amended from 0 to
"0 NEW divergences"** with this justification. NOTE + prior-claim
correction: the 2026-07-06 hostile-eval report stated "0 divergences" —
that was an environment artifact (checker ran against an isolated 3-line
test trail because STATUTEPROOF_BASE_DIR was exported in that shell).
The truthful number on real data is 16, unchanged by this train.

## PHASE 2 — CI

`.github/workflows/test.yml` written (backend suite + pip-audit with dummy
SECRET_KEY env; frontend vitest + build + eslint + npm audit
--audit-level=high), YAML-validated, all referenced paths verified to
exist, exact backend command re-run locally green (721 passed).
Committed as 9ce12a7 on `integrate/converge-2026-07-06`.

**Push of the workflow file is BLOCKED**: both the stored git credential and
the gh CLI token lack the `workflow` OAuth scope
(`gh auth status` → scopes: gist, read:org, repo; push rejected with
"refusing to allow an OAuth App to create or update workflow ... without
`workflow` scope"). This is an owner credential action — see NOT DONE.
Plainly: **CI committed locally; no remote CI run exists or is verified.**
The pre-existing untracked test.yml was also found broken (pytest not in
requirements.txt — it would fail at its own test step).

## PHASE 3 — LANDED ON MAIN

Main merged `--no-ff` from the full train tip (4b5f680, all three branches;
CI commit excluded solely due to the scope block) and **pushed**:
`1e10e9f..1992acc  main -> main`.
Post-merge sanity: `git log main..<branch>` = 0 commits for excellence,
signal-max, eval-fixes. `integrate/converge-2026-07-06` retains exactly 1
commit not on main: the CI workflow commit (intentional, documented).

### AFTER (fresh clone of PUSHED main, this session)
| check | BEFORE (main 1e10e9f) | AFTER (main 1992acc, fresh clone) |
|---|---|---|
| backend suite, no .env | 1 failed / 654 passed | **721 passed / 0 failed** |
| frontend tests | 43/43 | **47/47** |
| build | ✓ | ✓ 286ms |
| eslint | 0 errors / 3 warnings | exit 0 |
| pip-audit | **10 findings** | **No known vulnerabilities found** |
| npm audit | 2 (1 HIGH) | **found 0 vulnerabilities** |
| ban⊂bank | HIGH ['ban','license'] | MEDIUM ['update'] (word-bounded) |
| CI on remote | none | none (blocked; committed locally) |

## ADVERSARIAL VERIFICATION (5 independent verifiers, schema-forced, this session)

All five claims held: remote main state (1992acc, all marker files, no
workflow file), rubric truthfulness (7 adversarial inputs incl. genuine-HIGH
retention in delta scoring), suite counts (721/0 + 47/47, 0 skip markers),
no weakened validators (exactly 5 removed lines in the whole train diff, all
stricter or dead code; gate modules untouched), real evidence data untouched
(1406/0 corrupt, 432/116, mtimes predate session).

## PROVEN (this session, command-backed)
- main == origin/main == 1992acc; excellence/signal-max/eval-fixes fully
  contained; no train commit missing.
- Fresh clone of pushed main: backend 721/0 (no .env, 0 skipped), frontend
  47/47, build ✓, eslint exit 0, pip-audit 0, npm audit 0.
- ban⊂bank dead; VARA letterhead / UAEFIU tagline no longer HIGH; genuine
  obligations still HIGH (incl. delta-only path).
- No validator/gate weakened anywhere in 1e10e9f..1992acc (adversarial diff).
- Real trail and sources.json unmodified by the whole convergence.

## ASSUMED (not proven this session)
- CI workflow runs green on GitHub runners (never executed remotely; Python
  3.12 on ubuntu-latest is untested — local proof is 3.14/macOS).
- Post-reset steady-state noise levels (adapter stability, language flapping)
  — only historical replay evidence exists.
- The in-flight deploy session's state on the droplet (observed from outside:
  ssh open, no web ports).
- Persona/market value of the source portfolio (no customer evidence).

## STILL BROKEN (with severity)
1. **S0 — no production**: DNS → 207.154.250.157 (443 refused), droplet
   138.68.70.215 ssh-only; no scheduler or listener running anywhere; the
   parallel deploy pins c1ddb8a which ships the 10 pip CVEs + HIGH vite CVE
   and none of today's fixes. Owner must pick pin strategy (DEPLOY_RUNBOOK.md).
2. **S1 — no CI on remote**: workflow committed locally only; push blocked by
   missing `workflow` OAuth scope on both git and gh credentials. First
   remote run unverified. Owner: `gh auth refresh -h github.com -s workflow`,
   then push `integrate/converge-2026-07-06` or cherry-pick 9ce12a7 to main.
3. **S1 — baseline reset pending**: v2 normalization on 1992acc flips
   300/316 stored baselines; ANY monitoring run against existing baselines
   without ALERT_DRY_RUN mass-fires planned CHANGED alerts. Owner-scheduled
   Update Day per RESET_RUNBOOK.md. Until then main must not drive live alerts.
4. **S1 — alerts-bot token rotation overdue** (sat in a 438MB world-readable
   log; D5). Checklist in DEPLOY_RUNBOOK.md. Listener also down locally
   since Jul 5 18:27 (stale pidfile).
5. **S1 — NEW (found by adversarial verify on pushed main)**: strong/context
   self-pairing in app/risk.py — 'license', 'sanction', 'fine', 'penalty'
   sit in BOTH _HIGH_KEYWORDS and _HIGH_CONTEXT_WORDS, so ONE non-regulatory
   occurrence self-amplifies to HIGH ("penalty shootout ..." → HIGH;
   'licence' UK → MEDIUM but 'license' US → HIGH). Filed for the next
   scoring cycle; not patched (gates green, no-new-features rule).
6. **S1 — NEW**: NON_MATERIAL obligation gate is English-only
   (app/risk.py _OBLIGATION_KEYWORDS) — a genuine short (<80 char) Arabic
   obligation (يجب + ترخيص + عقوبة) is downgraded to NON_MATERIAL; the
   English equivalent is protected. Filed alongside #5.
7. **S2 — 16 legacy JSONL/SQLite divergences** on the real trail (documented,
   auto-heal forbidden) — resolved only by the Update-Day reset/investigation.
8. **S2 — landing 46,373px** (liability doubled from 24,926px); adapter
   format-shift noise class (22/63 historical) now capped at
   FORMAT_SHIFT_REVIEW MEDIUM but still enters customer-visible flow —
   routing to internal review is an open owner decision.
9. **S3 — verification emails still written as brief_unknown_*.json;
   /api/alerts/action-log 400 without params; risk.py docstring stale
   ('rate' listed, actual keyword set omitted).**

## NOT DONE (and why)
- **Deploy: NOT performed** — no owner confirmation in-session; parallel
  deploy session owns the droplet. DEPLOY_RUNBOOK.md emitted instead.
- **Token rotation / DNS cutover / log truncation**: owner-hands actions —
  checklists prepared, nothing executed, no secrets printed.
- **Update-Day baseline reset**: prepared (RESET_RUNBOOK.md, measured
  numbers), NOT executed anywhere.
- **ADGM source activation (2 proven)**: prepared, sources.json untouched
  (verified 432/116 unchanged) — awaiting explicit owner yes.
- **CI remote run**: blocked by credential scope (see STILL BROKEN #2).
- **Rubric defects #5/#6**: found post-land by adversarial verify; fixing
  them is a new behavior change outside this mission's no-new-features rule
  and deserves its own red-first cycle.
