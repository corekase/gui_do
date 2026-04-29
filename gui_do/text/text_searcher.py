"""TextSearcher — find/replace engine for plain text.

Wraps Python's :mod:`re` module to provide case-insensitive, whole-word,
and full-regex search over a string, with helpers for converting match spans
into :class:`~gui_do.TextSpan` highlight descriptors.

Usage::

    from gui_do import TextSearcher, TextMatch

    searcher = TextSearcher("Hello World hello", case_sensitive=False)
    matches = searcher.find_all("hello")
    # → [TextMatch(start=0, end=5, text="Hello"),
    #    TextMatch(start=12, end=17, text="hello")]

    m = searcher.find_next("hello", from_pos=1)
    # → TextMatch(start=12, end=17, text="hello")

    new_text = searcher.replace(m, "Hi")
    new_all  = searcher.replace_all("hello", "Hi")

    # Whole-word, regex:
    s2 = TextSearcher(text, whole_word=True)
    s3 = TextSearcher(text, use_regex=True)
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional, Sequence


# ---------------------------------------------------------------------------
# TextMatch
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TextMatch:
    """A single text search match.

    Attributes
    ----------
    start:
        Inclusive start character index.
    end:
        Exclusive end character index.
    text:
        The matched substring.
    """
    start: int
    end: int
    text: str


# ---------------------------------------------------------------------------
# TextSearcher
# ---------------------------------------------------------------------------


class TextSearcher:
    """Plain-text and regex search/replace engine.

    Parameters
    ----------
    text:
        The source text to search within.
    case_sensitive:
        When ``False`` (default) searches are case-insensitive.
    whole_word:
        When ``True`` matches are anchored to word boundaries.
    use_regex:
        When ``True`` the *query* argument to search methods is treated as a
        regular expression pattern.  *whole_word* is ignored in regex mode
        (include ``\\b`` in your pattern explicitly if needed).

    The *text* attribute may be replaced at runtime to search a new string
    without constructing a new instance.
    """

    def __init__(
        self,
        text: str,
        *,
        case_sensitive: bool = False,
        whole_word: bool = False,
        use_regex: bool = False,
    ) -> None:
        self._text = text
        self._case_sensitive = bool(case_sensitive)
        self._whole_word = bool(whole_word)
        self._use_regex = bool(use_regex)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, value: str) -> None:
        self._text = value

    @property
    def case_sensitive(self) -> bool:
        return self._case_sensitive

    @property
    def whole_word(self) -> bool:
        return self._whole_word

    @property
    def use_regex(self) -> bool:
        return self._use_regex

    # ------------------------------------------------------------------
    # Internal: compile a search pattern
    # ------------------------------------------------------------------

    def _compile(self, query: str) -> re.Pattern:
        flags = 0 if self._case_sensitive else re.IGNORECASE
        if self._use_regex:
            pattern = query
        else:
            pattern = re.escape(query)
            if self._whole_word:
                pattern = r"\b" + pattern + r"\b"
        return re.compile(pattern, flags)

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def find_all(self, query: str) -> List[TextMatch]:
        """Return all non-overlapping matches of *query* in the text."""
        if not query:
            return []
        try:
            rx = self._compile(query)
        except re.error:
            return []
        results = []
        for m in rx.finditer(self._text):
            results.append(TextMatch(start=m.start(), end=m.end(), text=m.group()))
        return results

    def find_next(self, query: str, from_pos: int = 0) -> Optional[TextMatch]:
        """Return the first match at or after *from_pos*, or ``None``."""
        if not query:
            return None
        try:
            rx = self._compile(query)
        except re.error:
            return None
        m = rx.search(self._text, from_pos)
        if m is None:
            return None
        return TextMatch(start=m.start(), end=m.end(), text=m.group())

    def find_prev(self, query: str, from_pos: int) -> Optional[TextMatch]:
        """Return the last match that ends before *from_pos*, or ``None``."""
        if not query:
            return None
        matches = self.find_all(query)
        # Walk backwards through all matches
        result: Optional[TextMatch] = None
        for m in matches:
            if m.end <= from_pos:
                result = m
            else:
                break
        return result

    # ------------------------------------------------------------------
    # Replace
    # ------------------------------------------------------------------

    def replace(self, match: TextMatch, replacement: str) -> str:
        """Return a new string with *match* replaced by *replacement*.

        Does not modify :attr:`text` in-place.
        """
        return self._text[: match.start] + replacement + self._text[match.end :]

    def replace_all(self, query: str, replacement: str) -> str:
        """Return a new string with all matches of *query* replaced.

        Does not modify :attr:`text` in-place.
        """
        if not query:
            return self._text
        try:
            rx = self._compile(query)
        except re.error:
            return self._text
        if self._use_regex:
            return rx.sub(replacement, self._text)
        return rx.sub(re.escape(replacement) if False else replacement, self._text)

    # ------------------------------------------------------------------
    # TextSpan helpers
    # ------------------------------------------------------------------

    def highlight_spans(
        self,
        matches: Sequence[TextMatch],
        style: Optional[dict] = None,
    ) -> List[dict]:
        """Convert *matches* to TextSpan-style dicts for use with TextFlow.

        Returns a list of ``{"start": int, "end": int, "style": dict}``
        descriptors.  Pass these to :class:`~gui_do.TextSpan` or process
        them however your text renderer expects.

        Parameters
        ----------
        style:
            Optional style dict applied to each highlight span.
            Defaults to ``{"background": (255, 255, 0)}``.
        """
        if style is None:
            style = {"background": (255, 255, 0)}
        return [
            {"start": m.start, "end": m.end, "text": m.text, "style": style}
            for m in matches
        ]
