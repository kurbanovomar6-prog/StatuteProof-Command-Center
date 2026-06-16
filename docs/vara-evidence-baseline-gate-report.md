# VARA Evidence Baseline Gate Report

Date: 2026-06-16

## Activated Sources

All six sources below have:

- strong no-save pass;
- saved proof/evidence;
- two saved baseline runs;
- stable normalized hash;
- mass-monitor dry-run `MONITOR_OK`;
- Source Monitor, Evidence Trail, QA/Critic, Legal Language, Product Manager, and Code Architect gates emulated as pass.

| Source ID | Proof path | Baseline | MONITOR_OK |
| --- | --- | ---: | --- |
| `AE-vara-compliance-risk-rulebook-pdf` | `data/source_snapshots/2026-06-16/AE/AE-vara-compliance-risk-rulebook-pdf/intake-20260616T124723Z/proof.json` | 2/2 | yes |
| `AE-vara-technology-information-rulebook-pdf` | `data/source_snapshots/2026-06-16/AE/AE-vara-technology-information-rulebook-pdf/intake-20260616T124725Z/proof.json` | 2/2 | yes |
| `AE-vara-va-issuance-rulebook-pdf` | `data/source_snapshots/2026-06-16/AE/AE-vara-va-issuance-rulebook-pdf/intake-20260616T124726Z/proof.json` | 2/2 | yes |
| `AE-vara-broker-dealer-rulebook-pdf` | `data/source_snapshots/2026-06-16/AE/AE-vara-broker-dealer-rulebook-pdf/intake-20260616T124728Z/proof.json` | 2/2 | yes |
| `AE-vara-lending-borrowing-rulebook-pdf` | `data/source_snapshots/2026-06-16/AE/AE-vara-lending-borrowing-rulebook-pdf/intake-20260616T124758Z/proof.json` | 2/2 | yes |
| `AE-vara-va-regulations-2023-pdf` | `data/source_snapshots/2026-06-16/AE/AE-vara-va-regulations-2023-pdf/intake-20260616T124800Z/proof.json` | 2/2 | yes |

## Agent Gate Decisions

- Source Monitor: pass. Official/public `rulebooks.vara.ae` PDFs, no private access, no CAPTCHA/paywall.
- Evidence Trail: pass. Proof paths exist and repeat baseline is complete.
- QA/Critic: pass. No nav-shell, no shallow output, no duplicate shell hash, no high unresolved risk.
- Legal Language: pass. Wording remains monitoring intelligence only, not legal advice.
- Product Manager: pass. High VASP MLRO relevance.
- Code Architect: pass. Reuses existing document extractor and source-intake adapter pattern.
