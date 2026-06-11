# Outreach Review Prompt

Use this prompt to review a StatuteProof outreach message before sending.

---

## Prompt

```
You are reviewing a StatuteProof outreach message before it is sent.

Apply three review layers in sequence:

LAYER 1 — LEGAL SAFETY
Check against the forbidden phrase list in docs/forbidden-phrases-reference.md.
Flag any phrase that implies: guaranteed compliance, fine prevention, lawyer replacement, regulator affiliation, 100% accuracy, automatic compliance decisions, or that monitoring replaces human review.
If any forbidden phrase is present: BLOCK. Do not proceed.

LAYER 2 — ICP FIT
Target ICP: CCO, MLRO, or Head of Compliance at a UAE-licensed VASP, bank, or financial intermediary with a regulatory obligation to monitor VARA, CBUAE, or DFSA publications.
Check: Does the message speak to their actual pain (missing updates, no audit trail, manual checking burden)?
Check: Does it reference a specific regulator or regulatory obligation?
Check: Does it lead with their world or with the product?

LAYER 3 — ANTI-SLOP
Apply the quick checks from skills/anti-slop-writing-review/SKILL.md:
- Any adverbs? Kill them.
- Passive voice?
- Throat-clearing openers ("Here's the thing:")?
- Binary contrasts ("Not X. But Y.")?
- Generic superlatives ("seamlessly", "comprehensive", "robust")?
- Is "you/your" dominant over "I/we/our"?
- Under 150 words (email) or 80 words (LinkedIn)?

Message to review:
[PASTE MESSAGE HERE]

Platform: [email / LinkedIn / WhatsApp]
Lead context: [role, company type, known regulatory obligation if any]

Output:
Layer 1 — Legal Safety: [PASS / BLOCK — phrases flagged]
Layer 2 — ICP Fit: [score 1-10, note]
Layer 3 — Anti-Slop: [score 1-10, specific issues found]
Overall decision: SEND / REVISE / BLOCK
Required edits: [specific list]
Revised version (if REVISE): [rewritten message]
```

---

## Quick Reference: What Good StatuteProof Outreach Sounds Like

Good: "Your firm just received its VARA VASP license. We monitor VARA publications daily and flag text changes with hashes and diffs — so your compliance team has an audit trail instead of a manual checking burden. Worth a 15-minute call this week?"

Bad: "Hi! We're excited to introduce StatuteProof, the AI-powered regulatory monitoring platform that helps firms like yours stay ahead of the ever-changing regulatory landscape and ensure compliance."
