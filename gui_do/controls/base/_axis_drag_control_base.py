from __future__ import annotations

from typing import TYPE_CHECKING

from ._focus_activatable_control_base import _FocusActivatableControlBase

if TYPE_CHECKING:
    from ...app.gui_application import GuiApplication


class _AxisDragControlBase(_FocusActivatableControlBase):
    """Shared drag + focus-activation behavior for axis-oriented controls."""

    def _init_axis_drag_state(self) -> None:
        self.dragging = False
        self._drag_anchor_offset = 0
        self._drag_handle_axis_pixel = 0
        self._programmatic_change_epoch = 0
        self._drag_start_programmatic_epoch = 0

    def _ancestor_window(self):
        current = self.parent
        while current is not None:
            if current.is_window():
                return current
            current = current.parent
        return None

    def _end_drag(self, app: "GuiApplication", *, sync_pointer: bool = False, release_pos=None) -> None:
        self.dragging = False
        if app.pointer_capture.is_owned_by(self.control_id):
            app.pointer_capture.end(self.control_id)
        if sync_pointer:
            final_pos = release_pos if release_pos is not None else app.logical_pointer_pos
            if final_pos is not None:
                app.sync_pointer_to_logical_position(final_pos)
