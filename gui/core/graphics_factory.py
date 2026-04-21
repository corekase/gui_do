"""Compatibility wrapper for graphics factory imports.

The implementation now lives in gui.graphics to keep rendering code grouped.
"""

from ..graphics import InteractiveVisuals, BuiltInGraphicsFactory, WindowChromeVisuals

__all__ = ["InteractiveVisuals", "WindowChromeVisuals", "BuiltInGraphicsFactory"]
