import json
import shutil
from pathlib import Path

import pytest

from tools import agent_council


ROOT = Path(__file__).resolve().parents[3]
BOARD_PATH = ROOT / "product" / "regradar" / "config" / "agent_council_tasks.json"


REQUIRED_TASK_IDS = {
    "evidence-validator-hardening",
    "customer-claim-truth-cleanup",
    "source-summary-fresh-alert-counting",
    "vara-final-source-to-25",
    "dfsa-publication-listing-adapter",
    "sca-table-download-adapter",
    "fiu-circulars-public-source-investigation",
    "difc-consultation-listing-adapter",
    "mof-document-publication-adapter",
    "moj-gazette-official-alternative-research",
    "ruflo-safe-tooling-intake",
}


REQUIRED_TASK_FIELDS = {
    "task_id",
    "title",
    "status",
    "owner_agent",
    "reviewer_agents",
    "source_family",
    "files_allowed_to_touch",
    "files_forbidden_to_touch",
    "objective",
    "acceptance_criteria",
    "evidence_required",
    "validation_commands",
    "blocker",
    "next_handoff_agent",
    "created_at",
    "updated_at",
}


def _copy_board(tmp_path: Path) -> Path:
    board = tmp_path / "agent_council_tasks.json"
    shutil.copyfile(BOARD_PATH, board)
    return board


def test_agent_council_board_contains_initial_tasks_and_required_fields():
    payload = agent_council.load_board(BOARD_PATH)

    assert payload["schema_version"] == "1.0"
    assert set(payload["allowed_statuses"]) == agent_council.ALLOWED_STATUSES
    assert {task["task_id"] for task in payload["tasks"]} == REQUIRED_TASK_IDS

    for task in payload["tasks"]:
        assert REQUIRED_TASK_FIELDS <= set(task)
        assert task["status"] in agent_council.ALLOWED_STATUSES
        assert task["owner_agent"]
        assert isinstance(task["reviewer_agents"], list)
        assert isinstance(task["acceptance_criteria"], list)
        assert isinstance(task["validation_commands"], list)


def test_update_status_rejects_unknown_status(tmp_path):
    board = _copy_board(tmp_path)

    with pytest.raises(ValueError, match="Unknown status"):
        agent_council.update_status(
            "evidence-validator-hardening",
            "almost_done",
            board_path=board,
        )


def test_update_status_and_assign_update_existing_task(tmp_path):
    board = _copy_board(tmp_path)

    task = agent_council.update_status(
        "evidence-validator-hardening",
        "in_progress",
        board_path=board,
    )
    assert task["status"] == "in_progress"

    task = agent_council.assign_task(
        "evidence-validator-hardening",
        "Evidence Trail",
        board_path=board,
    )
    assert task["owner_agent"] == "Evidence Trail"

    saved = agent_council.load_board(board)
    saved_task = agent_council.find_task(saved, "evidence-validator-hardening")
    assert saved_task["status"] == "in_progress"
    assert saved_task["owner_agent"] == "Evidence Trail"


def test_add_note_is_additive_and_preserves_existing_task_fields(tmp_path):
    board = _copy_board(tmp_path)

    before = agent_council.find_task(
        agent_council.load_board(board),
        "vara-final-source-to-25",
    )
    original_title = before["title"]

    task = agent_council.add_note(
        "vara-final-source-to-25",
        "Source Monitor should retest regulatory notices first.",
        board_path=board,
    )

    assert task["title"] == original_title
    assert task["notes"][-1]["note"] == "Source Monitor should retest regulatory notices first."
    assert task["notes"][-1]["created_at"].endswith("Z")


def test_cli_show_outputs_json_for_task(capsys):
    exit_code = agent_council.main(["show", "evidence-validator-hardening"])

    assert exit_code == 0
    output = capsys.readouterr().out
    task = json.loads(output)
    assert task["task_id"] == "evidence-validator-hardening"
