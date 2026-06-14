# UAE Regulatory Source Taxonomy

## 1. Purpose

This taxonomy defines the default source universe StatuteProof should move toward for a professional UAE compliance monitoring baseline. It is designed for MLROs, CCOs, compliance managers, legal counsel, founders at regulated fintechs/VASPs, and compliance consultants.

Target range: **40-60 official or officially linked endpoints** after validation.

The goal is not to force 60. A 40-source validated, non-garbage pack is better than a 60-source inflated pack.

## 2. Category A: VARA / Dubai Virtual Assets

Target: 8-12 endpoints.

Why MLRO cares:

- VARA is the central regulator for Dubai virtual assets.
- VASP obligations often hinge on rulebooks, AML/CFT guidance, enforcement notices, public registers, administrative orders, and consultations.

Minimum viable endpoints:

- VARA homepage/news anchor.
- VARA regulatory framework/rulebook page.
- VARA rulebook PDFs or grouped rulebook pages.
- VARA enforcement notices.
- VARA AML/CFT guidance.

Expansion endpoints:

- Company rulebook.
- Activity-specific rulebooks.
- Administrative orders.
- Public register / licensed entity registry if public and monitorable.
- Consultation/timeline/update pages.
- Guidance/publications pages.

Not useful:

- Generic marketing pages.
- Social media.
- Duplicated PDF links that are already covered by a higher-quality listing source.

Priority: P0 for VASP/crypto buyers.

## 3. Category B: UAE FIU / AML Reporting

Target: 4-8 endpoints.

Why MLRO cares:

- UAE FIU/goAML guidance, circulars, typologies, notices, and AML publications are directly relevant to MLRO operations, suspicious transaction reporting, and AML control updates.

Minimum viable endpoints:

- FIU publications/circulars listing.
- FIU guidance/typologies if public.
- goAML public guidance/documentation if officially published.
- AML/CFT notice pages.

Expansion endpoints:

- Annual reports.
- sector-specific typologies.
- STR/SAR guidance.
- training/awareness notices if public and regulator-owned.

Not useful:

- Homepage-only monitoring when publications/circulars pages exist.
- Login-only goAML portals.

Priority: P0 for MLROs.

## 4. Category C: CBUAE / Central Bank

Target: 8-12 endpoints.

Why MLRO cares:

- CBUAE controls banking, payment, stored value, retail payment services, AML/CFT, licensing, and many fintech-relevant rule/guidance surfaces.

Minimum viable endpoints:

- CBUAE regulations.
- CBUAE circulars/notices where public.
- AML/CFT regulatory pages/guidance.
- payments / stored value / retail payment services regulations.
- consultations/publications.

Expansion endpoints:

- licensing/public registers if useful.
- consumer protection regulations.
- sanctions/AML guidance.
- rulebook pages if public.

Not useful:

- Homepage-only rate/statistical pages unless they drive evidence demos.
- Counter widgets/rating changes as alert-worthy content.

Priority: P0 for banks, payment firms, fintechs, and many VASPs.

## 5. Category D: DFSA / DIFC

Target: 8-12 endpoints.

Why MLRO cares:

- DIFC-authorised firms need DFSA rulebook, financial crime, notices, enforcement, consultation papers, and DIFC legal/regulatory updates.

Minimum viable endpoints:

- DFSA rulebook modules.
- DFSA AML/financial crime prevention notices and MLRO letters.
- DFSA enforcement/regulatory actions.
- DFSA consultation papers.
- DIFC laws/regulations.

Expansion endpoints:

- DFSA public register.
- DFSA rulebook module pages by module.
- DFSA thematic pages, if official and meaningful.
- DIFC Data Protection pages where compliance-relevant.

Not useful:

- Current 404 DFSA URLs.
- Navigation-only shells.
- Ambiguous `AE-dfsa-notices` label without a defined notice class.

Priority: P0/P1 depending on customer licence.

## 6. Category E: ADGM / FSRA

Target: 8-12 endpoints.

Why MLRO cares:

- ADGM/FSRA firms need FSRA rulebook, guidance, consultation, notices, enforcement, public register, AML/financial crime, and ADGM regulations.

Minimum viable endpoints:

- FSRA rulebook.
- FSRA guidance/publications.
- FSRA notices/circulars.
- ADGM regulations/laws.
- public register if public and useful.

Expansion endpoints:

- enforcement/decisions.
- consultation papers.
- AML/financial crime pages.
- data protection if relevant.

Not useful:

- Broad ADGM landing pages if better FSRA subpages exist.
- Pages requiring external access that the parser cannot safely reach.

Priority: P0/P1 depending on customer licence.

## 7. Category F: SCA / UAE Securities And Commodities Authority

Target: 5-8 endpoints.

Why MLRO cares:

- SCA is relevant to securities, capital markets, investment firms, and UAE federal financial regulation. It must not be confused with Saudi CMA.

Minimum viable endpoints:

- SCA legislation/regulations.
- SCA board decisions.
- SCA circulars.
- SCA consultations/publications where public.

Expansion endpoints:

- virtual assets pages if officially public.
- AML/CFT pages if public.
- licensing/register pages if useful.

Not useful:

- Saudi CMA.
- SCA homepage-only monitoring if subpages exist.
- Navigation-only pages unless a selector/adapter solves them.

Priority: P1.

## 8. Category G: Federal / AML / Sanctions / Corporate Compliance

Target: 6-10 endpoints.

Why MLRO cares:

- Federal AML, sanctions/TFS, corporate compliance, tax, and legislation sources shape MLRO obligations and customer-risk controls.

Minimum viable endpoints:

- Executive Office for Control and Non-Proliferation / sanctions/TFS pages if public.
- Ministry of Economy AML pages/notices.
- Ministry of Finance relevant publications.
- FTA guides/public clarifications relevant to regulated firms.
- UAE legislation portal.

Expansion endpoints:

- Official Gazette / legislation database if accessible.
- business register/company registry updates where compliance-relevant.
- sectoral compliance pages.

Not useful:

- Generic government service pages.
- private registries or login-only portals.
- broad tax pages not relevant to financial compliance.

Priority: P1/P2 depending on customer profile.

## 9. Category H: Other Strongly Relevant Sources

Potential sources:

- UAE Data Office / data protection guidance.
- DIFC Data Protection.
- ADGM Data Protection.
- TDRA only if telecom/data/payment relevance is clear.

Not useful by default:

- customs/environment/municipal pages unless a customer profile makes them relevant.
- general news portals.
- law firm explainers.

Priority: P2 unless a specific ICP requires it.

## 10. Initial Target Shape

| Group | P0/P1 target candidate count | Expected validated target after testing |
|---|---:|---:|
| VARA | 10 | 5-8 |
| UAE FIU | 6 | 3-5 |
| CBUAE | 10 | 6-8 |
| DFSA / DIFC | 12 | 5-8 after remediation |
| ADGM / FSRA | 10 | 5-8 after remediation |
| SCA | 7 | 3-5 |
| Federal / AML / sanctions / tax / legislation | 10 | 5-8 |
| Other compliance sources | 5 | 1-3 |

This yields roughly 60-70 researched candidates, with a realistic first professional pack of 40-60 after no-save validation and remediation work.
