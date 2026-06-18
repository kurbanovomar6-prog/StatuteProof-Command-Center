# Weak-Family Bulk Activation Final Report

Date: 2026-06-18

## 1. Executive Result

Starting truth: 81 enabled / 80 monitoring-active / 1 remediation
Ending truth: 122 enabled / 121 monitoring-active / 1 remediation

Newly active sources: 41
New or reactivated source IDs are proof-backed, repeat-baseline-complete, and mass-monitor dry-run `MONITOR_OK` with no hash drift. Monitoring intelligence only. Not legal advice.

## 2. Batch Funnel

- No-save attempts run: 213
- Raw strong no-save passes: 74
- Evidence/baseline candidates processed: 63
- Baseline-complete candidates: 63
- Final unique MONITOR_OK/no-drift activations: 41
- Held for nav-shell, quality drop, dry-run drift, or duplicate latest hash: 22

## 3. Newly Active By Family

- DFSA: 30
- Ministry of Economy / DNFBP AML: 7
- DIFC: 4

## 4. Sources Activated

- `AE-moet-aml-170b7988`
- `AE-moet-auditing-accounts-legislations-84d91bc4`
- `AE-moet-economic-substance-regulations-a5b9825b`
- `AE-moet-registering-companies-in-goaml-c83375da`
- `AE-moet-regulation-of-business-fd17959e`
- `AE-moet-regulation-of-competition-ba53cc4c`
- `AE-moet-targeted-financial-sanctions-586d6f96`
- `AE-dfsa-news-notice-amendment-dfsa-forms-3-5b23279e`
- `AE-dfsa-news-notice-amendment-dfsa-forms-4-238b095a`
- `AE-dfsa-news-notice-amendment-dfsa-forms-5-87f5ab7b`
- `AE-dfsa-news-notice-amendment-dfsa-forms-6-516f99a2`
- `AE-dfsa-news-notice-amendments-1-c8efa9bf`
- `AE-dfsa-news-notice-amendments-3fadbb97`
- `AE-dfsa-news-notice-amendments-dfsa-forms-1-7eb3ddbd`
- `AE-dfsa-news-notice-amendments-dfsa-forms-2-26da0ea8`
- `AE-dfsa-news-notice-amendments-dfsa-forms-3-6a085fc2`
- `AE-dfsa-news-notice-amendments-dfsa-forms-4-871a906a`
- `AE-dfsa-news-notice-amendments-dfsa-forms-fdd4d828`
- `AE-dfsa-news-notice-amendments-legislation-b5739a79`
- `AE-dubai-financial-services-authority-dfsa`
- `AE-difc-business-aml-cft-991d9543`
- `AE-difc-business-economic-substance-regulations-05c9f19b`
- `AE-difc-whats-on-insights-difc-data-protection-law-pioneers-6615d880`
- `AE-difc-whats-on-news-difc-arbitration-law-consultation-684af25c`
- `AE-dfsa-rulebook-official`
- `AE-dfsa-consultation-papers`
- `AE-dfsa-news-notice-relation-cp90-1ea4f448`
- `AE-dfsa-news-notice-discussion-paper-67ac395d`
- `AE-dfsa-news-notice-consultation-paper-26232647`
- `AE-dfsa-news-notice-amendments-rulebook-f3b17fd6`
- `AE-dfsa-news-notice-consultation-paper-1-0fd2727d`
- `AE-dfsa-news-notice-consultation-paper-2-ce31d49f`
- `AE-dfsa-news-notice-consultation-release-128d0518`
- `AE-dfsa-news-notice-amendments-rulebook-1-a3b7e98d`
- `AE-dfsa-news-notice-amendments-rulebook-2-51efcaf3`
- `AE-dfsa-news-notice-amendments-rulebook-3-5fb25116`
- `AE-dfsa-news-notice-amendments-rulebook-4-532da6ec`
- `AE-dfsa-news-notice-amendments-rulebook-5-2fceb723`
- `AE-dfsa-news-notice-amendments-rulebook-6-077b65fb`
- `AE-dfsa-news-notice-call-evidence-release-0e8f9854`
- `AE-dfsa-news-notice-consultation-release-1-f752cf93`

## 5. Sources Held And Why

- `AE-dfsa-ar-what-we-do-enforcement-f0487f7a` — NAV_SHELL_ONLY,changed_on_dry_run,monitor_hash_mismatch
- `AE-dfsa-news-notice-amendment-dfsa-forms-adabf2e1` — NAV_SHELL_ONLY,changed_on_dry_run,monitor_hash_mismatch
- `AE-dfsa-news-reminder-rulebook-amendments-e6e4718a` — NAV_SHELL_ONLY,changed_on_dry_run,monitor_hash_mismatch
- `AE-dfsa-what-we-do-enforcement-1a837c50` — NAV_SHELL_ONLY,changed_on_dry_run,monitor_hash_mismatch
- `AE-adgm-adgm-courts-english-common-law-4fef1515` — QUALITY_DROP,changed_on_dry_run,monitor_hash_mismatch
- `AE-adgm-business-areas-capital-markets-3ce15bcf` — NAV_SHELL_ONLY,changed_on_dry_run,monitor_hash_mismatch
- `AE-adgm-media-announcements-adgm-amends-founding-law-64b8b408` — NAV_SHELL_ONLY,changed_on_dry_run,monitor_hash_mismatch
- `AE-adgm-operating-in-adgm-it-risk-management-dd67c9de` — NAV_SHELL_ONLY,changed_on_dry_run,monitor_hash_mismatch
- `AE-adgm-operating-in-adgm-monitoring-and-enforcement-bf47a626` — NAV_SHELL_ONLY,changed_on_dry_run,monitor_hash_mismatch
- `AE-adgm-operating-in-adgm-tax-services-5d62f306` — QUALITY_DROP,changed_on_dry_run,monitor_hash_mismatch
- `AE-adgm-registration-authority-lpa-risk-report-de50d051` — NAV_SHELL_ONLY,changed_on_dry_run,monitor_hash_mismatch
- `AE-difc-whats-on-insights-why-regulation-essential-fintech-success-99d7bb19` — changed_on_dry_run,monitor_hash_mismatch
- `AE-vara-en-regulations-regulatory-notices-e922bca2` — QUALITY_DROP,changed_on_dry_run,monitor_hash_mismatch
- `AE-added-en-grow-regulations-63dfab49` — changed_on_dry_run,monitor_hash_mismatch
- `AE-dfsa-aml-ctf-sanctions` — NAV_SHELL_ONLY,changed_on_dry_run,monitor_hash_mismatch
- `AE-dfsa-guidance-notes` — NAV_SHELL_ONLY,changed_on_dry_run,monitor_hash_mismatch
- `AE-dfsa-ar-data-protection-00f21b77` — QUALITY_DROP,changed_on_dry_run,monitor_hash_mismatch
- `AE-dfsa-what-we-do-supervision-5fba6a56` — NAV_SHELL_ONLY,changed_on_dry_run,monitor_hash_mismatch
- `AE-dfsa-news-dfsa-signs-mou-amlscu-uae-d443a85d` — NAV_SHELL_ONLY,changed_on_dry_run,monitor_hash_mismatch
- `AE-dfsa-ar-what-we-do-about-supervision-adddadb1` — NAV_SHELL_ONLY,changed_on_dry_run,monitor_hash_mismatch
- `AE-dfsa-news-dfsa-host-cyber-risk-forum-08a4afd4` — NAV_SHELL_ONLY,changed_on_dry_run,monitor_hash_mismatch
- `AE-moet-consumer-protection-legislations-df9cdeb7` — duplicate latest monitor hash with `AE-moet-auditing-accounts-legislations-84d91bc4`

## 6. Adapter / Parser Improvements

- Added `uae_legal_database` adapter for UAE legal/regulatory pages where content appears as document cards, legal text blocks, tables, or compliance links.
- Added Source Intake support for `uae_legal_database` as a structured/document adapter so no-save previews do not treat isolated legal listings as nav-shells.
- Added fixture tests for meaningful UAE legal database extraction, nav-shell rejection, and preview-only evidence boundaries.

## 7. Commercial Impact

DFSA depth is now strong and Ministry of Economy/DNFBP AML moved from weak single-source coverage to a useful seven-source layer. DIFC moved from 8 to 12 active sources. This improves UAE Monitor credibility, but it does not solve every weak family: FTA, SCA, FIU, EOCN, MoJ/Gazette, data privacy outside DIFC/ADGM, markets/exchanges, customs, courts, and free zones still need targeted adapter sprints.

## 8. Claim Safety

Did we claim complete UAE coverage? No.
Safe wording: StatuteProof monitors selected public official UAE sources that pass proof, baseline, source-health, noise, and review gates. Candidate URLs are research targets, not active monitoring. Monitoring intelligence only. Not legal advice.

## 9. Readiness Impact

- $199 pilot: stronger; more DFSA/DIFC/MoE sources make controlled pilots more credible.
- $399 UAE Monitor: improved but still partial for weak families outside DFSA/CBUAE.

## 10. Next Exact Activation Batch

Build targeted adapters for SCA, UAE FIU/EOCN, FTA, and MoJ/Gazette before attempting another large activation batch.

## 11. Next Exact Product Task

Add 7/30/90-day source reliability trend charts for monitoring-active sources.

## 12. Next Exact Sales Task

Update demo language to say 122 enabled / 121 monitoring-active selected official UAE sources, with explicit weak-family caveats and no completeness claim.
