# StatuteProof — Vendor Due-Diligence FAQ

**Audience:** procurement and vendor-risk teams. Short, verifiable answers to
the questions a financial-institution vendor questionnaire typically asks.
**Last reviewed:** 2026-07-20. Where an answer cites a module or config file,
the claim can be checked against the codebase. Where a fact is not in place or
not committed, this document says so plainly rather than guessing or implying
otherwise.

Companion documents in this pack: `SECURITY-OVERVIEW.md`,
`DATA-FLOW-AND-RESIDENCY.md`, `EVIDENCE-INTEGRITY-WHITEPAPER.md`.

---

## Company

**1. What is StatuteProof?**
Official-source regulatory monitoring with evidence-backed compliance briefs.
The system monitors selected public regulator websites, detects text changes,
stores hash-sealed evidence records, and produces monitoring briefs and alerts
for human review. It is monitoring support — not legal advice, not a
compliance guarantee, and not a substitute for qualified counsel or
compliance professionals.

**2. What is the legal entity, registration number and registered address?**
Corporate registration details are not published in this pack — nothing in the
codebase or deployment configuration evidences them, and we would rather leave
this unanswered here than guess. Request entity details directly through
hello@statuteproof.com as part of contracting.

**3. How large is the team?**
StatuteProof is built and operated by a single founder-operator. We state this
plainly rather than imply a larger organisation; the operational consequences
(support posture, continuity) are addressed honestly in questions 17–19.

**4. Do you hold SOC 2, ISO 27001 or similar certifications?**
No. No SOC 2, no ISO 27001, no other security certification. We do not claim
any regulator certification, approval or partnership anywhere, and our own
content rules forbid such claims. What we offer instead is a small, fully
inspectable control surface: this documentation names the exact module for
each control so the claims can be verified against the codebase. There is no
standing, committed code-inspection programme (e.g. a scheduled supervised
read-only review under NDA is not currently offered as a formal product);
evaluating teams that need code inspection should arrange it case-by-case via
hello@statuteproof.com.

## Hosting and infrastructure

**5. Where is the service hosted?**
A single DigitalOcean virtual machine (droplet) running Ubuntu 24.04, deployed
per the runbook in `DEPLOY.md`. Region: DigitalOcean **FRA1 (Frankfurt,
Germany — EU)**, verified against the live deployment 2026-07-18 — single
region, no multi-region replication (`DATA-FLOW-AND-RESIDENCY.md` §5).

**6. What is the production architecture?**
Caddy (TLS via Let's Encrypt, HSTS, security headers) reverse-proxies a
Python API bound to localhost only; storage is SQLite plus a file-based
evidence store; monitoring, backups, integrity checks and watchdogs run as
separate hardened systemd services and timers. Full diagram:
`SECURITY-OVERVIEW.md` §1.

**7. Is data encrypted in transit and at rest?**
In transit: yes — TLS on all customer traffic (Caddy/Let's Encrypt), and
outbound deliveries go over TLS to Telegram/SMTP endpoints. At rest: the
application does not add its own encryption-at-rest layer for on-host data;
disk-level protection is what the hosting provider supplies for droplet
volumes. Stated plainly. The one exception is the off-box backup archive,
which is encrypted on the host (age or gpg AES-256) before it is pushed to the
operator's remote, and is never pushed if that encryption is unavailable. The integrity (rather than confidentiality) of evidence at rest is
separately protected by hash sealing and daily re-verification
(`EVIDENCE-INTEGRITY-WHITEPAPER.md`).

## Data

**8. What customer data do you store?**
Account email and password hash (PBKDF2-SHA256, 600k iterations —
`app/auth.py`), optional profile fields (name, company, industry), an optional
Telegram chat id if the customer pairs Telegram (`app/telegram_pairing.py`),
user-authored review checklist text (`app/action_checklist.py`), delivery
logs, and plan state. Everything else the system stores is public regulator
content and its integrity metadata. Full inventory:
`DATA-FLOW-AND-RESIDENCY.md` §3.

**9. Do you process our transaction, consumer or client data?**
No. There is no ingestion path for customer transaction or consumer data — no
upload feature, no integration that reads your systems. The monitored content
is public regulator material. This scoping is the factual basis for assessing
UAE data-residency rules against this service (see
`DATA-FLOW-AND-RESIDENCY.md` §1); your own advisers should make that
assessment.

**10. Who are your sub-processors?**
DigitalOcean (hosting); Telegram and the configured email provider — currently
Zoho Mail SMTP in production, verified 2026-07-18 (only when the customer
enables those delivery channels); Google (only for optional Google sign-in);
Anthropic (only if optional AI analysis is enabled — `ENABLE_AI_ANALYSIS` is
currently **disabled** in production, verified 2026-07-18; when enabled it
receives bounded excerpts of monitored public content, never customer data);
an RFC 3161 timestamping authority — dormant by default in code, **enabled in
production since 2026-07-18** (freetsa.org; it receives a single hash, never
content); off-box backup storage — **required in code** since 2026-07-20, so
any host deployed from that code pushes a daily archive to an operator-chosen
remote, encrypted on the host before it is sent; that requirement **takes
effect on the production host at its next deploy**, and until then production
backups are local to the host. Ask us for the deploy date and for that remote's
provider and region as part of your assessment. Full
table with "engaged when" conditions: `DATA-FLOW-AND-RESIDENCY.md` §7.

**11. What is your data retention policy?**
Evidence of change is kept indefinitely (that is the product); redundant
"unchanged" heartbeats older than 30 days are compacted to one per source per
day; sessions expire in 7 days; share links expire in at most 90 days; backups
keep the newest 14 daily archives; the access log is append-only and
permanent. Account data has no automated expiry; deletion is on request via
the operator (no self-service deletion yet). Full table:
`DATA-FLOW-AND-RESIDENCY.md` §6.

## Security controls

**12. How is access to the production environment controlled?**
SSH is key-only (password authentication disabled), root login restricted,
firewall default-deny with only 22/80/443 open, fail2ban enabled
(`DEPLOY.md` §2). Application services run as a dedicated non-login user with
systemd hardening (`NoNewPrivileges`, `PrivateTmp`, `ProtectSystem=full`,
resource ceilings — `deploy/systemd/`). Production access is held by the
operator only.

**13. How is customer access authenticated and authorized?**
Password login (PBKDF2-SHA256) or optional Google OAuth; server-side sessions
with HttpOnly/SameSite=Strict/Secure cookies; per-IP rate limits on auth
endpoints. Authorization uses a default-deny RBAC matrix (owner / admin /
reviewer / approver / auditor / system) enforced at mutating endpoints, with
decisions written to an append-only access log whose rows cannot be updated or
deleted at the database layer (`app/rbac.py`, `app/rbac_runtime.py`,
`app/access_log.py`). One honest caveat, documented in
`SECURITY-OVERVIEW.md` §3: on an internal RBAC-evaluation error, ordinary
mutations currently fail open (the authenticated request proceeds, and the
anomaly is logged); high-stakes external-share actions already fail closed.

**14. Is there MFA?**
Not yet on customer accounts. On the roadmap; we will not claim it before it
ships.

**15. How do you prevent one customer seeing another's data?**
Application-level tenancy on a single database, enforced through one shared
fail-closed scoping rule: official monitored sources are shared public content
by design; a customer's custom sources and all per-user records (checklists,
deliveries, pairings) are scoped to the owning account, and unresolvable or
conflicting ownership denies rather than grants (`app/tenancy.py`). Cross-user
lookups return the same 404 as "not found" (no existence oracle).

**16. What protects the service from abuse and hostile inputs?**
Per-IP, per-endpoint rate limiting keyed on a proxy-controlled header; a
512 KB request-body cap; strict security headers and a `default-src 'none'`
API CSP; generic error messages (no stack traces). Outbound fetching of
monitored sites is SSRF-guarded (public-IP-only resolution with IP pinning,
manual bounded redirects, scheme allowlist) and size-bounded (10 MB
decompressed cap; 1 MB cap on TSA responses). Details with module references:
`SECURITY-OVERVIEW.md` §5–§6.

## Operations, BCP and incident response

**17. What is your backup and recovery capability?**
Daily automated backups (consistent SQLite online copy + evidence tree
archive), 14-archive retention, and a documented step-by-step restore runbook
(`deploy/backup.sh`, `DEPLOY.md` § Restore). An off-box backup remote is
**required in code** since 2026-07-20: the deploy gate fails without one, so a
host deployed from that code copies each archive to an operator-chosen remote.
That copy is encrypted on the host first (age public key or gpg AES-256) and
the push is refused outright if encryption is unavailable or its tooling is not
installed, so an archive containing account data never leaves the host in
clear. A single development-only override (`STATUTEPROOF_ALLOW_UNENCRYPTED_BACKUP`)
exists to let a local developer push without encryption, and a second
(`STATUTEPROOF_ALLOW_LOCAL_BACKUP_ONLY`) lets a developer skip the off-box
remote entirely; the deploy gate **refuses both on a production host** (one
identified by `ENVIRONMENT=production` or the `/srv/regradar` install path) and
flags them as failures, so neither can be used to weaken a live deployment — we
disclose them here rather than state the controls as unqualified absolutes. That requirement **takes effect on the
production host at its next deploy**; before that deploy the live host keeps
backups locally only, so they do not survive host loss — ask us for the deploy
date. Recovery from
host loss is restore-from-backup onto a fresh host using the documented
deployment runbook — there is no hot standby or failover. Restore drills are
not run on a fixed calendar and no tested-restore date is claimed, so no
recovery-time objective is claimed.

**18. What is your incident response process?**
Best-effort, operator-led. Automated detection exists and pages the operator:
a daily evidence-integrity verification that alerts on any divergence, a
30-minute watchdog for a wedged monitoring loop, and automatic service
restarts (`deploy/systemd/`). There is no 24×7 SOC or on-call rotation, and no
automated status page. No contractual incident-notification window is
currently committed; notification of affected customers is best-effort by the
operator. If a contractual window is a requirement, it must be negotiated
explicitly — none exists by default.

**19. What happens if the operator is unavailable (key-person risk)?**
Acknowledged as the largest continuity risk. Current mitigations: fully
documented deploy and restore runbooks; daily backups; and — most importantly
for an evidence product — customer-held Evidence Packs that verify offline
with a standalone script and a published open specification, so evidence
already delivered to you remains usable and provable with no StatuteProof
involvement at all (`EVIDENCE-INTEGRITY-WHITEPAPER.md` §5). A formal
escrow/continuity agreement is not currently in place.

**20. Do you offer an SLA?**
No formal SLA at present. The monitoring sweep runs hourly by design
(`deploy/systemd/statuteproof-scheduler.service`); detection can be delayed by
source publication delays, website changes, PDF formatting, access limits or
source structure changes, and we say so in every report disclaimer. No uptime
or response commitment is offered today; if one is required it would have to
be negotiated per contract — none is in place.

## Assurance and development practice

**21. Has the service been penetration tested?**
Not externally. Security work to date is internal adversarial review (findings
are tracked and fixed in the commit history) plus an automated test suite of
over 120 test modules that includes dedicated security tests (API security surface,
SSRF guard, auth guards, tenancy leaks, backup wiring — `tests/`). An external
penetration test has not yet been commissioned; when one is commissioned,
the intent is to make the report shareable under NDA.

**22. How are changes managed and reviewed?**
Single-operator development with a mandatory pre-push review gate (automated
code review agents on `git push`), a deployment precondition checklist that
aborts on failure, and a first-hour smoke-test checklist after each deploy
(`DEPLOY.md` §0, §7, first-hour checklist). Honestly stated: there is no
multi-person code-review team.

**23. Are alerts reviewed by a human before customers receive them?**
Review tooling exists and is used — draft/review statuses, an approval
workflow, and evidence-first gates that block briefs without complete sealed
evidence (`app/alert_review.py`, `app/evidence_records.py`). However, a
code-enforced universal "no alert leaves without human sign-off" gate is not
currently implemented for every delivery path; review policy on live delivery
is operator-managed. We flag this ourselves rather than overclaim.

**24. Do you carry professional indemnity / cyber insurance?**
No insurance cover is claimed in this pack — nothing in the codebase or
deployment configuration can evidence an insurance policy either way, and we
will not assert cover we cannot show. If cover is a procurement requirement,
raise it via hello@statuteproof.com during contracting.

## Exit and portability

**25. How do we get our data out, and what survives termination?**
Self-service exports exist today: Evidence Packs, period-based Audit Vault
archives and Regulator Binders — sealed ZIPs containing the captured bytes,
hash manifests and a standalone offline verifier (`app/evidence_pack.py`,
`app/audit_export.py`). Because verification needs only SHA-256 and the
published open spec, exported evidence remains independently verifiable
forever, without StatuteProof. Account records are also self-service: the
dashboard's Settings page ("Export my data") calls `GET /api/account/export`
and downloads one JSON file containing the account profile, workspace
monitoring profile, notification preferences, the user's review checklist
items, the organisation's sealed decision records (verbatim envelopes plus
the chain head), and the Telegram delivery link (`app/account_export.py`).
Sealed decision records in that file are self-contained SHA-256 envelopes, so
they verify offline forever — with the public verifier or standard tools —
without a StatuteProof account.

---

*For monitoring information only. Not legal advice and not a guarantee of
compliance.*

Questions: hello@statuteproof.com (the monitored operator contact address)
