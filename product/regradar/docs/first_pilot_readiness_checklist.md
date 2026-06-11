# First Pilot Readiness Checklist

---

## 1. Product readiness

- [x] All 9 commercial priority source packs completed (UAE, SA, QA, BH, HK, MY, SG, TR, KZ)
- [x] Full health refresh completed — 96 sources PASS, 0 FAIL (2026-05-27)
- [x] Overall coverage score: 90 (up from 69)
- [x] Contact form works and queues requests (smoke tested locally)
- [x] Source proof visible on landing page (Interactive Demo + SourceProofPanel)
- [x] Coverage disclaimers documented and visible in product
- [x] Claims are honest — no overclaims in copy
- [ ] Site deployed on a public URL with HTTPS
- [ ] Production contact delivery smoke test passed (Telegram confirmed)

---

## 2. What we can safely claim

Use careful, source-backed language in all outreach and demos.

**Safe language:**
> "RegRadar monitors validated official regulatory sources across UAE, Saudi Arabia, Qatar, Bahrain, Hong Kong, Malaysia, Singapore, Turkey, and Kazakhstan — with source proof, documented coverage, and disclosed limitations."

> "Each source is individually validated. We show you which official URL the alert came from and when it was extracted."

> "Coverage is strong in most markets. Saudi Arabia and Qatar have known monitoring gaps due to government geo-restrictions. These are disclosed in full."

**Safe framing for demos:**
- "Here are the exact sources we monitor, with extraction quality confirmed."
- "When we detect a change, we show you the source URL and the extracted text."
- "We are not a news aggregator — every alert links to official government or regulatory publications."

---

## 3. What we must NOT claim

- Complete or exhaustive regulatory coverage in any market
- That we will never miss an update
- Coverage of all regulations, statutes, or enforcement actions
- Legal advice or compliance sign-off of any kind
- Guaranteed alerting within a specific time window
- Coverage of geo-blocked sources (SA gazette, SA FIU, QA central bank, UAE FTA, etc.) — these are disabled and documented

---

## 4. Demo-ready markets and status

| Market | Score | Status | Caveats to disclose |
|--------|-------|--------|---------------------|
| UAE | 100 strong | ✅ Full demo | FTA (tax), Official Gazette, TDRA, GCA Customs are geo-blocked |
| Hong Kong | 94 strong | ✅ Full demo | PCPD (data protection) needs adapter; HK Gazette needs adapter |
| Bahrain | 88 strong | ✅ Full demo | FIU/AML domains DNS-dead; NCSC not confirmed |
| Malaysia | 92 strong | ✅ Full demo | Standalone FIU not active; Customs SPA; Federal Gazette DNS-dead |
| Singapore | 100 strong | ✅ Full demo | No material gaps |
| Turkey | 100 strong | ✅ Full demo | No material gaps |
| Kazakhstan | 100 strong | ✅ Full demo | No material gaps |
| Qatar | 100 limited | ⚠️ Demo with caveats | QCB (central bank) + QFMA (securities) inaccessible; MoJ/Customs SSL failures |
| Saudi Arabia | 100 limited | ⚠️ Demo with caveats | SAFIU, Umm Al-Qura (gazette), BOE (legal database), SDAIA (data protection), Istitlaa — all geo-blocked |

**GCC4 bundle pitch:** UAE + Saudi Arabia + Qatar + Bahrain — four markets, one subscription, disclosed limitations.  
**SEA pair pitch:** Singapore + Malaysia — both confirmed strong.

---

## 5. Caveats to disclose per market

### Saudi Arabia
- SAFIU (AML/financial intelligence unit): geo-blocked — not monitored
- Umm Al-Qura (official gazette): geo-blocked — new laws/royal decrees not tracked at source
- Bureau of Experts / laws.boe.gov.sa (legal database): geo-blocked — not accessible
- SDAIA (data protection authority): HTTP2 protocol block — not accessible
- Ministry of Finance portal: SPA — not accessible

*What is covered:* SAMA (central bank + banking + insurance + payments), ZATCA (tax/customs), CMA (capital markets), MISA (investment), Ministry of Commerce, NCA (cybersecurity), CST (digital regulation — limited).

### Qatar
- Qatar Central Bank (QCB): SSL certificate failure — central bank regulatory publications not monitored
- QFMA (capital markets authority): SPA — securities regulatory publications not accessible
- Ministry of Justice / official gazette: DNS failure
- General Customs Authority: SSL failure

*What is covered:* QFCRA (financial regulation), QFC (free zone), MoF, GTA (tax), MOCI (company/commerce), Al-Meezan (legislation), QFIU (AML/FIU), NCSA (cybersecurity), CRA (digital regulation).

### Malaysia
- No standalone FIU/AML source — BNM covers financial-sector AML/CFT policy only
- Federal Gazette: DNS failure — not monitored
- Customs department: SharePoint SPA — not accessible
- Ministry of Finance (mof.gov.my): SPA — Budget Portal (belanjawan) is activated instead

### Bahrain
- Bahrain FIU: all tested domains DNS-dead or geo-blocked — AML not monitored at FIU level
- CBB covers banking-sector AML supervision; not a replacement for standalone FIU monitoring
- NCSC: not yet confirmed or activated

### Hong Kong
- PCPD (data protection): navigation adapter required — not activated
- HK Government Gazette: limited (991c) — not activated as primary source
- No dedicated crypto-exchange regulatory feed (SFC covers crypto as capital markets)

### UAE
- UAE Federal Tax Authority (FTA): geo-blocked — UAE tax monitoring not active
- UAE Official Gazette (uag.gov.ae): geo-blocked
- TDRA (telecom/data): geo-blocked
- GCA Customs: geo-blocked

---

## 6. Ideal first pilot customer profiles

**Highest priority:**
1. **Fintech startup with GCC or SEA market entry** — needs BNM, CBUAE, VARA, CBB, MAS regulatory monitoring
2. **Crypto / VASP advisory firm** — SC Malaysia (DAX), CBB Bahrain Volume 8, VARA UAE, SFC Hong Kong are all active
3. **Compliance consultant serving financial institutions** — all 9 markets covered; source proof strengthens client deliverables
4. **GCC-focused law firm or Big 4 team** — GCC4 bundle (UAE+SA+QA+BH) with disclosed limitations is a credible offering
5. **Payments company expanding in SEA** — BNM Malaysia + MAS Singapore + HKMA regulatory feeds

**Good secondary profiles:**
- Investment manager or asset manager with SEA/GCC fund mandates
- Data protection / privacy compliance team (PDPA Malaysia, PDPL Bahrain, PDPC Singapore, JPDP Malaysia)
- Market entry advisor for companies entering Middle East or ASEAN

---

## 7. Pilot offer structure

**Recommended pitch:**

> "Let us run a 2-week pilot for your team. We'll configure a watchlist for your specific markets and topic areas, deliver source-backed regulatory alerts, and provide a weekly summary brief."

**Pilot components:**
- 3–5 target markets from our covered set
- Custom watchlist: select from sectors (banking, fintech, AML, data protection, tax, etc.)
- Official-source alerts: each alert includes source URL, extraction date, and relevant text
- Source proof: every alert cites which official publication it came from
- Weekly brief: compiled summary of significant updates
- 1 feedback call at end of pilot (30 min)
- Priced at: \[your call — suggest free or $200–500 for 2 weeks to qualify seriousness\]

**Pilot success criteria:**
- Pilot user confirms at least 2–3 alerts were genuinely relevant to their work
- Pilot user receives alerts they would not have found manually within a reasonable time
- Pilot user asks to add a market, source, or topic (signals product fit)
- Pilot user agrees to continue on a paid basis or refer a colleague

---

## 8. First outreach checklist

Before contacting a prospect:

- [ ] Site is live on HTTPS URL
- [ ] Contact form smoke test passed (Telegram confirmed)
- [ ] Source proof is visible on landing page
- [ ] Coverage disclaimers are visible on landing page
- [ ] Pilot offer structure is prepared
- [ ] Market-specific caveats are ready to disclose honestly
- [ ] No overclaims in outreach message
- [ ] Outreach message focuses on "source-backed, documented, honest" — not "complete" or "all-in-one"
