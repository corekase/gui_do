from __future__ import annotations

from typing import Callable, Generic, TypeVar


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
