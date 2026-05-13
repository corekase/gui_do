"""VirtualizationCore — unified list/tree/grid windowing engine.

Provides the building blocks for virtualised UI controls:

* :class:`MeasurePolicy` — strategy for computing item heights
* :class:`VirtualizedWindow` — visible range calculator with overscan
* :class:`RecyclePool` — generic typed pool for reusing view cells
* :class:`VirtualizationCore` — combines window + pool + identity tracking
"""
from __future__ import annotations

from enum import Enum, auto
from typing import Callable, Generic, TypeVar

__all__ = [
    "MeasurePolicy",
    "VirtualizedWindow",
    "RecyclePool",
    "VirtualizationCore",
]

T = TypeVar("T")


# ---------------------------------------------------------------------------
# MeasurePolicy
# ---------------------------------------------------------------------------


class MeasureMode(Enum):
    """Whether all items share the same height or have variable heights."""

    UNIFORM = auto()
    VARIABLE = auto()


class MeasurePolicy:
    """Strategy object for computing item positions and heights.

    Parameters
    ----------
    mode:
        ``UNIFORM`` — all items have the same height; ``VARIABLE`` — each item
        has its own height supplied by *height_fn*.
    item_height:
        The fixed height used in ``UNIFORM`` mode.
    height_fn:
        ``(item_index: int) -> int`` used in ``VARIABLE`` mode.
    """

    def __init__(
        self,
        mode: MeasureMode = MeasureMode.UNIFORM,
        item_height: int = 30,
        height_fn: Optional[Callable[[int], int]] = None,
    ) -> None:
        self.mode = mode
        self.item_height = item_height
        self.height_fn = height_fn

    def get_height(self, index: int) -> int:
        """Return the pixel height of item at *index*."""
        if self.mode == MeasureMode.UNIFORM:
            return self.item_height
        if self.height_fn is not None:
            return self.height_fn(index)
        return self.item_height

    def total_height(self, item_count: int) -> int:
        """Return the total scroll height for *item_count* items."""
        if self.mode == MeasureMode.UNIFORM:
            return item_count * self.item_height
        return sum(self.get_height(i) for i in range(item_count))

    def item_at_offset(self, offset: int, item_count: int) -> int:
        """Return the index of the item visible at scroll *offset* pixels."""
        if item_count == 0:
            return 0
        if self.mode == MeasureMode.UNIFORM:
            idx = offset // max(self.item_height, 1)
            return max(0, min(idx, item_count - 1))
        cumulative = 0
        for i in range(item_count):
            h = self.get_height(i)
            if cumulative + h > offset:
                return i
            cumulative += h
        return item_count - 1

    def offset_of_item(self, index: int) -> int:
        """Return the pixel offset (top) of item *index*."""
        if self.mode == MeasureMode.UNIFORM:
            return index * self.item_height
        return sum(self.get_height(i) for i in range(index))


# ---------------------------------------------------------------------------
# VirtualizedWindow
# ---------------------------------------------------------------------------


class VirtualizedWindow:
    """Computes which item indices are currently visible given scroll state.

    Parameters
    ----------
    viewport_height:
        The pixel height of the scrollable viewport.
    overscan:
        Extra items to render above/below the visible region (avoids
        pop-in on rapid scrolling).
    policy:
        The :class:`MeasurePolicy` used to calculate item offsets.
    """

    def __init__(
        self,
        viewport_height: int,
        overscan: int = 2,
        policy: Optional[MeasurePolicy] = None,
    ) -> None:
        self._viewport_height = viewport_height
        self._overscan = overscan
        self._policy = policy or MeasurePolicy()
        self._scroll_offset: int = 0
        self._item_count: int = 0

    @property
    def policy(self) -> MeasurePolicy:
        return self._policy

    def update(self, *, scroll_offset: int, item_count: int) -> None:
        """Notify the window of new scroll position and item count."""
        self._scroll_offset = max(0, scroll_offset)
        self._item_count = max(0, item_count)

    def visible_range(self) -> Tuple[int, int]:
        """Return ``(first_index, last_index)`` inclusive of visible items.

        Includes overscan.  Both values are clamped to ``[0, item_count)``.
        """
        if self._item_count == 0:
            return (0, -1)  # empty range

        first = self._policy.item_at_offset(self._scroll_offset, self._item_count)
        first = max(0, first - self._overscan)

        end_offset = self._scroll_offset + self._viewport_height
        last = self._policy.item_at_offset(end_offset, self._item_count)
        last = min(self._item_count - 1, last + self._overscan)

        return (first, last)

    @property
    def visible_count(self) -> int:
        first, last = self.visible_range()
        if last < first:
            return 0
        return last - first + 1


# ---------------------------------------------------------------------------
# RecyclePool
# ---------------------------------------------------------------------------


class RecyclePool(Generic[T]):
    """Typed pool for recycling view cells.

    Parameters
    ----------
    factory:
        Callable that creates a new cell instance when the pool is empty.
    reset_fn:
        Optional callable ``(cell: T) -> None`` called on reclaimed cells
        before they are returned to callers.
    """

    def __init__(
        self,
        factory: Callable[[], T],
        reset_fn: Optional[Callable[[T], None]] = None,
    ) -> None:
        self._factory = factory
        self._reset_fn = reset_fn
        self._pool: List[T] = []

    def acquire(self) -> T:
        """Return a cell from the pool or create a new one."""
        if self._pool:
            cell = self._pool.pop()
        else:
            cell = self._factory()
        return cell

    def release(self, cell: T) -> None:
        """Return *cell* to the pool, optionally resetting it."""
        if self._reset_fn is not None:
            self._reset_fn(cell)
        self._pool.append(cell)

    @property
    def pool_size(self) -> int:
        """Number of cells currently waiting in the pool."""
        return len(self._pool)


# ---------------------------------------------------------------------------
# VirtualizationCore
# ---------------------------------------------------------------------------


class VirtualizationCore(Generic[T]):
    """Combines :class:`VirtualizedWindow`, :class:`RecyclePool`, and identity tracking.

    Manages a set of *active cells* (one per visible item) and recycles
    cells that scroll out of view.

    Parameters
    ----------
    window:
        Configured :class:`VirtualizedWindow`.
    pool:
        Typed :class:`RecyclePool` for the cell type.
    bind_fn:
        ``(cell: T, item_index: int) -> None`` — binds a cell to data.
    """

    def __init__(
        self,
        window: VirtualizedWindow,
        pool: RecyclePool[T],
        bind_fn: Callable[[T, int], None],
    ) -> None:
        self._window = window
        self._pool = pool
        self._bind_fn = bind_fn
        self._active: dict[int, T] = {}  # index → cell

    @property
    def window(self) -> VirtualizedWindow:
        return self._window

    @property
    def pool(self) -> RecyclePool[T]:
        return self._pool

    def refresh(self, *, scroll_offset: int, item_count: int) -> List[Tuple[int, T]]:
        """Update scroll state and return the list of ``(index, cell)`` pairs
        that should be rendered this frame.

        Cells that go out of range are released back to the pool; new cells
        are acquired and bound.
        """
        self._window.update(scroll_offset=scroll_offset, item_count=item_count)
        first, last = self._window.visible_range()

        if last < first:
            # Nothing visible — recycle all
            for cell in self._active.values():
                self._pool.release(cell)
            self._active.clear()
            return []

        active = self._active
        # Release cells no longer needed
        for idx in tuple(active.keys()):
            if idx < first or idx > last:
                self._pool.release(active.pop(idx))

        # Acquire cells for newly visible indices
        for idx in range(first, last + 1):
            if idx in active:
                continue
            cell = self._pool.acquire()
            self._bind_fn(cell, idx)
            active[idx] = cell

        return [(idx, active[idx]) for idx in range(first, last + 1)]
