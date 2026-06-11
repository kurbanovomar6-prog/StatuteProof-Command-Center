# Anti-Slop Writing System

## Purpose

This document defines the writing standards for StatuteProof. It exists because compliance professionals read dense regulatory text all day. They will immediately detect generic AI prose, vague B2B fluff, or hype language — and lose trust in any product associated with it.

## The Core Problem

Most AI-generated copy for compliance-adjacent products sounds like this:

> "Our AI-powered platform seamlessly monitors the ever-changing regulatory landscape, ensuring your compliance team never misses a critical update. Stay ahead of regulators with our comprehensive, enterprise-grade compliance intelligence solution."

This is: vague, false (we do not "ensure" anything), hype-laden, passive, and structured exactly like every other RegTech vendor's homepage. A CCO reading this in 2026 will click away.

## What StatuteProof Copy Must Sound Like

Specific. Evidence-grounded. Direct. No promises that exceed capability. A sharp colleague sharing relevant information, not a vendor pitching a product.

**Good:**
> "VARA published a circular on AML/CFT obligations for VASP intermediaries on 2026-05-15. The normalized text changed in sections 3.1 and 4.2. We flagged it within the monitoring cycle. Here is the diff."

**Bad:**
> "Never miss a VARA update again! Our AI ensures 100% regulatory coverage."

## Core Writing Rules

1. **Cut filler phrases.** Remove throat-clearing openers and all adverbs. No -ly words.
2. **Break formulaic structures.** No binary contrasts ("not X, but Y"). No negative listings. No dramatic fragmentation.
3. **Active voice.** Every sentence needs a human actor. No passive constructions. No inanimate subjects doing human verbs ("the platform ensures compliance").
4. **Be specific.** Name the regulator. Name the date. Name the change. No vague declaratives.
5. **Put the reader in their situation.** "You need to review VARA's new circular before your board meeting" beats "compliance teams face challenges."
6. **Vary rhythm.** Mix sentence lengths. Two items beat three in a list.
7. **Trust the reader.** CCOs and MLROs know their job. Do not explain what AML/CFT means. State facts.
8. **Cut quotables.** If it sounds like a LinkedIn pull-quote, rewrite it.

## Banned Phrases (StatuteProof-Specific)

In addition to general anti-slop rules:

| Banned | Reason |
|--------|--------|
| "navigating the regulatory landscape" | Vague cliché |
| "in today's rapidly changing regulatory environment" | Empty throat-clearing |
| "stay ahead of compliance" | Implied guarantee |
| "seamlessly monitor" | Adverb + vague verb |
| "comprehensive solution" | Means nothing specific |
| "end-to-end" | Meaningless claim |
| "empower your compliance team" | Corporate fluff |
| "robust framework" | GenericAI filler |
| "unlock compliance confidence" | Hype |
| "peace of mind" | Implied guarantee |
| "sleep easy knowing" | Emotional guarantee (also a forbidden claim) |
| "game-changer" | Means nothing |

## The Quick-Check Protocol

Run before any customer-facing text is finalized:

- Any adverbs? Kill them.
- Any passive voice? Find the actor.
- Sentence starts with a Wh- word? Restructure it.
- Any "Here's the thing:" or similar? Cut to the point.
- Any "not X, it's Y" contrasts? State Y directly.
- Three consecutive same-length sentences? Break one.
- Any em dash? Remove it.
- Vague declarative ("The implications are significant")? Name the specific implication.
- Narrator-from-a-distance voice? Put the reader in the situation.
- Meta-joiners ("This brief explains...")? Delete. Let the content move.

## Scoring (1–10 per dimension)

| Dimension | Question |
|-----------|----------|
| Directness | Statements, not announcements? |
| Rhythm | Varied sentence length? |
| Trust | Respects reader's expertise? |
| Authenticity | Sounds like a sharp human, not a template? |
| Density | Anything cuttable without losing meaning? |

Below 35/50: revise. Above 45/50: good to proceed.

## Legal-Safe Writing Constraints

Anti-slop rules must operate within legal-safe boundaries. The goal is direct, specific, evidence-grounded language — not bold claims.

Do not use directness as a cover for forbidden claims. "VARA changed their fee schedule" is specific and safe. "VARA's fee change means you must update your compliance plan immediately" is direct but implies legal advice.

Reference: `docs/forbidden-phrases-reference.md`

## Skills Reference

| Task | Skill |
|------|-------|
| General prose review | `#anti-slop-writing-review` |
| Outreach message review | `#marketing-outreach-review` |
| Landing page copy | `#landing-page-conversion-review` + `#anti-slop-writing-review` |
| Legal copy check | Legal Language Agent + `prompts/legal-safe-copy-review-prompt.md` |
