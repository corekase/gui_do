from enum import Enum


class ValueChangeReason(str, Enum):
    """Canonical source tags for value/offset change notifications."""

    KEYBOARD = "keyboard"
    PROGRAMMATIC = "programmatic"
    MOUSE_DRAG = "mouse_drag"
    WHEEL = "wheel"
