"""render_telegram must never exceed Telegram's 4096-char limit, and must never
truncate the proof URL / disclaimer footer off the message.

Regression: the auto alert path had no length cap, so an oversized message got
a Telegram 400, the send failed, and — because alerts are only built when
content changed — it was never retried. The alert was permanently lost.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.alert_content import render_telegram, FOOTER, _TELEGRAM_LIMIT


def _content(**over):
    base = {
        "title": "DFSA amends AML Module",
        "severity_line": "HIGH — multiple strong indicators",
        "url": "https://dfsa.example/rulebook/aml",
        "footer": FOOTER,
    }
    base.update(over)
    return base


def test_short_message_is_unchanged_and_carries_footer():
    msg = render_telegram(_content(excerpt="+ a small change"))
    assert len(msg) <= _TELEGRAM_LIMIT
    assert FOOTER in msg
    assert "https://dfsa.example/rulebook/aml" in msg
    assert "truncated" not in msg.lower()


def test_oversized_message_is_capped_but_keeps_url_and_footer():
    huge = "This is a very long summary sentence. " * 400  # ~15k chars
    msg = render_telegram(_content(summary=huge, excerpt="+ " + ("x" * 5000)))
    assert len(msg) <= _TELEGRAM_LIMIT
    # The disclaimer and proof URL must survive truncation.
    assert msg.rstrip().endswith(f"_{FOOTER}_")
    assert "https://dfsa.example/rulebook/aml" in msg
    assert "truncated" in msg.lower()


def test_footer_survives_even_with_maximal_fields():
    big = "Y" * 9000
    msg = render_telegram(
        _content(summary=big, action=big, affected=big, excerpt=big)
    )
    assert len(msg) <= _TELEGRAM_LIMIT
    assert FOOTER in msg


def test_pathological_long_url_never_exceeds_limit():
    # A URL longer than the whole limit must NOT produce an over-limit message
    # (which Telegram would 400, losing the alert). The hard backstop clamps it.
    msg = render_telegram(_content(url="https://x.example/" + ("a" * 6000)))
    assert len(msg) <= _TELEGRAM_LIMIT


def test_markdown_metachars_stripped_from_dynamic_fields():
    # Customer alerts are sent with parse_mode='Markdown', so an adversarial
    # link/markup in AI/source-derived fields must NOT survive into the message
    # (else it renders as a live clickable link injected into the alert).
    msg = render_telegram(_content(
        summary="See [click here](https://evil.example) now",
        action="_urgent_ *bold* [x](http://evil)",
        affected="a[b]c*d_e",
    ))
    # The link-forming brackets and emphasis metacharacters must be gone, so a
    # Markdown parser can never build a live [text](url) link from injected text.
    assert "[click here]" not in msg
    assert "[x]" not in msg
    assert "[b]" not in msg
    # Emphasis wrappers from the dynamic 'action' field are stripped.
    assert "_urgent_" not in msg
    assert "*bold*" not in msg
    # The plain text survives (just without the metacharacters).
    assert "click here" in msg
    assert "urgent" in msg
