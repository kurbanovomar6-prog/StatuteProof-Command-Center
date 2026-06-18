# Post-50 Source Distribution Audit

Date: 2026-06-16

## Executive Verdict

The source pack is credible enough for an internal demo and a cautious MLRO prospect demo, but it is not yet ideally balanced. The system has crossed the 50-source threshold honestly; the next commercial risk is concentration, especially CBUAE-heavy coverage.

## Source Counts

| Metric | Count |
| --- | ---: |
| Enabled UAE sources | 122 |
| Monitoring-active UAE sources | 121 |
| Under extraction remediation | 1 |

## Sources By Regulator

| Regulator / group | Monitoring-active count | Share |
| --- | ---: | ---: |
| CBUAE | 27 | 22.3% |
| DFSA/DIFC | 52 | 43.0% |
| ADGM/FSRA | 12 | 9.9% |
| VARA | 9 | 7.4% |
| UAE FIU / EOCN / AML / DNFBP | 14 | 11.6% |
| SCA | 5 | 4.1% |
| Federal / legislation / tax | 2 | 1.7% |
| Total | 121 | 100.0% |

## Sources By Source Type

| Source type | Count |
| --- | ---: |
| Rulebook / module / regulatory page | 83 |
| AML / sanctions / DNFBP | 17 |
| Legal database / law / regulation | 10 |
| Document / PDF listing | 7 |
| Data protection | 5 |
| Consultation | 1 |

## Concentration Risk

CBUAE concentration is **27 / 121 = 22.3%**.

This is commercially useful for banking, payments, AML/CFT, consumer protection, open finance, and prudential monitoring. The largest concentration has shifted from CBUAE to DFSA/DIFC after the weak-family bulk activation sprint. That is a real improvement for DIFC/DFSA buyers, but the pack is still not evenly balanced because FTA, SCA, FIU/EOCN, MoJ/Gazette, markets/exchanges, customs, courts, and federal privacy remain thin.

Risk rating: **medium concentration risk, now DFSA/DIFC-heavy rather than CBUAE-heavy**.

## Commercial Credibility Score

| Use case | Verdict | Score |
| --- | --- | ---: |
| Internal demo | Ready | 8.5/10 |
| MLRO prospect demo | Ready with family-depth caveat | 8/10 |
| $199 pilot | Ready for CBUAE/AML/DFSA/DIFC/ADGM-heavy prospects | 8.5/10 |
| $399 UAE Monitor | Stronger, still partial outside financial-regulator families | 7/10 |

## Brutally Honest Assessment

The pack is no longer a source-count toy. It has proof-backed, baseline-tested monitoring across 121 active UAE endpoints, and validators now protect source truth. But it is not yet a perfectly balanced UAE regulatory monitoring product. The next highest-value work is targeted weak-family adapters, not more DFSA/CBUAE endpoints.

## Weakest Commercial Zones

1. FTA/tax official document listings remain candidate-only.
2. SCA laws/decisions and FIU/EOCN live sources still need source-specific adapters.
3. MoJ/Gazette and federal privacy coverage remain thin or missing.
4. Markets/exchanges, customs, courts, and free-zone regulatory sources remain mostly candidate-only.
5. Source reliability trend visibility across 7/30/90-day windows is still a product gap.

## Recommended Positioning

Safe customer-facing wording:

"StatuteProof currently has 122 enabled UAE official-source endpoints, including 121 monitoring-active sources after proof, baseline, source-health, noise, and review gates. One source remains under remediation. FTA tax pages are candidates, not monitoring-active. Monitoring intelligence only, not legal advice."

Do not say:

- "60 validated sources."
- "Complete UAE regulatory coverage."
- "Never miss updates."
- "Perfect parsing."
- "Guaranteed compliance."
