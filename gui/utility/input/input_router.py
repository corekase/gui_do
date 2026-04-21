from __future__ import annotations

from pygame.event import Event as PygameEvent
from pygame.locals import QUIT, KEYDOWN, KEYUP, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION, MOUSEWHEEL
from typing import TYPE_CHECKING
from ..events import Event
from ..geometry import clamp_point_to_rect, to_window
from .normalized_event import NormalizedInputEvent, normalize_input_event
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
        normalized = normalize_input_event(event)
        pre_locking_object = self.gui.locking_object
        pre_mouse_locked = bool(self.gui.mouse_locked)
        pre_mouse_point_locked = bool(self.gui.mouse_point_locked)
        pre_lock_area_rect = self.gui.lock_area_rect
        self._sync_pointer_from_mouse_event(event, normalized)
        is_left_mouse_down = normalized.is_left_down
        self.gui.lock_state.resolve()
        if event.type == MOUSEMOTION:
            self._handle_mouse_motion(event, normalized)
        if is_left_mouse_down:
            self.gui.focus_state.activate_window_at_pointer()
        action: InputAction
        if event.type in (QUIT, KEYUP, KEYDOWN):
            action = self._handle_system_event(event, normalized)
        else:
            self._update_active_window()
            if self.gui.dragging:
                if self.gui.dragging_window is None or self.gui.mouse_delta is None:
                    self._reset_window_drag_state()
                    action = InputAction.pass_event()
                else:
                    action = self._handle_window_dragging(event, normalized)
            elif self.gui.locking_object:
                action = self._handle_locked_object(event)
            else:
                task_panel_event = self._process_task_panel_widgets(event, normalized)
                if task_panel_event is not None:
                    action = task_panel_event
                else:
                    if is_left_mouse_down and not self.gui.dragging:
                        self._check_window_drag_start(event, normalized)
                    if self.gui.active_window:
                        action = self._process_window_widgets(event, normalized)
                    else:
                        action = self._process_screen_widgets(event, normalized)
        self._finalize_left_release_pointer(
            event,
            normalized,
            pre_locking_object,
            pre_mouse_locked,
            pre_mouse_point_locked,
            pre_lock_area_rect,
        )
        return action

    def _handle_locked_object(self, event: PygameEvent) -> InputAction:
        """Handle locked object."""
        lock_obj = self.gui.locking_object
        if not self._is_active_lock_widget(lock_obj):
            self.gui.set_lock_area(None)
            return InputAction.pass_event()
        window = lock_obj.window
        if self.gui.handle_widget(lock_obj, event, window):
            widget_id = lock_obj.id
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

    def _handle_mouse_motion(
        self,
        event: PygameEvent,
        normalized: NormalizedInputEvent,
    ) -> None:
        """Handle mouse motion."""
        rel = normalized.rel
        pos = normalized.pos or self.gui._get_mouse_pos()
        if self.gui.mouse_locked:
            x, y = self.gui.mouse_pos
            dx, dy = rel
            self._set_logical_mouse_pos(self.gui.lock_state.clamp_position((x + dx, y + dy)))
            self.gui.lock_state.enforce_point_lock(pos)
        else:
            self._set_logical_mouse_pos(self.gui.lock_state.clamp_position(pos))

    def _handle_system_event(
        self,
        event: PygameEvent,
        normalized: NormalizedInputEvent,
    ) -> InputAction:
        """Handle system event."""
        if event.type == QUIT:
            return InputAction.emit(Event.Quit)
        if event.type == KEYUP:
            return InputAction.emit(Event.KeyUp, key=normalized.key)
        if event.type == KEYDOWN:
            return InputAction.emit(Event.KeyDown, key=normalized.key)
        return InputAction.pass_event()

    def _handle_window_dragging(
        self,
        event: PygameEvent,
        normalized: NormalizedInputEvent,
    ) -> InputAction:
        """Handle window dragging."""
        return self.gui.drag_state.handle_drag_event(event, normalized)

    def _process_screen_widgets(
        self,
        event: PygameEvent,
        normalized: NormalizedInputEvent,
    ) -> InputAction:
        """Process screen widgets."""
        return self.targets.process_screen_widgets(event, normalized)

    def _process_window_widgets(
        self,
        event: PygameEvent,
        normalized: NormalizedInputEvent,
    ) -> InputAction:
        """Process window widgets."""
        return self.targets.process_window_widgets(event, normalized)

    def _process_task_panel_widgets(
        self,
        event: PygameEvent,
        normalized: NormalizedInputEvent,
    ):
        """Process task panel widgets."""
        return self.targets.process_task_panel_widgets(event, normalized)

    def _check_window_drag_start(
        self,
        event: PygameEvent,
        normalized: NormalizedInputEvent,
    ) -> None:
        """Check window drag start."""
        self.gui.drag_state.start_if_possible(event, normalized)

    def _is_registered_widget(self, widget) -> bool:
        """Is registered widget."""
        return self.targets.is_registered_widget(widget)

    def _reset_window_drag_state(self) -> None:
        """Reset window drag state."""
        self.gui.drag_state.reset()

    def _update_active_window(self) -> None:
        """Update active window."""
        self.targets.update_active_window()

    def _event_pos_inside_lock_owner(self, event_pos) -> bool:
        """Return whether a screen-space event position is inside lock owner draw rect."""
        lock_obj = self.gui.locking_object
        return self._event_pos_inside_specific_lock_owner(lock_obj, event_pos)

    @staticmethod
    def _event_pos_inside_specific_lock_owner(lock_obj, event_pos) -> bool:
        """Return whether a screen-space event position is inside a specific lock owner draw rect."""
        if lock_obj is None:
            return False
        draw_rect = lock_obj.draw_rect
        window = lock_obj.window
        if window is None:
            return bool(draw_rect.collidepoint(event_pos))
        try:
            local_pos = to_window(event_pos, window)
        except ValueError:
            return False
        return bool(draw_rect.collidepoint(local_pos))

    @staticmethod
    def _clamp_to_rect(point, rect):
        """Clamp a point to Rect inclusive bounds."""
        return clamp_point_to_rect(point, rect)

    def _finalize_left_release_pointer(
        self,
        event: PygameEvent,
        normalized: NormalizedInputEvent,
        pre_locking_object,
        pre_mouse_locked,
        pre_mouse_point_locked,
        pre_lock_area_rect,
    ) -> None:
        """Resolve logical/physical cursor position once after left-button release from area-lock drag."""
        hint_pos = self._consume_release_pointer_hint()
        if event.type != MOUSEBUTTONUP or not normalized.is_left_up:
            return
        if isinstance(hint_pos, tuple) and len(hint_pos) == 2:
            desired_pos = hint_pos
            self._set_logical_mouse_pos(desired_pos)
            if self.gui.mouse_locked:
                return
            self.gui.pointer.set_physical_mouse_pos(desired_pos)
            return
        if not pre_mouse_locked or pre_mouse_point_locked:
            return
        event_pos = normalized.pos
        if not isinstance(event_pos, tuple) or len(event_pos) != 2:
            return

        current_pos = self.gui.mouse_pos
        desired_pos = event_pos
        if (
            not self._event_pos_inside_specific_lock_owner(pre_locking_object, event_pos)
            and self._event_pos_inside_specific_lock_owner(pre_locking_object, current_pos)
        ):
            desired_pos = current_pos
        if pre_lock_area_rect is not None:
            if pre_lock_area_rect.collidepoint(desired_pos):
                pass
            elif self._event_pos_inside_specific_lock_owner(pre_locking_object, desired_pos):
                pass
            elif pre_lock_area_rect.collidepoint(event_pos):
                desired_pos = event_pos
            elif self._event_pos_inside_specific_lock_owner(pre_locking_object, event_pos):
                desired_pos = event_pos
            else:
                desired_pos = self._clamp_to_rect(event_pos, pre_lock_area_rect)

        self._set_logical_mouse_pos(desired_pos)

        if self.gui.mouse_locked:
            return
        self.gui.pointer.set_physical_mouse_pos(desired_pos)

    def _sync_pointer_from_mouse_event(
        self,
        event: PygameEvent,
        normalized: NormalizedInputEvent,
    ) -> None:
        """Sync logical pointer from mouse events before hit-testing/widget routing."""
        if event.type in (MOUSEBUTTONDOWN, MOUSEBUTTONUP):
            event_pos = normalized.pos
            if isinstance(event_pos, tuple) and len(event_pos) == 2:
                if (
                    event.type == MOUSEBUTTONUP
                    and normalized.is_left_up
                    and self.gui.mouse_locked
                    and not self.gui.mouse_point_locked
                    and self._event_pos_inside_lock_owner(event_pos)
                ):
                    self._set_logical_mouse_pos(event_pos)
                else:
                    self._set_logical_mouse_pos(self.gui.lock_state.clamp_position(event_pos))
            return
        if event.type != MOUSEWHEEL:
            return
        physical_pos = self.gui.input_providers.mouse_get_pos()
        if not isinstance(physical_pos, tuple) or len(physical_pos) != 2:
            return
        self._set_logical_mouse_pos(self.gui.lock_state.clamp_position(physical_pos))

    def _set_logical_mouse_pos(self, pos) -> None:
        """Set logical pointer position through manager helper when available."""
        self.gui._set_mouse_pos(pos, False)

    def _consume_release_pointer_hint(self):
        """Consume one-shot widget-provided release pointer override when present."""
        return self.gui.lock_flow.consume_release_pointer_hint()
