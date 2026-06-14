# Workflow 11: Source Baseline And Evidence Save

Purpose: ensure a source does not move from preview/remediation into evidence-confirmed or monitoring-ready status without real saved proof artifacts.

## Required Agents

- Source Monitor: owns URL, selector, source type, extraction quality, and readiness status.
- Evidence Trail: owns proof completeness, hash paths, artifact paths, and append-only expectations.
- Code Architect: reviews implementation risk and data model impact.
- QA / Critic: blocks UI/API mismatch and false ready states.
- Legal Language: reviews customer-facing status wording.

## Rules

1. No-save Source Lab results are preview only.
2. One successful no-save test is not monitoring-ready.
3. Evidence confirmed requires saved proof artifacts.
4. Monitoring-ready requires baseline criteria and activation readiness rules.
5. Protected/private/login/CAPTCHA/paywall sources are blocked or remediation, not confirmed.
6. Selector timeout, nav-shell extraction, shallow text, PDF shallow extraction, or hash collision blocks confirmation.
7. DFSA/JS-heavy sources require live Playwright verification before any readiness promotion.
8. Founder/operator approval is required before customer-visible ready state if live verification is incomplete.

## Minimum Saved Artifact Checklist

- source ID
- official URL
- fetch/render provider
- extraction method
- normalized text path
- normalized hash
- proof JSON path
- quality score and label
- warnings
- failure reason or evidence-ready reason
- activation readiness

## Output

Create a source-baseline report with:

- command run
- saved artifact paths
- quality/evidence/activation status
- customer-facing label recommendation
- next action
