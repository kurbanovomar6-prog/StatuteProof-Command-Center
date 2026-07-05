# PROGRESS_SIGNAL — signal-max sprint

Branch: `signal-max` off main `1e10e9f6bf618225d23667d69ea54b79bf638679`.
Worktree: `.claude/worktrees/signal-max` (main checkout untouched — deploy
session may run in parallel). Real trail read-only at the primary checkout;
all tests isolated via STATUTEPROOF_BASE_DIR.

## Phase 0 — DONE (this file's commit)

- A. Severity replay: 68 CHANGED, 63 replayed, 0 unambiguous genuine changes;
  59 noise / 3 possible-genuine (count increments) / 1 weak-genuine (rebrand).
  Two 2026-07-05 recorded-HIGHs replay LOW. Proven rubric defects:
  substring `ban`⊂`bank`, Arabic branch missing rule id, error-page baselines,
  extractor-change CHANGED events (44% of history).
  → docs/signal/SIGNAL_QUALITY.md, judgment_table.md, replay_severity.jsonl
- B. Term frequency EN/AR with counts → term_frequency_output.txt
- C. Noise anatomy: 92/311 sources flip baseline on clean (minimum) →
  noise_anatomy.jsonl
- D. Portfolio: 432 = A56/B27/C33/REM27/EXCL153/POOL136; 33 ineligible with
  exact reasons; top-20 AE candidates (persona value ASSUMED) →
  SOURCE_PORTFOLIO.md, portfolio.jsonl
- E. BUILD_BACKLOG.md written; F1→F6 order confirmed by evidence.

## Phase 1 — build cycles (hard cap 6)

- [x] F1 extraction truth + RESET_RUNBOOK.md (cycle 1) — DONE
      Commits: 8cc4ce2 (dedup test .env hidden dependency — pre-existing
      failure on main, fixed), f61c44f (v2 normalization).
      Red→green: 16 new tests failed on import, then 24 green; full suite
      672 passed / 0 failed. Real-data proof: 63 replayed CHANGED runs →
      13 no-diff after clean (incl. both 05-Jul title-flips) + 2
      error-page-filtered; 48 remain CHANGED (adapter-format noise — not
      fixable by normalization; mitigated operationally by
      normalization_version stamping + reset discipline).
      Reset sizing measured: 300/316 snapshots flip, 86 of 116 enabled →
      RESET_RUNBOOK.md (prepared, NOT executed).
- [ ] F2 detected facts in alerts (cycle 2)
- [ ] F3 Arabic lane (cycle 3)
- [ ] F4 scoring depth (cycle 4)
- [ ] F5 QUALITY_DROP retention (cycle 5)
- [ ] F6 activation-ready pack (cycle 6)
- [ ] Verification gate (suites green with counts; 3 historical alert
      regenerations incl. 05-Jul title-flip + genuine change; e2e EN+AR+PDF
      in isolated dir; fresh-clone sim)

NOTE for gate: history contains NO unambiguous genuine regulatory change.
Closest real candidates: UAEFIU publications count 61→62 (2026-06-11),
legislation-portal category counts. A genuine-change regeneration will use
the closest real one plus a clearly-labeled synthetic genuine paragraph on a
real snapshot. This is stated honestly, not hidden.

## Safety rails held

- No touches to deploy/, DEPLOY.md, UPDATE.md, DEPLOY_PROGRESS.md, secrets,
  real data/evidence trail (read-only analysis only).
- No baseline reset executed anywhere. Deploy pin c1ddb8a untouched.
