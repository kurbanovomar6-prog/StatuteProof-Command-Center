# SAMPLE / FAKE — Landing Page Review Output

This is a SAMPLE / FAKE example of a `#ui-ux-review` output for the StatuteProof landing page.

---

## Review Output

Page reviewed: StatuteProof landing page (local dev, 2026-06-11)
Audience: Head of Compliance, UAE-licensed VASP

### Scores

- Trust Signals: 5/10 — Proof section shows hashes and timestamps but they are from mockData.js with no SAMPLE / FAKE label. This is a HIGH severity issue for any customer-facing demo.
- CTA Clarity: 8/10 — "Request a monitoring demo" is specific and low-friction. Good.
- Copy Safety: BLOCK — Found "Never miss a VARA update again" in the hero subheading. This is a forbidden claim (complete capture guarantee). Requires rewrite before demo.
- Audience Fit: 7/10 — Copy speaks to compliance monitoring pain. Hero language is too generic in the second paragraph.
- Source Transparency: 3/10 — sourceHealthRows shows all 9 UAE sources as PASS/active. This is fabricated. No SAMPLE / FAKE label. A CCO seeing this data would assume real monitoring is running.
- Information Hierarchy: 7/10 — Evidence trail section is easy to find. Last-checked timestamp visible in first scroll.

Total: 35/60

### Mock Data Issues

1. sourceHealthRows in mockData.js — shows VARA, CBUAE, DFSA and 6 others as PASS/active. Not from live source_runs.jsonl. HIGH severity.
2. riskTrendData — fabricated April-May weekly numbers. Displayed in the dashboard trend chart. Needs label.
3. Hero proof section hashes — "a3f1e2b4..." displayed as evidence. Not real. Needs SAMPLE / FAKE label.

### Forbidden Claims Found

1. "Never miss a VARA update again." — forbidden: complete capture guarantee. Replace with: "Monitor selected VARA source pages on a defined schedule with visible last-checked timestamps."

### Required Fixes Before Customer Demo

1. BLOCK: Rewrite hero subheading to remove "Never miss a VARA update again."
2. HIGH: Add SAMPLE / FAKE labels to sourceHealthRows component (or connect to live API).
3. HIGH: Add SAMPLE / FAKE labels to riskTrendData chart.
4. HIGH: Add SAMPLE / FAKE labels to proof section hashes.
5. MEDIUM: Tighten the second paragraph in the hero section — too generic.

### Decision: BLOCK

The landing page is not demo-ready. One forbidden claim must be rewritten. Three high-severity mock data issues must be labeled before any customer sees this.

---

# SAMPLE / FAKE — END OF REVIEW
