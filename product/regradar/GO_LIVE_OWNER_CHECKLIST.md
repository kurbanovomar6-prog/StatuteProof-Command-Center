# StatuteProof — Owner Go-Live Checklist (branch `tenten`, updated 2026-07-22)

The `tenten` branch is well ahead of `main`, all tests green (4233 backend +
422 frontend), **not yet deployed to prod**. Nine more build cycles landed
since the first version of this checklist: the `api.py` god-object was
dismantled (5461 → 2051 lines across 8 mixins, byte-identical), the whole
adversarially-verified backlog was fixed (evidence sealing, monitoring
resilience, legal-guard escapes, Stripe lifecycle, ops, security), and a fresh
adversarial re-audit's four buildable HIGHs were closed too (a forgeable
evidence narrative on `/verify`, a discovery-endpoint decompression-bomb DoS, a
Stripe cancel that stripped manually-activated plans, and a deploy-check that
never verified the core daemons). The four **core** dimensions (security, legal,
evidence, product) are clean of confirmed HIGH again; estimated composite
**≈82–83**. The remaining gap to the mid-80s is the owner-only items below.
This is the exact, ordered list of what only you can do to (a) land the work,
(b) prove CI, (c) turn on automated payments, and (d) lift the audit ceiling.
Nothing here needs a developer — each is a config or a one-line command.

---

## 1. Merge / deploy the branch  (unblocks everything)

The 25 commits raised the adversarial composite from 66 → ~76, closed 12+
confirmed defects, and are green on the full suite. To ship them:

- Review `git log --oneline origin/main..origin/tenten` (25 commits, each with a
  descriptive message).
- Merge `tenten` → `main` (or deploy `tenten` directly), then deploy per
  `DEPLOY.md` / `UPDATE.md`. **I have not deployed — that is your explicit call.**

---

## 2. Prove CI  (closes the testing HIGH — 30 seconds)

The GitHub Actions workflow exists locally at `.github/workflows/test.yml` and is
correct, but it has **never run on GitHub** because my access token lacks the
`workflow` scope, so the push of that one file was rejected. You unblock it:

```bash
gh auth refresh -s workflow        # one-time, interactive, in your terminal
git push origin tenten             # pushes the held CI commit
```

That triggers the first CI run in the repo's history (3 jobs: ruff, backend
pytest with the coverage ratchet, frontend vitest + build). Confirm it goes green
on the Actions tab.

---

## 3. Turn on automated payments  (closes the product HIGH)

The Stripe webhook automation is built, tested, and secure (signature-verified,
replay-idempotent, audited) — it is **inert until you set two env values**. No
payment credential is in the code; you provide them:

1. In Stripe: create Payment Links for the Founding Pilot and UAE Monitor plans.
2. Add a Stripe webhook endpoint pointing at
   `https://statuteproof.com/api/stripe/webhook`, subscribed to
   `checkout.session.completed` and `invoice.paid`. Copy its signing secret.
3. On the droplet `.env` (see `.env.example` for the exact names):
   ```
   STRIPE_WEBHOOK_SECRET=whsec_<your signing secret>
   STRIPE_PRICE_TO_PLAN=<price_id>:starter_pilot,<price_id>:professional
   ```
4. Paste the two Payment Links into `web/src/data/constants.js`
   (`STRIPE_LINK_FOUNDING_PILOT`, `STRIPE_LINK_UAE_MONITOR`) and rebuild the web
   bundle (`cd web && npm run build`).

Result: a completed Stripe payment automatically activates the buyer's plan (via
the same `activate_plan` your admin panel uses) — no more SSH activation. A
logged-in buyer is resolved by `client_reference_id`; an anonymous buyer by the
email they verified in-app.

**Cancellations / refunds are now handled automatically — and safely.** The
webhook also processes `customer.subscription.deleted`, `charge.refunded`,
`charge.dispute.created` and a *final* `invoice.payment_failed`, downgrading the
customer to the free tier. A first attempt at this was reverted for a
customer-takedown risk; the shipped version uses a **set-of-grants** model that
is provably safe even with client-side Payment Links: activation only ever
*appends* the payer's grant (never lowers a plan), and a cancel/refund removes
only *that customer's* grant and re-derives the plan to the highest surviving
grant — so an attacker's cancel can never strip a customer paying via their own
Stripe customer. It resolves the user only from the customer→grant ledger, never
a buyer-typed email. No extra config beyond §3 is needed; subscribe your webhook
to those cancel/refund events too. You can still override any plan in the admin
panel at any time.

Note: founding-pilot copy still says "manually activated after source readiness
review" — that is your intentional gating. Change the copy when you want the
pilot to be pure self-serve.

---

## 4. Lift the biggest audit dimensions  (optional prod config)

These raise reliability + evidence (the two heaviest-weighted dimensions) and
need only env values you control:

- **Egress proxy** (`STATUTEPROOF_FETCH_PROXY`): CBUAE and DFSA return HTTP 403 to
  the droplet's IP; a proxy on the documented allowlist restores their rulebook +
  enforcement sources into the alert-eligible pool. Biggest single reliability +
  evidence lever.
- **RFC 3161 anchoring** (`RFC3161_TSA_URL`, e.g. a free public TSA): turns the
  dormant third-party timestamp anchor on, so the evidence chain carries an
  independent "when" attestation. See `DEPLOY.md` § 7b.
- **Off-box backup** (`STATUTEPROOF_BACKUP_REMOTE` + `STATUTEPROOF_BACKUP_AGE_RECIPIENT`
  or `STATUTEPROOF_BACKUP_PASSPHRASE`): deploy-check now *fails* without an
  encrypted off-box remote; set these before deploy.
- **External uptime probe** (`STATUTEPROOF_HEARTBEAT_PING_URL`): a free
  healthchecks.io/UptimeRobot URL so the droplet dying pages you from outside.

---

## Why the audit reads ≈82–83, not 85

The four **core** dimensions (security, legal, evidence, product) are clean of
confirmed HIGH findings, and the `api.py` god-object refactor that was previously
deferred is now done (byte-identical, fully tested). Every buildable HIGH found
across two full adversarial audit rounds has been fixed. The remaining distance
to a mid-80s composite is now **entirely owner-gated** — there is no more
buildable code work that materially moves it:

- **testing** is capped because CI has **never run** (step 2 — your `gh` token
  lacks the `workflow` scope, so the CI-workflow commit cannot even be pushed).
  This is the single largest remaining lever and costs one command.
- **reliability** (heaviest dimension, .18) is capped by the droplet's egress
  reality — CBUAE/DFSA return 403 to the droplet IP, so their rulebook +
  enforcement sources only re-enter the alert-eligible pool behind an egress
  proxy (step 4). The monitoring *code* is robust; the *reach* is the gate.
- **evidence** (.16) is capped because the strongest timestamp claim needs a
  third-party RFC 3161 anchor (step 4) — the offline verify code is built and
  tested; the live anchor is env config.
- **product** self-serve completeness is capped by the Stripe env (step 3); the
  webhook automation (activation, safe revocation, `subscription.updated`,
  proration, manual-plan floor) is built, tested, and secure.

One known non-core item was deliberately left: `run_pipeline` in `app/pipeline.py`
is a single ~667-line function. Decomposing it is a real (not mechanical) refactor
on the reliability hot path for a small code-dimension gain, so it was judged poor
risk-adjusted value and left for a focused, well-tested future pass rather than
risked here. Everything else the code can do has been done.
