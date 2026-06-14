# Top-40 UAE Source No-Save Validation Report

## 1. Executive Verdict

Tested count: **40**.

Readiness-supported no-save count: **2**.

Remediation count: **38**.

Rejected count: **0** in this run. No candidate was removed from the candidate file, but 38 remain not accepted for default-pack activation.

Blocked count: **23**.

Can we market 40+ sources now? **No.**

Can we market 60 sources now? **No.**

Current customer-facing source truth remains:

**13 enabled UAE sources / 9 readiness-supported / 4 under extraction remediation.**

Important: all tests were no-save Source Lab checks. No evidence was written. No source became evidence-confirmed or monitoring-ready.

## 2. Batch Results By Regulator

| Regulator | Tested | Readiness statuses | Notes |
|---|---:|---|---|
| ADGM/FSRA | 6 | {'NAV_SHELL_ONLY': 4, 'CONFIRMED_ACCESSIBLE': 1, 'BLOCKED': 1} | {'remediation': 6} |
| ADGM | 2 | {'NAV_SHELL_ONLY': 2} | {'remediation': 2} |
| SCA | 5 | {'BLOCKED': 5} | {'remediation': 5} |
| VARA | 7 | {'NAV_SHELL_ONLY': 7} | {'remediation': 7} |
| CBUAE | 7 | {'BLOCKED': 7} | {'remediation': 7} |
| UAE FIU | 3 | {'BLOCKED': 3} | {'remediation': 3} |
| Executive Office for Control and Non-Proliferation | 1 | {'BLOCKED': 1} | {'remediation': 1} |
| Ministry of Economy | 1 | {'BLOCKED': 1} | {'remediation': 1} |
| Ministry of Finance | 1 | {'BLOCKED': 1} | {'remediation': 1} |
| UAE Legislation | 1 | {'NAV_SHELL_ONLY': 1} | {'remediation': 1} |
| DFSA | 5 | {'CONFIRMED_ACCESSIBLE': 2, 'BLOCKED': 3} | {'readiness_supported_no_save': 2, 'remediation': 3} |
| DIFC | 1 | {'BLOCKED': 1} | {'remediation': 1} |


## 3. Per-Source Results

| Candidate | Regulator | Readiness | Quality | Noise | Health | Length | Hash prefix | Preview |
|---|---|---|---:|---|---|---:|---|---|
| `AE-adgm-fsra-consultations` | ADGM/FSRA | `NAV_SHELL_ONLY` | 0 / POOR | high | high | 2641 | `ff5039aa00bc` | 404 / Overview / Jurisdiction / Authorities / Initiatives / ADGM Academy / Dispute Resolution / Careers / A pl |
| `AE-adgm-fsra-enforcement` | ADGM/FSRA | `CONFIRMED_ACCESSIBLE` | 54 / LIMITED | medium | medium | 31393 | `fecc1446362a` | Additional Financial Services Entities / Overview / Jurisdiction / Authorities / Initiatives / ADGM Academy /  |
| `AE-adgm-fsra-guidance-policy` | ADGM/FSRA | `NAV_SHELL_ONLY` | 0 / POOR | high | high | 2641 | `ff5039aa00bc` | 404 / Overview / Jurisdiction / Authorities / Initiatives / ADGM Academy / Dispute Resolution / Careers / A pl |
| `AE-adgm-fsra-homepage` | ADGM/FSRA | `BLOCKED` | 0 / POOR | high | high | 9804 | `df8923acddfc` | Financial Services Regulatory Authority (FSRA) | ADGM / Overview / Jurisdiction / Authorities / Initiatives /  |
| `AE-adgm-fsra-notices` | ADGM/FSRA | `NAV_SHELL_ONLY` | 0 / POOR | high | high | 2641 | `ff5039aa00bc` | 404 / Overview / Jurisdiction / Authorities / Initiatives / ADGM Academy / Dispute Resolution / Careers / A pl |
| `AE-adgm-fsra-rulebooks` | ADGM/FSRA | `NAV_SHELL_ONLY` | 0 / POOR | high | high | 2641 | `ff5039aa00bc` | 404 / Overview / Jurisdiction / Authorities / Initiatives / ADGM Academy / Dispute Resolution / Careers / A pl |
| `AE-adgm-legal-framework-legislation` | ADGM | `NAV_SHELL_ONLY` | 0 / POOR | high | high | 2641 | `ff5039aa00bc` | 404 / Overview / Jurisdiction / Authorities / Initiatives / ADGM Academy / Dispute Resolution / Careers / A pl |
| `AE-adgm-legal-framework-rules` | ADGM | `NAV_SHELL_ONLY` | 0 / POOR | high | high | 4472 | `3ff6b227e04d` | ADGM Legal Regulations and Rules / Overview / Jurisdiction / Authorities / Initiatives / ADGM Academy / Disput |
| `AE-sca-circulars` | SCA | `BLOCKED` | 23 / POOR | high | high | 3146 | `63df29361568` | Capital Market Authority / Services / My Fvourites / Most Used Services / Access to legislations / Legislation |
| `AE-sca-decisions` | SCA | `BLOCKED` | 23 / POOR | high | high | 3146 | `63df29361568` | Capital Market Authority / Services / My Fvourites / Most Used Services / Access to legislations / Legislation |
| `AE-sca-laws` | SCA | `BLOCKED` | 23 / POOR | high | high | 3146 | `63df29361568` | Capital Market Authority / Services / My Fvourites / Most Used Services / Access to legislations / Legislation |
| `AE-sca-legislation` | SCA | `BLOCKED` | 23 / POOR | high | high | 3146 | `63df29361568` | Capital Market Authority / Services / My Fvourites / Most Used Services / Access to legislations / Legislation |
| `AE-sca-regulations` | SCA | `BLOCKED` | 23 / POOR | high | high | 3146 | `63df29361568` | Capital Market Authority / Services / My Fvourites / Most Used Services / Access to legislations / Legislation |
| `AE-vara-aml-cft-rulebook` | VARA | `NAV_SHELL_ONLY` | 0 / POOR | high | high | 85 | `82dfed9854d5` | Not found / Page not found / Sorry 😔, we couldn’t find what you were looking for. / Go home |
| `AE-vara-company-rulebook` | VARA | `NAV_SHELL_ONLY` | 0 / POOR | high | high | 85 | `82dfed9854d5` | Not found / Page not found / Sorry 😔, we couldn’t find what you were looking for. / Go home |
| `AE-vara-enforcement` | VARA | `NAV_SHELL_ONLY` | 0 / POOR | high | high | 4506 | `7e5ab9c8d356` | Enforcement - VARA / ENFORCEMENT / Ensuring swift action to tackle regulatory breaches in the virtual assets s |
| `AE-vara-homepage` | VARA | `NAV_SHELL_ONLY` | 0 / POOR | high | high | 2676 | `1044425c60cb` | Virtual Assets Regulatory Authority (VARA) - VARA / A SINGULAR APPROACH TO REGULATION / Empowering innovation  |
| `AE-vara-public-register` | VARA | `NAV_SHELL_ONLY` | 0 / POOR | high | high | 85 | `82dfed9854d5` | Not found / Page not found / Sorry 😔, we couldn’t find what you were looking for. / Go home |
| `AE-vara-regulatory-framework` | VARA | `NAV_SHELL_ONLY` | 0 / POOR | high | high | 85 | `82dfed9854d5` | Not found / Page not found / Sorry 😔, we couldn’t find what you were looking for. / Go home |
| `AE-vara-rulebooks-overview` | VARA | `NAV_SHELL_ONLY` | 0 / POOR | high | high | 85 | `82dfed9854d5` | Not found / Page not found / Sorry 😔, we couldn’t find what you were looking for. / Go home |
| `AE-cbuae-aml-cft` | CBUAE | `BLOCKED` | 0 / POOR | high | high | 3789 | `3fe8475d7535` | Error404 / Search our website / Advanced Search / {{history.Search}} / Notifications / Monday 07 April 2025 /  |
| `AE-cbuae-consultations` | CBUAE | `BLOCKED` | 0 / POOR | high | high | 3789 | `3fe8475d7535` | Error404 / Search our website / Advanced Search / {{history.Search}} / Notifications / Monday 07 April 2025 /  |
| `AE-cbuae-homepage` | CBUAE | `BLOCKED` | 19 / POOR | high | high | 13940 | `e6f417163198` | مصرف الإمارات العربية المتحدة المركزي | الصفحة الرئيسية / الإشعارات / الإثنين 07 أبريل 2025 / المصرف المركزي ي |
| `AE-cbuae-licensing` | CBUAE | `BLOCKED` | 21 / POOR | high | high | 40659 | `fd150e8828a0` | CBUAE | Licensing / Notifications / Monday 07 April 2025 / CBUAE Issues its 2024 Annual Report / Press Release |
| `AE-cbuae-payment-systems` | CBUAE | `BLOCKED` | 0 / POOR | high | high | 3789 | `3fe8475d7535` | Error404 / Search our website / Advanced Search / {{history.Search}} / Notifications / Monday 07 April 2025 /  |
| `AE-cbuae-publications` | CBUAE | `BLOCKED` | 0 / POOR | high | high | 6921 | `e6f2dd27f970` | CBUAE | Publications / Notifications / Monday 07 April 2025 / CBUAE Issues its 2024 Annual Report / Press Rele |
| `AE-cbuae-regulations` | CBUAE | `BLOCKED` | 22 / POOR | high | high | 14484 | `51c99b6ffc25` | CBUAE | Central Bank of the UAE / Notifications / Monday 07 April 2025 / CBUAE Issues its 2024 Annual Report / |
| `AE-uaefiu-goaml-public` | UAE FIU | `BLOCKED` | 0 / POOR | high | high | 3646 | `8a5028889802` | Error404 / Required / Search by / Keywords / Sentence / Your search returned / Search Results / Order by / Rel |
| `AE-uaefiu-laws-regulations` | UAE FIU | `BLOCKED` | 0 / POOR | high | high | 3646 | `c75485082ca8` | Error404 / Required / Search by / Keywords / Sentence / Your search returned / Search Results / Order by / Rel |
| `AE-uaefiu-publications` | UAE FIU | `BLOCKED` | 0 / POOR | high | high | 5742 | `93ebfa4aafb3` | FIU | Publications / Required / Search by / Keywords / Sentence / Your search returned / Search Results / Orde |
| `AE-eocn-homepage` | Executive Office for Control and Non-Proliferation | `BLOCKED` | 0 / POOR | high | high | 2085 | `c857d7c0d276` | الصفحة الرئيسية | المكتب التنفيذي للرقابة وحظر الانتشار / الأخبار / المزيد / اختتام أعمال الاجتماع العام الـ42 |
| `AE-moec-aml` | Ministry of Economy | `BLOCKED` | 0 / POOR | high | high | 4665 | `a0ffba537dad` | الصفحة الرئيسية | وزارة الاقتصاد والسياحة - الإمارات العربية المتحدة / الصفحة الرئيسية / MOE Popular Search Ke |
| `AE-mof-homepage` | Ministry of Finance | `BLOCKED` | 0 / POOR | high | high | 6634 | `e81e75a73f89` | الرئيسية | وزارة المالية - الإمارات العربية المتحدة / تخطى إلى المحتوى الرئيسي / استمع / Close modal / اللغات  |
| `AE-uae-legislation-portal` | UAE Legislation | `NAV_SHELL_ONLY` | 0 / POOR | high | high | 369 | `34cd3144a851` | Один момент… uaelegislation.gov.ae / Выполнение проверки безопасности / Этот веб-сайт использует сервис безопа |
| `AE-dfsa-aml-mlro-notices` | DFSA | `CONFIRMED_ACCESSIBLE` | 59 / LIMITED | medium | medium | 3175 | `2585e5910649` | Amendments to the DFSA AML and Glossary Modules and the AML FAQ document / Open / Updates to Federal Anti-Mone |
| `AE-dfsa-consultation-papers` | DFSA | `BLOCKED` | 0 / POOR | high | high | 2578 | `4a0f9e832c5b` | Page Not Found | DFSA | THE INDEPENDENT REGULATOR OF FINANCIAL SERVICES / About us / Go Back / Who we are / Th |
| `AE-dfsa-enforcement-regulatory-actions` | DFSA | `BLOCKED` | 0 / POOR | high | high | 3075 | `d25ee1f7e667` | Decision Notices & Regulatory Actions | DFSA / About us / Go Back / Who we are / The DFSA / Governance / How w |
| `AE-dfsa-rulebook-official` | DFSA | `BLOCKED` | 0 / POOR | high | high | 5447 | `e40ad4fc1f5b` | Laws and Rules | DFSA | THE INDEPENDENT REGULATOR OF FINANCIAL SERVICES / About us / Go Back / Who we are / Th |
| `AE-dfsa-rulebook-thomsonreuters` | DFSA | `CONFIRMED_ACCESSIBLE` | 59 / LIMITED | medium | medium | 10634 | `352dcfd27d1b` | Rulebook Modules / Anti-Money Laundering, Counter-Terrorist Financing and Sanctions Module (AML) [VER30/04-26] |
| `AE-difc-laws-regulations` | DIFC | `BLOCKED` | 29 / POOR | high | high | 4123 | `fa6e64c30cc0` | Comprehensive Laws and Regulations in Dubai | DIFC / Laws & Regulations. / Laws and Regulations in Dubai Inter |

## 4. Readiness-Supported Candidates

These candidates passed no-save accessibility well enough to be considered for the next validation step. They are not evidence-confirmed and not monitoring-ready.

| Candidate | Why it is a next-step candidate | Conditions before activation |
|---|---|---|
| `AE-dfsa-aml-mlro-notices` | `CONFIRMED_ACCESSIBLE`, quality 59, non-nav-shell, unique hash, meaningful preview. | Save proof, complete baseline runs, add source-specific noise filters, and keep evidence level clear. |
| `AE-dfsa-rulebook-thomsonreuters` | `CONFIRMED_ACCESSIBLE`, quality 59, non-nav-shell, unique hash, meaningful preview. | Save proof, complete baseline runs, add source-specific noise filters, and keep evidence level clear. |


## 5. Remediation Candidates

Most top-40 candidates remain remediation because the no-save output was blocked, navigation-shell, page-not-found shell, access-warning, duplicate/chrome-heavy, or source-label mismatched.

High-priority remediation groups:

- ADGM/FSRA: several candidate URLs resolved to 404/nav shells; enforcement parsed but did not clearly match the expected enforcement source model.
- SCA: selected pages returned service-directory style text with identical hash patterns and login/access warnings.
- VARA: several rulebook/register URLs returned not-found shells; enforcement/homepage parsed but were still nav-shell under strict quality scoring.
- CBUAE: selected pages returned access-warning/chrome-heavy or 404-like outputs, with high health risk.
- UAE FIU: selected pages returned blocked/search/chrome-heavy output.
- Federal AML/MoF/legislation: useful official candidates, but no-save output was blocked/chrome-heavy or security-check content.

## 6. Rejected Candidates

No top-40 candidate was permanently rejected in this run. Rejection should happen in a follow-up source-model cleanup only after official URL alternatives are found.

The candidate file still separately tracks six rejected no-garbage examples from the prior source-pack strategy task.

## 7. Alert Fatigue Risk Summary

- Low noise risk: {noise.get('low',0)}.
- Medium noise risk: {noise.get('medium',0)}.
- High noise risk: {noise.get('high',0)}.

The two accepted no-save candidates still have medium noise risk because they are listing/module pages and require source-specific diff filters.

## 8. Source Health Risk Summary

- Low source-health risk: {health.get('low',0)}.
- Medium source-health risk: {health.get('medium',0)}.
- High source-health risk: {health.get('high',0)}.

The current top-40 pack is not operationally safe as a default active pack without selectors/adapters and health-state surfacing.

## 9. Recommended Default Packs

Demo pack now:

- Use existing proof-backed sample brief.
- Use `AE-dfsa-rulebook-thomsonreuters` and `AE-dfsa-aml-mlro-notices` only as no-save/readiness demo candidates, not evidence-confirmed sources.
- Show remediation examples from SCA/VARA/ADGM to prove the product is honest about failures.

Founding Pilot pack:

- Keep to the existing 13 enabled sources until customer-specific source readiness review.
- Add DFSA candidate migration only after saved proof/baseline.

UAE Monitor pack:

- Not ready for 40+ source marketing.
- Requires source-specific remediation across ADGM/FSRA, SCA, VARA, CBUAE, FIU, and federal portals.

Consultant pack:

- Candidate map is useful for consulting discovery, but not active monitoring coverage yet.

## 10. Customer-Facing Source Truth

Allowed now:

“13 enabled UAE sources; 9 readiness-supported; 4 under extraction remediation.”

“40 UAE source candidates are undergoing no-save readiness validation.”

“Two DFSA candidates passed no-save accessibility checks and still require saved evidence and baseline runs.”

## 11. What We Cannot Claim

Do not say:

- “40+ monitored sources.”
- “60 validated sources.”
- “DFSA ready.”
- “ADGM/SCA ready.”
- “Comprehensive UAE monitor.”
- “Any website can be parsed.”
- “Guaranteed compliance.”
- “Legal advice.”

## 12. Next Exact Task

Run selector/URL remediation for the highest-value failed groups: ADGM/FSRA official rulebook/notices URLs and SCA legislation/decisions pages, using browser DOM investigation before any further Source Lab batch.
