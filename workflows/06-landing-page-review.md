# Workflow 06: Landing Page Review

**When:** Before any customer-facing update to the landing page or dashboard.
**Agents:** Product Manager Agent, Legal Language Agent.
**Skills:** `#ui-ux-review`.
**Output:** DEMO-READY, REVISE, or BLOCK decision.

---

## Rule: No Live Demo Before This Workflow Passes

Do not show the landing page or dashboard to a customer until this workflow produces DEMO-READY for both.

---

## Step 1 — Run the Before-Website-Copy Checklist

`checklists/before-website-copy.md` — complete all items.

---

## Step 2 — Identify All Mock Data Points

Open `regradar/web/src/data/mockData.js` and `appMockData.js`.
List every data array that feeds the dashboard and landing page.

Current known mock data (as of 2026-06-11):
- `sourceHealthRows` — shows all 9 UAE sources as PASS/active (FABRICATED)
- `riskTrendData` — April/May weekly numbers (FABRICATED)
- Alert list data — FABRICATED

For each: is it labeled SAMPLE / FAKE? If not, label it or replace it before demo.

---

## Step 3 — UI/UX Review

```
#ui-ux-review
Page: [URL]
Audience: CCO / MLRO at UAE-licensed VASP
Known mock data issue: sourceHealthRows shows PASS/active without real data
Concern: [describe specific concern]
```

Score target: >= 45/60 for DEMO-READY.

---

## Step 4 — Landing Page Copy Review

Use `prompts/legal-safe-copy-review-prompt.md` for every headline, subheading, CTA, and badge.

Focus areas:
- Hero headline — does it state a specific evidence-backed capability?
- Proof section — are hashes/timestamps labeled SAMPLE / FAKE if fabricated?
- Source list — does it match only actually-enabled sources?
- Pricing/pilot section — no compliance guarantee in tier descriptions?
- Disclaimer — present above fold or within one scroll?

---

## Step 5 — Dashboard Review

Before demo, the source health matrix must show one of:
a) Real data from `GET /api/sources/health` (not yet implemented as of 2026-06-11)
b) All data labeled SAMPLE / FAKE clearly

Current status: (b) is not implemented. Until (a) or (b) is complete, the dashboard is NOT demo-ready.

---

## Step 6 — Legal Language Agent Sign-Off

Route the full landing page text to the Legal Language Agent.
Use `prompts/legal-safe-copy-review-prompt.md`.
One forbidden claim = BLOCK.

---

## Step 7 — Record Decision

DEMO-READY: all checks passed, no mock data without labels, no forbidden claims.
REVISE: specific fixes required, listed.
BLOCK: forbidden claim or unlabeled mock data on customer-facing demo path.

Log the decision with date. Revisit whenever the page is updated.
