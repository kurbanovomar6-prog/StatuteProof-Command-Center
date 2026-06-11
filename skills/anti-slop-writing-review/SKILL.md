---
name: anti-slop-writing-review
description: Remove AI writing patterns from StatuteProof prose. Use when drafting, editing, or reviewing outreach messages, brief summaries, landing page copy, or any customer-facing text. Trigger with #anti-slop-writing-review.
metadata:
  trigger: "#anti-slop-writing-review"
  version: 1.0.0
  adapted_from: stop-slop by Hardik Pandya (hvpandya.com), MIT License
---

# Skill: anti-slop-writing-review

## Purpose

Eliminate predictable AI writing patterns from StatuteProof prose.

Compliance professionals read dense regulatory text. Any text that sounds like generic AI output will lose credibility immediately.

## Core Rules

1. **Cut filler phrases.** Remove throat-clearing openers, emphasis crutches, and all adverbs. No -ly words.

2. **Break formulaic structures.** Avoid binary contrasts, negative listings, dramatic fragmentation, rhetorical setups.

3. **Use active voice.** Every sentence needs a human actor. No passive constructions. No inanimate objects performing human actions ("the system ensures compliance" → who ensures what?).

4. **Be specific.** Name the regulation. Name the regulator. Name the date. No vague declaratives ("regulatory changes are complex").

5. **Put the reader in their situation.** "You need to check VARA publications before your next board meeting" beats "Firms face compliance challenges."

6. **Vary rhythm.** Mix sentence lengths. Two items beat three. End paragraphs differently.

7. **Trust the reader.** CCOs and MLROs know their job. Don't explain what AML/CFT means. Don't hand-hold. State facts.

8. **Cut quotables.** If it sounds like a LinkedIn pull-quote, rewrite it.

## Quick Checks (Run Before Every Delivery)

- Any adverbs? Kill them.
- Any passive voice? Find the actor, make them the subject.
- Inanimate thing doing a human verb ("the platform catches..." → who catches what?)? Name the actor.
- Sentence starts with a Wh- word? Restructure it.
- Any "here's what/this/that" throat-clearing? Cut to the point.
- Any "not X, it's Y" contrasts? State Y directly.
- Three consecutive sentences match length? Break one.
- Paragraph ends with punchy one-liner? Vary it.
- Any em dash? Remove it.
- Vague declarative ("The implications are significant")? Name the specific implication.
- Narrator-from-a-distance ("Compliance teams often struggle")? Put the reader in the situation.
- Meta-joiners ("This brief explains...")? Delete. Let the content move.

## Banned Phrases for StatuteProof Specifically

In addition to general anti-slop rules, never use:
- "navigating the regulatory landscape"
- "in today's rapidly changing regulatory environment"
- "stay ahead of compliance"
- "seamlessly monitor"
- "comprehensive solution"
- "end-to-end"
- "empower your compliance team"
- "robust framework"
- "unlock compliance confidence"
- "peace of mind"
- "sleep easy knowing"

These are high-risk because they either imply guarantees or sound like every other RegTech vendor.

## Scoring

Rate 1-10 on each dimension:

| Dimension | Question |
|-----------|----------|
| Directness | Makes statements or makes announcements? |
| Rhythm | Varied sentence length or metronomic? |
| Trust | Respects the reader's expertise? |
| Authenticity | Sounds like a sharp human, not a template? |
| Density | Anything cuttable without losing meaning? |

Below 35/50: revise. Above 45/50: good to proceed.

## Output Format

```
Quick check results:
- [issue found or "clear"]

Score:
- Directness: [1-10]
- Rhythm: [1-10]
- Trust: [1-10]
- Authenticity: [1-10]
- Density: [1-10]
- Total: [X/50]

Decision: PASS (>35) / REVISE (<35)
Required edits: [specific list, or "none"]
Revised version (if REVISE): [optional]
```

## StatuteProof Tone Standard

The target voice: a sharp compliance-industry professional who noticed something relevant and is sharing it. Specific. Evidence-grounded. No jargon. No hype.

Correct: "VARA published a circular on AML/CFT obligations for VASP intermediaries on 2026-05-15. The normalized text changed in sections 3.1 and 4.2. We flagged this for your review."

Wrong: "Our AI-powered platform seamlessly monitors the regulatory landscape and ensures your team never misses a critical compliance update."
