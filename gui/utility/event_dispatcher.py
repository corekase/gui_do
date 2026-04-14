from typing import TYPE_CHECKING, Any
from pygame.locals import QUIT, KEYDOWN, KEYUP, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION
from .values.constants import EventKind, WidgetKind, InteractiveState

if TYPE_CHECKING:
    from ..guimanager import GuiManager

class EventDispatcher:
    def __init__(self, gui_manager: "GuiManager") -> None:
        self.gui: "GuiManager" = gui_manager

    def handle(self, event: Any) -> "GuiManager.GuiEvent":
        # update internal mouse position
        if event.type == MOUSEMOTION:
            self._handle_mouse_motion(event)
        # check for system events (QUIT, KEYUP, KEYDOWN)
        if event.type in (QUIT, KEYUP, KEYDOWN):
            return self._handle_system_event(event)
        # find active window context
        self._update_active_window()
        # Priority 1: Window dragging
        if self.gui.dragging:
            return self._handle_window_dragging(event)
        # Priority 2: Standard interaction (check for start of drag)
        if event.type == MOUSEBUTTONDOWN and not self.gui.dragging and event.button == 1:
            self._check_window_drag_start(event)
        # Priority 3: Locked object
        if self.gui.locking_object:
            return self._handle_locked_object(event)
        # Priority 4: Window / Screen widgets
        if self.gui.active_window:
            return self._process_window_widgets(event)
        return self._process_screen_widgets(event)

    def _handle_mouse_motion(self, event: Any) -> None:
        if self.gui.mouse_locked:
            x, y = self.gui.mouse_pos
            dx, dy = event.rel
            self.gui.mouse_pos = (x + dx, y + dy)
        else:
            self.gui.mouse_pos = self.gui.lock_area(event.pos)

    def _handle_system_event(self, event: Any) -> "GuiManager.GuiEvent":
        if event.type == QUIT:
            return self.gui.event(EventKind.Quit)
        if event.type == KEYUP:
            return self.gui.event(EventKind.KeyUp, key=event.key)
        elif event.type == KEYDOWN:
            return self.gui.event(EventKind.KeyDown, key=event.key)
        return self.gui.event(EventKind.Pass)

    def _update_active_window(self) -> None:
        top_window = None
        for window in self.gui.windows[::-1]:
            if window.visible and window.get_window_rect().collidepoint(self.gui.get_mouse_pos()):
                top_window = window
                break
        self.gui.active_window = top_window

    def _handle_window_dragging(self, event: Any) -> "GuiManager.GuiEvent":
        if event.type == MOUSEBUTTONUP and event.button == 1:
            self.gui.dragging = False
            self.gui.dragging_window.set_pos((self.gui.dragging_window.x, self.gui.dragging_window.y))
            self.gui.set_mouse_pos((self.gui.dragging_window.x - self.gui.mouse_delta[0], self.gui.dragging_window.y - self.gui.mouse_delta[1]))
            self.gui.dragging_window = None
            self.gui.mouse_delta = None
        elif event.type == MOUSEMOTION and self.gui.dragging:
            x = self.gui.dragging_window.x + event.rel[0]
            y = self.gui.dragging_window.y + event.rel[1]
            self.gui.set_mouse_pos((x - self.gui.mouse_delta[0], y - self.gui.mouse_delta[1]), False)
            self.gui.dragging_window.set_pos((x, y))
        return self.gui.event(EventKind.Pass)

    def _check_window_drag_start(self, event: Any) -> None:
        if self.gui.active_window and self.gui.active_window.get_title_bar_rect().collidepoint(self.gui.lock_area(event.pos)):
            if self.gui.active_window.get_widget_rect().collidepoint(self.gui.lock_area(event.pos)):
                self.gui.lower_window(self.gui.active_window)
                self.gui.active_window = self.gui.windows[-1]
            else:
                self.gui.dragging = True
                self.gui.dragging_window = self.gui.active_window
                self.gui.mouse_delta = (self.gui.dragging_window.x - self.gui.mouse_pos[0],
                                    self.gui.dragging_window.y - self.gui.mouse_pos[1])

    def _handle_locked_object(self, event: Any) -> "GuiManager.GuiEvent":
        if self.gui.locking_object.WidgetKind == WidgetKind.Scrollbar:
            window = self.gui.locking_object.window if hasattr(self.gui.locking_object, 'window') else None
            if self.gui.handle_widget(self.gui.locking_object, event, window):
                widget_id = getattr(self.gui.locking_object, 'id', None)
                return self.gui.event(EventKind.Widget, widget_id=widget_id)
            return self.gui.event(EventKind.Pass)
        return self.gui.event(EventKind.Pass)

    def _process_window_widgets(self, event: Any) -> "GuiManager.GuiEvent":
        if event.type == MOUSEBUTTONDOWN and event.button == 1:
            self.gui.raise_window(self.gui.active_window)
        hit_any = False
        for window in self.gui.windows.copy()[::-1]:
            if window.visible and window.get_window_rect().collidepoint(self.gui.get_mouse_pos()):
                for widget in window.widgets.copy()[::-1]:
                    if widget.visible:
                        if widget.get_collide(window):
                            hit_any = True
                            self.gui.update_focus(widget)
                            if self.gui.handle_widget(widget, event, window):
                                if widget.WidgetKind == WidgetKind.ButtonGroup:
                                    return self.gui.event(EventKind.Group, group=widget.read_group(), widget_id=widget.read_id())
                                return self.gui.event(EventKind.Widget, widget_id=widget.id)
                        elif widget.WidgetKind == WidgetKind.ButtonGroup and widget.state == InteractiveState.Armed:
                            if self.gui.handle_widget(widget, event, window):
                                return self.gui.event(EventKind.Group, group=widget.read_group(), widget_id=widget.read_id())
                if not hit_any:
                    self.gui.update_focus(None)
                return self.gui.event(EventKind.Pass)
        self.gui.update_focus(None)
        return self._handle_base_mouse_events(event)

    def _process_screen_widgets(self, event: Any) -> "GuiManager.GuiEvent":
        hit_any = False
        for widget in self.gui.widgets.copy()[::-1]:
            if widget.visible:
                hit_rect = widget.hit_rect if widget.hit_rect else widget.draw_rect
                if hit_rect.collidepoint(self.gui.convert_to_window(self.gui.get_mouse_pos(), None)):
                    hit_any = True
                    self.gui.update_focus(widget)
                    if self.gui.handle_widget(widget, event):
                        if widget.WidgetKind == WidgetKind.ButtonGroup:
                            return self.gui.event(EventKind.Group, group=widget.read_group(), widget_id=widget.read_id())
                        return self.gui.event(EventKind.Widget, widget_id=widget.id)
        if not hit_any:
            self.gui.update_focus(None)
            return self._handle_base_mouse_events(event)
        return self.gui.event(EventKind.Pass)

    def _handle_base_mouse_events(self, event: Any) -> "GuiManager.GuiEvent":
        if event.type == MOUSEBUTTONUP:
            return self.gui.event(EventKind.MouseButtonUp, button=event.button)
        elif event.type == MOUSEBUTTONDOWN:
            return self.gui.event(EventKind.MouseButtonDown, button=event.button)
        if event.type == MOUSEMOTION:
            return self.gui.event(EventKind.MouseMotion, rel=event.rel)
        return self.gui.event(EventKind.Pass)
