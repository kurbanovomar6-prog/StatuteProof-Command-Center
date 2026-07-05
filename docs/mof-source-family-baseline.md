# MoF Source Family Baseline

Date: 2026-06-21

## Baseline Verdict

- MoF score before this sprint: 4.0/10
- Baseline source family state: weak, but not empty
- Actual MoF source rows before activation: 4
- Fresh-alert sources before activation: 3
- Evidence-library rows before activation: 1
- Candidate rows before activation: 0
- Remediation rows before activation: 0
- Canonical evidence records before activation: 3
- Alert-linked MoF canonical evidence before activation: 0

MoF must not borrow FTA, Ministry of Economy, DIFC, or tax-adjacent non-MoF
sources. The only rows counted here are MoF-owned `mof.gov.ae` rows and the
generic UAE Ministry of Finance evidence-library homepage.

## Source Rows Before This Sprint

| Source ID | URL | Mode | Status | Alert eligible | Proof / hash / baseline |
| --- | --- | --- | --- | --- | --- |
| `AE-uae-ministry-of-finance` | `https://mof.gov.ae/` | evidence-library | active | false | No source-level proof path on the row; generic homepage only |
| `AE-mof-publications-and-releases` | `https://mof.gov.ae/en/media-center/publications-and-releases` | fresh-alert | active | true | Proof-backed, baseline 2/2, MONITOR_OK, hash `9969f3f74f2b718032f0b6f3e3a2d57c0ff1ec1617f10298de2351b8906b506e` |
| `AE-mof-financial-legislation` | `https://mof.gov.ae/en/financial-legislation` | fresh-alert | active | true | Proof-backed, baseline 2/2, MONITOR_OK, hash `98775e38247a313be2d05cc3de840bd90afadb0b468e78d1e4196f92526a7aad` |
| `AE-mof-esr` | `https://mof.gov.ae/en/public-finance/international-relations/economic-substance-regulations/` | fresh-alert | active | true | Proof-backed, baseline 2/2, MONITOR_OK, hash `b8eac4a534b0d8485170dc026b218a8b0d06f5584c12385cc61c63bf93a904db` |

## Saved Runs Before This Sprint

The three existing MoF fresh-alert sources each had a FIRST_SEEN run and a
stable UNCHANGED baseline run. The generic homepage had older source runs but
remained evidence-library, not fresh-alert eligible.

## Queued Alerts Before This Sprint

One MoF-family queued alert existed for `AE-uae-ministry-of-finance`, but it was
the generic evidence-library homepage and had no `evidence_record_id`. It was
not safe to treat it as a fresh-alert MoF brief path.

## Canonical Evidence Before This Sprint

- `evr_AE-mof-publications-and-releases_intake-20260619T174253Z`
- `evr_AE-mof-financial-legislation_intake-20260620T092307Z`
- `evr_AE-mof-esr_intake-20260620T101409Z`

All were complete and hash-verifiable, but pending review.

## What Blocked 6/10

- Only 3 fresh-alert sources.
- No alert linkage for MoF fresh-alert sources.
- Generic MoF homepage alert was not a usable fresh-alert proof path.
- No human/operator review decisions on MoF evidence.

## What Blocked 7/10

- Too few high-value MoF source types.
- No additional official MoF pages had proof-backed repeat baselines.
- No new MoF canonical evidence examples for tax-policy pages.
- Broad MoF/tax coverage could not be claimed safely.

## What Blocked 8/10

- No multiple reviewed MoF evidence examples.
- No exact alert linkage for new MoF sources.
- Open Data, DTAs, public debt, budget archive, and broad publication categories
  still require source-specific proof/baseline or remain held.

## Safe Claim Before This Sprint

Three selected MoF official sources plus an evidence-library homepage.

## Forbidden Claim Before This Sprint

Broad MoF coverage, complete MoF coverage, complete tax coverage, or complete
financial legislation monitoring.
