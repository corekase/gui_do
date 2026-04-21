from typing import Callable, List, Optional
import pygame
from pygame import Rect
from pygame.draw import rect as draw_rect

from ..core.ui_node import UiNode


class WindowControl(UiNode):
    """Window container with title bar and child controls."""

    def __init__(
        self,
        control_id: str,
        rect: Rect,
        title: str,
        titlebar_height: int = 24,
        preamble: Optional[Callable[[], None]] = None,
        event_handler: Optional[Callable[[object], bool]] = None,
        postamble: Optional[Callable[[], None]] = None,
    ) -> None:
        super().__init__(control_id, rect)
        self.title = title
        self.titlebar_height = max(18, int(titlebar_height))
        self.children: List[UiNode] = []
        self._active = False
        self.parent: Optional[UiNode] = None
        self._chrome = None
        self._chrome_size = (0, 0, "")
        self._disabled_overlay = None
        self._disabled_overlay_size = (0, 0)
        self._preamble = preamble
        self._event_handler = event_handler
        self._postamble = postamble

    def set_lifecycle(self, preamble=None, event_handler=None, postamble=None) -> None:
        self._preamble = preamble
        self._event_handler = event_handler
        self._postamble = postamble

    @property
    def active(self) -> bool:
        return self._active

    @active.setter
    def active(self, value: bool) -> None:
        is_active = bool(value)
        if self._active == is_active:
            return
        if is_active:
            parent = self.parent
            set_active = getattr(parent, "_set_active_window", None) if parent is not None else None
            if callable(set_active):
                set_active(self)
                return
        self._active = is_active

    def title_bar_rect(self) -> Rect:
        lower_rect = self.lower_widget_rect()
        width = max(0, lower_rect.left - self.rect.left)
        return Rect(self.rect.left, self.rect.top, width, self.titlebar_height)

    def content_rect(self) -> Rect:
        return Rect(self.rect.left, self.rect.top + self.titlebar_height, self.rect.width, self.rect.height - self.titlebar_height)

    def lower_widget_rect(self) -> Rect:
        if self._chrome is not None:
            lower_rect = self._chrome.lower_widget.get_rect()
            return Rect(self.rect.right - lower_rect.width, self.rect.top, lower_rect.width, lower_rect.height)
        size = max(12, self.titlebar_height)
        top = self.rect.top
        return Rect(self.rect.right - size, top, size, size)

    def _on_visibility_changed(self, old_visible: bool, new_visible: bool) -> None:
        parent = self.parent
        if parent is None:
            return
        visibility_changed = getattr(parent, "_on_window_visibility_changed", None)
        if callable(visibility_changed):
            visibility_changed(self, old_visible, new_visible)
            return
        if old_visible or not new_visible:
            return
        raise_window = getattr(parent, "_raise_window", None)
        if callable(raise_window):
            raise_window(self)
            return
        children = getattr(parent, "children", None)
        if isinstance(children, list) and self in children:
            children.remove(self)
            children.append(self)

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
        if self._preamble is not None:
            self._preamble()
        for child in self.children:
            if child.visible:
                child.update(dt_seconds)
        if self._postamble is not None:
            self._postamble()

    def handle_event(self, event, app) -> bool:
        def _owns_node(target) -> bool:
            if target is None:
                return False
            if target is self:
                return True
            pending = list(self.children)
            while pending:
                node = pending.pop()
                if node is target:
                    return True
                children = getattr(node, "children", None)
                if isinstance(children, list) and children:
                    pending.extend(children)
            return False

        raw = getattr(event, "pos", None)
        if isinstance(raw, tuple) and len(raw) == 2 and not self.rect.collidepoint(raw):
            lock_object = getattr(app, "locking_object", None)
            lock_active = bool(getattr(app, "mouse_point_locked", False) and getattr(app, "lock_point_pos", None) is not None)
            if not (lock_active and _owns_node(lock_object)):
                return False
        if self._event_handler is not None and self._event_handler(event):
            return True
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
                chrome_height = self._chrome.title_bar_active.get_height()
                self.titlebar_height = max(18, chrome_height)
                self._chrome_size = (self.rect.width, self.titlebar_height, self.title)
            draw_rect(surface, theme.medium, self.rect, 0)
            title_bitmap = self._chrome.title_bar_inactive if self.active else self._chrome.title_bar_active
            title_rect = self.title_bar_rect()
            source_rect = Rect(0, 0, title_rect.width, title_rect.height)
            surface.blit(title_bitmap, title_rect.topleft, source_rect)
            draw_rect(surface, theme.dark, self.rect, 2)
            surface.blit(self._chrome.lower_widget, self.lower_widget_rect().topleft)
            if not self.enabled:
                overlay_size = (self.rect.width, self.rect.height)
                if self._disabled_overlay is None or self._disabled_overlay_size != overlay_size:
                    self._disabled_overlay = factory.build_disabled_bitmap(self._chrome.title_bar_inactive)
                    wash = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
                    wash.fill((50, 50, 50, 120))
                    self._disabled_overlay = wash
                    self._disabled_overlay_size = overlay_size
                surface.blit(self._disabled_overlay, self.rect.topleft)
        for child in self.children:
            if child.visible:
                child.draw(surface, theme)
