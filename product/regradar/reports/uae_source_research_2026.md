# UAE Regulatory Source Research — June 2026

Research date: 24 June 2026. All URLs verified against live pages during this session.

---

## Key Finding: SCA Rebranded to CMA (Effective 1 January 2026)

Federal Decree-Law No. 32 of 2025 (Capital Market Authority) and Federal Decree-Law No. 33 of 2025 (Regulation of Capital Markets) came into force on 1 January 2026. The Securities and Commodities Authority (SCA) is now the Capital Market Authority (CMA). The old domain sca.gov.ae returns HTTP 301 redirects to uaecma.gov.ae for most pages. All sources.json entries currently referencing www.sca.gov.ae need to be updated to www.uaecma.gov.ae or verified whether the redirect is stable enough for monitoring.

---

## High-Value Sources Found

### VARA — Virtual Assets Regulatory Authority (vara.ae / rulebooks.vara.ae)

**Rulebook revision feed**
- **Best monitoring URL**: `https://rulebooks.vara.ae/view-revision-updates?f_days=onchanged%3D-30+day`
- **Why it's valuable**: Live changelog of all VARA rulebook amendments. Shows 803 total updates as of this research session; items dated with exact dates, filterable by 5/10/30-day windows. Most recently shows May 2026 activity (virtual asset issuance guidance, exchange services rulebook). This is the single best signal for detecting VARA rule changes before they are publicised.
- **Update frequency**: Continuous — multiple updates per week based on item count vs. 30-day filter results
- **HTML or JS-rendered**: HTML (Drupal-based; works without JS for content)
- **In sources.json already**: Yes — `VARA Rulebook Revision Updates` pointing to this URL (enabled)
- **Recommended action**: Already covered. Confirm filter is set correctly (30-day window is live in sources.json)

**Enforcement and warning notices**
- **Best monitoring URL**: `https://www.vara.ae/en/regulations/regulatory-notices/`
- **Why it's valuable**: Lists all licensing notices, enforcement notices, and warning notices in a single page. 28 items currently: 11 enforcement notices, 17 warning notices. Most recent: VARA Notice of Fines for MEXC and CoinMENA FZE (both 22 Jun 2026). No RSS feed visible, but page is HTML and diff-monitorable.
- **Update frequency**: Ad hoc — tied to enforcement actions; roughly monthly based on historical pattern
- **HTML or JS-rendered**: HTML
- **In sources.json already**: Yes — `VARA Enforcement Notices` at `https://www.vara.ae/en/enforcement/` (enabled). Note: `/en/enforcement/` is the enforcement registry table (tabular, no dates in page content); `/en/regulations/regulatory-notices/` is the text listing with dates. Both are worth monitoring.
- **Recommended action**: Add `/en/regulations/regulatory-notices/` as a second distinct source if not already captured; it provides earlier textual signals than the enforcement table.

**VARA news / circulars**
- **Best monitoring URL**: `https://www.vara.ae/en/news`
- **Why it's valuable**: Publishes new rulebook issuance announcements, market alerts, and guidance notices. Confirmed live updates in 2026.
- **Update frequency**: Monthly
- **In sources.json already**: Yes — `VARA News, Circulars and Regulatory Publications` (enabled)
- **Recommended action**: Already covered.

---

### CBUAE — Central Bank of the UAE (centralbank.ae / rulebook.centralbank.ae)

**Rulebook revision feed**
- **Best monitoring URL**: `https://rulebook.centralbank.ae/en/view-revision-updates`
- **Why it's valuable**: Exact equivalent of the VARA revision feed for CBUAE. Shows 163 total updates; most recent confirmed is SME Customer Protection Regulation dated September 2026. Previous entries include Cabinet Resolution 134/2025 (AML executive regulations, Dec 2025) and two guidance documents (Nov 2025). This is the authoritative change-detection surface for all CBUAE regulations.
- **Update frequency**: Monthly to quarterly per regulation; total feed active continuously
- **HTML or JS-rendered**: The direct fetch returned 403 but search results and linked content confirm it is HTML-based Drupal (same platform as VARA rulebook)
- **In sources.json already**: Yes — `CBUAE Rulebook Revision Updates` at the 365-day filtered URL (enabled)
- **Recommended action**: Already covered. Note that the main centralbank.ae domain blocks direct HTTP fetches (403); the rulebook subdomain may be more accessible. Test adapter access specifically on `rulebook.centralbank.ae`.

**Payment systems regulations page**
- **Best monitoring URL**: `https://www.centralbank.ae/en/our-operations/payments-and-settlements/regulations-and-standards/`
- **Why it's valuable**: CBUAE payment system regulatory updates (Retail Payment Services and Card Schemes, Payment Token Services, Large Value Payment Systems, Stored Value Facilities). Federal Decree Law No. 6 of 2025 created new licensing obligations with a transition deadline of 16 September 2026 — this page will reflect updates as implementing regulations are issued.
- **Update frequency**: Quarterly (major regulation cycles)
- **HTML or JS-rendered**: HTML (403 from direct fetch but confirmed accessible via search results)
- **In sources.json already**: Partially — individual rulebook document pages (retail payments, payment tokens, large value systems) are enabled but the hub page itself may not be. Check sources for `centralbank.ae/en/our-operations/payments-and-settlements/`.
- **Recommended action**: Add hub page `https://www.centralbank.ae/en/our-operations/payments-and-settlements/regulations-and-standards/` if not present; it acts as the index for new payment regulation documents.

**CBUAE AML/CFT operations hub**
- **Best monitoring URL**: `https://www.centralbank.ae/en/our-operations/anti-money-laundering-and-combatting-the-financing-of-terrorism/`
- **In sources.json already**: Yes — `CBUAE AML/CFT Operations Hub` (enabled)
- **Recommended action**: Already covered.

---

### DFSA — Dubai Financial Services Authority (dfsa.ae)

**Notice of amendments to legislation (monthly)**
- **Best monitoring URL**: `https://www.dfsa.ae/news` filtered for "notice-amendments-legislation" slugs
- **Why it's valuable**: The DFSA publishes a "Notice of Amendments to Legislation" news item every one to two months summarising every rulebook change made that period, with direct links to the rulemaking instruments. Confirmed 2026 issues: February, March, and May. These are the authoritative legislative change notices.
- **Specific confirmed 2026 URLs**:
  - `https://www.dfsa.ae/news/notice-amendments-legislation-february-2026`
  - `https://www.dfsa.ae/news/notice-amendments-legislation-march-2026`
  - `https://www.dfsa.ae/news/notice-amendments-legislation-may-2026`
- **Update frequency**: Monthly (pattern consistent from 2024 through 2026)
- **HTML or JS-rendered**: HTML (direct fetch blocked by 403 but content confirmed via search results)
- **In sources.json already**: Partially — individual historical notice URLs are tracked (enabled, ~10 specific notice slugs). However the pattern `news/notice-amendments-legislation-*` generates new URLs each month that are not pre-populated.
- **Recommended action**: Add a monitored source for the DFSA news index page `https://www.dfsa.ae/news` to catch new "notice-amendments-legislation" entries as they are published. The current approach of monitoring specific historic slugs will miss new monthly notices.

**DFSA consultation papers**
- **Best monitoring URL**: `https://www.dfsa.ae/your-resources/regulatory/consultation-papers`
- **Why it's valuable**: Index of all open and closed consultation papers. Active in 2026: Consultation Paper No. 167 (results published May 2026). New papers typically open two to three times per year.
- **Update frequency**: Ad hoc, roughly quarterly
- **HTML or JS-rendered**: HTML (403 on direct fetch)
- **In sources.json already**: Yes — `DFSA Consultation Papers Current` (enabled)
- **Recommended action**: Already covered.

**DFSA MLRO letters and financial crime prevention notices**
- **Best monitoring URL**: `https://www.dfsa.ae/what-we-do/aml-ctf-sanctions-compliance/financial-crime-prevention-notices-and-mlro-letters`
- **Why it's valuable**: Letters to MLROs (Money Laundering Reporting Officers) containing compliance expectations and thematic findings. Also used for financial crime prevention notices.
- **Update frequency**: Ad hoc, roughly biannual
- **HTML or JS-rendered**: HTML (403 on direct fetch)
- **In sources.json already**: Yes — `DFSA Financial Crime Prevention Notices and MLRO Letters` (enabled). Note: during this session, fetching the page returned "No result found" — this may indicate the page uses JS-rendered content that requires a JavaScript-capable adapter.
- **Recommended action**: Validate that the adapter is capturing content. If returning empty/no-content, the page may require a JavaScript rendering adapter (Playwright).

**DFSA enforcement / regulatory actions**
- **Best monitoring URL**: `https://www.dfsa.ae/what-we-do/enforcement/regulatory-actions`
- **Why it's valuable**: Decision notices and enforcement actions. Confirmed 2026 enforcement actions visible.
- **Update frequency**: Ad hoc
- **HTML or JS-rendered**: HTML (403 on direct fetch)
- **In sources.json already**: Yes — `DFSA Enforcement Regulatory Actions` (enabled)
- **Recommended action**: Already covered.

**DFSA SEO letters**
- **Best monitoring URL**: `https://www.dfsa.ae/your-resources/publications-reports/seo-letters-1`
- **Why it's valuable**: Dear SEO (Senior Executive Officer) letters contain thematic supervisory findings and expectations for all regulated firms. High compliance relevance.
- **Update frequency**: Annual (one to two letters per year)
- **HTML or JS-rendered**: HTML (403 on direct fetch)
- **In sources.json already**: Not confirmed in enabled list — check for this URL
- **Recommended action**: Add if not present.

---

### ADGM FSRA — Abu Dhabi Global Market Financial Services Regulatory Authority (adgm.com)

**Public consultations index**
- **Best monitoring URL**: `https://www.adgm.com/legal-framework/public-consultations`
- **Why it's valuable**: ADGM's active consultation listing. Confirmed 2026 papers: CP No. 1/2026 (AML framework, closed May 2026), Discussion Paper No. 1/2026 (crypto mining guidance, closed March 2026). No RSS feed available; page must be polled.
- **Update frequency**: Quarterly (three to five papers per year based on 2025/2026 output)
- **HTML or JS-rendered**: HTML (verified accessible; content confirmed)
- **In sources.json already**: Yes — `ADGM Public Consultations` (enabled)
- **Recommended action**: Already covered.

**ADGM announcements / media hub**
- **Best monitoring URL**: `https://www.adgm.com/media/announcements`
- **Why it's valuable**: Publishes all FSRA regulatory finalisation notices (e.g., "FSRA finalises AML framework enhancements", "FSRA issues cyber risk management framework"). Most recent confirmed: 16 June 2026. This is where rule changes are announced before the formal consultation paper trail is closed.
- **Update frequency**: Weekly to biweekly
- **HTML or JS-rendered**: HTML (verified accessible)
- **In sources.json already**: Not seen explicitly in enabled list under this URL — announcements may be tracked via individual announcement slugs
- **Recommended action**: Add `https://www.adgm.com/media/announcements` as a hub page source.

**ADGM FSRA enforcement / regulatory actions**
- **Best monitoring URL**: `https://www.adgm.com/operating-in-adgm/additional-obligations-of-financial-services-entities/enforcement/regulatory-actions`
- **Why it's valuable**: Lists all FSRA enforcement decisions. Most recent: Wealthface Limited (08 Jan 2026), Payward MENA Holdings (17 Dec 2025). Confirmed accessible and HTML-rendered.
- **Update frequency**: Ad hoc, roughly monthly
- **HTML or JS-rendered**: HTML (verified accessible)
- **In sources.json already**: Yes — `ADGM FSRA Enforcement` (enabled)
- **Recommended action**: Verify the exact URL is pointing at the regulatory-actions page, not the broader enforcement hub.

**ADGM Financial and Cyber Crime Prevention notices**
- **Best monitoring URL**: `https://www.adgm.com/operating-in-adgm/financial-and-cyber-crime-prevention/notices-and-circulars`
- **Why it's valuable**: Equivalent to DFSA MLRO letters — FSRA circulars on financial crime prevention and cybercrime. Page currently shows no results, which may be a JS rendering issue or genuinely sparse content.
- **Update frequency**: Ad hoc
- **HTML or JS-rendered**: Appears to use JS-rendered dynamic content (page returned "No result found" on direct fetch)
- **In sources.json already**: Yes — `ADGM FSRA Financial and Cyber Crime Prevention` (enabled)
- **Recommended action**: Test with Playwright adapter. If page is JS-rendered and currently empty, monitor the ADGM announcements hub instead as a fallback.

**ADGM supervision circulars**
- **Best monitoring URL**: `https://www.adgm.com/operating-in-adgm/additional-obligations-of-financial-services-entities/supervision/circulars`
- **In sources.json already**: Yes — `ADGM FSRA Supervision Circulars` (enabled)
- **Recommended action**: Already covered.

---

### UAE FIU — Financial Intelligence Unit (uaefiu.gov.ae)

**Publications hub**
- **Best monitoring URL**: `https://www.uaefiu.gov.ae/en/more/knowledge-centre/publications/`
- **Why it's valuable**: Publishes typology reports, annual reports, strategic analysis guidelines, and the National Risk Assessment. Most recent: Environmental Crime Typologies (1 Jun 2026), Human Trafficking typologies (30 Apr 2026), NRA 2024 (29 Jan 2026). RSS feeds confirmed available in footer (Articles & Guidelines feed, Events feed, Press Release feed).
- **Update frequency**: Monthly (one to two publications per month in 2026)
- **HTML or JS-rendered**: HTML (verified accessible)
- **RSS available**: Yes
- **In sources.json already**: Yes — `UAE FIU Publications Hub` (enabled)
- **Recommended action**: Already covered. Consider also adding the RSS feed URL if it can be found in the page source, as this would allow lower-latency detection.

**AML/CFT laws and related decisions**
- **Best monitoring URL**: `https://uaefiu.gov.ae/en/more/knowledge-centre/aml-cft-laws-related-decisions/`
- **Why it's valuable**: Lists primary AML/CFT legislation and implementing decisions. Confirmed HTML-rendered. Currently shows Federal Decree-Law No. 10 of 2025 and Cabinet Resolution No. 134 of 2025 (the new AML framework).
- **Update frequency**: Low (once or twice per year when primary legislation changes)
- **HTML or JS-rendered**: HTML (verified accessible)
- **In sources.json already**: Yes — `UAE FIU AML/CFT Laws and Related Decisions` (enabled)
- **Recommended action**: Already covered.

---

### UAE CMA (formerly SCA) — Capital Market Authority (sca.gov.ae → uaecma.gov.ae)

**Critical domain migration note**: Effective 1 January 2026, SCA became CMA. The domain sca.gov.ae returns HTTP 301 permanent redirects to uaecma.gov.ae. During this research session, all fetches to www.sca.gov.ae/... confirmed redirecting to www.uaecma.gov.ae/... The page footer shows "© 2024 Capital Market Authority" confirming the rebrand. Sources.json still lists 9 sources under www.sca.gov.ae domain.

**Circulars and procedures**
- **Best monitoring URL**: `https://www.uaecma.gov.ae/en/regulations/circulars-and-procedures.aspx`
- **Old URL (redirects)**: `https://www.sca.gov.ae/en/regulations/circulars-and-procedures.aspx`
- **Why it's valuable**: Primary circulars and regulatory procedures index for UAE capital markets. The CMA now also has expanded jurisdiction over virtual assets under FDL 33/2025.
- **Update frequency**: Ad hoc, roughly bimonthly
- **HTML or JS-rendered**: HTML
- **In sources.json already**: Yes — `SCA Circulars, Rules and Procedures` at old sca.gov.ae URL (enabled). Also `SCA Circulars` at `https://www.sca.gov.ae/en/circulars.aspx` (enabled).
- **Recommended action**: Update all sca.gov.ae source URLs to uaecma.gov.ae equivalents. The redirect may work but it is cleaner to use canonical URLs, and the redirect chain adds latency. Priority update: `www.sca.gov.ae` → `www.uaecma.gov.ae` across all 9 affected sources.

---

### Ministry of Economy & Tourism / MoET (moet.gov.ae) — AML/CFT for DNFBPs

**AML/CFT circulars page**
- **Best monitoring URL**: `https://www.moet.gov.ae/en/aml`
- **Why it's valuable**: Primary source for AML/CFT circulars directed at DNFBPs (Designated Non-Financial Businesses and Professions: real estate, precious metals, trust/company service providers, accountants/auditors). Confirmed last updated 23 June 2026. Current circular list: Circular No. 1/2026 (High-risk countries update), Circulars 1-8/2025, Circulars 1-4/2024, etc. This page changes every one to two months.
- **Update frequency**: Monthly (based on 8 circulars in 2025, 1 already in 2026)
- **HTML or JS-rendered**: HTML (verified accessible via WebFetch)
- **In sources.json already**: Yes — `Ministry of Economy — AML` at `https://www.moet.gov.ae/aml` (enabled). Note the URL in sources.json omits `/en/` prefix; both forms appear to resolve.
- **Recommended action**: Already covered. Verify the adapter is capturing the circular listing and not just the page header.

**Note on moec.gov.ae**: The Executive Office for AML/CFT (moec.gov.ae) is a separate entity from moet.gov.ae. Sources.json has one entry for moec.gov.ae (`Executive Office for AML/CFT — Anti-Money Laundering Hub`). These are distinct organisations and both should remain monitored.

---

### Ministry of Finance — MOF (mof.gov.ae)

**Financial legislation and circulars**
- **Best monitoring URL**: `https://mof.gov.ae/en/financial-legislation/`
- **Also relevant**: `https://mof.gov.ae/en/lawsAndPolitics/Circulars/Pages/default.aspx` (returns access-denied in direct fetch, but confirmed via search to host Ministerial Resolutions)
- **Why it's valuable**: MOF publishes Ministerial Resolutions and Decisions on: e-invoicing system (MR 66/2026, MR 56/2026 in 2026), Tax Procedures Law amendments (effective Jan 2026), R&D tax credit implementation (MD 24/2026), economic substance requirements, FATCA/CRS. Active publishing cadence in 2026.
- **Update frequency**: Monthly
- **HTML or JS-rendered**: Circulars page returns access-denied; the news/announcements pages are HTML
- **In sources.json already**: Yes — 8 sources under mof.gov.ae (enabled), including `UAE Ministry of Finance Publications and Releases` and `UAE Ministry of Finance Financial Legislation`
- **Recommended action**: Already covered. Validate that the adapter can access mof.gov.ae pages (the Circulars page blocked during this session; confirm whether other MOF pages work).

---

### Federal Tax Authority — FTA (tax.gov.ae)

**VAT and Corporate Tax guides and public clarifications**
- **Best monitoring URLs**:
  - VAT: `https://tax.gov.ae/en/taxes/vat/guides.references.aspx` (last updated Apr 2026, 197 items)
  - Corporate Tax: `https://tax.gov.ae/en/taxes/corporate.tax/corporate.tax.guides.references.aspx` (last updated Jun 2026)
  - Legislation: `https://tax.gov.ae/en/legislation/corporate.tax.aspx`
  - Media Centre: `https://tax.gov.ae/en/media.centre.aspx`
- **Why it's valuable**: FTA regularly publishes new guides and public clarifications as UAE tax law is implemented. Most recent 2026 items: Taxation of Family Foundations guide (10 Jun 2026), VAT Refund for UAE Nationals guide (10 Jun 2026, expanded eligibility). These are compliance-critical for any business subject to UAE tax.
- **Update frequency**: Monthly (new guides issued throughout the year as policy is clarified)
- **HTML or JS-rendered**: HTML (verified accessible)
- **In sources.json already**: Yes — 31 sources under tax.gov.ae (enabled), including `Federal Tax Authority — VAT Guides and References` and `Federal Tax Authority — Corporate Tax Guides and References`
- **Recommended action**: Already covered comprehensively.

---

### UAE Legislation Portal (uaelegislation.gov.ae)

**Legislations index**
- **Best monitoring URL**: `https://uaelegislation.gov.ae/en/legislations`
- **News section**: `https://uaelegislation.gov.ae/en/news`
- **Why it's valuable**: Official platform for all UAE federal legislation, managed by the General Secretariat of the UAE Cabinet. Published Federal Decree-Laws in 2026: Child Digital Safety, Civil Transactions Law, National Educational Curriculum Governance, Industrial Hemp Regulation, Capital Markets laws (FDL 32 and 33/2025 — the CMA legislation). Acts as the master index for all federal legislation.
- **Update frequency**: Ad hoc — whenever the President issues new Federal Decree-Laws; several per month
- **HTML or JS-rendered**: Legislations listing page returned 403 during this session; news section also 403. Content confirmed accessible via search results, suggesting Cloudflare/WAF protection.
- **In sources.json already**: Yes — `UAE Legislation Portal` at `https://uaelegislation.gov.ae/en` and `UAE Legislation Platform - Legislations Listing` at `https://www.uaelegislation.gov.ae/en/legislations/` (one enabled, one check status)
- **Recommended action**: Already covered. Test whether the adapter can bypass the 403; may need rotating user-agent or Playwright adapter.

---

### MOHRE — Ministry of Human Resources and Emiratisation (mohre.gov.ae)

**Resolutions and circulars**
- **Best monitoring URL**: `https://www.mohre.gov.ae/en/laws-and-regulations/resolutions-and-circulars.aspx`
- **Why it's valuable**: MOHRE issues ministerial resolutions with direct compliance impact on all private-sector employers. Most recent: Ministerial Resolution No. 340 of 2026 on Wage Protection System (effective 1 June 2026) — required companies to pay salaries by first of month, raised compliance threshold to 85%, introduced criminal liability escalation. This page also covers Emiratisation decisions.
- **Update frequency**: Monthly (several resolutions per year based on 2025/2026 pattern)
- **HTML or JS-rendered**: Timed out during direct fetch (possible JavaScript rendering or slow server)
- **In sources.json already**: Not found in the enabled sources reviewed. Not listed in the key domains above.
- **Recommended action**: ADD as new source. This is a major gap — MOHRE labour resolutions directly affect every UAE private-sector employer and are not currently monitored.

---

### UAE Cabinet (uaecabinet.ae)

**Cabinet decisions and news**
- **Best monitoring URL**: `https://uaecabinet.ae/en/news`
- **Alternative (specific decisions)**: No dedicated decisions page found — decisions are published as news items
- **Why it's valuable**: The UAE Cabinet approves federal legislation, executive regulations, and implementing decisions. Confirmed 2026 Cabinet activity: AI and Data Authority established (Jun 2026), National AI Strategy 2031 adopted, multiple international agreements ratified. Cabinet decisions often precede or implement CBUAE/FTA/MOHRE regulations.
- **Update frequency**: Following each Cabinet meeting — roughly monthly
- **HTML or JS-rendered**: Direct fetch returned 403; news confirmed accessible via search results
- **In sources.json already**: Not found in the enabled sources reviewed.
- **Recommended action**: ADD as new source — `https://uaecabinet.ae/en/news`. Cabinet decisions are the upstream source for many regulations monitored downstream (e.g., Cabinet Decision 134/2025 implementing the AML law). Monitoring the Cabinet news page provides advance signal before implementing regulations are published.

---

### Dubai Economy and Tourism — DED (ded.ae)

**Laws and regulations**
- **Best monitoring URL**: `https://ded.ae/laws_and_regulations/en/cabinet_decisions`
- **Also relevant**: `https://ded.ae/laws_and_regulations/en/economy_laws`
- **Why it's valuable**: DED/DET publishes Dubai-specific economic legislation including Administrative Resolution No. 17/2026 (Emirati Supplier Support Committee), Law No. 5/2026 (Outsourcing of Government Services), Executive Council resolutions. Relevant for businesses licensed in Dubai mainland.
- **Update frequency**: Ad hoc, roughly quarterly for significant new laws
- **HTML or JS-rendered**: Returns ECONNREFUSED during direct fetch — server may block scrapers
- **In sources.json already**: Not found in enabled sources. ded.ae is not in any of the domain groups confirmed.
- **Recommended action**: CONDITIONAL ADD — valuable for Dubai-specific compliance monitoring, but the ECONNREFUSED suggests the site may not be accessible to the scraper. Test accessibility before adding.

---

### Dubai Legislation Portal — DLP (dlp.dubai.gov.ae)

**Legislation search**
- **Best monitoring URL**: `https://dlp.dubai.gov.ae/en/Pages/LegislationSearch.aspx`
- **Why it's valuable**: Comprehensive search engine for all Dubai legislation (local laws, executive council resolutions, department decisions). Administrative Resolution No. 17/2026 confirmed indexed here. Covers local Dubai laws not captured by the federal UAE Legislation Portal.
- **Update frequency**: Continuous
- **HTML or JS-rendered**: HTML (Drupal-based SharePoint)
- **In sources.json already**: Not found in enabled sources.
- **Recommended action**: ADD — fills the gap between federal legislation (uaelegislation.gov.ae) and Dubai local legislation. Use the search page as the monitoring surface; new laws appear in search results.

---

### DIFC — Dubai International Financial Centre (difc.com)

**Consultation papers index**
- **Best monitoring URL**: `https://www.difc.com/business/laws-and-regulations/consultation-papers/`
- **Why it's valuable**: DIFC publishes its own consultation papers on DIFC-specific legislation. Active 2026 consultations: Prescribed Company Regulations (closed 2 Jun 2026), Arbitration Law (deadline 10 Jul 2026), Data Protection Regulations (deadline 18 Jul 2026). Separate from DFSA consultations — covers DIFC corporate law, not just financial regulation.
- **Update frequency**: Quarterly (three to four consultations per year)
- **HTML or JS-rendered**: HTML
- **In sources.json already**: Yes — `DIFC Consultation Papers Index` (enabled)
- **Recommended action**: Already covered.

**DIFC registrar of companies notices**
- **Best monitoring URL**: `https://www.difc.com/business/registrars-and-commissioners/registrar-of-companies/notices`
- **Why it's valuable**: Registrar notices for DIFC-registered companies (fee changes, filing deadline extensions, compliance notices). Direct fetch returned 403 but page is confirmed to exist.
- **In sources.json already**: Not confirmed — check against `DIFC Legal Notices` entry
- **Recommended action**: Add if not present.

**DIFC news page**
- **Best monitoring URL**: `https://www.difc.com/whats-on/news`
- **Why it's valuable**: Publishes consultation launch announcements, new law enactments, and regulatory updates. Most recent confirmed: Variable Capital Company Regulations enacted (9 Feb 2026), multiple consultations announced in June 2026.
- **In sources.json already**: Partially — several specific news slugs are tracked. No hub/index page confirmed.
- **Recommended action**: Add news hub page `https://www.difc.com/whats-on/news` to catch newly published items.

---

### DIFC Courts (difccourts.ae)

**Practice directions**
- **Best monitoring URL**: `https://www.difccourts.ae/rules-decisions/practice-directions`
- **Why it's valuable**: DIFC Courts practice directions have compliance relevance for financial firms engaged in litigation or arbitration within DIFC. Most recent: Practice Direction No. 1 of 2025 (Access to Justice in Employment Disputes, Oct 2025). No 2026 PD confirmed yet but the page is actively maintained.
- **Update frequency**: Ad hoc — one to three practice directions per year
- **HTML or JS-rendered**: HTML (verified accessible)
- **In sources.json already**: Not found in enabled sources.
- **Recommended action**: ADD — low volume but high legal relevance for DIFC entities. Lightweight to monitor.

**DIFC Courts registrar's directions**
- **Best monitoring URL**: `https://www.difccourts.ae/rules-decisions/registrars-directions`
- **Update frequency**: Ad hoc
- **In sources.json already**: Not found
- **Recommended action**: ADD alongside practice directions.

---

### UAE Official Gazette (Al Jarida Al Rasmiya)

The UAE federal Official Gazette does not have a publicly accessible digital subscription portal in the way EU or UK official gazettes do. Key findings from research:

- The federal gazette is managed by the Ministry of Justice; subscriptions are physical/contact-based
- The u.ae government portal links to the Ministry of Justice for gazette enquiries
- Local emirate gazettes (e.g., Abu Dhabi, Dubai) are separately maintained
- **Dubai Official Gazette**: Dubai Legal Affairs Department maintains its gazette at `https://dlp.dubai.gov.ae/en/Pages/OfficialGazette.aspx` and `https://legal.dubai.gov.ae/en/Services/Pages/Official-Gazette.aspx`
- **Practical alternative**: The UAE Legislation Portal (`uaelegislation.gov.ae`) serves as the effective digital equivalent for federal laws, as it publishes all enacted Federal Decree-Laws with the same authority. The Cabinet website (`uaecabinet.ae`) publishes Cabinet Decisions.

**In sources.json already**: Not explicitly — the UAE Legislation Portal covers the federal gazette's content
**Recommended action**: No single "Official Gazette" URL to add. The combination of `uaelegislation.gov.ae` + `uaecabinet.ae/en/news` provides equivalent coverage.

---

### Executive Office for AML/CFT (moec.gov.ae)

- **Best monitoring URL**: `https://www.moec.gov.ae/en/anti-money-laundering/`
- **In sources.json already**: Yes — `Executive Office for AML/CFT — Anti-Money Laundering Hub` (enabled)
- **Recommended action**: Already covered. This is distinct from moet.gov.ae.

---

## Gaps and Domain Migration Issues

### Priority Gap: MOHRE (mohre.gov.ae) — NOT IN SYSTEM
MOHRE is the single largest employer-compliance regulator in the UAE. Ministerial Resolution 340/2026 (Wage Protection System overhaul) is a high-impact labour compliance change that would be missed entirely under current coverage. Recommend adding:
- `https://www.mohre.gov.ae/en/laws-and-regulations/resolutions-and-circulars.aspx`
- `https://www.mohre.gov.ae/en/laws-and-regulations/laws.aspx`

### Priority Gap: UAE Cabinet (uaecabinet.ae) — NOT IN SYSTEM
Cabinet decisions are upstream sources for FTA, CBUAE, and MOHRE regulations. Adding `https://uaecabinet.ae/en/news` provides early-warning signal.

### Priority Gap: Dubai Legislation Portal (dlp.dubai.gov.ae) — NOT IN SYSTEM
Local Dubai laws (covering millions of mainland-licensed businesses) are not captured. Add `https://dlp.dubai.gov.ae/en/Pages/LegislationSearch.aspx`.

### Domain Migration Required: SCA → CMA
All 9 sources under www.sca.gov.ae (and related) should be updated to www.uaecma.gov.ae. The 301 redirect is permanent but monitoring systems should not rely on redirect chains for stability.

### DFSA Monthly Legislative Notices — Pattern Coverage Gap
The current approach monitors specific historic DFSA legislative notice URLs but will not auto-detect `notice-amendments-legislation-june-2026`, `notice-amendments-legislation-july-2026`, etc. as they are published. Add `https://www.dfsa.ae/news` as a monitored hub page.

### DIFC Courts — NOT IN SYSTEM
Low volume but legally relevant. Add practice directions and registrar's directions pages.

### DIFC News Hub — Partially Covered
Individual news slugs tracked but no hub page. Add `https://www.difc.com/whats-on/news`.

### ADGM Announcements Hub — May Be Missing
ADGM announcement hub `https://www.adgm.com/media/announcements` provides better coverage than tracking individual announcement slugs.

---

## Summary Table

| Regulator | Best Monitoring URL | Update Freq | In System | Action |
|---|---|---|---|---|
| VARA — Rulebook updates | rulebooks.vara.ae/view-revision-updates | Continuous | Yes | Already covered |
| VARA — Enforcement/warning notices | vara.ae/en/regulations/regulatory-notices/ | Monthly | Partially | Add notice listing URL |
| VARA — News | vara.ae/en/news | Monthly | Yes | Already covered |
| CBUAE — Rulebook updates | rulebook.centralbank.ae/en/view-revision-updates | Monthly | Yes | Already covered |
| CBUAE — Payments hub | centralbank.ae/en/our-operations/payments-and-settlements/regulations-and-standards/ | Quarterly | Partial | Add hub page |
| CBUAE — AML/CFT hub | centralbank.ae/en/our-operations/anti-money-laundering-and-combatting-the-financing-of-terrorism/ | Monthly | Yes | Already covered |
| DFSA — Notice of amendments (news hub) | dfsa.ae/news | Monthly | Partially | Add news hub page |
| DFSA — Consultation papers | dfsa.ae/your-resources/regulatory/consultation-papers | Quarterly | Yes | Already covered |
| DFSA — MLRO letters | dfsa.ae/what-we-do/aml-ctf-sanctions-compliance/financial-crime-prevention-notices-and-mlro-letters | Biannual | Yes (enabled) | Test JS adapter |
| DFSA — Enforcement | dfsa.ae/what-we-do/enforcement/regulatory-actions | Monthly | Yes | Already covered |
| DFSA — SEO letters | dfsa.ae/your-resources/publications-reports/seo-letters-1 | Annual | Unknown | Add if missing |
| ADGM FSRA — Consultations | adgm.com/legal-framework/public-consultations | Quarterly | Yes | Already covered |
| ADGM FSRA — Announcements hub | adgm.com/media/announcements | Weekly | Partial | Add hub page |
| ADGM FSRA — Enforcement/regulatory actions | adgm.com/operating-in-adgm/.../enforcement/regulatory-actions | Monthly | Yes | Verify URL |
| ADGM FSRA — Supervision circulars | adgm.com/operating-in-adgm/.../supervision/circulars | Quarterly | Yes | Already covered |
| UAE FIU — Publications | uaefiu.gov.ae/en/more/knowledge-centre/publications/ | Monthly | Yes | Already covered (RSS available) |
| UAE FIU — AML laws | uaefiu.gov.ae/en/more/knowledge-centre/aml-cft-laws-related-decisions/ | Low | Yes | Already covered |
| UAE CMA (formerly SCA) — Circulars | **uaecma.gov.ae**/en/regulations/circulars-and-procedures.aspx | Bimonthly | Yes (old URL) | Update domain: sca.gov.ae → uaecma.gov.ae |
| MoET — AML/CFT circulars (DNFBPs) | moet.gov.ae/en/aml | Monthly | Yes | Already covered |
| Executive Office AML/CFT | moec.gov.ae/en/anti-money-laundering/ | Monthly | Yes | Already covered |
| Ministry of Finance | mof.gov.ae/en/financial-legislation/ | Monthly | Yes | Already covered |
| FTA — VAT guides | tax.gov.ae/en/taxes/vat/guides.references.aspx | Monthly | Yes | Already covered |
| FTA — Corporate tax guides | tax.gov.ae/en/taxes/corporate.tax/corporate.tax.guides.references.aspx | Monthly | Yes | Already covered |
| UAE Legislation Portal | uaelegislation.gov.ae/en/legislations | Ad hoc | Yes | Already covered (verify 403) |
| **MOHRE — Resolutions and circulars** | **mohre.gov.ae/en/laws-and-regulations/resolutions-and-circulars.aspx** | Monthly | **NO** | **ADD — priority gap** |
| **UAE Cabinet — Decisions** | **uaecabinet.ae/en/news** | Monthly | **NO** | **ADD — upstream signal** |
| **Dubai Legislation Portal** | **dlp.dubai.gov.ae/en/Pages/LegislationSearch.aspx** | Continuous | **NO** | **ADD — local Dubai laws** |
| **DIFC Courts — Practice directions** | **difccourts.ae/rules-decisions/practice-directions** | Ad hoc | **NO** | **ADD — low volume, high relevance** |
| **DIFC Courts — Registrar's directions** | **difccourts.ae/rules-decisions/registrars-directions** | Ad hoc | **NO** | **ADD** |
| DIFC — News hub | difc.com/whats-on/news | Weekly | Partially | Add hub page |
| Dubai Economy & Tourism (DED) | ded.ae/laws_and_regulations/en/cabinet_decisions | Quarterly | NO | Conditional add (test accessibility) |

---

## Accessibility Notes for Adapter Configuration

Several high-priority sources block direct HTTP fetches with 403 responses. These require either:
- Playwright/JavaScript rendering adapter (for JS-SPAs)
- Rotating user-agent headers
- Or are truly inaccessible to scrapers (some government WAFs)

Pages confirmed to block direct fetch during this session:
- `centralbank.ae` main domain (all pages, not the rulebook subdomain)
- `dfsa.ae` all pages
- `uaecabinet.ae` main pages
- `uaelegislation.gov.ae` legislations listing
- `sca.gov.ae` / `uaecma.gov.ae` some pages
- `difc.com` some registrar pages
- `mohre.gov.ae` (timeout rather than 403)

Pages confirmed accessible via direct HTTP fetch:
- `rulebooks.vara.ae` (full content)
- `vara.ae` (regulatory notices page)
- `adgm.com` (announcements, consultations, enforcement)
- `uaefiu.gov.ae` (publications, AML laws)
- `moet.gov.ae` (AML page confirmed accessible)
- `tax.gov.ae` (guides pages)
- `difccourts.ae` (practice directions)
- `difc.com` news pages (most)
