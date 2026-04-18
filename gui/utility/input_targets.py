from pygame.event import Event as PygameEvent
from pygame.locals import MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION
from dataclasses import dataclass
from typing import Any, Optional, TYPE_CHECKING
from .constants import Event
from .input_actions import InputAction

if TYPE_CHECKING:
    from .guimanager import GuiManager


@dataclass(frozen=True)
class _WidgetTargetMeta:
    widget: Any
    collides: bool
    outside_collision: bool


class InputTargetResolver:
    """Resolves active-window state and routes events to widget target layers."""

    def __init__(self, gui_manager: "GuiManager") -> None:
        self.gui: "GuiManager" = gui_manager

    def update_active_window(self) -> None:
        self.gui.update_active_window()

    @staticmethod
    def _screen_hit_meta(widget: Any, mouse_pos, convert_to_window) -> _WidgetTargetMeta:
        hit_rect = widget.hit_rect if widget.hit_rect else widget.draw_rect
        collides = bool(hit_rect.collidepoint(convert_to_window(mouse_pos, None)))
        return _WidgetTargetMeta(widget=widget, collides=collides, outside_collision=False)

    @staticmethod
    def _window_hit_meta(widget: Any, window: Any) -> _WidgetTargetMeta:
        collides = bool(widget.get_collide(window))
        outside_collision = bool(widget.should_handle_outside_collision()) if not collides else False
        return _WidgetTargetMeta(widget=widget, collides=collides, outside_collision=outside_collision)

    @staticmethod
    def _resolve_topmost_window_at_pos(windows, mouse_pos) -> Optional[Any]:
        for window in tuple(windows)[::-1]:
            if window not in windows:
                continue
            if window.visible and window.get_window_rect().collidepoint(mouse_pos):
                return window
        return None

    def process_screen_widgets(self, event: PygameEvent) -> InputAction:
        hit_any = False
        focus_target = None
        mouse_pos = self.gui.get_mouse_pos()
        for widget in tuple(self.gui.widgets)[::-1]:
            if widget not in self.gui.widgets:
                continue
            if widget.visible:
                target_meta = self._screen_hit_meta(widget, mouse_pos, self.gui.convert_to_window)
                if target_meta.collides:
                    hit_any = True
                    focus_target = target_meta.widget
                    if self.gui.handle_widget(target_meta.widget, event):
                        if focus_target is not None and self.is_registered_widget(focus_target):
                            self.gui.update_focus(focus_target)
                        return InputAction.from_builder(lambda w=target_meta.widget: w.build_gui_event(None))
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
        window = self._resolve_topmost_window_at_pos(self.gui.windows, self.gui.get_mouse_pos())
        if window is None:
            self.gui.update_focus(None)
            return self._handle_base_mouse_events(event)
        hit_any = False
        focus_target = None
        for widget in tuple(window.widgets)[::-1]:
            if widget not in window.widgets:
                continue
            if widget.visible:
                target_meta = self._window_hit_meta(widget, window)
                if target_meta.collides:
                    hit_any = True
                    focus_target = target_meta.widget
                    if self.gui.handle_widget(target_meta.widget, event, window):
                        if focus_target is not None and self.is_registered_widget(focus_target):
                            self.gui.update_focus(focus_target)
                        return InputAction.from_builder(lambda w=target_meta.widget, win=window: w.build_gui_event(win))
                elif target_meta.outside_collision:
                    if self.gui.handle_widget(target_meta.widget, event, window):
                        if focus_target is not None and self.is_registered_widget(focus_target):
                            self.gui.update_focus(focus_target)
                        return InputAction.from_builder(lambda w=target_meta.widget, win=window: w.build_gui_event(win))
        if hit_any and focus_target is not None and self.is_registered_widget(focus_target):
            self.gui.update_focus(focus_target)
        else:
            self.gui.update_focus(None)
        return InputAction.pass_event()

    def process_task_panel_widgets(self, event: PygameEvent):
        task_panel = self.gui.task_panel
        if task_panel is None or not task_panel.visible:
            return None
        if not task_panel.get_rect().collidepoint(self.gui.get_mouse_pos()):
            return None
        hit_any = False
        focus_target = None
        for widget in tuple(task_panel.widgets)[::-1]:
            if widget not in task_panel.widgets:
                continue
            if widget.visible:
                target_meta = self._window_hit_meta(widget, task_panel)
                if target_meta.collides:
                    hit_any = True
                    focus_target = target_meta.widget
                    if self.gui.handle_widget(target_meta.widget, event, task_panel):
                        if focus_target is not None and self.is_registered_widget(focus_target):
                            self.gui.update_focus(focus_target)
                        return InputAction.emit(Event.Widget, widget_id=target_meta.widget.id, task_panel=True)
                elif target_meta.outside_collision:
                    if self.gui.handle_widget(target_meta.widget, event, task_panel):
                        if focus_target is not None and self.is_registered_widget(focus_target):
                            self.gui.update_focus(focus_target)
                        return InputAction.emit(Event.Widget, widget_id=target_meta.widget.id, task_panel=True)
        if hit_any and focus_target is not None and self.is_registered_widget(focus_target):
            self.gui.update_focus(focus_target)
        else:
            self.gui.update_focus(None)
        return InputAction.pass_event()

    def is_registered_widget(self, widget) -> bool:
        if widget is None:
            return False
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
