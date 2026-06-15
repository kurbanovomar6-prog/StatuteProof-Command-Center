#!/usr/bin/env python3
"""Validate the UAE 50-source activation scoreboard.

The scoreboard is allowed to contain candidates, remediation, and blocked
sources. It must not let candidate/no-save/evidence-only records masquerade as
activation-ready monitoring sources.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCOREBOARD = ROOT / "product/regradar/config/uae_50_activation_scoreboard.json"
SOURCES = ROOT / "product/regradar/sources.json"


REQUIRED_TARGET_FIELDS = {
    "target_id",
    "source_id",
    "regulator",
    "title",
    "official_url",
    "official_status",
    "adapter_family",
    "adapter_name",
    "no_save_status",
    "evidence_status",
    "baseline_status",
    "noise_risk",
    "source_health_risk",
    "source_monitor_gate",
    "evidence_trail_gate",
    "qa_critic_gate",
    "legal_language_gate",
    "product_manager_gate",
    "code_architect_gate",
    "activation_status",
    "activation_blocker",
    "next_action",
}

GATE_FIELDS = {
    "source_monitor_gate",
    "evidence_trail_gate",
    "qa_critic_gate",
    "legal_language_gate",
    "product_manager_gate",
    "code_architect_gate",
}

FORBIDDEN_PUBLIC_CLAIMS = {
    "any website can be parsed",
    "perfect parsing",
    "never miss updates",
    "guaranteed compliance",
    "we provide legal advice",
    "provides legal advice",
    "is legal advice",
    "regulator certified",
    "60 validated sources",
}


def _load(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _proof_path_exists(value: str) -> bool:
    if not value:
        return False
    path = Path(value)
    if not path.is_absolute():
        path = ROOT / value
    if path.exists():
        return True
    product_path = ROOT / "product/regradar" / value
    return product_path.exists()


def _fail(errors: list[str], message: str) -> None:
    errors.append(message)


def main() -> int:
    errors: list[str] = []
    if not SCOREBOARD.exists():
        _fail(errors, "Missing product/regradar/config/uae_50_activation_scoreboard.json")
    if not SOURCES.exists():
        _fail(errors, "Missing product/regradar/sources.json")
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    scoreboard = _load(SCOREBOARD)
    sources = _load(SOURCES)
    if not isinstance(scoreboard, dict):
        _fail(errors, "Scoreboard must be a JSON object.")
        scoreboard = {}
    targets = scoreboard.get("targets")
    if not isinstance(targets, list) or not targets:
        _fail(errors, "Scoreboard targets must be a non-empty list.")
        targets = []

    seen_ids: set[str] = set()
    activation_ready = []
    for target in targets:
        if not isinstance(target, dict):
            _fail(errors, "Every scoreboard target must be an object.")
            continue
        sid = str(target.get("source_id") or "")
        if not sid:
            _fail(errors, "Every scoreboard target requires source_id.")
            continue
        if sid in seen_ids:
            _fail(errors, f"Duplicate scoreboard source_id: {sid}")
        seen_ids.add(sid)
        missing = sorted(REQUIRED_TARGET_FIELDS - set(target))
        if missing:
            _fail(errors, f"{sid}: missing fields {missing}")
        status = str(target.get("activation_status") or "")
        if status == "activation_ready":
            activation_ready.append(target)
            is_legacy_active = target.get("evidence_status") == "legacy_active_needs_evidence_index"
            if not _proof_path_exists(str(target.get("proof_path") or "")):
                # Existing legacy active records may predate this scoreboard, but
                # newly activated records must carry proof. Keep legacy records
                # explicit instead of silently pretending proof exists.
                if not is_legacy_active:
                    _fail(errors, f"{sid}: activation_ready requires existing proof_path.")
            if int(target.get("baseline_run_count") or 0) < 2 and target.get("baseline_status") not in {"complete", "legacy_active"}:
                _fail(errors, f"{sid}: activation_ready requires baseline completion.")
            if target.get("noise_risk") == "high":
                _fail(errors, f"{sid}: high noise risk cannot be activation_ready.")
            if target.get("source_health_risk") == "high":
                _fail(errors, f"{sid}: high source-health risk cannot be activation_ready.")
            for gate in GATE_FIELDS:
                gate_value = target.get(gate) or {}
                if is_legacy_active:
                    continue
                if not isinstance(gate_value, dict) or gate_value.get("status") != "pass":
                    _fail(errors, f"{sid}: activation_ready requires {gate}=pass.")

    if not isinstance(sources, list):
        _fail(errors, "sources.json must remain a list.")
        sources = []
    active_source_ids = {
        str(source.get("source_id"))
        for source in sources
        if isinstance(source, dict)
        and source.get("jurisdiction") == "AE"
        and source.get("enabled") is True
        and source.get("status") == "active"
    }
    scoreboard_ready_ids = {str(target.get("source_id")) for target in activation_ready}
    missing_from_scoreboard = active_source_ids - scoreboard_ready_ids
    if missing_from_scoreboard:
        _fail(errors, f"Active UAE sources missing activation_ready scoreboard rows: {sorted(missing_from_scoreboard)}")

    summary = scoreboard.get("summary") or {}
    if int(summary.get("activation_ready_count") or 0) != len(activation_ready):
        _fail(errors, "Scoreboard summary activation_ready_count does not match targets.")
    if summary.get("did_reach_50") and len(activation_ready) < 50:
        _fail(errors, "Scoreboard cannot claim did_reach_50 with fewer than 50 activation_ready targets.")

    text = "\\n".join(
        path.read_text(encoding="utf-8", errors="ignore").lower()
        for path in [ROOT / "README.md", ROOT / "START_HERE.md"]
        if path.exists()
    )
    for claim in FORBIDDEN_PUBLIC_CLAIMS:
        if claim in text:
            _fail(errors, f"Forbidden public claim found: {claim}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print("Batch onboarding scoreboard validation passed.")
    print(f"Targets: {len(targets)}")
    print(f"Activation-ready/current active: {len(activation_ready)}")
    print(f"Remaining to 50: {max(0, 50 - len(activation_ready))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
