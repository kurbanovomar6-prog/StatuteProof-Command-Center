# StatuteProof — Owner Go-Live Checklist (branch `tenten`, 2026-07-21)

25 commits sit on `origin/tenten`, all tests green, **not yet deployed to prod**.
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
email they verified in-app. Cancellations/refunds remain a manual step for now.

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

## Why the audit still reads ~76, not 85

The four **core** dimensions (security, legal, evidence, product) are now clean of
confirmed HIGH findings. The remaining distance to an 85 composite is gated by:
CI never having run (step 2 — your token scope), payment config (step 3), and the
prod env in step 4 — plus a large `api.py`/`run.py` refactor that carries real
risk to the strong security score for a small weight, which was deliberately not
attempted. Steps 2–4 are the levers; the code is ready for all of them.
