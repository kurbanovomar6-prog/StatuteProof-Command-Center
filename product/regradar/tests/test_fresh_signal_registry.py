import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.adapters.registry import get_adapter_for_url


def test_cbuae_rulebook_adapter_registered_for_rulebook_pages():
    adapter = get_adapter_for_url(
        "https://rulebook.centralbank.ae/en/rulebook/amlcft",
        {"source_id": "AE-cbuae-rulebook-amlcft"},
    )

    assert adapter is not None
    assert adapter.name == "uae_cbuae_rulebook"


def test_cbuae_rulebook_adapter_registered_for_revision_updates():
    adapter = get_adapter_for_url(
        "https://rulebook.centralbank.ae/en/view-revision-updates?f_days=on&changed=-365%20day",
        {"source_id": "AE-cbuae-rulebook-revision-updates"},
    )

    assert adapter is not None
    assert adapter.name == "uae_cbuae_rulebook"


def test_fsra_circulars_adapter_registered_for_supervision_circulars():
    adapter = get_adapter_for_url(
        "https://www.adgm.com/operating-in-adgm/additional-obligations-of-financial-services-entities/supervision/circulars",
        {"source_id": "AE-adgm-fsra-supervision-circulars"},
    )

    assert adapter is not None
    assert adapter.name == "uae_fsra_circulars"


def test_fsra_adapter_registered_for_configured_adgm_listing_sources():
    adapter = get_adapter_for_url(
        "https://www.adgm.com/legal-framework/public-consultations",
        {"source_id": "AE-adgm-fsra-consultations", "adapter_name": "adgm_fsra_listing"},
    )

    assert adapter is not None
    assert adapter.name == "uae_fsra_circulars"


def test_uae_adapters_reject_unrelated_urls():
    adapter = get_adapter_for_url(
        "https://www.dfsa.ae/rules-and-standards",
        {"source_id": "AE-dubai-financial-services-authority-dfsa"},
    )

    assert adapter is None
