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
- [x] F2 detected facts in alerts (cycle 2) — DONE
      Commit a6d1ed4. Red first (module missing), then 13 tests green;
      full suite 684 passed / 0 failed. One legacy test
      (test_detected_deadline_is_rendered_when_present) updated to the new
      contract: deadline renders ONLY from a rule detection with a span.
      Real-delta proof (docs/signal/detected_facts_real_deltas.txt):
      CBUAE retail-payment delta -> "Effective from 1/8/2022",
      "Status: In-Force"; SCA delta -> 8 law refs incl. Federal Decree-Law
      No. (20) of 2018; EOCN delta -> AR ref قرار مجلس الوزراء رقم (134)
      لسنة 2025 detected.
- [x] F3 Arabic lane (cycle 3) — DONE, commit e3e0b6a
      app/arabic_text.py (diacritics/kashida/directional/digit folding);
      measured AR term lane merged into the severity ladder; MEDIUM_ARABIC
      human-review rule id restored; letterhead noise-guards (VARA name,
      UAEFIU tagline demoted after replay showed noise upgrades 17->32 HIGH;
      corrected before commit). 11 AR tests red->green; suite 696 green.
- [x] F4 scoring depth (cycle 4) — DONE, commit f223635
      Word-bounded matching (ban-in-bank dead), topic terms demoted,
      FORMAT_SHIFT_REVIEW guard for adapter output flips, EN additions.
      9 tests red->green; suite 705 green. Full-stack regression over all
      63 historical runs: HIGH 23->11, 13 NO_DIFF, 2 error-filtered; every
      shift justified per judgment class in
      docs/signal/severity_regression_f4.md. Residual 11 HIGHs are
      PDF-reflow / wrong-page / adapter-jitter classes addressed
      operationally by the F1 reset + stable adapters — stated, not hidden.
- [x] F5 QUALITY_DROP retention (cycle 5) — DONE, commit 68e858a
      compact_quality_drop_repeats: transitions forever, old repeats to
      last-of-day; idempotent; CLI-wired. Real split: 122 QD = 103
      transitions + 19 repeats. 3 tests red->green; suite 708 green.
- [x] F6 activation-ready pack (cycle 6) — DONE, commit 31c2834
      One real probe per top-10: ADGM waivers (1,931ch good) + RA circulars
      (9,291ch good) proven fresh-alert; 5 FTA = nav-shell (11-66ch, JS
      adapter needed); UAEFIU fetched OK today (geo-block intermittent) BUT
      circulars & typology render the same Publications shell — flagged.
      Probe found 2 normalization leaks (Total visitors, bare hex colors)
      — fixed red->green. Sources remain DISABLED; sources.json untouched.
- [x] Verification gate — DONE (commit c4b4414 + this one)
      Backend 714 passed / 0 failed. Frontend vitest 43/43, build OK,
      eslint 0 errors (3 pre-existing warnings, untouched files). Ruff
      clean on sprint files. Alert regenerations
      (docs/signal/ALERT_REGENERATION.md): both 05-Jul title-flips
      (recorded HIGH + queued) -> UNCHANGED, NO alert; UAEFIU 61->62 -> LOW
      rendered honestly; SAMPLE/FAKE genuine circular -> HIGH with 5
      detected facts in Telegram + email bodies. e2e EN+AR+PDF lifecycle
      green in isolated dir (baseline -> alert-once -> heartbeat;
      error-page never baselines; found+fixed status-clobber defect in
      run_pipeline_for_source). Fresh-clone simulation: see final report.

NOTE for gate: history contains NO unambiguous genuine regulatory change.
Closest real candidates: UAEFIU publications count 61→62 (2026-06-11),
legislation-portal category counts. A genuine-change regeneration will use
the closest real one plus a clearly-labeled synthetic genuine paragraph on a
real snapshot. This is stated honestly, not hidden.

## Safety rails held

- No touches to deploy/, DEPLOY.md, UPDATE.md, DEPLOY_PROGRESS.md, secrets,
  real data/evidence trail (read-only analysis only).
- No baseline reset executed anywhere. Deploy pin c1ddb8a untouched.
