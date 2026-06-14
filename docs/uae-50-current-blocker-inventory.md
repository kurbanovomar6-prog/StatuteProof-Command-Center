# UAE 50 Current Blocker Inventory

Date: 2026-06-14

## 1. Current Activation-Ready Sources

Current agent-gated work queue activation-ready count: **2**.

| source_id | regulator | URL | proof/baseline state | blocker before public activation |
|---|---|---|---|---|
| `AE-adgm-fsra-financial-crime-prevention` | ADGM/FSRA | `https://www.adgm.com/operating-in-adgm/financial-and-cyber-crime-prevention` | proof-backed, baseline complete, queue activation-ready | Requires founder/source-registry approval before `sources.json` expansion. |
| `AE-adgm-fsra-rulebooks` | ADGM/FSRA | `https://www.adgm.com/legal-framework/rules-and-regulations` | proof-backed, baseline complete, queue activation-ready | Requires source model decision and possible dedupe with ADGM legal-framework rules. |

## 2. Candidates Close To Activation

These are not activation-ready. They are the nearest next candidates because at least one no-save path or previous extraction signal exists.

| source_id | regulator | current state | blocker | quickest next action |
|---|---|---|---|---|
| `AE-adgm-fsra-enforcement` | ADGM/FSRA | no-save passed | Source label is broader than pure enforcement; evidence missing. | Confirm source model, run custom-element no-save, then save baseline if label is acceptable. |
| `AE-adgm-fsra-guidance-policy` | ADGM/FSRA | no-save passed | High listing/document-list noise; evidence missing. | Add listing/link normalization and noise filters, then save baseline. |
| `AE-adgm-fsra-consultations` | ADGM/FSRA | no-save passed | High consultation archive noise; evidence missing. | Add item-level status/date/title extraction before save. |
| `AE-adgm-legal-framework-rules` | ADGM | no-save passed | Overlaps with `AE-adgm-fsra-rulebooks`. | Choose canonical ID or split clearly before save. |
| `AE-dfsa-aml-mlro-notices` | DFSA | no-save passed | Evidence and baseline missing; listing noise medium. | Build DFSA listing adapter config and save baseline. |
| `AE-dfsa-rulebook-thomsonreuters` | DFSA | no-save passed | Evidence and baseline missing; adapter metadata not configured. | Add rulebook/module adapter and save baseline. |

## 3. Candidates Blocked By Adapter Issues

| group | source_ids | blocker |
|---|---|---|
| SCA | `AE-sca-latest-regulations`, `AE-sca-aml-cft`, `AE-sca-circulars`, `AE-sca-laws`, `AE-sca-decisions`, `AE-sca-legislation`, `AE-sca-regulations` | SCA pages expose useful text but current generic listing adapter does not isolate stable item rows; policy warnings/source-health remain unresolved. |
| DFSA | `AE-dfsa-enforcement-regulatory-actions`, `AE-dfsa-consultation-papers`, `AE-dfsa-rulebook-official`, `AE-dfsa-notices` | Several configured URLs are shell/blocked/404 or need model split; rulebook needs module adapter. |
| CBUAE | `AE-cbuae-regulations`, `AE-cbuae-publications`, `AE-cbuae-consultations`, `AE-cbuae-aml-cft`, `AE-cbuae-payment-systems`, `AE-cbuae-licensing` | Public pages are widget/chrome-heavy or blocked-like; need CBUAE listing/document adapter and likely official rulebook URLs. |
| VARA | `AE-vara-enforcement`, `AE-vara-regulatory-framework`, `AE-vara-rulebooks-overview`, `AE-vara-company-rulebook`, `AE-vara-aml-cft-rulebook`, `AE-vara-public-register` | Many current URLs returned nav/not-found shells; needs official URL cleanup plus PDF/rulebook listing adapter. |
| FIU/EOCN/MoE | `AE-uaefiu-publications`, `AE-uaefiu-goaml-public`, `AE-uaefiu-laws-regulations`, `AE-eocn-homepage`, `AE-moec-aml` | Search/chrome-heavy or blocked-like pages; need document-listing adapter and source URL refinement. |

## 4. Blocked By Source-Health Risk

High source-health risk currently dominates:

- 21 work-queue entries are blocked.
- 21 work-queue entries are remediation.
- SCA latest regulations has proof and baselines but remains remediation because listing/source-health risk is high.
- CBUAE, VARA, FIU, EOCN, MoE, MoF, and UAE legislation pages need either better official endpoints or source-specific adapters.

## 5. Blocked By Noise Risk

High-noise categories:

- Long archive/listing pages with changing counters.
- Consultations and notices pages with status/listing churn.
- Homepage-like regulator pages.
- Search/service shell pages.
- Rulebook module listings without module-level hashes.

High noise blocks activation unless item-level diff filters exist.

## 6. Blocked By Proof / Baseline Missing

The biggest evidence gap:

- 78 work-queue entries exist.
- 3 are proof-backed.
- 3 are baseline-complete.
- 2 are activation-ready.

Even if no-save tests improved quickly, activation count cannot move toward 50 without saved proof and repeat baselines.

## 7. Exact Source-Specific Adapters Needed

P0:

- SCA rendered/listing adapter.
- DFSA rulebook/module adapter.
- DFSA AML/MLRO listing adapter.
- ADGM listing/link normalization adapter.

P1:

- CBUAE document/listing adapter.
- VARA PDF/rulebook/enforcement listing adapter.
- FIU/EOCN document listing adapter.

P2:

- PDF listing + shallow/OCR classification.
- Register adapter for public registers.
- Screenshot/WARC evidence enrichment.

## 8. Quickest Route To 50 If Possible

The honest quickest route is not “activate 50 now.” It is:

1. Activate the 2 ADGM candidates only after source-registry approval.
2. Convert the 6 baseline-pending/no-save candidates into proof-backed baselines.
3. Fix SCA listing extraction and retest 5-7 SCA candidates.
4. Add DFSA module/listing adapters and baseline 2-4 DFSA candidates.
5. Add CBUAE/VARA/FIU document listing adapters and run controlled no-save tests.
6. Repeat baselines for every passing source.

Best-case near-term activation count after this sprint is likely **2-8**, not 50, unless many official endpoints unexpectedly pass no-save and saved baseline gates. A true 50-source pack requires multiple focused remediation/baseline cycles.
