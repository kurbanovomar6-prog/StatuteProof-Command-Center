# Mass Source Activation Live Validation Report

Date: 2026-06-15

## Scope

This was a controlled discovery/no-save validation check only.

Rules followed:

- no broad monitoring;
- no all-source monitor command;
- no evidence save;
- no Telegram/email/customer delivery;
- no public source truth change;
- no `sources.json` change.

## Targets Tested

| Target | Command Type | Result | Notes |
|---|---:|---|---|
| SCA latest regulations | `discover-source --json` | discovery succeeded | DOM investigator found table/listing signals. Recommended SCA/table paths exist, but same-domain discovery also surfaced low-value pages such as About/Services, so relevance filtering must be tightened before batch onboarding. |
| DFSA AML/MLRO | discovery via internal `discover_source()` | discovery succeeded | Final URL resolved to `/summary`. Recommended paths found, but DOM type was `unknown`; needs DOM/selector remediation before no-save. |
| ADGM financial crime | discovery via internal `discover_source()` and one `source-lab --no-save` | no-save extracted content but did not pass save gate | Discovery detected `custom_element`. No-save produced normalized length 4,788 and hash `fa442e94df6d70a8ecff211b9c8e35ee8cddc1120b119894c708d0cdbbfdeaf6`; quality was `LIMITED` at 59 and `can_save_evidence=false`, so it is not evidence-ready from this run. |
| CBUAE regulations | discovery via internal `discover_source()` | blocked/remediation | HTTP 403. Needs access/source-health remediation and possibly official alternate endpoint discovery. |
| VARA framework | discovery via internal `discover_source()` | stale/remediation | HTTP 404 for the tested framework URL. Needs official URL rediscovery before any parser work. |

Initial non-escalated discovery for DFSA/ADGM/CBUAE/VARA hit sandbox DNS failures. The same scoped discovery was rerun with approved escalated network access and produced the results above.

## Counts

- Live validation targets tested: 5.
- Discovery succeeded: 3.
- Discovery blocked/stale: 2.
- No-save attempted: 1.
- Strong no-save passed: 0.
- Saved evidence: 0.
- Activation-ready new sources: 0.

## Findings

1. Discovery is useful but still noisy.
   SCA generated useful table/listing signals, but link graph scoring also surfaced generic pages. Mass onboarding needs stricter buyer-relevance and source-type filtering before queue promotion.

2. ADGM extraction works partially but did not meet save gate.
   The page is meaningful and not nav-shell, but quality score 59 and `can_save_evidence=false` correctly blocked evidence save.

3. CBUAE and VARA need source-health/URL remediation before parser work.
   CBUAE returned 403; VARA tested URL returned 404.

4. No customer-facing source truth changed.
   The live checks produced remediation intelligence only.

## Next Live Sprint Recommendation

Run a dedicated source-specific remediation sprint for:

1. SCA relevance filtering and table/listing item extraction;
2. DFSA `/summary` DOM selector discovery;
3. CBUAE official alternate endpoint discovery for 403-safe access;
4. VARA official framework URL rediscovery.
