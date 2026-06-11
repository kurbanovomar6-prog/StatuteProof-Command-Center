"""
Paragraph-level structured diff engine — v2.

Returns a dict instead of a raw string so callers can inspect each
category (added, removed, modified) independently.

Algorithm:
  1. Split both texts on double newlines → paragraph sequences.
  2. Strip whitespace-only paragraphs.
  3. Run unified_diff with n=0 (zero context lines).
  4. Parse output into per-hunk (removed, added) pairs.
  5. Classify:
       - hunk has only '-' lines   → pure removal
       - hunk has only '+' lines   → pure addition
       - hunk has both            → modification (counted in modified_count)
  6. Drop any block shorter than 20 chars (formatting artifacts).

Return format:
    {
        "has_changes":    bool,
        "added":          list[str],   # new paragraphs (pure additions + modified new)
        "removed":        list[str],   # deleted paragraphs (pure removals + modified old)
        "modified_count": int,         # hunks that had both additions and removals
    }
"""

from difflib import unified_diff

_MIN_FRAGMENT = 20


def _parse_hunks(
    diff_lines: list[str],
) -> list[tuple[list[str], list[str]]]:
    """
    Break unified_diff output into (removed_lines, added_lines) per hunk.

    Each hunk boundary is marked by a line starting with '@@'.
    """
    hunks: list[tuple[list[str], list[str]]] = []
    rem:   list[str] = []
    add:   list[str] = []
    in_hunk = False

    for line in diff_lines:
        if line.startswith("@@"):
            if in_hunk:
                hunks.append((rem[:], add[:]))
            rem, add = [], []
            in_hunk = True
        elif in_hunk:
            if line.startswith("-") and not line.startswith("---"):
                text = line[1:].strip()
                if len(text) >= _MIN_FRAGMENT:
                    rem.append(text)
            elif line.startswith("+") and not line.startswith("+++"):
                text = line[1:].strip()
                if len(text) >= _MIN_FRAGMENT:
                    add.append(text)

    if in_hunk:
        hunks.append((rem, add))

    return hunks


def get_diff(old_text: str, new_text: str) -> dict:
    """
    Compute a structured paragraph-level diff.

    Parameters
    ----------
    old_text : str
        Previously stored content (paragraphs separated by "\\n\\n").
    new_text : str
        Freshly scraped content (paragraphs separated by "\\n\\n").

    Returns
    -------
    dict
        {
            "has_changes":    bool,
            "added":          list[str],
            "removed":        list[str],
            "modified_count": int,
        }
    """
    _EMPTY: dict = {
        "has_changes":    False,
        "added":          [],
        "removed":        [],
        "modified_count": 0,
    }

    old_paras = [p.strip() for p in old_text.split("\n\n") if p.strip()]
    new_paras = [p.strip() for p in new_text.split("\n\n") if p.strip()]

    raw_diff = list(unified_diff(
        old_paras,
        new_paras,
        fromfile="previous",
        tofile="current",
        lineterm="",
        n=0,
    ))

    if not raw_diff:
        return _EMPTY

    hunks = _parse_hunks(raw_diff)

    if not hunks:
        return _EMPTY

    added:          list[str] = []
    removed:        list[str] = []
    modified_count: int       = 0

    for rem, add in hunks:
        if rem and add:
            # Both sides present → modification
            modified_count += 1
            removed.extend(rem)
            added.extend(add)
        elif rem:
            removed.extend(rem)
        elif add:
            added.extend(add)

    has_changes = bool(added or removed)

    return {
        "has_changes":    has_changes,
        "added":          added,
        "removed":        removed,
        "modified_count": modified_count,
    }
