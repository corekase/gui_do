from __future__ import annotations

from enum import Enum


class CanvasEvent(Enum):
    """Canvas-scoped semantic event kinds used by canvas widgets."""

    MouseWheel = 'MouseWheel'
    MouseMotion = 'MouseMotion'
    MouseButtonDown = 'MouseButtonDown'
    MouseButtonUp = 'MouseButtonUp'
    MousePosition = 'MousePosition'
