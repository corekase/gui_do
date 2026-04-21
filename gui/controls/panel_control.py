from typing import List

from pygame import Rect
from pygame.draw import rect as draw_rect

from ..core.ui_node import UiNode


class PanelControl(UiNode):
    """Container control that owns child controls."""

    def __init__(self, control_id: str, rect: Rect) -> None:
        super().__init__(control_id, rect)
        self.children: List[UiNode] = []

    def add(self, child: UiNode) -> UiNode:
        """Attach one child control and return it."""
        child.parent = self
        self.children.append(child)
        return child

    def update(self, dt_seconds: float) -> None:
        for child in self.children:
            if child.visible:
                child.update(dt_seconds)

    def handle_event(self, event, app) -> bool:
        for child in reversed(self.children):
            if child.visible and child.enabled and child.handle_event(event, app):
                return True
        return False

    def draw(self, surface, theme) -> None:
        draw_rect(surface, theme.medium, self.rect, 0)
        draw_rect(surface, theme.dark, self.rect, 2)
        for child in self.children:
            if child.visible:
                child.draw(surface, theme)
