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
        self._chrome = None
        self._chrome_size = (0, 0, "")

    def title_bar_rect(self) -> Rect:
        return Rect(self.rect.left, self.rect.top, self.rect.width, self.titlebar_height)

    def content_rect(self) -> Rect:
        return Rect(self.rect.left, self.rect.top + self.titlebar_height, self.rect.width, self.rect.height - self.titlebar_height)

    def lower_widget_rect(self) -> Rect:
        if self._chrome is not None:
            lower_rect = self._chrome.lower_widget.get_rect()
            return Rect(self.rect.right - lower_rect.width - 2, self.rect.top + 2, lower_rect.width, lower_rect.height)
        size = max(12, self.titlebar_height - 6)
        return Rect(self.rect.right - size - 4, self.rect.top + 3, size, size)

    def move_by(self, dx: int, dy: int) -> None:
        if dx == 0 and dy == 0:
            return
        self.rect.x += int(dx)
        self.rect.y += int(dy)
        for child in self.children:
            child.rect.x += int(dx)
            child.rect.y += int(dy)

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
        if isinstance(raw, tuple) and len(raw) == 2 and not self.rect.collidepoint(raw):
            return False
        for child in reversed(self.children):
            if child.visible and child.enabled and child.handle_event(event, app):
                return True
        return False

    def draw(self, surface, theme) -> None:
        factory = getattr(theme, "graphics_factory", None)
        if factory is None:
            draw_rect(surface, theme.medium, self.rect, 0)
            title_fill = theme.dark if self.active else theme.medium
            draw_rect(surface, title_fill, self.title_bar_rect(), 0)
            draw_rect(surface, theme.dark, self.rect, 2)
            title_color = theme.text if self.active else theme.highlight
            text_bitmap = theme.render_text(self.title, size=16, title=True, color=title_color, shadow=True)
            surface.blit(text_bitmap, (self.title_bar_rect().left + 8, self.title_bar_rect().top + 2))
        else:
            if self._chrome is None or self._chrome_size != (self.rect.width, self.titlebar_height, self.title):
                self._chrome = factory.build_window_chrome_visuals(self.rect.width, self.titlebar_height, self.title)
                self._chrome_size = (self.rect.width, self.titlebar_height, self.title)
            draw_rect(surface, theme.medium, self.rect, 0)
            title_bitmap = self._chrome.title_bar_active if self.active else self._chrome.title_bar_inactive
            surface.blit(title_bitmap, self.title_bar_rect().topleft)
            draw_rect(surface, theme.dark, self.rect, 2)
            surface.blit(self._chrome.lower_widget, self.lower_widget_rect().topleft)
        for child in self.children:
            if child.visible:
                child.draw(surface, theme)
