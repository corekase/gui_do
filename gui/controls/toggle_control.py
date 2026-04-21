from typing import Callable, Optional
from typing import TYPE_CHECKING

from pygame import Rect
from pygame.locals import MOUSEBUTTONDOWN

from ..core.gui_event import GuiEvent
from ..core.ui_node import UiNode

if TYPE_CHECKING:
    import pygame
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
    ) -> None:
        super().__init__(control_id, rect)
        self.text_on = text_on
        self.text_off = text_off if text_off is not None else text_on
        self.pushed = bool(pushed)
        self.on_toggle = on_toggle
        self.style = style
        self.hovered = False
        self._visuals = None
        self._visual_key = None

    def handle_event(self, event: GuiEvent, _app) -> bool:
        raw = event.pos
        if isinstance(raw, tuple) and len(raw) == 2:
            self.hovered = self.rect.collidepoint(raw)
        if event.type == MOUSEBUTTONDOWN and event.button == 1:
            if isinstance(raw, tuple) and len(raw) == 2 and self.rect.collidepoint(raw):
                self.pushed = not self.pushed
                if self.on_toggle is not None:
                    self.on_toggle(self.pushed)
                return True
        return False

    def draw(self, surface: "pygame.Surface", theme: "ColorTheme") -> None:
        factory = theme.graphics_factory
        visual_key = (self.style, self.text_on, self.text_off, self.rect.width, self.rect.height)
        if self._visuals is None or self._visual_key != visual_key:
            self._visuals = factory.build_toggle_visuals(self.style, self.text_on, self.text_off, self.rect)
            self._visual_key = visual_key
        selected = factory.resolve_visual_state(
            self._visuals,
            visible=self.visible,
            enabled=self.enabled,
            armed=self.pushed,
            hovered=self.hovered,
        )
        surface.blit(selected, self.rect)
