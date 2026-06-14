# Actual Hosting Location Audit

Date: 2026-06-12
Scope: `/Users/kurbnovomar/StatuteProof-Command-Center`, `/Users/kurbnovomar/документы/obsidian/`, `/Users/kurbnovomar/`, shell history, deployment docs and configs.
Safety: no `.env` contents, API keys, tokens, passwords, SSH private keys, Telegram IDs, or customer data were printed.

## 1. Most Likely Live Host

`statuteproof.com` is most likely hosted on a **DigitalOcean VPS in Frankfurt, Germany**, reachable at:

- IP: `207.154.250.157`
- ASN/org: `AS14061 DigitalOcean, LLC`
- Public server: `nginx/1.24.0 (Ubuntu)`
- Backend health endpoint: `https://statuteproof.com/api/health`

Classification: **VPS**, not Railway, Vercel, Render, Netlify, or Fly.io.

Confidence: **High**.

## 2. Evidence Found

### Live HTTP Evidence

Safe public checks showed:

```text
curl https://statuteproof.com/api/health
-> HTTP/1.1 200 OK
-> Server: nginx/1.24.0 (Ubuntu)
-> Body: {"status": "ok", "service": "StatuteProof API"}
```

```text
curl https://statuteproof.com/
-> HTTP/1.1 200 OK
-> Server: nginx/1.24.0 (Ubuntu)
-> Content-Type: text/html
```

```text
curl remote IP metadata
-> remote_ip=207.154.250.157
-> http_code=200
```

Public IP ownership lookup:

```text
207.154.250.157
AS14061 DigitalOcean, LLC
Frankfurt am Main, Hesse, DE
```

### Shell History Evidence

`/Users/kurbnovomar/.zsh_history` contains commands that match the live IP and VPS deployment model:

```text
ssh-keygen -t ed25519 -C "statuteproof"
cat ~/.ssh/id_ed25519.pub
ssh root@207.154.250.157
systemctl restart regradar-api
systemctl reload nginx
curl http://127.0.0.1:5001/api/health
curl https://statuteproof.com/api/health
```

This is the strongest local evidence that `statuteproof.com` was deployed manually to a VPS at `207.154.250.157`, with systemd service `regradar-api`, nginx reverse proxy, and backend on local port `5001`.

### Deployment Docs Evidence

`product/regradar/docs/vps_deployment_runbook.md` describes the exact architecture observed live:

- nginx serves `web/dist/`
- nginx proxies `/api/*` to `http://127.0.0.1:5001`
- Python API starts with `run.py api`
- repo path is `/srv/regradar`
- systemd service is `regradar-api`
- SSL via certbot/nginx

`product/regradar/docs/production_deployment_checklist.md` repeats the same intended production path:

- VPS selected: Hetzner or DigitalOcean Basic recommended
- clone repo to `/srv/regradar`
- create `/etc/systemd/system/regradar-api.service`
- nginx config at `/etc/nginx/sites-available/regradar`
- `curl http://127.0.0.1:5001/api/health`
- `curl https://your-domain.com/api/health`

`product/regradar/docs/deployment_architecture.md` explicitly says static-only hosting is not enough and recommends VPS + nginx.

## 3. Files / Commands That Prove It

Local files:

- `product/regradar/docs/vps_deployment_runbook.md`
- `product/regradar/docs/production_deployment_checklist.md`
- `product/regradar/docs/deployment_architecture.md`
- `product/regradar/app/api.py`
- `product/regradar/run.py`
- `product/regradar/web/index.html`
- `product/regradar/deploy/systemd/statuteproof-cbuae-rulebook-watch.service`

Commands run safely during audit:

```bash
curl -sS --connect-timeout 10 -D - https://statuteproof.com/api/health
curl -sS --connect-timeout 10 -I https://statuteproof.com/
curl -sS --connect-timeout 10 -o /dev/null -w 'remote_ip=%{remote_ip}\nhttp_code=%{http_code}\n' https://statuteproof.com/api/health
curl -sS --connect-timeout 10 https://ipinfo.io/207.154.250.157/org
```

Observed results:

- `https://statuteproof.com/api/health` returns `200` and `{"status":"ok","service":"StatuteProof API"}`.
- `https://statuteproof.com/` returns `200` and `Server: nginx/1.24.0 (Ubuntu)`.
- curl reports `remote_ip=207.154.250.157`.
- ipinfo reports `AS14061 DigitalOcean, LLC`.

## 4. Platform Classification

| Platform | Evidence | Verdict |
|---|---|---|
| Railway | `railway.toml` files exist, and shell history has `railway login`; no live Railway host evidence for `statuteproof.com` | Unlikely live host |
| Vercel | no `vercel.json`; live server is nginx/Ubuntu, not Vercel headers | No |
| Render | no `render.yaml`; live server is nginx/Ubuntu | No |
| Netlify | no project Netlify config for StatuteProof; live server is nginx/Ubuntu | No |
| Fly.io | no `fly.toml`; live server is nginx/Ubuntu | No |
| VPS | shell history, nginx, systemd, `/srv/regradar`, backend on `127.0.0.1:5001`, DigitalOcean IP | Yes |
| DigitalOcean | live IP ASN is `AS14061 DigitalOcean, LLC` | Yes |

## 5. What Is Still Unknown

- Which DigitalOcean account owns the droplet.
- Whether `207.154.250.157` is the only production server.
- Whether DNS has only an A record or also CNAME/AAAA records.
- Exact nginx virtual host config currently installed on the server.
- Exact certbot certificate status and renewal timer on the server.
- Which git commit is deployed under `/srv/regradar`.
- Whether production `.env` has contact delivery enabled and correct values.
- Whether data backups exist for `/srv/regradar/data` and `regradar.db`.

## 6. What To Check Manually In Accounts / DNS

1. Domain registrar / DNS provider:
   - Confirm `A` record for `statuteproof.com` points to `207.154.250.157`.
   - Check whether `www.statuteproof.com` exists and where it points.
   - Check for old CNAMEs to Railway/Vercel/Netlify/Render.

2. DigitalOcean account:
   - Find droplet with public IP `207.154.250.157`.
   - Confirm region is Frankfurt.
   - Confirm backups/snapshots are enabled or intentionally disabled.
   - Confirm firewall allows only SSH, HTTP, HTTPS.

3. Server over SSH:
   - Confirm `/etc/nginx/sites-enabled/regradar`.
   - Confirm `systemctl status regradar-api nginx`.
   - Confirm `/srv/regradar` git remote and current commit.
   - Confirm certbot certificate for `statuteproof.com` and auto-renewal.
   - Confirm `.env` variable presence without printing values.

4. Railway account:
   - Check whether any old RegRadar/StatuteProof project is still active.
   - If active, confirm it is not receiving traffic for `statuteproof.com`.

## 7. Safe Next Command To Confirm Without Exposing Secrets

Run this from local machine:

```bash
curl -sS --connect-timeout 10 -D - https://statuteproof.com/api/health
curl -sS --connect-timeout 10 -o /dev/null -w 'remote_ip=%{remote_ip}\nhttp_code=%{http_code}\n' https://statuteproof.com/api/health
```

Run this only if SSH access is expected and you want server-side confirmation without printing secrets:

```bash
ssh root@207.154.250.157 'hostname; systemctl is-active regradar-api nginx; nginx -T 2>/dev/null | grep -E "server_name|root /srv/regradar|proxy_pass http://127.0.0.1:5001"; cd /srv/regradar && git remote -v && git rev-parse --short HEAD; test -f /srv/regradar/.env && echo env_present || echo env_missing'
```

Do not run `cat /srv/regradar/.env` or print environment variables.
