from __future__ import annotations

from typing import Any, Callable, Generic, List, Optional, TypeVar


T = TypeVar("T")
Observer = Callable[[T], None]


class ObservableValue(Generic[T]):
    """Minimal observable value used by presentation models."""

    def __init__(self, value: T) -> None:
        self._value = value
        self._observers: list[Observer[T]] = []

    @property
    def value(self) -> T:
        return self._value

    @value.setter
    def value(self, new_value: T) -> None:
        if self._value == new_value:
            return
        self._value = new_value
        for observer in list(self._observers):
            observer(self._value)

    def set_silently(self, new_value: T) -> None:
        """Update the stored value without notifying any observers."""
        self._value = new_value

    def force_notify(self) -> None:
        """Notify all observers with the current value, even if it has not changed."""
        for observer in list(self._observers):
            observer(self._value)

    @property
    def observer_count(self) -> int:
        """Return the number of active observer subscriptions."""
        return len(self._observers)

    def subscribe(self, observer: Observer[T]) -> Callable[[], None]:
        self._observers.append(observer)

        def _unsubscribe() -> None:
            if observer in self._observers:
                self._observers.remove(observer)

        return _unsubscribe


class PresentationModel:
    """Base class for view-independent presentation state containers."""

    def __init__(self) -> None:
        self._subscriptions: list[Callable[[], None]] = []

    def bind(self, observable: ObservableValue[T], observer: Observer[T]) -> None:
        self._subscriptions.append(observable.subscribe(observer))

    def dispose(self) -> None:
        for unsubscribe in self._subscriptions:
            unsubscribe()
        self._subscriptions.clear()


class ComputedValue(Generic[T]):
    """A read-only reactive value derived from one or more observable dependencies.

    Re-computes lazily when any dependency changes and notifies subscribers.

    Usage::

        a = ObservableValue(1)
        b = ObservableValue(2)
        total = ComputedValue(lambda: a.value + b.value, deps=[a, b])
        total.subscribe(lambda v: print("total:", v))
        a.value = 10  # prints "total: 12"
        print(total.value)  # 12
    """

    def __init__(self, compute_fn: Callable[[], T], deps: List) -> None:
        self._compute_fn = compute_fn
        self._observers: List[Observer[T]] = []
        self._cached: Optional[T] = None
        self._dirty: bool = True
        self._unsub_fns: List[Callable[[], None]] = []
        for dep in deps:
            self._unsub_fns.append(dep.subscribe(self._on_dep_changed))

    def _on_dep_changed(self, _ignored: Any) -> None:
        self._dirty = True
        new_value = self.value
        for observer in list(self._observers):
            observer(new_value)

    @property
    def value(self) -> T:
        """Return the current computed value, recomputing if any dep changed."""
        if self._dirty:
            self._cached = self._compute_fn()
            self._dirty = False
        return self._cached  # type: ignore[return-value]

    def subscribe(self, observer: Observer[T]) -> Callable[[], None]:
        """Subscribe to value changes. Returns an unsubscribe callable."""
        self._observers.append(observer)

        def _unsub() -> None:
            if observer in self._observers:
                self._observers.remove(observer)

        return _unsub

    def dispose(self) -> None:
        """Remove all dependency subscriptions and clear observers."""
        for unsub in self._unsub_fns:
            unsub()
        self._unsub_fns.clear()
        self._observers.clear()
