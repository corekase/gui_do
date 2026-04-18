from pygame.event import Event as PygameEvent
from pygame.locals import MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION
from typing import TYPE_CHECKING
from .constants import Event

if TYPE_CHECKING:
    from .guimanager import GuiEvent, GuiManager


class InputTargetResolver:
    """Resolves active-window state and routes events to widget target layers."""

    def __init__(self, gui_manager: "GuiManager") -> None:
        self.gui: "GuiManager" = gui_manager

    def update_active_window(self) -> None:
        top_window = None
        for window in self.gui.windows[::-1]:
            if window.visible and window.get_window_rect().collidepoint(self.gui.get_mouse_pos()):
                top_window = window
                break
        self.gui.active_window = top_window

    def process_screen_widgets(self, event: PygameEvent) -> "GuiEvent":
        hit_any = False
        focus_target = None
        for widget in tuple(self.gui.widgets)[::-1]:
            if widget not in self.gui.widgets:
                continue
            if widget.visible:
                hit_rect = widget.hit_rect if widget.hit_rect else widget.draw_rect
                if hit_rect.collidepoint(self.gui.convert_to_window(self.gui.get_mouse_pos(), None)):
                    hit_any = True
                    focus_target = widget
                    if self.gui.handle_widget(widget, event):
                        if focus_target is not None and self.is_registered_widget(focus_target):
                            self.gui.update_focus(focus_target)
                        return widget.build_gui_event(None)
        if not hit_any:
            self.gui.update_focus(None)
            return self._handle_base_mouse_events(event)
        if focus_target is not None and self.is_registered_widget(focus_target):
            self.gui.update_focus(focus_target)
        return self.gui.event(Event.Pass)

    def process_window_widgets(self, event: PygameEvent) -> "GuiEvent":
        if event.type == MOUSEBUTTONDOWN and getattr(event, 'button', None) == 1:
            if self.gui.active_window is not None and self.gui.active_window in self.gui.windows:
                self.gui.raise_window(self.gui.active_window)
        hit_any = False
        focus_target = None
        for window in tuple(self.gui.windows)[::-1]:
            if window not in self.gui.windows:
                continue
            if window.visible and window.get_window_rect().collidepoint(self.gui.get_mouse_pos()):
                for widget in tuple(window.widgets)[::-1]:
                    if widget not in window.widgets:
                        continue
                    if widget.visible:
                        if widget.get_collide(window):
                            hit_any = True
                            focus_target = widget
                            if self.gui.handle_widget(widget, event, window):
                                if focus_target is not None and self.is_registered_widget(focus_target):
                                    self.gui.update_focus(focus_target)
                                return widget.build_gui_event(window)
                        elif widget.should_handle_outside_collision():
                            if self.gui.handle_widget(widget, event, window):
                                if focus_target is not None and self.is_registered_widget(focus_target):
                                    self.gui.update_focus(focus_target)
                                return widget.build_gui_event(window)
                if hit_any and focus_target is not None and self.is_registered_widget(focus_target):
                    self.gui.update_focus(focus_target)
                else:
                    self.gui.update_focus(None)
                return self.gui.event(Event.Pass)
        self.gui.update_focus(None)
        return self._handle_base_mouse_events(event)

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
                if widget.get_collide(task_panel):
                    hit_any = True
                    focus_target = widget
                    if self.gui.handle_widget(widget, event, task_panel):
                        if focus_target is not None and self.is_registered_widget(focus_target):
                            self.gui.update_focus(focus_target)
                        return self.gui.event(Event.Widget, widget_id=widget.id, task_panel=True)
                elif widget.should_handle_outside_collision():
                    if self.gui.handle_widget(widget, event, task_panel):
                        if focus_target is not None and self.is_registered_widget(focus_target):
                            self.gui.update_focus(focus_target)
                        return self.gui.event(Event.Widget, widget_id=widget.id, task_panel=True)
        if hit_any and focus_target is not None and self.is_registered_widget(focus_target):
            self.gui.update_focus(focus_target)
        else:
            self.gui.update_focus(None)
        return self.gui.event(Event.Pass)

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

    def _handle_base_mouse_events(self, event: PygameEvent) -> "GuiEvent":
        if event.type == MOUSEBUTTONUP:
            return self.gui.event(Event.MouseButtonUp, button=getattr(event, 'button', None))
        if event.type == MOUSEBUTTONDOWN:
            return self.gui.event(Event.MouseButtonDown, button=getattr(event, 'button', None))
        if event.type == MOUSEMOTION:
            return self.gui.event(Event.MouseMotion, rel=getattr(event, 'rel', (0, 0)))
        return self.gui.event(Event.Pass)
