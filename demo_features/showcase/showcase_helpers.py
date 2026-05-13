"""Helper functions for the showcase feature package."""

from __future__ import annotations

from .showcase_specs import SHOWCASE_CATEGORY_ROUTING_ROWS


def category_for_row(row_index: int) -> str:
    """Return the category key for the given placement row index."""
    if row_index < SHOWCASE_CATEGORY_ROUTING_ROWS["basics_max"]:
        return "basics"
    if row_index < SHOWCASE_CATEGORY_ROUTING_ROWS["data_max"]:
        return "data"
    if row_index < SHOWCASE_CATEGORY_ROUTING_ROWS["advanced_max"]:
        return "advanced"
    return "extended"


__all__ = [
    "category_for_row",
]
