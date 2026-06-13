# StatuteProof Pricing Strategy

> Written: 2026-06-13. Based on product inspection, market research, and founding-pilot stage reality.
> This document governs all pricing decisions until superseded.

---

## 1. Executive Recommendation

**Verdict: "Show pricing publicly, but keep activation manual."**

Do NOT launch self-serve Stripe checkout yet.  
DO show public pricing on the website — it builds credibility and filters serious buyers.

**Recommended prices (effective now, founding pilot stage):**

| Plan | Monthly | Annual | Who |
|------|---------|--------|-----|
| Source Readiness Review | Free | — | Lead generation |
| Monitor | $349/month | — (not yet) | Small VASP / 1-person compliance |
| Professional | $749/month | — (not yet) | UAE MLRO / compliance team |
| Consultant | Talk to us | Custom | Advisory firms (NOT READY TO SELL) |

**One version up (after Stripe + audit export + email brief are built):**

| Plan | Monthly | Annual |
|------|---------|--------|
| Source Readiness Review | Free | — |
| Monitor | $399/month | $329/month |
| Professional | $899/month | $749/month |
| Consultant | $2,200+/month | Custom |

**Confidence: Medium.**  
Reason: No paying customers yet to validate willingness-to-pay. Prices are based on value comparison (manual monitoring cost, compliance consultant rates), not empirical churn data.  
Assumption: UAE MLROs/CCOs are willing to pay for evidence-grade audit trail they cannot replicate manually.  
What could make this wrong: If founders discover MLROs cannot spend without procurement approval cycles, the right model may be annual contracts, not monthly SaaS.

---

## 2. Market Context

### Competitor pricing visibility

| Vendor | Pricing visible | Segment | Notes |
|--------|----------------|---------|-------|
| CUBE RegTech (cube.global) | Not publicly listed | Enterprise | Multi-jurisdiction regulatory tracking. Likely $5,000–$20,000+/mo for institutional clients. |
| Corlytics | Not publicly listed | Enterprise | AI regulatory change management. Enterprise contracts. |
| Vixio | Not publicly listed | Enterprise | Regulatory intelligence for payments/crypto. Premium market. |
| Diligent | Not publicly listed | Enterprise | GRC platform. Likely $3,000–$50,000+/mo depending on modules. |
| LogicGate | Not publicly listed | Mid-market/Enterprise | Risk workflow software. |
| Hyperproof | Not publicly listed | Mid-market | GRC compliance software. ~$1,200–$2,500+/mo estimated from public signals. |
| Compliance.ai | Not publicly listed | Enterprise | Regulatory change tracking. Demo-required. |
| Regology | Not publicly listed | Enterprise | Regulatory intelligence. Demo-required. |
| ChangeDetection.io | $13–$89/month | SMB | Simple webpage change alerts. Not compliance-grade. |
| Visualping | $29–$400/month | SMB | Visual monitoring. Not compliance-grade. |

**Key finding**: Every compliance-grade competitor requires a demo before pricing is disclosed. StatuteProof showing public prices is a differentiator — it signals transparent, accessible pricing and attracts SMB compliance teams who are tired of enterprise sales cycles.

**StatuteProof is NOT competing with CUBE or Corlytics.** Those are sold to banks and global regulators. StatuteProof competes with:
1. Manual MLRO monitoring (the $0 option with high hidden labor cost)
2. Simple change monitoring tools (ChangeDetection.io / Visualping) — accessible but not compliance-grade
3. Compliance consulting engagements ($5,000–$20,000/month) — expensive and not scalable

### UAE market context (unverified — inferred from known regulatory landscape)

- UAE has 500+ VARA-licensed entities (as of 2024)
- DFSA has 600+ regulated firms in DIFC
- ADGM FSRA has 200+ regulated entities
- UAE FIU requires AML compliance reporting from all these entities
- Each entity needs to monitor CBUAE, VARA, DFSA, ADGM/FSRA, UAE FIU minimum
- Small compliance teams (1–3 people) are common at VASPs under $50M revenue
- Manual monitoring at $80–$150/hour compliance consultant rate costs $3,200–$12,000/month equivalent

**This makes $349–$749/month look like exceptional ROI on paper.** The real question is procurement and budget authority — MLROs at early VASPs often cannot approve $749/month independently.

---

## 3. Pricing Philosophy

**Primary value metric: number of monitored sources.**

Sources are what the customer cares about. More sources = more coverage = more value. This is defensible, transparent, and scales naturally.

**Secondary metric: evidence retention period.**

Audit-grade compliance requires 12-month minimum retention. Regulators can ask for evidence up to 3 years back. Longer retention justifies higher price.

**Tertiary metric: users/seats.**

Small compliance teams. Seats are not the primary value driver but are a meaningful differentiator between tiers.

**What NOT to use as a value metric:**
- "AI" features (forbidden claims territory, and AI is a commodity)
- Alerts volume (too granular, hard to reason about)
- API calls (wrong customer archetype)

**Why not per-source pricing?**  
Per-source billing creates procurement friction ("how many sources do I need?") and makes the buying decision complex. Flat monthly tiers with clear source limits are easier to sell to compliance teams.

---

## 4. Final Plans

### Plan 1 — Source Readiness Review (Free)

**plan_id**: `evidence_preview`  
**Monthly price**: Free  
**Annual**: N/A  
**Who it is for**: Compliance leads evaluating whether StatuteProof covers their relevant sources before committing budget.

| Feature | Status |
|---------|--------|
| Official UAE sources | 0 live |
| Source readiness review | Sample / demonstration |
| Sample evidence record | Available (SAMPLE/FAKE labeled) |
| Sample brief preview | Available (SAMPLE/FAKE labeled) |
| Live monitoring | Not included |
| Custom sources | Not included |
| Weekly MLRO brief | Not included |
| Audit binder export | Not included |
| Diff view | Not included |
| Users | 1 |
| Evidence retention | Sample only |

**CTA**: Request source readiness review  
**Entry point**: This is the primary lead-generation offer. Not a time-limited trial — it's a permanent free tier that serves one purpose: let the prospect understand what their UAE regulatory source coverage looks like before buying.

**Upgrade reason**: "You've seen which sources are active and which are limited. Start monitoring the ones that matter to your licence."

---

### Plan 2 — Monitor (was: Starter Pilot)

**plan_id**: `monitor`  
**Monthly price**: $349/month  
**Annual price**: N/A for now  
**Who it is for**: 1-person compliance team at a UAE startup VASP, fintech, or small DFSA/ADGM firm.

| Feature | Status |
|---------|--------|
| Official UAE sources | Up to 5 (from the 13 validated set) |
| Source readiness review | Available |
| Evidence records | Available |
| Diff view | Available |
| Risk scoring | Available (basic) |
| Custom sources | Not included |
| Weekly MLRO brief | Source status summary only (not full MLRO brief) |
| Audit binder export | Not included |
| PDF export | Not included |
| High-risk review queue | Not included |
| Users | 1 |
| Evidence retention | 90 days |
| Multiple workspaces | Not included |
| Support | Standard (email) |

**CTA**: Start Monitor Pilot  
**Upgrade reason**: "You're monitoring 5 sources. The full UAE source pack (13 sources including VARA enforcement, CBUAE regulations, UAE FIU circulars) requires Professional. Audit export, diff archives, and high-risk review queue are also locked."

**Why $349 not $299**:  
$299 for compliance-grade software signals "not serious." $349 is still accessible for a small VASP spending $500–$2,000/month on compliance tasks. The extra $50/month does not create meaningful buyer resistance but adds credibility.

**Why changed from "Starter Pilot" to "Monitor"**:  
"Pilot" language is appropriate during the founding cohort phase, but for ongoing SaaS positioning "Monitor" is cleaner and more accurate. During the founding pilot period, keep "Founding Monitor Pilot" as the label.

**Confidence**: Medium-Low. 5 sources at $349 may still be too restrictive to feel valuable. If early customers churn from this tier, it means they need more coverage — which means they should be on Professional.

---

### Plan 3 — Professional

**plan_id**: `professional`  
**Monthly price**: $749/month *(lowered from $799 — honest about current missing features)*  
**Annual price**: N/A for now  
**Who it is for**: UAE MLRO, Chief Compliance Officer, or Head of Compliance at a VARA-licensed VASP, DFSA/ADGM firm, or UAE fintech.

| Feature | Status |
|---------|--------|
| Official UAE sources | All 13 validated UAE sources |
| Source readiness review | Available |
| Evidence records | Available |
| Full diff view | Available |
| Risk scoring | Available |
| High-risk review queue | Available |
| Custom sources | 3 custom public sources (requires activation) |
| Weekly MLRO brief | Available via Telegram. Email delivery: requires activation |
| Audit binder export | **Pilot roadmap** — not available yet |
| PDF/Markdown export | **Requires activation** — contact team |
| Users | 2 |
| Evidence retention | 12 months |
| Multiple workspaces | Not included |
| White-label reports | Not included |
| Support | Priority email |

**CTA**: Upgrade to Professional  
**Upgrade reason over Monitor**: "Professional covers the full UAE regulatory source pack — CBUAE, VARA, DFSA, ADGM/FSRA, UAE FIU, Ministry of Finance, DIFC Laws, and more. Includes the high-risk review queue for CHANGED events and 12-month evidence retention for audit purposes."

**Why $749 not $799**:  
Audit binder export and automated PDF export are not built yet. Charging $799 for incomplete professional-grade features is dishonest. $749 is the honest "we're building toward $899" price. As audit export is delivered, this becomes $899.

**Why this is the recommended plan for MLROs**:  
- All 13 active UAE sources are covered
- 12-month evidence retention satisfies most UAE regulatory audit windows
- High-risk review queue is the core MLRO workflow
- $749/month is dramatically cheaper than any compliance consulting engagement for equivalent coverage

**Confidence**: Medium. Price point is supported by the value comparison. Risk: enterprise procurement cycles may block monthly spend without annual contract option.

---

### Plan 4 — Compliance Consultant (Custom)

**plan_id**: `consultant`  
**Monthly price**: "Talk to us" — no fixed public price  
**Who it is for**: Advisory firms, consultants, or law firms managing multiple UAE-regulated clients.

| Feature | Status |
|---------|--------|
| Multiple client workspaces | **Pilot roadmap** |
| Custom source count | **Pilot roadmap** |
| White-label reports | **Pilot roadmap** |
| Team roles | **Pilot roadmap** |
| Audit binder export | **Pilot roadmap** |
| Extended retention | **Pilot roadmap** |

**CTA**: Talk to us  
**Why no fixed price**: The product does not support multiple workspaces yet. Selling a fixed-price Consultant plan would require delivering features that do not exist. The correct approach is discovery calls to understand what the consultant needs, then activate a custom Professional plan for their first client workspace.

**Do NOT promise Consultant plan features in the near term.** Show it as a direction, not a deliverable.

---

## 5. Why MLROs Would Pay

**Monitor ($349/month)**:  
A compliance manager at a small UAE VASP spends ~5 hours/week manually checking CBUAE, VARA, and DFSA websites for updates. At an internal cost of $80/hour, that's $1,600/month in labor. StatuteProof Monitor replaces 5 of those sources with timestamped evidence records. ROI is clear if the value metric is accepted.

**Professional ($749/month)**:  
An MLRO at a DFSA-regulated firm receives regulatory updates from 13+ sources. Missing a CBUAE circular or VARA enforcement notice creates regulatory risk. The $749/month cost is less than 1 compliance consultant hour per working day. The evidence trail — SHA-256 hash, timestamp, diff, human-reviewed before delivery — is something the MLRO cannot produce manually. It creates a defensible paper trail if the regulator asks "did you monitor this source?"

---

## 6. Why the Expensive Plan Is Worth It (Professional vs Monitor)

The Professional plan is not "more sources for more money." The upgrade from Monitor to Professional unlocks a qualitatively different compliance workflow:

1. **Full UAE regulatory source pack**: All 13 validated sources including VARA enforcement actions, CBUAE regulations database, UAE FIU circulars, DFSA supervisory notices, and DIFC Laws — not just 5
2. **High-risk review queue**: CHANGED events with HIGH/MEDIUM risk scoring are surfaced for urgent human review — Monitor does not have this
3. **12-month evidence retention**: Audit-grade retention for regulatory inspection windows — Monitor only keeps 90 days
4. **2 users**: Small compliance team can both access the workspace and review evidence
5. **Weekly MLRO brief delivery**: Formatted compliance monitoring summary for the MLRO, not just a source status log
6. **Custom sources (3)**: The MLRO can add their firm's specific internal or secondary sources for monitoring

**The Monitor plan is for trying StatuteProof on a small source set. Professional is for running it as a real compliance workflow.**

---

## 7. What Not to Sell Yet

**Do not sell or promise these features before they are built:**

| Feature | Why not ready | When to activate |
|---------|--------------|-----------------|
| Audit binder export (PDF) | Not implemented | After PDF generation is built and tested |
| White-label reports | Not implemented | Consultant plan only, after multi-workspace |
| Multiple client workspaces | Not implemented | After workspace isolation is built |
| Automated email brief delivery | Not implemented | After email delivery pipeline is built |
| Custom source onboarding (self-serve) | Not implemented | After source validator UI is built |
| Annual billing | Not implemented in Stripe | After Stripe is integrated |
| Team roles (admin/viewer) | Not implemented | After role-based auth is built |

**Do not mark these as "Available" in the pricing UI. Use "Pilot roadmap" or "Requires activation."**

---

## 8. Stripe Setup Plan (for future implementation — test mode only)

When ready to integrate Stripe, create these products in TEST mode first:

| Stripe Product Name | Price | Interval | env variable | lookup_key |
|--------------------|-------|----------|-------------|------------|
| StatuteProof Monitor | $349.00 | monthly | `STRIPE_PRICE_MONITOR` | `sp_monitor_monthly` |
| StatuteProof Professional | $749.00 | monthly | `STRIPE_PRICE_PROFESSIONAL` | `sp_professional_monthly` |
| StatuteProof Monitor Annual | $329.00 | monthly (×12) | `STRIPE_PRICE_MONITOR_ANNUAL` | `sp_monitor_annual` |
| StatuteProof Professional Annual | $699.00 | monthly (×12) | `STRIPE_PRICE_PROFESSIONAL_ANNUAL` | `sp_professional_annual` |

**Do NOT create Stripe products now.** Do NOT use live mode until:
1. Source readiness review workflow is tested with at least 2-3 founding pilots
2. Evidence retention is working reliably
3. The human review queue is staffed and operational
4. At least one customer has confirmed value before charging

**Current Stripe env variable names to use in .env.example:**
```
STRIPE_SECRET_KEY=
STRIPE_PUBLISHABLE_KEY=
STRIPE_PRICE_MONITOR=
STRIPE_PRICE_PROFESSIONAL=
STRIPE_WEBHOOK_SECRET=
```

---

## 9. Website Pricing Copy (Legal-Safe)

### Section headline
> Choose the source monitoring plan that matches your UAE compliance footprint.

### Billing note (below headline)
> Founding pilots are manually activated after source readiness review. No credit card required to start. Stripe billing will be available after pilot completion.

### Plan cards

**Source Readiness Review — Free**
> Request a structured source readiness review before any monitoring commitment. StatuteProof maps your UAE regulatory sources, documents their access quality, and shows you what is active, limited, or blocked.
> 
> *Monitoring intelligence only. Not legal advice.*

**Monitor — $349/month**
> Live monitoring of up to 5 validated UAE regulatory sources. Evidence records with SHA-256 hash and timestamp. Diff view for content changes. 90-day retention.
> 
> Suitable for: 1-person compliance teams at UAE startups, early VASPs.
> 
> *Monitoring intelligence only. Not legal advice.*

**Professional — $749/month** *(Recommended)*
> Full UAE source pack: all 13 validated official sources — CBUAE, VARA, DFSA, ADGM/FSRA, UAE FIU, Ministry of Finance, DIFC Laws, and more. High-risk review queue, weekly brief, 12-month retention.
> 
> Suitable for: MLRO, CCO, or Head of Compliance at a UAE-regulated firm.
> 
> *Monitoring intelligence only. Not legal advice.*

**Compliance Consultant — Talk to us**
> Multi-client workspaces, extended source coverage, team roles, and white-label reporting are on the roadmap for advisory firms. Contact us to discuss your requirements.
> 
> *Pilot roadmap — features in development.*

### Legal footnote (required on every pricing page)
> StatuteProof reports are generated from monitored official-source records and are provided for information and compliance review support only. StatuteProof reports do not constitute legal advice, regulatory advice, compliance certification, or a legal opinion. StatuteProof does not guarantee compliance, prevent fines, or certify that all regulatory updates have been captured. Users should verify official source material directly and consult qualified legal or compliance professionals before making regulatory or operational decisions.

---

## 10. Dashboard Upgrade Copy (Plan Banner and Locked Features)

### Evidence Preview banner
**Title**: "7-day Evidence Preview active"  
**Body**: "Explore the StatuteProof workspace with sample evidence and source-readiness tools. Monitor plan activates live monitoring of up to 5 UAE sources. Professional covers all 13 validated sources with the full MLRO workflow."

**Fields row**: Current plan: Evidence Preview | Trial ends in: X days | Recommended: Professional | Next step: Request source readiness review

### Locked feature copy
- Live monitoring locked: "Available on Monitor ($349/month) — requires source readiness activation"
- High-risk review queue locked: "Available on Professional ($749/month)"
- Audit binder export locked: "Pilot roadmap — not available yet"
- Multiple workspaces locked: "Consultant plan — talk to us"
- PDF export locked: "Requires activation — contact team"
- Custom sources locked: "Available on Professional — 3 custom public sources (requires activation)"

### Post-plan-selection confirmation
> "Plan intent recorded. No payment has been processed. Our team will contact you to confirm your source pack and activate your founding pilot. You will receive advance notice before any billing begins."

---

## 11. Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Professional price too high for UAE VASP procurement | Medium | Offer founding pilot discount; allow monthly cancel; do not require annual commitment yet |
| Monitor plan (5 sources, $349) too limited to feel valuable | Medium | Consider "starter pack" of 5 most important sources (CBUAE + VARA + DFSA + UAE FIU + ADGM) — that covers the core UAE compliance stack |
| Missing audit export damages credibility of "Professional" label | High | Label clearly as "Pilot roadmap." Do not call it Professional until audit export ships. Consider renaming to "Professional Pilot" in the interim. |
| MLROs cannot approve $749/month without annual contract | Medium | Prepare annual pricing ($699/month) and offer 12-month prepay option once Stripe is wired |
| No paying customers = no proof prices are right | High | Validate with 2-3 founding pilot customers before hardcoding prices in Stripe. Be willing to adjust. |
| Competitor launches a similar product at lower price | Low-Medium | StatuteProof's moat is UAE-specific source knowledge + evidence trail + human review gate, not features alone |
| UAE compliance buyers require enterprise contracts, not SaaS | Medium | If true, pivot to annual enterprise agreements ($8,988/year for Professional). Keep monthly pricing as the public anchor. |

---

## 12. Final Recommendation

### What to implement now

1. **Update pricing UI** to reflect honest prices: $349 Monitor, $749 Professional
2. **Fix source count**: The Professional plan currently claims "13–16 sources." Use "13 validated UAE sources" — that is the honest current count. Do not claim 16.
3. **Mark audit export as "Pilot roadmap"** in all plan displays and feature tables
4. **Mark PDF export as "Requires activation"** (not "Available")
5. **Remove Starter plan's claim of "weekly MLRO brief (Limited)"** — replace with "Weekly source status summary" which is what is actually delivered
6. **Add Stripe env variable names to .env.example** — not live values, just the variable names
7. **Keep activation manual** — no Stripe checkout yet
8. **Show pricing publicly** on the website — it's the right signal

### What to do before charging the first customer

1. Complete at least one full source readiness review cycle with a real customer
2. Deliver at least one human-reviewed brief to confirm quality
3. Confirm the weekly Telegram brief delivery is reliable
4. Set up Stripe test-mode products
5. Manually process first payment (invoice or Stripe payment link)

### What NOT to do

- Do not add "audit binder export" to any plan as "Available" until it is built
- Do not launch self-serve Stripe checkout until source readiness, brief delivery, and evidence retention are validated
- Do not price Consultant at a fixed monthly until multi-workspace is built
- Do not claim annual pricing until annual billing is configured in Stripe

---

*Monitoring intelligence only. Not legal advice. Not a compliance certification.*
