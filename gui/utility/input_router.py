from pygame.event import Event as PygameEvent
from pygame.locals import QUIT, KEYDOWN, KEYUP, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION
from typing import TYPE_CHECKING
from .constants import Event
from .input_actions import InputAction
from .input_targets import InputTargetResolver

if TYPE_CHECKING:
    from .guimanager import GuiEvent, GuiManager


class InputRouter:
    """Resolves input target priority and produces framework GuiEvent values."""

    def __init__(self, gui_manager: "GuiManager") -> None:
        self.gui: "GuiManager" = gui_manager
        self.targets: InputTargetResolver = InputTargetResolver(gui_manager)

    def handle(self, event: PygameEvent) -> InputAction:
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
                return InputAction.pass_event()
            return self._handle_window_dragging(event)
        if self.gui.locking_object:
            return self._handle_locked_object(event)
        task_panel_event = self._process_task_panel_widgets(event)
        if task_panel_event is not None:
            return task_panel_event
        if event.type == MOUSEBUTTONDOWN and not self.gui.dragging and getattr(event, 'button', None) == 1:
            self._check_window_drag_start(event)
        if self.gui.active_window:
            return self._process_window_widgets(event)
        return self._process_screen_widgets(event)

    def _handle_base_mouse_events(self, event: PygameEvent) -> InputAction:
        return self.targets._handle_base_mouse_events(event)

    def _handle_locked_object(self, event: PygameEvent) -> InputAction:
        lock_obj = self.gui.locking_object
        if not self._is_registered_widget(lock_obj):
            self.gui.set_lock_area(None)
            return InputAction.pass_event()
        window = lock_obj.window if hasattr(lock_obj, 'window') else None
        if self.gui.handle_widget(lock_obj, event, window):
            widget_id = getattr(lock_obj, 'id', None)
            return InputAction.emit(Event.Widget, widget_id=widget_id, window=window)
        return InputAction.pass_event()

    def _handle_mouse_motion(self, event: PygameEvent) -> None:
        rel = getattr(event, 'rel', (0, 0))
        pos = getattr(event, 'pos', self.gui.get_mouse_pos())
        lock_state = getattr(self.gui, 'lock_state', None)
        if self.gui.mouse_locked:
            x, y = self.gui.mouse_pos
            dx, dy = rel
            if lock_state is not None:
                self.gui.mouse_pos = lock_state.clamp_position((x + dx, y + dy))
                lock_state.enforce_point_lock(pos)
            else:
                self.gui.mouse_pos = self.gui.lock_area((x + dx, y + dy))
                self.gui.enforce_point_lock(pos)
        else:
            if lock_state is not None:
                self.gui.mouse_pos = lock_state.clamp_position(pos)
            else:
                self.gui.mouse_pos = self.gui.lock_area(pos)

    def _handle_system_event(self, event: PygameEvent) -> InputAction:
        if event.type == QUIT:
            return InputAction.emit(Event.Quit)
        if event.type == KEYUP:
            return InputAction.emit(Event.KeyUp, key=getattr(event, 'key', None))
        if event.type == KEYDOWN:
            return InputAction.emit(Event.KeyDown, key=getattr(event, 'key', None))
        return InputAction.pass_event()

    def _handle_window_dragging(self, event: PygameEvent) -> InputAction:
        drag_state = getattr(self.gui, 'drag_state', None)
        if drag_state is not None:
            return drag_state.handle_drag_event(event)
        if (
            self.gui.dragging_window is None
            or self.gui.dragging_window not in self.gui.windows
            or self.gui.mouse_delta is None
        ):
            self._reset_window_drag_state()
            return InputAction.pass_event()
        if event.type == MOUSEBUTTONUP and getattr(event, 'button', None) == 1:
            self.gui.dragging = False
            self.gui.dragging_window.position = (self.gui.dragging_window.x, self.gui.dragging_window.y)
            self.gui.set_mouse_pos(
                (
                    self.gui.dragging_window.x - self.gui.mouse_delta[0],
                    self.gui.dragging_window.y - self.gui.mouse_delta[1],
                )
            )
            self.gui.dragging_window = None
            self.gui.mouse_delta = None
        elif event.type == MOUSEMOTION and self.gui.dragging:
            rel = getattr(event, 'rel', (0, 0))
            x = self.gui.dragging_window.x + rel[0]
            y = self.gui.dragging_window.y + rel[1]
            self.gui.set_mouse_pos((x - self.gui.mouse_delta[0], y - self.gui.mouse_delta[1]), False)
            self.gui.dragging_window.position = (x, y)
        return InputAction.pass_event()

    def _process_screen_widgets(self, event: PygameEvent) -> InputAction:
        return self.targets.process_screen_widgets(event)

    def _process_window_widgets(self, event: PygameEvent) -> InputAction:
        return self.targets.process_window_widgets(event)

    def _process_task_panel_widgets(self, event: PygameEvent):
        return self.targets.process_task_panel_widgets(event)

    def _check_window_drag_start(self, event: PygameEvent) -> None:
        drag_state = getattr(self.gui, 'drag_state', None)
        if drag_state is not None:
            drag_state.start_if_possible(event)
            return
        event_pos = getattr(event, 'pos', self.gui.get_mouse_pos())
        if self.gui.active_window and self.gui.active_window.get_title_bar_rect().collidepoint(self.gui.lock_area(event_pos)):
            if self.gui.active_window.get_widget_rect().collidepoint(self.gui.lock_area(event_pos)):
                self.gui.lower_window(self.gui.active_window)
                self.gui.active_window = self.gui.windows[-1] if self.gui.windows else None
            else:
                self.gui.dragging = True
                self.gui.dragging_window = self.gui.active_window
                self.gui.mouse_delta = (
                    self.gui.dragging_window.x - self.gui.mouse_pos[0],
                    self.gui.dragging_window.y - self.gui.mouse_pos[1],
                )

    def _is_registered_widget(self, widget) -> bool:
        return self.targets.is_registered_widget(widget)

    def _reset_window_drag_state(self) -> None:
        drag_state = getattr(self.gui, 'drag_state', None)
        if drag_state is not None:
            drag_state.reset()
            return
        self.gui.dragging = False
        self.gui.dragging_window = None
        self.gui.mouse_delta = None

    def _update_active_window(self) -> None:
        self.targets.update_active_window()
