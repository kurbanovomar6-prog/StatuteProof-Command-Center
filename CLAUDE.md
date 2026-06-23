# StatuteProof Command Center — Claude Code Instructions

## Workspace Scope

This workspace is **only** for StatuteProof: official-source regulatory monitoring with evidence-backed compliance briefs.

Do not use this workspace for: Polymarket, Excel orders, YouTube pipelines, Ruflo, random automation, or any non-StatuteProof project.

## Priority Order

When given any StatuteProof task, prioritize in this sequence:

1. Official source monitoring (get real evidence first)
2. Evidence trail (store and verify before proceeding)
3. Risk brief (score and draft after evidence is complete)
4. Legal-safe wording (check every customer-facing sentence)
5. QA review (check before delivery)
6. Outreach (only after evidence exists and QA passes)

## Correct Positioning

> "Official-source regulatory monitoring with evidence-backed compliance briefs."

StatuteProof monitors selected public official sources, detects text changes, stores cryptographic evidence records, and drafts monitoring briefs for human review.

## Forbidden Claims (Never Write These)

- AI lawyer
- guarantee compliance
- prevent fines
- replace lawyers
- automatic legal advice
- official partner of [any regulator]
- certified by [any regulator]
- 100% accurate
- never miss an update
- stay compliant automatically
- we handle compliance for you
- automated compliance decisions
- avoid all penalties

See `docs/forbidden-phrases-reference.md` for the full table with approved replacements.

## Standard Disclaimer

All StatuteProof briefs and outreach must include one of:

**Full (briefs):** StatuteProof reports are generated from monitored official-source records and are provided for information and compliance review support only. StatuteProof reports do not constitute legal advice, regulatory advice, compliance certification, or a legal opinion. StatuteProof does not replace qualified legal counsel, compliance professionals, MLROs, or other professional advisers. StatuteProof does not guarantee compliance, prevent fines, or certify that all regulatory updates have been captured. Source monitoring may be affected by publication delays, website changes, PDF formatting, access limits, or source structure changes. Users should verify official source material directly and review evidence records, hashes, timestamps, and diffs before relying on a report. Users should consult qualified legal or compliance professionals before making regulatory, filing, operational, or customer decisions based on a report.

**Short (outreach):** For monitoring information only. Not legal advice and not a guarantee of compliance.

## Tool Router

See `TOOL_ROUTER.md` for which agent or skill to use for each task type.

## Agent Rules

- Agents in `.claude/agents/` are the authoritative role definitions.
- Agents in `agents/` are the human-readable system prompt docs.
- Chief of Staff is the routing coordinator — do not bypass it for multi-agent tasks.

## SAMPLE / FAKE Label Rule

Any example brief, example evidence record, or example output that uses invented regulatory content **must** be labeled `SAMPLE / FAKE` near the top. This is a legal safety requirement.

## Evidence-First Rule

No brief is drafted before evidence_record_status is complete. No score is assigned without a diff excerpt. No customer delivery without human review when risk >= 70 or confidence < 0.70.

## Skills

Ten skills are available in `skills/`. Invoke by typing the trigger in Claude Code:

| Skill | Trigger | Purpose |
|-------|---------|---------|
| `evidence-audit` | `#evidence-audit` | Verify evidence record completeness |
| `risk-brief-review` | `#risk-brief-review` | Brief SHIP / NO-SHIP gate |
| `weekly-founder-plan` | `#weekly-founder-plan` | Weekly planning |
| `marketing-outreach-review` | `#marketing-outreach-review` | Outreach ICP fit + legal safety |
| `anti-slop-writing-review` | `#anti-slop-writing-review` | Catch AI writing patterns in prose |
| `ui-ux-review` | `#ui-ux-review` | UX + trust review of landing page or dashboard |
| `design-polish` | `#design-polish` | Component-level design + animation polish |
| `design-taste-review` | `#design-taste-review` | Taste check, AI slop detection, product credibility |
| `landing-page-conversion-review` | `#landing-page-conversion-review` | Conversion review for the landing page |
| `agent-council-review` | `#agent-council-review` | 7-stage written review for high-stakes decisions |

## Agent Council (Document Workflow Only)

For high-stakes decisions, run `workflows/07-agent-council-review.md`. This is a sequential written review where each agent role challenges the decision in writing before the Chief of Staff gives a final verdict.

Run it for: first real customer delivery, new source activation, pricing or positioning changes, any irreversible action.

Do not run it for: routine brief drafts, source spec updates, internal planning.

See `docs/agent-council-decision-system.md` for the full decision framework.

## Ruflo

Ruflo (`https://github.com/ruvnet/ruflo`) — разрешено изучать, скачивать и использовать агентов.

## Telegram Architecture (два бота — не путать)

Система использует **два отдельных бота**. Не смешивать токены.

### Бот 1 — Админ / Founder only
- **Username:** `@StatuteProof_bot`
- **Env var:** `TELEGRAM_BOT_TOKEN`
- **Chat ID:** `TELEGRAM_CHAT_ID` (ID чата основателя)
- **Назначение:** только уведомления с контактной формы сайта → идут основателю
- **Код:** `_handle_contact()` в `app/api.py` — использует эти переменные напрямую
- **Никогда не показывать этот токен и Chat ID покупателям**

### Бот 2 — Customer alerts bot (публичный)
- **Username:** `@statuteproofalerts_bot`
- **Env var:** `TELEGRAM_ALERTS_BOT_TOKEN`
- **Назначение:** привязка аккаунтов покупателей + отправка регуляторных алертов
- **Код:** `telegram_settings.get_token()` возвращает этот токен первым; `telegram_onboarding.py` — листенер для `/start CODE`
- **Показывается на сайте**, публичный

### Как работает привязка покупателя
1. Покупатель открывает дашборд → Integrations → "Connect Telegram" → получает код `SP-XXXXXX`
2. Отправляет `/start SP-XXXXXX` боту `@statuteproofalerts_bot`
3. Бот автоматически захватывает `chat_id` из Telegram update
4. `consume_pairing_code()` в `telegram_pairing.py` сохраняет `chat_id` в SQLite
5. Покупатель **никогда не вводит Chat ID вручную** — это происходит невидимо

### Что показывает бот в ответе на /start
- Только инструкции по коду — Chat ID **не показывается** (убрано 2026-06-21)
- `/id` — единственная команда, которая показывает chat_id (явная команда, для отладки)

### Переменные в .env
```
TELEGRAM_BOT_TOKEN=<admin bot token>          # @StatuteProof_bot
TELEGRAM_CHAT_ID=<founder chat id>            # куда идут контакты
TELEGRAM_BOT_USERNAME=StatuteProof_bot

TELEGRAM_ALERTS_BOT_TOKEN=<alerts bot token>  # @statuteproofalerts_bot
TELEGRAM_ALERTS_BOT_USERNAME=statuteproofalerts_bot
```

### Запуск листенера
```bash
PYTHONUNBUFFERED=1 nohup python3 -u run.py telegram-listen > logs/telegram_bot.log 2>&1 &
echo $! > logs/telegram_bot.pid
```
Или: `./run_telegram_bot.sh`

Конфликт (несколько экземпляров): `pkill -f "run.py telegram-listen"` перед перезапуском.

## Product Code Location

The actual StatuteProof product code (Python pipeline, frontend, deployment config) is in:

```
product/
```

When doing implementation work:
- Inspect `product/regradar/app/` for the relevant module before writing anything
- Use the Source Monitor Agent for monitoring code and source configurations
- Use the Evidence Trail Agent for evidence files and run records
- Use the Risk + Brief Pipeline Agent for brief generation and risk scoring logic
- Use the Legal Language Agent and QA / Critic for any customer-facing text
- Do not edit Command Center docs (agents/, skills/, workflows/, docs/) unless asked

See `docs/product-integration.md` for the full agent-to-code mapping and Week 1 path.

## File Organization

- Product code: `product/` (the actual running application)
- Agents: `.claude/agents/` (Claude Code subagents) and `agents/` (docs)
- Skills: `.claude/skills/` (Claude Code skills) and `skills/` (docs)
- Docs: `docs/`
- Prompts: `prompts/`
- Workflows: `workflows/`
- Examples: `examples/`
- Checklists: `checklists/`
- Tools: `tools/`
- References: `references/` (third-party repo notes — read-only, no runtime deps)
