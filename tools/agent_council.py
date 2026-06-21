#!/usr/bin/env python3
"""Small local task-board helper for the StatuteProof Agent Council."""

from __future__ import annotations

import argparse
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TASK_BOARD_PATH = ROOT / "product" / "regradar" / "config" / "agent_council_tasks.json"

ALLOWED_STATUSES = {
    "proposed",
    "accepted",
    "in_progress",
    "blocked",
    "review_source_monitor",
    "review_evidence",
    "review_qa",
    "review_legal",
    "review_product",
    "done",
    "rejected",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_board(board_path: Path = TASK_BOARD_PATH) -> dict[str, Any]:
    with board_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    validate_board(payload)
    return payload


def save_board(payload: dict[str, Any], board_path: Path = TASK_BOARD_PATH) -> None:
    validate_board(payload)
    with board_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=True)
        handle.write("\n")


def validate_board(payload: dict[str, Any]) -> None:
    statuses = set(payload.get("allowed_statuses", []))
    if statuses != ALLOWED_STATUSES:
        raise ValueError("Task board allowed_statuses does not match the council status contract")
    task_ids: set[str] = set()
    for task in payload.get("tasks", []):
        task_id = task.get("task_id")
        if not task_id:
            raise ValueError("Task is missing task_id")
        if task_id in task_ids:
            raise ValueError(f"Duplicate task_id: {task_id}")
        task_ids.add(task_id)
        status = task.get("status")
        if status not in ALLOWED_STATUSES:
            raise ValueError(f"Unknown status for {task_id}: {status}")


def find_task(payload: dict[str, Any], task_id: str) -> dict[str, Any]:
    for task in payload.get("tasks", []):
        if task.get("task_id") == task_id:
            return task
    raise KeyError(f"Task not found: {task_id}")


def list_tasks(board_path: Path = TASK_BOARD_PATH) -> list[dict[str, Any]]:
    return load_board(board_path)["tasks"]


def show_task(task_id: str, board_path: Path = TASK_BOARD_PATH) -> dict[str, Any]:
    return find_task(load_board(board_path), task_id)


def update_status(task_id: str, status: str, board_path: Path = TASK_BOARD_PATH) -> dict[str, Any]:
    if status not in ALLOWED_STATUSES:
        raise ValueError(f"Unknown status: {status}")
    payload = load_board(board_path)
    task = find_task(payload, task_id)
    task["status"] = status
    task["updated_at"] = utc_now()
    save_board(payload, board_path)
    return task


def assign_task(task_id: str, owner_agent: str, board_path: Path = TASK_BOARD_PATH) -> dict[str, Any]:
    if not owner_agent.strip():
        raise ValueError("owner_agent must not be empty")
    payload = load_board(board_path)
    task = find_task(payload, task_id)
    task["owner_agent"] = owner_agent
    task["updated_at"] = utc_now()
    save_board(payload, board_path)
    return task


def add_note(task_id: str, note: str, board_path: Path = TASK_BOARD_PATH) -> dict[str, Any]:
    if not note.strip():
        raise ValueError("note must not be empty")
    payload = load_board(board_path)
    task = find_task(payload, task_id)
    task.setdefault("notes", []).append({"created_at": utc_now(), "note": note})
    task["updated_at"] = utc_now()
    save_board(payload, board_path)
    return task


def _print_json(value: Any) -> None:
    print(json.dumps(value, indent=2, ensure_ascii=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage the local StatuteProof Agent Council task board.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list", help="List all task IDs and statuses.")

    show_parser = subparsers.add_parser("show", help="Show one task as JSON.")
    show_parser.add_argument("task_id")

    status_parser = subparsers.add_parser("update-status", help="Update a task status.")
    status_parser.add_argument("task_id")
    status_parser.add_argument("status")

    assign_parser = subparsers.add_parser("assign", help="Assign a task owner.")
    assign_parser.add_argument("task_id")
    assign_parser.add_argument("owner_agent")

    note_parser = subparsers.add_parser("add-note", help="Append an operator note to a task.")
    note_parser.add_argument("task_id")
    note_parser.add_argument("note")

    subparsers.add_parser("validate-protocol", help="Validate the governed Agent Council protocol and blackboard.")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "list":
            for task in list_tasks():
                print(f"{task['task_id']}\t{task['status']}\t{task['owner_agent']}")
            return 0
        if args.command == "show":
            _print_json(show_task(args.task_id))
            return 0
        if args.command == "update-status":
            _print_json(update_status(args.task_id, args.status))
            return 0
        if args.command == "assign":
            _print_json(assign_task(args.task_id, args.owner_agent))
            return 0
        if args.command == "add-note":
            _print_json(add_note(args.task_id, args.note))
            return 0
        if args.command == "validate-protocol":
            validator_path = ROOT / "tools" / "validate_agent_council_protocol.py"
            spec = importlib.util.spec_from_file_location("validate_agent_council_protocol", validator_path)
            if spec is None or spec.loader is None:
                raise ValueError("Unable to load validate_agent_council_protocol.py")
            validate_agent_council_protocol = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(validate_agent_council_protocol)

            return validate_agent_council_protocol.main([])
    except (KeyError, ValueError) as exc:
        parser.exit(2, f"agent_council: {exc}\n")
    parser.error(f"Unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
