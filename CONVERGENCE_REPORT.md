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
