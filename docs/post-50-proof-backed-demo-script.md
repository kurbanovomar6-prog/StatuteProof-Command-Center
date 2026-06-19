# Post-50 Proof-Backed Demo Script

SAMPLE / DEMO / NOT LEGAL ADVICE

Date: 2026-06-16

## Demo Goal

Show an MLRO prospect that StatuteProof is not just a website checker. It monitors official sources, preserves evidence, exposes source health, and keeps remediation visible.

## Opening

"StatuteProof monitors selected public official or officially linked UAE sources that are technically accessible and permitted to monitor. Today the UAE pack has 238 enabled official-source endpoints, with 237 legacy monitoring-active rows and 168 fresh-alert eligible daily monitors after proof, baseline, source-health, noise, and review gates. One legacy registry source remains under extraction remediation. This is monitoring intelligence only, not legal advice."

## Show Source Coverage

Open the source readiness view.

Say:

"The important part is not the number alone. We show which sources are ready, which are under remediation, and why. A source is not marked ready from a one-off preview."

## Show Proof-Backed Source

Use:

- Source ID: `AE-cbuae-open-finance-rulebook`
- Source: CBUAE Open Finance Regulation
- URL: `https://rulebook.centralbank.ae/en/rulebook/open-finance-regulation`
- Proof path: `data/source_snapshots/2026-06-16/AE/AE-cbuae-open-finance-rulebook/intake-20260616T073001Z/proof.json`
- Normalized hash: `e109dd47cb7be06ae5e47d6871162a12d4be8e944fcfed5b1b46c7de24f472a2`

Say:

"This source has a proof path and normalized hash. The point is auditability: we can explain what we checked and what evidence supports the monitoring status."

## Show Non-CBUAE Breadth

Use examples:

- VARA Compliance and Risk Management Rulebook PDF: `AE-vara-compliance-risk-rulebook-pdf`
- ADGM FSRA Guidance and Policy Statements: `AE-adgm-fsra-guidance-policy`
- DFSA Consultation Papers Current: `AE-dfsa-consultation-current`
- EOCN AML/CFT Laws and Regulations: `AE-eocn-laws-regulations-en`

Say:

"Coverage is stronger but still not perfectly balanced. CBUAE, DFSA/DIFC, ADGM/FSRA, VARA, FTA, and MoE/DNFBP now have strong selected-source depth. SCA, UAE FIU, and direct EOCN/UAEIEC coverage still require blocker disclosure."

## Show Honest Held Source

Use:

- Source ID: `AE-dfsa-aml-ctf-sanctions`
- Status: held
- Reason: evidence baseline hash `d66b...` does not match monitor dry-run hash `468409...`
- Report: `docs/dfsa-aml-ctf-sanctions-hash-drift-investigation.md`

Say:

"This is exactly why the gate matters. Even with proof and baseline, we do not activate a source if monitor dry-run produces a drift signal that would create false alerts."

## Show Acknowledge & Assess Roadmap

Say:

"The next product layer is not more scraping. It is MLRO workflow: acknowledge an evidence-backed update, record impact assessment, and export an audit record."

## Close

"StatuteProof is not legal advice and does not guarantee complete capture. It is an evidence-backed monitoring and review workflow for official-source changes."
