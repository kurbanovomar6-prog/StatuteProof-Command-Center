---
name: marketing-outreach-review
description: Review StatuteProof outreach messages for quality, ICP fit, evidence grounding, and legal safety. Use when drafting cold emails, LinkedIn messages, pilot invites, or follow-ups to UAE compliance professionals. Trigger with #marketing-outreach-review.
metadata:
  trigger: "#marketing-outreach-review"
  version: 1.0.0
  adapted_from: marketingskills/skills/cold-email (Corey Haines, MIT)
---

# Skill: marketing-outreach-review

## Purpose

Review a StatuteProof outreach message for:
1. ICP fit — does it speak to a UAE compliance professional's actual pain?
2. Evidence grounding — is it rooted in a real monitoring capability or evidence record?
3. Legal safety — does it avoid forbidden claims?
4. Anti-slop — does it sound human, direct, and credible?
5. CTA quality — is the ask low-friction and specific?

## Scope

Use for: cold emails, LinkedIn messages, pilot invite notes, follow-up sequences, referral requests.
Do not use for: customer brief delivery, landing page copy, legal disclaimers.

## Required Inputs

- Draft outreach message (full text)
- Lead context: role, company, regulatory obligation if known
- Whether the message references a specific evidence record or monitoring capability
- Intended platform (email / LinkedIn / WhatsApp)
- Whether a disclaimer is required for this platform

## Procedure

1. Read `STATUTEPROOF_CONTEXT.md` to confirm current monitoring capabilities before reviewing claims.
2. Check the message against `docs/forbidden-phrases-reference.md` for unsafe phrases.
3. Check: does the message lead with the lead's world (their pain, their obligation) or with the product?
4. Check: is there one clear, low-friction CTA? ("Worth a 15-minute call?" beats "Book a demo.")
5. Check: is every capability claim supported by what the pipeline actually does?
6. Check: does the message pass the anti-slop rules (see below)?
7. Check: is the disclaimer present when required?
8. Score the message on 5 dimensions (1-10 each):
   - ICP Relevance: Does it speak to the exact role and regulatory obligation?
   - Evidence Grounding: Are claims about capabilities real and specific?
   - Legal Safety: No forbidden claims or unsafe implications?
   - Directness: No throat-clearing, no passive voice, no AI tells?
   - CTA Quality: One low-friction ask?

## Anti-Slop Rules for Outreach

**Cut immediately:**
- Any sentence starting with "Here's the thing:"
- "Game-changer", "landscape", "navigate challenges", "deep dive"
- Any adverb (-ly words: "really", "truly", "extremely", "seamlessly")
- Passive voice ("updates are monitored" → "we monitor updates")
- Inanimate objects acting ("the platform ensures..." → "the system records...")
- Binary contrast openers ("Not because X. Because Y.")
- Three consecutive same-length sentences

**Required:**
- "You/your" must dominate over "I/we/our"
- Personalization must connect to the problem (not just mention the company name)
- One paragraph = one idea
- Total length: under 150 words for cold outreach, under 80 words for LinkedIn

## Forbidden Claim Check (StatuteProof-Specific)

Flag any of these as BLOCK:
- AI lawyer / AI legal advisor
- guarantee compliance / guaranteed compliance
- prevent fines / avoid penalties
- replace your legal team / replace your MLRO
- never miss an update / 100% coverage
- official partner of VARA / CBUAE / DFSA
- certified by any regulator
- automatic compliance decisions
- stay compliant automatically

## Output Format

```
ICP Relevance: [1-10] — [one-line note]
Evidence Grounding: [1-10] — [one-line note]
Legal Safety: [PASS / BLOCK] — [flagged phrases if BLOCK]
Directness: [1-10] — [slop phrases found if any]
CTA Quality: [1-10] — [note]
Total: [X/50]

Decision: SEND / REVISE / BLOCK
Required fixes: [list, or "none"]
Revised draft (if REVISE): [optional]
```

Threshold: below 35/50 → REVISE. Any BLOCK in Legal Safety → BLOCK regardless of total score.

## Example Invocation

```
#marketing-outreach-review
Lead: Head of Compliance, UAE-licensed crypto exchange
Platform: LinkedIn DM
Draft: "Hi [Name], I noticed your firm just received its VARA VASP license.
We built StatuteProof to help teams like yours monitor VARA publications
without missing updates. Would a 15-minute call be useful this week?"
```
