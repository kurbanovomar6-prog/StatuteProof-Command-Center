# UAE Adapter Remediation Report

Date: 2026-06-14

## 1. Executive Verdict

Adapter platform improvements were validated against a small scoped live set:

- ADGM/FSRA financial crime page: custom-element adapter no-save passed.
- ADGM/FSRA rules/regulations page: custom-element adapter no-save passed.
- SCA latest regulations: listing adapter no-save still failed to isolate rows and remained blocked/remediation.

This is useful progress, but not a 50-source breakthrough. Public source truth remains unchanged:

`13 enabled UAE sources / 9 readiness-supported / 4 under extraction remediation`

## 2. Live No-Save Smoke Results

| Source | URL | Adapter | Result | Notes |
|---|---|---|---|---|
| ADGM/FSRA financial crime prevention | `https://www.adgm.com/operating-in-adgm/financial-and-cyber-crime-prevention` | `custom_element` with `adgm-page > span` | no-save passed | 4,819 normalized chars, no nav-shell, no hash collision, `can_save_for_validation=true`, baseline required. |
| ADGM/FSRA rules and regulations | `https://www.adgm.com/legal-framework/rules-and-regulations` | `custom_element` with `adgm-page > span` | no-save passed | 1,876 normalized chars, no nav-shell, no hash collision, `can_save_for_validation=true`, baseline required. |
| SCA latest regulations | `https://www.sca.gov.ae/en/regulations/regulations` | `listing` with `[data-icms-list]` config | remediation | Adapter did not isolate item rows. Generic text was present but Source Lab stayed blocked because policy warnings were triggered. |

## 3. ADGM / FSRA Findings

The `custom_element` adapter is a good fit for ADGM rendered pages where meaningful text is exposed inside `adgm-page > span`.

Recommended next actions:

- Use this adapter family for ADGM page-level sources.
- Keep evidence/baseline gates unchanged.
- Do not expand `sources.json` until activation decision policy is complete.

## 4. SCA Findings

SCA remains harder than ADGM. The generic page text can be extracted, but the listing adapter did not isolate stable item rows in this live smoke.

Likely issue:

- The rendered page exposes enough text for generic extraction, but stable row/container markup is not available in a simple BeautifulSoup parse of `page.content()`.

Recommended next actions:

- Browser/DOM investigation for actual rendered SCA item structure.
- Check whether list items are rendered through shadow DOM, client-side data, or a script-backed API.
- Build an SCA-specific listing adapter only if the public rendered data source is official and accessible without bypassing controls.
- Keep SCA latest regulations in remediation until item-level extraction, noise risk, and source-health risk pass.

## 5. DFSA / CBUAE / VARA / FIU

No new live checks were run for these groups in this sprint. Adapter families now provide a platform for future remediation, but no source in these groups gained readiness or activation status.

## 6. Source Monitor Gate

ADGM custom-element sources:
- PASS for no-save extraction path.
- HOLD for activation count changes until proof/baseline status is tied to source registry policy.

SCA latest regulations:
- HOLD. Official source remains useful, but current listing extraction is not stable enough.

## 7. Evidence Trail Gate

All live checks in this adapter sprint were no-save. Evidence level remains `PREVIEW_ONLY` for the live checks performed in this run.

Previously saved ADGM/SCA proof artifacts are not invalidated, but this sprint did not create new proof artifacts.

## 8. QA / Critic Gate

Pass:
- Adapter metadata is visible.
- No-save is still preview-only.
- SCA did not get promoted despite partial extraction.

Hold:
- 50-source pack remains far below working threshold.

## 9. Legal Language Gate

Allowed wording:

- “Adapter platform improved for official-source onboarding.”
- “ADGM custom-element adapter passed scoped no-save checks.”
- “SCA latest regulations remains under extraction remediation.”

Forbidden wording:

- “50 UAE sources are working.”
- “60 sources validated.”
- “SCA is ready.”
- “Any website can be parsed.”
- “Certified monitoring.”

## 10. sources.json Decision

Changed: no.

Reason:

The adapter platform improves testing and remediation, but does not by itself create evidence-confirmed or monitoring-ready sources. `sources.json` should only change after proof/baseline and agent gates pass under the existing source-readiness policy.
