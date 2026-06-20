from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.api import _truthy_param


def test_truthy_param_accepts_boolean_true_values():
    assert _truthy_param(True) is True
    assert _truthy_param("true") is True
    assert _truthy_param("1") is True
    assert _truthy_param("yes") is True


def test_truthy_param_rejects_false_strings_and_empty_values():
    assert _truthy_param(False) is False
    assert _truthy_param("false") is False
    assert _truthy_param("0") is False
    assert _truthy_param("no") is False
    assert _truthy_param("") is False
    assert _truthy_param(None) is False
