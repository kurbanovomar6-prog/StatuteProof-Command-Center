# UAE Coverage Public Claim Safety Table

Date: 2026-06-17
Purpose: Definitive reference for what can and cannot be claimed publicly about StatuteProof UAE coverage.

Legend:
- SAFE: Use now without modification.
- CONDITIONAL: Safe only with the accompanying disclaimer, in the required context, with the exact wording.
- NO: Never use. Forbidden phrase. Remove immediately if found in any document.

---

## Claim Safety Table

| # | Proposed Claim | Safe? | Why | Required Evidence | Safer Wording |
|---|---------------|-------|-----|-------------------|---------------|
| 1 | "78 readiness-supported UAE sources" | **SAFE** | Exact count from sources.json; factual and verifiable | sources.json enabled=true, status=active | "78 readiness-supported UAE official-source endpoints as of [date]" |
| 2 | "79 enabled UAE sources" | **SAFE** | Exact enabled count from sources.json | sources.json enabled=true count | "79 enabled UAE official-source endpoints" |
| 3 | "200+ official-source candidates mapped" | **SAFE** | 203 records in uae_source_universe_candidates.json; "mapped" ≠ "monitored" | uae_source_universe_candidates.json; validator passes | "StatuteProof has mapped 200+ official or officially linked UAE regulatory source candidates for pipeline research" |
| 4 | "Major UAE regulator coverage" | **CONDITIONAL** | All 8 named regulators have ≥5 active sources. But VARA guidance is broken, SCA lacks primary legislation. | All 8 regulators verified in sources.json; disclaimer required | "StatuteProof monitors selected official sources from major UAE regulatory bodies including CBUAE, DFSA, ADGM/FSRA, VARA, UAE FIU, EOCN, SCA, and DIFC. Selected sources only — not all publications from each body." |
| 5 | "Broad UAE compliance monitoring" | **CONDITIONAL** | "Broad" is safe if followed by scope qualifier. Not safe as standalone claim. | Disclaimer required; source count context required | "StatuteProof provides broad UAE official-source monitoring across major financial, AML/CFT, virtual asset, securities, and financial free-zone regulatory families. Monitoring intelligence only — not legal advice." |
| 6 | "Comprehensive UAE official-source universe" | **NO** (current state) / **CONDITIONAL** (post-P0 sprint) | VARA guidance broken; SCA laws missing; FTA 0 active; CBUAE consultations missing. After P0 sprint resolves those 6 gaps, conditional use is acceptable with disclaimer. | 6 specific P0 activations required; disclaimer required | After P0 sprint: "StatuteProof monitors selected official sources across all major UAE financial regulatory families. Coverage notes and source-health status shown transparently." |
| 7 | "Complete UAE coverage" | **NO** | 0 FTA sources; VARA guidance broken; MoJ not active; customs not mapped; recall rate not measured; <3 months monitoring history. Never acceptable as standalone claim. | Never achievable as standalone claim | Replace with: "Selected UAE official-source monitoring. Coverage scope and source-health shown transparently. Not comprehensive. Not guaranteed." |
| 8 | "All UAE regulatory updates" | **NO** | "All" implies 100% recall rate. Not measured. Not achievable. | Never achievable | Replace with: "Monitoring selected official UAE regulatory sources. StatuteProof does not capture all regulatory publications and does not guarantee completeness." |
| 9 | "Never miss updates" | **NO** | Absolute claim. Cannot be supported by any source monitoring system. Forbidden phrase per CLAUDE.md. | Never achievable | Replace with: "Designed to detect changes to monitored official sources. Source monitoring may be affected by access restrictions, website changes, PDF formatting changes, and publication delays." |
| 10 | "Monitoring intelligence only" | **SAFE** | Accurate descriptor of the product's scope. No legal advice implied. | Use exactly as written | "Monitoring intelligence only. Not legal advice." |
| 11 | "Not legal advice" | **SAFE** | Accurate and required. Must appear on all customer-facing materials. | Must be present on all outputs | "StatuteProof reports are monitoring intelligence only and do not constitute legal advice, regulatory advice, compliance certification, or a legal opinion." |
| 12 | "Source-health and gaps shown transparently" | **SAFE** | Source health visibility is implemented (status, remediation, quality scores). Gap documentation exists. | sources.json status fields; uae_source_universe_candidates.json gap documentation | "StatuteProof shows source readiness status, extraction quality, evidence hashes, source-health risk, and known gaps transparently." |
| 13 | "Evidence-backed compliance monitoring" | **CONDITIONAL** | "Evidence-backed" is safe if referring to the cryptographic hash and proof artifact system. Not safe if implying the evidence proves compliance. | Proof artifacts exist in product; SHA-256 hashes implemented | "StatuteProof stores cryptographic evidence records — hashes, timestamps, diffs, and proof artifacts — for each monitored source. Evidence records are for review support only and do not constitute compliance certification." |
| 14 | "AML/CFT monitoring across all major UAE regulators" | **CONDITIONAL** | Mostly true but VARA AML/CFT live page is broken. Must not claim VARA AML guidance is covered. | After VARA AML URL fix: conditional use acceptable | "AML/CFT source monitoring across CBUAE, DFSA, ADGM/FSRA, UAE FIU, EOCN, and SCA. VARA AML/CFT live guidance monitoring pending source remediation." |
| 15 | "Comprehensive AML/CFT monitoring" | **NO** (current) / **CONDITIONAL** (post-VARA fix) | VARA AML gap is the blocker. DNFBP MLRO guidance (ADGM RA AML guides) not active. | VARA AML live page active + ADGM RA AML guides active | After activation: "Selected AML/CFT source monitoring across major UAE regulatory bodies. Monitoring intelligence only." |
| 16 | "CBUAE certified" or "DFSA certified" | **NO** | StatuteProof has no regulatory certification. Forbidden phrase per CLAUDE.md. | Not achievable | Remove entirely. |
| 17 | "Prevent fines" or "avoid penalties" | **NO** | Causal compliance claim. Cannot be supported. Forbidden phrase. | Not achievable | Remove entirely. |
| 18 | "Replace lawyers" or "replace compliance professionals" | **NO** | False claim. StatuteProof supplements, not replaces. Forbidden phrase. | Not achievable | "StatuteProof supplements, not replaces, qualified legal counsel, MLROs, and compliance professionals." |
| 19 | "79 sources covering all key compliance areas" | **NO** | "All key" is an overstatement. FTA (tax), customs, VARA guidance, MoJ are not covered. | Cannot be supported | Replace with: "79 active sources across major UAE financial, AML/CFT, virtual asset, securities, and financial free-zone regulatory bodies." |
| 20 | "Guaranteed compliance" | **NO** | Absolute guarantee claim. Forbidden phrase. | Not achievable | Remove entirely. Replace with disclaimer. |

---

## Quick Reference: Always-Safe Phrases

Use these in any customer-facing context without modification:

1. "79 enabled UAE official-source endpoints. 78 readiness-supported."
2. "Monitoring intelligence only. Not legal advice."
3. "Not a guarantee of regulatory completeness."
4. "Source monitoring may be affected by access restrictions, website changes, and publication delays."
5. "Users should verify official source material directly."
6. "StatuteProof does not replace qualified legal counsel, MLROs, or compliance professionals."
7. "Source readiness, extraction quality, and known gaps are shown transparently."
8. "Selected official UAE regulatory sources — not all publications from each body."

---

## Quick Reference: Never-Use Phrases

| Phrase | Reason |
|--------|--------|
| Complete UAE coverage | Absolute claim; not true |
| Never miss an update | Absolute claim; not achievable |
| All UAE regulations | "All" not supported |
| Full AML/CFT monitoring | VARA AML gap |
| Comprehensive UAE monitoring | Tier 3 criteria not met |
| Guaranteed compliance | Absolute claim; forbidden |
| Certified by [any regulator] | False certification claim |
| Prevent fines / avoid penalties | Causal claim; forbidden |
| Replace lawyers | False; forbidden |
| 100% accurate | Absolute; forbidden |
| Perfect parsing | Absolute; forbidden |

---

## Claim Review Checklist (Use Before Any Public Output)

Before publishing any customer-facing claim about coverage:

- [ ] Does it use an exact count from sources.json? (Use Tier 0)
- [ ] Does it say "selected" rather than "all" or "complete"?
- [ ] Does it include "not legal advice"?
- [ ] Does it include "not a guarantee of completeness"?
- [ ] Does it avoid the 10 never-use phrases above?
- [ ] Has the legal language agent reviewed it?
- [ ] Has the QA/Critic approved it?

If any checkbox is unchecked, the claim is not ready for public use.
