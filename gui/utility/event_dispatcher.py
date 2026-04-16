from pygame.event import Event as PygameEvent
from typing import TYPE_CHECKING
from pygame.locals import QUIT, KEYDOWN, KEYUP, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION
from .constants import Event, WidgetKind, InteractiveState

if TYPE_CHECKING:
    from .guimanager import GuiEvent, GuiManager

class EventDispatcher:
    """Routes pygame events to windows/widgets and emits GuiEvent values."""
    def __init__(self, gui_manager: "GuiManager") -> None:
        self.gui: "GuiManager" = gui_manager

    def _reset_window_drag_state(self) -> None:
        self.gui.dragging = False
        self.gui.dragging_window = None
        self.gui.mouse_delta = None

    def _is_registered_widget(self, widget) -> bool:
        if widget is None:
            return False
        if widget in self.gui.widgets:
            return True
        for window in self.gui.windows:
            if widget in window.widgets:
                return True
        return False

    def handle(self, event: PygameEvent) -> "GuiEvent":
        """Dispatch one pygame event using drag/lock/window/widget priority."""
        self.gui._resolve_locking_state()
        if event.type == MOUSEMOTION:
            self._handle_mouse_motion(event)
        if event.type in (QUIT, KEYUP, KEYDOWN):
            return self._handle_system_event(event)
        self._update_active_window()
        if self.gui.dragging:
            if self.gui.dragging_window is None or self.gui.mouse_delta is None:
                self._reset_window_drag_state()
                return self.gui.event(Event.Pass)
            return self._handle_window_dragging(event)
        if event.type == MOUSEBUTTONDOWN and not self.gui.dragging and getattr(event, 'button', None) == 1:
            self._check_window_drag_start(event)
        if self.gui.locking_object:
            return self._handle_locked_object(event)
        if self.gui.active_window:
            return self._process_window_widgets(event)
        return self._process_screen_widgets(event)

    def _handle_mouse_motion(self, event: PygameEvent) -> None:
        rel = getattr(event, 'rel', (0, 0))
        pos = getattr(event, 'pos', self.gui.get_mouse_pos())
        if self.gui.mouse_locked:
            x, y = self.gui.mouse_pos
            dx, dy = rel
            self.gui.mouse_pos = self.gui.lock_area((x + dx, y + dy))
        else:
            self.gui.mouse_pos = self.gui.lock_area(pos)

    def _handle_system_event(self, event: PygameEvent) -> "GuiEvent":
        if event.type == QUIT:
            return self.gui.event(Event.Quit)
        if event.type == KEYUP:
            return self.gui.event(Event.KeyUp, key=getattr(event, 'key', None))
        elif event.type == KEYDOWN:
            return self.gui.event(Event.KeyDown, key=getattr(event, 'key', None))
        return self.gui.event(Event.Pass)

    def _update_active_window(self) -> None:
        top_window = None
        for window in self.gui.windows[::-1]:
            if window.visible and window.get_window_rect().collidepoint(self.gui.get_mouse_pos()):
                top_window = window
                break
        self.gui.active_window = top_window

    def _handle_window_dragging(self, event: PygameEvent) -> "GuiEvent":
        if (
            self.gui.dragging_window is None
            or self.gui.dragging_window not in self.gui.windows
            or self.gui.mouse_delta is None
        ):
            self._reset_window_drag_state()
            return self.gui.event(Event.Pass)
        if event.type == MOUSEBUTTONUP and getattr(event, 'button', None) == 1:
            self.gui.dragging = False
            self.gui.dragging_window.set_pos((self.gui.dragging_window.x, self.gui.dragging_window.y))
            self.gui.set_mouse_pos((self.gui.dragging_window.x - self.gui.mouse_delta[0], self.gui.dragging_window.y - self.gui.mouse_delta[1]))
            self.gui.dragging_window = None
            self.gui.mouse_delta = None
        elif event.type == MOUSEMOTION and self.gui.dragging:
            rel = getattr(event, 'rel', (0, 0))
            x = self.gui.dragging_window.x + rel[0]
            y = self.gui.dragging_window.y + rel[1]
            self.gui.set_mouse_pos((x - self.gui.mouse_delta[0], y - self.gui.mouse_delta[1]), False)
            self.gui.dragging_window.set_pos((x, y))
        return self.gui.event(Event.Pass)

    def _check_window_drag_start(self, event: PygameEvent) -> None:
        event_pos = getattr(event, 'pos', self.gui.get_mouse_pos())
        if self.gui.active_window and self.gui.active_window.get_title_bar_rect().collidepoint(self.gui.lock_area(event_pos)):
            if self.gui.active_window.get_widget_rect().collidepoint(self.gui.lock_area(event_pos)):
                self.gui.lower_window(self.gui.active_window)
                self.gui.active_window = self.gui.windows[-1]
            else:
                self.gui.dragging = True
                self.gui.dragging_window = self.gui.active_window
                self.gui.mouse_delta = (self.gui.dragging_window.x - self.gui.mouse_pos[0],
                                    self.gui.dragging_window.y - self.gui.mouse_pos[1])

    def _handle_locked_object(self, event: PygameEvent) -> "GuiEvent":
        lock_obj = self.gui.locking_object
        if not self._is_registered_widget(lock_obj):
            self.gui.set_lock_area(None)
            return self.gui.event(Event.Pass)
        window = lock_obj.window if hasattr(lock_obj, 'window') else None
        if self.gui.handle_widget(lock_obj, event, window):
            widget_id = getattr(lock_obj, 'id', None)
            return self.gui.event(Event.Widget, widget_id=widget_id, window=window)
        return self.gui.event(Event.Pass)

    def _process_window_widgets(self, event: PygameEvent) -> "GuiEvent":
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
                                if focus_target is not None and self._is_registered_widget(focus_target):
                                    self.gui.update_focus(focus_target)
                                if widget.WidgetKind == WidgetKind.ButtonGroup:
                                    return self.gui.event(Event.Group, group=widget.read_group(), widget_id=widget.read_id(), window=window)
                                return self.gui.event(Event.Widget, widget_id=widget.id, window=window)
                        elif widget.WidgetKind == WidgetKind.ButtonGroup and widget.state == InteractiveState.Armed:
                            if self.gui.handle_widget(widget, event, window):
                                if focus_target is not None and self._is_registered_widget(focus_target):
                                    self.gui.update_focus(focus_target)
                                return self.gui.event(Event.Group, group=widget.read_group(), widget_id=widget.read_id(), window=window)
                if hit_any and focus_target is not None and self._is_registered_widget(focus_target):
                    self.gui.update_focus(focus_target)
                else:
                    self.gui.update_focus(None)
                return self.gui.event(Event.Pass)
        self.gui.update_focus(None)
        return self._handle_base_mouse_events(event)

    def _process_screen_widgets(self, event: PygameEvent) -> "GuiEvent":
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
                        if focus_target is not None and self._is_registered_widget(focus_target):
                            self.gui.update_focus(focus_target)
                        if widget.WidgetKind == WidgetKind.ButtonGroup:
                            return self.gui.event(Event.Group, group=widget.read_group(), widget_id=widget.read_id(), window=None)
                        return self.gui.event(Event.Widget, widget_id=widget.id, window=None)
        if not hit_any:
            self.gui.update_focus(None)
            return self._handle_base_mouse_events(event)
        if focus_target is not None and self._is_registered_widget(focus_target):
            self.gui.update_focus(focus_target)
        return self.gui.event(Event.Pass)

    def _handle_base_mouse_events(self, event: PygameEvent) -> "GuiEvent":
        if event.type == MOUSEBUTTONUP:
            return self.gui.event(Event.MouseButtonUp, button=getattr(event, 'button', None))
        elif event.type == MOUSEBUTTONDOWN:
            return self.gui.event(Event.MouseButtonDown, button=getattr(event, 'button', None))
        if event.type == MOUSEMOTION:
            return self.gui.event(Event.MouseMotion, rel=getattr(event, 'rel', (0, 0)))
        return self.gui.event(Event.Pass)
