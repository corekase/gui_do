from typing import Callable, List, Optional
from typing import TYPE_CHECKING
from pathlib import Path
import pygame
from pygame import Rect
from pygame.draw import rect as draw_rect

from ..core.gui_event import EventPhase, GuiEvent
from ..core.ui_node import UiNode

if TYPE_CHECKING:
    from ..app.gui_application import GuiApplication
    from ..theme.color_theme import ColorTheme


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
        self._pristine = None
        self._pristine_scaled = None
        self._pristine_scaled_size = (0, 0)
        self._frame_visuals = None
        self._frame_visual_size = (0, 0)

    def set_lifecycle(self, preamble=None, event_handler=None, postamble=None) -> None:
        self._preamble = preamble
        self._event_handler = event_handler
        self._postamble = postamble

    def is_window(self) -> bool:
        return True

    def set_active(self, value: bool) -> None:
        self._active = bool(value)

    @staticmethod
    def _load_pristine_surface(source):
        if source is None:
            return None
        if isinstance(source, pygame.Surface):
            return source.convert()
        if isinstance(source, (str, Path)):
            candidate = Path(source)
            if not candidate.is_absolute():
                root = Path(__file__).resolve().parents[2]
                candidate = root / "data" / "images" / str(source)
            return pygame.image.load(str(candidate)).convert()
        raise TypeError("pristine source must be a Surface or path-like string")

    def set_pristine(self, source) -> None:
        self._pristine = self._load_pristine_surface(source)
        self._pristine_scaled = None
        self._pristine_scaled_size = (0, 0)

    def restore_pristine(self, surface) -> bool:
        if self._pristine is None:
            return False
        target_size = (self.rect.width, self.rect.height)
        bitmap = self._pristine
        if bitmap.get_size() != target_size:
            if self._pristine_scaled is None or self._pristine_scaled_size != target_size:
                self._pristine_scaled = pygame.transform.smoothscale(bitmap, target_size)
                self._pristine_scaled_size = target_size
            bitmap = self._pristine_scaled
        surface.blit(bitmap, self.rect.topleft)
        return True

    def _draw_default_window_background(self, surface, theme, factory) -> None:
        visual_size = (self.rect.width, self.rect.height)
        if self._frame_visuals is None or self._frame_visual_size != visual_size:
            self._frame_visuals = factory.build_frame_visuals(self.rect)
            self._frame_visual_size = visual_size
        selected = factory.resolve_visual_state(
            self._frame_visuals,
            visible=self.visible,
            enabled=self.enabled,
            armed=False,
            hovered=False,
        )
        surface.blit(selected, self.rect)

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
            if parent is not None:
                parent._set_active_window(self)
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
        parent._on_window_visibility_changed(self, old_visible, new_visible)

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
        if hasattr(child, "on_mount"):
            child.on_mount(self)
        if hasattr(child, "invalidate"):
            child.invalidate()
        return child

    def remove(self, child: UiNode, *, dispose: bool = False) -> bool:
        if child not in self.children:
            return False
        self.children.remove(child)
        child.parent = None
        if hasattr(child, "on_unmount"):
            child.on_unmount(self)
        if dispose:
            if hasattr(child, "dispose"):
                child.dispose()
        if hasattr(self, "invalidate"):
            self.invalidate()
        return True

    def update(self, dt_seconds: float) -> None:
        if self._preamble is not None:
            self._preamble()
        for child in self.children:
            if child.visible:
                child.update(dt_seconds)
        if self._postamble is not None:
            self._postamble()

    def _owns_node(self, target) -> bool:
        if target is None:
            return False
        if target is self:
            return True
        pending = list(self.children)
        while pending:
            node = pending.pop()
            if node is target:
                return True
            pending.extend(node.children)
        return False

    def _accepts_event_scope(self, event: GuiEvent, app: "GuiApplication") -> bool:
        raw = event.pos
        if isinstance(raw, tuple) and len(raw) == 2 and not self.rect.collidepoint(raw):
            lock_object = app.locking_object
            lock_active = bool(app.mouse_point_locked and app.lock_point_pos is not None)
            if not (lock_active and self._owns_node(lock_object)):
                return False
        return True

    @staticmethod
    def _dispatch_child_event(child: UiNode, event: GuiEvent, app: "GuiApplication") -> bool:
        if hasattr(child, "handle_routed_event"):
            return bool(child.handle_routed_event(event, app))
        if event.phase is EventPhase.TARGET and hasattr(child, "handle_event"):
            return bool(child.handle_event(event, app))
        return False

    def _dispatch_children(self, event: GuiEvent, app: "GuiApplication", *, reverse: bool) -> bool:
        ordered = list(reversed(self.children)) if reverse else list(self.children)
        for child in ordered:
            if not (child.visible and child.enabled):
                continue
            if self._dispatch_child_event(child, event, app):
                return True
            if event.propagation_stopped:
                return True
        return False

    def on_event_capture(self, event: GuiEvent, app: "GuiApplication") -> bool:
        if not self._accepts_event_scope(event, app):
            return False
        return self._dispatch_children(event, app, reverse=False)

    def handle_event(self, event: GuiEvent, app: "GuiApplication") -> bool:
        if not self._accepts_event_scope(event, app):
            return False
        if self._event_handler is not None and self._event_handler(event):
            event.prevent_default()
            event.stop_propagation()
            return True
        return self._dispatch_children(event, app, reverse=True)

    def on_event_bubble(self, event: GuiEvent, app: "GuiApplication") -> bool:
        if not self._accepts_event_scope(event, app):
            return False
        return self._dispatch_children(event, app, reverse=True)

    def draw(self, surface: pygame.Surface, theme: "ColorTheme") -> None:
        factory = theme.graphics_factory
        if not self.restore_pristine(surface):
            self._draw_default_window_background(surface, theme, factory)
        if self._chrome is None or self._chrome_size != (self.rect.width, self.titlebar_height, self.title):
            self._chrome = factory.build_window_chrome_visuals(self.rect.width, self.titlebar_height, self.title)
            chrome_height = self._chrome.title_bar_active.get_height()
            self.titlebar_height = max(18, chrome_height)
            self._chrome_size = (self.rect.width, self.titlebar_height, self.title)
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
