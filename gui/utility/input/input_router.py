from __future__ import annotations

from pygame.event import Event as PygameEvent
from pygame.locals import QUIT, KEYDOWN, KEYUP, MOUSEBUTTONDOWN, MOUSEMOTION
from typing import TYPE_CHECKING
from ..events import Event
from .input_actions import InputAction
from .input_targets import InputTargetResolver

if TYPE_CHECKING:
    from ..gui_manager import GuiManager


class InputRouter:
    """Resolves input target priority and produces framework GuiEvent values."""

    def __init__(self, gui_manager: "GuiManager") -> None:
        """Create InputRouter."""
        self.gui: "GuiManager" = gui_manager
        self.targets: InputTargetResolver = InputTargetResolver(gui_manager)

    def route(self, event: PygameEvent) -> InputAction:
        """Dispatch one pygame event using drag/lock/window/widget priority."""
        self.gui.lock_state.resolve()
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

    def _handle_locked_object(self, event: PygameEvent) -> InputAction:
        """Handle locked object."""
        lock_obj = self.gui.locking_object
        if not self._is_active_lock_widget(lock_obj):
            self.gui.set_lock_area(None)
            return InputAction.pass_event()
        window = lock_obj.window
        if self.gui.handle_widget(lock_obj, event, window):
            widget_id = getattr(lock_obj, 'id', None)
            return InputAction.emit(Event.Widget, widget_id=widget_id, window=window)
        return InputAction.pass_event()

    def _is_active_lock_widget(self, widget) -> bool:
        """Return whether lock widget is both registered and still container-attached."""
        if not self._is_registered_widget(widget):
            return False
        for screen_widget in self.gui.widgets:
            if screen_widget is widget:
                return True
        task_panel = self.gui.task_panel
        if task_panel is not None:
            for panel_widget in task_panel.widgets:
                if panel_widget is widget:
                    return True
        for window in self.gui.windows:
            for window_widget in window.widgets:
                if window_widget is widget:
                    return True
        return False

    def _handle_mouse_motion(self, event: PygameEvent) -> None:
        """Handle mouse motion."""
        rel = getattr(event, 'rel', (0, 0))
        pos = getattr(event, 'pos', self.gui.get_mouse_pos())
        if self.gui.mouse_locked:
            x, y = self.gui.mouse_pos
            dx, dy = rel
            self.gui.mouse_pos = self.gui.lock_state.clamp_position((x + dx, y + dy))
            self.gui.lock_state.enforce_point_lock(pos)
        else:
            self.gui.mouse_pos = self.gui.lock_state.clamp_position(pos)

    def _handle_system_event(self, event: PygameEvent) -> InputAction:
        """Handle system event."""
        if event.type == QUIT:
            return InputAction.emit(Event.Quit)
        if event.type == KEYUP:
            return InputAction.emit(Event.KeyUp, key=getattr(event, 'key', None))
        if event.type == KEYDOWN:
            return InputAction.emit(Event.KeyDown, key=getattr(event, 'key', None))
        return InputAction.pass_event()

    def _handle_window_dragging(self, event: PygameEvent) -> InputAction:
        """Handle window dragging."""
        return self.gui.drag_state.handle_drag_event(event)

    def _process_screen_widgets(self, event: PygameEvent) -> InputAction:
        """Process screen widgets."""
        return self.targets.process_screen_widgets(event)

    def _process_window_widgets(self, event: PygameEvent) -> InputAction:
        """Process window widgets."""
        return self.targets.process_window_widgets(event)

    def _process_task_panel_widgets(self, event: PygameEvent):
        """Process task panel widgets."""
        return self.targets.process_task_panel_widgets(event)

    def _check_window_drag_start(self, event: PygameEvent) -> None:
        """Check window drag start."""
        self.gui.drag_state.start_if_possible(event)

    def _is_registered_widget(self, widget) -> bool:
        """Is registered widget."""
        return self.targets.is_registered_widget(widget)

    def _reset_window_drag_state(self) -> None:
        """Reset window drag state."""
        self.gui.drag_state.reset()

    def _update_active_window(self) -> None:
        """Update active window."""
        self.targets.update_active_window()
