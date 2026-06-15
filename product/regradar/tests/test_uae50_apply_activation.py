from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_apply_activation_module():
    root = Path(__file__).resolve().parents[3]
    module_path = root / "tools" / "uae50_apply_activation.py"
    spec = importlib.util.spec_from_file_location("uae50_apply_activation", module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _spec() -> dict:
    return {
        "source_id": "AE-test-source",
        "name": "AE Test Source",
        "url": "https://example.gov.ae/test",
        "category": "aml",
        "adapter_family": "fiu_eocn_document_listing",
        "adapter_name": "fiu_eocn_document_listing",
        "adapter_config": {"container_selector": "body"},
        "expected_min_length": 500,
        "proof_path": "data/source_snapshots/proof.json",
        "no_save_normalized_hash": "abc123",
    }


def test_activation_status_entry_preserves_adapter_config():
    module = _load_apply_activation_module()

    entry = module.slug_to_status_entry(_spec())

    assert entry["adapter_config"] == {"container_selector": "body"}
    assert entry["normalized_hash"] == "abc123"


def test_activation_status_entry_updates_existing_source():
    module = _load_apply_activation_module()
    sources = [{
        "source_id": "AE-test-source",
        "url": "https://example.gov.ae/test",
        "normalized_hash": "old",
    }]

    action = module.upsert_status_entry(sources, _spec())

    assert action == "updated"
    assert len(sources) == 1
    assert sources[0]["enabled"] is True
    assert sources[0]["adapter_config"] == {"container_selector": "body"}
    assert sources[0]["normalized_hash"] == "abc123"
