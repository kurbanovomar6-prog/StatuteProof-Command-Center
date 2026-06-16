# VARA Official Source Research Log

Date: 2026-06-16

All researched sources below are public, unauthenticated, official VARA URLs on `rulebooks.vara.ae` or `www.vara.ae`.

| Candidate | Official URL | Type | Why official/public | MLRO/VASP relevance | Strategy | Decision |
| --- | --- | --- | --- | --- | --- | --- |
| VARA rulebook portal | `https://rulebooks.vara.ae/` | official rulebook portal | VARA rulebook subdomain. Public. | High: official rulebook corpus. | Use as source discovery anchor only. | Research anchor. |
| Company Rulebook | `https://rulebooks.vara.ae/rulebook/company-rulebook` | rulebook page + PDFs | Public official VARA rulebook page. | High: governance, board, senior management, fit and proper. | Page no-save and direct current PDF. | Page passed no-save; direct PDF held by quality gate. |
| Compliance and Risk Management Rulebook | `https://rulebooks.vara.ae/rulebook/compliance-and-risk-management-rulebook` | rulebook page + PDF | Public official VARA rulebook page. | Critical: compliance, risk management, AML/CFT, reporting. | Direct current PDF. | Activated. |
| Technology and Information Rulebook | `https://rulebooks.vara.ae/rulebook/technology-and-information-rulebook` | rulebook page + PDF | Public official VARA rulebook page. | High: technology, security, information controls. | Direct current PDF. | Activated. |
| Market Conduct Rulebook | `https://rulebooks.vara.ae/rulebook/market-conduct-rulebook` | rulebook page + PDF | Public official VARA rulebook page. | High but direct PDF quality score below strict gate. | Hold until quality/extraction scoring improves. | Held. |
| Virtual Asset Issuance Rulebook | `https://rulebooks.vara.ae/rulebook/virtual-asset-issuance-rulebook` | rulebook page + PDF | Public official VARA rulebook page. | High: issuance requirements. | Direct current PDF. | Activated. |
| Broker-Dealer Services Rulebook | `https://rulebooks.vara.ae/rulebook/broker-dealer-services-rulebook` | rulebook page + PDF | Public official VARA rulebook page. | High: activity-specific VASP obligations. | Direct current PDF. | Activated. |
| Custody Services Rulebook | `https://rulebooks.vara.ae/rulebook/custody-services-rulebook` | rulebook page + PDF | Public official VARA rulebook page. | High but direct PDF quality score below strict gate. | Hold until quality/extraction scoring improves. | Held. |
| Exchange Services Rulebook | `https://rulebooks.vara.ae/rulebook/exchange-services-rulebook` | rulebook page + PDF | Public official VARA rulebook page. | High but direct PDF quality score below strict gate. | Hold until quality/extraction scoring improves. | Held. |
| Lending and Borrowing Services Rulebook | `https://rulebooks.vara.ae/rulebook/lending-and-borrowing-services-rulebook` | rulebook page + PDF | Public official VARA rulebook page. | High: activity-specific VASP obligations. | Direct current PDF. | Activated. |
| Virtual Assets Regulations 2023 | `https://rulebooks.vara.ae/rulebook/virtual-assets-and-related-activities-regulations-2023` | regulations page + PDF | Public official VARA rulebook page. | Critical: top-level VARA framework. | Direct current PDF. | Activated. |

## Rejected / Held

- `www.vara.ae/en/regulatory-framework/...` paths remain held because they previously produced stale/nav-shell/domain-stop failures.
- Public register/news pages were not used for this sprint because the goal was direct rulebook/PDF regulatory depth.
- Company, custody, exchange, and market-conduct direct PDFs were accessible but not activated because strict quality gates returned 58/59 or `can_save_evidence=false`.
