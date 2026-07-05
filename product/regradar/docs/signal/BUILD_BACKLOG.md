# BUILD_BACKLOG — signal-max sprint (Phase 1, ≤6 cycles)

Per item: expected impact on a real customer alert · effort · risk.
Order confirmed by Phase-0 evidence (SIGNAL_QUALITY.md): 44% of historical
CHANGED events were self-inflicted extraction noise → F1 first.

## F1 — Extraction truth (cycle 1)

Strip nav/chrome/boilerplate so hashes and diffs are content-only; detect
error pages (404/502/Cloudflare) and route them to FAILED instead of
baseline; stamp extractor version into run records so extractor upgrades
trigger a *planned* reset instead of fake CHANGED alerts.
- Impact on a real alert: the 2026-07-05 title-flip alerts simply do not
  exist; DFSA/ADGM diffs shrink from ~140 lines of nav to content lines only;
  CBUAE rating counters (2 recorded false HIGHs) never reach scoring.
- Effort: M (normalization layer + tests + reset runbook). Risk: over-stripping
  genuine short lines — mitigated by conservative markers measured from the
  real trail (92/311 sources contain them) and title/publication-date
  preservation tests.
- Deliverable includes `RESET_RUNBOOK.md` (operator-scheduled prod baseline
  reset; alerts suppressed during window; NEVER executed in this sprint).

## F2 — Detected facts in alerts (cycle 2)

Extract dates/deadlines, AED amounts, licence/category refs, effective dates
from the actual delta; render in Telegram + email only when truly detected.
- Impact: closes the "Deadline: Not specified" boilerplate gap with truth.
  Pattern counts in the real corpus justify each extractor (629 law refs,
  200 effective-date, 145 AED amounts in deltas — SIGNAL_QUALITY.md §B).
- Effort: M. Risk: false facts worse than no facts → every fact carries its
  matched span; absence renders nothing.

## F3 — Arabic lane (cycle 3)

AR normalization (RTL, diacritics, Arabic-Indic digits) + AR detection terms
from measured frequencies (قرار 257, مرسوم بقانون 149, درهم 233 in deltas) +
EN/AR parity tests + explicit "Arabic — human review required" path.
- Impact: 20/63 historical deltas hit the Arabic branch that today returns
  MEDIUM with no rule id and no matched terms; they get truthful scoring or
  an honest human-review flag.
- Effort: M. Risk: AR deadline vocabulary too thin in trail (0 delta hits) —
  no fake confidence; that subset stays human-review.

## F4 — Scoring depth (cycle 4)

Word-boundary matching (kills `ban`⊂`bank` — proven defect), EN+AR rubric
expansion from §B counts, UK/US variants kept, every rule names actual
matches; regression over all 63 replayed runs: severities preserved or
justified-improved.
- Impact: CBUAE-style false HIGHs impossible; every alert reason cites its
  matched terms.
- Effort: S-M. Risk: silent severity reshuffle → full replay regression is
  part of the definition of done.

## F5 — QUALITY_DROP retention (cycle 5, small)

Transition records kept forever; steady-state repeats compacted like
heartbeats after 30 days; idempotent.
- Impact: indirect (trail hygiene; 122 QUALITY_DROP records today).
- Effort: S. Risk: low; TDD.

## F6 — Activation-ready pack (cycle 6)

Top-10 candidates from SOURCE_PORTFOLIO.md: configs/adapters + ONE one-shot
real fetch each proving extraction/normalization/hashing; label
fresh-alert-eligible vs evidence-library-only honestly; remain DISABLED.
- Impact: honest expansion pipeline; geo-blocked reality gets measured, not
  assumed.
- Effort: M. Risk: fetch failures are a *finding*, not a blocker — recorded
  as-is.

## Flagged, out of sprint scope

- The 21 never-classified enabled sources need monitoring_mode/alert_eligible
  decisions (owner call).
- `data/market_strategy.json` is legacy RegRadar positioning; persona values
  remain ASSUMED until real market evidence exists.
- `evidence-library` productization of the 83 static PDFs/docs.
