"""Shared specs and constants for the systems demo feature package.

This module intentionally centralizes package-local constants to preserve the
default kind-file layout contract (`*_feature.py` + `*_specs.py`).
"""

from __future__ import annotations


SYSTEMS_TAB_KEYS = (
    "data",
    "validation",
    "history",
    "theme",
    "state",
    "infrastructure",
    "scheduling",
    "persistence",
    "graphics",
)


__all__ = ["SYSTEMS_TAB_KEYS"]
