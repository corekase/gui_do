from typing import Callable, Optional, TypeVar

from .value_change_reason import ValueChangeReason

TValue = TypeVar("TValue")
ValueChangeCallback = Callable[[TValue, ValueChangeReason], None]


def validate_value_change_callback(callback: Optional[ValueChangeCallback[TValue]]) -> None:
    """Raise TypeError if callback is not None and not callable."""
    if callback is not None and not callable(callback):
        raise TypeError("on_change callback must be callable or None")


def dispatch_value_change(
    callback: Optional[ValueChangeCallback[TValue]],
    value: TValue,
    reason: ValueChangeReason,
) -> None:
    """Invoke a value-change callback with (value, reason)."""
    if callback is None:
        return
    callback(value, reason)
