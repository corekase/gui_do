"""VirtualItemSource — protocol for on-demand item rendering in data controls.

Data controls (:class:`~gui_do.ListViewControl`, :class:`~gui_do.DataGridControl`,
:class:`~gui_do.TreeControl`) accept an optional *source* argument that implements
:class:`VirtualItemSource`.  The control only calls :meth:`~VirtualItemSource.item_at`
for the indices currently visible in the viewport, so sources may fetch pages
lazily, compute items on demand, or delegate to an async data provider.

Built-in source
---------------
:class:`FixedItemSource` wraps a plain Python list and is suitable for small
to medium datasets where all items are already in memory.

Usage::

    from gui_do import ListViewControl, FixedItemSource, ListItem

    source = FixedItemSource([
        ListItem("Alpha"),
        ListItem("Beta"),
        ListItem("Gamma"),
    ])

    list_view = ListViewControl("list", rect, source=source)

    # Add an item at runtime:
    source.append(ListItem("Delta"))
    list_view.invalidate()

Custom source::

    class MyPagedSource:
        def item_count(self) -> int:
            return self._total_rows   # known from initial query

        def item_at(self, index: int):
            page = index // PAGE_SIZE
            if page not in self._cache:
                self._cache[page] = self._fetch_page(page)
            return self._cache[page][index % PAGE_SIZE]

        def item_height(self, index: int) -> int:
            return 32   # uniform rows
"""
from __future__ import annotations

from typing import Generic, List, Optional, Protocol, TypeVar, runtime_checkable


T = TypeVar("T")


# ---------------------------------------------------------------------------
# VirtualItemSource protocol
# ---------------------------------------------------------------------------


@runtime_checkable
class VirtualItemSource(Protocol[T]):
    """Protocol for lazy/on-demand item data sources consumed by data controls.

    Controls call :meth:`item_count` once per layout pass and :meth:`item_at`
    only for currently visible indices, so large or remote datasets remain
    efficient.

    The optional :meth:`item_height` method enables variable-height rows when
    present; controls that support it check ``hasattr(source, "item_height")``.
    """

    def item_count(self) -> int:
        """Return the total number of items available."""
        ...

    def item_at(self, index: int) -> T:
        """Return the item at zero-based *index*.

        Implementations may raise ``IndexError`` for out-of-range access.
        """
        ...


# ---------------------------------------------------------------------------
# FixedItemSource
# ---------------------------------------------------------------------------


class FixedItemSource(Generic[T]):
    """A :class:`VirtualItemSource` backed by a plain Python list.

    All items live in memory.  Suitable for datasets where all items are
    known upfront or small enough to hold in RAM.

    Parameters
    ----------
    items:
        Initial list of items.  Copied on construction.
    row_height:
        Uniform row height returned by :meth:`item_height`.  ``0`` means
        controls should use their own default height.
    """

    def __init__(
        self,
        items: Optional[List[T]] = None,
        *,
        row_height: int = 0,
    ) -> None:
        self._items: List[T] = list(items) if items else []
        self._row_height: int = max(0, int(row_height))

    # ------------------------------------------------------------------
    # VirtualItemSource protocol
    # ------------------------------------------------------------------

    def item_count(self) -> int:
        """Return the number of items."""
        return len(self._items)

    def item_at(self, index: int) -> T:
        """Return the item at *index*."""
        return self._items[index]

    def item_height(self, index: int) -> int:  # noqa: ARG002
        """Return the uniform row height (0 = use control default)."""
        return self._row_height

    # ------------------------------------------------------------------
    # Mutation helpers
    # ------------------------------------------------------------------

    def set_items(self, items: List[T]) -> None:
        """Replace all items with *items*."""
        self._items = list(items)

    def append(self, item: T) -> None:
        """Append *item* to the end of the list."""
        self._items.append(item)

    def insert(self, index: int, item: T) -> None:
        """Insert *item* before *index*."""
        self._items.insert(index, item)

    def remove_at(self, index: int) -> None:
        """Remove the item at *index*."""
        del self._items[index]

    def replace(self, index: int, item: T) -> None:
        """Replace the item at *index* with *item*."""
        self._items[index] = item

    def clear(self) -> None:
        """Remove all items."""
        self._items.clear()

    def snapshot(self) -> List[T]:
        """Return a copy of the current item list."""
        return list(self._items)
