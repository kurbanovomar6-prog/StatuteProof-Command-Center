---
name: landing-page-conversion-review
description: Review the StatuteProof landing page for conversion quality — headline clarity, ICP fit, proof elements, objection handling, CTA, and founding pilot offer. Use before any live update or pilot outreach campaign. Trigger with #landing-page-conversion-review.
metadata:
  trigger: "#landing-page-conversion-review"
  version: 1.0.0
  adapted_from: marketingskills/skills/copywriting and cro by Corey Haines (MIT)
---

# Skill: landing-page-conversion-review

## Purpose

Review the StatuteProof landing page as a compliance professional would see it for the first time. Does it answer their 4 questions in order?

1. Is this for me? (ICP fit)
2. What does it actually do? (headline clarity)
3. Can I trust this? (proof elements)
4. What should I do next? (CTA)

If any of these fails, the page does not convert — regardless of design quality.

## Target Visitor

UAE-licensed financial firm (VASP, bank, brokerage, fund) with a regulatory obligation to monitor VARA, CBUAE, DFSA, or ADGM publications.

Contact: CCO, MLRO, Head of Compliance, in-house Counsel.

They arrive skeptical. They have been burned by RegTech vendors who promised compliance guarantees and delivered newsletter aggregators. They will leave in 10 seconds if the headline does not speak to their specific situation.

## Review Sections

### 1. Headline Clarity

The headline must answer: what does this do, for whom?

**Good:** "We monitor selected VARA, CBUAE, and DFSA publications. Every change gets a hash, a timestamp, and a diff."
**Bad:** "Never miss a compliance update." (promise, not capability)
**Bad:** "AI-powered regulatory intelligence." (buzzwords, not specifics)

Check:
- [ ] Does the headline name at least one specific regulator?
- [ ] Does it describe a specific action (monitor, detect, hash, diff) rather than a promise?
- [ ] Can a CCO tell in 5 words if this is for them?
- [ ] Is the sub-headline evidence-first (what we actually do) or benefit-first (what you'll feel)?

### 2. ICP Fit (Above the Fold)

Check:
- [ ] Is "UAE" or a specific UAE regulator mentioned above the fold?
- [ ] Is the target role (CCO, MLRO, compliance team) named or implied?
- [ ] Is the specific pain (manual checking burden, missing updates, no audit trail) named?
- [ ] Would a generic SaaS company's CCO mistake this for a product for them? (Bad — too broad)

### 3. Proof Elements

This is the most important section for compliance buyers. They need to see that the product actually works.

Check:
- [ ] Is there a real or SAMPLE/FAKE evidence record visible?
- [ ] Does it show a real or SAMPLE hash value, timestamp, and source URL?
- [ ] Is the SAMPLE/FAKE label visible if the data is not real?
- [ ] Does the proof section explain what the hash and timestamp mean to a compliance professional?
- [ ] Is there a diff excerpt? Is it readable?
- [ ] Are source names named (VARA, CBUAE, DFSA) — not "major UAE regulators"?

### 4. Objection Handling

Compliance buyers have specific objections. Check each:

| Objection | Does the page address it? | Where? |
|-----------|--------------------------|--------|
| "This is just a newsletter aggregator." | | |
| "What happens when VARA changes their website structure?" | | |
| "Can I show this evidence record to an auditor?" | | |
| "Is this legal advice?" | | |
| "What if you miss an update?" | | |
| "Who else is using this?" | | |

All 6 should be addressed or acknowledged with honest language. "We don't guarantee complete capture" is better than ignoring the objection.

### 5. CTA Clarity

Check:
- [ ] Is there one clear primary CTA?
- [ ] Is the CTA specific? ("Request a monitoring demo" > "Learn more")
- [ ] Does the CTA match the product stage? (Pilot invite, not "Start free trial")
- [ ] Is the ask low-friction? (No credit card, no 20-field form)
- [ ] Is there a secondary CTA for visitors not ready to act? ("See a SAMPLE brief")

**Founding Pilot Offer (if present):**
- [ ] Is it clear what the pilot includes? (which sources, how many runs, what output format)
- [ ] Is the pilot framed as limited access, not "free trial"?
- [ ] Is the disclaimer present in the pilot section?

### 6. Legal Safety

Quick scan (full review: use `prompts/legal-safe-copy-review-prompt.md`):
- [ ] No forbidden claims in headline or sub-headline
- [ ] No "guarantee compliance", "prevent fines", "official partner", "AI lawyer"
- [ ] Disclaimer present (full or link to full)
- [ ] "For compliance review support only" visible in at least one place

### 7. Source Readiness Review Funnel

Check:
- [ ] Does the page show the funnel: source → change detected → evidence record → brief → human review?
- [ ] Is it clear that a human reviews every brief before any action?
- [ ] Is the source list on the page honest? (Only list monitored + enabled sources)

## Scoring

Rate each 1–10:

| Dimension | Score |
|-----------|-------|
| Headline clarity | |
| ICP fit above fold | |
| Proof elements | |
| Objection handling | |
| CTA quality | |
| Legal safety | |

Below 42/60: REVISE. Below 30/60: BLOCK before any outreach campaign.

## Output Format

```
Headline clarity: [1-10] — [note]
ICP fit: [1-10] — [note]
Proof elements: [1-10] — [note; flag mock data if unlabeled]
Objection handling: [1-10] — [which objections are unaddressed]
CTA quality: [1-10] — [note]
Legal safety: [PASS / BLOCK] — [flagged phrases if any]
Total: [X/60]

Unaddressed objections: [list]
Mock data risks: [list or "none"]
Required fixes: [list]
Decision: LAUNCH-READY / REVISE / BLOCK
```
