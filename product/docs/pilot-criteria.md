# StatuteProof Pilot Criteria

_Last updated: 2026-06-12_

## What is monitored

Current UAE source-readiness framing: 13 enabled sources, 10 confirmed, and 3 under extraction remediation. Only confirmed sources are covered in a pilot after scope is agreed.

| Regulator | Jurisdiction | Source |
|---|---|---|
| CBUAE Main | UAE Federal | Confirmed |
| CBUAE Regulations | UAE Federal | Confirmed |
| UAE Ministry of Finance | UAE Federal | Confirmed |
| VARA Main | Dubai / VARA | Confirmed |
| VARA Enforcement Notices | Dubai / VARA | Confirmed |
| ADGM FSRA Main | ADGM / FSRA | Confirmed |
| UAE FIU Circulars | UAE Federal | Confirmed |
| DIFC Laws Portal | DIFC / DFSA | Confirmed |
| UAE Legislation Portal | UAE Federal | Confirmed |
| UAE Ministry of Economy | UAE Federal | Confirmed |
| DFSA Rulebook | DIFC / DFSA | Under extraction remediation |
| DFSA Regulatory Notices | DIFC / DFSA | Under extraction remediation |
| UAE FIU Homepage | UAE Federal | Under extraction remediation |

Champion demo source: CBUAE homepage (AE-central-bank-of-the-uae). A CHANGED event was detected on 2026-05-30 with a stored SHA-256 snapshot record.

## What is NOT covered in this pilot

The following 3 enabled sources are under extraction remediation. They are not treated as confirmed in a pilot until the remediation work clears and the readiness state is rerun.

- DFSA Rulebook (navigation-shell extraction requires selector/adapter remediation)
- DFSA Regulatory Notices (hash collision with rulebook source requires adapter remediation)
- UAE FIU Homepage (shallow homepage extraction; circulars/publications source remains the primary FIU layer)

Additional known limitations:

- The FTA (Federal Tax Authority) website has documented access limitations that prevent reliable automated fetching. FTA is excluded.
- SCA is low priority for the VASP compliance officer ICP and is not covered in this pilot.
- Monitoring covers selected official-source pages only. Not all pages, sub-pages, or linked documents from each regulator are fetched in every run. Scope is defined per source configuration.
- Change detection compares snapshots by hash. Text extraction differences introduced by site layout changes or PDF rendering may affect detection accuracy. Results are reviewed by a human before delivery.

## How it works

StatuteProof fetches each monitored source URL on the configured schedule and normalizes the page text or PDF content. A SHA-256 hash of the normalized content is stored with a UTC timestamp. On each subsequent run, the new hash is compared to the stored baseline — a mismatch indicates a change. When a change is detected, a monitoring brief is drafted and placed in a human-review queue. No brief is delivered to the pilot customer until a human reviewer has signed off. StatuteProof does not make compliance decisions.

## Delivery format

- Weekly monitoring digest per pilot customer, covering confirmed sources in the agreed pilot scope
- Delivered by email
- Each digest includes: regulator name, source URL, last checked timestamp (UTC), event type (CHANGED or NO CHANGE), and the SHA-256 snapshot hash for that run
- A SAMPLE / FAKE brief template is available on request for preview before the pilot starts
- All delivered briefs carry the full StatuteProof disclaimer

## Human review gate

All briefs require human sign-off before delivery to the pilot customer. StatuteProof does not deliver automated compliance decisions. If a CHANGED event is detected, the draft brief is reviewed by a human operator before it is sent. The pilot customer is not automatically notified of a change until that review is complete.

## Pricing

- **Entry — $199/month:** 1 regulator, weekly monitoring digest, email delivery. Covers one selected regulator from the confirmed source list.
- **Standard — $599/month:** Up to 5 regulators, daily monitoring, email and Telegram delivery. Standard tier requires additional sources to have completed baseline runs. Not available until confirmed.
- **Enterprise — Custom pricing:** Expanded UAE official-source monitoring scope (subject to confirmed source readiness and availability), priority support, defined SLA. Contact for scope and pricing.

Pilot offer: 1 free week at Entry tier for qualified UAE VASP compliance teams. No card required during the pilot week.

## What this pilot is not

- Not legal advice. StatuteProof briefs are monitoring information for human review. They do not constitute legal advice, regulatory advice, compliance determination, or a legal opinion.
- Not a compliance outcome service. StatuteProof does not determine that all regulatory changes have been detected, that all relevant sources are covered, or that relying on a digest will prevent regulatory penalties.
- Not a replacement for qualified professionals. StatuteProof does not replace a qualified MLRO, compliance officer, legal counsel, or other professional adviser. Pilot customers remain responsible for their own compliance decisions.

---

StatuteProof reports are generated from monitored official-source records and are provided for information and compliance review support only. StatuteProof reports do not constitute legal advice, regulatory advice, compliance determination, or a legal opinion. StatuteProof does not replace qualified legal counsel, compliance professionals, MLROs, or other professional advisers. StatuteProof does not determine compliance outcomes, prevent fines, or confirm that all regulatory updates have been captured. Source monitoring may be affected by publication delays, website changes, PDF formatting, access limits, or source structure changes. Users should verify official source material directly and review evidence records, hashes, timestamps, and diffs before relying on a report. Users should consult qualified legal or compliance professionals before making regulatory, filing, operational, or customer decisions based on a report.
