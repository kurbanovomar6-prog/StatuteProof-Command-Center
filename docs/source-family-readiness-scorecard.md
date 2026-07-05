# StatuteProof Source Family Readiness Scorecard

Date: 2026-06-21

## Purpose

This scorecard records current UAE source-family readiness after the source-truth
and source-health classification repair. It is an operator artifact, not a
customer coverage claim.

## Scoring Rules

- 8/10 requires strong selected-source breadth, proof paths, repeat baseline,
  meaningful parser output, clean active source health, and scoped customer
  claims.
- 7/10 can support a carefully scoped pilot when source limits are disclosed.
- Below 6/10 should not be the headline ICP for Apollo outreach.
- No family score means complete family coverage.

## Current Source Truth

- Enabled UAE source records: 246
- Fresh-alert eligible: 180
- Evidence-library only: 60
- Candidate: 4
- Remediation: 2
- Active source-health blockers: 0
- Disabled/historical repeated-failure source IDs retained for audit history: 5

## Family Readiness

| Family | Before | After | Total | Fresh-alert | Evidence-library | Candidate | Remediation | Readiness | Safe sales claim | Forbidden claim | Next exact fix |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- |
| CBUAE | 8.0 | 8.0 | 27 | 25 | 1 | 1 | 0 | Strong selected-source | Selected CBUAE official rulebook/regulatory monitoring | Complete CBUAE coverage | Add family drilldown and canonical evidence examples |
| VARA | 8.0 | 8.0 | 26 | 25 | 1 | 0 | 0 | Strong selected-source | Selected VARA official rulebook/circular/enforcement monitoring | Complete VARA coverage | Add VASP pilot source profile and evidence examples |
| DFSA | 6.9 | 7.2 | 44 | 16 | 28 | 0 | 0 | Good selected-source; several evidence-linked examples now exist | Selected DFSA rulebook, AML, consultation, enforcement monitoring with MLRO, consultation, and enforcement alerts now canonical-evidence linked | Complete DFSA coverage | Founder-review DFSA linked evidence; then add evidence/noise review for AML rulebook alerts |
| DIFC | 6.5 | 7.0 | 25 | 11 | 14 | 0 | 0 | Selected-source pilot-ready; official Legal Database listing now proof-backed and evidence-linked | Selected DIFC laws/data-protection/legal database/legal notice monitoring | Complete DIFC legal database coverage | Founder-review `evr_AE-difc-legal-database_intake-20260621T214518Z`; add item-level legal detail source only if proof and baseline pass |
| ADGM/FSRA | 6.8 | 7.0 | 27 | 11 | 14 | 2 | 0 | Selected-source pilot-ready, with two candidates still held | Selected ADGM/FSRA rulebook/guidance/policy/circular monitoring with financial-crime and rulebook evidence examples | Complete ADGM/FSRA coverage | Founder-review `evr_AE-adgm-fsra-guidance-policy_intake-20260621T214439Z`; resolve or hold waivers and RA circulars with consistent source-run statuses |
| UAE FIU | 6.2 | 6.3 | 8 | 6 | 0 | 1 | 1 | Partial, with cleaner circulars blocker and one high-value evidence-linked alert | Selected UAE FIU publications, typologies, AML/CFT laws, system guides, with circulars disclosed as unproven/held | UAE FIU circulars monitored or complete UAE FIU coverage | Founder-review `evr_AE-uaefiu-typology-reports_intake-20260619T150224Z`; move next to DIFC or ADGM/FSRA unless a distinct FIU circular endpoint is found |
| SCA | 5.8 | 6.5 | 6 | 6 | 0 | 0 | 0 | Improved selected endpoints; regulations listing is proof-backed and evidence-linked, but AML/CFT parser warning remains | Selected SCA direct/regulations endpoints only | Full SCA coverage or SCA root portal monitoring | Resolve SCA AML/CFT parser-review warning before any material-change claim |
| MoF | 4.0 | 7.0 | 8 | 7 | 1 | 0 | 0 | Selected-source pilot-ready; still not complete MoF/tax coverage | Selected MoF publications/releases, financial legislation, ESR, DMTT/top-up tax, corporate tax, AEOI/FATCA/CRS, and UAE financial framework monitoring | Broad MoF coverage or complete tax coverage | Founder-review 7 MoF canonical evidence records; link future MoF alerts only on exact source_id/run_id match |
| FTA / Tax | 7.0 | 7.5 | 25 | 25 | 0 | 0 | 0 | Strong but narrow | 25 direct official FTA PDF endpoints | FTA portal monitoring | Keep portal/listing out of claims unless adapter passes proof/baseline |
| EOCN / TFS | 7.0 | 7.0 | 25 | 25 | 0 | 0 | 0 | Strong selected-source | Selected EOCN/TFS-related official sources | Complete sanctions coverage | Add canonical evidence examples before using in buyer proof |
| MoJ / Gazette | 1.0 | 7.0 | 2 | 1 | 0 | 0 | 1 | Partial selected-source, now proof-backed | One selected UAE Legislation Platform listing fresh-alert source; root/e-Laws/Gazette limits disclosed | Complete UAE legislation or Official Gazette coverage | Add item-level Gazette/legislation detail source or official feed/API only if proof/baseline passes |

## What Changed In This Sprint

1. Fixed source-truth drift for SCA and UAE FIU between `sources.json`,
   `source_signal_quality_audit.json`, `source_signal_quality_audit.md`, and
   `sourceQualityAudit.ts`.
2. Added family-level audit validation so stale family counts fail tests and
   preflight.
3. Changed operator source-health reporting to separate currently enabled
   source blockers from disabled/historical repeated-failure source IDs.
4. Regenerated the verified monitoring digest. It now reports 0 active
   source-health blockers and 5 historical disabled-source failures.
5. Added a focused UAE FIU proof-recovery pass: generated a complete,
   hash-verifiable canonical evidence record for
   `AE-uaefiu-typology-reports` / `intake-20260619T150224Z` and linked the
   matching alert queue item. The record remains pending review and is not
   customer-brief eligible.
6. Re-tested `AE-uaefiu-circulars` safely and held it: the URL redirects to the
   general UAE FIU publications index; page text and sitemap expose no distinct
   circular/notice endpoint; Source Lab no-save returned `NAV_SHELL_ONLY`.
   Registry metadata now says this is a held publications-index candidate, not
   a monitored circulars/notices source.
7. Added a DFSA proof-backed upgrade pass: generated complete, hash-verifiable
   canonical evidence for `AE-dfsa-financial-crime-mlro-letters` /
   `intake-20260619T151120Z` and linked the exact matching alert queue item.
   The record remains pending review and is not customer-brief eligible.
8. Added a full weak-family upgrade pass: generated six additional complete,
   hash-verifiable canonical evidence records and linked six exact matching
   alert queue items:
   `AE-adgm-fsra-financial-crime-prevention`,
   `AE-adgm-fsra-rulebooks`, `AE-difc-data-protection-regulation-10`,
   `AE-sca-circulars-rules-procedures`, `AE-dfsa-consultation-current`, and
   `AE-dfsa-what-we-do-enforcement-1a837c50`. All remain pending review and
   are not customer-brief eligible.
9. Added a focused MoJ/Gazette recovery pass: discovered that
   `https://www.uaelegislation.gov.ae/en/legislations` can be monitored as a
   selected official UAE Legislation Platform listing, ran strong no-save,
   saved two proof-backed baseline runs, confirmed stable normalized hash,
   passed mass-monitor dry-run `MONITOR_OK`, activated one scoped fresh-alert
   source, generated canonical evidence for the new listing, and linked the
   existing UAE Legislation Portal alert to its canonical evidence record. The
   root portal/e-Laws/Gazette limitation remains disclosed.
10. Added a focused MoF recovery pass: activated four additional official MoF
    sources after strong no-save, two proof-backed baseline runs, stable
    normalized hashes, mass-monitor dry-run `MONITOR_OK`, and scoped claim
    review:
    `AE-mof-top-up-tax`, `AE-mof-corporate-tax-in-the-uae`,
    `AE-mof-aeoi-fatca-crs`, and `AE-mof-uae-financial-framework`.
    Generated four complete canonical evidence records for those sources. They
    remain pending review and are not customer-brief eligible.
11. Added a four-weak-family upgrade pass: activated three official sources
    only after no-save preview, proof-backed repeat baseline, stable hashes,
    and mass-monitor `MONITOR_OK`: `AE-adgm-fsra-guidance-policy`,
    `AE-difc-legal-database`, and `AE-sca-regulations-listing`. Generated and
    exact-linked canonical evidence records for all three matching alert queue
    entries. The records remain pending review and are not customer-brief
    eligible.
12. Held `AE-adgm-fsra-waivers`, `AE-adgm-ra-circulars`,
    `AE-adgm-federal-legislation`, and `AE-adgm-fsra-regulatory-alerts` because
    current proof, selector, or source-run gates did not pass cleanly enough to
    claim fresh-alert readiness.

## What Did Not Change

- One scoped UAE Legislation Platform listing source was activated in the prior
  pass, and four scoped MoF sources were activated in this MoF pass.
- No source row was downgraded.
- Fresh-alert count increased from 177 to 180 in this four-family pass because
  three official ADGM/FSRA, DIFC, and SCA sources passed proof-backed repeat
  baseline and mass-monitor `MONITOR_OK`.
- No proof or baseline was fabricated.
- No UAE FIU source row was activated or strengthened in this four-family pass.
- The new UAE FIU canonical evidence record remains pending review.
- The new DFSA canonical evidence record remains pending review.
- The new ADGM/FSRA, DIFC, SCA, and additional DFSA records remain pending
  review.
- The new MoJ/Gazette canonical evidence records remain pending review.
- The new MoF canonical evidence records remain pending review and have no
  alert linkage yet.
- The new ADGM/FSRA, DIFC, and SCA canonical evidence records remain pending
  review even though their matching alerts are linked.
- FIU circular monitoring remains unproven and must not be claimed.
- No complete family coverage claim was added.
- UAE Legislation/Gazette is now a scoped selected-source claim, not complete
  UAE legislation or Official Gazette monitoring.
- MoF is now viable only as selected-source MoF fiscal/tax-policy monitoring;
  broad MoF coverage and complete tax coverage remain forbidden claims.

## Apollo Guidance

Safe to contact now:

- VARA/VASP prospects, if scoped as selected VARA official-source monitoring.
- CBUAE/payments prospects, if scoped as selected CBUAE rulebook/regulatory monitoring.
- DNFBP/AML prospects, if scoped around MoE/DNFBP, EOCN/TFS, and selected FIU sources.

Use caution:

- DFSA prospects: viable for selected-source pilot, but not complete DFSA monitoring.
- ADGM/FSRA prospects: viable for selected-source pilot with explicit candidate
  caveats; not complete ADGM/FSRA coverage.
- DIFC prospects: viable for selected-source pilot with explicit legal database
  caveats; not complete DIFC legal database coverage.
- UAE FIU prospects: viable only as selected-source AML/FIU publication and
  typology monitoring, with FIU circulars disclosed as candidate/held.
- Legal/governance prospects: viable only for a selected UAE Legislation
  Platform listing pilot with explicit disclosure that root/e-Laws/Gazette
  routes remain unproven.
- MoF/tax-policy-adjacent prospects: viable only when scoped to selected MoF
  pages and not positioned as complete MoF, FTA, or tax coverage.

Avoid as headline ICP for now:

- MoJ/Gazette-heavy buyers who need complete Official Gazette publication
  monitoring or item-level law coverage.
- SCA-heavy buyers needing broad securities-law coverage or SCA root portal
  monitoring.
- MoF-heavy buyers needing broad fiscal/tax portal monitoring across all MoF,
  FTA, treaty, budget, public-debt, and open-data surfaces.

## Boundary

Monitoring intelligence only. Not legal advice. Not complete UAE coverage. Not
complete family coverage. Not a guarantee that every regulatory update will be
captured.
