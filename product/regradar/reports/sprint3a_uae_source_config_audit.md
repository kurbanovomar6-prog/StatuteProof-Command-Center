# Sprint 3A — UAE Source Config Audit

## 1. Verdict

- This was config-only plus documentation.
- No sources were activated.
- No backend behavior, API behavior, source monitoring logic, adapter logic, hashing, diffing, proof, alert draft, or weekly brief behavior was changed.
- Only existing UAE source URL metadata and limitation notes were corrected where the repo already had a stale official URL.

## 2. Files changed

- `sources.json`
- `reports/sprint3a_uae_source_config_audit.md`

## 3. URL corrections made

| Source | Old URL | New URL | Why corrected | Status changed? |
| --- | --- | --- | --- | --- |
| DIFC Laws and Regulations | `https://www.difc.ae/business/laws-regulations/` | `https://www.difc.com/business/laws-and-regulations/` | Current official DIFC laws/regulations page is under `difc.com`; note added to verify item-level structure before expansion. | No |
| UAE Ministry of Economy | `https://www.moec.gov.ae/en/` | `https://www.moet.gov.ae/en/` | Current official Ministry of Economy and Tourism domain is `moet.gov.ae`; note added that PDF-heavy content requires validation. | No |
| UAE Legislation Portal | `https://uaelegislation.gov.ae/` | `https://uaelegislation.gov.ae/` | URL left unchanged; limitation note added because item-level monitoring and access behavior still require validation. | No |

## 4. Sources left unchanged

- Central Bank of the UAE — current URL: `https://www.centralbank.ae/`; unchanged.
- Dubai Virtual Assets Regulatory Authority (VARA) — current URL: `https://www.vara.ae/`; unchanged.
- Dubai Financial Services Authority (DFSA) — current URL: `https://www.dfsa.ae/`; unchanged.
- Abu Dhabi Global Market (ADGM) — current URL: `https://www.adgm.com/`; unchanged. No `fsra.adgm.com` active source entry was found.
- UAE Ministry of Finance — current URL: `https://mof.gov.ae/`; unchanged.
- UAE Financial Intelligence Unit (UAEFIU) — current URL: `https://www.uaefiu.gov.ae/`; unchanged.
- UAE Securities and Commodities Authority (SCA) — disabled navigation-only entry remains unchanged.
- UAE Federal Tax Authority (FTA) — disabled external-access entry remains unchanged.
- UAE e-Laws Portal (Ministry of Justice) — disabled external-access entry remains unchanged.

## 5. Sources not activated

- UAE Data Office / PDPL — no monitorable source entry was activated; standalone candidate URL remains unconfirmed.
- UAE Official Gazette — no separate source was activated; no separate official-gazette monitoring was claimed.
- UAE Legislation Portal — already active, but item-level access and WAF behavior still require validation.
- Executive Office AML/CFT — no source was activated; no consolidated publications index was confirmed in this config pass.
- ADGM/FSRA dedicated notices or circulars — not activated; exact official listing still requires validation.
- Federal Tax Authority — not activated; current repo entry remains disabled due access limitations.
- Capital Market Authority / former SCA — not activated; current repo entry remains disabled navigation-only.

## 6. Recommended Sprint 3B candidates

- ADGM/FSRA — validate a dedicated official notices or circulars listing if one can be located under `adgm.com`.
- Federal Tax Authority — validate whether any public laws/guides page is extractable from current infrastructure.
- SCA/CMA — validate the current authority domain and any publications endpoint before considering config changes.
- DIFC Laws — validate the corrected `difc.com` page and item-level structure.
- VARA — validate official publications/rulebook sub-pages for item-level monitoring.
- UAE FIU — validate whether guidance, typologies, or publication sub-pages are more stable than the root.

## 7. Risks / limitations

- WAF and 403 behavior may change without notice.
- Official pages mirrored or routed through third-party infrastructure may create dependency risk.
- PDF-heavy sources need extraction validation before being used for client brief output.
- JavaScript pagination and SPA sources need rendering validation before source expansion.
- Source status must be re-verified before any activation or public coverage update.

## 8. Next recommended action

Run Sprint 3B as validation-only checks for the five lowest-barrier candidates. Do not activate immediately. Produce a validation table first, then decide separately whether any candidate is safe for a later source configuration change.
