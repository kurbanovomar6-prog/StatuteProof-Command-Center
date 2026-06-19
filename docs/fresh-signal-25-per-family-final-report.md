# Fresh Signal 25 Per Family Final Report

Date: 2026-06-19

## 1. Starting Source Truth

- Enabled UAE sources: 226
- Fresh-alert eligible sources: 96
- Overall MONITOR_OK sources: 150
- Evidence-library-only sources: 60
- Candidate/pending validation: 62
- Remediation: 8

## 2. Ending Source Truth

- Enabled UAE sources: 238
- Fresh-alert eligible sources: 168
- Overall MONITOR_OK sources: 222
- Evidence-library-only sources: 61
- Candidate/pending validation: 6
- Remediation: 3

## 3. What Changed

This sprint and the follow-on fresh-source expansion converted or confirmed 66 sources as daily-checkable `fresh_alert` sources after proof, repeat baseline, and mass-monitor dry-run `MONITOR_OK`.

No customer emails or customer alerts were sent.

## 4. Family Before / After

| Family | Before Fresh Alert | After Fresh Alert | Target | Result |
|---|---:|---:|---:|---|
| CBUAE | 0 | 25 | 25 | Strong |
| VARA | 16 | 24 | 25 | Good, still short by 1 |
| DFSA | 5 | 16 | 25 | Partial |
| DIFC | 3 | 10 | 25 | Partial |
| ADGM/FSRA | 2 | 10 | 25 | Partial |
| UAE FIU | 2 | 5 | 25 | Weak |
| EOCN/TFS | 18 | 25 | 25 | Strong selected-source |
| SCA | 1 | 5 | 25 | Weak |
| MoJ/Gazette | 0 | 0 | 25 | Blocked |
| MoF | 0 | 1 | 25 | Weak |
| FTA | 25 | 25 | 25 | Strong |
| MoE/DNFBP AML | 42 | 42 | 25 | Strong |

## 5. Families Now Strong

- CBUAE
- FTA
- MoE/DNFBP AML

## 6. Families Still Not Strong And Exact Blocker

- VARA: 25 fresh-alert sources after adding the proof-backed official enforcement table source. This is selected-source monitoring, not complete VARA coverage.
- DFSA: 16 fresh-alert sources after adding DFSA Laws and Rules. Static individual notice pages and duplicate-hash publication pages cannot count. Guidance/publication/policy pages still collapse to nav-shell under current public DOM.
- DIFC: 10 fresh-alert sources. Static whats-on/news pages cannot count. Needs more legal/database/data-protection/consultation/publication listing endpoints.
- ADGM/FSRA: 10 fresh-alert sources after adding two medium-signal ADGM Courts legal/document listings. Some FSRA candidates still fail `QUALITY_DROP` or nav-shell and need adapter refinement.
- UAE FIU: 5 fresh-alert sources. FIU circulars failed nav-shell. Public FIU universe may be smaller than 25; goAML remains forbidden.
- EOCN/TFS: 25 fresh-alert sources after adding the UAEIEC news listing. This is Strong selected-source monitoring, not complete sanctions/TFS coverage.
- SCA: 5 fresh-alert sources after adding the SCA FinTech Regulatory Sandbox page. Regulations listing still failed nav-shell. Needs better SCA listing/table adapter and more official endpoints.
- MoJ/Gazette: 0 fresh-alert sources. UAE legislation portal remains access/WAF remediation. Needs official alternative endpoint research.
- MoF: 1 fresh-alert source after adding the official MoF publications and releases hub. Current MoF source depth is still Weak and needs specific decision/news/document listing endpoints.

## 7. Daily-Checkable Source Count

- Daily-checkable fresh-alert sources after this pass: 168

All fresh-alert sources now carry:

- `recommended_check_frequency: daily`
- `fresh_signal_type`
- `expected_update_pattern`
- `customer_alert_policy`

## 8. New Sources Activated By Family

- CBUAE: 25
- VARA: 7
- EOCN/TFS: 4 direct/official EOCN or UAEIEC-linked TFS sources after the expansion
- UAE FIU: 3
- SCA: 4
- ADGM/FSRA: 6
- DFSA: 10
- DIFC: 7

Detailed source IDs are in `docs/fresh-signal-25-per-family-final-activation-set.json`.

## 9. Sources Held / Rejected By Family

- CBUAE: `AE-cbuae-regulations` held due access/private-risk classification.
- VARA: `AE-vara-enforcement` held due nav-shell.
- UAE FIU: `AE-uaefiu-circulars` held due nav-shell.
- SCA: `AE-sca-regulations-listing` held due nav-shell.
- ADGM/FSRA: `AE-adgm-fsra-guidance-policy` and `AE-adgm-ra-circulars` held due `QUALITY_DROP`; `AE-adgm-fsra-waivers` held due nav-shell.
- DFSA: `AE-dfsa-consultation-paper-165` held as evidence-library only because it is a static historical consultation paper, not a fresh listing.

## 10. Adapter Fixes Implemented / Used

- Used registered CBUAE rulebook adapter path and CBUAE document-listing configs.
- Used registered ADGM/FSRA adapter path plus existing ADGM custom/listing configs.
- Used SCA listing/table configs for SCA sources that passed.
- Used EOCN listing/news configs with Playwright.
- Used FIU document/listing configs with Playwright.
- Used VARA PDF/document listing paths.
- Used DFSA rulebook/listing/Playwright configs.
- Used DIFC legal/data-protection page extraction paths.

No unsafe access bypass was used.

## 11. Adapters Still Needed

- VARA enforcement/admin-order listing adapter.
- SCA regulations listing/table adapter.
- FIU circulars-specific listing adapter.
- ADGM guidance/RA circular adapter refinement.
- MoJ/Gazette access-safe legal database/gazette adapter or official alternative.
- MoF decision/news/document listing adapter.
- Additional DFSA/DIFC/ADGM discovery adapters to avoid counting static detail pages.

## 12. No-Save Tests Run

Batch records reviewed in this pass: 68.

## 13. Evidence Saved

Sources activated or confirmed with proof/baseline/MONITOR_OK across this pass and follow-on expansion: 66.

## 14. Baseline Complete

All promoted sources have `baseline_runs_completed >= 2`.

## 15. Mass-Monitor MONITOR_OK Count

All promoted sources had mass-monitor dry-run `MONITOR_OK`.

## 16. Static Sources Demoted / Held

Static/evidence-library count after this pass: 61.

Static detail pages remain excluded from fresh-alert claims.

## 17. Customer-Safe Claims Now Allowed

Allowed:

- “StatuteProof has 169 fresh-alert eligible UAE official-source daily monitors with MONITOR_OK status, proof records, hashes, baseline confirmation, and daily-check metadata.”
- “CBUAE rulebook monitoring includes 25 fresh-alert official rulebook/regulatory sources.”
- “FTA and MoE/DNFBP AML remain Strong Fresh Signal families.”
- “VARA has 25 confirmed selected-source fresh-alert sources, including the official enforcement table source. This is not complete VARA coverage.”
- “SCA has 5 confirmed fresh-alert sources; broader SCA coverage remains under remediation.”

## 18. Claims Still Forbidden

Forbidden:

- “Complete UAE coverage.”
- “Every family is Strong.”
- “Complete SCA coverage.”
- “Complete EOCN/TFS coverage.”
- “UAE FIU circulars are monitored.”
- “MoJ/Gazette monitoring is live.”
- “MoF is Strong.”
- “Guaranteed compliance.”
- “Legal advice.”
- “Perfect parsing.”
- “Never miss updates.”

## 19. Tests Added / Updated

Added or updated:

- `tools/validate_fresh_signal_sources.py`
- `tools/validate_daily_checkable_sources.py`
- `tools/validate_fresh_signal_25_per_family.py`

## 20. Validators Added / Updated

Validators now check:

- fresh-alert proof/hash/baseline/MONITOR_OK;
- `normalized_text_path`;
- daily check frequency;
- fresh signal type;
- expected update pattern;
- customer alert policy;
- static pages excluded from alerts;
- family cannot be called Strong without 25 fresh-alert MONITOR_OK sources.

## 21. $199 Pilot Impact

Stronger. The product now has a much more defensible fresh-monitoring claim for CBUAE, FTA, and MoE/DNFBP pilots, plus materially improved VARA/EOCN/DFSA/DIFC/ADGM/SCA/FIU evidence.

## 22. $399 UAE Monitor Impact

Improved but not fully ready for a 9/10 broad UAE Monitor claim. The product is materially stronger, but several families are still below 25 and MoJ/MoF remain weak.

## 23. Next Exact Source Task

Run a targeted weak-family discovery + adapter sprint for:

1. VARA regulatory notices/enforcement/admin orders: find or build one more official fresh-alert endpoint.
2. DFSA/DIFC/ADGM: prioritize official listing adapters and avoid static article/detail inflation.
3. SCA: build a stronger regulations/listing/table adapter and research more SCA official endpoints.
4. UAE FIU: build FIU circulars adapter and prove whether 25 public endpoints exist.
5. MoJ/Gazette and MoF: research official alternatives and build access-safe adapters.

## 24. Next Exact Product Task

Update the frontend Sources/Coverage UI so customers can see:

- Fresh alerts
- Evidence library
- Candidate
- Remediation
- Family strength
- Exact blockers

## 25. Next Exact Sales Task

Use only the updated safe claim:

“169 fresh-alert eligible UAE official-source daily monitors with MONITOR_OK, proof records, hashes, baseline confirmation, and daily-check metadata.”

Do not sell complete UAE coverage or complete family coverage.

## Follow-On Fresh Source Expansion Addendum

After this report was first written, a targeted fresh-source expansion added six unique `fresh_alert` sources after no-save, two evidence runs, repeat baseline, duplicate/static-detail review, and mass-monitor dry-run `MONITOR_OK`:

- `AE-dfsa-laws-rules-legal-resources-3dc15494`
- `AE-dfsa-innovation-59c1dc61`
- `AE-dfsa-what-we-do-enforcement-1a837c50`
- `AE-sca-fintech-sandbox`
- `AE-uaeiec-en-us-laws-regulations-listing-00a71863`
- `AE-eocn-tfs`

Held despite technical no-save passes: DFSA guidance/publication/policy pages with duplicate normalized hashes, DFSA `/test/` URLs, static DFSA news detail, wrong-family MoE candidate, FIU static/single-report pages, and ADGM pages that failed mass-monitor selector verification.


## Fresh Source Completion Next Addendum

A follow-on completion pass added six more proof-backed `fresh_alert` sources after no-save, two saved evidence runs, stable baseline hash, mass-monitor dry-run `MONITOR_OK`, and static/detail review:

- `AE-uaeiec-news-listing-next`
- `AE-vara-news-circulars-listing`
- `AE-dfsa-laws-rules-2dee8ba9`
- `AE-adgm-adgm-courts-legislation-and-procedures-66abfd89`
- `AE-adgm-adgm-courts-forms-fees-and-guides-a3b9d695`
- `AE-mof-publications-and-releases`

Updated family truth after this addendum:

- EOCN/TFS: 25, Strong selected-source monitoring. This does not claim complete sanctions/TFS coverage.
- VARA: 25 selected-source fresh-alert monitors; Strong threshold reached without claiming complete VARA coverage.
- DFSA: 16.
- DIFC: 10.
- ADGM/FSRA: 10.
- UAE FIU: 5.
- SCA: 5.
- MoJ/Gazette: 0.
- MoF: 1.

Current pilot-safe count: 169 fresh-alert eligible UAE official-source daily monitors with MONITOR_OK, proof records, hashes, baseline confirmation, and daily-check metadata.
