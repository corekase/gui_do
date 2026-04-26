from typing import Callable, Optional
from typing import TYPE_CHECKING
from time import perf_counter

import pygame
from pygame import Rect

from ..core.gui_event import GuiEvent
from ..core.first_frame_profiler import first_frame_profiler
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
        self._pushed = bool(pushed)
        self.on_toggle = on_toggle
        self.style = style
        self._font_role = "body"
        self.font_role = font_role
        self.hovered = False
        self._focus_activation_armed = False
        self._visuals_off = None
        self._visuals_on = None
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

    @property
    def pushed(self) -> bool:
        return self._pushed

    @pushed.setter
    def pushed(self, value: bool) -> None:
        next_value = bool(value)
        if self._pushed == next_value:
            return
        self._pushed = next_value
        self.invalidate()

    def _commit_toggle(self) -> None:
        self.pushed = not self.pushed
        if self.on_toggle is not None:
            self.on_toggle(self.pushed)

    def set_on_toggle(self, callback: Optional[Callable[[bool], None]]) -> None:
        """Replace the toggle callback at runtime. Pass None to remove it."""
        if callback is not None and not callable(callback):
            raise ValueError("on_toggle callback must be callable or None")
        self.on_toggle = callback

    def _invoke_click(self) -> None:
        self._commit_toggle()

    def begin_focus_activation_visual(self) -> None:
        """Show a temporary armed visual after focus-driven activation."""
        if self._focus_activation_armed:
            return
        self._focus_activation_armed = True
        self.invalidate()

    def end_focus_activation_visual(self) -> None:
        """Clear temporary armed visual after focus activation hint timeout."""
        if not self._focus_activation_armed:
            return
        self._focus_activation_armed = False
        self.invalidate()

    def _on_enabled_changed(self, _old_enabled: bool, _new_enabled: bool) -> None:
        self.hovered = False
        self._focus_activation_armed = False
        super()._on_enabled_changed(_old_enabled, _new_enabled)

    def _on_visibility_changed(self, _old_visible: bool, _new_visible: bool) -> None:
        self.hovered = False
        self._focus_activation_armed = False
        super()._on_visibility_changed(_old_visible, _new_visible)

    def reconcile_hover(self, wants_hover: bool) -> None:
        if self.hovered != wants_hover:
            self.hovered = wants_hover
            self.invalidate()

    def handle_event(self, event: GuiEvent, app: "GuiApplication") -> bool:
        if not self.visible or not self.enabled:
            self.hovered = False
            return False

        raw = event.pos
        if isinstance(raw, tuple) and len(raw) == 2:
            self.hovered = self.rect.collidepoint(raw)
        if event.is_mouse_down(1):
            if isinstance(raw, tuple) and len(raw) == 2 and self.rect.collidepoint(raw):
                self._commit_toggle()
                return True
        return False

    def draw(self, surface: "pygame.Surface", theme: "ColorTheme") -> None:
        factory = theme.graphics_factory
        font_revision = factory.font_revision()
        visual_key = (self.style, self.text_on, self.text_off, self.font_role, self.rect.width, self.rect.height, font_revision)
        if self._visuals_off is None or self._visuals_on is None or self._visual_key != visual_key:
            start = perf_counter()
            self._visuals_off = factory.build_interactive_visuals(
                self.style,
                self.text_off,
                self.rect,
                font_role=self.font_role,
            )
            self._visuals_on = factory.build_interactive_visuals(
                self.style,
                self.text_on,
                self.rect,
                font_role=self.font_role,
            )
            self._visual_key = visual_key
            first_frame_profiler().record_once(
                "control.first_draw",
                f"toggle:{self.control_id}",
                (perf_counter() - start) * 1000.0,
                detail=f"style={self.style} size={self.rect.width}x{self.rect.height}",
            )
        visuals = self._visuals_on if self.pushed else self._visuals_off
        selected = factory.resolve_visual_state(
            visuals,
            visible=self.visible,
            enabled=self.enabled,
            # Pushed toggles are rendered in armed state; keyboard activation hint
            # temporarily arms the current pushed/unpushed state as well.
            armed=self.pushed or self._focus_activation_armed,
            hovered=self.hovered,
        )
        surface.blit(selected, self.rect)
