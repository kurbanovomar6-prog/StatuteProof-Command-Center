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

- Enabled UAE sources: 226
- Fresh-alert eligible sources: 156
- Overall MONITOR_OK sources: 210
- Evidence-library-only sources: 61
- Candidate/pending validation: 6
- Remediation: 3

## 3. What Changed

This sprint converted or confirmed 60 sources as daily-checkable `fresh_alert` sources after proof, repeat baseline, and mass-monitor dry-run `MONITOR_OK`.

No customer emails or customer alerts were sent.

## 4. Family Before / After

| Family | Before Fresh Alert | After Fresh Alert | Target | Result |
|---|---:|---:|---:|---|
| CBUAE | 0 | 25 | 25 | Strong |
| VARA | 16 | 23 | 25 | Good, still short by 2 |
| DFSA | 5 | 12 | 25 | Partial |
| DIFC | 3 | 10 | 25 | Partial |
| ADGM/FSRA | 2 | 8 | 25 | Partial |
| UAE FIU | 2 | 5 | 25 | Weak |
| EOCN/TFS | 18 | 22 | 25 | Good, still short by 3 |
| SCA | 1 | 4 | 25 | Weak |
| MoJ/Gazette | 0 | 0 | 25 | Blocked |
| MoF | 0 | 0 | 25 | Weak |
| FTA | 25 | 25 | 25 | Strong |
| MoE/DNFBP AML | 42 | 42 | 25 | Strong |

## 5. Families Now Strong

- CBUAE
- FTA
- MoE/DNFBP AML

## 6. Families Still Not Strong And Exact Blocker

- VARA: 23 fresh-alert sources. Enforcement page failed nav-shell. Needs enforcement/admin-order listing adapter or two more official endpoints.
- DFSA: 12 fresh-alert sources. Static individual notice pages cannot count. Needs more official listing/rulebook/enforcement/consultation endpoints.
- DIFC: 10 fresh-alert sources. Static whats-on/news pages cannot count. Needs more legal/database/data-protection/consultation/publication listing endpoints.
- ADGM/FSRA: 8 fresh-alert sources. Some candidates failed `QUALITY_DROP` or nav-shell. Needs adapter refinement and more official endpoints.
- UAE FIU: 5 fresh-alert sources. FIU circulars failed nav-shell. Public FIU universe may be smaller than 25; goAML remains forbidden.
- EOCN/TFS: 22 fresh-alert sources. Direct EOCN now has 2 MONITOR_OK sources, but broad TFS family is still below 25.
- SCA: 4 fresh-alert sources. Regulations listing failed nav-shell. Needs better SCA listing/table adapter and more official endpoints.
- MoJ/Gazette: 0 fresh-alert sources. UAE legislation portal remains access/WAF remediation. Needs official alternative endpoint research.
- MoF: 0 fresh-alert sources. Current MoF source is generic homepage/evidence-library. Needs specific official decision/news/document listing endpoints.

## 7. Daily-Checkable Source Count

- Daily-checkable fresh-alert sources after this pass: 156

All fresh-alert sources now carry:

- `recommended_check_frequency: daily`
- `fresh_signal_type`
- `expected_update_pattern`
- `customer_alert_policy`

## 8. New Sources Activated By Family

- CBUAE: 25
- VARA: 7
- EOCN/TFS: 2 direct EOCN sources
- UAE FIU: 3
- SCA: 3
- ADGM/FSRA: 6
- DFSA: 7
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

Sources activated or confirmed with proof/baseline/MONITOR_OK in this pass: 60.

## 14. Baseline Complete

All promoted sources have `baseline_runs_completed >= 2`.

## 15. Mass-Monitor MONITOR_OK Count

All promoted sources had mass-monitor dry-run `MONITOR_OK`.

## 16. Static Sources Demoted / Held

Static/evidence-library count after this pass: 61.

Static detail pages remain excluded from fresh-alert claims.

## 17. Customer-Safe Claims Now Allowed

Allowed:

- “StatuteProof has 156 fresh-alert eligible UAE official-source monitors with MONITOR_OK status, proof records, hashes, baseline confirmation, and daily-check metadata.”
- “CBUAE rulebook monitoring includes 25 fresh-alert official rulebook/regulatory sources.”
- “FTA and MoE/DNFBP AML remain Strong Fresh Signal families.”
- “VARA has 23 confirmed fresh-alert sources and remains two short of the 25-source Strong threshold.”
- “SCA has 4 confirmed fresh-alert sources; broader SCA coverage remains under remediation.”

## 18. Claims Still Forbidden

Forbidden:

- “Complete UAE coverage.”
- “Every family is Strong.”
- “Complete SCA coverage.”
- “Complete EOCN/TFS coverage.”
- “UAE FIU circulars are monitored.”
- “MoJ/Gazette monitoring is live.”
- “MoF monitoring is live.”
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

1. VARA enforcement/admin orders: find or build two more official fresh-alert endpoints.
2. EOCN/TFS: find or build three more official TFS/sanctions endpoints or prove the official public universe limit.
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

“156 fresh-alert eligible UAE official-source monitors with MONITOR_OK, proof records, hashes, baseline confirmation, and daily-check metadata.”

Do not sell complete UAE coverage or complete family coverage.
