from __future__ import annotations

from typing import TYPE_CHECKING

from pygame.event import Event as PygameEvent
from pygame.locals import MOUSEBUTTONUP, MOUSEMOTION

from ..gui_utils.drag_state_model import DragState
from ..geometry import point_in_rect
from .input_actions import InputAction

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

    def _has_valid_drag_context(self) -> bool:
        """Return whether drag state still references valid window and delta."""
        return (
            self.state.has_context()
            and self.state.dragging_window is not None
            and self.state.dragging_window in self.gui.windows
        )

    def _set_drag_from_active_window(self) -> None:
        """Initialize drag state from current active window and pointer offset."""
        active_window = self.gui.active_window
        if active_window is None:
            return
        wx, wy = self._window_position(active_window)
        mouse_delta = (
            wx - self.gui.mouse_pos[0],
            wy - self.gui.mouse_pos[1],
        )

        self.state.start_drag(active_window, mouse_delta)

    @staticmethod
    def _window_position(window) -> tuple[int, int]:
        """Return current window position from structural x/y contract."""
        wx = getattr(window, 'x', None)
        wy = getattr(window, 'y', None)
        if not isinstance(wx, int) or not isinstance(wy, int):
            raise ValueError(f'window must provide integer x/y, got: {window}')
        return (wx, wy)

    @staticmethod
    def _set_window_position(window, x: int, y: int) -> None:
        """Update window position via property setter when present, else x/y attrs."""
        if hasattr(type(window), 'position'):
            window.position = (x, y)
            return
        window.x = x
        window.y = y

    def _release_drag(self) -> None:
        """Finalize drag, sync pointer position, and clear drag state."""
        dragging_window = self.state.dragging_window
        mouse_delta = self.state.mouse_delta
        wx, wy = self._window_position(dragging_window)
        self._set_window_position(dragging_window, wx, wy)
        self.gui._set_mouse_pos(
            (
                wx - mouse_delta[0],
                wy - mouse_delta[1],
            )
        )
        self.state.stop_drag()

    def reset(self) -> None:
        """Clear drag state without additional side effects."""
        self.state.stop_drag()

    def start_if_possible(self, event: PygameEvent) -> None:
        """Start dragging active window when titlebar hit rules are satisfied."""
        event_pos = getattr(event, 'pos', self.gui._get_mouse_pos())
        titlebar_pos = self.gui.lock_area(event_pos)
        if self.gui.active_window and point_in_rect(titlebar_pos, self.gui.active_window.get_title_bar_rect()):
            widget_pos = self.gui.lock_area(event_pos)
            if point_in_rect(widget_pos, self.gui.active_window.get_widget_rect()):
                self.gui.lower_window(self.gui.active_window)
                self.gui.active_window = self.gui.windows[-1] if self.gui.windows else None
            else:
                self._set_drag_from_active_window()

    def handle_drag_event(self, event: PygameEvent) -> InputAction:
        """Handle drag release/motion events and update window position."""
        if not self._has_valid_drag_context():
            self.reset()
            return InputAction.pass_event()
        if event.type == MOUSEBUTTONUP and getattr(event, 'button', None) == 1:
            self._release_drag()
        elif event.type == MOUSEMOTION and self.state.dragging:
            rel = getattr(event, 'rel', (0, 0))
            wx, wy = self._window_position(self.state.dragging_window)
            x = wx + rel[0]
            y = wy + rel[1]
            self.gui._set_mouse_pos((x - self.state.mouse_delta[0], y - self.state.mouse_delta[1]), False)
            self._set_window_position(self.state.dragging_window, x, y)
        return InputAction.pass_event()
