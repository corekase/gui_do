from __future__ import annotations

from typing import Dict, Tuple

from pygame import Rect, Surface
from pygame.draw import line, rect as draw_rect

# Literal built-in palette from the original widget base.
BUILT_IN_COLOURS: Dict[str, Tuple[int, int, int]] = {
    "full": (255, 255, 255),
    "light": (0, 200, 200),
    "medium": (0, 150, 150),
    "dark": (0, 100, 100),
    "none": (0, 0, 0),
    "text": (255, 255, 255),
    "highlight": (238, 230, 0),
    "background": (0, 60, 60),
}


def draw_frame_bitmap(
    surface: Surface,
    ul,
    lr,
    ul_d,
    lr_d,
    background,
    surface_rect: Rect,
) -> None:
    """Literal frame routine from the built-in bitmap factory."""
    x, y, width, height = surface_rect
    surface.lock()
    draw_rect(surface, background, surface_rect, 0)
    line(surface, ul, (x, y), (x + width - 1, y))
    line(surface, ul, (x, y), (x, y + height - 1))
    line(surface, lr, (x, y + height - 1), (x + width - 1, y + height - 1))
    line(surface, lr, (x + width - 1, y - 1), (x + width - 1, y + height - 1))
    if width > 2 and height > 2:
        surface.set_at((x + 1, y + 1), ul_d)
        surface.set_at((x + width - 2, y + height - 2), lr_d)
    surface.unlock()


def draw_box_bitmap(surface: Surface, state: str, rect: Rect, colours: Dict[str, Tuple[int, int, int]]) -> None:
    """Literal state-to-frame mapping from the old factory."""
    if state == "idle":
        draw_frame_bitmap(surface, colours["light"], colours["dark"], colours["full"], colours["none"], colours["medium"], rect)
    elif state == "hover":
        draw_frame_bitmap(surface, colours["light"], colours["dark"], colours["full"], colours["none"], colours["light"], rect)
    elif state == "armed":
        draw_frame_bitmap(surface, colours["none"], colours["light"], colours["none"], colours["full"], colours["dark"], rect)
