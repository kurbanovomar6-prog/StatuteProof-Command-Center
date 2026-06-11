"""Shared sidebar — rendered on every page via ui.left_drawer."""
from nicegui import ui

# Each entry: (page_id, material_icon, display_label, route_path)
_NAV = [
    ("dashboard", "dashboard",  "Дашборд",   "/"),
    ("tasks",     "history",    "Задачи",     "/tasks"),
    ("settings",  "tune",       "Настройки",  "/settings"),
]


def render(active: str, dark_mode=None) -> None:
    with ui.left_drawer(fixed=True, bordered=False).classes("rr-sidebar").style("width:220px"):

        # ── Logo ─────────────────────────────────────────────────
        with ui.row().classes("items-center gap-2 px-4 py-5"):
            ui.icon("policy", size="28px").style("color:#3b82f6")
            ui.label("RegRadar").classes("text-xl font-bold").style("color:#f1f5f9")

        ui.separator().style("background:#1e293b; margin:0 16px")

        # ── Navigation ───────────────────────────────────────────
        with ui.column().classes("px-2 gap-1 mt-3"):
            for page_id, icon_name, label_text, path in _NAV:
                is_active = page_id == active

                # Use ui.html for the button label to bypass any template
                # encoding path that has caused Cyrillic garbling on some hosts.
                with ui.button(
                    on_click=lambda p=path: ui.navigate.to(p),
                ).classes(
                    "rr-nav-btn" + (" rr-nav-active" if is_active else "")
                ).props("flat no-caps align=left") as _btn:
                    ui.icon(icon_name, size="20px").style(
                        "color:#60a5fa" if is_active else "color:#64748b"
                    )
                    ui.html(
                        f'<span style="font-size:13px;font-family:Inter,sans-serif;'
                        f'color:{"#93c5fd" if is_active else "#94a3b8"};'
                        f'margin-left:8px;letter-spacing:0.02em">'
                        f'{label_text}</span>'
                    )

        # ── Theme toggle ─────────────────────────────────────────
        ui.separator().style("background:#1e293b; margin:16px 16px 8px")
        with ui.row().classes("items-center px-4 gap-2 pb-2"):
            ui.icon("dark_mode", size="18px").style("color:#94a3b8")
            _dm = dark_mode if dark_mode is not None else ui.dark_mode(value=True)
            ui.switch(value=True, on_change=lambda e: _dm.set_value(e.value))
            ui.html('<span style="font-size:12px;color:#64748b;font-family:Inter,sans-serif">'
                    'Темная тема</span>')
