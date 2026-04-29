from __future__ import annotations

from ..core.ui_node import UiNode


class _FocusActivatableControlBase(UiNode):
    """Shared focus-activation visual protocol for interactive controls."""

    def __init__(self, control_id: str, rect) -> None:
        super().__init__(control_id, rect)
        self._focus_activation_armed = False

    def begin_focus_activation_visual(self) -> None:
        """Show temporary armed visual after focus-driven activation."""
        if self._focus_activation_armed:
            return
        self._focus_activation_armed = True
        self.invalidate()

    def end_focus_activation_visual(self) -> None:
        """Clear temporary armed visual after focus activation timeout."""
        if not self._focus_activation_armed:
            return
        self._focus_activation_armed = False
        self.invalidate()

    def _invoke_click(self) -> None:
        """Keyboard-activation entry point. Override in leaf controls."""

    def _on_enabled_changed(self, old_enabled: bool, new_enabled: bool) -> None:
        self._focus_activation_armed = False
        super()._on_enabled_changed(old_enabled, new_enabled)

    def _on_visibility_changed(self, old_visible: bool, new_visible: bool) -> None:
        self._focus_activation_armed = False
        super()._on_visibility_changed(old_visible, new_visible)
