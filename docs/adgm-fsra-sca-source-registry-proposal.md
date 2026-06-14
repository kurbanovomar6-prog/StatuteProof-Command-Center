# ADGM/FSRA + SCA Source Registry Proposal

## 1. Decision

Do not change `product/regradar/sources.json` in this sprint.

The ADGM/FSRA and SCA work produced useful no-save extraction candidates, but no source is evidence-confirmed and no source is monitoring-ready. The correct place for this sprint's result is the candidate registry:

`product/regradar/config/uae_source_candidates.json`

Current public truth remains:

**13 enabled UAE sources / 9 readiness-supported / 4 under extraction remediation.**

## 2. Proposed ADGM/FSRA Registry Model

| Proposed source ID | URL | Wait selector | Content selector | Proposed status | Reason |
|---|---|---|---|---|---|
| `AE-adgm-fsra-rulebooks` | `https://www.adgm.com/legal-framework/rules-and-regulations` | `adgm-page > span` | `adgm-page > span` | `readiness_supported_no_save` | Official ADGM rules/regulations page extracted meaningful rulebook index text. Save/proof and baseline still required. |
| `AE-adgm-fsra-guidance-policy` | `https://www.adgm.com/legal-framework/guidance-and-policy-statements` | `adgm-page > span` | `adgm-page > span` | `readiness_supported_no_save`, not default-pack accepted yet | Official guidance page extracted meaningful text, but high listing noise requires item-level filters. |
| `AE-adgm-fsra-consultations` | `https://www.adgm.com/legal-framework/public-consultations` | `adgm-page > span` | `adgm-page > span` | `readiness_supported_no_save`, not default-pack accepted yet | Official consultation archive extracted meaningful text, but whole-page diffs would be noisy. |
| `AE-adgm-fsra-financial-crime-prevention` | `https://www.adgm.com/operating-in-adgm/financial-and-cyber-crime-prevention` | `adgm-page > span` | `adgm-page > span` | `readiness_supported_no_save` | Strong MLRO-relevant official AML/TFS and financial-crime page. |
| `AE-adgm-fsra-enforcement` | `https://www.adgm.com/operating-in-adgm/additional-obligations-of-financial-services-entities` | `adgm-page > span` | `adgm-page > span` | `readiness_supported_no_save`, model review needed | Extractable, but this URL is broader than pure enforcement. Rename or split before activation. |
| `AE-adgm-fsra-public-register` | `https://www.adgm.com/public-registers` | `adgm-page > span` | `adgm-page > span` | `remediation` | Extractable but shallow. Treat as a register/search adapter source, not a normal text page. |

## 3. Proposed SCA Registry Model

| Proposed source ID | URL | Wait selector | Content selector | Proposed status | Reason |
|---|---|---|---|---|---|
| `AE-sca-latest-regulations` | `https://www.sca.gov.ae/en/regulations/regulations` | `[data-icms-list]` | `[data-icms-list]` | `readiness_supported_no_save` | Official SCA latest-regulations listing. Must be monitored as a listing, not a full-page text source. |
| `AE-sca-aml-cft` | `https://www.sca.gov.ae/en/regulations/anti-money-laundering-and-terrorist-financing` | `[data-icms-list]` | `[data-icms-list]` | `readiness_supported_no_save` | Strong official AML/CFT page. Site chrome says CMA, but the official domain and source owner are UAE SCA. |
| `AE-sca-circulars-rules-procedures` | `https://www.sca.gov.ae/en/regulations/circulars-rules-and-procedures` | `main section` | `main section` | `remediation` | Correct current URL was found, but current extraction is too shallow for activation. Needs item/card adapter. |
| `AE-sca-regulations-listing` | `https://www.sca.gov.ae/en/regulations/regulations-listing` | to be determined | to be determined | `remediation` | Official filter/listing page is useful but selectors are unstable and full `main` includes CAPTCHA-sensitive chrome. |

## 4. Legacy URLs To Avoid

ADGM legacy URLs that should not be activated from the previous candidate map:

- `https://www.adgm.com/fsra/rules-and-regulations`
- `https://www.adgm.com/fsra/guidance-and-policy-statements`
- `https://www.adgm.com/fsra/notices`
- `https://www.adgm.com/fsra/consultations`

SCA legacy URLs that should not be activated from the previous candidate map:

- `https://www.sca.gov.ae/en/legislation.aspx`
- `https://www.sca.gov.ae/en/legislation/sca-decisions.aspx`
- `https://www.sca.gov.ae/en/legislation/laws.aspx`
- `https://www.sca.gov.ae/en/legislation/regulations.aspx`
- `https://www.sca.gov.ae/en/circulars.aspx`

These URLs produced 404 shells, service-directory shells, or duplicate noisy hashes in the top-40 sprint.

## 5. Why Not Active Yet

The passing candidates are no-save Source Lab results only. They are not active sources because:

- no proof artifacts were saved;
- no evidence baseline exists;
- no append-only source-run history exists;
- no item-level noise filters exist for noisy listings;
- no customer-facing readiness report has promoted these sources;
- no founder approval has been recorded for a source-pack expansion.

## 6. Next Registry Action

Run a saved-evidence baseline sprint for the strongest no-save candidates only:

1. `AE-adgm-fsra-financial-crime-prevention`
2. `AE-adgm-fsra-rulebooks`
3. `AE-sca-aml-cft`
4. `AE-sca-latest-regulations`

After those saved baselines pass, update `sources.json` conservatively with explicit status, selectors, expected minimum lengths, remediation notes, and evidence-readiness boundaries.
