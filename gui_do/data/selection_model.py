"""SelectionModel — shared observable selection state for data controls.

:class:`SelectionModel` decouples selection policy from rendering so that
multiple controls (a :class:`~gui_do.ListViewControl`, a preview pane, a
toolbar "N selected" label) can share a single source of truth and stay
synchronised automatically.

Modes
-----
- ``SINGLE`` — at most one item selected (default).
- ``MULTI``  — arbitrary set selected by toggling individual items.
- ``RANGE``  — anchor + active end defines a contiguous block.

Usage::

    model = SelectionModel(mode=SelectionMode.MULTI, item_count=100)
    unsub = model.subscribe(lambda m: list_view.invalidate())

    model.select(5)
    model.toggle(10)
    print(model.selected_indices)   # frozenset({5, 10})

    # Range selection (anchor at 3, active at 8 → selects 3-8):
    model2 = SelectionModel(mode=SelectionMode.RANGE, item_count=100)
    model2.set_anchor(3)
    model2.set_active(8)
    print(model2.selected_indices)  # frozenset({3, 4, 5, 6, 7, 8})
"""
from __future__ import annotations

from enum import Enum
from typing import Callable, Optional, Set


# ---------------------------------------------------------------------------
# SelectionMode
# ---------------------------------------------------------------------------


class SelectionMode(Enum):
    """Governs how many items may be selected simultaneously."""

    SINGLE = "single"
    MULTI = "multi"
    RANGE = "range"


# ---------------------------------------------------------------------------
# SelectionModel
# ---------------------------------------------------------------------------

SelectionChangeCallback = Callable[["SelectionModel"], None]


class SelectionModel:
    """Observable selection state for list, grid, and tree controls.

    Parameters
    ----------
    mode:
        Selection mode (``SINGLE``, ``MULTI``, or ``RANGE``).
    item_count:
        Total number of selectable items.  Updated via :meth:`set_item_count`.
    on_change:
        Optional initial subscriber called on every selection change.
    """

    def __init__(
        self,
        *,
        mode: SelectionMode = SelectionMode.SINGLE,
        item_count: int = 0,
        on_change: Optional[SelectionChangeCallback] = None,
    ) -> None:
        self._mode: SelectionMode = SelectionMode(mode) if isinstance(mode, str) else mode
        self._item_count: int = max(0, int(item_count))
        self._selected: Set[int] = set()
        self._anchor: Optional[int] = None
        self._active: Optional[int] = None
        self._listeners: List[SelectionChangeCallback] = []
        if on_change is not None:
            self._listeners.append(on_change)

    # ------------------------------------------------------------------
    # Subscription
    # ------------------------------------------------------------------

    def subscribe(self, callback: SelectionChangeCallback) -> Callable[[], None]:
        """Register *callback* for selection changes.

        Returns a no-arg callable that unsubscribes when called.
        """
        self._listeners.append(callback)

        def _unsub() -> None:
            try:
                self._listeners.remove(callback)
            except ValueError:
                pass

        return _unsub

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def mode(self) -> SelectionMode:
        """Current selection mode."""
        return self._mode

    @mode.setter
    def mode(self, value: SelectionMode) -> None:
        self._mode = SelectionMode(value) if isinstance(value, str) else value
        self.clear()

    @property
    def item_count(self) -> int:
        """Total number of selectable items."""
        return self._item_count

    def set_item_count(self, count: int) -> None:
        """Update total item count, pruning out-of-range selections."""
        self._item_count = max(0, int(count))
        out_of_range = {i for i in self._selected if i >= self._item_count}
        if out_of_range:
            self._selected -= out_of_range
            if self._anchor is not None and self._anchor >= self._item_count:
                self._anchor = None
            if self._active is not None and self._active >= self._item_count:
                self._active = None
            self._fire()

    @property
    def selected_indices(self) -> FrozenSet[int]:
        """Frozenset of currently selected indices."""
        if self._mode is SelectionMode.RANGE:
            return frozenset(self._range_set())
        return frozenset(self._selected)

    @property
    def selected_index(self) -> int:
        """Lowest selected index, or ``-1`` when nothing is selected."""
        indices = self.selected_indices
        return min(indices) if indices else -1

    @property
    def anchor(self) -> Optional[int]:
        """Range-selection anchor index (``RANGE`` mode)."""
        return self._anchor

    @property
    def active_end(self) -> Optional[int]:
        """Moving end of the range selection (``RANGE`` mode)."""
        return self._active

    # ------------------------------------------------------------------
    # Mutation API
    # ------------------------------------------------------------------

    def select(self, index: int) -> None:
        """Select *index*, clearing all others in ``SINGLE`` mode."""
        if not self._valid(index):
            return
        if self._mode is SelectionMode.SINGLE:
            if self._selected == {index}:
                return
            self._selected = {index}
        else:
            self._selected.add(index)
        self._anchor = index
        self._active = index
        self._fire()

    def deselect(self, index: int) -> None:
        """Deselect *index* (all modes)."""
        if index in self._selected:
            self._selected.discard(index)
            self._fire()

    def toggle(self, index: int) -> None:
        """Toggle selection of *index* (``MULTI`` and ``RANGE`` modes).

        In ``SINGLE`` mode behaves like :meth:`select`.
        """
        if not self._valid(index):
            return
        if self._mode is SelectionMode.SINGLE:
            new = set() if self._selected == {index} else {index}
            if new == self._selected:
                return
            self._selected = new
        else:
            if index in self._selected:
                self._selected.discard(index)
            else:
                self._selected.add(index)
        self._anchor = index
        self._active = index
        self._fire()

    def set_anchor(self, index: int) -> None:
        """Set the range anchor without changing the active end (``RANGE`` mode)."""
        if not self._valid(index):
            return
        self._anchor = index
        if self._active is None:
            self._active = index
        self._fire()

    def set_active(self, index: int) -> None:
        """Set the moving end of the range (``RANGE`` mode)."""
        if not self._valid(index):
            return
        self._active = index
        if self._anchor is None:
            self._anchor = index
        self._fire()

    def select_all(self) -> None:
        """Select all items."""
        new: Set[int] = set(range(self._item_count))
        if new == self._selected:
            return
        self._selected = new
        self._fire()

    def clear(self) -> None:
        """Deselect all items."""
        if not self._selected and self._anchor is None and self._active is None:
            return
        self._selected.clear()
        self._anchor = None
        self._active = None
        self._fire()

    def is_selected(self, index: int) -> bool:
        """Return whether *index* is currently selected."""
        return index in self.selected_indices

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _valid(self, index: int) -> bool:
        return 0 <= int(index) < self._item_count

    def _range_set(self) -> Set[int]:
        if self._anchor is None or self._active is None:
            return set(self._selected)
        lo = min(self._anchor, self._active)
        hi = max(self._anchor, self._active)
        return set(range(lo, hi + 1))

    def _fire(self) -> None:
        for cb in list(self._listeners):
            try:
                cb(self)
            except Exception:
                pass
