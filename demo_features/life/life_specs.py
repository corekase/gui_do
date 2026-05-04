"""Shared specs and layout constants for the Life demo feature."""

from .life_simulation_feature import (
    _LIFE_LIFECYCLE_SPEC,
    _LIFE_RUNTIME_SPEC,
    _LIFE_WINDOW_SPEC,
)

LIFE_WINDOW_SPEC = _LIFE_WINDOW_SPEC
LIFE_RUNTIME_SPEC = _LIFE_RUNTIME_SPEC
LIFE_LIFECYCLE_SPEC = _LIFE_LIFECYCLE_SPEC

__all__ = ["LIFE_LIFECYCLE_SPEC", "LIFE_RUNTIME_SPEC", "LIFE_WINDOW_SPEC"]
