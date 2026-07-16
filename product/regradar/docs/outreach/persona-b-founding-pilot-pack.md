# Persona B Outreach Pack — Founding Pilot (DRAFT)

**Status:** DRAFT for owner review — legal-language review APPLIED (3 rewords + disclaimers on objection replies; Email A line requires owner attestation if reverted). Nothing in this file has been sent.
**Send discipline:** Owner sends manually. Follow-up in-thread as a reply, 5–7 days after the first email, once only.
**Persona B:** Compliance Officer / CCO (often also the MLRO) at a small DFSA-, DIFC- or VARA-licensed UAE firm. Tracks multiple rulebooks manually (spreadsheets, email). Fears silent in-place edits to regulator pages. Must show a diligence paper trail at supervisory visits. SEO/CEO signs; pricing is public on the site and sits within discretionary spend.

---

## 1. Channel and objective

- **Channels:** cold email (3 variants), LinkedIn DM (1 variant), follow-up email (1).
- **Objective:** book the free Source Readiness Review. Nothing else. No demo push, no pricing talk in the first message (pricing is public on the site if they look).
- **Positioning boundary:** official-source regulatory monitoring with evidence-backed briefs. Lead with "the page changed and nobody noticed"; close with the sealed evidence record. Never legal advice, never applicability conclusions, never a compliance guarantee.

## 2. Personalization fields used

| Field | Example | Required |
|---|---|---|
| `{FirstName}` | Sara | Yes |
| `{Firm}` | Meridian Capital (DIFC) | Yes (Email C, follow-up) |
| `{Jurisdiction}` | "the DIFC" / "ADGM" / "the VARA regime" | Yes (Email A, opening line) |
| `{RegulatorList}` | DFSA + EOCN sanctions + CBUAE | Optional; only if verified by ICP + Lead Research. Do NOT name EOCN as monitored in copy until it reaches MONITOR_OK (sources.json flags it unreliable) — its limits are what the readiness review discloses. |

If `{Jurisdiction}` or the lead's regulator set is unverified, return the lead to ICP + Lead Research before sending. Do not guess a firm's licence type.

## 3. Message variants

### Email A — pain-led ("the page changed and nobody noticed")

**Subject:** When a regulator page changes quietly

Hi {FirstName},

Many compliance teams in {Jurisdiction} track rulebook changes the same way: bookmarks, a spreadsheet, and a weekly look at the regulator's site. The gap is the quiet edit, when a page changes in place and nothing announces it.

StatuteProof monitors selected official UAE regulator pages (DFSA, VARA, ADGM/FSRA, DIFC, CBUAE, SCA and others) and detects text changes. Each detected change is sealed with a SHA-256 hash, a capture timestamp and a stored diff, then drafted into a brief for your review. You stay the reviewer of record.

The first step is free: a Source Readiness Review. Send me your regulator list and we will report per-source access status and limitations before any pilot or payment.

Would that be useful?

{OwnerName}

*For monitoring information only. Not legal advice and not a guarantee of compliance.*

---

### Email B — proof-led (the 60-second public verifier)

**Subject:** Re-hash a real DFSA capture in about 60 seconds

Hi {FirstName},

Before I describe anything, you can test the core of StatuteProof yourself. Go to statuteproof.com/verify, click 'Load a real record' (a real DFSA capture) and re-hash it. No account, about a minute.

What you are checking: every change we detect on monitored official UAE regulator pages is sealed with a SHA-256 hash, a capture timestamp and the stored diff. Exports verify offline with a standalone script, so the record stands on its own.

If the verifier holds up, the free next step is a Source Readiness Review: you send your regulator list, we disclose per-source access status and limitations before any pilot or payment.

Worth a minute?

{OwnerName}

*For monitoring information only. Not legal advice and not a guarantee of compliance.*

---

### Email C — exam-led (supervisory-visit paper trail)

**Subject:** When someone asks when you first saw a change

Hi {FirstName},

At a supervisory visit, "we track regulatory changes" usually means an Excel tracker and email folders. It works until someone asks when you first saw a specific change, and what exactly changed.

StatuteProof gives you a sealed record for each detected change on monitored official UAE regulator pages: SHA-256 hash, capture timestamp, stored diff. Anyone can re-verify a record at statuteproof.com/verify, and exports verify offline without our servers or an account. Briefs are drafted for your review; your MLRO or CCO stays the reviewer of record.

The free first step is a Source Readiness Review of your regulator list: per-source access status and limitations, disclosed before any pilot or payment.

Shall I run one for {Firm}?

{OwnerName}

*For monitoring information only. Not legal advice and not a guarantee of compliance.*

---

### LinkedIn DM

Hi {FirstName}, quick one. If a rulebook page you rely on changed in place last month, would your current tracker show it? StatuteProof monitors selected official UAE regulator pages and seals each detected change: hash, timestamp, stored diff. Free first step: a Source Readiness Review of your regulator list, before any pilot or payment. Open to that?

*For monitoring information only. Not legal advice and not a guarantee of compliance.*

## 4. Follow-up sequence

**One follow-up only, 5–7 days later, sent as a reply in the same thread. If no response, stop.**

**Subject:** (reply in thread)

Hi {FirstName}, following up once on the free Source Readiness Review. If you send your regulator list, even a rough one, we will return per-source access status and known limitations. No payment method stored, no commitment. If the timing is wrong, tell me and I will close this off. Either way, the public verifier at statuteproof.com/verify is there if you want to test the evidence format.

{OwnerName}

*For monitoring information only. Not legal advice and not a guarantee of compliance.*

## 5. Objection replies

**"My consultant already sends me updates."**
Keep the consultant; their judgement is exactly what StatuteProof does not replace. We cover the layer underneath: scheduled monitoring of the official pages themselves, on a defined per-source cadence, plus a sealed record (hash, timestamp, diff) showing when a change appeared and what changed. The readiness review is free either way, so you can see whether your sources are reliably monitorable before deciding anything.

*For monitoring information only. Not legal advice and not a guarantee of compliance.*

**"Another dashboard I won't open."**
Understood. The working output is not a portal to patrol: it is a drafted brief for your review plus the sealed record behind it. The record is exportable and verifies offline with a standalone script, so its value does not depend on you logging in anywhere.

*For monitoring information only. Not legal advice and not a guarantee of compliance.*

**"Is this legal advice?"**
No, and we are careful about that boundary. StatuteProof reports that a monitored official page changed, what changed and when, with a sealed evidence record. Applicability and any legal conclusions remain with you and your advisers; your MLRO or CCO is the reviewer of record.

*For monitoring information only. Not legal advice and not a guarantee of compliance.*

**"What happens to my evidence if you shut down?"**
Your exports include a small standalone verify.py (Python standard library only) you can read and run yourself; no StatuteProof servers or account are needed. The hash, timestamp and diff keep their value independently of us, which is the point of sealing them in the first place.
*For monitoring information only. Not legal advice and not a guarantee of compliance.*

## 6. CTA options

Primary (use in all first-touch messages):
- "Send me your regulator list for a free Source Readiness Review."

Acceptable alternates (follow-up or DM only):
- "Worth a minute?" (paired with the public verifier link)
- "Shall I run one for {Firm}?"

Not allowed: demo-first CTAs, pricing CTAs, deadline or scarcity CTAs ("only X pilot slots"), meeting links in the first email.

## 7. Safe-claim self-review

| Claim in copy | Backing fact | Status |
|---|---|---|
| Monitors selected official UAE regulator pages (DFSA, VARA, ADGM/FSRA, DIFC, CBUAE, SCA and others) and detects text changes | Verified fact list | PASS |
| Each detected change sealed: SHA-256 hash, capture timestamp, stored diff | Verified fact list | PASS |
| Public verifier at statuteproof.com/verify, ~60 seconds, no account, real DFSA capture | Verified fact list | PASS |
| Briefs drafted for human review; MLRO/CCO is reviewer of record | Verified fact list | PASS |
| Free Source Readiness Review discloses per-source access status and limitations before pilot or payment | Verified fact list | PASS |
| Founding pilot: no payment method stored; pricing public on site | Verified fact list | PASS (pricing not quoted in copy) |
| Offline verification via standalone verify.py; record survives the vendor | Verified fact list | PASS |

Forbidden-phrase scan: no instance of "guarantee compliance", "prevent fines", "never miss", "100% accurate", "AI lawyer", "stay compliant automatically", "replace lawyers", "certified by / official partner of". "Selected" and "monitored" qualifiers used throughout; no absolute coverage claim. No invented regulatory events, fines, statistics or market facts. No fake urgency, no implied partnerships, no applicability conclusions. Short disclaimer present on every sendable unit, including each objection reply (added after legal-language review).

## 8. Handoff to Legal Language

- Route this pack to the Legal Language Agent for sentence-level review, then to QA / Critic for batch approval, before the owner sends anything.
- Flag for Legal Language: Email C subject "Evidence for your next supervisory visit" — confirm it cannot be read as promising exam outcomes (body limits the claim to the sealed record).
- Missing lead facts ({Jurisdiction}, regulator set, whether CO = MLRO) go back to ICP + Lead Research before send.
