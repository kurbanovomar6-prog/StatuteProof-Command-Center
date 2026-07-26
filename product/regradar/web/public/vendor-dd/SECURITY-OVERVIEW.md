# StatuteProof — Security Overview

**Audience:** vendor-risk and information-security teams evaluating StatuteProof.
**Last reviewed:** 2026-07-25. Every control statement below names the module or
configuration file that implements it, so it can be checked against the codebase.
Where a control does not exist, this document says so plainly (see §11, Known
limitations).

StatuteProof is an official-source regulatory monitoring service with
evidence-backed briefs. It monitors selected public regulator websites, detects
text changes, stores hash-sealed evidence records, and delivers monitoring
alerts and briefs for human review. It is monitoring support, not legal advice.

---

## 1. Architecture

Production is a single Linux virtual machine (DigitalOcean droplet, Ubuntu
24.04) running a small set of systemd services. There is no container
orchestration, no managed database cluster, and no multi-region footprint —
this is stated plainly rather than dressed up.

```
                              Internet
                                 |
                       HTTPS 443 (TLS 1.2+)
                                 |
              +------------------+------------------+
              |  Caddy reverse proxy                |
              |  - automatic TLS (Let's Encrypt)    |
              |  - HSTS + security headers          |
              |  - overwrites X-Real-IP per request |
              +---------+----------------+----------+
                        |                |
                 /api/* proxied    static SPA files
                        |            (web/dist)
              +---------v----------+
              |  Python API server |   binds 127.0.0.1:5001 ONLY
              |  (systemd,         |   never exposed directly
              |   statuteproof-api)|
              +---------+----------+
                        |
        +---------------+-------------------------------+
        |               |                               |
  +-----v-----+  +------v------------------+  +---------v--------+
  | SQLite    |  | File evidence store     |  | sources.json     |
  | regradar. |  | evidence/ + data/       |  | (source registry)|
  | db        |  | (hash-chained JSONL +   |  +------------------+
  +-----------+  |  raw/normalized         |
                 |  snapshots)             |
                 +-------------------------+

  Separate systemd units (same host):
    statuteproof-scheduler      - the ONLY process that fetches sources
                                  (hourly sweep, SSRF-guarded outbound)
    statuteproof-telegram-bot   - customer alert-bot pairing listener
    statuteproof-backup.timer   - daily backup (02:30 UTC)
    statuteproof-compaction.timer - daily evidence heartbeat compaction
    statuteproof-verify.timer   - daily evidence-integrity self-check
    statuteproof-heartbeat.timer - 30-min watchdog for a wedged watch loop
```

Sources: `deploy/Caddyfile`, `deploy/systemd/*`, `DEPLOY.md`.

Inbound network surface: ports 22 (SSH, key-only), 80 (redirect), 443 (Caddy).
The firewall (`ufw`) defaults to deny-incoming; `fail2ban` is enabled
(`DEPLOY.md` §2). The API process itself binds to localhost only
(`deploy/systemd/statuteproof-api.service`).

Outbound network activity: fetches of the monitored public regulator
websites (140 enabled sources at the time of writing, from a registry of 461 —
`sources.json`; "enabled" means the fetcher runs against it, which is **not**
the same as producing alert-eligible monitoring — some enabled hosts return 403
to our egress or are geo-restricted, and the per-workspace Source Readiness
Review discloses exactly which sources are alert-eligible for you),
Telegram Bot API and SMTP when those delivery channels are
enabled, and the Anthropic API when AI analysis is enabled (currently disabled
in production, verified 2026-07-18). The RFC 3161 timestamping code is dormant
by default and is **not currently enabled in production**, so no timestamping
authority is contacted at all. See `docs/vendor-dd/DATA-FLOW-AND-RESIDENCY.md`.

## 2. Authentication

- **Password storage:** PBKDF2-HMAC-SHA256, 600,000 iterations, 16-byte random
  per-user salt, constant-time comparison (`hmac.compare_digest`) —
  `app/auth.py::hash_password` / `verify_password`.
- **Sessions:** server-side sessions in SQLite with a 7-day expiry; the session
  cookie is `HttpOnly`, `SameSite=Strict`, `Secure` on non-localhost hosts —
  `app/auth.py` (session table), `app/api.py::_session_cookie_header`.
- **Email verification:** single-use, expiring verification tokens
  (`app/auth.py`, `email_verification_tokens` table).
- **Google sign-in (optional):** OAuth with random `state` values that are
  stored server-side, expire after 10 minutes, and are single-consumption —
  `app/auth.py` (`oauth_states` table).
- **Brute-force resistance:** registration and login endpoints are
  rate-limited per client IP (5/hour and 10/hour respectively) —
  `app/api.py` (`_REGISTER_LIMITER`, `_LOGIN_LIMITER`).

There is no multi-factor authentication at present (see §11).

## 3. Authorization, RBAC and the access log

- **Role model:** a default-deny role→permission matrix with roles `owner`,
  `admin`, `reviewer`, `approver`, `auditor`, and a machine `system` principal.
  Any action not explicitly granted to a role is denied; there is no wildcard —
  `app/rbac.py::can` and the `_MATRIX` table.
- **Runtime enforcement:** mutating API endpoints pass through an RBAC guard
  that resolves the caller's org membership and evaluates the matrix —
  `app/api.py::_rbac_guard`, `app/rbac_runtime.py`. Today every live account is
  the `owner` of its own single-user org (Stage-1 backfill), so the
  least-privilege machinery is live but exercised only when a non-owner seat
  (e.g. `auditor`) is assigned.
- **Fail-open caveat, stated honestly:** if RBAC evaluation itself errors on an
  ordinary mutation, the guard currently fails OPEN (the already-authenticated
  request proceeds) and the anomaly is written to the audit trail. High-stakes
  governance actions — creating or revoking an external Auditor Evidence Room
  share — pass `fail_closed=True` and are DENIED on any RBAC error. The code
  documents a gate: before any real `auditor` seat is assigned to a customer,
  the ordinary path must flip to fail-closed — `app/api.py::_rbac_guard`.
- **Append-only access log:** authorization decisions and sensitive actions are
  written to an `access_log` table that is append-only at two layers: the
  application exposes insert/read helpers only, and SQLite `BEFORE UPDATE` /
  `BEFORE DELETE` triggers abort any modification of recorded rows —
  `app/access_log.py`, triggers in `app/db.py`. External evidence-room views
  (allowed and denied) are also logged — `app/evidence_room.py`.
- **Paid-capability gate:** exports are additionally gated server-side on the
  account's operator-activated plan; a plan-lookup failure denies access
  (fail-closed) — `app/api.py::_require_capability`, `app/plan.py`.

## 4. Tenancy and isolation model

StatuteProof runs a single application instance and a single database;
isolation is enforced in the application layer, not by physical separation.
Stated plainly:

- **Shared content:** official regulator sources and their evidence records are
  public-content and shared across accounts by design.
- **Private content:** a customer's *custom* sources are visible only to the
  account recorded as owner. The scoping rule is centralised in one module and
  is fail-closed: a custom source whose owner cannot be resolved is denied,
  never attributed; a duplicate or conflicting ownership row denies rather than
  widens access — `app/tenancy.py` (`denied_custom_source_ids`,
  `custom_source_owner`).
- **Per-user records:** review checklists, delivery logs, Telegram pairing,
  plan state and profile data are keyed and queried by owner user id; cross-user
  lookups match zero rows and return the same 404 as "does not exist" (no
  existence oracle) — e.g. `app/action_checklist.py`.

## 5. Rate limiting and request hardening

- Fixed-window, per-client-IP, per-endpoint rate limiters cover registration,
  login, contact, Telegram pairing/tests, delivery tests, brief generation,
  checklists, exports (30/hour per export type), the public verifier (60/hour)
  and the public evidence room (60/hour) — `app/api.py` (`_RateLimiter` and the
  limiter table around it).
- The rate-limit key uses only the proxy-controlled `X-Real-IP` header, which
  Caddy strips and re-sets on every request from the real TCP peer;
  client-appendable `X-Forwarded-For` is deliberately not trusted —
  `app/api.py::_client_ip`, `deploy/Caddyfile`.
- Request bodies are capped at 512 KB; oversized bodies get a 413 and the
  connection is closed — `app/api.py::_read_json`.
- Every API response carries: `Cache-Control: no-store`,
  `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`,
  `Referrer-Policy: strict-origin-when-cross-origin`, a restrictive
  `Permissions-Policy`, HSTS, and `Content-Security-Policy: default-src 'none';
  frame-ancestors 'none'; base-uri 'none'` — `app/api.py::_SECURITY_HEADERS`.
  The SPA is served with its own scoped CSP — `deploy/Caddyfile`.
- CORS is off by default (same-origin production deployment); an explicit
  origin allowlist can be configured by environment variable —
  `app/api.py` (`CORS_ALLOWED_ORIGIN`).
- Error responses are generic (`"Internal server error."`); stack traces are
  not returned to clients — throughout `app/api.py`.

## 6. Outbound transport hardening (the fetch pipeline)

The monitoring pipeline fetches external regulator websites on a schedule.
Because those fetches are the product's largest attack surface, they are
bounded and SSRF-guarded (`app/adapters/base.py`):

- **Scheme allowlist:** only `http`/`https` are ever fetched; `file://`,
  `ftp://` etc. are refused.
- **SSRF guard with IP pinning:** before every hop, the target host is
  resolved and rejected if ANY resolved address is non-public (loopback,
  RFC 1918, link-local including cloud metadata 169.254.169.254, unique-local,
  multicast, reserved, IPv4-mapped IPv6 unwrapped first). The vetted IP is then
  pinned for the actual connection so DNS rebinding between check and connect
  is closed — `_resolve_public_addr`, `_PinnedHTTPAdapter`.
- **Manual, bounded redirects:** redirects are followed manually
  (`allow_redirects=False`) with a maximum of 5 hops, and every hop re-runs the
  SSRF guard.
- **Bounded reads:** responses are read in chunks with a hard 10 MB
  decompressed-size ceiling (`MAX_FETCH_BYTES`), guarding against
  decompression-bomb responses; PDF fetches carry their own 15 MB caps
  (e.g. `app/adapters/vara.py`, `app/adapters/fta.py`).
- **Undecodable-content guard:** content that does not decode as readable text
  is failed closed rather than propagated to customers (`app/adapters/base.py`
  readability checks; excerpt guards in `app/evidence_room.py`).
- The optional RFC 3161 timestamping call applies the same discipline:
  http(s)-only, redirects refused outright, 1 MB response cap, clamped
  timeouts — `app/rfc3161_anchor.py::_post_timestamp_query`. (That call is not
  currently enabled in production, so this hardening is latent rather than
  load-bearing today — see §11.8.)

## 7. Secrets handling

- All secrets and configuration come from environment variables loaded from a
  `.env` file owned by the service user with mode 600; nothing is hardcoded —
  `app/config.py`, `DEPLOY.md` §4.
- Supported secrets: session `SECRET_KEY` (generator command provided),
  Telegram bot tokens, SMTP / email-provider credentials, optional
  `ANTHROPIC_API_KEY`. A pre-start `deploy/deploy-check.sh` gate verifies
  required configuration before services are enabled.
- The admin (founder) Telegram bot token and chat id are never exposed to
  customers; the customer alert bot is a separate token
  (`app/telegram_settings.py`, project `CLAUDE.md`).

## 8. Host and service hardening

From `deploy/systemd/*` and `DEPLOY.md`:

- Services run as a dedicated non-login system user (`regradar`), with
  `NoNewPrivileges=true`, `PrivateTmp=true`, `ProtectSystem=full`, and
  per-service memory/CPU/task ceilings so one runaway process cannot take the
  host down.
- SSH is key-only (password auth disabled); root login is
  `prohibit-password`; `fail2ban` is enabled.
- Logs go to journald with a global 500 MB cap plus logrotate for app file
  logs (daily, 14 rotations, 50 MB max per file) — `deploy/logrotate.d/`.

## 9. Backups, recovery and integrity self-checks

- **Daily backup (02:30 UTC, systemd timer):** a consistent SQLite copy via
  the online-backup API plus a tar of the evidence tree and source registry;
  the newest 14 archives are retained — `deploy/backup.sh`,
  `deploy/systemd/statuteproof-backup.*`.
- **Off-box copies:** each archive is pushed to an operator-configured off-box
  remote (rclone/S3 or scp). Since 2026-07-20 this is **required in code**: the
  deploy gate (`deploy/deploy-check.sh`) fails when `STATUTEPROOF_BACKUP_REMOTE`
  is unset, so a host deployed from that code copies the database and evidence
  tree to storage outside the droplet on every run. **The archive is encrypted
  before it leaves the host** — age public-key encryption
  (`STATUTEPROOF_BACKUP_AGE_RECIPIENT`, private identity held off-box) or gpg
  symmetric AES-256; the same gate fails when a remote is configured without an
  encryption secret, or with a secret whose tool is not installed, and
  `backup.sh` refuses the push outright rather than sending an archive in clear.
  The remote is operator-chosen, so its jurisdiction is a deployment decision —
  see DATA-FLOW-AND-RESIDENCY.md § 4.
  **Deployment status (stated plainly):** this control **takes effect on the
  production host at its next deploy**. Until that deploy the live host's
  backups are local to the droplet only, so they do not survive host loss. Ask
  us for the deploy date and for the remote's provider and region.
- **Documented restore:** a step-by-step restore runbook exists
  (`DEPLOY.md` § Restore). Restore drills are not run on a fixed calendar and
  no tested-restore date is claimed, so no recovery-time objective is claimed.
- **Daily integrity self-check:** a read-only job re-hashes every evidence
  snapshot against its sealed hash and re-verifies the tamper-evident chain;
  any divergence pages the operator and exits non-zero —
  `deploy/systemd/statuteproof-verify.*`, `run.py verify-trail-watch`. This is
  a property of the deployment rather than of the code: it runs because the
  timer unit is enabled on the host, and `deploy/deploy-check.sh` fails the
  deploy when that unit is not both enabled and active.
- **Watchdog:** a 30-minute heartbeat check alerts the operator if the
  monitoring loop is wedged or stale — `deploy/systemd/statuteproof-heartbeat.*`.
  **Its limit, stated plainly:** the watchdog runs *on the host it watches*, so
  it detects a wedged monitoring loop but cannot page anyone if the droplet
  itself dies. Coverage for total host loss requires an external probe — after
  each successful internal check the app pings an operator-supplied
  healthchecks.io/UptimeRobot-style URL (`STATUTEPROOF_HEARTBEAT_PING_URL`,
  `app/ops_alert.py`), and that external service alerts when the pings stop.
  That variable is optional; the deploy gate warns rather than fails when it is
  empty. Ask us whether it is set on the host you are assessing — we will not
  assert an external probe here that this repository cannot evidence.

## 10. Incident response and support posture (honest)

StatuteProof is operated by a single founder-operator. There is no 24×7 SOC,
no on-call rotation, and no formal incident-response retainer. What exists:

- Operational alerts (integrity divergence, wedged monitor loop, service
  failures) page the operator via Telegram automatically.
- systemd restarts failed services automatically (`Restart=on-failure`).
- Incident handling is best-effort by the operator. The operator's practice
  is to notify customers of incidents affecting their data or deliveries
  directly; there is no automated status page. No contractual notification
  commitment or target response window is currently offered — if one is
  required, it must be negotiated explicitly; none exists by default.

## 11. Known limitations (candid)

We would rather you read these here than discover them in diligence:

1. **Single host, single region.** One virtual machine hosts everything.
   Availability is bounded by that host and by DigitalOcean; recovery from
   host loss is restore-from-backup, not failover.
2. **SQLite + file store, not a managed database.** Appropriate at current
   scale; it is not a clustered or point-in-time-recovery database.
3. **No external penetration test yet.** Security review to date is internal
   adversarial review and an automated test suite (over 120 test modules covering,
   among others, the API security surface, SSRF guard, RBAC, tenancy, evidence
   hashing and backup wiring — `tests/`). No third-party pentest report exists.
4. **No certifications.** No SOC 2, no ISO 27001, no regulator certification of
   any kind. We do not claim otherwise anywhere.
5. **No MFA** on customer accounts yet.
6. **RBAC fail-open on ordinary mutations** (see §3) until the documented
   Stage-3 flip; high-stakes external-share actions already fail closed.
7. **Solo-operator continuity risk.** Key-person risk is real. Mitigations
   that exist today: documented deploy/restore runbooks (`DEPLOY.md`,
   `RESET_RUNBOOK.md`), customer-held evidence packs that verify offline
   without StatuteProof (see the Evidence Integrity Whitepaper), and daily
   backups. A formal continuity/escrow arrangement: not currently in place.
8. **Tamper-EVIDENT, not tamper-proof, evidence.** The evidence chain detects
   in-place alteration; an actor with full write access who re-links the whole
   trail is caught today only by the separately persisted head anchor. The
   external RFC 3161 anchor that would add a third-party signature is built and
   tested but **not currently enabled in production** — `RFC3161_TSA_URL` is
   unset on the live host, so no timestamp tokens exist and none ship in
   evidence packs. Earlier revisions of this pack dated 2026-07-18 said it was
   enabled; that was wrong and is corrected here and in
   `EVIDENCE-INTEGRITY-WHITEPAPER.md` §7. This scope is stated in the open spec
   (`docs/EVIDENCE-VERIFICATION-SPEC.md` §1).
9. **No formal SLA.** Monitoring sweep cadence is hourly by design
   (`deploy/systemd/statuteproof-scheduler.service`), but no contractual
   uptime or detection-latency guarantee is offered. Source publication
   delays, site changes and access limits can delay or prevent detection.

---

*For monitoring information only. Not legal advice and not a guarantee of
compliance.*

Questions: hello@statuteproof.com (the monitored operator contact address)
