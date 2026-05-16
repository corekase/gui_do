from typing import Optional
from typing import TYPE_CHECKING
from time import perf_counter
import pygame
from pygame import Rect
from pygame.draw import rect as draw_rect

from ...events.gui_event import GuiEvent
from ...app.first_frame_profiler import first_frame_profiler
from ..base.ui_node import UiNode
from ...graphics import load_pristine_surface
from ...app.error_handling import logical_error

if TYPE_CHECKING:
    from ...app.gui_application import GuiApplication
    from ...theme.color_theme import ColorTheme


class _WindowContentHost(UiNode):
    """Content-layer host mounted inside a window's body area."""

    def add(self, child: UiNode) -> UiNode:
        return self.add_child(child)

    def remove(self, child: UiNode, *, dispose: bool = False) -> bool:
        return self.remove_child(child, dispose=dispose)

    def clear(self, *, dispose: bool = False) -> int:
        return self.clear_children(dispose=dispose)

    def update(self, dt_seconds: float) -> None:
        for child in self.children:
            if child.visible:
                child.update(dt_seconds)

    def on_event_capture(self, event: GuiEvent, app: "GuiApplication", theme=None) -> bool:
        return self._dispatch_children(event, app, reverse=False, theme=theme)

    def handle_event(self, event: GuiEvent, app: "GuiApplication", theme=None) -> bool:
        return self._dispatch_children(event, app, reverse=True, theme=theme)

    def on_event_bubble(self, event: GuiEvent, app: "GuiApplication", theme=None) -> bool:
        return self._dispatch_children(event, app, reverse=True, theme=theme)

    def draw(self, surface: pygame.Surface, theme: "ColorTheme") -> None:
        for child in self.children:
            if child.visible:
                child.draw(surface, theme)



class WindowControl(UiNode):

    # --- Shear window effects drag event hooks ---
    def on_titlebar_drag_start(self, mouse_pos, surface=None):
        """
        Called when the user starts dragging the window via the title bar.
        If shear_wobble_enabled is enabled, start the shear effect.
        """
        if getattr(self, 'window_effects', {}).get('shear_wobble_enabled', True):
            if self.shear_controller is None:
                # Lazy import to avoid circular dependency
                from ...graphics.shear_window import ShearWindowController
                self.shear_controller = ShearWindowController(self, getattr(self, 'window_effects', None))
            self.shear_controller.start_drag(mouse_pos, surface)
            self.shear_active = True
        else:
            self.shear_active = False
        # Existing drag logic continues here

    def on_titlebar_drag_update(self, mouse_pos):
        """
        Called on each drag update (mouse move) while dragging the title bar.
        """
        if self.shear_active and self.shear_controller:
            self.shear_controller.update_drag(mouse_pos)
        # Existing drag update logic continues here

    def on_titlebar_drag_end(self, mouse_pos=None):
        """
        Called when the user releases the drag on the title bar.
        """
        if self.shear_active and self.shear_controller:
            self.shear_controller.end_drag(mouse_pos)
            self.shear_active = self.shear_controller.is_active()
        # Existing drag end logic continues here


        # --- Shear windows effect integration ---
        shear_controller = None  # type: Optional[object]
        shear_active = False

    """Window container with title bar and child controls."""

    presenter: Optional[object] = None
    _TITLEBAR_MIN_HEIGHT = 14
    _TITLEBAR_VERTICAL_PADDING = 8

    def set_presenter(self, presenter) -> None:
        """Attach a presenter/controller to this window."""
        if self.presenter is presenter:
            return
        previous = self.presenter
        self.presenter = presenter
        if previous is not None and hasattr(previous, "on_detach"):
            previous.on_detach(self)
        if presenter is None:
            return
        presenter.window = self
        if hasattr(presenter, "on_attach"):
            presenter.on_attach(self)
        if hasattr(presenter, "on_create"):
            presenter.on_create()

    def __init__(
        self,
        control_id: str,
        rect: Rect,
        title: str,
        titlebar_height: int = 24,
        title_font_role: str = "title",
        use_frame_backdrop: bool = False,
    ) -> None:
        super().__init__(control_id, rect)
        self.title = title
        self.titlebar_height = max(self._TITLEBAR_MIN_HEIGHT, int(titlebar_height))
        self.title_font_role = title_font_role
        self._active = False
        self.parent: Optional[UiNode] = None
        self._chrome = None
        self._chrome_size = (0, 0, "")
        self._disabled_overlay = None
        self._disabled_overlay_size = (0, 0)
        self._pristine = None
        if not use_frame_backdrop:
            self._pristine = pygame.Surface((self.rect.width, self.rect.height))
            self._pristine.fill((0, 0, 0))
        self._pristine_scaled = None
        self._pristine_scaled_size = (0, 0)
        self._frame_visuals = None
        self._frame_visual_size = (0, 0)
        self._content_host = _WindowContentHost(f"{self.control_id}__content", self.content_rect())
        self._content_host_rect_dirty = False
        super().add_child(self._content_host)

        # Shear effect: initialize controller if enabled in spec (integration to be completed)
        self.shear_controller = None
        self.shear_active = False
        # Actual instantiation and event hookup will be handled in drag logic

    def _mark_content_host_rect_dirty(self) -> None:
        self._content_host_rect_dirty = True

    def _sync_content_host_rect(self) -> None:
        if not self._content_host_rect_dirty:
            return
        content_rect = self.content_rect()
        if self._content_host.rect != content_rect:
            self._content_host.rect = Rect(content_rect)
        self._content_host_rect_dirty = False

    def _notify_presenter_resized(self) -> None:
        if self.presenter is not None and hasattr(self.presenter, "on_resize"):
            self.presenter.on_resize(Rect(self.rect))

    def resize(self, width: int, height: int) -> None:
        previous = Rect(self.rect)
        super().resize(width, height)
        self._mark_content_host_rect_dirty()
        self._sync_content_host_rect()
        if self.rect.size != previous.size:
            self._notify_presenter_resized()

    def set_pos(self, x: int, y: int) -> None:
        previous = self.rect.topleft
        super().set_pos(x, y)
        if self.rect.topleft != previous:
            self._mark_content_host_rect_dirty()
            self._sync_content_host_rect()

    def set_rect(self, rect: Rect) -> None:
        previous = Rect(self.rect)
        super().set_rect(rect)
        self._mark_content_host_rect_dirty()
        self._sync_content_host_rect()
        if self.rect.size != previous.size:
            self._notify_presenter_resized()

    @property
    def title_font_role(self) -> str:
        return self._title_font_role

    @title_font_role.setter
    def title_font_role(self, value: str) -> None:
        next_role = str(value).strip()
        if not next_role:
            raise logical_error("title_font_role must be a non-empty string", subsystem="gui.controls", operation="WindowControl.title_font_role", source_skip_frames=1)
        self._title_font_role = next_role

    def is_window(self) -> bool:
        return True

    def set_active(self, value: bool) -> None:
        self._active = bool(value)

    def set_pristine(self, source) -> None:
        self._pristine = load_pristine_surface(source)
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
            if not (self.visible and self.enabled):
                self._active = False
                return
            parent = self.parent
            if parent is not None:
                parent._set_active_window(self)
                return
        self._active = is_active

    def title_bar_rect(self) -> Rect:
        # Calculate the titlebar width as the window width minus the lower control width (if present and valid)
        lower_rect = self.lower_control_rect()
        lower_left = lower_rect.left if lower_rect.left > self.rect.left else self.rect.right
        width = max(0, lower_left - self.rect.left)
        # Fallback: if lower control is missing or overlaps, use the full width
        if width == 0 or width > self.rect.width or lower_left > self.rect.right or lower_left <= self.rect.left:
            width = self.rect.width
        return Rect(self.rect.left, self.rect.top, width, self.titlebar_height)

    def _fit_titlebar_height_to_font(self, theme: "ColorTheme") -> None:
        """Keep titlebar height aligned to title font metrics for vertical centering."""
        try:
            font_instance = theme.fonts.font_instance(self.title_font_role)
            line_height = int(font_instance.line_height)
        except Exception:
            return

        fitted_height = max(
            self._TITLEBAR_MIN_HEIGHT,
            line_height + self._TITLEBAR_VERTICAL_PADDING,
        )
        if fitted_height == self.titlebar_height:
            return
        self.titlebar_height = fitted_height
        self._mark_content_host_rect_dirty()
        self._sync_content_host_rect()
        self._notify_presenter_resized()

    def content_rect(self) -> Rect:
        return Rect(
            self.rect.left,
            self.rect.top + self.titlebar_height,
            max(1, self.rect.width),
            max(1, self.rect.height - self.titlebar_height),
        )

    def lower_control_rect(self) -> Rect:
        if self._chrome is not None:
            lower_rect = self._chrome.lower_control.get_rect()
            return Rect(self.rect.right - lower_rect.width, self.rect.top, lower_rect.width, lower_rect.height)
        size = max(12, self.titlebar_height)
        top = self.rect.top
        return Rect(self.rect.right - size, top, size, size)

    def _on_visibility_changed(self, old_visible: bool, new_visible: bool) -> None:
        if self.presenter is not None:
            if new_visible and hasattr(self.presenter, "on_show"):
                self.presenter.on_show()
            if not new_visible and hasattr(self.presenter, "on_hide"):
                self.presenter.on_hide()
            if not new_visible and hasattr(self.presenter, "on_close"):
                self.presenter.on_close()
        parent = self.parent
        if parent is None:
            return
        parent._on_window_visibility_changed(self, old_visible, new_visible)

    def _on_enabled_changed(self, old_enabled: bool, new_enabled: bool) -> None:
        parent = self.parent
        if parent is None:
            return
        parent._on_window_enabled_changed(self, old_enabled, new_enabled)

    def close(self) -> None:
        """Hide this window, releasing active state and drag ownership.

        Equivalent to setting ``visible = False`` but provides a clear,
        intent-revealing API consistent with standard GUI window semantics.
        """
        self.visible = False

    def move_by(self, dx: int, dy: int) -> None:
        if dx == 0 and dy == 0:
            return
        self.rect.x += int(dx)
        self.rect.y += int(dy)

        def _move_subtree(node: UiNode) -> None:
            node.rect.x += int(dx)
            node.rect.y += int(dy)
            for descendant in node.children:
                _move_subtree(descendant)

        for child in self.children:
            _move_subtree(child)

    def add(self, child: UiNode) -> UiNode:
        return self._content_host.add(child)

    def add_child(self, child: UiNode) -> UiNode:
        if child is self._content_host:
            return super().add_child(child)
        return self._content_host.add(child)

    def remove(self, child: UiNode, *, dispose: bool = False) -> bool:
        return self._content_host.remove(child, dispose=dispose)

    def remove_child(self, child: UiNode, *, dispose: bool = False) -> bool:
        if child is self._content_host:
            return super().remove_child(child, dispose=dispose)
        return self._content_host.remove(child, dispose=dispose)

    def clear_children(self, *, dispose: bool = False) -> int:
        """Remove all direct children and return the count removed.

        Pass ``dispose=True`` to also call ``dispose()`` on every removed child.
        """
        return self._content_host.clear(dispose=dispose)

    def update(self, dt_seconds: float) -> None:
        self._sync_content_host_rect()
        if self.presenter is not None and hasattr(self.presenter, "before_update"):
            self.presenter.before_update(dt_seconds)
        for child in self.children:
            if child.visible:
                child.update(dt_seconds)
        if self.presenter is not None and hasattr(self.presenter, "update"):
            self.presenter.update(dt_seconds)
        if self.presenter is not None and hasattr(self.presenter, "after_update"):
            self.presenter.after_update(dt_seconds)

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

    def _accepts_content_scope(self, event: GuiEvent, app: "GuiApplication") -> bool:
        raw = event.pos
        content = self.content_rect()
        if isinstance(raw, tuple) and len(raw) == 2 and not content.collidepoint(raw):
            lock_object = app.locking_object
            lock_active = bool(app.mouse_point_locked and app.lock_point_pos is not None)
            if not (lock_active and self._owns_node(lock_object)):
                return False
        return True

    def _dispatch_window_handler(self, event: GuiEvent) -> bool:
        if self.presenter is not None and hasattr(self.presenter, "handle_event"):
            if self.presenter.handle_event(event):
                event.prevent_default()
                event.stop_propagation()
                return True
        return False

    def on_event_capture(self, event: GuiEvent, app: "GuiApplication", theme=None) -> bool:
        if not self._accepts_event_scope(event, app):
            return False
        if not self._accepts_content_scope(event, app):
            return False
        return self._dispatch_children(event, app, reverse=False, theme=theme)

    def handle_event(self, event: GuiEvent, app: "GuiApplication", theme=None) -> bool:
        if not self._accepts_event_scope(event, app):
            return False
        if self._dispatch_window_handler(event):
            return True
        if not self._accepts_content_scope(event, app):
            return False
        return self._dispatch_children(event, app, reverse=True, theme=theme)

    def on_event_bubble(self, event: GuiEvent, app: "GuiApplication", theme=None) -> bool:
        if not self._accepts_event_scope(event, app):
            return False
        if not self._accepts_content_scope(event, app):
            return False
        return self._dispatch_children(event, app, reverse=True, theme=theme)

    def _draw_standard(self, surface: pygame.Surface, theme: "ColorTheme") -> None:
        self._sync_content_host_rect()
        self._fit_titlebar_height_to_font(theme)
        factory = theme.graphics_factory
        font_revision = factory.font_revision()
        if not self.restore_pristine(surface):
            self._draw_default_window_background(surface, theme, factory)
        chrome_key = (self.rect.width, self.titlebar_height, self.title, self.title_font_role, font_revision)
        if self._chrome is None or self._chrome_size != chrome_key:
            start = perf_counter()
            self._chrome = factory.build_window_chrome_visuals(
                self.rect.width,
                self.titlebar_height,
                self.title,
                title_font_role=self.title_font_role,
            )
            old_titlebar_height = self.titlebar_height
            chrome_height = self._chrome.title_bar_active.get_height()
            self.titlebar_height = max(self._TITLEBAR_MIN_HEIGHT, chrome_height)
            if self.titlebar_height != old_titlebar_height:
                self._sync_content_host_rect()
                self._notify_presenter_resized()
            self._chrome_size = (self.rect.width, self.titlebar_height, self.title, self.title_font_role, font_revision)
            first_frame_profiler().record_once(
                "control.first_draw",
                f"window:{self.control_id}",
                (perf_counter() - start) * 1000.0,
                detail=f"title={self.title}",
            )
        title_bitmap = self._chrome.title_bar_active if self.active else self._chrome.title_bar_inactive
        title_rect = self.title_bar_rect()
        source_rect = Rect(0, 0, title_rect.width, title_rect.height)
        surface.blit(title_bitmap, title_rect.topleft, source_rect)
        draw_rect(surface, theme.dark, self.rect, 2)
        surface.blit(self._chrome.lower_control, self.lower_control_rect().topleft)

        # Debug overlay removed; normal rendering restored.

        if not self.enabled:
            overlay_size = (self.rect.width, self.rect.height)
            if self._disabled_overlay is None or self._disabled_overlay_size != overlay_size:
                wash = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
                wash.fill((50, 50, 50, 120))
                self._disabled_overlay = wash
                self._disabled_overlay_size = overlay_size
            surface.blit(self._disabled_overlay, self.rect.topleft)
        previous_clip = surface.get_clip()
        content_clip = self.content_rect()
        clip_rect = previous_clip.clip(content_clip)
        surface.set_clip(clip_rect)
        try:
            for child in self.children:
                if child.visible:
                    child.draw(surface, theme)
        finally:
            surface.set_clip(previous_clip)

    def draw(self, surface: pygame.Surface, theme: "ColorTheme") -> None:
        # If shear effect is active, render from a fresh per-frame snapshot.
        if self.shear_active and self.shear_controller:
            self.shear_controller.render(surface, theme, self._draw_standard)
            self.shear_active = self.shear_controller.is_active()
            return
        self._draw_standard(surface, theme)
