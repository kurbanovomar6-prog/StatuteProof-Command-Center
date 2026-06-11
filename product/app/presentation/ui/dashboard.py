import threading
from nicegui import ui

from app.infrastructure.db.repository import RegulationRepository
from app.application.pipeline import run_all_regulators

_repo = RegulationRepository()

_LEVEL_COLORS = {
    "CRITICAL": "#FF4444",
    "HIGH": "#FF8800",
    "MEDIUM": "#FFD700",
    "LOW": "#44BB44",
}

_ROW_CLASS_RULES = {
    "bg-red-100": "params.data.critical_level === 'CRITICAL'",
    "bg-orange-100": "params.data.critical_level === 'HIGH'",
    "bg-yellow-50": "params.data.critical_level === 'MEDIUM'",
}

_COLUMNS = [
    {"field": "jurisdiction", "headerName": "Юрисдикция", "width": 110},
    {"field": "critical_level", "headerName": "Уровень", "width": 110},
    {"field": "effective_date", "headerName": "Дата вступления", "width": 140},
    {"field": "title", "headerName": "Название", "flex": 2},
    {"field": "summary", "headerName": "Краткое описание", "flex": 3},
    {"field": "confidence", "headerName": "Достоверность", "width": 130,
     "valueFormatter": "parseFloat(params.value).toFixed(2)"},
    {"field": "status", "headerName": "Статус", "width": 130},
]


def _kpi_card(label: str, value: str, color: str = "#1976D2"):
    with ui.card().classes("p-4 min-w-[140px] text-center shadow"):
        ui.label(label).classes("text-xs text-gray-500 uppercase")
        ui.label(value).classes("text-3xl font-bold").style(f"color: {color}")


def build_dashboard():
    jur_filter = {"value": ""}
    level_filter = {"value": ""}
    days_filter = {"value": 30}

    grid_ref: dict = {}
    kpi_total_ref: dict = {}
    kpi_crit_ref: dict = {}
    kpi_review_ref: dict = {}
    run_btn_ref: dict = {}
    run_status_ref: dict = {}

    def load_data():
        rows = _repo.list_recent(
            days=days_filter["value"],
            jurisdiction=jur_filter["value"] or None,
            level=level_filter["value"] or None,
        )
        return rows

    def refresh_grid():
        rows = load_data()
        total = len(rows)
        critical = sum(1 for r in rows if r["critical_level"] == "CRITICAL")
        review = sum(1 for r in rows if r["status"] == "HUMAN_REVIEW")

        if "label" in kpi_total_ref:
            kpi_total_ref["label"].set_text(str(total))
        if "label" in kpi_crit_ref:
            kpi_crit_ref["label"].set_text(str(critical))
        if "label" in kpi_review_ref:
            kpi_review_ref["label"].set_text(str(review))
        if "grid" in grid_ref:
            grid_ref["grid"].options["rowData"] = rows
            grid_ref["grid"].update()

    def on_run_monitor():
        run_btn_ref["btn"].disable()
        run_status_ref["label"].set_text("⏳ Мониторинг запущен...")

        def _worker():
            count = run_all_regulators()
            run_status_ref["label"].set_text(f"✅ Готово — сохранено {count} регламентов")
            run_btn_ref["btn"].enable()
            refresh_grid()

        threading.Thread(target=_worker, daemon=True).start()

    with ui.column().classes("w-full p-4 gap-4"):
        ui.label("RegRadar — Мониторинг регуляторики СНГ").classes("text-2xl font-bold text-gray-800")

        with ui.row().classes("gap-4 flex-wrap"):
            with ui.card().classes("p-4 min-w-[140px] text-center shadow"):
                ui.label("Всего").classes("text-xs text-gray-500 uppercase")
                lbl = ui.label("—").classes("text-3xl font-bold").style("color: #1976D2")
                kpi_total_ref["label"] = lbl

            with ui.card().classes("p-4 min-w-[140px] text-center shadow"):
                ui.label("Критических").classes("text-xs text-gray-500 uppercase")
                lbl2 = ui.label("—").classes("text-3xl font-bold").style("color: #FF4444")
                kpi_crit_ref["label"] = lbl2

            with ui.card().classes("p-4 min-w-[140px] text-center shadow"):
                ui.label("На проверке").classes("text-xs text-gray-500 uppercase")
                lbl3 = ui.label("—").classes("text-3xl font-bold").style("color: #FF8800")
                kpi_review_ref["label"] = lbl3

        with ui.row().classes("gap-3 items-center flex-wrap"):
            ui.label("Фильтры:").classes("text-sm font-semibold text-gray-600")
            jur_sel = ui.select(
                options=["", "RU", "KZ", "AZ", "BY", "UZ"],
                label="Юрисдикция",
                value="",
            ).classes("w-32")
            jur_sel.on("update:model-value", lambda e: (jur_filter.update({"value": e.args}), refresh_grid()))

            level_sel = ui.select(
                options=["", "CRITICAL", "HIGH", "MEDIUM", "LOW"],
                label="Уровень",
                value="",
            ).classes("w-32")
            level_sel.on("update:model-value", lambda e: (level_filter.update({"value": e.args}), refresh_grid()))

            days_sel = ui.select(
                options=[7, 30, 90, 365],
                label="Период (дней)",
                value=30,
            ).classes("w-36")
            days_sel.on("update:model-value", lambda e: (days_filter.update({"value": int(e.args)}), refresh_grid()))

            ui.button("Обновить", on_click=refresh_grid).props("outline").classes("ml-2")

        grid = ui.aggrid({
            "columnDefs": _COLUMNS,
            "rowData": [],
            "rowClassRules": _ROW_CLASS_RULES,
            "pagination": True,
            "paginationPageSize": 20,
            "domLayout": "autoHeight",
        }).classes("w-full")
        grid_ref["grid"] = grid

        with ui.row().classes("gap-3 items-center mt-2"):
            btn = ui.button("▶ Запустить мониторинг", on_click=on_run_monitor).props("color=primary")
            run_btn_ref["btn"] = btn
            status_lbl = ui.label("").classes("text-sm text-gray-500")
            run_status_ref["label"] = status_lbl

    refresh_grid()
