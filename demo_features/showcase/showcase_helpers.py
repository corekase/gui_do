"""Helper functions for the showcase feature package."""

from __future__ import annotations

from .showcase_specs import SHOWCASE_CATEGORY_ROW_GROUPS, SHOWCASE_CATEGORY_ROW_RANGES


def category_for_row(row_index: int) -> str:
    """Return the category key for the given placement row index."""
    idx = int(row_index)
    for key, rows in SHOWCASE_CATEGORY_ROW_GROUPS.items():
        if idx in rows:
            return key
    for key, ranges in SHOWCASE_CATEGORY_ROW_RANGES.items():
        for start, end in ranges:
            if start <= idx <= end:
                return key
    return "display"


__all__ = [
    "category_for_row",
]
