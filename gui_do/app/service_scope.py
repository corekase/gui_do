"""ServiceScope — typed scoped dependency injection registry.

Provides hierarchical service scopes where child scopes inherit parent
bindings but can override them locally.  A ``ScopeStack`` manages a
push/pop-based scope hierarchy with context-manager support.
"""
from __future__ import annotations

from typing import Generic, Optional, TypeVar, List

__all__ = ["ServiceKey", "ServiceScope", "ScopeStack"]

T = TypeVar("T")


class ServiceKey(Generic[T]):
    """Typed key for a service binding.

    Two keys with the same *name* are considered equal, regardless of the
    type parameter (which is erased at runtime but aids static analysis).
    """

    __slots__ = ("name",)

    def __init__(self, name: str) -> None:
        if not name:
            raise ValueError("ServiceKey name must be non-empty")
        self.name: str = name

    def __repr__(self) -> str:
        return f"ServiceKey({self.name!r})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, ServiceKey) and self.name == other.name

    def __hash__(self) -> int:
        return hash(self.name)


class ServiceScope:
    """Dict-backed service registry with optional parent inheritance.

    Child scopes delegate misses to the parent; bindings set on a child
    shadow the parent without mutating it.  ``dispose()`` calls
    ``dispose()`` on all *locally-owned* instances that expose the method.
    """

    def __init__(self, parent: Optional["ServiceScope"] = None) -> None:
        self._parent = parent
        self._bindings: dict[ServiceKey, object] = {}
        self._owned: List[object] = []

    # ------------------------------------------------------------------
    # Binding / resolution
    # ------------------------------------------------------------------

    def bind(self, key: ServiceKey[T], instance: T, *, owned: bool = True) -> None:
        """Register *instance* under *key* in this scope.

        If *owned* is ``True`` (default) the scope will call
        ``instance.dispose()`` when :meth:`dispose` is invoked.
        """
        self._bindings[key] = instance
        if owned and hasattr(instance, "dispose") and callable(instance.dispose):
            self._owned.append(instance)

    def get(self, key: ServiceKey[T]) -> T:
        """Return the instance bound to *key*, raising ``KeyError`` if missing."""
        value = self._lookup(key)
        if value is _MISSING:
            raise KeyError(key)
        return value  # type: ignore[return-value]

    def get_optional(self, key: ServiceKey[T]) -> Optional[T]:
        """Return the instance bound to *key*, or ``None`` if not found."""
        value = self._lookup(key)
        return None if value is _MISSING else value  # type: ignore[return-value]

    def _lookup(self, key: ServiceKey) -> object:
        if key in self._bindings:
            return self._bindings[key]
        if self._parent is not None:
            return self._parent._lookup(key)
        return _MISSING

    # ------------------------------------------------------------------
    # Scope hierarchy
    # ------------------------------------------------------------------

    def child(self) -> "ServiceScope":
        """Return a new child scope that inherits this scope's bindings."""
        return ServiceScope(parent=self)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def dispose(self) -> None:
        """Dispose all locally-owned instances in LIFO order."""
        for instance in reversed(self._owned):
            try:
                instance.dispose()
            except Exception:
                pass
        self._owned.clear()
        self._bindings.clear()


class _MissingSentinel:
    """Sentinel for missing lookup results (avoids ``None`` ambiguity)."""
    __slots__ = ()


_MISSING = _MissingSentinel()


class ScopeStack:
    """Push/pop scope hierarchy with context-manager support.

    The *root* scope is always present.  Each :meth:`push` creates and
    activates a new child scope; :meth:`pop` disposes it and returns to
    the parent.

    Example::

        stack = ScopeStack()
        with stack.push() as child:
            child.bind(MY_KEY, MyService())
            # child scope active here
        # child disposed automatically on exit
    """

    def __init__(self) -> None:
        self._root = ServiceScope()
        self._stack: List[ServiceScope] = [self._root]

    @property
    def current(self) -> ServiceScope:
        """The innermost active scope."""
        return self._stack[-1]

    @property
    def root(self) -> ServiceScope:
        """The root (outermost) scope."""
        return self._root

    def push(self) -> "_PushedScope":
        """Push a new child scope onto the stack and return a context manager."""
        return _PushedScope(self)

    def _push_raw(self) -> ServiceScope:
        child = self._stack[-1].child()
        self._stack.append(child)
        return child

    def _pop_raw(self) -> None:
        if len(self._stack) <= 1:
            raise RuntimeError("Cannot pop the root scope")
        scope = self._stack.pop()
        scope.dispose()


class _PushedScope:
    """Context manager returned by :meth:`ScopeStack.push`."""

    __slots__ = ("_stack", "_scope")

    def __init__(self, stack: ScopeStack) -> None:
        self._stack = stack
        self._scope: Optional[ServiceScope] = None

    def __enter__(self) -> ServiceScope:
        self._scope = self._stack._push_raw()
        return self._scope

    def __exit__(self, *_: object) -> None:
        self._stack._pop_raw()
