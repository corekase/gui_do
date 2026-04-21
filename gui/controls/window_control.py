from typing import List, Optional
from pygame import Rect
from pygame.draw import rect as draw_rect

from ..core.ui_node import UiNode


class WindowControl(UiNode):
    """Window container with title bar and child controls."""

    def __init__(self, control_id: str, rect: Rect, title: str, titlebar_height: int = 24) -> None:
        super().__init__(control_id, rect)
        self.title = title
        self.titlebar_height = max(18, int(titlebar_height))
        self.children: List[UiNode] = []
        self.active = False
        self.parent: Optional[UiNode] = None

    def title_bar_rect(self) -> Rect:
        return Rect(self.rect.left, self.rect.top, self.rect.width, self.titlebar_height)

    def content_rect(self) -> Rect:
        return Rect(self.rect.left, self.rect.top + self.titlebar_height, self.rect.width, self.rect.height - self.titlebar_height)

    def add(self, child: UiNode) -> UiNode:
        child.parent = self
        self.children.append(child)
        return child

    def update(self, dt_seconds: float) -> None:
        for child in self.children:
            if child.visible:
                child.update(dt_seconds)

    def handle_event(self, event, app) -> bool:
        raw = getattr(event, "pos", None)
        if isinstance(raw, tuple) and len(raw) == 2 and self.title_bar_rect().collidepoint(raw):
            self.active = True
        for child in reversed(self.children):
            if child.visible and child.enabled and child.handle_event(event, app):
                return True
        return False

    def draw(self, surface, theme) -> None:
        draw_rect(surface, theme.medium, self.rect, 0)
        title_fill = theme.dark if self.active else theme.medium
        draw_rect(surface, title_fill, self.title_bar_rect(), 0)
        draw_rect(surface, theme.dark, self.rect, 2)
        title_color = theme.text if self.active else theme.highlight
        text_bitmap = theme.render_text(self.title, size=16, title=True, color=title_color, shadow=True)
        surface.blit(text_bitmap, (self.title_bar_rect().left + 8, self.title_bar_rect().top + 2))
        for child in self.children:
            if child.visible:
                child.draw(surface, theme)
