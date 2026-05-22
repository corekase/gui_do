from typing import Optional
from typing import TYPE_CHECKING
from time import perf_counter
import pygame
from pygame import Rect
from pygame.draw import rect as draw_rect

from ...events.gui_event import GuiEvent
from ...app.first_frame_profiler import first_frame_profiler
from ..base.ui_node import UiNode
from ..input.image_button_control import ImageButtonControl
from ...graphics import load_pristine_surface
from ...graphics.window_visibility_transition import WindowVisibilityTransitionController
from ...app.screen_util import get_screen_size
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
        If shear_enabled is enabled, start the shear effect.
        """
        effects = self._resolved_window_effects()
        if effects.get('shear_enabled', True):
            if self.shear_controller is None:
                # Lazy import to avoid circular dependency
                from ...graphics.shear_window import ShearWindowController
                self.shear_controller = ShearWindowController(self)
            self.shear_controller.start_drag(mouse_pos, surface)
            self.shear_active = True
        else:
            self.shear_active = False
        # Existing drag logic continues here

    def on_titlebar_drag_update(self, mouse_pos, *, blocked: bool = False):
        """
        Called on each drag update (mouse move) while dragging the title bar.
        """
        if self.shear_active and self.shear_controller:
            update_drag = getattr(self.shear_controller, "update_drag", None)
            if update_drag is not None:
                try:
                    update_drag(mouse_pos, blocked=blocked)
                except TypeError:
                    update_drag(mouse_pos)
        # Existing drag update logic continues here

    def on_titlebar_drag_end(self, mouse_pos=None, *, blocked: bool = False):
        """
        Called when the user releases the drag on the title bar.
        """
        if self.shear_active and self.shear_controller:
            end_drag = getattr(self.shear_controller, "end_drag", None)
            if end_drag is not None:
                try:
                    end_drag(mouse_pos, blocked=blocked)
                except TypeError:
                    end_drag(mouse_pos)
            self.shear_active = self.shear_controller.is_active()
        # Existing drag end logic continues here

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
        size: tuple[int, int],
        title: str,
        titlebar_height: int = 24,
        title_font_role: str = "title",
        use_frame_backdrop: bool = False,
        titlebar_controls: dict | object | None = None,
    ) -> None:
        # Window size represents content/body size; titlebar height is added on top.
        content_width = max(1, int(size[0]))
        content_height = max(1, int(size[1]))
        self._content_size = (content_width, content_height)
        total_height = content_height + max(self._TITLEBAR_MIN_HEIGHT, int(titlebar_height))
        rect = Rect(0, 0, content_width, total_height)
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
        placeholder = pygame.Surface((1, 1), pygame.SRCALPHA)
        self._lower_control_button = ImageButtonControl(
            f"{control_id}__lower_order",
            Rect(0, 0, 1, 1),
            placeholder,
            placeholder,
            placeholder,
            on_click=self._queue_lower_control_click,
        )
        self._hide_control_button = ImageButtonControl(
            f"{control_id}__hide",
            Rect(0, 0, 1, 1),
            placeholder,
            placeholder,
            placeholder,
            on_click=self._on_hide_control_click,
        )
        self._hide_control_visual_size = (0, 0)
        self._lower_control_visual_size = (0, 0)
        self._titlebar_control_requests: list[str] = []
        self.set_titlebar_controls(titlebar_controls)
        self._content_host = _WindowContentHost(f"{self.control_id}__content", self.content_rect())
        self._content_host_rect_dirty = False
        super().add_child(self._content_host)

        # Shear effect: initialize controller if enabled in spec (integration to be completed)
        self.shear_controller = None
        self.shear_active = False
        self.visibility_transition_controller: Optional[WindowVisibilityTransitionController] = None
        # Actual instantiation and event hookup will be handled in drag logic

    def ensure_visibility_transition_controller(self) -> WindowVisibilityTransitionController:
        controller = self.visibility_transition_controller
        if controller is None:
            controller = WindowVisibilityTransitionController(self)
            self.visibility_transition_controller = controller
        return controller

    def is_visibility_transition_active(self) -> bool:
        controller = self.visibility_transition_controller
        return bool(controller is not None and controller.is_active())

    def is_visibility_transition_renderable(self) -> bool:
        controller = self.visibility_transition_controller
        return bool(controller is not None and controller.should_render())

    def begin_visibility_transition(self, visible: bool, *, app=None, binding=None) -> None:
        effects = self._resolved_window_effects()
        hide_show_enabled = bool(effects.get("hide_show_enabled", False))
        grow_shrink_enabled = bool(effects.get("grow_shrink_enabled", False))
        if hide_show_enabled and grow_shrink_enabled:
            raise logical_error(
                "window visibility transition must enable at most one of hide_show_enabled or grow_shrink_enabled",
                subsystem="gui.controls",
                operation="WindowControl.begin_visibility_transition",
                details={"window_effects": effects},
                source_skip_frames=1,
            )
        if not hide_show_enabled and not grow_shrink_enabled:
            return
        controller = self.ensure_visibility_transition_controller()
        transition_mode = "hide_show" if hide_show_enabled else "grow_shrink"
        controller.begin_transition(bool(visible), app=app, binding=binding, mode=transition_mode)

    def _resolved_window_effects(self) -> dict:
        raw = getattr(self, "window_effects", None)
        if isinstance(raw, dict):
            source = raw
        else:
            source = {
                "shear_enabled": getattr(raw, "shear_enabled", None),
                "hide_show_enabled": getattr(raw, "hide_show_enabled", None),
                "grow_shrink_enabled": getattr(raw, "grow_shrink_enabled", None),
            }
        return {
            "shear_enabled": True if source.get("shear_enabled") is None else bool(source.get("shear_enabled")),
            "hide_show_enabled": False if source.get("hide_show_enabled") is None else bool(source.get("hide_show_enabled")),
            "grow_shrink_enabled": False if source.get("grow_shrink_enabled") is None else bool(source.get("grow_shrink_enabled")),
        }

    def release_visibility_transition_resources(self) -> None:
        controller = self.visibility_transition_controller
        if controller is None:
            return
        controller.dispose()
        self.visibility_transition_controller = None

    def _mark_content_host_rect_dirty(self) -> None:
        self._content_host_rect_dirty = True

    def _sync_content_host_rect(self) -> None:
        if not self._content_host_rect_dirty:
            return
        previous_rect = Rect(self._content_host.rect)
        content_rect = self.content_rect()
        if previous_rect != content_rect:
            delta_x = int(content_rect.x - previous_rect.x)
            delta_y = int(content_rect.y - previous_rect.y)
            if delta_x != 0 or delta_y != 0:
                self._translate_subtree(self._content_host, delta_x, delta_y)
            self._content_host.rect = Rect(content_rect)
        self._content_host_rect_dirty = False

    @staticmethod
    def _translate_subtree(node: UiNode, dx: int, dy: int) -> None:
        for child in node.children:
            child.rect.x += int(dx)
            child.rect.y += int(dy)
            WindowControl._translate_subtree(child, dx, dy)

    def _notify_presenter_resized(self) -> None:
        if self.presenter is not None and hasattr(self.presenter, "on_resize"):
            self.presenter.on_resize(Rect(self.rect))

    def resize(self, width: int, height: int) -> None:
        previous = Rect(self.rect)
        content_width = max(1, int(width))
        content_height = max(1, int(height))
        self._content_size = (content_width, content_height)
        total_height = content_height + self.titlebar_height
        super().resize(content_width, total_height)
        self._mark_content_host_rect_dirty()
        self._sync_content_host_rect()
        if self.rect.size != previous.size:
            self._notify_presenter_resized()

    # set_pos is removed; window position is managed by the tiler only.

    # set_rect is removed; window rect is managed by the tiler only.

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

    def _draw_default_window_background(self, surface, theme, factory, *, visible_for_visuals: bool) -> None:
        visual_size = (self.rect.width, self.rect.height)
        if self._frame_visuals is None or self._frame_visual_size != visual_size:
            self._frame_visuals = factory.build_frame_visuals(self.rect)
            self._frame_visual_size = visual_size
        selected = factory.resolve_visual_state(
            self._frame_visuals,
            visible=bool(visible_for_visuals),
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
        # Reserve trailing titlebar controls so drag starts only in free title area.
        control_size = max(12, self.titlebar_height)
        reserved_width = 0
        if self._include_window_lower_button():
            lower_width = max(1, int(self._lower_control_button.rect.width))
            reserved_width += lower_width if lower_width > 1 else control_size
        if self._include_window_hide_image_button():
            hide_width = max(1, int(self._hide_control_button.rect.width))
            reserved_width += hide_width if hide_width > 1 else control_size
        width = max(0, self.rect.width - reserved_width)
        return Rect(self.rect.left, self.rect.top, width, self.titlebar_height)

    @staticmethod
    def _normalize_titlebar_controls(spec) -> dict:
        if spec is None:
            return {
                "include_window_lower_button": True,
                "include_window_hide_image_button": True,
            }
        if isinstance(spec, dict):
            raw = spec
        else:
            raw = {
                "include_window_lower_button": getattr(spec, "include_window_lower_button", None),
                "include_window_hide_image_button": getattr(spec, "include_window_hide_image_button", None),
            }
        lower_value = raw.get("include_window_lower_button")
        hide_value = raw.get("include_window_hide_image_button")
        return {
            "include_window_lower_button": True if lower_value is None else bool(lower_value),
            "include_window_hide_image_button": True if hide_value is None else bool(hide_value),
        }

    def set_titlebar_controls(self, spec) -> None:
        self.titlebar_controls = self._normalize_titlebar_controls(spec)

    def _include_window_lower_button(self) -> bool:
        return bool(self.titlebar_controls.get("include_window_lower_button", True))

    def _include_window_hide_image_button(self) -> bool:
        return bool(self.titlebar_controls.get("include_window_hide_image_button", True))

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
        previous_total_height = int(self.rect.height)
        self.titlebar_height = fitted_height
        self.rect.height = int(self._content_size[1] + self.titlebar_height)
        self._mark_content_host_rect_dirty()
        self._sync_content_host_rect()
        if int(self.rect.height) != previous_total_height:
            self._notify_presenter_resized()

    def content_rect(self) -> Rect:
        return Rect(
            self.rect.left,
            self.rect.top + self.titlebar_height,
            max(1, int(self._content_size[0])),
            max(1, int(self._content_size[1])),
        )

    def lower_control_rect(self) -> Rect:
        if not self._include_window_lower_button():
            return Rect(self.rect.right, self.rect.top, 0, 0)
        if self._lower_control_button is not None:
            width = max(1, int(self._lower_control_button.rect.width))
            height = max(1, int(self._lower_control_button.rect.height))
            if width > 1 and height > 1:
                return Rect(self.rect.right - width, self.rect.top, width, height)
        if self._chrome is not None:
            lower_rect = self._chrome.lower_control.get_rect()
            return Rect(self.rect.right - lower_rect.width, self.rect.top, lower_rect.width, lower_rect.height)
        size = max(12, self.titlebar_height)
        top = self.rect.top
        return Rect(self.rect.right - size, top, size, size)

    def hide_control_rect(self) -> Rect:
        if not self._include_window_hide_image_button():
            return Rect(self.rect.right, self.rect.top, 0, 0)
        lower_rect = self.lower_control_rect()
        if self._hide_control_button is not None:
            width = max(1, int(self._hide_control_button.rect.width))
            height = max(1, int(self._hide_control_button.rect.height))
            if width > 1 and height > 1:
                left = lower_rect.left - width if self._include_window_lower_button() else self.rect.right - width
                return Rect(left, self.rect.top, width, height)
        size = max(12, self.titlebar_height)
        top = self.rect.top
        left = lower_rect.left - size if self._include_window_lower_button() else self.rect.right - size
        return Rect(left, top, size, size)

    def _on_hide_control_click(self) -> None:
        if not self._include_window_hide_image_button():
            return
        self._titlebar_control_requests.append("hide")

    def _queue_lower_control_click(self) -> None:
        if not self._include_window_lower_button():
            return
        self._titlebar_control_requests.append("lower")

    def consume_titlebar_control_requests(self) -> tuple[str, ...]:
        if not self._titlebar_control_requests:
            return ()
        requests = tuple(self._titlebar_control_requests)
        self._titlebar_control_requests.clear()
        return requests

    def _pop_titlebar_control_request(self, request_kind: str) -> bool:
        for idx, request in enumerate(self._titlebar_control_requests):
            if request == request_kind:
                del self._titlebar_control_requests[idx]
                return True
        return False

    def consume_lower_control_click_request(self) -> bool:
        return self._pop_titlebar_control_request("lower")

    def consume_hide_control_click_request(self) -> bool:
        return self._pop_titlebar_control_request("hide")

    def is_lower_control_pressed(self) -> bool:
        lower_pressed = self._include_window_lower_button() and bool(getattr(self._lower_control_button, "pressed", False))
        hide_pressed = self._include_window_hide_image_button() and bool(getattr(self._hide_control_button, "pressed", False))
        return bool(lower_pressed or hide_pressed)

    def clear_lower_control_hover(self) -> None:
        if self._include_window_lower_button():
            self._lower_control_button.reconcile_hover(False)
        if self._include_window_hide_image_button():
            self._hide_control_button.reconcile_hover(False)

    def _sync_hide_control_button_rect(self) -> None:
        if self._hide_control_button is None or not self._include_window_hide_image_button():
            return
        target = self.hide_control_rect()
        if self._hide_control_button.rect != target:
            self._hide_control_button.set_rect(target)

    def _sync_lower_control_button_rect(self) -> None:
        if self._lower_control_button is None or not self._include_window_lower_button():
            return
        target = self.lower_control_rect()
        if self._lower_control_button.rect != target:
            self._lower_control_button.set_rect(target)

    def _ensure_lower_control_button_visuals(self, theme: "ColorTheme") -> None:
        if not self._include_window_lower_button():
            return
        factory = theme.graphics_factory
        control_size = max(12, self.titlebar_height)
        if self._lower_control_visual_size == (control_size, control_size):
            return
        visuals = factory.build_window_lower_control_visuals(control_size)
        self._lower_control_button.set_bitmaps(visuals.idle, visuals.hover, visuals.armed, factory=factory)
        self._lower_control_visual_size = (control_size, control_size)

    def _ensure_hide_control_button_visuals(self, theme: "ColorTheme") -> None:
        if not self._include_window_hide_image_button():
            return
        factory = theme.graphics_factory
        control_size = max(12, self.titlebar_height)
        if self._hide_control_visual_size == (control_size, control_size):
            return
        visuals = factory.build_window_hide_control_visuals(control_size)
        self._hide_control_button.set_bitmaps(visuals.idle, visuals.hover, visuals.armed, factory=factory)
        self._hide_control_visual_size = (control_size, control_size)

    def handle_lower_control_event(self, event: GuiEvent, app: "GuiApplication", theme=None) -> bool:
        if not (self.visible and self.enabled):
            self._lower_control_button.hovered = False
            self._lower_control_button.pressed = False
            self._hide_control_button.hovered = False
            self._hide_control_button.pressed = False
            return False
        include_lower = self._include_window_lower_button()
        include_hide = self._include_window_hide_image_button()
        if not (include_lower or include_hide):
            self._lower_control_button.hovered = False
            self._lower_control_button.pressed = False
            self._hide_control_button.hovered = False
            self._hide_control_button.pressed = False
            return False
        if theme is not None:
            if include_lower:
                self._ensure_lower_control_button_visuals(theme)
            if include_hide:
                self._ensure_hide_control_button_visuals(theme)
        if include_lower:
            self._sync_lower_control_button_rect()
        if include_hide:
            self._sync_hide_control_button_rect()
        self._lower_control_button.enabled = self.enabled
        self._lower_control_button.visible = self.visible and include_lower
        self._hide_control_button.enabled = self.enabled
        self._hide_control_button.visible = self.visible and include_hide
        hide_consumed = self._hide_control_button.handle_event(event, app, theme) if include_hide else False
        lower_consumed = self._lower_control_button.handle_event(event, app, theme) if include_lower else False
        return bool(hide_consumed or lower_consumed)

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
        transition_controller = self.visibility_transition_controller
        if transition_controller is not None:
            transition_controller.update(dt_seconds)
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

    def _is_position_in_window_bounds(self, event: GuiEvent) -> bool:
        """Return True when the event carries a position that falls inside this window's rect.

        Windows are opaque to position-based mouse input: any mouse event whose
        position is within ``self.rect`` must be consumed by this window so that it
        does not fall through to windows rendered underneath.
        """
        raw = event.pos
        return isinstance(raw, tuple) and len(raw) == 2 and self.rect.collidepoint(raw)

    def on_event_capture(self, event: GuiEvent, app: "GuiApplication", theme=None) -> bool:
        # Capture phase: propagate normally without opaque-window clamping.
        # Returning True here would prevent the scene from ever reaching the target
        # phase, so child controls would never receive events.
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
        in_bounds = self._is_position_in_window_bounds(event)
        if not self._accepts_content_scope(event, app):
            # Chrome/titlebar area: consume position-based events to prevent fall-through.
            return in_bounds
        child_handled = self._dispatch_children(event, app, reverse=True, theme=theme)
        return child_handled or in_bounds

    def on_event_bubble(self, event: GuiEvent, app: "GuiApplication", theme=None) -> bool:
        # Bubble phase: propagate normally without opaque-window clamping.
        # The target phase (handle_event) already ensures fall-through prevention.
        if not self._accepts_event_scope(event, app):
            return False
        if not self._accepts_content_scope(event, app):
            return False
        return self._dispatch_children(event, app, reverse=True, theme=theme)

    def _draw_standard(
        self,
        surface: pygame.Surface,
        theme: "ColorTheme",
        *,
        force_visible_visuals: bool = False,
    ) -> None:
        self._sync_content_host_rect()
        visible_for_visuals = bool(self.visible or force_visible_visuals)
        factory = theme.graphics_factory
        font_revision = factory.font_revision()
        if not self.restore_pristine(surface):
            self._draw_default_window_background(
                surface,
                theme,
                factory,
                visible_for_visuals=visible_for_visuals,
            )
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
            old_total_height = int(self.rect.height)
            chrome_height = self._chrome.title_bar_active.get_height()
            self.titlebar_height = max(self._TITLEBAR_MIN_HEIGHT, chrome_height)
            self.rect.height = int(self._content_size[1] + self.titlebar_height)
            if self.titlebar_height != old_titlebar_height:
                self._mark_content_host_rect_dirty()
                self._sync_content_host_rect()
            if self.titlebar_height != old_titlebar_height or int(self.rect.height) != old_total_height:
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
        include_lower = self._include_window_lower_button()
        include_hide = self._include_window_hide_image_button()
        if include_lower:
            self._ensure_lower_control_button_visuals(theme)
            self._sync_lower_control_button_rect()
        if include_hide:
            self._ensure_hide_control_button_visuals(theme)
            self._sync_hide_control_button_rect()
        self._lower_control_button.enabled = self.enabled
        self._lower_control_button.visible = visible_for_visuals and include_lower
        self._hide_control_button.enabled = self.enabled
        self._hide_control_button.visible = visible_for_visuals and include_hide
        if include_hide:
            self._hide_control_button.draw(surface, theme)
        if include_lower:
            self._lower_control_button.draw(surface, theme)

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
        transition_controller = self.visibility_transition_controller
        if transition_controller is not None and transition_controller.should_render():
            transition_controller.render(
                surface,
                theme,
                lambda s, t: self._draw_standard(s, t, force_visible_visuals=True),
            )
            return
        # If shear effect is active, render from a fresh per-frame snapshot.
        if self.shear_active and self.shear_controller:
            self.shear_controller.render(surface, theme, self._draw_standard)
            self.shear_active = self.shear_controller.is_active()
            return
        self._draw_standard(surface, theme)

    def dispose(self) -> None:
        self.release_visibility_transition_resources()
        controller = self.shear_controller
        if controller is not None:
            release = getattr(controller, "dispose", None)
            if callable(release):
                release()
        self.shear_controller = None
        self.shear_active = False
        super().dispose()
