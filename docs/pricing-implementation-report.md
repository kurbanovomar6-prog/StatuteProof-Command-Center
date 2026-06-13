# StatuteProof Pricing Implementation Report

**Date:** 2026-06-13  
**Status:** Complete — validated, not yet deployed

---

## What Changed

### Plan names and prices

| Plan ID (DB) | Display name | Old price | New price | Change |
|---|---|---|---|---|
| evidence_preview | Evidence Preview | Free | Free | — |
| starter_pilot | Monitor | $299/mo | $349/mo | +$50 |
| professional | Professional | $799/mo | $749/mo | -$50 |
| consultant | Compliance Consultant | From $1,500/mo | Talk to us | removed fixed price |

### Feature corrections (honesty fixes)

| Feature | Before | After | Reason |
|---|---|---|---|
| Monitor source limit | 3 | 5 | Matches actual capability |
| Monitor retention | 30 days | 90 days | Matches actual capability |
| Professional source limit | 13-16 | 13 (exact) | sources.json enabled count is 13 |
| Audit binder export | Available | Pilot roadmap | Feature not built |
| PDF export (Professional) | Available | Requires activation | Not enabled by default |
| Custom sources (Professional) | Available | 3 (requires activation) | Needs onboarding step |
| Weekly brief (Professional) | true | Telegram (email: requires activation) | Email brief not wired |
| Professional users | 3 | 2 | Corrected to match capability |
| Consultant audit export | Available | Pilot roadmap | Feature not built |
| Consultant multi-workspace | Available | Pilot roadmap | Feature not built |
| Consultant white-label | Available | Pilot roadmap | Feature not built |

---

## Files Modified

| File | Type of change |
|---|---|
| `app/plan.py` | PLAN_DISPLAY, PLAN_PRICE_MONTHLY, PLAN_CAPABILITIES corrected |
| `web/src/data/planCapabilities.js` | Full rewrite — honest capabilities, PLAN_FEATURE_STATUS added |
| `web/src/components/PricingPage.jsx` | PLANS_DATA updated — prices, source counts, feature labels |
| `web/src/components/app/ChoosePlanPage.jsx` | PLANS updated — prices, feature lists, locked features |
| `docs/statuteproof-pricing-strategy.md` | Created — full 12-section pricing strategy |
| `product/regradar/.env.example` | Created — Stripe variable names, no real values |

---

## Validation Results

- Python compile: `python3 -m compileall app -q` — **clean, no errors**
- Frontend build: `npm run build` — **clean, built in 2.96s**
- Forbidden claims scan: no forbidden phrases in customer-facing text
- Price consistency: $349 / $749 / "Talk to us" confirmed identical across plan.py, planCapabilities.js, PricingPage.jsx, ChoosePlanPage.jsx
- No .env file committed (only .env.example with placeholder values)
- No legal advice claims, no regulator partner claims, no fake source counts

---

## Stripe Products to Create (when ready)

| Product | Price | Billing | Env var |
|---|---|---|---|
| StatuteProof Monitor | $349/month | Recurring, monthly | `STRIPE_PRICE_MONITOR` |
| StatuteProof Professional | $749/month | Recurring, monthly | `STRIPE_PRICE_PROFESSIONAL` |

Annual discount: not offered yet. Add 15–20% discount after first 10 paying customers confirm annual preference.

---

## What Is Not Wired

- No Stripe checkout or subscription management
- No automated billing trigger on plan selection
- All paid plan activations are manual (team contacts user after plan intent is recorded)
- PDF export, email brief, and custom sources require manual activation per workspace

---

## Next Steps Before Charging Real Money

1. Build and validate audit binder export (currently pilot roadmap)
2. Wire Stripe checkout (use price IDs from .env.example)
3. Add webhook handler for `customer.subscription.created` → update `plan_name` in DB
4. Remove "requires activation" label from PDF export once enabled by default
5. Run Agent Council review before first live billing activation
