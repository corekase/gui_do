"""AppStateStore — transactional, selector-driven application state store.

Provides a single source of truth for mutable application state with:

* :class:`StatePatch` — typed dict delta applied in a single commit
* :class:`StateTransaction` — context manager for batching multiple patches
* :class:`StateSelector` — reactive derived slice via an extractor function
* :class:`AppStateStore` — dispatch/select/subscribe/snapshot/restore
"""
from __future__ import annotations

import copy
import threading
from typing import Any, Callable, Dict, Generic, List, Optional, TypeVar

__all__ = ["AppStateStore", "StateSelector", "StatePatch", "StateTransaction"]

T = TypeVar("T")

# A patch is simply a flat dict of key→value updates.
StatePatch = Dict[str, Any]


# ---------------------------------------------------------------------------
# StateSelector
# ---------------------------------------------------------------------------


class StateSelector(Generic[T]):
    """Derived reactive view of a slice of the :class:`AppStateStore`.

    The selector re-evaluates *extractor* whenever the store changes and
    notifies subscribers only if the derived value actually changed.

    Parameters
    ----------
    extractor:
        ``(state: dict) -> T`` — pure function that projects the state dict
        to the value of interest.
    initial_state:
        Starting state dict used to compute the initial cached value.
    depends_on:
        Optional set of state keys that this selector depends on. If provided,
        the selector only re-evaluates when one of these keys changes. If None,
        the selector re-evaluates on every patch (classic behavior, safer but slower).
    """

    def __init__(
        self,
        extractor: Callable[[Dict[str, Any]], T],
        initial_state: Dict[str, Any],
        depends_on: set[str] | None = None,
    ) -> None:
        self._extractor = extractor
        self._cached: T = extractor(initial_state)
        self._listeners: List[Callable[[T], None]] = []
        self._depends_on: set[str] | None = depends_on

    @property
    def value(self) -> T:
        """The most recently computed value."""
        return self._cached

    def subscribe(self, callback: Callable[[T], None]) -> Callable[[], None]:
        """Register *callback* to be called whenever the derived value changes.

        Returns an unsubscribe callable.
        """
        self._listeners.append(callback)

        def _unsub() -> None:
            try:
                self._listeners.remove(callback)
            except ValueError:
                pass

        return _unsub

    # ------------------------------------------------------------------
    # Internal — called by the store
    # ------------------------------------------------------------------

    def _update(self, new_state: Dict[str, Any], changed_keys: List[str] | None = None) -> None:
        """Update the selector if its dependencies changed.

        Args:
            new_state: New state dict to evaluate
            changed_keys: List of keys that changed in this patch. If provided and
                          _depends_on is set, only updates if overlap exists.
                          If changed_keys is None, always updates (legacy behavior).
        """
        # Legacy behavior: if no changed_keys provided, always update.
        # (Used for backward compatibility with code that calls _update without changed_keys)
        if changed_keys is None:
            new_val = self._extractor(new_state)
            if new_val != self._cached:
                self._cached = new_val
                for cb in list(self._listeners):
                    cb(new_val)
            return

        # Dependency-aware update: only recompute if a dependency changed.
        if self._depends_on is None:
            # No dependencies declared: conservative, always update
            new_val = self._extractor(new_state)
            if new_val != self._cached:
                self._cached = new_val
                for cb in list(self._listeners):
                    cb(new_val)
        elif any(key in self._depends_on for key in changed_keys):
            # At least one dependency changed: update
            new_val = self._extractor(new_state)
            if new_val != self._cached:
                self._cached = new_val
                for cb in list(self._listeners):
                    cb(new_val)


# ---------------------------------------------------------------------------
# AppStateStore
# ---------------------------------------------------------------------------


class AppStateStore:
    """Centralised application state store.

    State is stored as a flat or nested ``dict``.  Callers dispatch
    :data:`StatePatch` dicts which are shallow-merged into the store.
    Selectors and key-based subscribers are notified after each commit.

    Thread Safety
    -------------
    Dispatch and snapshot are protected by an internal :class:`threading.Lock`.
    Subscriber callbacks are invoked *while the lock is held* — keep them
    short and non-blocking.
    """

    def __init__(self, initial_state: Optional[Dict[str, Any]] = None) -> None:
        self._state: Dict[str, Any] = dict(initial_state or {})
        self._lock = threading.Lock()
        self._key_subs: Dict[str, List[Callable[[Any], None]]] = {}
        self._selectors: List[StateSelector] = []
        self._pending_patches: Optional[List[StatePatch]] = None  # set during tx

    # ------------------------------------------------------------------
    # Dispatch
    # ------------------------------------------------------------------

    def dispatch(self, patch: StatePatch) -> None:
        """Apply *patch* to the store and notify subscribers.

        Inside a :class:`StateTransaction` context the patch is queued and
        all queued patches are applied atomically when the transaction exits.
        """
        with self._lock:
            if self._pending_patches is not None:
                # Defer until transaction commits
                self._pending_patches.append(patch)
                return
            self._apply(patch)

    def _apply(self, patch: StatePatch) -> None:
        """Apply one patch and fire notifications (must be called under lock)."""
        changed_keys: List[str] = []
        for key, value in patch.items():
            if self._state.get(key) != value:
                self._state[key] = value
                changed_keys.append(key)

        if not changed_keys:
            return

        # Key-based subscribers
        for key in changed_keys:
            for cb in list(self._key_subs.get(key, [])):
                cb(self._state[key])

        # Selectors — only snapshot state if selectors are registered (optimization for hot path).
        if self._selectors:
            state_snapshot = dict(self._state)
            for sel in list(self._selectors):
                # Pass changed_keys to selector so it can short-circuit if it has no dependencies on them.
                sel._update(state_snapshot, changed_keys=changed_keys)

    # ------------------------------------------------------------------
    # Selectors
    # ------------------------------------------------------------------

    def select(self, extractor: Callable[[Dict[str, Any]], T], depends_on: set[str] | None = None) -> StateSelector[T]:
        """Create and register a :class:`StateSelector` backed by *extractor*.

        Args:
            extractor: Function to extract/compute the derived value from state.
            depends_on: Optional set of state keys this selector depends on. If provided,
                       the selector only re-evaluates when one of these keys changes.
                       If None, re-evaluates on every state change (safe but slower).
        """
        sel: StateSelector[T] = StateSelector(extractor, dict(self._state), depends_on=depends_on)
        with self._lock:
            self._selectors.append(sel)
        return sel

    # ------------------------------------------------------------------
    # Key subscriptions
    # ------------------------------------------------------------------

    def subscribe(self, key: str, callback: Callable[[Any], None]) -> Callable[[], None]:
        """Subscribe to changes on a specific top-level *key*.

        Returns an unsubscribe callable.
        """
        with self._lock:
            self._key_subs.setdefault(key, []).append(callback)

        def _unsub() -> None:
            with self._lock:
                bucket = self._key_subs.get(key, [])
                try:
                    bucket.remove(callback)
                except ValueError:
                    pass

        return _unsub

    # ------------------------------------------------------------------
    # Snapshot / restore
    # ------------------------------------------------------------------

    def snapshot(self) -> Dict[str, Any]:
        """Return a deep copy of the current state."""
        with self._lock:
            return copy.deepcopy(self._state)

    def restore(self, snapshot: Dict[str, Any]) -> None:
        """Replace the entire state with *snapshot* and notify all subscribers."""
        with self._lock:
            self._state = copy.deepcopy(snapshot)
            state_copy = dict(self._state)
            for key, callbacks in self._key_subs.items():
                if key in state_copy:
                    for cb in list(callbacks):
                        cb(state_copy[key])
            for sel in list(self._selectors):
                sel._update(state_copy)

    # ------------------------------------------------------------------
    # Direct read (no reactive tracking)
    # ------------------------------------------------------------------

    def get(self, key: str, default: Any = None) -> Any:
        """Return the current value of *key* without subscribing."""
        with self._lock:
            return self._state.get(key, default)

    # ------------------------------------------------------------------
    # Transaction support (internal)
    # ------------------------------------------------------------------

    def _begin_transaction(self) -> None:
        with self._lock:
            if self._pending_patches is not None:
                raise RuntimeError("Nested transactions are not supported")
            self._pending_patches = []

    def _commit_transaction(self) -> None:
        with self._lock:
            patches = self._pending_patches
            self._pending_patches = None
            if patches:
                # Merge all patches into one then apply
                merged: StatePatch = {}
                for p in patches:
                    merged.update(p)
                self._apply(merged)

    def _rollback_transaction(self) -> None:
        with self._lock:
            self._pending_patches = None


# ---------------------------------------------------------------------------
# StateTransaction
# ---------------------------------------------------------------------------


class StateTransaction:
    """Context manager that batches multiple :meth:`AppStateStore.dispatch` calls.

    All dispatched patches are merged and applied atomically on exit.
    If the body raises an exception the patches are discarded (rollback).

    Example::

        with StateTransaction(store):
            store.dispatch({"x": 1})
            store.dispatch({"y": 2})
        # subscribers fire once, with both changes
    """

    __slots__ = ("_store",)

    def __init__(self, store: AppStateStore) -> None:
        self._store = store

    def __enter__(self) -> "StateTransaction":
        self._store._begin_transaction()
        return self

    def __exit__(self, exc_type: Any, *_: Any) -> None:
        if exc_type is None:
            self._store._commit_transaction()
        else:
            self._store._rollback_transaction()
