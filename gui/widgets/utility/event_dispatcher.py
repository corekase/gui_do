from pygame.locals import QUIT, KEYDOWN, KEYUP, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION
from ...values.constants import EventKind, WidgetKind, ContainerKind
from .interactive import State

class EventDispatcher:
    def __init__(self, gui_manager):
        self.gui = gui_manager

    def handle(self, event):
        # update internal mouse position
        if event.type == MOUSEMOTION:
            self._handle_mouse_motion(event)
        # check for system events (QUIT, KEYUP, KEYDOWN)
        if event.type in (QUIT, KEYUP, KEYDOWN):
            return self._handle_system_event(event)
        # find active window context
        self.gui._update_active_window()
        # Priority 1: Window dragging
        if self.gui.dragging:
            return self.gui._handle_window_dragging(event)
        # Priority 2: Standard interaction (check for start of drag)
        if event.type == MOUSEBUTTONDOWN and not self.gui.dragging and event.button == 1:
            self.gui._check_window_drag_start(event)
        # Priority 3: Locked object
        if self.gui.locking_object:
            return self.gui._handle_locked_object(event)
        # Priority 4: Window / Screen widgets
        if self.gui.active_window:
            return self.gui._process_window_widgets(event)
        return self.gui._process_screen_widgets(event)

    def _handle_mouse_motion(self, event):
        if self.gui.mouse_locked:
            x, y = self.gui.mouse_pos
            dx, dy = event.rel
            self.gui.mouse_pos = (x + dx, y + dy)
        else:
            self.gui.mouse_pos = self.gui.lock_area(event.pos)

    def _handle_system_event(self, event):
        if event.type == QUIT:
            return self.gui.event(EventKind.Quit)
        if event.type == KEYUP:
            return self.gui.event(EventKind.KeyUp, key=event.key)
        elif event.type == KEYDOWN:
            return self.gui.event(EventKind.KeyDown, key=event.key)
        return self.gui.event(EventKind.Pass)
