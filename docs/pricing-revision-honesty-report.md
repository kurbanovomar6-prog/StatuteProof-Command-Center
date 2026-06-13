# StatuteProof Pricing Revision — Honesty Report

**Date:** 2026-06-13  
**Revision:** Early pilot stage correction  
**Status:** Complete — validated, committed

---

## Why the Previous Pricing Was Too Aggressive

The previous pricing ($349 / $749 / month) was set as if StatuteProof were a validated product with:
- paying customers
- proven evidence delivery workflow
- audit binder export shipped
- weekly brief confirmed in production
- source-readiness validation completed at scale

None of those are true yet. The honest product state is:

| Dimension | Honest assessment |
|---|---|
| Paying customers | 0 — no revenue yet |
| Source validation | 13 sources enabled, evidence-readiness pass still in progress |
| Audit binder export | Not built — pilot roadmap |
| PDF export | Not default — requires activation |
| Weekly MLRO brief | Telegram wired; email requires activation |
| Custom sources | Requires manual onboarding — not self-serve |
| Multi-workspace | Pilot roadmap |
| White-label reports | Pilot roadmap |
| Dashboard UX | Improving but not customer-proven |
| Public trust signals | None yet — no reviews, case studies, or public pilots |

At $349/month with no track record, a compliance buyer sees a product claiming enterprise pricing without enterprise proof. The right response is to price for trust-building, not revenue maximization.

---

## Final Pricing Decision

| Plan | DB ID | Old price | New price | Change |
|---|---|---|---|---|
| Source Readiness Review | evidence_preview | Free | Free | — |
| Founding Pilot | starter_pilot | $349/month | **$199/month** | -$150 |
| UAE Monitor | professional | $749/month | **$399/month** | -$350 |
| Compliance Consultant | consultant | Talk to us | Talk to us | — |

### Why $199, not $149, for Founding Pilot

$149 signals toy tier in B2B compliance tooling. Compliance buyers have high CAC tolerance and expect professional pricing — even for early products. At $149:
- Buyers may doubt the data quality
- It anchors expectations too low for future price increases
- It's harder to justify $399 as "twice as good" when the gap starts at $149

$199/month is accessible for an early pilot while still reading as a real commercial product. The gap to $399 (UAE Monitor) is clear and earnable. Both are still 80%+ below Hyperproof's $1,000/month entry point and 95%+ below LogicGate's $4,300/month median.

### Why $399 for UAE Monitor, not higher

UAE Monitor includes:
- 13 sources under evidence-readiness validation (not yet fully proven at scale)
- High-risk review queue
- Weekly MLRO brief (Telegram; email still requires activation)
- 180-day retention
- 2 users
- Up to 2 custom sources (requires activation — not yet self-serve)

Audit binder export and PDF export are missing. These are the features compliance buyers expect at $600+. Until they ship, $399 is the right ceiling. After audit export is available and at least 5 customers have used the full evidence workflow, $499–$599 is defensible.

---

## Current Product Maturity Assumptions

These assumptions are baked into the pricing and must be checked before any increase:

1. **Evidence-readiness validation is complete** — all 13 enabled sources pass source readiness review for at least one UAE-regulated firm profile
2. **Weekly brief delivery is stable** — Telegram brief fires correctly on schedule for paying pilots
3. **Evidence records are reliable** — diff hashes, timestamps, and evidence records are generated correctly and reproducibly
4. **Dashboard is customer-usable** — a compliance officer can log in, navigate to evidence, review a diff, and understand the source status without hand-holding

None of these should be assumed. They must be proven with the first 2–3 founding pilot customers.

---

## What Must Be Proven Before Increasing Prices

| Gate | What to prove | Unlocks |
|---|---|---|
| Evidence readiness pass | All 13 sources pass readiness for at least 1 customer | Claim "validated source pack" without qualification |
| First paying customer | 1 customer completes source readiness → activation → live monitoring | Any price increase |
| Brief delivery | Weekly brief fires correctly for 4 consecutive weeks | Remove "requires activation" from weekly brief |
| Audit binder export | Feature built, tested, delivered to a pilot customer | $499+ pricing; remove "pilot roadmap" label |
| 5 paying customers | 5 customers on founding pilot or UAE Monitor | Public pricing page confident |
| Case study or testimonial | 1 named or anonymized reference | Enterprise pricing ($799+) |

---

## Plan Capability Changes (Honesty Corrections)

| Plan | Field | Old value | New value | Reason |
|---|---|---|---|---|
| Founding Pilot | sourceLimit | 5 | 3 | Back to honest early-pilot count |
| Founding Pilot | retentionDays | 90 | 30 | Matches actual founding pilot scope |
| Founding Pilot | weeklyBriefs | status_only | status_only | Unchanged — correct |
| UAE Monitor | sourceLimit | 13 | 13 | Unchanged — correct, qualified label added |
| UAE Monitor | customSources | 3 | 2 | "Up to 2 requires activation" is more honest than 3 |
| UAE Monitor | retentionDays | 365 | 180 | 365 days implies a proven archive; 180 is more honest pre-validation |
| Consultant | auditExport | true (old) | false (pilot roadmap) | Not built |
| Consultant | multipleWorkspaces | true (old) | false (pilot roadmap) | Not built |
| Consultant | whiteLabel | true (old) | false (pilot roadmap) | Not built |

---

## Stripe Handling

No Stripe products created. No real price IDs inserted.

`.env.example` updated with correct env variable names:

```
STRIPE_PRICE_STARTER=price_...        # $199/month — Founding Pilot
STRIPE_PRICE_PROFESSIONAL=price_...  # $399/month — UAE Monitor
# Consultant stays manual — no Stripe product yet
```

**Old names** (STRIPE_PRICE_MONITOR, STRIPE_PRICE_PROFESSIONAL) are replaced with STRIPE_PRICE_STARTER / STRIPE_PRICE_PROFESSIONAL to match the new plan positioning.

Self-serve Stripe recommended now: **No.** Activate manually for the first 5 customers. Stripe adds complexity (webhooks, subscription state, proration) before the product value is validated. Manual activation keeps the team in the loop for every pilot.

---

## Files Changed

| File | Change |
|---|---|
| `product/regradar/app/plan.py` | PLAN_DISPLAY (new names), PLAN_PRICE_MONTHLY ($199/$399), PLAN_CAPABILITIES (source limits, retention, high_risk_queue field) |
| `product/regradar/web/src/data/planCapabilities.js` | Full rewrite — new names, prices, capabilities |
| `product/regradar/web/src/components/PricingPage.jsx` | PLANS_DATA — new names, prices, feature labels, new FAQ entry on evidence-readiness validation |
| `product/regradar/web/src/components/app/ChoosePlanPage.jsx` | PLANS — new names, prices, feature lists, honest locked features |
| `product/regradar/web/src/components/app/BillingPage.jsx` | PLAN_DISPLAY, upgrade CTA copy, weekly brief label |
| `product/regradar/web/src/components/app/PlanBanner.jsx` | Recommended plan updated to "UAE Monitor"; trial expired copy updated |
| `product/regradar/.env.example` | Stripe variable names updated |
| `tools/validate_workspace.py` | Allow `.env.example` files (false positive fix) |

---

## Validation Results

| Check | Result |
|---|---|
| `python3 -m compileall app -q` | Clean |
| `npm run build` | Clean — built in 499ms |
| Forbidden claims scan | None in customer-facing pricing surfaces |
| Stale price scan ($349/$749) | None found |
| `validate_codex_skills.py` | Passed — 8 skills validated |
| `validate_workspace.py` | Passed — workspace clean |
| `.env` committed | No — only `.env.example` with placeholders |
| Price consistency | $199/$399/"Talk to us" confirmed across plan.py, planCapabilities.js, PricingPage.jsx, ChoosePlanPage.jsx, BillingPage.jsx |

---

## Public Pricing Recommended Now: Yes, with Caveats

Show pricing publicly. Buyers expect to see numbers. Hiding pricing signals either "we charge too much" or "we don't know what we charge."

**But qualify it clearly:**
- "Founding pilot pricing — manually activated after source readiness review"
- "No payment method required to start"
- Features marked "Pilot roadmap" are not live by default

Do not publish a Stripe checkout or self-serve payment link until the first founding pilot customer has completed the full evidence → brief → review cycle.

---

## Next Exact Task

**Run the first source-readiness validation pass on a real UAE-regulated firm profile.**

Steps:
1. Select a firm type (e.g., VARA-licensed VASP)
2. Run `python3 app/source_readiness.py --profile vara_vasp` (or equivalent)
3. Review which of the 13 sources pass / are limited / blocked
4. Document the results as the first real evidence record
5. Use this as the founding pilot onboarding template

Until this is done, no pricing claim — however conservative — is fully verifiable.
