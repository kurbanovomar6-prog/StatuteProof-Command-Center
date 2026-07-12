# StatuteProof — Data Flow and Residency

**Audience:** vendor-risk, data-protection and compliance teams.
**Last reviewed:** 2026-07-12. Claims are grounded in the referenced modules
and deployment configuration; unverifiable operational details are marked
[CONFIRM WITH OPERATOR].

---

## 1. Data minimization — the core statement

StatuteProof monitors **public regulator websites**. The overwhelming majority
of data the system stores is *published official-source content*: page text,
document text, hashes, diffs and capture timestamps of material that the
regulators themselves publish to the open internet.

StatuteProof does **not** receive, process or store:

- customer transaction data;
- consumer / end-client personal data;
- payment card data (plan activation is a manual operator step after payment
  is confirmed off-platform — `DEPLOY.md` §10, `app/plan.py`; there is no
  payment-processing code in the application);
- documents uploaded from the customer's own systems (there is no customer
  document-upload feature);
- special-category personal data of any kind.

The personal data StatuteProof holds about a customer is limited to the
account and delivery records listed in §3 — essentially a work email address,
optional profile fields the user typed, an optional Telegram chat id, and the
user's own authored review notes.

**Residency scoping note.** StatuteProof does not receive, process or store
customer transaction data, consumer or end-client personal data, or payment
data (see the list above); the monitored content is public regulator
material, and the stored customer data is limited to the vendor-account
records in §3. Whether and how UAE data-localization and outsourcing
requirements — including any applicable CBUAE rules — apply to a buyer's use
of this service is for the buyer to assess with its own advisers. This
document states what the system stores and where, so that assessment can be
made accurately.

## 2. Data entering the system

| Flow | Data | Module |
|---|---|---|
| Scheduled monitoring fetches | Public regulator web pages and documents (116 enabled sources at time of writing) | `app/scraper.py`, `app/adapters/*`, `sources.json` |
| Account registration / login | Email, password (stored only as PBKDF2-SHA256 hash), optional full name, company name, industry | `app/auth.py` |
| Google sign-in (optional, user's choice) | Google-asserted email/identity for the account | `app/auth.py` |
| Telegram pairing (optional, user's choice) | Telegram chat id, username, first name, pairing timestamps | `app/telegram_pairing.py` |
| Per-alert review checklist | User-authored to-do text, optional assignee name and due date (the user's own words; StatuteProof never generates checklist items) | `app/action_checklist.py` |
| Website contact form | Name / contact details / message the visitor submits; relayed to the operator via the admin Telegram bot | `app/api.py::_handle_contact` |
| Public verifier (`POST /api/verify`) | Caller-submitted record/bytes, processed statelessly in memory — no filesystem, database or network access; nothing is stored | `app/public_verify.py` |

## 3. Data stored, and where

All storage is on the production host (see §5): a SQLite database
(`regradar.db`) and a file-based evidence store (`evidence/`, `data/`).

| Category | Contents | Store |
|---|---|---|
| Monitored evidence | Raw + normalized snapshots of public regulator content, SHA-256 hashes, diffs, capture timestamps, hash-chained run records | `data/source_runs/`, `evidence/` (see `app/source_runs.py`, `app/evidence_records.py`) |
| Accounts | Email, password hash, profile fields, email-verification and session records | SQLite (`app/auth.py`, `app/db.py`) |
| Delivery | Telegram pairing data, per-user delivery logs, email delivery status log | SQLite + `data/email_outbox/` (`app/telegram_pairing.py`, `app/user_delivery.py`, `app/email_delivery.py`) |
| Review workflow | Alert review decisions, user checklist items, canonical evidence reviews | SQLite + `data/` (`app/alert_review.py`, `app/action_checklist.py`) |
| Audit | Append-only access log of authorization decisions and sensitive/external actions (update/delete blocked by SQLite triggers) | SQLite (`app/access_log.py`) |
| Plan state | Self-selected plan intent + operator-activated plan | SQLite (`app/plan.py`) |

## 4. Data leaving the system

No customer data and no evidence data leaves the system except through the
channels below, each of which the customer or operator explicitly enables.
(Infrastructure traffic — ACME certificate issuance to Let's Encrypt, which
sees domain names only, and the outbound monitoring fetches themselves — is
covered in §5 and §7.)

| Destination | When | What is sent | Module |
|---|---|---|---|
| Telegram Bot API | Customer has paired Telegram and enabled alerts | Alert/brief text (derived from monitored public content) to the customer's own chat id | `app/telegram.py`, `app/telegram_clients.py` |
| Email provider (SMTP; SendGrid/Postmark also supported in code) | Customer email delivery is configured | Verification emails, briefs/alerts to the customer's address | `app/email_delivery.py` |
| Anthropic API (Claude) | Only when `ENABLE_AI_ANALYSIS=true` AND an API key is set; off by default | Bounded excerpts of the *monitored public regulator content* diff (max 20 added + 20 removed paragraphs, each truncated to 400 characters). No customer account data is included in the prompt | `app/ai.py`, `app/ai_brief.py`, `app/config.py` |
| RFC 3161 Time-Stamping Authority | Only when `RFC3161_TSA_URL` is set; **dormant by default** | A single SHA-256 hash (the evidence chain head) — no content, no personal data | `app/rfc3161_anchor.py` |
| Off-box backup remote | Only when `STATUTEPROOF_BACKUP_REMOTE` is set | The encrypted-in-transit backup archive (database + evidence tree) | `deploy/backup.sh` |
| Admin Telegram bot (operator) | Contact-form submissions and operational alerts | Contact message contents; operational health signals | `app/api.py`, `app/ops_alert.py` |

Customer-facing exports (Evidence Packs, Audit Vault, Regulator Binder,
evidence-room shares) are *downloads initiated by the customer* or time-boxed
read-only links the customer creates; they are not automatic outbound flows —
`app/evidence_pack.py`, `app/audit_export.py`, `app/evidence_room.py`.

## 5. Hosting

- **Provider:** DigitalOcean (single droplet / virtual machine), Ubuntu 24.04,
  deployed per `DEPLOY.md`.
- **Region:** [CONFIRM WITH OPERATOR] — the region is chosen at droplet
  creation and is not recorded in the repository. It is a single region; there
  is no multi-region replication.
- **TLS:** terminated by Caddy with automatically managed Let's Encrypt
  certificates; HSTS enabled (`deploy/Caddyfile`).
- **Storage:** SQLite database + file-based evidence store on the droplet's
  disk. Disk-level encryption at rest is whatever the provider supplies for
  droplet volumes; StatuteProof does not add application-level encryption at
  rest (stated plainly; see the FAQ).
- **Backups:** daily on-box archives (14 retained) with an optional off-box
  remote — see `SECURITY-OVERVIEW.md` §9.

## 6. Retention posture

| Data | Retention | Mechanism |
|---|---|---|
| Evidence records: CHANGED / FIRST_SEEN / FAILED / QUALITY_DROP-transition | Kept indefinitely (they are the evidence trail) | `app/retention.py` |
| UNCHANGED heartbeat records | Older than 30 days compacted to one per source per UTC day; the survivor carries the same hash, so no evidence content is lost, only repetition | `app/retention.py`, daily `statuteproof-compaction.timer` |
| Access log | Append-only, retained indefinitely; deletion blocked at the database layer | `app/access_log.py`, `app/db.py` triggers |
| Backups | Newest 14 daily archives | `deploy/backup.sh` |
| Sessions | 7-day expiry | `app/auth.py` |
| Telegram pairing codes | 15-minute time-to-live, single use | `app/telegram_pairing.py` |
| Evidence-room share links | Mandatory expiry: default 30 days, hard cap 90 days, revocable | `app/evidence_room.py` |
| OAuth state values | 10-minute expiry, single consumption | `app/auth.py` |
| Server logs | journald capped at 500 MB; file logs rotated daily, 14 rotations, 50 MB max | `DEPLOY.md` §2, `deploy/logrotate.d/` |
| Account data | No automated expiry. There is currently **no self-service account deletion**; deletion is handled by the operator on request. [CONFIRM WITH OPERATOR] for the deletion-request process and turnaround |

## 7. Sub-processors

| Sub-processor | Purpose | Data exposed | Engaged when |
|---|---|---|---|
| DigitalOcean | Hosting (compute + disk) | All stored data resides on their infrastructure | Always |
| Telegram | Alert delivery + account pairing | Alert text; the customer's Telegram chat id | Only if the customer connects Telegram |
| Email provider — SMTP account [CONFIRM WITH OPERATOR for the current provider]; SendGrid and Postmark are supported in code | Email delivery | Email address; brief/alert text; verification emails | Only if email delivery is configured |
| Anthropic | Optional AI analysis of detected changes | Excerpts of monitored **public** regulator content only; no customer data | Only if `ENABLE_AI_ANALYSIS=true` — [CONFIRM WITH OPERATOR] whether currently enabled in production |
| Google | Optional sign-in identity | Google-asserted account email | Only if the customer chooses Google sign-in |
| RFC 3161 TSA (operator-selected) | External timestamp anchoring of the evidence chain head | One SHA-256 hash; no content, no personal data | Only if `RFC3161_TSA_URL` is configured (dormant by default) |
| Off-box backup storage (rclone/S3 or scp target) | Backup survival beyond the host | Backup archives | Only if `STATUTEPROOF_BACKUP_REMOTE` is configured — [CONFIRM WITH OPERATOR] |
| Let's Encrypt | TLS certificate issuance | Domain names only | Always |

No other third party receives data from the system. Web typography is
self-hosted (bundled with the application — a visitor's browser contacts no
third-party font CDN), and there is no analytics or advertising tooling
anywhere in the codebase.

## 8. What an exiting customer keeps

Evidence Packs, Audit Vault archives and Regulator Binders are self-contained
ZIP downloads that include the captured bytes, the manifest of hashes, and a
standalone, stdlib-only `verify.py` — they remain independently verifiable
offline, with no StatuteProof account and no StatuteProof server, after the
relationship ends (`app/evidence_pack.py`, `app/audit_export.py`,
`docs/EVIDENCE-VERIFICATION-SPEC.md`).

---

*For monitoring information only. Not legal advice and not a guarantee of
compliance.*

Questions: security@statuteproof.com [CONFIRM WITH OPERATOR]
