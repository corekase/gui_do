"""Compatibility wrapper for graphics factory imports.

The implementation now lives in gui.graphics to keep rendering code grouped.
"""

from ..graphics import InteractiveVisuals, LegacyGraphicsFactory, WindowChromeVisuals

__all__ = ["InteractiveVisuals", "WindowChromeVisuals", "LegacyGraphicsFactory"]
