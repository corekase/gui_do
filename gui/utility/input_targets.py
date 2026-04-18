from __future__ import annotations

from pygame.event import Event as PygameEvent
from pygame.locals import MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION
from dataclasses import dataclass
from typing import Any, Optional, TYPE_CHECKING
from .events import Event
from .input_actions import InputAction

if TYPE_CHECKING:
    from .gui_manager import GuiManager


@dataclass(frozen=True)
class InputTargetMeta:
    widget: Any
    collides: bool
    outside_collision: bool


class InputTargetResolver:
    """Resolves active-window state and routes events to widget target layers."""

    def __init__(self, gui_manager: "GuiManager") -> None:
        self.gui: "GuiManager" = gui_manager

    def update_active_window(self) -> None:
        self.gui.update_active_window()

    def _build_context(self) -> Any:
        return {'mouse_pos': self.gui.get_mouse_pos()}

    @staticmethod
    def _build_widget_action(widget: Any, window: Optional[Any]) -> InputAction:
        return InputAction.from_builder(lambda w=widget, win=window: w.build_gui_event(win))

    def _dispatch_widget_layer(self, event: PygameEvent, container: Any, emit_task_panel: bool = False):
        hit_any = False
        focus_target = None
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
        hit_rect = widget.hit_rect if widget.hit_rect else widget.draw_rect
        collides = bool(hit_rect.collidepoint(convert_to_window(mouse_pos, None)))
        return InputTargetMeta(widget=widget, collides=collides, outside_collision=False)

    @staticmethod
    def _window_hit_meta(widget: Any, window: Any) -> InputTargetMeta:
        collides = bool(widget.get_collide(window))
        outside_collision = bool(widget.should_handle_outside_collision()) if not collides else False
        return InputTargetMeta(widget=widget, collides=collides, outside_collision=outside_collision)

    @staticmethod
    def _resolve_topmost_window_at_pos(windows, mouse_pos) -> Optional[Any]:
        for window in tuple(windows)[::-1]:
            if window not in windows:
                continue
            if window.visible and window.get_window_rect().collidepoint(mouse_pos):
                return window
        return None

    def _is_registered_via_registry(self, widget: Any) -> Optional[bool]:
        registry = getattr(self.gui, 'object_registry', None)
        if registry is None or not hasattr(registry, 'is_registered_object'):
            return None
        try:
            return bool(registry.is_registered_object(widget))
        except Exception:
            return None

    def process_screen_widgets(self, event: PygameEvent) -> InputAction:
        hit_any = False
        focus_target = None
        context = self._build_context()
        for widget in tuple(self.gui.widgets)[::-1]:
            if widget not in self.gui.widgets:
                continue
            if widget.visible:
                target_meta = self._screen_hit_meta(widget, context['mouse_pos'], self.gui.convert_to_window)
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
        if event.type == MOUSEBUTTONDOWN and getattr(event, 'button', None) == 1:
            if self.gui.active_window is not None and self.gui.active_window in self.gui.windows:
                self.gui.raise_window(self.gui.active_window)
        context = self._build_context()
        window = self._resolve_topmost_window_at_pos(self.gui.windows, context['mouse_pos'])
        if window is None:
            self.gui.update_focus(None)
            return self._handle_base_mouse_events(event)
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
        if widget is None:
            return False
        registry_result = self._is_registered_via_registry(widget)
        if registry_result is not None:
            return registry_result
        if widget in self.gui.widgets:
            return True
        if self.gui.task_panel is not None and widget in self.gui.task_panel.widgets:
            return True
        for window in self.gui.windows:
            if widget in window.widgets:
                return True
        return False

    def _handle_base_mouse_events(self, event: PygameEvent) -> InputAction:
        if event.type == MOUSEBUTTONUP:
            return InputAction.emit(Event.MouseButtonUp, button=getattr(event, 'button', None))
        if event.type == MOUSEBUTTONDOWN:
            return InputAction.emit(Event.MouseButtonDown, button=getattr(event, 'button', None))
        if event.type == MOUSEMOTION:
            return InputAction.emit(Event.MouseMotion, rel=getattr(event, 'rel', (0, 0)))
        return InputAction.pass_event()
