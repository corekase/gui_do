from __future__ import annotations

from pygame.event import Event as PygameEvent
from pygame.locals import MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION
from dataclasses import dataclass
from typing import Any, Optional, TYPE_CHECKING
from ..events import Event
from .input_actions import InputAction

if TYPE_CHECKING:
    from ..gui_manager import GuiManager


@dataclass(frozen=True)
class InputTargetMeta:
    """Hit-test metadata describing one candidate widget target."""

    widget: Any
    collides: bool
    outside_collision: bool


class InputTargetResolver:
    """Resolves active-window state and routes events to widget target layers."""

    def __init__(self, gui_manager: "GuiManager") -> None:
        """Bind resolver to a `GuiManager` event-routing context."""
        self.gui: "GuiManager" = gui_manager

    def update_active_window(self) -> None:
        """Refresh active-window selection from current pointer position."""
        self.gui.update_active_window()

    def _build_context(self) -> Any:
        """Build lightweight per-dispatch context values."""
        return {'mouse_pos': self.gui._get_mouse_pos()}

    def _convert_to_window_point(self, point, window):
        """Convert points using manager coordinate helpers."""
        return self.gui._convert_to_window(point, window)

    @staticmethod
    def _build_widget_action(widget: Any, window: Optional[Any]) -> InputAction:
        """Create deferred widget-event emission action for dispatcher integration."""
        return InputAction.from_builder(lambda w=widget, win=window: w.build_gui_event(win))

    def _dispatch_widget_layer(self, event: PygameEvent, container: Any, emit_task_panel: bool = False):
        """Route an event through one widget container from topmost to backmost."""
        hit_any = False
        focus_target = None
        # Iterate reversed snapshot to respect topmost draw/hit precedence.
        for widget in tuple(container.widgets)[::-1]:
            if widget not in container.widgets:
                continue
            if not widget.visible:
                continue
            target_meta = self._window_hit_meta(widget, container)
            if target_meta.collides:
                hit_any = True
                focus_target = target_meta.widget
                if self.gui.handle_widget(target_meta.widget, event, container):
                    if focus_target is not None and self.is_registered_widget(focus_target):
                        self.gui.update_focus(focus_target)
                    if emit_task_panel:
                        return InputAction.emit(Event.Widget, widget_id=target_meta.widget.id, task_panel=True)
                    return self._build_widget_action(target_meta.widget, container)
            elif target_meta.outside_collision:
                if self.gui.handle_widget(target_meta.widget, event, container):
                    if focus_target is not None and self.is_registered_widget(focus_target):
                        self.gui.update_focus(focus_target)
                    if emit_task_panel:
                        return InputAction.emit(Event.Widget, widget_id=target_meta.widget.id, task_panel=True)
                    return self._build_widget_action(target_meta.widget, container)
        return hit_any, focus_target

    @staticmethod
    def _screen_hit_meta(widget: Any, mouse_pos, convert_to_window) -> InputTargetMeta:
        """Compute hit metadata for root-screen widgets."""
        hit_rect = widget.hit_rect if widget.hit_rect else widget.draw_rect
        collides = bool(hit_rect.collidepoint(convert_to_window(mouse_pos, None)))
        return InputTargetMeta(widget=widget, collides=collides, outside_collision=False)

    @staticmethod
    def _window_hit_meta(widget: Any, window: Any) -> InputTargetMeta:
        """Compute hit metadata for widgets hosted in a window-like container."""
        collides = bool(widget.get_collide(window))
        outside_collision = bool(widget.should_handle_outside_collision()) if not collides else False
        return InputTargetMeta(widget=widget, collides=collides, outside_collision=outside_collision)

    @staticmethod
    def _resolve_topmost_window_at_pos(windows, mouse_pos) -> Optional[Any]:
        """Return the topmost visible window containing `mouse_pos`."""
        for window in tuple(windows)[::-1]:
            if window not in windows:
                continue
            if window.visible and window.get_window_rect().collidepoint(mouse_pos):
                return window
        return None

    def process_screen_widgets(self, event: PygameEvent) -> InputAction:
        """Route an event through root-screen widgets and base mouse fallbacks."""
        hit_any = False
        focus_target = None
        context = self._build_context()
        for widget in tuple(self.gui.widgets)[::-1]:
            if widget not in self.gui.widgets:
                continue
            if widget.visible:
                target_meta = self._screen_hit_meta(widget, context['mouse_pos'], self._convert_to_window_point)
                if target_meta.collides:
                    hit_any = True
                    focus_target = target_meta.widget
                    if self.gui.handle_widget(target_meta.widget, event):
                        if focus_target is not None and self.is_registered_widget(focus_target):
                            self.gui.update_focus(focus_target)
                        return self._build_widget_action(target_meta.widget, None)
        if not hit_any:
            self.gui.update_focus(None)
            return self._handle_base_mouse_events(event)
        if focus_target is not None and self.is_registered_widget(focus_target):
            self.gui.update_focus(focus_target)
        return InputAction.pass_event()

    def process_window_widgets(self, event: PygameEvent) -> InputAction:
        """Route an event through topmost window widgets at current pointer position."""
        if event.type == MOUSEBUTTONDOWN and getattr(event, 'button', None) == 1:
            if self.gui.active_window is not None and self.gui.active_window in self.gui.windows:
                self.gui.raise_window(self.gui.active_window)
        context = self._build_context()
        window = self._resolve_topmost_window_at_pos(self.gui.windows, context['mouse_pos'])
        if window is None:
            # When no window is under the pointer, continue with root-screen
            # widget routing instead of dropping to base mouse events.
            return self.process_screen_widgets(event)
        layer_result = self._dispatch_widget_layer(event, window)
        if isinstance(layer_result, InputAction):
            return layer_result
        hit_any, focus_target = layer_result
        if hit_any and focus_target is not None and self.is_registered_widget(focus_target):
            self.gui.update_focus(focus_target)
        else:
            self.gui.update_focus(None)
        return InputAction.pass_event()

    def process_task_panel_widgets(self, event: PygameEvent):
        """Route an event through task-panel widgets when pointer is over panel."""
        context = self._build_context()
        task_panel = self.gui.task_panel
        if task_panel is None or not task_panel.visible:
            return None
        if not task_panel.get_rect().collidepoint(context['mouse_pos']):
            return None
        layer_result = self._dispatch_widget_layer(event, task_panel, emit_task_panel=True)
        if isinstance(layer_result, InputAction):
            return layer_result
        hit_any, focus_target = layer_result
        if hit_any and focus_target is not None and self.is_registered_widget(focus_target):
            self.gui.update_focus(focus_target)
        else:
            self.gui.update_focus(None)
        return InputAction.pass_event()

    def is_registered_widget(self, widget) -> bool:
        """Return whether the widget is currently registered in any GUI container."""
        if widget is None:
            return False
        return bool(self.gui.object_registry.is_registered_object(widget))

    def _handle_base_mouse_events(self, event: PygameEvent) -> InputAction:
        """Map raw mouse pygame events into base GUI input actions."""
        if event.type == MOUSEBUTTONUP:
            return InputAction.emit(Event.MouseButtonUp, button=getattr(event, 'button', None))
        if event.type == MOUSEBUTTONDOWN:
            return InputAction.emit(Event.MouseButtonDown, button=getattr(event, 'button', None))
        if event.type == MOUSEMOTION:
            return InputAction.emit(Event.MouseMotion, rel=getattr(event, 'rel', (0, 0)))
        return InputAction.pass_event()
