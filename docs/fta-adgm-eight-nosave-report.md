# FTA / ADGM Eight No-Save Report

Date: 2026-06-18

## Summary

Eight dirty active rows were retested with controlled no-save Source Lab checks. No evidence was saved during this phase.

Result:

- Strong no-save passes: 2
- Failed / remediation-needed no-save checks: 6
- Sources allowed to proceed to evidence/baseline: 2
- Sources not allowed to remain active from no-save alone: 8

## Results

| source_id | Source | Status | Quality | Normalized length | Hash | Can save evidence | Risk / blocker | Recommendation |
|---|---|---:|---:|---:|---|---|---|---|
| `AE-fta-tax-legislation-listing` | FTA All Tax Legislation | `NAV_SHELL_ONLY` | 0 / `POOR` | 35 | `018073a2d206e44dc1b8e8a52df55cb85f56ee7f204ab89572a0fe762e0d342c` | No | Rendered page produced title/nav-shell only. | Candidate only; needs FTA-specific item-level extraction. |
| `AE-fta-vat-guides-references` | FTA VAT Guides and References | `NAV_SHELL_ONLY` | 0 / `POOR` | 66 | `664c17c325c77da52acb1280c47c05f983b2b7c6a01b0c10290a704f6ef442ad` | No | Rendered page produced title/nav-shell only. | Candidate only; needs FTA-specific item-level extraction. |
| `AE-fta-corporate-tax-guides-references` | FTA Corporate Tax Guides and References | `NAV_SHELL_ONLY` | 0 / `POOR` | 37 | `4d12d5e4ba05940225f3a1f6e9f9cb45d1bc961a925a55c2aa099eb5d1549703` | No | Rendered page produced title/nav-shell only. | Candidate only; needs FTA-specific item-level extraction. |
| `AE-fta-media-centre` | FTA Media Centre | `NAV_SHELL_ONLY` | 0 / `POOR` | 36 | `f207d71a8b4633ef14ce203c132cc835726a2f7a8e19d659bd2eb7427ef2bf13` | No | Rendered page produced title/nav-shell only. | Candidate only; needs FTA-specific item-level extraction. |
| `AE-fta-corporate-tax-legislation` | FTA Corporate Tax Legislation | `NAV_SHELL_ONLY` | 0 / `POOR` | 11 | `f040781d8221f3ef7dfff9cb94d55d638872002437e3f5b121c95809ff9c241d` | No | Rendered page produced title/nav-shell only. | Candidate only; needs FTA-specific item-level extraction. |
| `AE-adgm-fsra-supervision-circulars` | ADGM FSRA Supervision Circulars | `CONFIRMED_ACCESSIBLE` | 65 / `ACCEPTABLE` | 4,765 | `6c1e3f3f4634f70efc0e61fd627649059dd23ea6fcd4f53ab23240e7bfdeef00` | Yes | Public `adgm-page` listing produced 10 circular/document rows. | Proceed to evidence/baseline. |
| `AE-adgm-fsra-regulatory-alerts` | ADGM FSRA Regulatory Alerts | `NAV_SHELL_ONLY` | 0 / `POOR` | 4,138 | `2d2b9c7bea4d0357d2bed3b469c6f82c82440d946f93bd8f43607ff38cc39d90` | No | Official page is public, but configured listing isolated no regulatory alert rows and output stayed nav-shell-like. | Candidate only; needs source-specific selector/listing investigation. |
| `AE-adgm-data-protection-regulations-2021-pdf` | ADGM Data Protection Regulations 2021 PDF | `CONFIRMED_ACCESSIBLE` | 61 / `ACCEPTABLE` | 10,670 | `cdaa340d5523440c1b15bb8b3d11f78b0e330e0a7c53fb68c01606ff8b44d6d5` | Yes | Direct official PDF extraction is meaningful after line-preserving PDF normalization. | Proceed to evidence/baseline. |

## FTA Finding

The five FTA pages are public URLs, but the current Source Lab extraction path returns rendered title/nav-shell content, not item-level tax document listings. They should remain candidates until an FTA-specific rendered document-listing adapter or public unauthenticated data endpoint is proven.

## ADGM Finding

- `AE-adgm-fsra-supervision-circulars` is strong enough to save evidence.
- `AE-adgm-fsra-regulatory-alerts` is not strong enough: the page is official/public, but the current selector does not isolate alert rows.
- `AE-adgm-data-protection-regulations-2021-pdf` is strong enough to save evidence after the PDF adapter preserves document line structure.

Monitoring intelligence only. Not legal advice.
