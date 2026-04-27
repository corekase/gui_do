"""ObservableList and ObservableDict — reactive collection primitives.

These mirror the :class:`~gui_do.ObservableValue` API but for mutable
collections.  Mutations fire registered listeners with a
:class:`CollectionChange` event describing what changed.

Usage::

    items = ObservableList([ListItem("Alpha"), ListItem("Beta")])
    unsub = items.subscribe(lambda change: list_view.set_items(items.snapshot()))

    items.append(ListItem("Gamma"))   # fires listener
    items.remove_at(0)                # fires listener

    settings = ObservableDict({"volume": 1.0})
    settings.subscribe(lambda change: print(change.key, "->", change.new_value))
    settings["volume"] = 0.5         # fires listener
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    Iterable,
    Iterator,
    List,
    Optional,
    TypeVar,
)

T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")

# ---------------------------------------------------------------------------
# Change descriptor
# ---------------------------------------------------------------------------


class ChangeKind(Enum):
    """The type of mutation that triggered a :class:`CollectionChange`."""

    ADDED = "added"
    REMOVED = "removed"
    REPLACED = "replaced"
    CLEARED = "cleared"
    MOVED = "moved"


@dataclass(frozen=True)
class CollectionChange:
    """Describes a single mutation to an observable collection.

    Attributes:
        kind:       The mutation type.
        index:      List index (``ObservableList`` mutations).  ``None`` for
                    dict mutations and ``CLEARED`` events.
        key:        Dict key (``ObservableDict`` mutations).  ``None`` for list
                    mutations and ``CLEARED`` events.
        old_value:  Value before the mutation (``REMOVED`` / ``REPLACED`` /
                    ``MOVED`` events).
        new_value:  Value after the mutation (``ADDED`` / ``REPLACED`` events).
        new_index:  Destination index for ``MOVED`` events.
    """

    kind: ChangeKind
    index: Optional[int] = None
    key: Optional[Any] = None
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    new_index: Optional[int] = None


ChangeListener = Callable[[CollectionChange], None]

# ---------------------------------------------------------------------------
# ObservableList
# ---------------------------------------------------------------------------


class ObservableList(Generic[T]):
    """A mutable list that notifies subscribers on every structural change.

    Supports the same mutation surface as a plain Python list plus a few extras
    (``remove_at``, ``move``, ``replace``).  Read operations (iteration, length,
    indexing) work without triggering notifications.

    Usage::

        lst = ObservableList([1, 2, 3])
        unsub = lst.subscribe(lambda ch: print(ch.kind, ch.new_value))
        lst.append(4)          # fires ADDED
        lst[0] = 10            # fires REPLACED
        lst.remove_at(1)       # fires REMOVED
        print(lst.snapshot())  # [10, 3, 4]
        unsub()                # stop receiving notifications
    """

    def __init__(self, initial: Optional[Iterable[T]] = None) -> None:
        self._items: List[T] = list(initial) if initial is not None else []
        self._listeners: List[ChangeListener] = []

    # ------------------------------------------------------------------
    # Subscription
    # ------------------------------------------------------------------

    def subscribe(self, listener: ChangeListener) -> Callable[[], None]:
        """Register *listener* and return an unsubscribe callable."""
        if not callable(listener):
            raise ValueError("listener must be callable")
        self._listeners.append(listener)

        def _unsub() -> None:
            if listener in self._listeners:
                self._listeners.remove(listener)

        return _unsub

    @property
    def listener_count(self) -> int:
        return len(self._listeners)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _notify(self, change: CollectionChange) -> None:
        for listener in list(self._listeners):
            listener(change)

    # ------------------------------------------------------------------
    # Read operations (non-notifying)
    # ------------------------------------------------------------------

    def __len__(self) -> int:
        return len(self._items)

    def __getitem__(self, index: int) -> T:
        return self._items[index]

    def __iter__(self) -> Iterator[T]:
        return iter(self._items)

    def __contains__(self, item: object) -> bool:
        return item in self._items

    def index(self, item: T) -> int:
        """Return the first index of *item*, raising ``ValueError`` if absent."""
        return self._items.index(item)

    def snapshot(self) -> List[T]:
        """Return a shallow copy of the current list contents."""
        return list(self._items)

    # ------------------------------------------------------------------
    # Mutation operations (all notify listeners)
    # ------------------------------------------------------------------

    def append(self, item: T) -> None:
        """Append *item* to the end of the list."""
        self._items.append(item)
        self._notify(CollectionChange(kind=ChangeKind.ADDED, index=len(self._items) - 1, new_value=item))

    def insert(self, index: int, item: T) -> None:
        """Insert *item* before position *index*."""
        self._items.insert(index, item)
        self._notify(CollectionChange(kind=ChangeKind.ADDED, index=index, new_value=item))

    def remove_at(self, index: int) -> T:
        """Remove and return the item at *index*."""
        old = self._items.pop(index)
        self._notify(CollectionChange(kind=ChangeKind.REMOVED, index=index, old_value=old))
        return old

    def remove(self, item: T) -> bool:
        """Remove the first occurrence of *item*. Returns ``True`` if found."""
        try:
            idx = self._items.index(item)
        except ValueError:
            return False
        self._items.pop(idx)
        self._notify(CollectionChange(kind=ChangeKind.REMOVED, index=idx, old_value=item))
        return True

    def replace(self, index: int, new_item: T) -> T:
        """Replace the item at *index* with *new_item*. Returns the old item."""
        old = self._items[index]
        self._items[index] = new_item
        self._notify(CollectionChange(kind=ChangeKind.REPLACED, index=index, old_value=old, new_value=new_item))
        return old

    def __setitem__(self, index: int, item: T) -> None:
        self.replace(index, item)

    def move(self, from_index: int, to_index: int) -> None:
        """Move item at *from_index* to *to_index* (before removal adjustment)."""
        n = len(self._items)
        if from_index < 0 or from_index >= n:
            raise IndexError(f"from_index {from_index} out of range for list of length {n}")
        if to_index < 0 or to_index >= n:
            raise IndexError(f"to_index {to_index} out of range for list of length {n}")
        if from_index == to_index:
            return
        item = self._items.pop(from_index)
        self._items.insert(to_index, item)
        self._notify(CollectionChange(kind=ChangeKind.MOVED, index=from_index, old_value=item, new_index=to_index))

    def extend(self, items: Iterable[T]) -> None:
        """Append all items from *items*, firing one ADDED event per item."""
        for item in items:
            self.append(item)

    def clear(self) -> None:
        """Remove all items and fire a single CLEARED event."""
        if not self._items:
            return
        self._items.clear()
        self._notify(CollectionChange(kind=ChangeKind.CLEARED))

    def set_all(self, items: Iterable[T]) -> None:
        """Replace all contents atomically: clear then extend, two notifications."""
        self.clear()
        self.extend(items)

    def sort(self, *, key: Optional[Callable[[T], Any]] = None, reverse: bool = False) -> None:
        """Sort the list in-place, firing CLEARED then ADDED events for each item.

        For simplicity a single CLEARED + N ADDED events are fired rather than
        trying to compute a permutation sequence.  Control code that caches item
        state should rebuild from the updated snapshot in the CLEARED handler.
        """
        self._items.sort(key=key, reverse=reverse)
        self._notify(CollectionChange(kind=ChangeKind.CLEARED))
        for i, item in enumerate(self._items):
            self._notify(CollectionChange(kind=ChangeKind.ADDED, index=i, new_value=item))

    def __repr__(self) -> str:  # pragma: no cover
        return f"ObservableList({self._items!r})"


# ---------------------------------------------------------------------------
# ObservableDict
# ---------------------------------------------------------------------------


class ObservableDict(Generic[K, V]):
    """A mutable dict that notifies subscribers on every structural change.

    Supports standard dict mutation operations.  Read operations are
    non-notifying.

    Usage::

        d = ObservableDict({"volume": 1.0, "muted": False})
        unsub = d.subscribe(lambda ch: print(ch.key, "changed"))
        d["volume"] = 0.5        # fires REPLACED
        d["pitch"] = 1.2         # fires ADDED
        del d["muted"]           # fires REMOVED
        d.clear()                # fires CLEARED
        unsub()
    """

    def __init__(self, initial: Optional[Dict[K, V]] = None) -> None:
        self._data: Dict[K, V] = dict(initial) if initial is not None else {}
        self._listeners: List[ChangeListener] = []

    # ------------------------------------------------------------------
    # Subscription
    # ------------------------------------------------------------------

    def subscribe(self, listener: ChangeListener) -> Callable[[], None]:
        """Register *listener* and return an unsubscribe callable."""
        if not callable(listener):
            raise ValueError("listener must be callable")
        self._listeners.append(listener)

        def _unsub() -> None:
            if listener in self._listeners:
                self._listeners.remove(listener)

        return _unsub

    @property
    def listener_count(self) -> int:
        return len(self._listeners)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _notify(self, change: CollectionChange) -> None:
        for listener in list(self._listeners):
            listener(change)

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    def __len__(self) -> int:
        return len(self._data)

    def __getitem__(self, key: K) -> V:
        return self._data[key]

    def __contains__(self, key: object) -> bool:
        return key in self._data

    def get(self, key: K, default: Optional[V] = None) -> Optional[V]:
        return self._data.get(key, default)  # type: ignore[arg-type]

    def keys(self):
        return self._data.keys()

    def values(self):
        return self._data.values()

    def items(self):
        return self._data.items()

    def __iter__(self) -> Iterator[K]:
        return iter(self._data)

    def snapshot(self) -> Dict[K, V]:
        """Return a shallow copy of the current dict."""
        return dict(self._data)

    # ------------------------------------------------------------------
    # Mutation operations
    # ------------------------------------------------------------------

    def __setitem__(self, key: K, value: V) -> None:
        if key in self._data:
            old = self._data[key]
            self._data[key] = value
            self._notify(CollectionChange(kind=ChangeKind.REPLACED, key=key, old_value=old, new_value=value))
        else:
            self._data[key] = value
            self._notify(CollectionChange(kind=ChangeKind.ADDED, key=key, new_value=value))

    def __delitem__(self, key: K) -> None:
        old = self._data.pop(key)
        self._notify(CollectionChange(kind=ChangeKind.REMOVED, key=key, old_value=old))

    def pop(self, key: K, *args) -> V:
        """Remove and return *key*. Accepts an optional default like ``dict.pop``."""
        if key not in self._data:
            if args:
                return args[0]
            raise KeyError(key)
        old = self._data.pop(key)
        self._notify(CollectionChange(kind=ChangeKind.REMOVED, key=key, old_value=old))
        return old

    def update(self, mapping: Dict[K, V]) -> None:
        """Update from *mapping*, firing one event per key."""
        for k, v in mapping.items():
            self[k] = v

    def setdefault(self, key: K, default: V) -> V:
        """Set *key* to *default* if absent. Returns the existing or new value."""
        if key not in self._data:
            self[key] = default
        return self._data[key]

    def clear(self) -> None:
        """Remove all entries and fire a single CLEARED event."""
        if not self._data:
            return
        self._data.clear()
        self._notify(CollectionChange(kind=ChangeKind.CLEARED))

    def __repr__(self) -> str:  # pragma: no cover
        return f"ObservableDict({self._data!r})"
