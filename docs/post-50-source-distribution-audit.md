# Post-50 Source Distribution Audit

Date: 2026-06-16

## Executive Verdict

The source pack is credible enough for an internal demo and a cautious MLRO prospect demo, but it is not yet ideally balanced. The system has crossed the 50-source threshold honestly; the next commercial risk is concentration, especially CBUAE-heavy coverage.

## Source Counts

| Metric | Count |
| --- | ---: |
| Enabled UAE sources | 147 |
| Monitoring-active UAE sources | 146 |
| Under extraction remediation | 1 |

## Sources By Regulator

| Regulator / group | Monitoring-active count | Share |
| --- | ---: | ---: |
| CBUAE | 27 | 18.5% |
| DFSA/DIFC | 52 | 35.6% |
| ADGM/FSRA | 12 | 8.2% |
| VARA | 9 | 6.2% |
| UAE FIU / EOCN / AML / DNFBP | 14 | 9.6% |
| SCA | 5 | 3.4% |
| Federal / legislation / tax | 27 | 18.5% |
| Total | 146 | 100.0% |

## Sources By Source Type

| Source type | Count |
| --- | ---: |
| Rulebook / module / regulatory page | 83 |
| AML / sanctions / DNFBP | 17 |
| Legal database / law / regulation | 10 |
| Document / PDF listing | 32 |
| Data protection | 5 |
| Consultation | 1 |

## Concentration Risk

CBUAE concentration is **27 / 146 = 18.5%**.

This is commercially useful for banking, payments, AML/CFT, consumer protection, open finance, prudential monitoring, and selected tax-document monitoring. The largest concentration remains DFSA/DIFC after the weak-family bulk activation sprint, while FTA is now materially stronger due to 25 direct official PDF endpoints. The pack is still not evenly balanced because SCA, FIU/EOCN, MoJ/Gazette, markets/exchanges, customs, courts, and federal privacy remain thin.

Risk rating: **medium concentration risk, now DFSA/DIFC-heavy rather than CBUAE-heavy**.

## Commercial Credibility Score

| Use case | Verdict | Score |
| --- | --- | ---: |
| Internal demo | Ready | 8.5/10 |
| MLRO prospect demo | Ready with family-depth caveat | 8/10 |
| $199 pilot | Ready for CBUAE/AML/DFSA/DIFC/ADGM-heavy prospects | 8.5/10 |
| $399 UAE Monitor | Stronger, still partial outside financial-regulator/tax families | 7.3/10 |

## Brutally Honest Assessment

The pack is no longer a source-count toy. It has proof-backed, baseline-tested monitoring across 146 active UAE endpoints, and validators now protect source truth. FTA is no longer a zero-coverage family. But it is not yet a perfectly balanced UAE regulatory monitoring product. The next highest-value work is targeted SCA, FIU/EOCN, VARA guidance/admin-order, DIFC/ADGM document-hub, MoJ/Gazette, and federal privacy adapters.

## Weakest Commercial Zones

1. SCA laws/decisions and FIU/EOCN live sources still need source-specific adapters.
2. FTA listing pages and pagination remain candidate-only even though 25 direct FTA PDFs are now monitoring-active.
3. MoJ/Gazette and federal privacy coverage remain thin or missing.
4. Markets/exchanges, customs, courts, and free-zone regulatory sources remain mostly candidate-only.
5. Source reliability trend visibility across 7/30/90-day windows is still a product gap.

## Recommended Positioning

Safe customer-facing wording:

"StatuteProof currently has 147 enabled UAE official-source endpoints, including 146 monitoring-active sources after proof, baseline, source-health, noise, and review gates. One source remains under remediation. FTA direct official tax PDFs are monitoring-active; broader FTA listing pages remain candidate/adapter work. Monitoring intelligence only, not legal advice."

Do not say:

- "60 validated sources."
- "Complete UAE regulatory coverage."
- "Never miss updates."
- "Perfect parsing."
- "Guaranteed compliance."
