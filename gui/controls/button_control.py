from typing import Callable, Optional
from typing import TYPE_CHECKING

from pygame import Rect

from ..core.gui_event import GuiEvent
from ..core.ui_node import UiNode

if TYPE_CHECKING:
    import pygame
    from ..app.gui_application import GuiApplication
    from ..theme.color_theme import ColorTheme


class ButtonControl(UiNode):
    """Clickable push button control."""

    def __init__(self, control_id: str, rect: Rect, text: str, on_click: Optional[Callable[[], None]] = None, style: str = "box") -> None:
        super().__init__(control_id, rect)
        self.text = text
        self.on_click = on_click
        self.style = style
        self.hovered = False
        self.pressed = False
        self._visuals = None
        self._visual_key = None

    def handle_event(self, event: GuiEvent, app: "GuiApplication") -> bool:
        if not self.visible or not self.enabled:
            self.hovered = False
            self.pressed = False
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
                if self.on_click is not None:
                    self.on_click()
                return True
            return was_pressed
        return False

    def draw(self, surface: "pygame.Surface", theme: "ColorTheme") -> None:
        factory = theme.graphics_factory
        visual_key = (self.style, self.text, self.rect.width, self.rect.height)
        if self._visuals is None or self._visual_key != visual_key:
            self._visuals = factory.build_interactive_visuals(self.style, self.text, self.rect)
            self._visual_key = visual_key
        selected = factory.resolve_visual_state(
            self._visuals,
            visible=self.visible,
            enabled=self.enabled,
            armed=self.pressed and self.hovered,
            hovered=self.hovered,
        )
        surface.blit(selected, self.rect)
