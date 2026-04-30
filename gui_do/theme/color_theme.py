
from __future__ import annotations
# --- Global singleton font registry and font manager ---
_GLOBAL_FONT_REGISTRY = None
_GLOBAL_FONT_MANAGER = None

def get_global_font_registry():
    global _GLOBAL_FONT_REGISTRY
    return _GLOBAL_FONT_REGISTRY

def set_global_font_registry(registry):
    global _GLOBAL_FONT_REGISTRY
    _GLOBAL_FONT_REGISTRY = registry

def get_global_font_manager():
    global _GLOBAL_FONT_MANAGER
    return _GLOBAL_FONT_MANAGER

def set_global_font_manager(manager):
    global _GLOBAL_FONT_MANAGER
    _GLOBAL_FONT_MANAGER = manager

from pathlib import Path

from ..graphics.built_in_definitions import BUILT_IN_COLOURS
from .font_manager import FontManager


class ColorTheme:
    """Classic gui_do-inspired palette and text services."""

    def __init__(self, font_roles=None) -> None:
        self.light = BUILT_IN_COLOURS["light"]
        self.medium = BUILT_IN_COLOURS["medium"]
        self.dark = BUILT_IN_COLOURS["dark"]
        self.background = BUILT_IN_COLOURS["background"]
        self.highlight = BUILT_IN_COLOURS["highlight"]
        self.text = BUILT_IN_COLOURS["text"]
        self.shadow = BUILT_IN_COLOURS["none"]

        # Always use the global font manager
        global_manager = get_global_font_manager()
        if global_manager is not None:
            self.fonts = global_manager
        else:
            # Fallback: create a default manager (should not happen in normal app flow)
            self.fonts = FontManager(resource_root=Path(__file__).resolve().parents[2])
        self._background_bitmap = None

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
        # Support both FontManager and FontRoleRegistry
        if hasattr(self.fonts, "register_role"):
            self.fonts.register_role(
                role_name,
                size=size,
                file_path=file_path,
                system_name=system_name,
                bold=bold,
                italic=italic,
            )
        elif hasattr(self.fonts, "define"):
            self.fonts.define(
                role_name,
                size=size,
                file_path=file_path,
                system_name=system_name,
                bold=bold,
                italic=italic,
            )
        else:
            raise TypeError(f"Unsupported font registry type: {type(self.fonts)}")

    def font_roles(self) -> tuple[str, ...]:
        return self.fonts.role_names()
