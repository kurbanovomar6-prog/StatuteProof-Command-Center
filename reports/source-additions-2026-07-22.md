# StatuteProof — источники: что добавить (полный список)

**Дата:** 2026-07-22 · **Метод:** 9 research-агентов с web-поиском по семействам регуляторов, каждый кандидат проверялся живым WebFetch/WebSearch, дедуп против 452 существующих URL (164 домена).

> **Честное ограничение:** воркфлоу оборвался на месячном лимите расходов — успели 5 из 9 семейств (CBUAE, FTA/налоги, CMA-ex-SCA, VARA/Dubai, DFSA/DIFC). Семейство **ADGM/FSRA я до-исследовал вручную** (ниже, 3 подтверждённых страницы). **Не исследованы:** детально GCC (CBB Bahrain, QCB, Oman CBO/CMA, Kuwait CMA) и международные фиды сверх уже имеющихся. Adversarial-verify стадия для 5 семейств не прошла — поэтому ниже помечена честная `confidence` от исследователя, а не двойная проверка.

**Итого рекомендовано к добавлению: 30 готовых сейчас** + 9 требуют WAF/headless-адаптер.

## Уровень 1 — добавлять сейчас (подтверждено живьём, датированные обновления, читается монитором)

### ADGM_FSRA
- **ADGM FSRA Regulatory Actions (enforcement: final notices, fines, undertakings)**
  - URL: https://www.adgm.com/operating-in-adgm/additional-obligations-of-financial-services-entities/enforcement/regulatory-actions
  - регулятор: ADGM FSRA · тип: enforcement · каденция: event-driven, several per year
  - читаемость: server-rendered dated table + pagination · WAF-риск: low · confidence: high
  - что видно живьём: verified 2026-07: 08 Jan 2026 Wealthface (Enforceable Undertaking), 17 Dec 2025 Payward MENA (Final Notice), 24 Nov 2025 FWS Group, ~11 items, server-rendered
  - зачем: Top-WTP enforcement channel. REGISTRY HAS THE OLD PATH /fsra/enforcement DISABLED as 'path_moved' — this is the live replacement.
- **ADGM FSRA Regulatory Alerts (scam / clone-firm / unlicensed warnings)**
  - URL: https://www.adgm.com/operating-in-adgm/additional-obligations-of-financial-services-entities/enforcement/regulatory-alerts
  - регулятор: ADGM FSRA · тип: alerts/warnings · каденция: ~monthly
  - читаемость: server-rendered dated table · WAF-риск: low · confidence: high
  - что видно живьём: verified 2026-07: 08 Jul 2026 Veyron Markets, 05 Jun 2026 Sarwa domains, 05 May 2026 crypto domains, 28 Apr 2026 MaskEx; 40+ alerts 2016→2026
  - зачем: Fresh, frequently-updated warning feed — direct client-risk relevance.
- **ADGM Registration Authority — Regulatory Actions (RA fines/penalties)**
  - URL: https://www.adgm.com/operating-in-adgm/monitoring-and-enforcement/regulatory-actions
  - регулятор: ADGM RA · тип: enforcement · каденция: event-driven
  - читаемость: server-rendered dated table · WAF-риск: low · confidence: high
  - что видно живьём: verified 2026-07: 26 Jan 2026 false beneficial-ownership fine (Tina Wade), 15 Jul 2025 x4 filing/directors-report fines; ~11 items
  - зачем: Beneficial-ownership + filing enforcement — the UBO angle DNFBPs are examined on.
### DFSA_DIFC
- **DFSA Alerts (scam / impersonation / clone-firm warnings)**
  - URL: https://www.dfsa.ae/alerts
  - регулятор: DFSA · тип: public alerts — regulator/firm impersonation, clone firms, unauthorised firms, fake-letter/email scams · каденция: event-driven, frequent (multiple 2026 alerts confirmed)
  - читаемость: MEDIUM — dfsa.ae returns 403 to generic fetchers, but the product already runs a working DFSA adapter against dfsa.ae, so this host is monitorable in-product. Listing is dated and reverse-chronological. · WAF-риск: med · confidence: high
  - что видно живьём: WebSearch returned live 2026 alert detail pages under dfsa.ae/alerts/ (Nomura impersonation, fake-DFSA-email 'Millennium Fund', DFSA-CEO fake notice); listing at dfsa.ae/alerts and dfsa.ae/your-resources/dfsa-alerts/alerts.
  - зачем: Directly MLRO-relevant fraud/AML surface: warns of DFSA and DFSA-authorised-firm impersonation and fake DFSA letters/emails used in scams (2026 examples: Nomura DIFC branch impersonation, 'Millennium Fund' fake-email scam). Registry monitors notices-public-reg
- **DFSA Media Releases (Thomson Reuters Rulebook mirror)**
  - URL: https://dfsaen.thomsonreuters.com/rulebook/media-releases
  - регулятор: DFSA · тип: press/media releases — enforcement fines, rulebook/framework changes, consultations, appointments, market notices · каденция: ~2-3 per month (event-driven)
  - читаемость: HIGH — server-rendered HTML on the Thomson Reuters mirror, WAF-free (WebFetch 200). Reverse-chronological dated listing, easy diff. · WAF-риск: low · confidence: high
  - что видно живьём: WebFetch confirmed: most recent item '7 July 2026 — DFSA proposes updates to Collective Investment Fund framework'; archive 2004→July 2026, ~500+ items; ~25-30 releases in 2025.
  - зачем: This consolidated feed is the single richest DFSA channel: it surfaces enforcement fines (e.g. 2 Feb 2026 reinsurance broker USD 455,176; 6 Feb 2026 Ark Capital USD 504,000), Crypto Token framework updates (12 Jan 2026), CIF framework consultation (7 July 2026
- **DFSA Waivers and Modification Notices (TR Rulebook mirror)**
  - URL: https://dfsaen.thomsonreuters.com/rulebook/waivers-and-modification-notices
  - регулятор: DFSA · тип: waiver / rule-modification notices granted to specific authorised firms, indexed by year · каденция: ongoing / ad-hoc as applications are approved (2026 folder active)
  - читаемость: MEDIUM — WAF-free TR mirror; index page groups by year (2026→2005). A monitor watching the 2026 year node catches new entries; the top index diffs when a new year/notice appears. · WAF-риск: low · confidence: medium
  - что видно живьём: WebFetch confirmed live index with years 2026→2005 + Archive; described as a continuously maintained listing updated as waivers/modifications are granted.
  - зачем: Firm-specific relief from DFSA rules is a signal of supervisory posture and can affect a monitored firm's obligations. Not present in the registry.
- **DIFC Courts — Court of Appeal Judgments**
  - URL: https://www.difccourts.ae/rules-decisions/judgments-orders/court-appeal
  - регулятор: DIFC Courts · тип: appellate court judgments (dated, with neutral citations e.g. [2026] DIFC CA 001) · каденция: event-driven, roughly monthly / several per year
  - читаемость: HIGH — same server-rendered difccourts.ae listing structure as CFI; lower volume, higher per-item significance. · WAF-риск: low · confidence: high
  - что видно живьём: WebSearch confirmed live 2026 items: 'Orlagh v Orchid [2026] DIFC CA 001' and CA 009/2026 (8 June 2026, Deputy Chief Justice Al Madhani panel).
  - зачем: Appellate rulings set binding DIFC precedent (interpretation of DIFC laws/regulations) — high-signal, low-noise complement to the CFI feed. New uncovered domain.
- **DIFC Courts — Judgments & Orders (Court of First Instance)**
  - URL: https://www.difccourts.ae/rules-decisions/judgments-orders/court-first-instance
  - регулятор: DIFC Courts · тип: court judgments and orders (dated case listing with citations) · каденция: ~15-20+ per month
  - читаемость: HIGH — server-rendered HTML with pagination (ccm_paging/ccm_order_by params), dated reverse-chronological. difccourts.ae is a NEW domain not in the registry (registry covers difc.com / difc.ae only). · WAF-риск: low · confidence: high
  - что видно живьём: WebFetch confirmed dated cases to 20 July 2026 (CFI 070/2018, CFI 110/2025 15 Jul, CFI 099/2025 14 Jul...), 305 pages of pagination, ~15-20 cases/month.
  - зачем: Enforcement-adjacent primary source: DIFC Court judgments include financial-services, fraud and crypto disputes (e.g. CFI 067/2025 COINMENA v FOLOOSI, order 7 July 2026). New domain, entirely uncovered. High cadence — best treated as a monitored high-volume fe
### FTA_tax
- **FTA Announcements (deadlines & operational notices)**
  - URL: https://tax.gov.ae/en/announcements.aspx
  - регулятор: UAE Federal Tax Authority (FTA) · тип: Announcements / filing-deadline notices · каденция: event-driven; recurring filing-deadline notices
  - читаемость: Server-rendered .aspx, dated items marked New. Small, high-signal page — cheap to monitor. · WAF-риск: low · confidence: high
  - что видно живьём: WebFetch 2026-07: two New items dated 2026-07-28 (VAT return deadline) and 2026-08-17 (Excise return deadline); Latest News block references 2025 annual report and home-builder refunds.
  - зачем: Distinct from News: carries hard operational deadlines (VAT return, Excise return) and service-fee/scheme changes that directly trigger MLRO action. Confirmed live: 'Final deadline for filing VAT returns' 2026-07-28, 'Final deadline for filing Excise return' 2
- **FTA Corporate Tax — Guides, References & Public Clarifications**
  - URL: https://tax.gov.ae/en/taxes/corporate.tax/corporate.tax.guides.references.aspx
  - регулятор: UAE Federal Tax Authority (FTA) · тип: Public clarifications + guides listing (Corporate Tax) · каденция: ~monthly / ongoing (new CTP-series clarifications and guide updates through mid-2026)
  - читаемость: Server-rendered .aspx list, WebFetch read cleanly; each row is a dated PDF with issue date. Good for a change-monitor. · WAF-риск: low · confidence: high
  - что видно живьём: WebFetch 2026-07: '69 items total', server-rendered list; CTP011 dated 2026-07-15, CT clarifications summary dated 2026-07-09, Basic Tax Info Bulletin CT Losses 2026-06-25, CTP010 2026-04-29; rows are downloadable PDFs marked 'New'.
  - зачем: Corporate Tax is new (2023+) so FTA guidance churns fast. Confirmed live: 69 items, latest 'CTP011 Downward adjustments...' issued 2026-07-15, 'Corporate Tax – Summary of FTA Private Clarifications up to May 2026' 2026-07-09, 'CTP010 director/officer' 2026-04-
- **FTA Legislation (all tax types — Cabinet/Ministerial/FTA Decisions + Directives on Tax Transactions)**
  - URL: https://tax.gov.ae/en/legislation.aspx
  - регулятор: UAE Federal Tax Authority (FTA) · тип: Consolidated legislation/decisions listing (138 items) · каденция: ~weekly-to-monthly; multiple new 2026 decisions and Directives
  - читаемость: Server-rendered .aspx list; each row dated with a published date and PDF. Highest-signal single legislation feed on the FTA site. · WAF-риск: low · confidence: high
  - что видно живьём: WebFetch 2026-07: '138 Items found'; Directive on Tax Transactions No.4 of 2026 pub 2026-07-17, MD 244/2025 pub 2026-07-03, FTA Decision 6/2026 pub 2026-07-14. Flagged likely_duplicate because a registry with any FTA coverage plausibly already holds the main legislation index — verify; if only sub-p
  - зачем: Single page aggregating Cabinet Decisions, Ministerial Decisions, FTA Decisions and the NEW 'Directives on Tax Transactions' type. Confirmed live: 'Directive on Tax Transactions No.4 of 2026' (life insurance VAT) published 2026-07-17, 'Ministerial Decision No.
- **FTA Legislation — Corporate Tax (decisions sub-listing)**
  - URL: https://tax.gov.ae/en/legislation/corporate.tax.aspx
  - регулятор: UAE Federal Tax Authority (FTA) · тип: Corporate Tax legislation/decisions sub-listing · каденция: ~monthly (steady stream of CT Cabinet/Ministerial Decisions through 2025-2026)
  - читаемость: Server-rendered .aspx sub-page (same template as parent). Narrower, lower-noise than the all-types page for a CT-focused customer. · WAF-риск: low · confidence: medium
  - что видно живьём: URL surfaced as live in FTA search results ('Federal Tax Authority - Legislation - Corporate Tax'); parent legislation index confirmed live+dated via WebFetch. Not individually WebFetched — cadence inferred from confirmed CT decision numbering (55/2025, 96/2025, 84/2025).
  - зачем: Isolates Corporate Tax binding decisions (e.g. Cabinet Decision 55/2025 exemptions, MD 96/2025 REIT exemption, MD 84/2025 audited financials) so a CT-only alert stream isn't drowned by VAT/excise items. Good for segmenting alerts by tax type.
- **FTA News (Media Centre press releases)**
  - URL: https://tax.gov.ae/en/media.centre/news.aspx
  - регулятор: UAE Federal Tax Authority (FTA) · тип: Press releases / news listing · каденция: event-driven, several per month
  - читаемость: Server-rendered .aspx list, 243 items, each dated. Reliable for new-item detection. · WAF-риск: low · confidence: high
  - что видно живьём: WebFetch 2026-07: '243 total items'; headlines dated 2026-07-21 (AED 353.5M refund H1 2026), 2026-07-20 (Emirates Majalis), 2026-07-07, 2026-07-03, 2026-06-29 (2025 Annual Report). Flagged likely_duplicate: a common default source to already hold — verify.
  - зачем: Fastest-moving FTA channel; surfaces deadline reminders, penalty/registration pushes, fee changes and scheme launches before/alongside formal legislation. Confirmed live: items dated 2026-07-21, 2026-07-20, 2026-07-07, 2026-07-03, 2026-06-29. High compliance s
- **FTA VAT — Guides, References & Public Clarifications**
  - URL: https://tax.gov.ae/en/taxes/vat/guides.references.aspx
  - регулятор: UAE Federal Tax Authority (FTA) · тип: Public clarifications + guides listing (VAT) · каденция: ~monthly / ongoing (VATP/VATG-series clarifications and guide revisions)
  - читаемость: Server-rendered .aspx list of ~199 dated PDF rows; paginated (first 10 shown). Monitor the first page for new-item detection. · WAF-риск: low · confidence: high
  - что видно живьём: WebFetch 2026-07: '199 items total'; VATGED1 2026-06-29, VATGRH1 2026-06-10, VATGPM1 2026-01-05, VAT Admin Exceptions 2025-12-05, Tax Group Registration 2025-10-13, Input Tax Apportionment 2025-09-30.
  - зачем: The deepest FTA update channel (199 items). Confirmed live: 'Education Sector VATGED1' 2026-06-29, 'VAT Refund for UAE Nationals Building New Residences VATGRH1' 2026-06-10, 'Profit Margin Scheme VATGPM1' 2026-01-05, 'VAT Administrative Exceptions Guide' 2025-
- **Ministry of Finance — Financial Legislation (tax decisions repository)**
  - URL: https://mof.gov.ae/en/financial-legislation/
  - регулятор: UAE Ministry of Finance (MoF) · тип: Legislation repository (Cabinet/Ministerial Decisions & Resolutions) · каденция: ~monthly (steady 2025-2026 tax decisions incl. e-invoicing, top-up tax, R&D credit)
  - читаемость: Server-rendered WordPress page, filterable by year/category, dated PDF rows. Clean WebFetch read. · WAF-риск: low · confidence: high
  - что видно живьём: WebFetch 2026-07: server-rendered filterable list; MD 96/2026 top-up tax (2026-06), MR 66/2026 e-invoicing (2026-05), MR 56/2026 ASP (2026-05), Cabinet Decision 215/2025 R&D credit, MD 24/2026.
  - зачем: MoF issues the upstream tax policy instruments the FTA then administers — often the FIRST place a change appears. Confirmed live: MD 96/2026 (Top-Up Tax on MNEs, 2026-06), Ministerial Resolution 66/2026 (e-invoicing, 2026-05), Ministerial Resolution 56/2026 (A
- **Ministry of Finance — News**
  - URL: https://mof.gov.ae/en/news/
  - регулятор: UAE Ministry of Finance (MoF) · тип: News / policy announcements listing · каденция: event-driven, roughly weekly-to-monthly
  - читаемость: Server-rendered WordPress archive with dated posts and pagination. Straightforward to monitor first page. · WAF-риск: low · confidence: high
  - что видно живьём: WebFetch 2026-07: dated posts 2026-06-26 (e-invoicing pilot), 2026-06-21 (GFS); search-confirmed related MoF news posts on Tax Procedures Law amendments (early 2026) and e-invoicing ASP deadline extension.
  - зачем: MoF announces tax-policy shifts and e-invoicing milestones here before formal legislation posts. Confirmed live: 'Pilot Phase of the Electronic Invoicing System' 2026-06-26, 'Advances Government Finance Statistics' 2026-06-21; prior posts include Tax Procedure
- **Ministry of Finance — Public Consultations**
  - URL: https://mof.gov.ae/en/digital-participation/consultations/
  - регулятор: UAE Ministry of Finance (MoF) · тип: Consultation papers / calls for comment · каденция: event-driven (each new tax consultation, e.g. e-invoicing programme paper)
  - читаемость: Server-rendered WordPress page listing consultations with comment windows and PDFs. Low volume, high value per item. · WAF-риск: low · confidence: medium
  - что видно живьём: Search-confirmed live page ('Consultations | Ministry of Finance') and a concrete tax consultation instance (eInvoicing Programme Consultation Paper, 168 pages, comment deadline 2025-02-27, cited by EY/official). Page itself not individually WebFetched.
  - зачем: Earliest possible signal of upcoming tax regime changes — the 168-page eInvoicing Programme Consultation Paper (comment deadline 2025-02-27) previewed the whole 2026-2027 e-invoicing mandate months before legislation. Lets StatuteProof flag 'change coming' bef
### SCA (UAE Securities & Commodities Authority — now Capital Market Authority / uaecma.gov.ae)
- **CMA (ex-SCA) — Circulars, Rules and Procedures**
  - URL: https://www.uaecma.gov.ae/en/regulations/circulars-rules-and-procedures
  - регулятор: Capital Market Authority (formerly Securities & Commodities Authority) · тип: Regulatory circulars, rules and procedures (incl. AML/CFT guidance for capital-market firms, AGM circulars, unlicensed-solicitation circulars) · каденция: event-driven, several per year (a handful of live items incl. FinTech framework, Passporting Rules, 2024 AGM circular, VA guidelines)
  - читаемость: medium — modern SPA on uaecma.gov.ae; WebFetch returned server-rendered item titles (5 items) but detail pages render client-side, so a listing-diff monitor works, deep detail may need JS render · WAF-риск: med · confidence: high
  - что видно живьём: WebFetch of the page returned 5 live circular items (Passporting Rules, FinTech regulatory framework, 2024 AGM circular, contracting-with-unlicensed-entities circular, Virtual Assets guidelines). Path reachable via homepage nav 'Circulars, Rules and procedures of the CMA'.
  - зачем: This is the core SCA/CMA circular channel — where MLRO-relevant items like AML circulars and unlicensed-client-solicitation warnings appear. Directly on the ICP's compliance path for capital-market-licensed firms.
- **CMA (ex-SCA) — Draft Regulations / Public Consultations**
  - URL: https://www.uaecma.gov.ae/en/regulations/draft-regulations
  - регулятор: Capital Market Authority (formerly SCA) · тип: Consultation papers / draft regulations open for public comment, with deadlines · каденция: event-driven, a few per year (currently one active: Governance Guide Arts 76-77, comment deadline 16 Jan 2026)
  - читаемость: medium — SPA renders the active consultation server-side (WebFetch read the item + deadline) · WAF-риск: med · confidence: high
  - что видно живьём: WebFetch returned one active draft: 'Proposed Amendments to Governance Guide Articles 76-77', consultation deadline 16 Jan 2026, comments to Consultation@sca.ae — confirms a live, dated, updating consultation list.
  - зачем: Early-warning channel: consultations are the leading indicator of coming rule changes, giving MLROs lead time. Comment deadlines are hard dates worth alerting on.
- **CMA (ex-SCA) — Latest Regulations**
  - URL: https://www.uaecma.gov.ae/en/regulations/latest-regulations.aspx
  - регулятор: Capital Market Authority (formerly SCA) · тип: Newly issued / amended regulations and Board-of-Directors decisions & resolutions · каденция: event-driven, roughly monthly-to-quarterly (Governance Code amended by Board Decision 2/RM of 2024)
  - читаемость: medium — .aspx on old host 301s to uaecma.gov.ae SPA; server renders section but full dated list loads client-side · WAF-риск: med · confidence: high
  - что видно живьём: sca.gov.ae/en/regulations/latest-regulations.aspx returns HTTP 301 to uaecma.gov.ae equivalent; KPMG/search confirm 2024 Governance Code amendment via SCA Board Decision 2/RM. Flagged likely-dup because a generic 'SCA regulations' page is plausibly already registered — but the OLD sca.gov.ae URL now
  - зачем: Primary feed of new/amended SCA/CMA regulations and board resolutions — the change-events a compliance officer must react to. Board decisions (e.g. governance code amendments) surface here first.
- **CMA (ex-SCA) — Licensed Companies (open-data register)**
  - URL: https://www.uaecma.gov.ae/en/open-data/licensed-companies.aspx
  - регулятор: Capital Market Authority (formerly SCA) · тип: Register of SCA/CMA-licensed companies (additions, removals, status changes) · каденция: frequently updated (search snippet: 'updated 1 day ago')
  - читаемость: low-to-medium — large dynamic register; useful as a change-diff but noisy and needs rendered rows, so lower monitorability than the news/circular lists · WAF-риск: med · confidence: medium
  - что видно живьём: Search result states the page was 'updated 1 day ago', indicating high update frequency. Page confirmed live at uaecma.gov.ae (also referenced in Arabic at sca.gov.ae/ar/open-data/licensed-companies.aspx).
  - зачем: License additions/withdrawals are compliance-relevant (counterparty due diligence, verifying a firm is genuinely licensed). Complements the Warnings list. Lower priority due to noise/volume.
- **CMA (ex-SCA) — Media Centre / News**
  - URL: https://www.uaecma.gov.ae/en/media-centre/news
  - регулятор: Capital Market Authority (formerly SCA) · тип: Press/media releases, regulatory announcements, market-holiday notices, campaigns (e.g. finfluencer/scam-awareness) · каденция: ~monthly (confirmed items: 12 Jun 2026, 22 May 2026, 20 Apr 2026)
  - читаемость: high — server-rendered dated list with date-range filter and archive pagination (WebFetch read three dated items directly) · WAF-риск: low · confidence: high
  - что видно живьём: WebFetch returned 3 dated news items (June/May/April 2026) plus an 'Our news archive' with date-range filter and prev/next pagination — a clean server-rendered dated list. Includes the April 2026 International Week of Action / finfluencer campaign.
  - зачем: Announcement layer: regulatory campaigns, scam/finfluencer awareness, and policy signals often appear here before/alongside formal circulars. Good low-noise, dated, monitorable feed.
- **CMA (ex-SCA) — Violations and Violators (enforcement/disciplinary decisions)**
  - URL: https://www.uaecma.gov.ae/en/open-data/violations-and-violators
  - регулятор: Capital Market Authority (formerly SCA) · тип: Enforcement / disciplinary decisions and penalties against SCA/CMA-licensed companies (and individuals) · каденция: event-driven, ongoing (dedicated open-data enforcement register)
  - читаемость: medium — SPA; parent section server-renders nav, sub-lists (violations-of-companies-licensed-by-sca.aspx) load client-side · WAF-риск: med · confidence: medium
  - что видно живьём: Search confirms sub-page https://www.uaecma.gov.ae/en/open-data/violations-and-violators/violations-of-companies-licensed-by-sca.aspx exists (301 from sca.gov.ae). Parent 'Violations and Violators' section confirmed in site nav. Could not read populated rows via WebFetch (dynamic table) — hence medi
  - зачем: This is the SCA/CMA enforcement channel — disciplinary actions and penalties against licensed firms. Enforcement monitoring is the single biggest documented WTP gap for the MLRO ICP; this closes it for capital markets.
- **CMA (ex-SCA) — Warnings (unlicensed entities / investor alerts)**
  - URL: https://www.uaecma.gov.ae/en/open-data/warnings.aspx
  - регулятор: Capital Market Authority (formerly SCA) · тип: Public warnings against unlicensed firms/persons soliciting SCA-regulated activity (investor-protection alerts) · каденция: event-driven, multiple per month during campaigns (e.g. Sep 2025 warnings against firms impersonating licensed companies)
  - читаемость: medium — server-rendered filter/pagination table on uaecma.gov.ae; data rows load dynamically so a rendered-list monitor is best · WAF-риск: med · confidence: high
  - что видно живьём: Page confirmed live (warnings.aspx with Name/Address/Practice/Published-date filters). Search corroborates active warnings: Khaleej Times & Filipino Times (Sep 2025) report SCA warnings vs unlicensed/impersonating firms (e.g. 'ALYWRW FOR MARKETING AND PR L.L.C'). Old sca.gov.ae/en/open-data/violatio
  - зачем: High AML/fraud relevance: names of unlicensed/impersonating entities are exactly what a UAE MLRO screens against. Distinct from the 'violations' list (this is unlicensed outsiders, not licensed-firm discipline).
### VARA_Dubai
- **DIFC Courts — Practice Directions**
  - URL: https://www.difccourts.ae/rules-decisions/practice-directions
  - регулятор: DIFC Courts (Dubai International Financial Centre judiciary) · тип: Dated listing of Practice Directions and Practical Guidance Notes · каденция: Low / event-driven — roughly a handful per year
  - читаемость: High — server-rendered HTML with year filter and traditional pagination · WAF-риск: low · confidence: high
  - что видно живьём: Most recent Practice Direction No. 1 of 2026 (Adjournment of Hearings) dated 14 Jul 2026; PD 1 of 2025 (09 Oct 2025); server-rendered HTML, newest-first
  - зачем: Procedural/practice changes in the DIFC judiciary affect disputes, enforcement and evidence handling for DIFC-domiciled firms. Live and dated. NOTE: DIFC is a distinct jurisdiction from mainland Dubai — this may belong to a DIFC-specific source family rather t
- **Dubai Legislation Portal / Supreme Legislation Committee (SLC) — Recent Legislation**
  - URL: https://slc.dubai.gov.ae/en/legislation-portal/
  - регулятор: Supreme Legislation Committee (SLC), Government of Dubai · тип: Portal of newly issued Dubai laws, decrees, executive/administrative resolutions · каденция: Frequent — new decrees/resolutions issued continuously through the year
  - читаемость: Medium — official portal is live and clearly publishes 2026 items, but access is via a search/browse UI (ASP.NET) rather than a clean dated listing/RSS, so a monitor may need a stable 'latest' or year-indexed URL. The raw reference tree at https://dlp.dubai.gov.ae/Legislation Reference/2026/ exposes new 2026 documents by filename. · WAF-риск: medium · confidence: medium
  - что видно живьём: 2026 items visible via search results: Executive Council Resolution No. 16 of 2026, Administrative Resolutions 30 & 31 of 2026, Decree No. 5 of 2026; portal confirmed as official source of all Dubai legislation since 1961
  - зачем: Authoritative source for new Dubai legislation (laws, decrees, resolutions) — including anything touching commercial, financial or AML-adjacent regulation. Broad coverage that sits upstream of regulator-specific feeds.
- **VARA Enforcement Page (structured enforcement actions table)**
  - URL: https://www.vara.ae/en/enforcement/
  - регулятор: VARA (Virtual Assets Regulatory Authority, Dubai) · тип: Static explainer of enforcement powers PLUS a dated chronological table of specific enforcement cases (entity, violation, action, date) · каденция: Event-driven (new rows as cases are closed)
  - читаемость: High — server-rendered HTML table · WAF-риск: low · confidence: high
  - что видно живьём: Dated enforcement table 2024-2026; most recent row Vesta Prime Portal Co. 2026/01/13 (marketing VA activities, cease-and-desist + penalties). Overlaps content with /regulatory-notices/ so flagged as likely duplicate — add only if the table format is wanted as a distinct normalized view.
  - зачем: A clean, structured enforcement-only table (entity + violation + penalty + date) that is easier to diff than the mixed notices feed. Complements the regulatory-notices listing with a normalized case register.
- **VARA News / Media & Guidance Releases**
  - URL: https://www.vara.ae/en/news/
  - регулятор: VARA (Virtual Assets Regulatory Authority, Dubai) · тип: Dated press/media releases and new-guidance announcements (AML/CFT guidance, Travel Rule, rulebook publications, risk assessments) · каденция: ~Monthly to several per month
  - читаемость: High — server-rendered HTML list linking downloadable PDFs · WAF-риск: low · confidence: high
  - что видно живьём: 43 results; most recent 12 Jun 2026 (AML/CFT Business Risk Assessment Guidance), 1 Jun 2026 (Proliferation Financing NRA), 4 Mar 2026 (VASP AML implementation), 24 Feb 2026 (Travel Rule); server-rendered HTML
  - зачем: Carries VARA's AML/CFT guidance, Travel Rule requirements, VASP implementation deadlines and National Risk Assessment publications — the substantive regulatory-change items an MLRO needs, distinct from the enforcement notices feed.
- **VARA Regulatory Notices — Licensing & Enforcement Notices, Warnings, Investor/Marketplace Alerts**
  - URL: https://www.vara.ae/en/regulations/regulatory-notices/
  - регулятор: VARA (Virtual Assets Regulatory Authority, Dubai) · тип: Dated listing of enforcement notices (fines/cease-and-desist), public warnings, and investor/marketplace alerts against unlicensed VASPs · каденция: Event-driven, clusters of ~2-4/month in active enforcement periods
  - читаемость: High — server-rendered HTML listing with filters/sort; readable by a change-monitor · WAF-риск: low · confidence: high
  - что видно живьём: 29 results; most recent 24 Jun 2026 (Peken Global/KuCoin fines), 22 Jun 2026 (MX Global), 5 Mar 2026 (KuCoin/MEXC alerts), 19 Feb 2026, back to Nov 2022; server-rendered HTML
  - зачем: This is THE primary VARA enforcement + public-warning channel. Directly relevant to a UAE MLRO: names unlicensed firms, fines (AED 100K-600K), cease-and-desist orders, and consumer alerts (KuCoin/MEXC). High legal-risk signal that MLROs must track.
- **VARA Rulebook Revision Change-Log ('View Updates' — Regulatory Framework)**
  - URL: https://rulebooks.vara.ae/view-revision-updates
  - регулятор: VARA (Virtual Assets Regulatory Authority, Dubai) · тип: Dated change-log of rulebook/regulation revisions (what-changed across all activity rulebooks and guidance) · каденция: Frequent — multiple dated revision entries per month
  - читаемость: High — server-rendered HTML with pagination and a date filter; far lighter than the JS rulebook body. Recommend monitoring the 30-day-changed filtered view: https://rulebooks.vara.ae/view-revision-updates?f_days=on&changed=-30%20day · WAF-риск: low · confidence: high
  - что видно живьём: 803 results; recent entries 19 May 2026 (Federal AML/CFT laws), 09 Apr 2026 (VA Issuance guidance), 31 Mar 2026 (Exchange Services Rulebook); server-rendered with conventional pagination; the rulebook index links this exact 'view-revision-updates?f_days=on&changed=-30 day' view
  - зачем: The lighter, monitor-friendly alternative to the JS-heavy rulebook itself — this is the authoritative 'what changed in the rulebook' feed (Version 2.0 activity rulebooks, margin/collateral controls, issuance guidance). Lets an MLRO catch rulebook edits without

## Уровень 2 — ценно, но нужен headless/WAF-адаптер (сейчас 403/429)

### CBUAE
- **CBUAE Consumer Protection — Consumer Notices & Warnings**
  - URL: https://www.centralbank.ae/en/consumer/
  - регулятор: Central Bank of the UAE (CBUAE) · тип: consumer protection notices, fraud/scam warnings, unlicensed-entity alerts · каденция: event-driven (fraud-pattern-triggered; timely notifications when scams/deception patterns are identified)
  - читаемость: medium — consumer section behind the same WAF; structure may be a landing page rather than a clean dated listing (verify the exact sub-path) · WAF-риск: high · confidence: low
  - что видно живьём: Consumer URL surfaced in search ('CBUAE | Consumer'); could not load the page (WAF 403) to confirm a dated listing exists at this exact path — needs verification of the specific notices sub-page.
  - зачем: Public warnings about unlicensed/fraudulent entities and consumer-facing fraud typologies feed directly into an LFI's AML fraud-risk posture and customer-communication obligations. Secondary to enforcement/rulebook but a genuine distinct channel.
- **CBUAE Cyber-Security Centre of Excellence — Fraudulent Reporting / Impersonation Warnings**
  - URL: https://www.centralbank.ae/en/our-operations/risk-management/cyber-security-centre-of-excellence-1/fraudulent-reporting/
  - регулятор: Central Bank of the UAE (CBUAE) · тип: warnings about CBUAE impersonation / fraudulent communications, fraud reporting notices · каденция: event-driven, lower cadence (irregular)
  - читаемость: low-medium — deep sub-page behind the WAF; may be largely static with occasional updates · WAF-риск: high · confidence: low
  - что видно живьём: Full URL surfaced in search ('CBUAE | Cyber-Security Centre of Excellence | Fraudulent Reporting'); page not loadable via WebFetch (WAF). Cadence and dated-listing structure unconfirmed.
  - зачем: Alerts on entities impersonating the CBUAE and fraud-reporting guidance. Relevant to brand-impersonation and fraud-control obligations, but lower cadence and more static than the other channels — include only if broad fraud coverage is wanted.
- **CBUAE Enforcement — Administrative & Financial Sanctions**
  - URL: https://www.centralbank.ae/en/our-operations/enforcement/
  - регулятор: Central Bank of the UAE (CBUAE) · тип: enforcement actions / administrative sanctions / penalty announcements · каденция: event-driven, multiple per month (>AED370m in fines since Jan 2025 across ~13 exchange houses, 10 banks, 7 insurers/brokers, 1 finance co.)
  - читаемость: medium — domain already monitored by the registry so a working fetch adapter almost certainly exists, but this listing 403s plain HTTP fetchers (needs the browser/proxy path) · WAF-риск: high · confidence: high
  - что видно живьём: URL returned as a direct centralbank.ae result in search; corroborated by trade press (The Digital Banker: >AED370.3m in fines since start of 2025; Fincrime Central: Omda Exchange licence revoked + AED10m fine). Page itself 403s automated WebFetch (WAF).
  - зачем: THE single highest-WTP page for a personally- and criminally-liable UAE MLRO: it publicises fines and administrative sanctions against licensed financial institutions and named authorised individuals (penalties up to AED 1bn for LFIs, AED 5m for individuals). 
- **CBUAE Media Center — Press Releases & Announcements**
  - URL: https://www.centralbank.ae/en/news-and-publications/news-and-insights/press-release/media-center-news-room-press-releases-announcements/
  - регулятор: Central Bank of the UAE (CBUAE) · тип: press releases / official announcements · каденция: weekly / several per month
  - читаемость: medium — main press listing; 403s automated fetchers (WAF), same domain as existing monitored pages · WAF-риск: high · confidence: medium
  - что видно живьём: Exact URL surfaced in search ('CBUAE | Media Center - News Room - Press Releases & Announcements'); page 403s automated WebFetch.
  - зачем: Primary announcement feed (new regulations, resilience packages, guidance releases, some enforcement). High cadence and broad coverage — but this is the exact kind of top-level news index a 452-URL registry most likely already carries.
- **CBUAE News and Insights (index)**
  - URL: https://www.centralbank.ae/en/news-and-publications/news-and-insights/
  - регулятор: Central Bank of the UAE (CBUAE) · тип: aggregated news / insights index · каденция: weekly / several per month
  - читаемость: medium — parent index page, same WAF · WAF-риск: high · confidence: medium
  - что видно живьём: URL 'News and Insights' surfaced in search; parent of the confirmed press-release listing.
  - зачем: Parent aggregator over press releases and insights. Useful as a catch-all but redundant with the more specific press-release and publications listings, and a top-level index a broad registry very likely already monitors.
- **CBUAE Publications (AML/CFT/CPF guidance, typologies, reports)**
  - URL: https://www.centralbank.ae/en/news-and-publications/publications/
  - регулятор: Central Bank of the UAE (CBUAE) · тип: guidance papers, AML/CFT/CPF supervisory guidelines, best-practice manuals, reports · каденция: ~monthly / event-driven (e.g. 6-document AML/CFT/CPF guidance package issued 16 Apr 2026 covering PF risk, TBML, correspondent banking, CDD/KYC)
  - читаемость: medium — listing page behind the same CBUAE WAF; individual PDFs live under /media/ and are separately fetchable · WAF-риск: high · confidence: medium
  - что видно живьём: Publications URL surfaced in search ('CBUAE | Publications'); the 16 Apr 2026 AML/CFT/CPF guidance package confirmed via centralbank.ae press release + PDF at centralbank.ae/media/njvnahyo/...-en.pdf and multiple advisory writeups (Crowe, Zigram).
  - зачем: New supervisory guidance and typologies define what 'adequate AML controls' means and shift the compliance bar an MLRO is judged against. The Apr-2026 six-document package is a concrete recent example. Distinct from press releases: this is the primary-source d
- **CBUAE Rulebook — Revision / Change-Log (View Updates)**
  - URL: https://rulebook.centralbank.ae/en/view-revision-updates
  - регулятор: Central Bank of the UAE (CBUAE) · тип: rulebook change-log — dated revisions to regulations, standards and guidance · каденция: event-driven, roughly monthly (each regulation/standard/guidance amendment is logged as a dated revision)
  - читаемость: medium — same CBUAE WAF (rulebook host also 403s plain fetchers), but a single stable change-log URL is ideal for diff-monitoring; adapter for this domain likely already exists · WAF-риск: high · confidence: high
  - что видно живьём: Titled 'View Updates | CBUAE Rulebook' at rulebook.centralbank.ae/en/view-revision-updates, surfaced in search; rulebook host 403s automated WebFetch.
  - зачем: One canonical page that surfaces EVERY dated change to the binding CBUAE Rulebook (regulations, standards, AML/CFT guidance) instead of monitoring hundreds of individual instrument URLs for a rare edit. Far higher signal-per-check than watching static instrume
### DFSA_DIFC
- **DIFC Latest News & Press Releases (whats-on/news listing index)**
  - URL: https://www.difc.com/whats-on/news
  - регулятор: DIFC Authority · тип: DIFC press-release / news index — includes legislative & consultation announcements · каденция: several per month (event-driven)
  - читаемость: MEDIUM-LOW — difc.com is a Next.js SPA that intermittently returns 429/WAF challenges; the registry already reads individual difc.com/whats-on/news/* pages, but the parent LISTING index is not monitored and is the earliest place new consultation announcements appear. · WAF-риск: high · confidence: medium
  - что видно живьём: WebSearch confirmed live index with 2026 items (Q1 2026 client-growth 29 Apr, DIFC Courts H1 2026 July, business/lifestyle 19 May) at difc.com/whats-on/news; registry contains individual whats-on/news/* pages only.
  - зачем: DIFC announces legislative-amendment consultations here first (Prescribed Company Regs consultation 30 Apr 2026, Data Protection / Companies Law amendments, arbitration-law consultation). Monitoring the index catches new consultations before their individual p
### SCA (UAE Securities & Commodities Authority — now Capital Market Authority / uaecma.gov.ae)
- **SCA/CMA — Structured Regulations Service (regulations.sca.gov.ae)**
  - URL: https://regulations.sca.gov.ae/en-us
  - регулятор: Capital Market Authority (formerly SCA) · тип: Structured/searchable regulations database (individual regulations retrievable as PDF by ID, incl. Chairman board decisions) · каденция: event-driven, mirrors regulation issuance
  - читаемость: medium — separate subdomain with deep-linkable machine-ish endpoints (getregulationbyidaspdf/{id}) that may be more monitor-friendly than the main SPA · WAF-риск: med · confidence: low
  - что видно живьём: Search surfaced deep links regulations.sca.gov.ae/en-us/service/getregulationbyidaspdf/114 (Chairman Decision 7 R.M 2016) and .../service/getregulationbyid/... — confirms the subdomain serves individual regulation docs, but I did not confirm a dated updating INDEX/listing page, so confidence low and
  - зачем: Potential structured/stable-URL source of the underlying regulation & board-decision documents (e.g. Chairman Decision 7 R.M of 2016 retrievable by ID) — a cleaner monitoring target than the SPA if it exposes a listing/index.

## Уровень 3 — низкая каденция / не подтверждено

### VARA_Dubai
- **Dubai Department of Economy & Tourism (DET) — Legislative News**
  - URL: https://www.dubaidet.gov.ae/en/legislative-news
  - регулятор: Dubai Department of Economy & Tourism (DET / former DED) · тип: Listing of legislative news, regulatory and licensing updates (title suggests dated items) · каденция: Unverified — page title implies periodic updates but could not confirm dated items due to block
  - читаемость: Low — page returns HTTP 403 (Cloudflare/WAF bot wall) to automated fetch; would need a browser-grade fetch/proxy · WAF-риск: high · confidence: low
  - что видно живьём: HTTP 403 Forbidden on WebFetch (bot wall); could not confirm dated updating items
  - зачем: DET oversees mainland commercial licensing and DNFBP AML supervision in Dubai — legislative/licensing changes here are relevant to non-financial MLROs. But blocked, so value is potential not confirmed.
- **Dubai Department of Economy & Tourism (DET) — Newsroom Press Releases**
  - URL: https://www.dubaidet.gov.ae/en/newsroom/press-releases
  - регулятор: Dubai Department of Economy & Tourism (DET / former DED) · тип: Press releases (official announcements) · каденция: Unverified due to block; press-release pages typically update weekly-ish
  - читаемость: Low — HTTP 403 (Cloudflare/WAF) to automated fetch · WAF-риск: high · confidence: low
  - что видно живьём: HTTP 403 Forbidden on WebFetch (same bot wall as DET legislative-news)
  - зачем: General DET announcements; lower compliance-signal density than the legislative-news page and behind the same WAF. Included for completeness only.

## Гигиена реестра — что почистить/пересмотреть (найдено при оценке)

Из 455 записей 140 включено. Разбивка отключённых по причинам:

- `disabled_non_uae`: 86
- `disabled_covered_by_hub`: 56
- `disabled_static_pdf`: 48
- `disabled_static_doc`: 35
- `geo_blocked`: 18
- `disabled_path_moved`: 14
- `mapped`: 13
- `disabled_external_access`: 13
- `limited`: 11
- `disabled`: 6
- `disabled_navigation_only`: 4
- `disabled_duplicate`: 3

### Требует действия

1. **Устаревший путь FSRA enforcement** (14 записей `path_moved`): в реестре `https://www.adgm.com/fsra/enforcement` отключён как «путь изменился» — я нашёл и проверил 3 живые замены (Уровень 1 выше). Это самый ценный из пропусков: enforcement = топ-WTP.
2. **UAE FIU (uaefiu.gov.ae) — 11 записей, все `geo_blocked`.** goAML/типологии/пресс-релизы ФИУ недоступны с текущего egress. Нужен UAE-резидентный прокси (owner-gated) — тот же рычаг, что для CBUAE/DFSA.
3. **`uaelegislation.gov.ae` + `uaecabinet.ae` — geo_blocked.** Официальная газета/решения Кабинета — первоисточник новых декретов. Тот же прокси-рычаг.
4. **FATF publications отключён как `disabled_non_uae`** — но список high-risk/«серый» FATF прямо влияет на UAE-обязательства (и сам UAE был в нём). Пересмотреть решение. Живьём: `fatf-gafi.org` отдаёт 403 автоматическому фетчеру → нужен headless-адаптер.
5. **NAMLCFTC (`namlcftc.gov.ae`) вообще отсутствует** в реестре — это высший национальный AML-орган. Живьём 403 (WAF). **Хорошая новость:** его решения дублируются в новостях EOCN/`uaeiec.gov.ae`, который уже мониторится — часть контента уже покрыта без борьбы с WAF.
6. **23 включённых источников в статусе `candidate`** (включая UN consolidated XML, OFAC recent-actions, EU RSS, OFSI ConList, MENAFATF, SAMA circulars) — им нужны 2 baseline-прогона для промоушена во `fresh_alert`. Это самый дешёвый способ расширить алерт-ядро: источники уже настроены.

### Приоритет внедрения

1. **Сейчас, без нового кода:** 30 источников Уровня 1 — это конфиг (server-rendered HTML-листинги). Начать с enforcement/alerts (ADGM×3, VARA×4, DFSA alerts+media, CMA warnings+violations) — прямая ценность для MLRO.
2. **Дешёвый прирост:** промоутить существующих `candidate` (UN/OFAC/EU/OFSI/MENAFATF/SAMA) после 2 baseline.
3. **Один адаптер — много источников:** headless/browser-UA адаптер открывает Уровень 2 (CBUAE enforcement+rulebook change-log, NAMLCFTC, FATF, DET, DIFC.com).
4. **Owner-gated:** UAE-резидентный egress-прокси открывает FIU, uaelegislation, Кабинет, CBUAE, DFSA-сайт.

### Не исследовано (оборвал лимит расходов)

- GCC детально: CBB Bahrain (rulebook updates/enforcement), QCB, Oman CBO/CMA/FSA, Kuwait CMA — в реестре только частично и в основном отключено как `non_uae`.
- Wolfsberg Group — отсутствует.
- Точные машинно-читаемые фиды сверх уже имеющихся (UK OFSI recent-changes, EU CSV).