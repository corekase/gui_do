from __future__ import annotations

from pathlib import Path

from ..graphics.built_in_definitions import BUILT_IN_COLOURS
from ..core.font_manager import FontManager

import pygame


class ColorTheme:
    """Classic gui_do-inspired palette and text services."""

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

        self.fonts = FontManager(resource_root=Path(__file__).resolve().parents[2])
        self.fonts.register_role("body", file_path="data/fonts/Ubuntu-B.ttf", size=16, system_name="arial")
        self.fonts.register_role("title", file_path="data/fonts/Gimbot.ttf", size=14, system_name="arial", bold=True)
        self.fonts.register_role("display", file_path="data/fonts/Gimbot.ttf", size=72, system_name="arial", bold=True)
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

    def render_text(self, text: str, *, role: str = "body", size: int | None = None, color=None, shadow: bool = True):
        text_color = self.text if color is None else color
        if not shadow:
            return self.fonts.render_text(text, text_color, role_name=role, size=size)
        return self.fonts.render_text_with_shadow(text, text_color, self.shadow, role_name=role, size=size)

    def register_font_role(
        self,
        role_name: str,
        *,
        size: int,
        file_path=None,
        system_name=None,
        bold: bool = False,
        italic: bool = False,
    ) -> None:
        """Create or update which typeface and size a named role uses."""
        self.fonts.register_role(
            role_name,
            size=size,
            file_path=file_path,
            system_name=system_name,
            bold=bold,
            italic=italic,
        )

    def font_roles(self) -> tuple[str, ...]:
        return self.fonts.role_names()
