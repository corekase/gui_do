from __future__ import annotations

from typing import Any, Callable, Generic, List, Optional, TypeVar

# Imported lazily inside methods to avoid circular import during module init.
import gui_do.data.reactive_batch as _batch_mod


T = TypeVar("T")
Observer = Callable[[T], None]

# ---------------------------------------------------------------------------
# Auto-tracking context
# ---------------------------------------------------------------------------

# Module-level tracker context.  When a ComputedValue is evaluating its
# compute_fn, it sets _current_tracker to itself so that any ObservableValue
# whose .value getter is called during that evaluation can automatically
# register the ComputedValue as a subscriber.  This eliminates the need for
# the explicit ``deps=[...]`` list.
_current_tracker: Optional["_AutoTrackingComputedMixin"] = None


class _AutoTrackingComputedMixin:
    """Internal mixin used by ComputedValue for dependency auto-registration."""

    def _register_as_dep(self, observable: "ObservableValue") -> None:  # pragma: no cover
        raise NotImplementedError


# ---------------------------------------------------------------------------
# ObservableValue
# ---------------------------------------------------------------------------


class ObservableValue(Generic[T]):
    """Minimal observable value used by presentation models."""

    def __init__(self, value: T) -> None:
        self._value = value
        self._observers: list[Observer[T]] = []

    @property
    def value(self) -> T:
        # Auto-tracking: if a ComputedValue is actively evaluating, register
        # this observable as one of its dependencies so changes here
        # automatically invalidate the computed result.
        if _current_tracker is not None:
            _current_tracker._register_as_dep(self)
        return self._value

    @value.setter
    def value(self, new_value: T) -> None:
        if self._value == new_value:
            return
        self._value = new_value
        if _batch_mod.is_batching():
            _batch_mod._enqueue(self)
        else:
            self._notify_observers()

    def _notify_observers(self) -> None:
        """Fire all registered observers with the current value."""
        observers = self._observers
        n = len(observers)
        if n == 0:
            return
        if n == 1:
            observers[0](self._value)
            return
        for observer in tuple(observers):
            observer(self._value)

    def set_silently(self, new_value: T) -> None:
        """Update the stored value without notifying any observers."""
        self._value = new_value

    def force_notify(self) -> None:
        """Notify all observers with the current value, even if it has not changed."""
        observers = self._observers
        n = len(observers)
        if n == 0:
            return
        if n == 1:
            observers[0](self._value)
            return
        for observer in tuple(observers):
            observer(self._value)

    @property
    def observer_count(self) -> int:
        """Return the number of active observer subscriptions."""
        return len(self._observers)

    def subscribe(self, observer: Observer[T]) -> Callable[[], None]:
        self._observers.append(observer)

        def _unsubscribe() -> None:
            try:
                self._observers.remove(observer)
            except ValueError:
                pass

        return _unsubscribe


# ---------------------------------------------------------------------------
# PresentationModel
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# ComputedValue (with auto-tracking)
# ---------------------------------------------------------------------------


class ComputedValue(Generic[T], _AutoTrackingComputedMixin):
    """A read-only reactive value derived from one or more observable dependencies.

    Re-computes lazily when any dependency changes and notifies subscribers.

    Dependencies may be declared explicitly via *deps* **or** discovered
    automatically: any :class:`ObservableValue` whose ``.value`` attribute is
    read during the *compute_fn* evaluation is automatically registered as a
    dependency.  The two approaches can be mixed freely.

    Usage (explicit deps -- unchanged API)::

        a = ObservableValue(1)
        b = ObservableValue(2)
        total = ComputedValue(lambda: a.value + b.value, deps=[a, b])
        total.subscribe(lambda v: print("total:", v))
        a.value = 10  # prints "total: 12"

    Usage (auto-tracking -- no deps list needed)::

        total = ComputedValue(lambda: a.value + b.value)
        # Dependencies are discovered on the first evaluation.

    Notes
    -----
    - Auto-tracked deps are discovered on the **first** evaluation and on
      every re-evaluation after a dep changes, so conditional paths that
      read different observables in different branches are handled correctly.
    - Passing an explicit *deps* list **and** relying on auto-tracking
      simultaneously is supported; explicit deps are always registered,
      auto-tracked deps complement them.
    """

    def __init__(
        self,
        compute_fn: Callable[[], T],
        deps: Optional[List] = None,
    ) -> None:
        self._compute_fn = compute_fn
        self._observers: List[Observer[T]] = []
        self._cached: Optional[T] = None
        self._dirty: bool = True
        self._unsub_fns: List[Callable[[], None]] = []
        # Set of observables already subscribed to avoid duplicate subscriptions
        self._tracked_ids: set = set()

        for dep in (deps or []):
            self._force_register_dep(dep)

    # ------------------------------------------------------------------
    # _AutoTrackingComputedMixin implementation
    # ------------------------------------------------------------------

    def _register_as_dep(self, observable: "ObservableValue") -> None:
        """Register *observable* as a dependency if not already subscribed."""
        oid = id(observable)
        if oid in self._tracked_ids:
            return
        self._tracked_ids.add(oid)
        self._unsub_fns.append(observable.subscribe(self._on_dep_changed))

    def _force_register_dep(self, dep: "ObservableValue") -> None:
        """Register an explicitly supplied dependency."""
        self._register_as_dep(dep)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _on_dep_changed(self, _ignored: Any) -> None:
        self._dirty = True
        new_value = self.value
        observers = self._observers
        n = len(observers)
        if n == 0:
            return
        if n == 1:
            observers[0](new_value)
            return
        for observer in tuple(observers):
            observer(new_value)

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    @property
    def value(self) -> T:
        """Return the current computed value, recomputing if any dep changed."""
        # Auto-tracking: if another ComputedValue is evaluating, register self
        # so that when this computed value changes, the outer one is invalidated.
        if _current_tracker is not None and _current_tracker is not self:
            _current_tracker._register_as_dep(self)  # type: ignore[arg-type]
        if self._dirty:
            self._cached = self._evaluate()
            self._dirty = False
        return self._cached  # type: ignore[return-value]

    def _evaluate(self) -> T:
        """Run compute_fn under the auto-tracking context."""
        global _current_tracker  # noqa: PLW0603
        previous = _current_tracker
        _current_tracker = self
        try:
            return self._compute_fn()
        finally:
            _current_tracker = previous

    def subscribe(self, observer: Observer[T]) -> Callable[[], None]:
        """Subscribe to value changes. Returns an unsubscribe callable."""
        self._observers.append(observer)

        def _unsub() -> None:
            try:
                self._observers.remove(observer)
            except ValueError:
                pass

        return _unsub

    def dispose(self) -> None:
        """Remove all dependency subscriptions and clear observers."""
        for unsub in self._unsub_fns:
            unsub()
        self._unsub_fns.clear()
        self._tracked_ids.clear()
        self._observers.clear()
