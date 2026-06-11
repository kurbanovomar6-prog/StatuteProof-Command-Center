"""Settings page — schedule info, AI scraping console, AI smart alerts."""
from nicegui import APIRouter, app, ui

from config import settings
from src import sidebar

router = APIRouter()


# ── AI Scraping Console ───────────────────────────────────────────────────────

def _ai_console() -> None:
    with ui.card().classes("rr-ai-card p-5 w-full mt-4"):
        with ui.row().classes("rr-card-hdr items-center gap-2"):
            ui.icon("rocket_launch", size="20px").style("color:#818cf8")
            ui.label("Universal AI-Driven Monitoring").classes("text-sm font-bold").style("color:#e0e7ff")
            with ui.badge("NEW").props("color=deep-purple").classes("text-xs ml-1"):
                pass

        ui.label(
            "Point at any regulatory URL — the LLM discovers НПА semantically. "
            "No CSS selectors. No XPath. Just intelligence."
        ).classes("text-xs mb-4").style("color:#4b5563; line-height:1.5")

        ai_url = ui.input(
            label="Target URL", placeholder="https://cbr.ru/press/pr/",
        ).classes("w-full").props("outlined dense dark")

        with ui.row().classes("items-end gap-3 mt-3"):
            ai_pages = ui.number(
                label="Max Pages", value=3, min=1, max=20, step=1, format="%.0f",
            ).classes("w-28").props("outlined dense dark")
            ai_jur = ui.select(
                options={"": "Auto-detect", "RU": "🇷🇺 Russia", "KZ": "🇰🇿 Kazakhstan",
                         "AZ": "🇦🇿 Azerbaijan", "BY": "🇧🇾 Belarus", "UZ": "🇺🇿 Uzbekistan"},
                value="", label="Jurisdiction",
            ).classes("w-44").props("outlined dense dark")

        status_row = ui.row().classes("items-center gap-2 mt-3")
        status_row.set_visibility(False)
        with status_row:
            ui.spinner("dots", size="sm").style("color:#818cf8")
            status_lbl = ui.label("Dispatching…").classes("text-xs font-semibold rr-task-badge")

        def _launch():
            url = (ai_url.value or "").strip()
            if not url.startswith(("http://", "https://")):
                ui.notify("Enter a valid URL starting with http:// or https://", type="warning", position="top", timeout=3000)
                return
            launch_btn.disable()
            status_row.set_visibility(True)
            status_lbl.set_text("Dispatching to Celery queue…")
            try:
                from celery_app import universal_scrape_url_task
                task = universal_scrape_url_task.apply_async(
                    kwargs={"url": url, "jurisdiction": ai_jur.value or "", "max_pages": int(ai_pages.value or 3)},
                    queue="scraping",
                )
                status_lbl.set_text(f"Processing  ·  task {task.id[:8]}…")
                ui.notify(f"🚀  AI Scraping Agent dispatched\n{url[:60]}", type="positive",
                          position="top-right", timeout=5000, close_button=True)
            except Exception as exc:
                status_row.set_visibility(False)
                ui.notify(f"Dispatch failed: {str(exc)[:90]}", type="negative", position="top", timeout=5000)
            finally:
                launch_btn.enable()

        launch_btn = (
            ui.button("🚀  Launch AI Scraping Agent", on_click=_launch)
            .classes("rr-ai-launch mt-4")
            .props("no-caps no-shadow")
        )


# ── AI Smart Alerts ───────────────────────────────────────────────────────────

def _smart_alerts() -> None:
    with ui.card().classes("rr-alert-card p-5 w-full mt-4"):
        with ui.row().classes("rr-card-hdr items-center gap-2"):
            ui.icon("notifications_active", size="20px").style("color:#60a5fa")
            ui.label("AI Smart Alerts").classes("text-sm font-bold").style("color:#e0e7ff")
            ui.html(
                '<span style="background:rgba(29,78,216,.15);color:#60a5fa;'
                'font-size:10px;font-weight:700;padding:2px 8px;border-radius:10px;'
                'letter-spacing:.06em;border:1px solid rgba(29,78,216,.4)">TELEGRAM</span>'
            )

        ui.label(
            "Subscribe to personalised regulatory alerts filtered by jurisdiction "
            "and risk level. Delivered directly to your Telegram chat."
        ).classes("text-xs mb-4").style("color:#4b5563; line-height:1.5")

        _jurs: set[str]   = set()
        _jur_btns: dict   = {}
        _freq             = {"v": "daily"}
        _freq_btns: dict  = {}
        _JUR_OPTS = [("", "🌐 GLOBAL"), ("RU", "🇷🇺 RU"), ("KZ", "🇰🇿 KZ"),
                     ("AZ", "🇦🇿 AZ"),  ("BY", "🇧🇾 BY"), ("UZ", "🇺🇿 UZ")]

        def _toggle_jur(jc: str):
            if jc in _jurs:
                _jurs.discard(jc)
                _jur_btns[jc].classes(add="rr-jur-inactive", remove="rr-jur-active")
            else:
                _jurs.add(jc)
                _jur_btns[jc].classes(add="rr-jur-active", remove="rr-jur-inactive")

        def _set_freq(fc: str):
            _freq["v"] = fc
            for k, b in _freq_btns.items():
                if k == fc:
                    b.classes(add="rr-freq-btn-active", remove="rr-freq-btn-inactive")
                else:
                    b.classes(add="rr-freq-btn-inactive", remove="rr-freq-btn-active")

        # Telegram Chat ID
        ui.label("TELEGRAM CHAT ID").classes("text-xs font-bold mb-1").style("color:#334155; letter-spacing:.1em")
        with ui.row().classes("items-end gap-3 w-full"):
            chat_id_inp = ui.input(placeholder="-1001234567890").classes("flex-1").props("outlined dense dark").style("min-width:140px")

            def _test_conn():
                cid = (chat_id_inp.value or "").strip()
                if not cid:
                    ui.notify("Enter a Telegram Chat ID first", type="warning", position="top")
                    return
                try:
                    int(cid)
                    ui.notify(f"✓ Format valid — ID {cid}\nEnsure the bot is admin in the chat.",
                              type="positive", position="top-right", timeout=5000)
                except ValueError:
                    ui.notify("Chat ID must be numeric (e.g. -1001234567890 for groups)", type="warning", position="top")

            ui.button("Test Connection", on_click=_test_conn).props("outline no-caps dense").style(
                "color:#60a5fa; border-color:#1e3a5f; font-size:12px; height:40px; white-space:nowrap"
            )

        # Jurisdictions
        ui.label("JURISDICTIONS").classes("text-xs font-bold mt-4 mb-2").style("color:#334155; letter-spacing:.1em")
        with ui.row().classes("gap-2 flex-wrap"):
            for _jc, _jlbl in _JUR_OPTS:
                _jbtn = (
                    ui.button(_jlbl, on_click=lambda jc=_jc: _toggle_jur(jc))
                    .classes("rr-jur-chip rr-jur-inactive")
                    .props("flat no-caps no-shadow")
                )
                _jur_btns[_jc] = _jbtn

        # Frequency
        ui.label("DELIVERY FREQUENCY").classes("text-xs font-bold mt-4 mb-2").style("color:#334155; letter-spacing:.1em")
        with ui.row().classes("gap-2 flex-wrap"):
            for _fc, _flbl in [("daily", "📅 Daily Digest — 09:00 UTC"), ("instant", "⚡ Instant (on detection)")]:
                _fbtn = (
                    ui.button(_flbl, on_click=lambda fc=_fc: _set_freq(fc))
                    .classes("rr-freq-btn " + ("rr-freq-btn-active" if _fc == "daily" else "rr-freq-btn-inactive"))
                    .props("flat no-caps no-shadow")
                )
                _freq_btns[_fc] = _fbtn

        # Min risk
        ui.label("MINIMUM RISK THRESHOLD").classes("text-xs font-bold mt-4 mb-2").style("color:#334155; letter-spacing:.1em")
        risk_sel = ui.select(
            options={"LOW": "🟢 Low and above", "MEDIUM": "🟡 Medium and above",
                     "HIGH": "🟠 High and above", "CRITICAL": "🔴 Critical only"},
            value="LOW",
        ).classes("w-56").props("outlined dense dark")

        ui.separator().classes("my-4").style("background:#0d1424")

        with ui.row().classes("items-center justify-between w-full"):
            save_status = ui.label("").classes("text-xs").style("color:#475569")

            def _save():
                cid = (chat_id_inp.value or "").strip()
                if not cid:
                    ui.notify("Telegram Chat ID is required", type="warning", position="top")
                    return
                try:
                    int(cid)
                except ValueError:
                    ui.notify("Chat ID must be numeric", type="warning", position="top")
                    return
                jurs = ",".join(j for j in sorted(_jurs) if j)
                try:
                    from app.infrastructure.db.repository import SubscriptionRepository
                    is_new = SubscriptionRepository().subscribe(
                        chat_id=cid, jurisdictions=jurs,
                        frequency=_freq["v"], min_risk_level=risk_sel.value or "LOW",
                    )
                    msg = "✓ Subscription created" if is_new else "✓ Preferences updated"
                    save_status.set_text(msg)
                    ui.notify(msg, type="positive", position="top-right", timeout=3000)
                except Exception as exc:
                    ui.notify(f"Error saving: {str(exc)[:80]}", type="negative", position="top")

            ui.button("Save Preferences", icon="save", on_click=_save).props("no-caps").style(
                "background:#1e3a8a; color:#93c5fd; font-size:12px; font-weight:600; border-radius:7px; padding:6px 16px"
            )


# ── page ──────────────────────────────────────────────────────────────────────

@router.page("/settings")
def settings_page() -> None:
    dark_mode = ui.dark_mode(value=True)
    sidebar.render("settings", dark_mode)

    with ui.column().classes("w-full p-0"):
        with ui.row().classes("w-full items-center px-6 py-3").style(
            "background:#1e293b; border-bottom:1px solid #334155"
        ):
            ui.icon("settings", size="20px").style("color:#60a5fa")
            ui.label("Настройки").classes("text-sm font-semibold").style("color:#e2e8f0")

        with ui.column().classes("w-full p-6 max-w-2xl"):
            # Schedule info card — ui.html() avoids any template encoding path
            # that has been observed to garble Cyrillic characters on some hosts.
            with ui.card().classes("p-5 w-full").style("background:#1e293b"):
                ui.html('<p style="font-size:13px;font-weight:600;color:#94a3b8;'
                        'font-family:Inter,sans-serif;margin-bottom:12px">'
                        'Параметры расписания</p>')
                _sched_rows = [
                    ("Интервал",   f"каждые {settings.SCRAPE_INTERVAL_HOURS} ч"),
                    ("Потоков",    str(settings.SCRAPE_MAX_WORKERS)),
                    ("Таймаут",    f"{settings.SCRAPE_TIMEOUT_SECONDS} с"),
                    ("База данных", settings.DATABASE_URL.split("///")[-1]),
                    ("Лог-уровень", settings.LOG_LEVEL),
                ]
                for _k, _v in _sched_rows:
                    with ui.row().classes("items-center justify-between w-full py-1").style(
                        "border-bottom:1px solid rgba(255,255,255,.04)"
                    ):
                        ui.html(
                            f'<span style="font-size:12px;color:#64748b;'
                            f'font-family:Inter,sans-serif">{_k}</span>'
                        )
                        ui.html(
                            f'<span style="font-size:13px;font-weight:600;'
                            f'color:#cbd5e1;font-family:monospace">{_v}</span>'
                        )

            # Tunnel card
            with ui.card().classes("p-5 w-full mt-4").style("background:#1e293b"):
                ui.label("Туннель (для демо)").classes("text-sm font-semibold text-slate-400 mb-3")
                if tunnel_url := app.storage.general.get("tunnel_url"):
                    ui.label("Публичный URL:").classes("text-xs text-slate-400")
                    ui.label(tunnel_url).classes("text-blue-400 font-mono text-sm")
                else:
                    ui.label("Туннель не активен. Запустите с ENABLE_TUNNEL=true в .env").classes("text-slate-500 text-sm")

            _ai_console()
            _smart_alerts()
