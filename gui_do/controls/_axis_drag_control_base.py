from __future__ import annotations

from typing import TYPE_CHECKING

from ..core.ui_node import UiNode

if TYPE_CHECKING:
    from ..app.gui_application import GuiApplication


class _AxisDragControlBase(UiNode):
    """Shared drag + focus-activation behavior for axis-oriented controls."""

    def _init_axis_drag_state(self) -> None:
        self.dragging = False
        self._drag_anchor_offset = 0
        self._drag_handle_axis_pixel = 0
        self._focus_activation_armed = False
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

    def begin_focus_activation_visual(self) -> None:
        """Show temporary armed handle visual after focus-driven activation."""
        if self._focus_activation_armed:
            return
        self._focus_activation_armed = True
        self.invalidate()

    def end_focus_activation_visual(self) -> None:
        """Clear temporary armed handle visual after focus activation timeout."""
        if not self._focus_activation_armed:
            return
        self._focus_activation_armed = False
        self.invalidate()

    def _on_enabled_changed(self, old_enabled: bool, new_enabled: bool) -> None:
        self._focus_activation_armed = False
        super()._on_enabled_changed(old_enabled, new_enabled)

    def _on_visibility_changed(self, old_visible: bool, new_visible: bool) -> None:
        self._focus_activation_armed = False
        super()._on_visibility_changed(old_visible, new_visible)
