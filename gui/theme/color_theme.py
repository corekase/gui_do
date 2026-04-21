from __future__ import annotations

from pathlib import Path
from typing import Dict, Tuple

import pygame

from ..graphics.built_in_definitions import BUILT_IN_COLOURS


class ColorTheme:
    """Classic gui_do-inspired palette, fonts, and text helper."""

    def __init__(self) -> None:
        # Literal palette from the built-in widget base.
        self.light = BUILT_IN_COLOURS["light"]
        self.medium = BUILT_IN_COLOURS["medium"]
        self.dark = BUILT_IN_COLOURS["dark"]
        self.background = BUILT_IN_COLOURS["background"]
        self.highlight = BUILT_IN_COLOURS["highlight"]
        self.text = BUILT_IN_COLOURS["text"]
        self.shadow = BUILT_IN_COLOURS["none"]

        # Shared aliases used by controls.
        self.panel = self.medium
        self.track = self.dark
        self.handle = self.light
        self.handle_active = self.highlight
        self.button = self.medium
        self.button_hover = self.light

        self._font_path_main = self._resource_path("data", "fonts", "Ubuntu-B.ttf")
        self._font_path_title = self._resource_path("data", "fonts", "Gimbot.ttf")
        self._font_cache: Dict[Tuple[str, int], pygame.font.Font] = {}
        self._background_bitmap = self._load_background_bitmap()

    def _resource_path(self, *parts: str) -> str:
        root = Path(__file__).resolve().parents[2]
        return str(root.joinpath(*parts))

    def _load_background_bitmap(self):
        try:
            path = self._resource_path("data", "images", "backdrop.jpg")
            return pygame.image.load(path).convert()
        except Exception:
            return None

    @property
    def background_bitmap(self):
        return self._background_bitmap

    def get_font(self, size: int, title: bool = False) -> pygame.font.Font:
        key = ("title" if title else "main", int(size))
        cached = self._font_cache.get(key)
        if cached is not None:
            return cached
        path = self._font_path_title if title else self._font_path_main
        try:
            font = pygame.font.Font(path, int(size))
        except Exception:
            font = pygame.font.SysFont("arial", int(size), bold=title)
        self._font_cache[key] = font
        return font

    def render_text(self, text: str, size: int = 16, title: bool = False, color=None, shadow: bool = True):
        text_color = self.text if color is None else color
        font = self.get_font(size=size, title=title)
        if not shadow:
            return font.render(text, True, text_color)
        text_bitmap = font.render(text, True, text_color)
        shadow_bitmap = font.render(text, True, self.shadow)
        out = pygame.Surface((text_bitmap.get_width() + 1, text_bitmap.get_height() + 1), pygame.SRCALPHA)
        out.blit(shadow_bitmap, (1, 1))
        out.blit(text_bitmap, (0, 0))
        return out
