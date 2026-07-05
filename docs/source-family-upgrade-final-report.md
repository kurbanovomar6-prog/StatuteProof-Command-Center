# StatuteProof Source Family Upgrade Final Report

Date: 2026-06-21

## Chosen Family

UAE FIU.

## Why Chosen

UAE FIU matters directly to MLRO buyers, and the most important remaining
family-level ambiguity was the `AE-uaefiu-circulars` candidate. If this source
could be proven, FIU readiness would improve materially. If it could not be
proven, the honest improvement was to tighten the blocker and remove misleading
metadata.

## Rejected Families

- DIFC: next best target, but not selected because UAE FIU circulars were the
  highest-risk current claim ambiguity.
- ADGM/FSRA: useful, but candidate-row work is a separate sprint.
- SCA: parser-review task, not the best source-family metadata sprint.
- DFSA: stronger than FIU and better suited for a canonical evidence expansion
  sprint.
- MoF: thin family, lower commercial priority for MLRO-first outreach.
- MoJ/Gazette: still remediation/access-constrained.

## Methods Attempted

1. Clean-gate validation.
2. Agent launch attempt.
3. UAE FIU source-row audit.
4. UAE FIU saved-run/proof audit.
5. Public page redirect/content check.
6. Public link extraction from the current FIU publications page.
7. Official `robots.txt` and English sitemap inspection.
8. Source Lab no-save test for `AE-uaefiu-circulars`.
9. Source registry metadata correction.
10. Source audit/frontend limitation update.

## Unsafe Methods Rejected

- Broad crawl.
- Bypassing Cloudflare, WAF, login, CAPTCHA, or private endpoints.
- Activating from no-save.
- Treating old saved runs as proof of a circulars endpoint.
- Claiming FIU circulars monitored.
- Claiming complete UAE FIU coverage.

## Source IDs Inspected

- `AE-uaefiu-circulars`
- `AE-uaefiu-guidance`
- `AE-uaefiu-publications-hub`
- `AE-uaefiu-typology-reports`
- `AE-uaefiu-system-guides`
- `AE-uaefiu-aml-cft-laws`
- `AE-uaefiu-annual-reports`
- `AE-uaefiu-press-releases`
- `AE-uae-financial-intelligence-unit-uaefiu`

## Source IDs Added

None.

## Source IDs Changed

Metadata only:

- `AE-uaefiu-circulars`
  - Name changed from a circulars/notices claim to a publications-index held
    candidate.
  - Notes now document the exact blocker and safe checks.
  - Fresh-signal reason now says it is not a distinct circulars/notices monitor.

- `AE-uaefiu-guidance`
  - Name and notes now say it is a disabled duplicate alias, not a distinct AML
    guidance or circulars source.

## Source IDs Held

All UAE FIU source monitoring modes remain unchanged.

## Source IDs Downgraded

None.

## Proof Created

No new proof artifact was created.

Reason: the live Source Lab no-save result was `NAV_SHELL_ONLY` and therefore
not eligible for save-proof or activation.

## Canonical Evidence Created

No.

Reason: this sprint targeted whether `AE-uaefiu-circulars` could be honestly
treated as a circulars/notices source. It could not.

## Alert Linked

No.

Reason: no new canonical evidence record was created.

## Internal Digest / Brief Generated

No internal brief was generated.

Existing verified digest remains valid after source metadata correction.

## Score Before / After

UAE FIU:

- Before: 6.2/10
- After: 6.3/10

Overall source-monitoring readiness:

- Before: 68/100
- After: 68/100

This is a truth/readiness-control improvement, not a material monitoring breadth
increase.

## Apollo Impact

Apollo is safer because the product no longer carries a misleading
`UAE FIU Circulars and Notices` source label.

Safe Apollo language:

> selected UAE FIU publications and typology-report monitoring, with explicit
> disclosure that FIU circulars/notices are not currently a proven monitored
> source.

Unsafe Apollo language:

> UAE FIU circulars monitored.

> Complete UAE FIU coverage.

> Every UAE AML/FIU update captured.

## Safe ICPs

- UAE MLROs who care about selected FIU publications, typology reports, AML/CFT
  laws, and system-guide monitoring.
- VASP/DNFBP compliance teams that accept a selected-source pilot.
- Design partners who value evidence gates and disclosed limitations.

## Unsafe ICPs

- Buyers who specifically require FIU circulars/notices monitoring today.
- Buyers requiring complete UAE FIU coverage.
- Buyers requiring production SLA, CI/CD history, or customer-delivery proof.

## Exact Next Source Task

DIFC legal database/listing proof sprint.

Alternative: ADGM/FSRA candidate rows if the founder wants to prioritize ADGM.

## Exact Next Evidence Task

Founder/operator review of:

- `evr_AE-uaefiu-typology-reports_intake-20260619T150224Z`

That evidence record remains pending and should not enter a customer brief until
review verifies whether the apparent typology-report removal is real or parser
noise.

## Exact Next Sales Task

Update Apollo copy to explicitly say:

> selected-source AML/FIU monitoring

and never:

> FIU circular monitoring

until a distinct official circulars/notices endpoint is proven.

## Final Boundary

This sprint made the UAE FIU family harder to misrepresent. It did not make UAE
FIU complete, did not add source breadth, and did not approve customer delivery.
