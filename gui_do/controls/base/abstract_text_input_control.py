from typing import Optional, Tuple
import pygame
from ...events.gui_event import GuiEvent
from ..base._text_edit_focus_base import _TextEditFocusBase

class AbstractTextInputControl(_TextEditFocusBase):
    """
    Abstract base for all text input controls (single-line, multi-line, formatted).
    Implements caret state, selection, event handling, and extension points for pixel/char mapping.
    """
    def __init__(self, control_id: str, rect) -> None:
        super().__init__(control_id, rect)
        self._value = ""
        self._cursor_pos = 0
        self._sel_anchor = None
        self._sel_active = None
        self._focused = False
        self._drag_selecting = False
        self._scroll_offset_px = 0
        self._font_role = "body"
        self._font_size = 16

    # --- Abstract pixel/char mapping ---
    def get_char_index_at_pixel(self, x: int, y: Optional[int] = None, theme=None) -> int:
        """Map pixel (x, y) to character index. Must be implemented by subclass."""
        raise NotImplementedError

    def get_pixel_for_char_index(self, index: int, theme=None) -> Tuple[int, int]:
        """Map character index to pixel (x, y). Must be implemented by subclass."""
        raise NotImplementedError

    # --- Caret/selection state ---
    @property
    def cursor_pos(self) -> int:
        return self._cursor_pos

    @property
    def selection_range(self) -> Tuple[int, int]:
        if self._sel_anchor is None or self._sel_active is None:
            return (self._cursor_pos, self._cursor_pos)
        return (min(self._sel_anchor, self._sel_active), max(self._sel_anchor, self._sel_active))

    def select_all(self) -> None:
        self._sel_anchor = 0
        self._sel_active = len(self._value)
        self._cursor_pos = len(self._value)
        self.invalidate()

    def clear_selection(self) -> None:
        self._sel_anchor = None
        self._sel_active = None
        self.invalidate()

    def _get_line_bounds(self, position: Optional[int] = None) -> Tuple[int, int]:
        value_len = len(self._value)
        if position is None:
            position = self._cursor_pos
        pos = max(0, min(int(position), value_len))
        line_start = self._value.rfind("\n", 0, pos)
        line_end = self._value.find("\n", pos)
        start = 0 if line_start == -1 else line_start + 1
        end = value_len if line_end == -1 else line_end
        return (start, end)

    # --- Event handling (keyboard/mouse) ---
    def handle_event(self, event: GuiEvent, app, theme=None) -> bool:
        # Subclasses should call this and extend as needed
        if not self.visible or not self.enabled:
            return False
        # ... implement standard keyboard/mouse event handling here ...
        return False

    # --- Extension points for formatting/masking ---
    def format_input(self, text: str) -> str:
        return text

    def mask_input(self, text: str) -> str:
        return text

    def on_caret_moved(self, old_pos: int, new_pos: int) -> None:
        pass

    def on_selection_changed(self, old_sel: Tuple[int, int], new_sel: Tuple[int, int]) -> None:
        pass

    # --- Rendering hooks ---
    def draw(self, surface: "pygame.Surface", theme) -> None:
        # Subclasses should implement drawing of text, caret, and selection
        pass
