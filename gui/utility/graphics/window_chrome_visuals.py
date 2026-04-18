from __future__ import annotations

from dataclasses import dataclass

from pygame.surface import Surface


@dataclass(frozen=True)
class WindowChromeVisuals:
    """Pre-rendered window chrome surfaces for active and inactive states."""

    title_bar_inactive: Surface
    title_bar_active: Surface
    lower_widget: Surface
