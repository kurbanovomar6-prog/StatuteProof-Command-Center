# StatuteProof — Deployment Runbook (fresh Ubuntu 24.04, target ≤ 30 min)

Every command below is meant to be run in order, as root unless stated.
Time estimates assume a 2 vCPU / 4 GB droplet and a registered domain with
DNS A records (`statuteproof.com`, `www.statuteproof.com`) already pointing
at the droplet — set DNS **before** droplet day, propagation is not counted.

## 0. Precondition gate (ABORT if any item fails)

Patched 2026-07-05 after the first droplet-day abort (unexplained host-key
change on the old IP). App code deploys from **origin/main** — the converged,
gate-green build (HEAD `679c0a3` at time of writing). The previous `c1ddb8a`
pin was **56 commits stale and pre-convergence** (missing the loader-status,
false-HIGH signal, relevance-scope, and claims fixes); do **not** deploy it.

1. **Telegram token**: rotated via @BotFather; old token revoked; new token
   staged in a local secret file (never chat, never git).
2. **DNS**: `dig +short` for apex + www via **8.8.8.8 and 9.9.9.9** (1.1.1.1
   is blocked on the operator network) both return the NEW droplet IP.
3. **Email — real SMTP required on prod** (`local_outbox` is NOT acceptable;
   the smoke test requires a real external delivery): Zoho app-specific
   password; host `smtp.zoho.eu` or `smtp.zoho.com` per account region;
   port 465 SSL; SMTP user = the alerts mailbox;
   `STATUTEPROOF_EMAIL_FROM` matching it. Credentials entered only at the
   .env step.
4. **Host trust — no trust-on-first-use**: the operator captures the
   expected fingerprint out-of-band from the DigitalOcean web console at
   droplet creation (`ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub`).
   The first SSH connection must match it exactly; any mismatch = ABORT.
5. **Old IP retired**: operator confirms 207.154.250.157 is destroyed (if
   owned) or abandoned (if foreign) and no DNS record anywhere still
   references it. **Zoho MX records stay untouched.**
6. Repository reachable from the droplet: pin present on origin/main.

Smoke-test addition: `dig TXT _dmarc.statuteproof.com` must return the new
DMARC record — paste it in the deploy report.

## 1. Base system + user (≈4 min)

```bash
apt-get update && apt-get install -y python3.12 python3.12-venv python3-pip \
    git curl ufw fail2ban debian-keyring debian-archive-keyring apt-transport-https
useradd -r -m -d /srv/regradar -s /usr/sbin/nologin regradar
```

## 2. Hardening: firewall, ssh, fail2ban (≈3 min)

```bash
ufw default deny incoming && ufw default allow outgoing
ufw allow 22/tcp && ufw allow 80/tcp && ufw allow 443/tcp
ufw --force enable
# ssh: key-only auth
sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
sed -i 's/^#\?PermitRootLogin.*/PermitRootLogin prohibit-password/' /etc/ssh/sshd_config
systemctl reload ssh
systemctl enable --now fail2ban
# journald cap — the 438MB-log lesson, applied globally
mkdir -p /etc/systemd/journald.conf.d
printf '[Journal]\nSystemMaxUse=500M\n' > /etc/systemd/journald.conf.d/statuteproof.conf
systemctl restart systemd-journald
```

## 3. App code + Python env (≈6 min)

```bash
# as root — clean clone of the converged main branch (never rsync a working tree)
git clone https://github.com/kurbanovomar6-prog/StatuteProof-Command-Center.git /srv/regradar-src
git -C /srv/regradar-src checkout main   # converged gate-green build (was: stale pin c1ddb8a)
cp -r /srv/regradar-src/product/regradar/. /srv/regradar/
cd /srv/regradar
python3.12 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt          # ~3-4 min
chown -R regradar:regradar /srv/regradar
```

> Playwright/chromium is only needed for JS-rendered sources. Install later
> if required: `.venv/bin/playwright install chromium --with-deps` (adds ~5
> min; NOT part of the 30-minute path).

## 4. Configuration (≈4 min)

```bash
cd /srv/regradar
cp .env.example .env
.venv/bin/python run.py generate-secret-key   # paste output into .env SECRET_KEY
nano .env    # fill: SECRET_KEY, ENVIRONMENT=production, NEW telegram tokens,
             # email: STATUTEPROOF_EMAIL_PROVIDER=smtp + Zoho app password
             # (precondition 3 — local_outbox is NOT acceptable on prod)
             # backups (§ 9 explains each — set them NOW so § 6 gates the real
             # config, not a half-configured host):
             #   STATUTEPROOF_BACKUP_REMOTE=<rclone remote or scp target>
             #   STATUTEPROOF_BACKUP_AGE_RECIPIENT=age1...   (preferred)
             #   ...or STATUTEPROOF_BACKUP_PASSPHRASE=<alphanumeric>
chown regradar:regradar .env && chmod 600 .env
```

> **Set the backup vars here, not later.** § 6 is the gate that catches a
> missing remote, a missing encryption secret, a secret whose tool is not
> installed, and a passphrase that `.env` sourcing mangles. A var written after
> § 6 is a var the gate never saw. § 9 re-runs the gate for the same reason.

Alert plan gate (added 2026-07-20):

- `STATUTEPROOF_ALERTS_REQUIRE_PLAN` — default `1`: official-source Telegram
  broadcasts go only to founder-activated paid plans + exempt operator
  emails. Set `0` to restore the ungated pilot broadcast.
- `STATUTEPROOF_ALERT_PLAN_EXEMPT_EMAILS` — comma-separated founder/operator
  account emails exempt from the gate.

## 5. Frontend build (≈3 min)

```bash
# Ubuntu 24.04's apt nodejs is 18.x — TOO OLD for our Vite (needs Node 20+;
# apt node fails with "ReferenceError: CustomEvent is not defined").
# Install Node 22 LTS from NodeSource instead:
curl -fsSL https://deb.nodesource.com/setup_22.x | bash -
apt-get install -y nodejs
cd /srv/regradar/web && npm ci && npm run build
# Same-origin deployment: do NOT set VITE_API_URL.
```

## 6. deploy-check gate (≈1 min)

```bash
cd /srv/regradar && sudo -u regradar bash deploy/deploy-check.sh
```

**Do not continue until it prints `DEPLOY-CHECK PASSED`.** Every ✗ names the
exact missing var/file.

> There is no way past the backup gates on a production host.
> `STATUTEPROOF_ALLOW_LOCAL_BACKUP_ONLY=1` and
> `STATUTEPROOF_ALLOW_UNENCRYPTED_BACKUP=1` are development-machine overrides:
> with `ENVIRONMENT=production` (or an install at `/srv/regradar`) deploy-check
> **fails** on either of them and `backup.sh` ignores them. Fix the config —
> § 9 has the two-line form of each value.

## 7. Services (≈3 min)

```bash
cp /srv/regradar/deploy/systemd/statuteproof-*.{service,timer} /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now statuteproof-api statuteproof-scheduler \
    statuteproof-telegram-bot statuteproof-compaction.timer \
    statuteproof-backup.timer statuteproof-heartbeat.timer \
    statuteproof-verify.timer statuteproof-api-health.timer \
    statuteproof-scheduler-watchdog.timer
systemctl status statuteproof-api --no-pager | head -5   # expect: active (running)
curl -s http://127.0.0.1:5001/api/health                  # expect: {"ok": true, ...}

# Prove the timers actually RUN — enabling is the step people skip, and a
# documented control that never fires is worse than a known gap. Re-running
# deploy-check now asserts each timer is BOTH enabled and active; before this
# step it only warns that the units are not installed yet.
bash deploy/deploy-check.sh   # expect: ✓ statuteproof-*.timer enabled and active
```

Notes:
- The API performs **zero** monitoring sweeps — sweeps come only from
  `statuteproof-scheduler` (first full sweep starts immediately and takes
  10–20 min in the background; you do not wait for it).
- Startup logs will print `BASELINE DIVERGENCE` errors for legacy pre-2026-07
  records — expected documented history; new runs realign the derived index.

### 7b. RFC 3161 evidence-chain anchoring (optional — recommended)

Why: upgrades the evidence chain from tamper-evident to externally anchored —
a third-party time-stamping authority signs the chain head, so the anchor can
be verified offline, independently of us. The anchor code
(`app/rfc3161_anchor.py`) is **dormant until enabled**: with `RFC3161_TSA_URL`
unset there is zero behavior change. The dependency (`asn1crypto==1.5.1`) is
already pinned in `requirements.txt`.

```bash
# Enable: add the TSA URL to /srv/regradar/.env (any RFC 3161 TSA works;
# freetsa.org is a free public one), then restart the services.
echo 'RFC3161_TSA_URL=https://freetsa.org/tsr' >> /srv/regradar/.env
systemctl restart statuteproof-api statuteproof-scheduler

# Force an anchor now + verify (run from /srv/regradar):
cd /srv/regradar
sudo -u regradar /srv/regradar/.venv/bin/python -c \
  "import json; from app.rfc3161_anchor import anchor_head_now; print(json.dumps(anchor_head_now(), indent=2))"
# expect: a token dict, and these sidecars to appear:
ls -la /srv/regradar/data/evidence_chain_head.tsr /srv/regradar/data/evidence_chain_head.tsr.json

# Offline check of the token (raw DER, readable by openssl ts):
openssl ts -reply -in /srv/regradar/data/evidence_chain_head.tsr -text | head
```

Notes:
- After enabling, every capture re-anchors the chain head out-of-band
  (`spawn_head_anchor` in `app/source_runs.py`) — no cron needed.
- Optional knobs: `RFC3161_TSA_TIMEOUT_S`, `RFC3161_TSA_CERT_REQ`,
  `RFC3161_TSA_POLICY_OID`.
- All anchor failures are logged and swallowed — anchoring never blocks or
  fails a capture.

## 8. Reverse proxy + TLS (≈4 min)

```bash
apt-get install -y caddy
cp /srv/regradar/deploy/Caddyfile /etc/caddy/Caddyfile
systemctl reload caddy
# Caddy fetches Let's Encrypt certificates automatically (~30-60 s)
curl -sI https://statuteproof.com | head -3          # expect HTTP/2 200
curl -s https://statuteproof.com/api/health          # expect {"ok": true, ...}
```

## 9. Log rotation + backups (≈2 min)

```bash
cp /srv/regradar/deploy/logrotate.d/statuteproof /etc/logrotate.d/statuteproof
logrotate -d /etc/logrotate.d/statuteproof   # dry-run parse check
# Nightly backup runs via statuteproof-backup.timer (enabled in step 7, ~02:30 UTC).
sudo -u regradar bash /srv/regradar/deploy/backup.sh   # first backup now
systemctl list-timers statuteproof-backup.timer --no-pager   # confirm scheduled
```

**Off-box copies (STRONGLY RECOMMENDED — survives droplet loss).** Backups
above are kept only on the droplet, so a lost droplet loses the entire evidence
trail. An off-box remote is the single most important backup setting. Set
`STATUTEPROOF_BACKUP_REMOTE` in `/srv/regradar/.env` (mode 600) to push the
newest archive off-box each run. It stays env-driven (no hardcoded remote), so
the push is a no-op when the var is unset — but `backup.sh` then **warns loudly
on stderr / in the journal every run** that backups are local-only and the
evidence trail is not protected against droplet loss. Point the remote at object
storage (S3/B2 via rclone) or a separate host (scp):

```bash
# rclone remote (preferred; e.g. an S3/B2 bucket) — install rclone + configure it first
echo 'STATUTEPROOF_BACKUP_REMOTE=s3remote:statuteproof-backups' >> /srv/regradar/.env
# ...or an scp target with key-based auth
echo 'STATUTEPROOF_BACKUP_REMOTE=backups@offbox.example:/srv/statuteproof-backups/' >> /srv/regradar/.env
systemctl restart statuteproof-backup.timer   # timer re-reads EnvironmentFile on next run
```

**Encryption is mandatory for anything that leaves the droplet.** The archive
contains `regradar.db`: password hashes, emails, `telegram_chat_id`s, and the
sessions table whose ids are bearer credentials — anyone who reads one archive
can replay live sessions until they expire. `backup.sh` therefore encrypts the
archive before the push and **refuses the push entirely** (loud stderr warning
+ founder page) if it cannot. The local copy in `backups/` stays plaintext by
design: the droplet already holds the live database, so it adds no new
exposure, and retention/restore stay simple.

These are the values § 4 asked you to put in `.env`. Install the tool **before**
writing its secret: a recipient set without `age` on the box is the exact state
`backup.sh` refuses and deploy-check fails on. Use the `echo` lines only if you
left the var blank in § 4.

```bash
# Preferred — age, public-key: generate the key pair OFF the droplet
apt-get install -y age
age-keygen -o statuteproof-backup.key      # on your laptop; KEEP THIS FILE SAFE
# -> prints: Public key: age1....  (only the PUBLIC key goes on the droplet)
echo 'STATUTEPROOF_BACKUP_AGE_RECIPIENT=age1...' >> /srv/regradar/.env

# ...or fallback — gpg symmetric with a generated ALPHANUMERIC passphrase
apt-get install -y gnupg
openssl rand -base64 48 | tr -dc 'A-Za-z0-9' | head -c 40   # store this in the password manager
echo 'STATUTEPROOF_BACKUP_PASSPHRASE=PasteTheAlphanumericValueHere' >> /srv/regradar/.env
```

> **The passphrase must be alphanumeric, and the line must be single-quoted as
> shown.** `.env` is SOURCED by both `backup.sh` and `deploy-check.sh`, so bash
> applies parameter expansion, command substitution and word splitting to every
> value: `a$b` silently becomes `a`, and a space truncates the value. gpg would
> then encrypt with a passphrase nobody stored and every archive would be
> unrecoverable. `deploy/deploy-check.sh` FAILS when the raw `.env` bytes and
> the sourced value differ, or when the passphrase contains `$`, a backtick or
> whitespace.

> **Losing the age identity file or the passphrase means losing every off-box
> archive — there is no recovery path.** Store it in the founder's password
> manager, never on the droplet, and test a restore (§ Restore from backup)
> before you rely on it.

Since 2026-07-20 the missing remote is enforced, not just warned about:
`deploy/deploy-check.sh` (§ 6) **FAILS** when `STATUTEPROOF_BACKUP_REMOTE` is
unset. `STATUTEPROOF_ALLOW_LOCAL_BACKUP_ONLY=1` is a dev-only override — never
set it on prod. The same gate covers encryption: deploy-check **FAILS** when
`STATUTEPROOF_BACKUP_REMOTE` is set but neither
`STATUTEPROOF_BACKUP_AGE_RECIPIENT` nor `STATUTEPROOF_BACKUP_PASSPHRASE` is —
**and equally when the secret is set but its tool (`age` / `gpg`) is not
installed**, because `backup.sh` requires both and refuses the push otherwise;
do not skip the `apt-get install` line above.
`STATUTEPROOF_ALLOW_UNENCRYPTED_BACKUP=1` is the dev-machine override there, and
off production it makes `backup.sh` push in the clear. **Both overrides are
refused on a production host** (`ENVIRONMENT=production`/`prod`,
`STATUTEPROOF_ENV`, or an install at `/srv/regradar`): deploy-check FAILS on
either, and `backup.sh` ignores and reports them rather than pushing plaintext
or skipping the off-box copy. In addition, `backup.sh` pages the founder via
the admin Telegram bot (same channel as the heartbeat/integrity watchdogs)
whenever the off-box push fails, is refused for lack of working encryption, or
is skipped.

**Close the loop — re-run the gate against the finished `.env`.** § 6 ran
before the encryption tooling existed, so run it again here; a gate that never
saw the final config is not a gate. Then prove the encrypt-and-push path once,
at deploy time, instead of learning it was broken at 02:30 UTC:

```bash
cd /srv/regradar && sudo -u regradar bash deploy/deploy-check.sh
sudo -u regradar bash /srv/regradar/deploy/backup.sh
```

Expect `DEPLOY-CHECK PASSED`, then an `encrypted for off-box push (age|gpg): …`
line followed by `off-box copy (rclone|scp): …`. Anything else — `REFUSED`, a
founder page, a push warning — is a live backup fault; fix it before you treat
this deploy as done.

## Scheduler watchdog — the one control that RESTARTS

`statuteproof-heartbeat.timer` only ever *notified*: it pages the founder about a
wedged loop and then does nothing. Monitoring was silently dead for four days in
exactly that state — the process was alive, so `Restart=on-failure` never fired,
and the page arrived to a founder who was asleep.

`statuteproof-scheduler-watchdog.timer` (every 10 min) is the control that acts.
It asks the app for the heartbeat state, and when the loop is provably wedged —
stale heartbeat AND a progress marker that has stopped moving — it restarts
`statuteproof-scheduler.service` within a backoff budget, then pages.

It runs as root because restarting a unit needs privilege; it touches the app's
Python only to READ state and to send the page, never to write monitoring data.
Exit 1 means "wedge found, remediation issued" and is treated as success so the
timer keeps ticking.

Verify after step 7:

```bash
systemctl list-timers statuteproof-scheduler-watchdog.timer --no-pager
systemctl start statuteproof-scheduler-watchdog.service   # safe: no-ops when healthy
journalctl -u statuteproof-scheduler-watchdog --no-pager -n 20
```

A run on a healthy box logs the heartbeat state and exits 0 without restarting
anything. If it logs `heartbeat query produced no output`, the app and the script
disagree about the sensor contract and the watchdog is inert — that exact failure
is covered by `tools/measure_reliability_axis.py`.

## External uptime probe (2-minute step, free tier)

The on-droplet deadman (`statuteproof-heartbeat.timer`) cannot page anyone if
the droplet itself dies — the watchdog dies with it. Close that gap with an
owner-created external heartbeat service (StatuteProof only sends the ping):

1. Create a free check at [healthchecks.io](https://healthchecks.io) (or an
   UptimeRobot heartbeat monitor).
2. Set the check's period/grace to **at least 40 min** — the heartbeat timer
   pings every 30 min, so anything tighter false-alarms.
3. Copy the check's ping URL into `/srv/regradar/.env`:

   ```bash
   echo 'STATUTEPROOF_HEARTBEAT_PING_URL=<ping url>' >> /srv/regradar/.env
   ```

No restart needed — the heartbeat oneshot re-reads `.env` each run. From then
on, `run.py heartbeat-check` GETs the URL after each SUCCESSFUL internal check
(and deliberately stays silent on a stale/missing heartbeat), so the external
service alerts the owner when pings stop arriving.

**Total: ≈30 min.**

## 10. Plan re-activation for paying customers — REQUIRED after this deploy

The paid-export entitlement gate is **fail-closed**: a user only gets paid
capabilities (audit/PDF export, source limits) when a founder has *activated*
their plan via the CLI. `activated_plan` is what the gate reads — the
self-selected `plan_name` grants nothing on its own. There is **no automatic
backfill**: any customer who was activated before this change drops to free-tier
caps on deploy until `activate-plan` is re-run for them.

You cannot infer who was previously activated, so list the current intent-vs-
activated state and re-activate every genuinely paying customer **and the founder
account**:

```bash
# See who self-selected a paid plan but is NOT yet activated (NEEDS ACT. = YES):
cd /srv/regradar && sudo -u regradar python3 run.py activate-plan --list

# Re-activate each real paying customer (and your own founder account).
# The --list output prints the exact command per user needing activation, e.g.:
sudo -u regradar python3 run.py activate-plan --user <id> --plan <plan_name>

# Confirm the flip: re-run --list; NEEDS ACT. should now read "-" for those users.
sudo -u regradar python3 run.py activate-plan --list
```

Only activate accounts you have independently confirmed are paying — a
self-selected paid `plan_name` is an intent, not proof of payment.

## Stripe payment links — owner-only step (optional until billing launch)

1. Stripe Dashboard → Payment Links → create two links: Founding Pilot
   ($199/mo) and UAE Monitor ($399/mo).
2. Paste the `https://buy.stripe.com/...` URLs into
   `web/src/data/constants.js` → `STRIPE_LINK_FOUNDING_PILOT` /
   `STRIPE_LINK_UAE_MONITOR`.
3. Rebuild the frontend (step 5) and redeploy.
4. Empty strings keep the current fallback: the pricing CTA routes to
   registration + plan-intent, which pages the founder via the admin bot.
5. Payment Links are public checkout URLs — no Stripe secret key ever goes
   into the repo or `.env` for this flow.
6. After a customer pays, the `/api/stripe/webhook` endpoint auto-activates the
   plan (and auto-downgrades on cancel/refund) once `STRIPE_WEBHOOK_SECRET` and
   `STRIPE_PRICE_TO_PLAN` are set — see the go-live checklist. The manual
   `run.py activate-plan` (§10) and the admin panel remain available as overrides.

## First-hour smoke-test checklist

1. `https://statuteproof.com` loads; login page renders; no console errors
2. `https://statuteproof.com/api/health` → `{"ok": true, ...}`
3. Register a test account → verification payload appears in
   `/srv/regradar/data/outbox/` (or real inbox if a provider is enabled) →
   verify → login works
4. `journalctl -u statuteproof-scheduler -n 50` shows sources being checked;
   after the first sweep `data/source_runs/source_runs.jsonl` grows with
   heartbeat + changed records carrying `normalized_hash`
5. `journalctl -u statuteproof-api -n 50` shows **no** fetch/pipeline lines
6. Telegram: send `/start` to @statuteproofalerts_bot → reply arrives
   (NEW token only)
7. `systemctl restart statuteproof-api` → health returns 200 within 10 s
8. Reboot the droplet once: all three services + the timers come back
   (`systemctl list-timers | grep statuteproof` — expect compaction + backup +
   heartbeat + verify + api-health)
9. Email dry-run (if a provider is configured):
   set `STATUTEPROOF_EMAIL_DRY_RUN=true`, restart api, trigger a test brief
   → `data/email_outbox/delivery_status.jsonl` gains a `dry_run` row → set
   back to false
10. `ufw status` shows only 22/80/443; `ssh` password login refused

## Restore from backup

If the droplet was lost, first pull the newest archive back from the off-box
remote (`STATUTEPROOF_BACKUP_REMOTE`) into `/srv/regradar/backups/` — e.g.
`rclone copy <remote> /srv/regradar/backups/`.

**Off-box archives are encrypted** (§ 9), so decrypt before extracting. Use
whichever suffix the archive carries; the key material lives with the founder,
never on the droplet:

```bash
cd /srv/regradar/backups
# age (.tar.gz.age) — needs the PRIVATE identity file kept off-box
age --decrypt -i statuteproof-backup.key \
    -o statuteproof-backup-<STAMP>.tar.gz \
       statuteproof-backup-<STAMP>.tar.gz.age
# ...or gpg (.tar.gz.gpg) — prompts for STATUTEPROOF_BACKUP_PASSPHRASE
gpg --decrypt -o statuteproof-backup-<STAMP>.tar.gz \
       statuteproof-backup-<STAMP>.tar.gz.gpg
# Sanity check before you rely on it:
tar -tzf statuteproof-backup-<STAMP>.tar.gz | head   # expect regradar.db, data/, evidence/
```

An archive nobody can decrypt is worse than no archive, so **test a restore**
on a throwaway box after every key rotation and at least quarterly: decrypt,
extract, and confirm `tar -tzf` lists `regradar.db`. A restore drill box must
not carry the production `STATUTEPROOF_HEARTBEAT_PING_URL`.

**What the archive holds — and what it does not.** `deploy/backup.sh` tars
exactly five paths: `regradar.db`, `data/` (minus `data/outbox`), `evidence/`,
`sources.json` and `.env.example`. Every one of them is restored below;
`evidence/` is a *sibling* of `data/`, so the `data/` rsync does not cover it,
and restoring the database without the sealed evidence tree is precisely the
BASELINE DIVERGENCE state the last line warns about.

**Not in the archive** — these must be reconstructed by hand from §§ 1-9:
`.env` (secrets: `SECRET_KEY`, telegram tokens, SMTP, backup keys — only
`.env.example` is archived, deliberately), the Python venv (`.venv/`), the
built frontend (`web/dist/`), the systemd units and Caddyfile under `/etc`,
`logs/`, and `data/outbox` (excluded on purpose — a queued outbox replayed
after a restore re-sends old mail).

Then restore locally (a local `backups/` archive is already plaintext — skip
straight here):

```bash
systemctl stop statuteproof-api statuteproof-scheduler statuteproof-telegram-bot
cd /srv/regradar
mkdir -p /tmp/restore
tar -xzf backups/statuteproof-backup-<STAMP>.tar.gz -C /tmp/restore
rsync -a /tmp/restore/data/ data/
[ -d /tmp/restore/evidence ] && rsync -a /tmp/restore/evidence/ evidence/   # absent only before the first seal
cp /tmp/restore/sources.json sources.json
cp /tmp/restore/regradar.db "$(.venv/bin/python -c 'import sys; sys.path.insert(0,"."); from app.config import DB_PATH; print(DB_PATH)')"
chown -R regradar:regradar /srv/regradar
# Re-verify the sealed trail BEFORE anything starts writing to it: this
# re-hashes every snapshot against its stored evidence hash and re-checks the
# tamper-evident chain. A clean run here is what makes the restored evidence
# tree usable as proof; a divergence means the archive and the DB disagree.
sudo -u regradar .venv/bin/python run.py verify-trail
systemctl start statuteproof-api statuteproof-scheduler statuteproof-telegram-bot
# Verify: /api/health 200, then check startup logs — BASELINE DIVERGENCE
# beyond the known legacy set means trail/index mismatch from the restore.
```

## Operational notes

- **Evidence retention**: `statuteproof-compaction.timer` runs daily; job is
  idempotent. Manual run: `run.py compact-heartbeats --days 30`.
- **Evidence backups**: `statuteproof-backup.timer` runs daily (~02:30 UTC);
  keeps the newest 14 archives in `backups/`. Manual run:
  `bash deploy/backup.sh`. Set `STATUTEPROOF_BACKUP_REMOTE` in `.env` to also
  push each archive off-box (see § 9, strongly recommended); unset means on-box
  copies only and the script warns loudly on every run. Off-box copies are
  always encrypted (age or gpg, § 9) — without a working encryption secret the
  push is refused, not downgraded to plaintext.
- **Evidence integrity self-check**: `statuteproof-verify.timer` runs daily
  (~04:20 UTC, after backup + compaction). It re-hashes every snapshot against
  its stored evidence hash and re-verifies the tamper-evident chain
  (read-only); on any divergence it pages the founder via the admin Telegram
  bot (best-effort) and the oneshot exits non-zero. Manual run:
  `run.py verify-trail-watch` (silent + exit 0 when clean). Confirm scheduled:
  `systemctl list-timers statuteproof-verify.timer --no-pager`.
- **API liveness watchdog**: `statuteproof-api-health.timer` runs every 2 min
  and probes `http://127.0.0.1:5001/api/health`. `statuteproof-api.service` is
  `Restart=on-failure`, which recovers a CRASH but not an alive-but-wedged API
  (SQLite writer-lock stall, `TasksMax` thread exhaustion) where
  `serve_forever()` stays up while every request blocks and Caddy returns 502.
  On a non-200 / no-response, the watchdog restarts `statuteproof-api.service`
  and pages the founder via the admin Telegram bot (same channel as the
  heartbeat/integrity watchdogs). It runs as **root** because restarting the
  API unit needs privilege. Manual run: `bash deploy/api-health-check.sh`
  (exit 0 = healthy, exit 1 = restart+page issued). Confirm scheduled:
  `systemctl list-timers statuteproof-api-health.timer --no-pager`.
- **Scheduler cadence**: change `--interval` in
  `statuteproof-scheduler.service`, then `systemctl daemon-reload && restart`.
- **Never** run two schedulers against the same data dir.
- **Secrets rotation**: tokens live only in `/srv/regradar/.env` (mode 600).
  After rotating, `systemctl restart` the affected service.
