// Buyer-facing source packs by licence type.
//
// SINGLE SOURCE OF TRUTH for the public "Source packs by licence type" section.
// Every layer's `sourceIds` MUST trace to a real entry in
// product/regradar/sources.json. The drift-guard test in `sourcePacks.test.js`
// fails the build if any id is missing or if a status no longer matches the
// real monitoring state — so this file cannot silently over-claim.
//
// Honesty rules (see CLAUDE.md):
//   - `active`      => source is ENABLED, monitoring_mode === 'fresh_alert',
//                      alert_eligible === true (a real fresh-alert source).
//   - `pending`     => source is ENABLED but not yet fresh-alert eligible
//                      (candidate / awaiting proof-backed baseline).
//   - `roadmap`     => source is CONFIGURED but not enabled (not yet activated).
//   - `geo_blocked` => source is geo-restricted / under remediation and is
//                      DOCUMENTED here, not hidden and never counted as active.
//   - `evidence`    => evidence-library-only snapshot, not a fresh-alert source.
//   - `out_of_scope`=> explicitly outside current monitoring scope.
//
// Never mark a source `active` unless it is genuinely fresh-alert eligible.

/**
 * @typedef {'active'|'pending'|'roadmap'|'geo_blocked'|'evidence_only'|'out_of_scope'} LayerStatus
 * @typedef {{ text: string, status: LayerStatus, sourceIds: string[] }} SourceLayer
 * @typedef {{
 *   profile: string,
 *   bestFor: string,
 *   coverage: 'strong'|'good'|'partial'|'limited',
 *   layers: SourceLayer[],
 *   caveat: string | null,
 * }} SourcePack
 */

/** @type {SourcePack[]} */
export const SOURCE_PACKS = [
  {
    profile: "VASP / Crypto",
    bestFor:
      "Exchanges, brokers, custodians, token projects and VASP compliance teams",
    coverage: "good",
    layers: [
      {
        text: "VARA Rulebook revision updates — live index of rulebook changes",
        status: "active",
        sourceIds: ["AE-vara-rulebook-updates"],
      },
      {
        text: "VARA news, circulars and regulatory publications",
        status: "active",
        sourceIds: ["AE-vara-news-circulars-listing"],
      },
      {
        text: "VARA enforcement notices index",
        status: "active",
        sourceIds: ["AE-vara-enforcement"],
      },
      {
        text: "CBUAE Payment Token Services Regulation",
        status: "active",
        sourceIds: ["AE-cbuae-payment-token-services-rulebook"],
      },
      {
        text: "UAE CMA (formerly SCA) circulars, rules and regulations listing",
        status: "active",
        sourceIds: [
          "AE-sca-circulars-rules-procedures",
          "AE-sca-regulations-listing",
        ],
      },
      {
        text: "UAE Executive Office (EOCN) AML/CFT laws and sanctions / TFS updates",
        status: "active",
        sourceIds: ["AE-eocn-laws-regulations-en", "AE-eocn-news-en"],
      },
      {
        text: "VARA public register of licensed entities",
        status: "pending",
        sourceIds: ["AE-vara-public-register-licensed-entities"],
      },
      {
        text: "VARA homepage — archived as an evidence snapshot",
        status: "evidence_only",
        sourceIds: ["AE-dubai-virtual-assets-regulatory-authority-vara"],
      },
      {
        text: "UAE FIU publications hub and typology reports",
        status: "geo_blocked",
        sourceIds: ["AE-uaefiu-publications-hub", "AE-uaefiu-typology-reports"],
      },
    ],
    caveat:
      "VARA monitoring covers 3 selected fresh-alert sources (rulebook updates, news/circulars, enforcement) — selected-source monitoring, not complete VARA coverage. The UAE FIU knowledge centre (uaefiu.gov.ae) is geo-restricted from outside the UAE and is not currently delivered as fresh alerts.",
  },
  {
    profile: "Payments & Fintech",
    bestFor:
      "Payment firms, stored value providers, fintech operators and compliance advisers",
    coverage: "strong",
    layers: [
      {
        text: "CBUAE Rulebook Revision Updates — master change index across modules",
        status: "active",
        sourceIds: ["AE-cbuae-rulebook-revision-updates"],
      },
      {
        text: "CBUAE Retail Payment Services and Card Schemes Regulation",
        status: "active",
        sourceIds: ["AE-cbuae-retail-payment-services-rulebook"],
      },
      {
        text: "CBUAE Stored Value Facilities and Retail / Large Value Payment Systems regulations",
        status: "active",
        sourceIds: [
          "AE-cbuae-stored-value-facilities-doclist",
          "AE-cbuae-retail-payment-systems-regulation-doclist",
          "AE-cbuae-large-value-payment-systems-doclist",
        ],
      },
      {
        text: "CBUAE Open Finance and Payment Token Services regulations",
        status: "active",
        sourceIds: [
          "AE-cbuae-open-finance-rulebook",
          "AE-cbuae-payment-token-services-rulebook",
        ],
      },
      {
        text: "DFSA and UAE CMA fintech / innovation sandbox pages",
        status: "active",
        sourceIds: ["AE-dfsa-innovation-59c1dc61", "AE-sca-fintech-sandbox"],
      },
      {
        text: "UAE Executive Office (EOCN) AML/CFT and sanctions updates",
        status: "active",
        sourceIds: ["AE-eocn-laws-regulations-en", "AE-eocn-news-en"],
      },
      {
        text: "UAE Legislation Portal — federal law texts and Official Gazette",
        status: "geo_blocked",
        sourceIds: ["AE-uae-legislation-portal"],
      },
    ],
    caveat:
      "CBUAE monitoring uses the rulebook.centralbank.ae subdomain; the main centralbank.ae domain is geo-restricted from outside the UAE. The UAE Legislation Portal is geo-restricted and under remediation — documented, not delivered.",
  },
  {
    profile: "DIFC / DFSA",
    bestFor:
      "DIFC regulated firms, funds, advisers, law firms and compliance consultants",
    coverage: "strong",
    layers: [
      {
        text: "DFSA Rulebook modules, including the AML/CTF & Sanctions module",
        status: "active",
        sourceIds: [
          "AE-dfsa-rulebook-thomsonreuters",
          "AE-dfsa-aml-rulebook-module",
        ],
      },
      {
        text: "DFSA laws, rules and legal resources",
        status: "active",
        sourceIds: [
          "AE-dfsa-rulebook-official",
          "AE-dfsa-laws-rules-2dee8ba9",
          "AE-dfsa-laws-rules-legal-resources-3dc15494",
        ],
      },
      {
        text: "DFSA consultation papers and enforcement / regulatory actions",
        status: "active",
        sourceIds: [
          "AE-dfsa-consultation-current",
          "AE-dfsa-regulatory-actions-current",
          "AE-dfsa-what-we-do-enforcement-1a837c50",
        ],
      },
      {
        text: "DFSA financial crime prevention notices and MLRO letters",
        status: "active",
        sourceIds: ["AE-dfsa-financial-crime-mlro-letters"],
      },
      {
        text: "DIFC Laws and Regulations and DIFC Legal Database listing",
        status: "active",
        sourceIds: ["AE-difc-laws-and-regulations", "AE-difc-legal-database"],
      },
      {
        text: "DIFC AML/CFT, Economic Substance and legal notices",
        status: "active",
        sourceIds: [
          "AE-difc-business-aml-cft-991d9543",
          "AE-difc-business-economic-substance-regulations-05c9f19b",
          "AE-difc-static-legal-notices-9f800f67",
        ],
      },
      {
        text: "DFSA News Hub and SEO letters",
        status: "pending",
        sourceIds: [
          "AE-dfsa-news-hub-legislative-amendment-notices",
          "AE-dfsa-seo-letters",
        ],
      },
      {
        text: "DIFC Courts practice and registrar directions",
        status: "pending",
        sourceIds: [
          "AE-difc-courts-practice-directions",
          "AE-difc-courts-registrar-s-directions",
        ],
      },
    ],
    caveat:
      "Selected-source DIFC/DFSA monitoring covers 21 fresh-alert sources. The DFSA News Hub / SEO letters and DIFC Courts direction pages are enabled but not yet fresh-alert eligible (pending validation). This is not complete DIFC legal-database coverage.",
  },
  {
    profile: "ADGM / FSRA",
    bestFor:
      "ADGM regulated firms, funds, securities teams and regulatory advisers",
    coverage: "good",
    layers: [
      {
        text: "ADGM FSRA Rules and Regulations",
        status: "active",
        sourceIds: ["AE-adgm-fsra-rulebooks"],
      },
      {
        text: "ADGM FSRA Guidance and Policy Statements",
        status: "active",
        sourceIds: ["AE-adgm-fsra-guidance-policy"],
      },
      {
        text: "ADGM FSRA Listing Authority rules and guidance",
        status: "active",
        sourceIds: ["AE-adgm-listing-rules"],
      },
      {
        text: "ADGM FSRA supervision circulars and public consultations",
        status: "active",
        sourceIds: [
          "AE-adgm-fsra-supervision-circulars",
          "AE-adgm-fsra-consultations",
        ],
      },
      {
        text: "ADGM FSRA financial and cyber crime prevention (AML/CFT)",
        status: "active",
        sourceIds: ["AE-adgm-fsra-financial-crime-prevention"],
      },
      {
        text: "ADGM Courts legislation, procedures, forms and guides",
        status: "active",
        sourceIds: [
          "AE-adgm-adgm-courts-legislation-and-procedures-66abfd89",
          "AE-adgm-adgm-courts-forms-fees-and-guides-a3b9d695",
        ],
      },
      {
        text: "ADGM Office of Data Protection — guidance",
        status: "active",
        sourceIds: ["AE-adgm-dp-guidance"],
      },
      {
        text: "ADGM FSRA regulatory alerts, waivers register and RA circulars",
        status: "pending",
        sourceIds: [
          "AE-adgm-fsra-regulatory-alerts",
          "AE-adgm-fsra-waivers",
          "AE-adgm-ra-circulars",
        ],
      },
      {
        text: "ADGM media announcements hub and Office of Data Protection index",
        status: "pending",
        sourceIds: [
          "AE-adgm-media-announcements-hub",
          "AE-adgm-office-of-data-protection",
        ],
      },
    ],
    caveat:
      "ADGM/FSRA covers 9 selected fresh-alert sources. The FSRA regulatory-alerts page, waivers/modifications register, RA circulars, media hub and Office of Data Protection index are enabled but held as candidate/pending until extraction passes proof-backed baseline — disclosed, not counted as active.",
  },
  {
    profile: "AML / Sanctions",
    bestFor:
      "MLROs, AML consultants, onboarding teams and regulated financial firms",
    coverage: "strong",
    layers: [
      {
        text: "UAE Executive Office (EOCN / UAEIEC) AML/CFT laws, sanctions and TFS updates",
        status: "active",
        sourceIds: [
          "AE-eocn-laws-regulations-en",
          "AE-eocn-news-en",
          "AE-uaeiec-en-us-laws-regulations-listing-00a71863",
          "AE-eocn-tfs",
          "AE-uaeiec-news-listing-next",
        ],
      },
      {
        text: "CBUAE AML/CFT rulebook, proliferation-finance and TBML guidance",
        status: "active",
        sourceIds: [
          "AE-cbuae-amlcft-rulebook-doclist",
          "AE-cbuae-amlcft-entire-section-doclist",
          "AE-cbuae-proliferation-finance-guidance-doclist",
          "AE-cbuae-tbml-transshipment-guidance-doclist",
        ],
      },
      {
        text: "Ministry of Economy DNFBP AML, targeted financial sanctions and goAML registration",
        status: "active",
        sourceIds: [
          "AE-moet-aml-170b7988",
          "AE-moet-targeted-financial-sanctions-586d6f96",
          "AE-moet-registering-companies-in-goaml-c83375da",
        ],
      },
      {
        text: "DFSA and ADGM financial-crime / MLRO and AML rulebook sources",
        status: "active",
        sourceIds: [
          "AE-dfsa-aml-rulebook-module",
          "AE-dfsa-financial-crime-mlro-letters",
          "AE-adgm-fsra-financial-crime-prevention",
        ],
      },
      {
        text: "UAE CMA and DIFC AML/CFT obligation pages",
        status: "active",
        sourceIds: ["AE-sca-aml-cft", "AE-difc-business-aml-cft-991d9543"],
      },
      {
        text: "UAE FIU publications hub, typology reports and AML/CFT laws",
        status: "geo_blocked",
        sourceIds: [
          "AE-uaefiu-publications-hub",
          "AE-uaefiu-typology-reports",
          "AE-uaefiu-aml-cft-laws",
        ],
      },
    ],
    caveat:
      "AML monitoring draws on the UAE Executive Office (EOCN), Ministry of Economy DNFBP sources, and the AML/CFT modules of CBUAE, DFSA, ADGM, UAE CMA and DIFC. The UAE FIU (uaefiu.gov.ae) knowledge centre is geo-restricted from outside the UAE and under remediation — documented, not delivered as fresh alerts.",
  },
  {
    profile: "Tax / Corporate",
    bestFor:
      "Finance teams, tax advisers, corporate service providers and legal teams",
    coverage: "good",
    layers: [
      {
        text: "UAE Ministry of Finance corporate tax and Domestic Minimum Top-up Tax (DMTT)",
        status: "active",
        sourceIds: ["AE-mof-corporate-tax-in-the-uae", "AE-mof-top-up-tax"],
      },
      {
        text: "UAE Ministry of Finance AEOI / FATCA / CRS and Economic Substance Regulations",
        status: "active",
        sourceIds: ["AE-mof-aeoi-fatca-crs", "AE-mof-esr"],
      },
      {
        text: "UAE Ministry of Finance financial legislation, publications and financial framework",
        status: "active",
        sourceIds: [
          "AE-mof-financial-legislation",
          "AE-mof-publications-and-releases",
          "AE-mof-uae-financial-framework",
        ],
      },
      {
        text: "UAE CMA FATCA/CRS guidance and DIFC / MoE Economic Substance pages",
        status: "active",
        sourceIds: [
          "AE-sca-fatca-crs",
          "AE-difc-business-economic-substance-regulations-05c9f19b",
          "AE-moet-economic-substance-regulations-a5b9825b",
        ],
      },
      {
        text: "Ministry of Economy — business regulation, competition and auditing legislation",
        status: "active",
        sourceIds: [
          "AE-moet-regulation-of-business-fd17959e",
          "AE-moet-regulation-of-competition-ba53cc4c",
          "AE-moet-auditing-accounts-legislations-84d91bc4",
        ],
      },
      {
        text: "FTA legislation, VAT and Corporate Tax listing pages",
        status: "pending",
        sourceIds: [
          "AE-fta-tax-legislation-listing",
          "AE-fta-vat-guides-references",
          "AE-fta-corporate-tax-guides-references",
          "AE-fta-corporate-tax-legislation",
        ],
      },
      {
        text: "UAE Legislation Portal — federal law texts and Official Gazette",
        status: "geo_blocked",
        sourceIds: ["AE-uae-legislation-portal"],
      },
      {
        text: "Dubai Legislation Portal — Dubai local laws and executive decisions",
        status: "pending",
        sourceIds: ["AE-dubai-legislation-portal-laws-search"],
      },
    ],
    caveat:
      "Tax coverage is anchored on 7 fresh-alert Ministry of Finance sources (corporate tax, DMTT, AEOI/FATCA/CRS, ESR, financial legislation, framework). FTA listing pages currently return nav-shell content and are held as candidate; direct FTA decision PDFs are configured and proof-backed but not yet activated. The UAE Legislation Portal is geo-restricted and under remediation; the Dubai Legislation Portal is enabled but not yet fresh-alert eligible. Not complete tax or Official Gazette coverage.",
  },
  {
    profile: "Data Protection",
    bestFor:
      "Privacy teams, DIFC/ADGM firms, legal teams and data protection leads",
    coverage: "good",
    layers: [
      {
        text: "DIFC Commissioner of Data Protection — guidance and supervision / enforcement",
        status: "active",
        sourceIds: [
          "AE-difc-data-protection-commissioner",
          "AE-difc-data-protection-supervision-enforcement",
          "AE-difc-data-protection-guidance",
        ],
      },
      {
        text: "DIFC Data Protection Regulation 10",
        status: "active",
        sourceIds: ["AE-difc-data-protection-regulation-10"],
      },
      {
        text: "ADGM Office of Data Protection — guidance",
        status: "active",
        sourceIds: ["AE-adgm-dp-guidance"],
      },
      {
        text: "ADGM Office of Data Protection — regulations and enforcement index",
        status: "pending",
        sourceIds: ["AE-adgm-office-of-data-protection"],
      },
      {
        text: "UAE federal PDPL (TDRA / UAE Data Office)",
        status: "pending",
        sourceIds: ["AE-tdra-uae-media-centre"],
      },
    ],
    caveat:
      "DIFC and ADGM data-protection sources are fresh-alert eligible where proof-backed. No dedicated UAE federal PDPL (Personal Data Protection Law) text source is currently fresh-alert eligible — the enabled TDRA media page is held pending validation. Selected-source monitoring, not complete data-protection coverage.",
  },
  {
    profile: "Banking & Prudential (CBUAE)",
    bestFor:
      "Banks, finance companies, exchange houses and prudential risk / compliance teams",
    coverage: "strong",
    layers: [
      {
        text: "CBUAE Rulebook Revision Updates — master change index",
        status: "active",
        sourceIds: ["AE-cbuae-rulebook-revision-updates"],
      },
      {
        text: "Capital Adequacy, Large Exposures, Market and Operational Risk regulations",
        status: "active",
        sourceIds: [
          "AE-cbuae-capital-adequacy-doclist",
          "AE-cbuae-large-exposures-regulation-doclist",
          "AE-cbuae-market-risk-regulation-doclist",
          "AE-cbuae-operational-risk-regulation-doclist",
        ],
      },
      {
        text: "Risk Management, Country & Transfer Risk and Interest-Rate Risk regulations",
        status: "active",
        sourceIds: [
          "AE-cbuae-risk-management-rulebook",
          "AE-cbuae-country-transfer-risk-regulation-doclist",
          "AE-cbuae-interest-rate-risk-regulation-doclist",
        ],
      },
      {
        text: "Consumer Protection, SME Customer Protection and Market Conduct regulations",
        status: "active",
        sourceIds: [
          "AE-cbuae-consumer-protection-rulebook-doclist",
          "AE-cbuae-sme-customer-protection-regulation-doclist",
          "AE-cbuae-market-conduct-consumer-protection-doclist",
        ],
      },
      {
        text: "Exchange Business, Model Management and Islamic Banks risk standards",
        status: "active",
        sourceIds: [
          "AE-cbuae-exchange-business-regulation-doclist",
          "AE-cbuae-model-management-standards-doclist",
          "AE-cbuae-islamic-banks-risk-management-doclist",
        ],
      },
      {
        text: "Federal Decree-Law No. 6 of 2025 (Central Bank & financial institutions)",
        status: "active",
        sourceIds: ["AE-cbuae-federal-decree-law-6-2025-doclist"],
      },
      {
        text: "CBUAE main centralbank.ae domain (regulations, circulars, publications)",
        status: "geo_blocked",
        sourceIds: ["AE-central-bank-of-the-uae", "AE-cbuae-regulations"],
      },
    ],
    caveat:
      "CBUAE monitoring covers 25 fresh-alert rulebook and regulation modules on the rulebook.centralbank.ae subdomain. The main centralbank.ae domain (regulations, circulars, publications, licensing) is geo-restricted from outside the UAE — documented, not delivered. Selected-source monitoring, not complete CBUAE coverage.",
  },
  {
    profile: "Capital Markets",
    bestFor:
      "Securities firms, listed companies, investment funds and capital-market advisers",
    coverage: "good",
    layers: [
      {
        text: "UAE CMA circulars, rules and procedures",
        status: "active",
        sourceIds: ["AE-sca-circulars-rules-procedures"],
      },
      {
        text: "UAE CMA regulations listing",
        status: "active",
        sourceIds: ["AE-sca-regulations-listing"],
      },
      {
        text: "UAE CMA corporate governance regulations",
        status: "active",
        sourceIds: ["AE-sca-corporate-governance"],
      },
      {
        text: "UAE CMA FATCA / CRS guidance and AML/CFT",
        status: "active",
        sourceIds: ["AE-sca-fatca-crs", "AE-sca-aml-cft"],
      },
      {
        text: "UAE CMA FinTech Regulatory Sandbox",
        status: "active",
        sourceIds: ["AE-sca-fintech-sandbox"],
      },
      {
        text: "ADGM FSRA Listing Authority rules and guidance",
        status: "active",
        sourceIds: ["AE-adgm-listing-rules"],
      },
      {
        text: "Dubai Financial Market (DFM) regulatory circulars",
        status: "pending",
        sourceIds: ["AE-dfm-regulatory-circulars"],
      },
    ],
    caveat:
      "UAE CMA (the successor to the Securities and Commodities Authority) coverage spans 6 selected fresh-alert sources. The uaecma.gov.ae root portal and full UAE CMA coverage are not claimed. DFM regulatory circulars are enabled but not yet fresh-alert eligible (pending).",
  },
];
