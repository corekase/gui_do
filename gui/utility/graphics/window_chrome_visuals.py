from dataclasses import dataclass

from pygame.surface import Surface


@dataclass(frozen=True)
class WindowChromeVisuals:
    title_bar_inactive: Surface
    title_bar_active: Surface
    lower_widget: Surface
