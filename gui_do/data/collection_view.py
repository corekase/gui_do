"""Collection view — reusable filter/sort/project pipeline over iterable sources."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Optional


CollectionPredicate = Callable[[Any], bool]
CollectionSorter = Callable[[Any], Any]
CollectionProjector = Callable[[Any], Any]
RefreshCallback = Callable[[], None]


@dataclass(slots=True)
class CollectionViewQuery:
    filters: List[CollectionPredicate] = field(default_factory=list)
    sort_key: Optional[CollectionSorter] = None
    reverse: bool = False
    projector: Optional[CollectionProjector] = None


class CollectionView:
    """Materialized collection pipeline used by list/tree/grid style consumers."""

    _IMMUTABLE_SOURCE_TYPES = (tuple, range, frozenset, str, bytes)

    def __init__(self, source: Iterable[Any] | Callable[[], Iterable[Any]], *, query: CollectionViewQuery | None = None) -> None:
        self._source = source
        self._query = query or CollectionViewQuery()
        self._items: List[Any] = []
        self._refresh_subscribers: Dict[int, RefreshCallback] = {}
        self._next_sub_id: int = 0
        self._last_source_obj: Any = None
        self._last_query_signature: Optional[tuple[Any, ...]] = None
        self._has_materialized: bool = False
        self._refresh_initial()

    @property
    def query(self) -> CollectionViewQuery:
        return self._query

    @property
    def items(self) -> List[Any]:
        return list(self._items)

    def iter_items(self) -> Iterable[Any]:
        return iter(self._items)

    def count(self) -> int:
        return len(self._items)

    def subscribe(self, callback: RefreshCallback) -> Callable[[], None]:
        """Register *callback* to be called after every :meth:`refresh`.

        Returns an unsub callable that removes the subscription when called.
        """
        sub_id = self._next_sub_id
        self._next_sub_id += 1
        self._refresh_subscribers[sub_id] = callback

        def _unsub() -> None:
            self._refresh_subscribers.pop(sub_id, None)

        return _unsub

    def _refresh_initial(self) -> None:
        """Internal: materialize items without notifying subscribers (used in __init__)."""
        self._materialize()

    def _query_signature(self) -> tuple[Any, ...]:
        filters = self._query.filters
        return (
            tuple(id(predicate) for predicate in filters),
            self._query.sort_key,
            self._query.reverse,
            self._query.projector,
        )

    def _materialize(self) -> None:
        source_obj = self._source() if callable(self._source) else self._source
        query_signature = self._query_signature()

        # Safe fast path: only reuse when the source object is immutable and
        # both source identity and query transform chain are unchanged.
        if (
            self._has_materialized
            and isinstance(source_obj, self._IMMUTABLE_SOURCE_TYPES)
            and source_obj is self._last_source_obj
            and query_signature == self._last_query_signature
        ):
            return

        items = list(source_obj)
        filters = self._query.filters
        if filters:
            if len(filters) == 1:
                predicate = filters[0]
                items = [item for item in items if predicate(item)]
            else:
                filtered: List[Any] = []
                for item in items:
                    for predicate in filters:
                        if not predicate(item):
                            break
                    else:
                        filtered.append(item)
                items = filtered
        if self._query.sort_key is not None:
            items.sort(key=self._query.sort_key, reverse=self._query.reverse)
        if self._query.projector is not None:
            items = [self._query.projector(item) for item in items]
        self._items = items
        self._last_source_obj = source_obj
        self._last_query_signature = query_signature
        self._has_materialized = True

    def refresh(self) -> List[Any]:
        self._materialize()
        if self._refresh_subscribers:
            # Iterate values directly; subscriber self-removal during callback
            # is not supported (would require a snapshot copy).
            for callback in self._refresh_subscribers.values():
                callback()
        return list(self._items)

    def set_source(self, source: Iterable[Any] | Callable[[], Iterable[Any]]) -> None:
        self._source = source
        self.refresh()

    def add_filter(self, predicate: CollectionPredicate) -> None:
        self._query.filters.append(predicate)
        self.refresh()

    def clear_filters(self) -> None:
        self._query.filters.clear()
        self.refresh()

    def set_sort(self, sort_key: Optional[CollectionSorter], *, reverse: bool = False) -> None:
        self._query.sort_key = sort_key
        self._query.reverse = bool(reverse)
        self.refresh()

    def set_projector(self, projector: Optional[CollectionProjector]) -> None:
        self._query.projector = projector
        self.refresh()

    def snapshot(self) -> List[Any]:
        return self.items

    def bind_observable_list(self, obs: Any) -> Callable[[], None]:
        """Wire *obs* (an :class:`~gui_do.ObservableList`) as the live source.

        Sets the source to ``obs.snapshot`` so items are re-read from the
        observable list on each refresh, then subscribes to its change events
        so any mutation automatically triggers :meth:`refresh` (and thereby
        notifies all of this view's own subscribers).

        Returns an unsubscribe callable.  Call it to detach the live binding.
        The CollectionView source remains pointing at ``obs.snapshot`` after
        unsubscribing; only the auto-refresh hook is removed.
        """
        self.set_source(obs.snapshot)
        return obs.subscribe(lambda _change: self.refresh())
