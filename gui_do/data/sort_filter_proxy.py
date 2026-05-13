"""SortFilterProxySource — reactive sort, filter, and group-by for VirtualItemSource.

Wraps any :class:`~gui_do.VirtualItemSource` (including :class:`~gui_do.FixedItemSource`
and :class:`~gui_do.ObservableList`) and applies composable filter, sort-key, and
optional group-by transforms.  The proxy re-computes its visible index list on
demand and notifies subscribers so data controls refresh automatically.

Usage::

    from gui_do import SortFilterProxySource, FixedItemSource, ListItem

    items = FixedItemSource([
        ListItem("Banana"),
        ListItem("Apple"),
        ListItem("Cherry"),
        ListItem("Apricot"),
    ])

    proxy = SortFilterProxySource(items)

    # Filter: only items whose text starts with 'A'
    proxy.set_filter(lambda item: item.text.startswith("A"))

    # Sort alphabetically
    proxy.set_sort_key(lambda item: item.text)

    proxy.subscribe(lambda: list_view.invalidate())

    # Use in a list view:
    list_view = ListViewControl("list", rect, source=proxy)

    # Change filter at runtime — subscribers are notified automatically:
    proxy.set_filter(None)   # clear filter

    # Attach to an ObservableList for live mutation tracking:
    obs = ObservableList([ListItem("X"), ListItem("Y")])
    proxy2 = SortFilterProxySource(obs)
    obs.subscribe(lambda _change: proxy2.invalidate())
"""
from __future__ import annotations

from typing import Any, Callable, Optional


class SortFilterProxySource:
    """A :class:`~gui_do.VirtualItemSource` decorator with reactive sort and filter.

    Parameters
    ----------
    source:
        Any object that implements ``item_count() -> int`` and
        ``item_at(index: int)`` (i.e. any :class:`~gui_do.VirtualItemSource`).
        :class:`~gui_do.ObservableList` is also supported — its ``__len__``
        and ``__getitem__`` are used when the protocol methods are absent.
    """

    def __init__(self, source: Any) -> None:
        self._source = source
        self._filter: Optional[Callable[[Any], bool]] = None
        self._sort_key: Optional[Callable[[Any], Any]] = None
        self._sort_reverse: bool = False
        self._visible: List[int] = []           # indices into raw source
        self._dirty: bool = True
        self._subscribers: List[Callable[[], None]] = []
        # Cache dispatch callables once so _raw_count/_source_item_at avoid
        # per-call hasattr lookups during _recompute().
        self._fn_raw_count = source.item_count if hasattr(source, "item_count") else lambda: len(source)
        self._fn_item_at = source.item_at if hasattr(source, "item_at") else source.__getitem__
        self._fn_item_height = source.item_height if hasattr(source, "item_height") else None

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    def set_filter(self, predicate: Optional[Callable[[Any], bool]]) -> None:
        """Set or clear the filter predicate.

        *predicate* receives each raw item and must return ``True`` to include it.
        Pass ``None`` to include all items.
        """
        self._filter = predicate
        self._invalidate()

    def set_sort_key(
        self,
        key_fn: Optional[Callable[[Any], Any]],
        *,
        reverse: bool = False,
    ) -> None:
        """Set or clear the sort key function.

        *key_fn* receives each raw item and returns a comparable sort key.
        Pass ``None`` to disable sorting (items appear in source order).
        """
        self._sort_key = key_fn
        self._sort_reverse = bool(reverse)
        self._invalidate()

    def invalidate(self) -> None:
        """Force recomputation on the next access (e.g. after source mutation)."""
        self._invalidate()

    # ------------------------------------------------------------------
    # Subscription
    # ------------------------------------------------------------------

    def subscribe(self, handler: Callable[[], None]) -> Callable[[], None]:
        """Register *handler* to be called after each recomputation.

        Returns an unsubscribe callable.
        """
        self._subscribers.append(handler)

        def _unsub() -> None:
            try:
                self._subscribers.remove(handler)
            except ValueError:
                pass

        return _unsub

    # ------------------------------------------------------------------
    # VirtualItemSource protocol
    # ------------------------------------------------------------------

    def item_count(self) -> int:
        """Return the number of visible items after filtering."""
        self._ensure_fresh()
        return len(self._visible)

    def item_at(self, index: int) -> Any:
        """Return the visible item at *index*."""
        self._ensure_fresh()
        raw_index = self._visible[index]
        return self._source_item_at(raw_index)

    def item_height(self, index: int) -> int:
        """Delegate item height to the underlying source when supported."""
        self._ensure_fresh()
        raw_index = self._visible[index]
        if self._fn_item_height is not None:
            return self._fn_item_height(raw_index)
        return 32

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _raw_count(self) -> int:
        return self._fn_raw_count()

    def _source_item_at(self, index: int) -> Any:
        return self._fn_item_at(index)

    def _invalidate(self) -> None:
        self._dirty = True
        subscribers = self._subscribers
        if not subscribers:
            return
        snapshot = subscribers if len(subscribers) == 1 else tuple(subscribers)
        for handler in snapshot:
            handler()

    def _ensure_fresh(self) -> None:
        if self._dirty:
            self._recompute()

    def _recompute(self) -> None:
        raw_count = self._raw_count()
        source_item_at = self._source_item_at
        predicate = self._filter
        sort_key = self._sort_key

        if predicate is None and sort_key is None:
            # No transform: expose all indices in source order.
            self._visible = list(range(raw_count))
            self._dirty = False
            return

        if predicate is not None and sort_key is None:
            # Filter-only fast path: single streaming pass, no pre-built pairs list.
            visible = []
            for i in range(raw_count):
                if predicate(source_item_at(i)):
                    visible.append(i)
            self._visible = visible
            self._dirty = False
            return

        if predicate is None:
            visible = list(range(raw_count))
        else:
            visible = []
            for i in range(raw_count):
                if predicate(source_item_at(i)):
                    visible.append(i)

        # Sort indices directly to avoid index-item tuple allocation.
        visible.sort(key=lambda idx: sort_key(source_item_at(idx)), reverse=self._sort_reverse)
        self._visible = visible
        self._dirty = False

    # ------------------------------------------------------------------
    # Inspection helpers
    # ------------------------------------------------------------------

    @property
    def source(self) -> Any:
        """The underlying data source."""
        return self._source

    @property
    def has_filter(self) -> bool:
        """``True`` when a filter predicate is active."""
        return self._filter is not None

    @property
    def has_sort(self) -> bool:
        """``True`` when a sort key is active."""
        return self._sort_key is not None
