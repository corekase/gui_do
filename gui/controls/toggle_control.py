from typing import Callable, Optional
from typing import TYPE_CHECKING

import pygame
from pygame import Rect

from ..core.gui_event import GuiEvent
from ..core.ui_node import UiNode

if TYPE_CHECKING:
    from ..app.gui_application import GuiApplication
    from ..theme.color_theme import ColorTheme


class ToggleControl(UiNode):
    """Two-state toggle control."""

    def __init__(
        self,
        control_id: str,
        rect: Rect,
        text_on: str,
        text_off: Optional[str] = None,
        pushed: bool = False,
        on_toggle: Optional[Callable[[bool], None]] = None,
        style: str = "box",
        font_role: str = "body",
    ) -> None:
        super().__init__(control_id, rect)
        self.text_on = text_on
        self.text_off = text_off if text_off is not None else text_on
        self.pushed = bool(pushed)
        self.on_toggle = on_toggle
        self.style = style
        self._font_role = "body"
        self.font_role = font_role
        self.hovered = False
        self._visuals = None
        self._visual_key = None

    @property
    def font_role(self) -> str:
        return self._font_role

    @font_role.setter
    def font_role(self, value: str) -> None:
        next_role = str(value).strip()
        if not next_role:
            raise ValueError("font_role must be a non-empty string")
        self._font_role = next_role

    def _commit_toggle(self) -> None:
        self.pushed = not self.pushed
        if self.on_toggle is not None:
            self.on_toggle(self.pushed)

    def set_on_toggle(self, callback: Optional[Callable[[bool], None]]) -> None:
        """Replace the toggle callback at runtime. Pass None to remove it."""
        if callback is not None and not callable(callback):
            raise ValueError("on_toggle callback must be callable or None")
        self.on_toggle = callback

    def _on_enabled_changed(self, old_enabled: bool, new_enabled: bool) -> None:
        if old_enabled != new_enabled:
            self.hovered = False
        super()._on_enabled_changed(old_enabled, new_enabled)

    def _on_visibility_changed(self, old_visible: bool, new_visible: bool) -> None:
        if old_visible != new_visible:
            self.hovered = False
        super()._on_visibility_changed(old_visible, new_visible)

    def handle_event(self, event: GuiEvent, app: "GuiApplication") -> bool:
        if not self.visible or not self.enabled:
            self.hovered = False
            return False

        raw = event.pos
        if isinstance(raw, tuple) and len(raw) == 2:
            self.hovered = self.rect.collidepoint(raw)
        if not self.focused and (event.is_key_down(pygame.K_RETURN) or event.is_key_down(pygame.K_SPACE)):
            return False
        if event.is_key_down(pygame.K_RETURN) or event.is_key_down(pygame.K_SPACE):
            self._commit_toggle()
            return True
        if event.is_mouse_down(1):
            if isinstance(raw, tuple) and len(raw) == 2 and self.rect.collidepoint(raw):
                self._commit_toggle()
                return True
        return False

    def draw(self, surface: "pygame.Surface", theme: "ColorTheme") -> None:
        factory = theme.graphics_factory
        font_revision = factory.font_revision()
        visual_key = (self.style, self.text_on, self.text_off, self.font_role, self.rect.width, self.rect.height, font_revision)
        if self._visuals is None or self._visual_key != visual_key:
            self._visuals = factory.build_toggle_visuals(self.style, self.text_on, self.text_off, self.rect, font_role=self.font_role)
            self._visual_key = visual_key
        selected = factory.resolve_visual_state(
            self._visuals,
            visible=self.visible,
            enabled=self.enabled,
            armed=self.pushed,
            hovered=self.hovered,
        )
        surface.blit(selected, self.rect)
