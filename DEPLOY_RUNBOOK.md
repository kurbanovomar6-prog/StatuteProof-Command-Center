# DEPLOY_RUNBOOK — converged main (2026-07-06)

**Deploy was NOT performed in this session.** No ssh action was attempted:
the parallel deploy session owns the droplet, and no owner confirmation for
agent-side deploy was given in-session. This runbook is the hand-off.

## Critical reconciliation with the in-flight deploy (owner decision)

The parallel deploy session pins **c1ddb8a**. That commit predates ALL of
today's converged fixes and ships the dependency set with **10 pip-audit
findings (pypdf ×5, deepdiff ×2, pdfminer-six ×2, requests ×1) and 1 HIGH
npm (vite)** — verified this session. Converged main **1992acc** carries the
fixed dependency set (0 pip-audit findings, 0 npm vulnerabilities, verified),
plus the truthful rubric, cache-freshness, base-dir, and badge fixes.

Owner choice (pick one, explicitly):
- **A (recommended):** move the deploy pin to `1992acc` before first
  customer-facing operation. Requires scheduling the coordinated baseline
  reset in the same window (see below) because v2 normalization flips
  ~300/316 stored baselines.
- **B:** finish the deploy on c1ddb8a as planned, accept known CVEs +
  false-HIGH rubric in prod until Update Day #1, then update to 1992acc
  WITH the baseline reset per `product/regradar/RESET_RUNBOOK.md`.

**Never run monitoring on 1992acc against existing baselines without alert
suppression** (`ALERT_DRY_RUN=true`, email send disabled): the first cycle
re-baselines ~86 enabled sources and would mass-fire planned CHANGED alerts.
This applies to LOCAL runs too.

## Owner-hands checklist 1 — Telegram alerts-bot token rotation (S1, overdue)

The old token sat in a 438MB world-readable local log for ~2 weeks (D5).
1. BotFather → `/mybots` → @statuteproofalerts_bot → API Token → Revoke.
2. Update `TELEGRAM_ALERTS_BOT_TOKEN` in the droplet `.env`
   (`umask 077; nano .env` on the server — never commit, never paste in chat).
3. Restart the listener service; verify fresh pid, no stale pidfile.
4. Verify the OLD token is dead:
   `curl -s https://api.telegram.org/bot<OLD_TOKEN>/getMe` → expect 401
   (run where the old token still exists; do not print it).
5. Count (never print) old-token occurrences in the big log:
   `grep -c '<OLD_TOKEN>' product/regradar/logs/telegram_bot.log`
6. Truncate/rotate that log ONLY after an explicit owner OK (evidence
   question: nothing in it is needed — it is retry noise + token leaks).
7. Repeat 1–2 for @StatuteProof_bot (admin) if it ever appeared in logs
   (not observed this session — optional).

## Owner-hands checklist 2 — DNS cutover

Current truth (verified this session): apex+www A → 207.154.250.157
(port 443 refused); new droplet 138.68.70.215 has only :22 open.
1. In the DNS panel (NS provider): A @ → 138.68.70.215 (TTL 300),
   A www → 138.68.70.215 (TTL 300). MX/SPF/DKIM untouched.
2. Verify propagation:
   `dig +short @8.8.8.8 statuteproof.com A` and `@9.9.9.9` → 138.68.70.215.
3. Pre-DNS smoke against the droplet directly:
   `curl -sk -H 'Host: statuteproof.com' https://138.68.70.215/health`
4. Post-cutover: `curl -s https://statuteproof.com/health` +
   cert issuer/expiry via `openssl s_client` or browser.

## Agent-deployable steps (ONLY with in-session owner confirmation + ssh)

Not executed. When authorized: deploy `1992acc` (never c1ddb8a) per
`product/regradar/DEPLOY.md` §step order, then:
- systemd units (in `product/regradar/deploy/`) with `Restart=always`
  for API, scheduler, telegram listener; `enable --now` each.
- Prove: fresh listener pid vs pidfile; one full scheduler cycle writing
  real MONITOR_OK evidence (with alerts suppressed if pre-reset);
  `curl https://statuteproof.com/api/health` from outside; services
  survive `systemctl restart`; reboot test only with owner OK.

## Phase 5 (owner-gated; prepared, NOT executed)

1. **Update-Day baseline reset** — procedure ready in
   `product/regradar/RESET_RUNBOOK.md` (measured: 300/316 flips, 86
   enabled). Needs: owner scheduling + suppressed window.
2. **ADGM activation (2 sources)** — probes proved extraction/normalization/
   hashing on 2026-07-06 (`docs/signal/ACTIVATION_PACK.md`):
   `AE-adgm-fsra-waivers` (1,931 chars good), `AE-adgm-ra-circulars`
   (9,291 chars good). Activation = set `monitoring_mode: fresh_alert`,
   `alert_eligible: true` in sources.json AFTER the reset window, with
   per-source MONITOR_OK proof (URL + timestamp + hash + baseline) recorded.
   Awaiting explicit owner yes.
