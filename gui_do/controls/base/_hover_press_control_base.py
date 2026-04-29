from __future__ import annotations

from ._focus_activatable_control_base import _FocusActivatableControlBase


class _HoverPressControlBase(_FocusActivatableControlBase):
    """Shared hover + press visual state for interactive controls."""

    def __init__(self, control_id: str, rect) -> None:
        super().__init__(control_id, rect)
        self.hovered = False
        self.pressed = False

    def reconcile_hover(self, wants_hover: bool) -> None:
        if self.hovered != wants_hover:
            self.hovered = wants_hover
            self.invalidate()

    def _on_enabled_changed(self, old_enabled: bool, new_enabled: bool) -> None:
        self.hovered = False
        self.pressed = False
        super()._on_enabled_changed(old_enabled, new_enabled)

    def _on_visibility_changed(self, old_visible: bool, new_visible: bool) -> None:
        self.hovered = False
        self.pressed = False
        super()._on_visibility_changed(old_visible, new_visible)
