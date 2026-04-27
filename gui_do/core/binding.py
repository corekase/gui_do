"""Binding — reactive two-way bridges between ObservableValue and widget properties.

A :class:`Binding` wires an :class:`~gui_do.ObservableValue` to a named
attribute on a target object (typically a control) so that changes on either
side propagate automatically.  A :class:`BindingGroup` collects multiple
bindings and disposes them together.

Usage::

    zoom = ObservableValue(1.0)

    # One-way: model → widget
    b = Binding(zoom, slider, "value", mode="one_way")

    # Two-way: model ↔ widget (widget publishes via on_change callback)
    b = Binding(zoom, slider, "value",
                mode="two_way",
                widget_change_signal="on_change")

    # Later dispose to stop receiving updates:
    b.dispose()

    # Group disposal:
    group = BindingGroup()
    group.add(Binding(zoom, slider, "value"))
    group.add(Binding(label_text, label, "text"))
    group.dispose()

Supported modes
---------------
- ``"one_way"`` (default): model value → widget attribute only.
- ``"one_way_to_source"``: widget attribute → model value only (requires
  ``widget_change_signal``).
- ``"two_way"``: bidirectional (requires ``widget_change_signal``).

``widget_change_signal`` must name a setter attribute on the target that
accepts a callable, e.g. ``"on_change"`` for
:class:`~gui_do.SliderControl`.  When the widget fires the callback the model
is updated, which in turn sets the widget attribute — a ``_updating`` guard
prevents infinite loops.

Type conversion
---------------
Pass ``to_widget`` and/or ``to_source`` callables to convert values between
model and widget representations, e.g. ``to_widget=int, to_source=float``.
"""
from __future__ import annotations

from typing import Any, Callable, List, Optional


BindingMode = str  # "one_way" | "one_way_to_source" | "two_way"

_VALID_MODES = ("one_way", "one_way_to_source", "two_way")


class Binding:
    """Reactive bridge between an :class:`~gui_do.ObservableValue` and a target attribute.

    Parameters
    ----------
    source:
        An :class:`~gui_do.ObservableValue` (or any object with ``subscribe``
        returning an unsubscribe callable and a ``.value`` property).
    target:
        The object whose attribute is driven (e.g. a control instance).
    attr:
        Name of the attribute on *target* to set (e.g. ``"value"``, ``"text"``).
    mode:
        ``"one_way"`` (default), ``"one_way_to_source"``, or ``"two_way"``.
    widget_change_signal:
        Name of the callback-setter attribute on *target* used to receive
        change notifications from the widget (e.g. ``"on_change"``).
        Required for ``"two_way"`` and ``"one_way_to_source"`` modes.
    to_widget:
        Optional converter applied to the source value before setting *attr*.
    to_source:
        Optional converter applied to the widget value before updating source.
    """

    def __init__(
        self,
        source,
        target: object,
        attr: str,
        *,
        mode: BindingMode = "one_way",
        widget_change_signal: Optional[str] = None,
        to_widget: Optional[Callable[[Any], Any]] = None,
        to_source: Optional[Callable[[Any], Any]] = None,
    ) -> None:
        if mode not in _VALID_MODES:
            raise ValueError(f"mode must be one of {_VALID_MODES!r}, got {mode!r}")
        if mode in ("two_way", "one_way_to_source") and widget_change_signal is None:
            raise ValueError(
                f"widget_change_signal is required for mode {mode!r}"
            )

        self._source = source
        self._target = target
        self._attr = str(attr)
        self._mode: BindingMode = mode
        self._widget_change_signal = widget_change_signal
        self._to_widget = to_widget
        self._to_source = to_source
        self._updating = False
        self._disposed = False
        self._unsub_source: Optional[Callable[[], None]] = None
        self._prev_widget_signal: Any = None

        self._setup()

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def _setup(self) -> None:
        mode = self._mode

        # Model → widget direction
        if mode in ("one_way", "two_way"):
            self._unsub_source = self._source.subscribe(self._on_source_changed)
            # Apply initial value immediately
            self._apply_to_widget(self._source.value)

        # Widget → model direction: hook the widget's change callback
        if mode in ("two_way", "one_way_to_source") and self._widget_change_signal is not None:
            self._install_widget_callback()

    def _install_widget_callback(self) -> None:
        """Save the existing callback (if any) and chain our own hook."""
        signal = self._widget_change_signal
        try:
            self._prev_widget_signal = getattr(self._target, signal)
        except AttributeError:
            self._prev_widget_signal = None
        setattr(self._target, signal, self._on_widget_changed)

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------

    def _on_source_changed(self, value: Any) -> None:
        if self._updating or self._disposed:
            return
        self._apply_to_widget(value)

    def _apply_to_widget(self, value: Any) -> None:
        converted = self._to_widget(value) if self._to_widget is not None else value
        self._updating = True
        try:
            setattr(self._target, self._attr, converted)
        finally:
            self._updating = False

    def _on_widget_changed(self, value: Any) -> None:
        # Forward to any previously registered widget callback first
        prev = self._prev_widget_signal
        if callable(prev):
            prev(value)
        if self._updating or self._disposed:
            return
        converted = self._to_source(value) if self._to_source is not None else value
        self._updating = True
        try:
            self._source.value = converted
        finally:
            self._updating = False

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def dispose(self) -> None:
        """Stop all change propagation and restore previous widget callbacks."""
        if self._disposed:
            return
        self._disposed = True
        if self._unsub_source is not None:
            self._unsub_source()
            self._unsub_source = None
        # Restore previous widget callback if we chained it
        if self._widget_change_signal is not None:
            try:
                setattr(self._target, self._widget_change_signal, self._prev_widget_signal)
            except AttributeError:
                pass

    @property
    def disposed(self) -> bool:
        return self._disposed

    # ------------------------------------------------------------------
    # Manual sync
    # ------------------------------------------------------------------

    def sync_to_widget(self) -> None:
        """Force an immediate model → widget synchronisation."""
        if not self._disposed and self._mode in ("one_way", "two_way"):
            self._apply_to_widget(self._source.value)

    def sync_to_source(self) -> None:
        """Force an immediate widget → model synchronisation."""
        if self._disposed or self._mode not in ("two_way", "one_way_to_source"):
            return
        value = getattr(self._target, self._attr, None)
        converted = self._to_source(value) if self._to_source is not None else value
        self._updating = True
        try:
            self._source.value = converted
        finally:
            self._updating = False


# ---------------------------------------------------------------------------
# BindingGroup — composite lifecycle for multiple bindings
# ---------------------------------------------------------------------------


class BindingGroup:
    """Collects :class:`Binding` instances and disposes them together.

    Usage::

        group = BindingGroup()
        group.add(Binding(model.name, name_input, "text",
                          mode="two_way", widget_change_signal="on_change"))
        group.add(Binding(model.volume, volume_slider, "value",
                          mode="two_way", widget_change_signal="on_change"))

        # When the form closes:
        group.dispose()
    """

    def __init__(self) -> None:
        self._bindings: List[Binding] = []

    def add(self, binding: Binding) -> Binding:
        """Register *binding* with this group and return it."""
        self._bindings.append(binding)
        return binding

    def dispose(self) -> None:
        """Dispose all registered bindings."""
        for binding in self._bindings:
            binding.dispose()
        self._bindings.clear()

    def sync_all_to_widget(self) -> None:
        """Force all bindings to re-synchronise their widget from the model."""
        for binding in self._bindings:
            binding.sync_to_widget()

    def __len__(self) -> int:
        return len(self._bindings)
