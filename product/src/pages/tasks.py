"""Tasks page — scrape job history log."""
from nicegui import APIRouter, ui

from database import job_repo
from src import sidebar

router = APIRouter()

_JOB_COLS = [
    {"field": "id",          "headerName": "#",         "width": 60},
    {"field": "regulator",   "headerName": "Регулятор", "flex": 2},
    {"field": "jurisdiction","headerName": "Юр.",       "width": 70},
    {"field": "status",      "headerName": "Статус",    "width": 100,
     ":cellStyle": """p=>({color:{DONE:'#4ade80',ERROR:'#f87171',PENDING:'#94a3b8',running:'#60a5fa'}[p.value]||'#fff',fontWeight:700})"""},
    {"field": "found",       "headerName": "Найдено",   "width": 90},
    {"field": "saved",       "headerName": "Сохранено", "width": 100},
    {"field": "duration",    "headerName": "Время",     "width": 90},
    {"field": "started",     "headerName": "Запущен",   "width": 130},
    {"field": "error",       "headerName": "Ошибка",    "flex": 2},
]


@router.page("/tasks")
def tasks_page() -> None:
    dark_mode = ui.dark_mode(value=True)
    sidebar.render("tasks", dark_mode)

    with ui.column().classes("w-full p-0"):
        with ui.row().classes("w-full items-center px-6 py-3").style(
            "background:#1e293b; border-bottom:1px solid #334155"
        ):
            ui.icon("history", size="20px").style("color:#60a5fa")
            ui.label("История задач парсинга").classes("text-sm font-semibold").style("color:#e2e8f0")

        with ui.column().classes("w-full p-6"):
            grid = ui.aggrid({
                "columnDefs": _JOB_COLS,
                "rowData": [],
                "pagination": True,
                "paginationPageSize": 20,
                "domLayout": "autoHeight",
                "theme": "quartz",
            }).classes("w-full")

            def _reload():
                grid.options["rowData"] = job_repo.recent(50)
                grid.update()

            ui.button("Обновить журнал", on_click=_reload, icon="refresh").props("outline no-caps").classes("mt-3")
            _reload()
