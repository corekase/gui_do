import inspect
from typing import Callable, Literal, Optional, TypeVar, Union

from .value_change_reason import ValueChangeReason

TValue = TypeVar("TValue")
ValueOnlyCallback = Callable[[TValue], None]
ValueReasonCallback = Callable[[TValue, ValueChangeReason], None]
ValueChangeCallback = Union[ValueOnlyCallback[TValue], ValueReasonCallback[TValue]]
ValueChangeCallbackMode = Literal["compat", "reason-required"]
VALUE_CHANGE_CALLBACK_MODES: tuple[ValueChangeCallbackMode, ...] = ("compat", "reason-required")


def normalize_value_change_callback_mode(mode: str) -> ValueChangeCallbackMode:
    """Validate and normalize callback dispatch mode values."""
    normalized = str(mode).strip().lower()
    if normalized not in VALUE_CHANGE_CALLBACK_MODES:
        raise ValueError(f"unsupported callback mode: {mode!r}")
    return normalized  # type: ignore[return-value]


def _accepts_reason(callback: Callable) -> bool:
    try:
        signature = inspect.signature(callback)
    except (TypeError, ValueError):
        return False
    for parameter in signature.parameters.values():
        if parameter.kind == inspect.Parameter.VAR_POSITIONAL:
            return True
    positional = [
        parameter
        for parameter in signature.parameters.values()
        if parameter.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
    ]
    return len(positional) >= 2


def dispatch_value_change(
    callback: Optional[ValueChangeCallback[TValue]],
    value: TValue,
    reason: ValueChangeReason,
    mode: ValueChangeCallbackMode = "compat",
) -> None:
    """Invoke a value-change callback with backward-compatible arity handling."""
    if callback is None:
        return
    mode = normalize_value_change_callback_mode(mode)
    accepts_reason = _accepts_reason(callback)
    if mode == "reason-required" and not accepts_reason:
        raise TypeError("on_change callback must accept (value, reason) when mode='reason-required'")
    if accepts_reason:
        callback(value, reason)
        return
    callback(value)
