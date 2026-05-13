"""Shared specs and constants for the systems demo feature package.

This module intentionally centralizes package-local constants to preserve the
default kind-file layout contract (`*_feature.py` + `*_specs.py`).
"""

from __future__ import annotations


SYSTEMS_TAB_DEFINITIONS = (
    ("data", "Data"),
    ("validation", "Validation"),
    ("history", "History"),
    ("theme", "Theme"),
    ("state", "State"),
    ("infrastructure", "Infrastructure"),
    ("scheduling", "Scheduling"),
    ("motion", "Motion"),
    ("persistence", "Persistence"),
    ("graphics", "Graphics"),
    ("text", "Text"),
)

SYSTEMS_TAB_KEYS = tuple(key for key, _label in SYSTEMS_TAB_DEFINITIONS)

SYSTEMS_PANEL_PADDING_X = 16
SYSTEMS_LEFT_SIDE_INSET_X = 10
SYSTEMS_LABEL_INSET_X = 10
SYSTEMS_BUTTON_ROW_HEIGHT = 32
SYSTEMS_BUTTON_ROW_GAP = 12
SYSTEMS_BUTTON_ROW_SPACING = 12

SYSTEMS_PRESENTER_TAB_HEIGHT = 36
SYSTEMS_PRESENTER_TAB_GAP = 8
SYSTEMS_PRESENTER_HORIZONTAL_PADDING = 2

SYSTEMS_LABEL_STACK_GAP = 8
SYSTEMS_COMPACT_LABEL_WIDTH = 120
SYSTEMS_COMPACT_ROW_GAP = 10
SYSTEMS_GRAPHICS_EMITTER_PADDING = 12
SYSTEMS_TEXT_PREVIEW_MIN_WIDTH = 240
SYSTEMS_TEXT_PREVIEW_MAX_EVENTS = 24

SYSTEMS_MOTION_ANIMATION_STATES = ("idle", "hover", "press")
SYSTEMS_SURFACE_EFFECT_CYCLE = ("blur", "greyscale", "tint", "brightness", "vignette", "pixelate")
SYSTEMS_HISTORY_STAGES = (
    "Draft",
    "Ready for Review",
    "Approved",
    "Shipped",
)


__all__ = [
    "SYSTEMS_BUTTON_ROW_GAP",
    "SYSTEMS_BUTTON_ROW_HEIGHT",
    "SYSTEMS_BUTTON_ROW_SPACING",
    "SYSTEMS_HISTORY_STAGES",
    "SYSTEMS_GRAPHICS_EMITTER_PADDING",
    "SYSTEMS_COMPACT_LABEL_WIDTH",
    "SYSTEMS_COMPACT_ROW_GAP",
    "SYSTEMS_LABEL_INSET_X",
    "SYSTEMS_LABEL_STACK_GAP",
    "SYSTEMS_LEFT_SIDE_INSET_X",
    "SYSTEMS_MOTION_ANIMATION_STATES",
    "SYSTEMS_PANEL_PADDING_X",
    "SYSTEMS_PRESENTER_HORIZONTAL_PADDING",
    "SYSTEMS_PRESENTER_TAB_GAP",
    "SYSTEMS_PRESENTER_TAB_HEIGHT",
    "SYSTEMS_SURFACE_EFFECT_CYCLE",
    "SYSTEMS_TEXT_PREVIEW_MAX_EVENTS",
    "SYSTEMS_TEXT_PREVIEW_MIN_WIDTH",
    "SYSTEMS_TAB_DEFINITIONS",
    "SYSTEMS_TAB_KEYS",
]
