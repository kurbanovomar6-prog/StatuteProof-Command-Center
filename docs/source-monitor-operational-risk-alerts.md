# Source Monitor Operational Risk Alerts

## 1. Product Principle

A serious compliance monitor must not fail silently. If a source becomes inaccessible, turns into a navigation shell, changes structure, collides with another hash, or requires selector remediation, StatuteProof should show that clearly instead of implying monitoring is healthy.

## 2. Current Gap

The parser already exposes statuses such as blocked, nav-shell, quality failure, hash collision, remediation, preview-only evidence, and baseline-required activation. The next product step is to make these operational states explicit in the source health model and UI.

## 3. Proposed Source Health States

| State | Meaning | User-facing copy |
|---|---|---|
| `MONITOR_OK` | Source passed current extraction, evidence, and baseline checks. | “Monitoring healthy.” |
| `MONITOR_DISCONNECTED` | Fetch/browser/source access failed after retries. | “Monitor disconnected. Check source manually.” |
| `QUALITY_DROP` | Quality score dropped below threshold. | “Extraction quality dropped. Review before relying on this source.” |
| `SELECTOR_BROKEN` | Required selector timed out or returned empty text. | “Selector needs remediation.” |
| `HASH_COLLISION` | Extracted hash collides unexpectedly with another source or prior bad shell. | “Hash collision detected. Review source mapping.” |
| `NAV_SHELL_ONLY` | Extracted text is primarily nav/search/accessibility chrome. | “Page shell detected. Configure a better selector or adapter.” |
| `SOURCE_STRUCTURE_CHANGED` | DOM/source structure changed enough to reduce extraction confidence. | “Source structure changed. Manual review required.” |
| `REMEDIATION_REQUIRED` | Source is official/useful but not ready. | “Under extraction remediation.” |
| `MANUAL_CHECK_REQUIRED` | A risk/access/quality uncertainty requires human review. | “Manual check required before monitoring.” |

## 4. Alerting Policy

Operational alerts should be generated when:

- a previously healthy source becomes blocked;
- a selector breaks;
- nav-shell extraction appears;
- normalized length drops sharply;
- regulatory density drops sharply;
- hash collision appears;
- source policy warning appears;
- baseline requirement is not met for an activated source;
- saved proof paths are missing for evidence-backed claims.

## 5. What To Build First

MVP:

1. Add canonical source health mapping from parser/readiness results.
2. Show health state on Sources and Source Lab pages.
3. Add remediation reason and next action.
4. Add validator checks so customer-facing UI cannot show raw `PASS`/`Validated` or hide remediation.

Full version:

1. Historical source health timeline.
2. Alert queue event for source health regressions.
3. Reviewer acknowledge/resolve workflow.
4. Exportable source-health audit report.
5. Notification integrations after manual approval.

## 6. Copy Rules

Allowed:

- “Monitor disconnected.”
- “Manual check required.”
- “Selector needs remediation.”
- “Source structure changed.”
- “Extraction quality dropped.”

Forbidden:

- “We never miss updates.”
- “Certified monitoring.”
- “Guaranteed parsing.”
- “Source is validated” unless evidence criteria explicitly justify an evidence-specific statement.

## 7. Implementation Recommendation

Do not build a full alerting system in this source-pack strategy task. Add the status model to the roadmap and validator scope, then implement health state mapping in a focused parser/UI sprint.
