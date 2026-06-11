# Sprint 3E — Under-Validation Source Stability Report

## 1. Verdict

- This was validation-only.
- No sources were activated.
- Candidates tested: 5.
- Repeated runs per candidate: 3.
- Candidates that look stable enough for later activation decision review are listed below; none are active.
- Candidates not ready: 1.

## 2. Candidate stability table

| Candidate | URL | Runs passed | Status codes seen | Avg response time | Avg extracted chars | PDF links stable | WAF seen | Content signature stable | Verdict | Recommended next action |
| --- | --- | ---: | --- | ---: | ---: | --- | --- | --- | --- | --- |
| `ae-adgm-fsra-main` | https://www.adgm.com/financial-services-regulatory-authority | 3/3 | 200 | 1040 ms | 10934 | unknown | no | yes | needs_item_level_validation | Repeated checks are stable; map item-level URLs before activation review. |
| `ae-adgm-fsra-rulebook` | https://www.adgm.com/financial-services-regulatory-authority | 3/3 | 200 | 462 ms | 10934 | unknown | no | yes | needs_item_level_validation | Repeated checks are stable; map item-level URLs before activation review. |
| `ae-difc-laws` | https://www.difc.com/business/laws-and-regulations/ | 3/3 | 200 | 497 ms | 5956 | yes | no | yes | needs_pdf_validation | Run PDF link resolution and document extraction validation before any activation decision. |
| `ae-moet-aml-dnfbp` | https://www.moet.gov.ae/en/ | 3/3 | 200 | 2148 ms | 12003 | unknown | no | no | unstable | Title or normalized content signature changed across repeated checks. |
| `ae-cbuae-rulebook` | https://rulebook.centralbank.ae/ | 3/3 | 200 | 1562 ms | 2193 | yes | no | yes | needs_pdf_validation | Run PDF link resolution and document extraction validation before any activation decision. |

## 3. Stable candidates for later activation decision

- None. No candidate should move to activation decision review from this run.

## 4. Candidates requiring more work

### needs item-level validation

- `ae-adgm-fsra-main` — Repeated checks are stable; map item-level URLs before activation review.
- `ae-adgm-fsra-rulebook` — Repeated checks are stable; map item-level URLs before activation review.

### needs PDF validation

- `ae-difc-laws` — Run PDF link resolution and document extraction validation before any activation decision.
- `ae-cbuae-rulebook` — Run PDF link resolution and document extraction validation before any activation decision.

### needs WAF workaround

- None.

### unstable/blocked

- `ae-moet-aml-dnfbp` — Title or normalized content signature changed across repeated checks.

### manual review required

- None.

## 5. Activation decision gate for future Sprint 3F

Before any source can be activated, all of the following must be true:

- Repeated stability pass.
- Item-level URL confirmed.
- Extraction quality above threshold.
- Proof/diff output tested.
- Limitation note written.
- Source transparency report updated.
- Human review gate confirmed.

## 6. Recommended Sprint 3F

Run item-level validation first. Generic source pages are not ready for activation decision review.
