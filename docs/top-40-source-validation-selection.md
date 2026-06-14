# Top-40 Source Validation Selection

## 1. Selection Verdict

Selected count: **40**.

Selection source:

`product/regradar/config/uae_source_candidates.json`

Selection rule:

- Use candidates marked `top_40_candidate: true`.
- Start validation with ADGM/FSRA and SCA.
- Keep current customer-facing truth unchanged: **13 enabled / 9 readiness-supported / 4 remediation**.

## 2. Selected 40 Candidates

| # | Candidate ID | Regulator / group | Priority | Parsing risk | MLRO / compliance relevance | Why selected |
|---:|---|---|---|---|---|---|
| 1 | `AE-adgm-fsra-homepage` | ADGM/FSRA | P1 | HTML/JS | ADGM firm, MLRO, CCO | Existing anchor; validates baseline ADGM/FSRA access behavior. |
| 2 | `AE-adgm-legal-framework-rules` | ADGM | P1 | HTML/listing | ADGM firm, legal counsel | ADGM rules/regulations are core regulated-firm obligations. |
| 3 | `AE-adgm-legal-framework-legislation` | ADGM | P1 | HTML/listing | ADGM firm, legal counsel | ADGM legislation is a core legal source for ADGM firms. |
| 4 | `AE-adgm-fsra-rulebooks` | ADGM/FSRA | P0 | HTML/listing | MLRO, CCO, ADGM firm | FSRA rulebooks are high-value compliance obligations. |
| 5 | `AE-adgm-fsra-guidance-policy` | ADGM/FSRA | P0 | HTML/listing | MLRO, CCO, ADGM firm | Guidance/policy statements can change operational compliance expectations. |
| 6 | `AE-adgm-fsra-notices` | ADGM/FSRA | P0 | HTML/listing | MLRO, CCO, ADGM firm | Notices are high-signal monitoring candidates. |
| 7 | `AE-adgm-fsra-consultations` | ADGM/FSRA | P1 | HTML/listing | CCO, legal counsel | Consultations give early-warning signals. |
| 8 | `AE-adgm-fsra-enforcement` | ADGM/FSRA | P1 | HTML/listing | MLRO, CCO, legal counsel | Enforcement is high-signal for regulatory expectations. |
| 9 | `AE-sca-legislation` | SCA | P1 | HTML/navigation | CCO, capital markets | UAE SCA legislation is core federal securities coverage. |
| 10 | `AE-sca-decisions` | SCA | P1 | HTML/navigation | CCO, capital markets | Board decisions can directly affect regulated market participants. |
| 11 | `AE-sca-laws` | SCA | P1 | HTML/navigation | CCO, legal counsel | Securities laws are high-value, but likely selector-sensitive. |
| 12 | `AE-sca-regulations` | SCA | P1 | HTML/navigation | CCO, capital markets | Regulations are better than homepage monitoring if extractable. |
| 13 | `AE-sca-circulars` | SCA | P1 | HTML/unknown | CCO, compliance manager | Circulars would be high-signal if the URL/source model is correct. |
| 14 | `AE-vara-homepage` | VARA | P1 | JS | VASP, MLRO, CCO | Existing anchor; useful to compare against specific VARA pages. |
| 15 | `AE-vara-enforcement` | VARA | P0 | JS | VASP, MLRO, legal counsel | Enforcement is high-signal and already showed meaningful preview text. |
| 16 | `AE-vara-regulatory-framework` | VARA | P0 | JS/PDF | VASP, legal counsel | Rulebook/framework is core VASP coverage; prior URL risk must be confirmed. |
| 17 | `AE-vara-public-register` | VARA | P1 | JS/table | VASP, compliance manager | Licensing/register changes matter for counterparty and authorization checks. |
| 18 | `AE-vara-rulebooks-overview` | VARA | P0 | JS/PDF/unknown | VASP, legal counsel | Cleaner rulebook source if reachable. |
| 19 | `AE-vara-company-rulebook` | VARA | P0 | JS/PDF/unknown | VASP, CCO | Company rulebook obligations are core VASP control inputs. |
| 20 | `AE-vara-aml-cft-rulebook` | VARA | P0 | JS/PDF/unknown | MLRO, VASP | Direct AML/CFT source if reachable. |
| 21 | `AE-cbuae-homepage` | CBUAE | P1 | WAF/HTML | MLRO, CCO, payment firm | Existing anchor; validates central bank access behavior. |
| 22 | `AE-cbuae-regulations` | CBUAE | P0 | WAF/listing | MLRO, CCO, fintech | Existing key source; needs strict noise/access review. |
| 23 | `AE-cbuae-publications` | CBUAE | P1 | WAF/listing | CCO, consultant | Publications may include guidance, reports, and policy context. |
| 24 | `AE-cbuae-payment-systems` | CBUAE | P1 | WAF/HTML | Payment firm, fintech | Payment systems/stored-value relevance. |
| 25 | `AE-cbuae-aml-cft` | CBUAE | P0 | WAF/HTML | MLRO, bank, fintech | Direct AML/CFT relevance. |
| 26 | `AE-cbuae-licensing` | CBUAE | P1 | WAF/HTML | CCO, fintech | Licensing/perimeter changes affect regulated firms. |
| 27 | `AE-cbuae-consultations` | CBUAE | P1 | WAF/listing | CCO, legal counsel | Consultations are early-warning regulatory signals. |
| 28 | `AE-uaefiu-publications` | UAE FIU | P0 | HTML/listing | MLRO | Direct AML publication/circular surface; previous no-save showed nav/access risk. |
| 29 | `AE-uaefiu-goaml-public` | UAE FIU | P0 | HTML/unknown | MLRO | Public goAML guidance is direct MLRO workflow relevance. |
| 30 | `AE-uaefiu-laws-regulations` | UAE FIU | P1 | HTML/unknown | MLRO, legal counsel | FIU-linked AML legal references are useful if public. |
| 31 | `AE-eocn-homepage` | EOCN | P0 | HTML/unknown | MLRO, sanctions | Sanctions/TFS is core AML screening relevance. |
| 32 | `AE-moec-aml` | Ministry of Economy | P1 | HTML/unknown | MLRO, DNFBP, consultant | Federal AML relevance for DNFBP/compliance context. |
| 33 | `AE-mof-homepage` | Ministry of Finance | P1 | HTML | CCO, tax, consultant | Existing readiness-supported federal finance anchor. |
| 34 | `AE-uae-legislation-portal` | UAE Legislation | P1 | WAF/search | Legal counsel, CCO | Federal legislation source with access/noise caveats. |
| 35 | `AE-dfsa-rulebook-official` | DFSA | P0 | Cloudflare/JS | DIFC firm, MLRO | Official DFSA laws/rules source, but still remediation risk. |
| 36 | `AE-dfsa-rulebook-thomsonreuters` | DFSA | P0 | HTML/officially linked | DIFC firm, MLRO | Prior no-save check produced meaningful rulebook content. |
| 37 | `AE-dfsa-aml-mlro-notices` | DFSA | P0 | JS/selector | MLRO, DIFC firm | Prior no-save check produced meaningful notice content. |
| 38 | `AE-dfsa-enforcement-regulatory-actions` | DFSA | P0 | JS/selector | MLRO, CCO | High-signal enforcement source if selector works. |
| 39 | `AE-dfsa-consultation-papers` | DFSA | P1 | Cloudflare/JS | CCO, legal counsel | Early-warning source for DIFC/DFSA regulatory change. |
| 40 | `AE-difc-laws-regulations` | DIFC | P1 | HTML/selector | DIFC firm, legal counsel | Existing remediation source; useful if hold is resolved. |

## 3. Excluded Candidates

Excluded from the top-40 no-save sprint:

- `AE-vara-news`: official but lower-signal news/listing source.
- `AE-cbuae-news`: lower-signal official news.
- `AE-cbuae-consumer-protection`: useful, but not core MLRO first pass.
- `AE-cbuae-open-data`: data/context source, higher noise risk.
- `AE-uaefiu-homepage`: current homepage is shallow/remediation.
- `AE-uaefiu-awareness`: lower priority than publications/goAML/legal references.
- `AE-dfsa-public-register`: useful but search/table adapter risk; defer.
- `AE-dfsa-publications`: broad index; use specific publication classes first.
- `AE-dfsa-aml-ctf-sanctions`: broad page; specific AML/MLRO notices selected instead.
- `AE-difc-legal-database`: search/listing complexity; defer.
- `AE-difc-consultation-papers`: lower MLRO priority than DFSA consultations.
- `AE-difc-data-protection`: useful for privacy scope, not default MLRO pack.
- `AE-adgm-fsra-public-register`: search/table complexity; defer.
- `AE-adgm-data-protection`: privacy scope; consultant/enterprise later.
- `AE-sca-homepage`: navigation-only risk; SCA subpages selected instead.
- `AE-sca-news`: lower-signal news source.
- `AE-federal-tax-authority-homepage`: broad tax homepage, current external access risk.
- `AE-fta-vat-public-clarifications`: consultant/tax expansion later.
- `AE-fta-corporate-tax-guides`: consultant/tax expansion later.
- `AE-uae-elaws-moj`: external access/search risk; defer.

## 4. Selection Risk Notes

- ADGM/FSRA candidates may be lower maintenance if pages are static listings, but exact URLs must be proven.
- SCA candidates are high-value but likely selector-sensitive/navigation-heavy.
- VARA rulebook candidates may be URL/JS/PDF sensitive.
- CBUAE candidates may trigger WAF/access warnings and page-chrome noise.
- UAE FIU candidates are direct MLRO value but previous publications test showed nav/access warnings.
- DFSA candidates have two promising no-save results, but DFSA still cannot leave remediation without saved evidence/baseline.
