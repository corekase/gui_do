from __future__ import annotations

from typing import TYPE_CHECKING

from pygame.event import Event as PygameEvent
from pygame.locals import MOUSEBUTTONUP, MOUSEMOTION

from ..drag_state_model import DragState
from ..input_actions import InputAction

if TYPE_CHECKING:
    from ..gui_manager import GuiManager


class DragStateController:
    """Encapsulates window drag state transitions and movement updates."""

    def __init__(self, gui_manager: "GuiManager") -> None:
        """Bind drag-state behavior to a GUI manager."""
        self.gui: "GuiManager" = gui_manager

    @property
    def state(self) -> DragState:
        """Return mutable drag-state model."""
        return self.gui._drag_state

    def _pass_event(self) -> InputAction:
        """Return a no-op dispatcher action."""
        return InputAction.pass_event()

    def _commit_drag_mutation(self, mutation) -> None:
        """Apply a mutation callback to drag-state model."""
        mutation(self.state)

    def _has_valid_drag_context(self) -> bool:
        """Return whether drag state still references valid window and delta."""
        return (
            self.state.dragging_window is not None
            and self.state.dragging_window in self.gui.windows
            and self.state.mouse_delta is not None
        )

    def _set_drag_from_active_window(self) -> None:
        """Initialize drag state from current active window and pointer offset."""
        active_window = self.gui.active_window
        if active_window is None:
            return
        mouse_delta = (
            active_window.x - self.gui.mouse_pos[0],
            active_window.y - self.gui.mouse_pos[1],
        )

        def _mutation(state: DragState) -> None:
            """Internal helper for mutation."""
            state.begin_drag(active_window, mouse_delta)

        self._commit_drag_mutation(_mutation)

    def _release_drag(self) -> None:
        """Finalize drag, sync pointer position, and clear drag state."""
        dragging_window = self.state.dragging_window
        mouse_delta = self.state.mouse_delta
        dragging_window.position = (dragging_window.x, dragging_window.y)
        self.gui.set_mouse_pos(
            (
                dragging_window.x - mouse_delta[0],
                dragging_window.y - mouse_delta[1],
            )
        )

        self._commit_drag_mutation(lambda state: state.clear_drag())

    def reset(self) -> None:
        """Clear drag state without additional side effects."""
        self._commit_drag_mutation(lambda state: state.clear_drag())

    def start_if_possible(self, event: PygameEvent) -> None:
        """Start dragging active window when titlebar hit rules are satisfied."""
        event_pos = getattr(event, 'pos', self.gui.get_mouse_pos())
        if self.gui.active_window and self.gui.active_window.get_title_bar_rect().collidepoint(self.gui.lock_area(event_pos)):
            if self.gui.active_window.get_widget_rect().collidepoint(self.gui.lock_area(event_pos)):
                self.gui.lower_window(self.gui.active_window)
                self.gui.active_window = self.gui.windows[-1] if self.gui.windows else None
            else:
                self._set_drag_from_active_window()

    def handle_drag_event(self, event: PygameEvent) -> InputAction:
        """Handle drag release/motion events and update window position."""
        if not self._has_valid_drag_context():
            self.reset()
            return self._pass_event()
        if event.type == MOUSEBUTTONUP and getattr(event, 'button', None) == 1:
            self._release_drag()
        elif event.type == MOUSEMOTION and self.state.dragging:
            rel = getattr(event, 'rel', (0, 0))
            x = self.state.dragging_window.x + rel[0]
            y = self.state.dragging_window.y + rel[1]
            self.gui.set_mouse_pos((x - self.state.mouse_delta[0], y - self.state.mouse_delta[1]), False)
            self._commit_drag_mutation(lambda state: setattr(state.dragging_window, 'position', (x, y)))
        return self._pass_event()
