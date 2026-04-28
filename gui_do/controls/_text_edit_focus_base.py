from __future__ import annotations

import pygame

from ..core.ui_node import UiNode


class _TextEditFocusBase(UiNode):
    """Shared focus/text-input session and cursor-blink behavior for text editors."""

    _BLINK_INTERVAL_SECONDS = 0.5

    def _on_text_edit_focus_changed(self, is_focused: bool, *, invalidate: bool = False) -> None:
        if is_focused:
            try:
                pygame.key.start_text_input()
                pygame.key.set_text_input_rect(self.rect)
            except Exception:
                pass
            self._cursor_visible = True
            self._blink_elapsed = 0.0
        else:
            try:
                pygame.key.stop_text_input()
            except Exception:
                pass
            self._drag_selecting = False
        if invalidate:
            self.invalidate()

    def _update_text_edit_blink(self, dt_seconds: float) -> bool:
        if not self._focused:
            return False
        self._blink_elapsed += dt_seconds
        if self._blink_elapsed >= self._BLINK_INTERVAL_SECONDS:
            self._blink_elapsed = 0.0
            self._cursor_visible = not self._cursor_visible
            self.invalidate()
            return True
        return False

    def _reset_text_edit_blink(self) -> None:
        self._cursor_visible = True
        self._blink_elapsed = 0.0
