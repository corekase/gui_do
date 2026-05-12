"""TextFormatter — pluggable input-formatting protocol for TextInputControl.

Formatters control how user-typed text is displayed and how the display
value is parsed back to a raw storage string.  Attach a formatter to a
:class:`~gui_do.TextInputControl` via the ``formatter`` constructor argument.

Built-in formatters
-------------------
- :class:`NumericFormatter` — integer or float with optional thousands separator
  and min/max bounds validation.
- :class:`PatternFormatter` — positional mask (phone number, IP address, date)
  using ``#`` slots for digit positions.
- :class:`FixedPatternFormatter` — like ``PatternFormatter`` but requires all
  digit slots to be filled for validation to pass.

Usage::

    from gui_do import TextInputControl, NumericFormatter, PatternFormatter

    # Integer field clamped 0–100:
    age_input = TextInputControl(
        "age", rect,
        formatter=NumericFormatter(decimals=0, min_value=0, max_value=100),
    )

    # Phone number mask:
    phone_input = TextInputControl(
        "phone", rect,
        formatter=PatternFormatter("(###) ###-####"),
    )

Custom formatter
----------------
Any object implementing ``format``, ``parse``, ``validate``, and
``adjust_cursor`` methods qualifies — no base class required.  The
:data:`TextFormatter` type alias documents the required interface.
"""
from __future__ import annotations

from typing import Any, Callable, Optional, Protocol, TYPE_CHECKING, runtime_checkable

if TYPE_CHECKING:
    from ..controls.input.text_input_control import TextInputControl


# ---------------------------------------------------------------------------
# TextFormatter protocol
# ---------------------------------------------------------------------------


@runtime_checkable
class TextFormatter(Protocol):
    """Protocol for pluggable text input formatters.

    All methods must be portable pure-Python — no OS APIs, no filesystem
    access, no threading.
    """

    def format(self, raw: str) -> str:
        """Convert *raw* storage value to a display string."""
        ...

    def parse(self, display: str) -> str:
        """Convert *display* string back to a raw storage value."""
        ...

    def validate(self, raw: str) -> bool:
        """Return ``True`` if *raw* is a valid value for this formatter."""
        ...

    def adjust_cursor(self, raw: str, cursor: int, inserted: str) -> int:
        """Return adjusted cursor position after *inserted* was typed at *cursor*."""
        ...


# ---------------------------------------------------------------------------
# NumericFormatter
# ---------------------------------------------------------------------------


class NumericFormatter:
    """Formats numeric text (integer or float) with optional validation bounds.

    Parameters
    ----------
    decimals:
        Number of decimal places.  ``0`` means integer-only.
    min_value / max_value:
        Optional inclusive validation bounds.
    thousands_sep:
        Optional character to group integer digits (e.g. ``","``).
        Default ``""`` means no grouping.
    """

    def format(self, raw: str) -> str:
        """Format *raw* for display."""
        try:
            value = float(raw)
        except (ValueError, TypeError):
            return raw
        if self._decimals == 0:
            formatted = str(int(round(value)))
        else:
            formatted = f"{value:.{self._decimals}f}"
        if self._sep:
            # Apply thousands separator to integer part.
            parts = formatted.split(".")
            sign = "-" if parts[0].startswith("-") else ""
            integer_digits = parts[0].lstrip("-")
            groups: list[str] = []
            while integer_digits:
                groups.append(integer_digits[-3:])
                integer_digits = integer_digits[:-3]
            grouped = self._sep.join(reversed(groups))
            formatted = sign + grouped + ("." + parts[1] if len(parts) > 1 else "")
        return formatted

    def parse(self, display: str) -> str:
        """Strip display formatting from *display* and return raw value."""
        clean = display.replace(self._sep, "").strip() if self._sep else display.strip()
        try:
            value = float(clean)
        except (ValueError, TypeError):
            return clean
        if self._decimals == 0:
            return str(int(round(value)))
        return f"{value:.{self._decimals}f}"

    def validate(self, raw: str) -> bool:
        """Return ``True`` if *raw* is numeric and within bounds."""
        try:
            value = float(raw)
        except (ValueError, TypeError):
            return False
        if self._min is not None and value < self._min:
            return False
        if self._max is not None and value > self._max:
            return False
        return True

    def adjust_cursor(self, raw: str, cursor: int, inserted: str) -> int:
        """Return new cursor position after insertion (moves forward by insertion length)."""
        return min(cursor + len(inserted), len(raw) + len(inserted))

    def __init__(
        self,
        *,
        decimals: int = 0,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        thousands_sep: str = "",
    ) -> None:
        self._decimals: int = max(0, int(decimals))
        self._min: Optional[float] = min_value
        self._max: Optional[float] = max_value
        self._sep: str = str(thousands_sep)

    def create_text_input(
        self,
        control_id: str,
        rect: Any,
        *,
        raw_value: str = "",
        placeholder: str = "",
        max_length: Optional[int] = None,
        masked: bool = False,
        on_change: Optional[Callable[[str], None]] = None,
        on_submit: Optional[Callable[[str], None]] = None,
        font_role: str = "body",
    ) -> "TextInputControl":
        """Create a TextInputControl with submit-time numeric normalization."""
        from ..controls.input.text_input_control import TextInputControl

        allowed_chars = set("0123456789.-")
        if self._sep:
            allowed_chars.add(self._sep)

        def _filter_numeric(text: str) -> str:
            return "".join(ch for ch in text if ch in allowed_chars)

        state = {
            "last_valid": self.format(str(raw_value)),
            "control": None,
        }

        def _format_live_numeric(raw: str) -> str:
            text = str(raw)
            if text in ("", "-", ".", "-."):
                return text
            negative = text.startswith("-")
            if negative:
                text = text[1:]
            has_dot = "." in text
            if has_dot:
                integer_part, fractional_part = text.split(".", 1)
            else:
                integer_part, fractional_part = text, ""
            integer_digits = "".join(ch for ch in integer_part if ch.isdigit())
            if self._sep and integer_digits:
                groups: list[str] = []
                tmp = integer_digits
                while tmp:
                    groups.append(tmp[-3:])
                    tmp = tmp[:-3]
                integer_display = self._sep.join(reversed(groups))
            else:
                integer_display = integer_digits
            if negative:
                integer_display = "-" + integer_display
            if has_dot:
                return integer_display + "." + "".join(ch for ch in fractional_part if ch.isdigit())
            return integer_display

        def _on_change(new_text: str) -> None:
            control = state["control"]
            if control is not None:
                old_cursor = control.cursor_pos
                parsed_live = self.parse(new_text)
                live_text = _format_live_numeric(parsed_live)
                if live_text != new_text:
                    # Use formatter protocol for accurate placement
                    new_cursor = self.adjust_cursor(parsed_live, old_cursor, "")
                    control.set_value_with_cursor(live_text, new_cursor)
                    new_text = live_text
            parsed = self.parse(new_text)
            if parsed == "":
                state["last_valid"] = ""
            elif self.validate(parsed):
                state["last_valid"] = self.format(parsed)
            if on_change is not None:
                on_change(new_text)

        def _on_submit(submitted_text: str) -> None:
            control = state["control"]
            if control is None:
                return
            parsed = self.parse(submitted_text)
            if parsed == "":
                normalized = ""
            elif self.validate(parsed):
                normalized = self.format(parsed)
            else:
                normalized = state["last_valid"]
            control.set_value(normalized)
            state["last_valid"] = normalized
            if on_submit is not None:
                on_submit(normalized)

        control = TextInputControl(
            control_id,
            rect,
            value=state["last_valid"],
            placeholder=placeholder,
            max_length=max_length,
            masked=masked,
            on_change=_on_change,
            on_submit=_on_submit,
            input_filter=_filter_numeric,
            font_role=font_role,
            display_value_provider=lambda: self.format(control._value),
        )
        state["control"] = control
        return control


# ---------------------------------------------------------------------------
# PatternFormatter
# ---------------------------------------------------------------------------


class PatternFormatter:
    """Formats text using a positional mask with ``#`` digit placeholders.

    Example mask: ``"(###) ###-####"`` for a 10-digit phone number.
    Literal characters in the mask are inserted automatically during display.

    Parameters
    ----------
    mask:
        Mask string.  ``#`` marks a digit slot; other characters are literals.
    fill_char:
        Character used to fill empty digit slots in display (default ``"_"``).
    """

    def __init__(self, mask: str, *, fill_char: str = "_") -> None:
        self._mask: str = str(mask)
        self._fill: str = (str(fill_char)[0] if fill_char else "_")
        self._slots: list[int] = [i for i, c in enumerate(self._mask) if c == "#"]

    @property
    def mask(self) -> str:
        """The mask string."""
        return self._mask

    @property
    def slot_count(self) -> int:
        """Number of digit slots in the mask."""
        return len(self._slots)

    def format(self, raw: str) -> str:
        """Apply the mask to *raw* digits, padding empty slots with :attr:`fill_char`."""
        digits = [c for c in raw if c.isdigit()]
        result = list(self._mask)
        for slot_idx, char_idx in enumerate(self._slots):
            result[char_idx] = digits[slot_idx] if slot_idx < len(digits) else self._fill
        return "".join(result)

    def parse(self, display: str) -> str:
        """Extract raw digits from a masked *display* string."""
        return "".join(c for c in display if c.isdigit())

    def validate(self, raw: str) -> bool:
        """Return ``True`` if *raw* supplies at least as many digits as the mask has slots."""
        return len([c for c in raw if c.isdigit()]) >= len(self._slots)

    def adjust_cursor(self, raw: str, cursor: int, inserted: str) -> int:
        """Return the display cursor position after typing *inserted* at *cursor*."""
        new_digit_count = min(len(raw) + len(inserted), len(self._slots))
        if new_digit_count == 0:
            return 0
        slot_idx = min(new_digit_count - 1, len(self._slots) - 1)
        return self._slots[slot_idx] + 1

    def format_partial(self, raw: str) -> str:
        """Format only the entered digits, inserting mask literals as needed."""
        digits = [c for c in str(raw) if c.isdigit()]
        if not digits:
            return ""

        out: list[str] = []
        digit_index = 0
        total = len(digits)
        for ch in self._mask:
            if ch == "#":
                if digit_index >= total:
                    break
                out.append(digits[digit_index])
                digit_index += 1
                continue
            if digit_index > 0 and digit_index < total:
                out.append(ch)
        return "".join(out)

    def create_text_input(
        self,
        control_id: str,
        rect: Any,
        *,
        raw_value: str = "",
        placeholder: str = "",
        max_length: Optional[int] = None,
        masked: bool = False,
        on_change: Optional[Callable[[str], None]] = None,
        on_submit: Optional[Callable[[str], None]] = None,
        font_role: str = "body",
    ) -> "TextInputControl":
        """Create a TextInputControl with submit-time pattern normalization."""
        from ..controls.input.text_input_control import TextInputControl

        def _filter_digits(text: str) -> str:
            return "".join(ch for ch in text if ch.isdigit())

        initial_digits = self.parse(str(raw_value))[: self.slot_count]
        state = {
            "last_valid": self.format_partial(initial_digits),
            "control": None,
        }

        def _on_change(new_text: str) -> None:
            control = state["control"]
            if control is not None:
                old_cursor = control.cursor_pos
                digits_live = self.parse(new_text)[: self.slot_count]
                live_text = self.format_partial(digits_live)
                if live_text != new_text:
                    new_cursor = self.adjust_cursor(digits_live, old_cursor, "")
                    control.set_value_with_cursor(live_text, new_cursor)
                    new_text = live_text
            digits = self.parse(new_text)[: self.slot_count]
            if digits:
                state["last_valid"] = self.format_partial(digits)
            elif new_text == "":
                state["last_valid"] = ""
            if on_change is not None:
                on_change(new_text)

        def _on_submit(submitted_text: str) -> None:
            control = state["control"]
            if control is None:
                return
            digits = self.parse(submitted_text)[: self.slot_count]
            normalized = "" if not digits else self.format_partial(digits)
            control.set_value(normalized)
            state["last_valid"] = normalized
            if on_submit is not None:
                on_submit(normalized)

        control = TextInputControl(
            control_id,
            rect,
            value=state["last_valid"],
            placeholder=placeholder,
            max_length=(len(self.mask) if max_length is None else max_length),
            masked=masked,
            on_change=_on_change,
            on_submit=_on_submit,
            input_filter=_filter_digits,
            font_role=font_role,
            display_value_provider=lambda: self.format(control._value),
        )
        state["control"] = control
        return control


# ---------------------------------------------------------------------------
# FixedPatternFormatter
# ---------------------------------------------------------------------------


class FixedPatternFormatter(PatternFormatter):
    """Like :class:`PatternFormatter` but requires *all* digit slots to be filled.

    :meth:`validate` returns ``True`` only when the raw digit count exactly
    equals the mask slot count.
    """

    def validate(self, raw: str) -> bool:
        return len([c for c in raw if c.isdigit()]) == len(self._slots)
