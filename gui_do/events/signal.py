"""Signal — typed class-level event descriptor for UiNode subclasses.

A :class:`Signal` declared as a class attribute on any object provides:

- Type-safe ``connect`` / ``disconnect`` lifecycle management
- Automatic interop with :class:`~gui_do.Binding` via ``control_change_signal``
- Discoverability via :class:`~gui_do.PropertyInspectorModel`
- Zero-cost emit when there are no connections

Usage::

    from gui_do import Signal, SignalConnection

    class MySlider(SliderControl):
        value_changed: Signal[float] = Signal()
        range_changed: Signal[tuple] = Signal()

    slider = MySlider(...)

    # Connect:
    conn = slider.value_changed.connect(lambda v: print("value:", v))

    # Emit (usually called inside the control):
    slider.value_changed.emit(3.14)

    # Disconnect:
    conn.disconnect()

    # Or disconnect by callable:
    slider.value_changed.disconnect(my_callback)

    # Connect once (auto-disconnects after first emit):
    slider.value_changed.connect_once(lambda v: do_something(v))

Binding interop::

    from gui_do import Binding, ObservableValue

    zoom = ObservableValue(1.0)
    # two-way binding using signal name
    b = Binding(zoom, slider, "value", mode="two_way",
                control_change_signal="value_changed")
"""
from __future__ import annotations

from typing import Any, Callable, Generic, Optional, TypeVar, List

T = TypeVar("T")


class SignalConnection:
    """A handle to an active signal connection.

    Call :meth:`disconnect` to remove the callback.
    """

    __slots__ = ("_signal_instance", "_callback", "_once")

    def __init__(
        self,
        signal_instance: "_SignalInstance",
        callback: Callable,
        *,
        once: bool = False,
    ) -> None:
        self._signal_instance = signal_instance
        self._callback = callback
        self._once = once

    def disconnect(self) -> None:
        """Remove this connection from the signal."""
        self._signal_instance._remove(self._callback)

    @property
    def callback(self) -> Callable:
        return self._callback


class _SignalInstance(Generic[T]):
    """Per-instance signal state stored on the owning object."""

    def __init__(self) -> None:
        self._callbacks: List[Callable[[T], Any]] = []
        self._callbacks_snapshot: tuple[Callable[[T], Any], ...] = ()
        self._callbacks_dirty: bool = False
        self._once: List[Callable[[T], Any]] = []

    def connect(self, callback: Callable[[T], Any]) -> SignalConnection:
        """Register *callback* and return a :class:`SignalConnection` handle."""
        if not callable(callback):
            raise TypeError("callback must be callable")
        if callback not in self._callbacks:
            self._callbacks.append(callback)
            self._callbacks_dirty = True
        return SignalConnection(self, callback)

    def connect_once(self, callback: Callable[[T], Any]) -> SignalConnection:
        """Register *callback* to fire exactly once, then auto-disconnect."""
        if not callable(callback):
            raise TypeError("callback must be callable")
        if callback not in self._once:
            self._once.append(callback)
        return SignalConnection(self, callback, once=True)

    def disconnect(self, callback: Callable[[T], Any]) -> None:
        """Remove *callback* (no-op if not connected)."""
        self._remove(callback)

    def disconnect_all(self) -> None:
        """Remove all connections."""
        self._callbacks.clear()
        self._callbacks_snapshot = ()
        self._callbacks_dirty = False
        self._once.clear()

    def emit(self, value: T) -> None:
        """Fire all connected callbacks with *value*."""
        # Copy lists so that connect/disconnect inside callbacks is safe.
        callbacks = self._callbacks
        if callbacks:
            if len(callbacks) == 1:
                snapshot = callbacks
            else:
                if self._callbacks_dirty:
                    self._callbacks_snapshot = tuple(callbacks)
                    self._callbacks_dirty = False
                snapshot = self._callbacks_snapshot
            for cb in snapshot:
                cb(value)
        once = self._once
        if once:
            self._once = []
            for cb in once:
                cb(value)

    def _remove(self, callback: Callable) -> None:
        try:
            self._callbacks.remove(callback)
            self._callbacks_dirty = True
        except ValueError:
            pass
        try:
            self._once.remove(callback)
        except ValueError:
            pass

    @property
    def connection_count(self) -> int:
        return len(self._callbacks) + len(self._once)


class Signal(Generic[T]):
    """Class-level descriptor that gives each instance its own :class:`_SignalInstance`.

    Declare as a class variable::

        class MyWidget(UiNode):
            clicked: Signal[tuple] = Signal()
            value_changed: Signal[float] = Signal()

    Access via an instance returns the per-instance :class:`_SignalInstance` so
    that ``widget.clicked.connect(...)`` and ``widget.clicked.emit(pos)`` work
    correctly across all instances of ``MyWidget``.
    """

    _ATTR_PREFIX = "_signal_"

    def __set_name__(self, owner: type, name: str) -> None:
        self._name = name
        self._attr = self._ATTR_PREFIX + name

    def __get__(self, obj: Any, objtype: Optional[type] = None) -> "_SignalInstance[T]":
        if obj is None:
            # Class-level access — return descriptor itself for introspection
            return self  # type: ignore[return-value]
        instance = obj.__dict__.get(self._attr)
        if instance is None:
            instance = _SignalInstance()
            obj.__dict__[self._attr] = instance
        return instance

    def __set__(self, obj: Any, value: Any) -> None:
        raise AttributeError(
            f"Signal '{self._name}' is a descriptor and cannot be reassigned. "
            "Use signal.connect(...) or signal.emit(...)."
        )

    # Descriptor metadata for PropertyInspector
    @property
    def signal_name(self) -> str:
        return getattr(self, "_name", "")
