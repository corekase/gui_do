from ._text_edit_focus_base import _TextEditFocusBase
from typing import Optional, Tuple

class _TextCaretPlacementBase(_TextEditFocusBase):
    """
    Base for text controls with correct caret placement (single/multi-line, formatted or plain).
    Implements pixel-to-char mapping and display/raw index mapping as per best UI/UX patterns.
    """
    def _get_display_value(self) -> str:
        """
        Return the display string for caret mapping. Override in subclass for masking/formatting.
        """
        return getattr(self, '_value', '')

    def _get_font(self, theme) -> Optional["pygame.font.Font"]:
        """
        Return the font instance for caret mapping. Override in subclass to provide font.
        """
        return None

    def _build_display_raw_mapping(self) -> Tuple[list, list]:
        """
        Returns (display_to_raw, raw_to_display) index mapping lists.
        display_to_raw[i] = raw index for display index i (or None for non-editable)
        raw_to_display[i] = display index for raw index i
        Override in formatted/masked controls for custom mapping.
        """
        formatter = getattr(self, "_formatter", None)
        raw = getattr(self, '_value', '')
        display = self._get_display_value()
        display_to_raw = [None] * (len(display) + 1)
        raw_to_display = [None] * (len(raw) + 1)
        # Default: 1:1 mapping for plain text
        if not formatter or not hasattr(formatter, "format") or not hasattr(formatter, "parse"):
            for i in range(len(display) + 1):
                display_to_raw[i] = i if i <= len(raw) else len(raw)
            for i in range(len(raw) + 1):
                raw_to_display[i] = i if i <= len(display) else len(display)
            return display_to_raw, raw_to_display
        # For formatters, walk both strings and map editable positions
        raw_idx = 0
        for disp_idx, ch in enumerate(display):
            parsed = formatter.parse(display[:disp_idx+1])
            if raw_idx < len(raw) and parsed[:raw_idx+1] == raw[:raw_idx+1]:
                display_to_raw[disp_idx] = raw_idx
                raw_to_display[raw_idx] = disp_idx
                raw_idx += 1
            else:
                display_to_raw[disp_idx] = None
        display_to_raw[len(display)] = len(raw)
        raw_to_display[len(raw)] = len(display)
        return display_to_raw, raw_to_display

    def _pos_to_char_index(self, x_screen: int, theme=None) -> int:
        """
        Convert screen x coordinate to logical (raw) caret index for single-line text.
        Uses font metrics for pixel-to-char mapping. Override in multi-line controls.
        """
        font = self._get_font(theme)
        if font is None:
            return 0
        display = self._get_display_value()
        x_local = x_screen - self.rect.left - getattr(self, '_H_PADDING', 4) + getattr(self, '_scroll_offset_px', 0)
        if x_local <= 0 or not display:
            return 0
        # Use font metrics to map x to char index
        lo = 0
        hi = len(display)
        def measure(n):
            px, _ = font.text_size(display[:n]) if hasattr(font, "text_size") else font.size(display[:n])
            return px
        while lo < hi:
            mid = (lo + hi) // 2
            if measure(mid) < x_local:
                lo = mid + 1
            else:
                hi = mid
        idx = lo
        if idx > 0 and idx < len(display):
            left_w = measure(idx - 1)
            right_w = measure(idx)
            if abs(x_local - left_w) <= abs(x_local - right_w):
                idx -= 1
        # Map to raw index, skipping non-editable if needed
        display_to_raw, _ = self._build_display_raw_mapping()
        # For formatted/masked, skip non-editable
        for offset in range(0, max(len(display), 1)):
            for test_idx in (idx - offset, idx + offset):
                if 0 <= test_idx <= len(display):
                    raw_idx = display_to_raw[test_idx]
                    if raw_idx is not None:
                        return raw_idx
        return 0
