# Workflow 05: Brief to Outreach

**When:** A brief exists and has passed QA. Outreach is now being prepared for a specific lead.
**Agents:** ICP Lead Research Agent, Outreach Writer Agent.
**Skills:** `#marketing-outreach-review`, `#anti-slop-writing-review`.
**Output:** A reviewed outreach message ready to send.

---

## Rule: Evidence Before Outreach

Do not send outreach that references monitoring capabilities without a real evidence record to back it up. If you claim "we detected a VARA change last week," that claim must trace to a real `run_id` in `source_runs.jsonl`.

---

## Step 1 — Confirm a Brief or Evidence Record Exists

Before writing outreach, identify:
- Which real CHANGED event will this outreach reference?
- Is there a QA-approved brief for this event?

If neither exists: do not send outreach claiming monitoring activity.

---

## Step 2 — Profile the Lead

Use the ICP Lead Research Agent with the lead's name, company, and role.

Check:
- Is this firm UAE-licensed and required to monitor the regulators we cover?
- Is the contact the right role (CCO, MLRO, Head of Compliance, in-house Counsel)?
- Is there a recent regulatory trigger? (New license, VARA circular, enforcement news)

---

## Step 3 — Draft the Outreach Message

Use `prompts/outreach-review-prompt.md` Layer 1-3 structure.
Use the Outreach Writer Agent.

Platform rules:
- Email: under 150 words, one CTA, short disclaimer in footer
- LinkedIn: under 80 words, one CTA, no disclaimer needed if no product claim
- First touch only references monitoring — no price, no pitch

---

## Step 4 — Review: Anti-Slop

```
#anti-slop-writing-review
[paste draft message]
```

Score must be >= 35/50 before proceeding.

---

## Step 5 — Review: Marketing Outreach

```
#marketing-outreach-review
Lead: [role, company type]
Platform: [email / LinkedIn]
Draft: [paste message]
```

Decision must be SEND or REVISE. BLOCK = do not send.

---

## Step 6 — Legal Safety Check

Quick check only (full review is for landing page copy):
- No forbidden claims?
- Short disclaimer present in email (not required for LinkedIn opener)?

Use `prompts/outreach-review-prompt.md` Layer 1 if unsure.

---

## Step 7 — Send and Log

Log: date sent, platform, lead role and company, message version, any response.
Do not send the same message twice without personalizing.

---

## What Not to Do

- Do not fabricate monitoring activity in outreach ("we detected X" when X is not in source_runs.jsonl)
- Do not attach a brief to cold outreach
- Do not use the full disclaimer in a LinkedIn opener — use common sense about context
- Do not send outreach to non-compliance roles (CFO, CEO) without a compliance-professional referral path
