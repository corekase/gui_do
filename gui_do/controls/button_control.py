from typing import Callable, Optional
from typing import TYPE_CHECKING
from time import perf_counter

import pygame
from pygame import Rect

from ..core.gui_event import GuiEvent
from ..core.first_frame_profiler import first_frame_profiler
from ..core.ui_node import UiNode
from ..core.error_handling import logical_error

if TYPE_CHECKING:
    from ..app.gui_application import GuiApplication
    from ..theme.color_theme import ColorTheme


class ButtonControl(UiNode):
    """Clickable push button control."""

    def __init__(
        self,
        control_id: str,
        rect: Rect,
        text: str,
        on_click: Optional[Callable[[], None]] = None,
        style: str = "box",
        font_role: str = "body",
    ) -> None:
        super().__init__(control_id, rect)
        self.text = text
        self.on_click = on_click
        self.style = style
        self._font_role = "body"
        self.font_role = font_role
        self.hovered = False
        self.pressed = False
        self._focus_activation_armed = False
        self._visuals = None
        self._visual_key = None

    @property
    def font_role(self) -> str:
        return self._font_role

    @font_role.setter
    def font_role(self, value: str) -> None:
        next_role = str(value).strip()
        if not next_role:
            raise logical_error("font_role must be a non-empty string", subsystem="gui.controls", operation="ButtonControl.font_role", source_skip_frames=1)
        self._font_role = next_role

    def _invoke_click(self) -> None:
        if self.on_click is not None:
            self.on_click()

    def set_on_click(self, callback: Optional[Callable[[], None]]) -> None:
        """Replace the click callback at runtime. Pass None to remove it."""
        if callback is not None and not callable(callback):
            raise logical_error("on_click callback must be callable or None", subsystem="gui.controls", operation="ButtonControl.set_on_click", source_skip_frames=1)
        self.on_click = callback

    def _on_enabled_changed(self, _old_enabled: bool, _new_enabled: bool) -> None:
        self.hovered = False
        self.pressed = False
        self._focus_activation_armed = False
        super()._on_enabled_changed(_old_enabled, _new_enabled)

    def _on_visibility_changed(self, _old_visible: bool, _new_visible: bool) -> None:
        self.hovered = False
        self.pressed = False
        self._focus_activation_armed = False
        super()._on_visibility_changed(_old_visible, _new_visible)

    def reconcile_hover(self, wants_hover: bool) -> None:
        if self.hovered != wants_hover:
            self.hovered = wants_hover
            self.invalidate()

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

    def handle_event(self, event: GuiEvent, app: "GuiApplication") -> bool:
        if not self.visible or not self.enabled:
            self.hovered = False
            self.pressed = False
            self._focus_activation_armed = False
            return False

        raw = event.pos
        if isinstance(raw, tuple) and len(raw) == 2:
            self.hovered = self.rect.collidepoint(raw)
        if event.is_mouse_down(1):
            if isinstance(raw, tuple) and len(raw) == 2 and self.rect.collidepoint(raw):
                self.pressed = True
                return True
        if event.is_mouse_up(1):
            was_pressed = self.pressed
            self.pressed = False
            if was_pressed and self.hovered:
                self._invoke_click()
                return True
            return was_pressed
        return False

    def draw(self, surface: "pygame.Surface", theme: "ColorTheme") -> None:
        factory = theme.graphics_factory
        font_revision = factory.font_revision()
        visual_key = (self.style, self.text, self.font_role, self.rect.width, self.rect.height, font_revision)
        if self._visuals is None or self._visual_key != visual_key:
            start = perf_counter()
            self._visuals = factory.build_interactive_visuals(self.style, self.text, self.rect, font_role=self.font_role)
            self._visual_key = visual_key
            first_frame_profiler().record_once(
                "control.first_draw",
                f"button:{self.control_id}",
                (perf_counter() - start) * 1000.0,
                detail=f"style={self.style} size={self.rect.width}x{self.rect.height}",
            )
        selected = factory.resolve_visual_state(
            self._visuals,
            visible=self.visible,
            enabled=self.enabled,
            armed=(self.pressed and self.hovered) or self._focus_activation_armed,
            hovered=self.hovered,
        )
        surface.blit(selected, self.rect)
