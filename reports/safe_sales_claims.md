# StatuteProof Safe Sales Claims
Audit date: 2026-06-24

This document defines exactly what can and cannot be said in customer-facing copy, sales conversations, and pilot outreach. It is based on the actual state of sources.json (116 enabled), the source_signal_quality_audit.md report, the evidence record pipeline, and the current product state.

---

## Safe Homepage Wording

**Use:**
- "StatuteProof monitors selected official UAE regulatory sources and sends your team a brief when relevant text changes."
- "Selected-source UAE regulatory monitoring with an evidence trail on every run."
- "116 enabled official UAE sources monitored on a scheduled cycle."
- "SHA-256 hash and UTC timestamp on every monitoring run."
- "Human review gate before any brief is delivered to your team."
- "Sources monitored include: CBUAE, DFSA, ADGM / FSRA, VARA, UAE CMA, UAE FIU, FTA, MoE, DIFC, EOCN."
- "Every known access limitation is disclosed before your pilot begins."
- "Monitoring intelligence only. Not legal advice."
- "StatuteProof does not guarantee compliance or replace qualified legal counsel."

**Avoid:**
- "246 UAE sources monitored" — wrong
- "180 fresh-alert eligible sources" — stale, wrong
- "Complete UAE regulatory coverage"
- "Never miss a regulatory update"
- "Real-time monitoring" (it is scheduled batch)
- "Monitoring active" with a live dot implying real-time (misleading)
- "24h check cycle — every source, every day" (ambiguous — the default is hourly, not daily)

---

## Safe Dashboard Wording

**Use:**
- "Source run — [timestamp] — [source name]"
- "Status: CHANGED / UNCHANGED / FIRST_SEEN / FAILED"
- "Extraction quality: GOOD / LOW / QUALITY_DROP"
- "Evidence: SHA-256 hash [hash] at [timestamp UTC]"
- "This alert is PENDING HUMAN REVIEW — not approved for delivery"
- "Brief status: DRAFT — Human review required before delivery"
- "Selected-source monitoring — not complete UAE regulatory coverage"
- "Source readiness: [status] — [caveats if any]"

**Avoid:**
- "Monitoring active" live dot with no last-run timestamp
- Any count that does not match the current sources.json
- "Alert delivered" before human_reviewed: True
- "Evidence verified" before the canonical evidence gate passes

---

## Safe Pricing Wording

**Use:**
- "Source Readiness Review — Free — Before committing to monitoring, know exactly which UAE regulatory sources are accessible for your licence type."
- "Founding Pilot — $199/month — Up to 3 official UAE sources, manually activated after source readiness review."
- "UAE Monitor — $399/month — Selected fresh-alert eligible official UAE sources. Manually activated."
- "Founding pilots are manually activated after source readiness review."
- "Evidence records on every configured run."
- "Human review before brief delivery."
- "30-day evidence retention (Founding Pilot) / 180-day (UAE Monitor)."
- "No payment method stored until billing is formally set up."

**Avoid:**
- Payment CTAs that don't route to a real checkout (wire Stripe first)
- "Most popular" badge (no customer data)
- "Automated compliance monitoring" — the human review gate is mandatory
- Any SLA promise not confirmed in the .env configuration

---

## Safe Source Transparency Wording

**Use:**
- "We disclose source limits, failed extraction paths, and review gates before pilot activation."
- "The UAE Official Gazette and UAE e-Laws Portal are geo-IP restricted from outside the UAE and are not currently monitored."
- "UAE Legislation Portal is currently in remediation and is not counted as an active monitored source."
- "FIU circulars endpoint resolves to the general publications index and is not counted as a separate monitored source."
- "ADGM FSRA rulebook on Thomson Reuters platform has restricted external access — FSRA content is captured through official ADGM pages instead."
- "SCA has 6 proof-backed fresh-alert eligible sources. Broader UAE CMA coverage is actively expanding."
- "DIFC has 12 selected active sources including laws, data protection, and DFSA listing sources."
- "CBUAE has 25 active sources covering rulebook modules, licensing, and policy notices."
- "DFSA has 16 active sources covering rulebook modules, consultation papers, enforcement, and annual reports."

**Avoid:**
- "Full VARA coverage" — only 6 direct VARA sources enabled (though PDFs add depth)
- "Full DFSA coverage" — 28 static DFSA pages are evidence-library only, not fresh-alert
- "Complete FIU monitoring" — circulars are not covered
- "UAE Legislation Portal is active" — it is in remediation
- Any source count higher than the current sources.json enabled count

---

## Safe Pilot Outreach Wording

**Template A — VASP / Virtual Assets:**
> "StatuteProof monitors selected official VARA sources for virtual asset regulatory changes, including VARA's rulebook modules, licensing updates, enforcement notices, and revision history. When text changes on a monitored VARA source, your compliance team receives a reviewed brief with a source link, change context, and SHA-256 evidence record.
>
> This is selected-source VARA monitoring. It is not complete VARA regulatory coverage. We disclose all known access limitations before activation.
>
> Monitoring information only. Not legal advice."

**Template B — DFSA / DIFC firms:**
> "StatuteProof monitors selected DFSA and DIFC regulatory sources for compliance-relevant changes, including DFSA rulebook modules, consultation papers, enforcement decisions, and annual reports, plus DIFC laws and data protection sources. Evidence records with SHA-256 hashes and timestamps are generated on every run.
>
> 28 static DFSA detail pages remain evidence-library only and are not counted as active monitoring. We disclose all known access limitations before activation.
>
> Monitoring information only. Not legal advice."

**Template C — ADGM / FSRA firms:**
> "StatuteProof monitors 14 selected ADGM and FSRA regulatory sources, including FSRA rules and guidance, supervision circulars, public consultations, enforcement, data protection, and RA circulars. Evidence records are generated on every run.
>
> The ADGM FSRA dedicated regulatory-alerts listing is not yet active. We disclose all known access limitations before activation.
>
> Monitoring information only. Not legal advice."

**Template D — Banks / CBUAE-regulated:**
> "StatuteProof monitors 25 selected CBUAE regulatory sources, including rulebook modules for AML/CFT, consumer protection, open finance, payment token services, and risk management. Evidence records with SHA-256 hashes and timestamps are generated on every run.
>
> This is selected-source CBUAE monitoring. Not complete CBUAE regulatory coverage.
>
> Monitoring information only. Not legal advice."

**Template E — AML / Compliance teams:**
> "StatuteProof monitors selected UAE AML/CFT sources across CBUAE, DFSA, ADGM/FSRA, UAE FIU, EOCN, VARA, and MoE/DNFBP sources. When text changes on a monitored AML-relevant source, your MLRO or CCO receives a brief for review.
>
> UAE FIU circulars are not currently covered — the endpoint resolves to the general publications index. EOCN and UAE FIU publications hub are covered. All limitations are disclosed before pilot activation.
>
> Monitoring information only. Not legal advice."

---

## Required Disclaimers

### Full disclaimer (required on all briefs and evidence documents):
"StatuteProof reports are generated from monitored official-source records and are provided for information and compliance review support only. StatuteProof reports do not constitute legal advice, regulatory advice, compliance certification, or a legal opinion. StatuteProof does not replace qualified legal counsel, compliance professionals, MLROs, or other professional advisers. StatuteProof does not guarantee compliance, prevent fines, or certify that all regulatory updates have been captured. Source monitoring may be affected by publication delays, website changes, PDF formatting, access limits, or source structure changes. Users should verify official source material directly and review evidence records, hashes, timestamps, and diffs before relying on a report. Users should consult qualified legal or compliance professionals before making regulatory, filing, operational, or customer decisions based on a report."

### Short disclaimer (outreach, pricing pages):
"Monitoring information only. Not legal advice and not a guarantee of compliance."

### SAMPLE / FAKE label:
Any example brief, example evidence record, or example output that uses invented regulatory content must be labeled "SAMPLE / FAKE" near the top.

---

## Family-Specific Caveats

### VARA
"VARA monitoring covers selected official VARA sources including rulebook modules, licensing updates, enforcement notice listings, and revision history. VARA is selected-source monitoring only. Not complete VARA regulatory coverage."

### DFSA / DIFC
"DFSA monitoring covers 16 fresh-alert eligible sources including rulebook modules (via Thomson Reuters platform), consultation papers, enforcement decisions, AML reports, and annual reports. 28 static DFSA individual notice/news pages are evidence-library only and are not counted as monitored. DIFC monitoring covers 12 selected sources including laws, data protection, DIFC Courts practice directions, and the official DIFC Legal Database listing. Not complete DFSA or DIFC coverage."

### ADGM / FSRA
"ADGM/FSRA monitoring covers 14 selected sources including FSRA rules and regulations, guidance notes, supervision circulars, public consultations, RA circulars, enforcement, and data protection. The ADGM FSRA dedicated regulatory-alerts listing is a candidate pending selector remediation and is not counted as active. The FSRA rulebook on the Thomson Reuters platform (fsra.adgm.com) has restricted external access. Not complete ADGM/FSRA coverage."

### CBUAE
"CBUAE monitoring covers 25 selected sources including rulebook modules for AML/CFT, consumer protection, open finance, payment token services, risk management, model management standards, exchange business regulation, retail payment services, and related guidance. The CBUAE main homepage and generic regulations listing are evidence-library only. Not complete CBUAE regulatory coverage."

### UAE FIU
"UAE FIU monitoring covers the publications hub, typology reports, AML/CFT laws, selected system guides, knowledge centre, and public notices. The FIU circulars page currently resolves to the general publications index and is not counted as a separate monitored source. UAE FIU Homepage is evidence-library only. Not complete FIU coverage."

### UAE CMA / SCA
"UAE CMA/SCA monitoring covers 6 selected proof-backed sources including the regulations listing, selected circulars/rules/procedures, and AML/CFT sources. UAE CMA root portal monitoring and broader UAE CMA coverage are actively expanding. SCA AML/CFT parser/noise review is in progress. Not complete UAE CMA coverage."

### FTA
"FTA monitoring covers 6 selected fresh-alert eligible sources. 25 direct official FTA PDF endpoints are fresh-alert eligible (counted in MoF family). Broader FTA portal/listing extraction is candidate/roadmap. Not complete FTA coverage."

### MoE / DNFBP
"MoE/DNFBP AML monitoring covers 9 selected sources including DNFBP licensing, AML guidance, and commercial regulation. Not complete MoE coverage."

### EOCN / TFS
"EOCN/TFS monitoring covers 5 selected sources related to AML/CFT laws, regulations, and targeted financial sanctions support. Not complete sanctions or TFS coverage. Not a sanctions screening service."

### Official Gazette / UAE Legislation
"The UAE Official Gazette (Al-Jaridah Al-Rasmiah) and UAE e-Laws Portal are geo-IP blocked from outside the UAE and are not currently monitored. One selected UAE Legislation Platform listing source is active for monitoring. Not complete UAE legislation or Official Gazette coverage. Federal legislation/gazette monitoring is not sold as ready."

---

## Forbidden Claims — Verbatim Examples Found in Current Code

These specific strings appear in the current codebase and must be corrected or removed:

1. `totalEnabled: 246` in `sourceQualityAudit.ts` — wrong count
2. `freshAlertEligible: 180` in `sourceQualityAudit.ts` — wrong count
3. `sourceLevelMonitorOk: 234` in `sourceQualityAudit.ts` — wrong count
4. `withProofPath: 237` in `sourceQualityAudit.ts` — wrong count
5. `sourceCount: '24 fresh-alert eligible'` for VARA in `SourceTransparencyMatrix.jsx` — internal audit says 25
6. `sourceCount: '10 fresh-alert eligible'` for ADGM in `SourceTransparencyMatrix.jsx` — internal audit says 11
7. `sourceCount: '26 fresh-alert eligible across DIFC/DFSA'` in `SourceTransparencyMatrix.jsx` — internal audit says 16+11=27
8. `sourceCount: '0 fresh-alert eligible'` for Legislation in `SourceTransparencyMatrix.jsx` while `BuyerSourcePacks.jsx` says "UAE Legislation Portal and Dubai Legislation Portal are fresh-alert eligible"
9. `"Monitoring active"` live dot — implies real-time; is actually scheduled batch

---

*This document was generated from the 2026-06-24 project audit. Update when source counts or product state changes.*
