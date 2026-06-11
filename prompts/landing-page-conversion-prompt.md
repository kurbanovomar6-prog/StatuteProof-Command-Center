# Landing Page Conversion Prompt

Use this prompt to review the StatuteProof landing page for conversion quality before any live update or outreach campaign.

---

## Prompt

```
You are reviewing the StatuteProof landing page for conversion quality.

Apply the #landing-page-conversion-review skill.

Target visitor: CCO, MLRO, or Head of Compliance at a UAE-licensed VASP, bank, or financial intermediary with an obligation to monitor VARA, CBUAE, or DFSA publications.

Page to review: [URL or description]
Known issues: [list any known problems to specifically check]

Run these checks in sequence:

CHECK 1 — HEADLINE CLARITY
Read the headline and sub-headline.
Does it name at least one specific regulator (VARA / CBUAE / DFSA)?
Does it describe a specific action (monitor / detect / hash / diff) or a promise?
Can a CCO tell in 5 words if this is for them?

CHECK 2 — ICP FIT (ABOVE THE FOLD)
Is "UAE" or a specific UAE regulator visible before scroll?
Is the target role named or implied?
Is the specific pain (manual checking burden, no audit trail) named?

CHECK 3 — PROOF ELEMENTS
What proof is shown? List each element.
Is it real data or mock data? Is mock data labeled SAMPLE/FAKE?
Are hashes and timestamps shown in a credible format (monospace, full values)?
Is a diff excerpt present?

CHECK 4 — OBJECTION HANDLING
Check each objection:
1. "This is just a newsletter aggregator" — addressed? Where?
2. "What happens when VARA changes their website?" — addressed?
3. "Can I show this to an auditor?" — addressed?
4. "Is this legal advice?" — addressed?
5. "What if you miss an update?" — addressed?
6. "Who else uses this?" — addressed?

CHECK 5 — CTA QUALITY
What is the primary CTA? Is it specific and low-friction?
Is there a secondary CTA for not-ready visitors?
If a founding pilot offer is shown: is it clear what is included?

CHECK 6 — LEGAL SAFETY
Check headline, sub-headline, CTAs, and badges for forbidden claims.
Is the disclaimer present?

Output:
Headline clarity: [1-10] — [note]
ICP fit: [1-10] — [note]
Proof elements: [1-10] — [note]
Objection handling: [1-10] — [which objections unaddressed]
CTA quality: [1-10] — [note]
Legal safety: [PASS / BLOCK] — [flagged phrases]
Total: [X/60]
Mock data risks: [list]
Required fixes: [list]
Decision: LAUNCH-READY / REVISE / BLOCK
```
