# Final Remediation Current-State Audit

Date: 2026-06-17

## Starting Truth

- Starting source truth: 79 enabled UAE sources / 76 readiness-supported / 3 remediation.
- Ending registry target is not assumed. Activation requires proof, repeat baseline, mass-monitor `MONITOR_OK`, and review gates.

## Remediation Sources Audited

| Source ID | Current URL | Owner | Starting status | Adapter/config | Last proof/hash | Exact blocker | Recommendation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `AE-dubai-financial-services-authority-dfsa` | `https://www.dfsa.ae/rules-and-standards` | DFSA | `enabled:true`, `status:remediation` | Generic selector / Playwright `main` test | None | Live no-save rendered a page-not-found/nav-shell result with normalized length 77 and quality 0. It collided conceptually with the notices remediation source. | Disable/replaced by stronger official DFSA report listing. |
| `AE-dfsa-notices` | `https://www.dfsa.ae/regulation/notices-public-registers` | DFSA | `enabled:true`, `status:remediation` | Generic selector / Playwright `main` test | None | Live no-save rendered the same page-not-found/nav-shell result with normalized length 77 and quality 0. | Disable/replaced by stronger official DFSA AML report listing. |
| `AE-uae-financial-intelligence-unit-uaefiu` | `https://www.uaefiu.gov.ae/` | UAE FIU | `enabled:true`, `status:remediation` | Generic extraction | None | Requests returned 403; Playwright rendered a large search/language/navigation shell. Source Lab classified it `NAV_SHELL_ONLY`, quality 0, no proof eligibility. | Keep remediation until a distinct official FIU endpoint passes proof, repeat baseline, mass-monitor, and gates. |

## Commercial Usefulness

- The two legacy DFSA URLs are not commercially useful as configured because they produce not-found shell output and would create false confidence.
- The UAE FIU homepage is official but too generic and shell-heavy. Existing active FIU circular/publication/typology endpoints carry the commercially useful FIU monitoring value today.
- Two official DFSA report endpoints are commercially useful replacements because annual and AML annual reports are useful for DFSA/MLRO review context and produce stable PDF-listing extraction.

## Final Audit Decision

- Attempt direct activation: none of the three original remediation URLs passed.
- Replace with better official endpoint: two DFSA sources.
- Keep remediation: UAE FIU homepage.
- Disable from customer-visible pack: two stale DFSA remediation endpoints were disabled and marked `status:replaced`.
