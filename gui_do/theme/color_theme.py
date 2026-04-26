from __future__ import annotations

from pathlib import Path

from ..graphics.built_in_definitions import BUILT_IN_COLOURS
from ..core.font_manager import FontManager
from ..core.error_handling import report_nonfatal_error

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

        self.fonts = FontManager(resource_root=Path(__file__).resolve().parents[2])
        # Package defaults intentionally avoid external font files.
        # Role rendering resolves through FontManager fallback (system default, then pygame default).
        self.fonts.register_role("body", size=16)
        self.fonts.register_role("title", size=14, bold=True)
        self.fonts.register_role("display", size=72, bold=True)
        self._background_bitmap = self._load_background_bitmap()

    def _resource_path(self, *parts: str) -> str:
        root = Path(__file__).resolve().parents[2]
        return str(root.joinpath(*parts))

    def _load_background_bitmap(self):
        try:
            path = self._resource_path("demo_features", "data", "images", "backdrop.jpg")
            loaded = pygame.image.load(path)
            try:
                return loaded.convert()
            except pygame.error:
                return loaded
        except Exception as exc:
            report_nonfatal_error(
                "failed to load theme background bitmap; continuing without background image",
                kind="io",
                subsystem="gui.theme",
                operation="ColorTheme._load_background_bitmap",
                cause=exc,
                path=path,
                source_skip_frames=1,
            )
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
