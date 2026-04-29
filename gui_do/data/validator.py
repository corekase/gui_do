"""Composable validator pipeline for data-entry controls and form fields.

A :class:`Validator` is a callable that inspects a value and returns a
:class:`ValidationResult`.  Validators compose into a :class:`ValidationPipeline`
that runs them in order, short-circuiting on the first failure or collecting
all failures, and optionally running an async check via :class:`AsyncValidator`.

Built-in validators
-------------------
- :class:`RequiredValidator`  — rejects ``None`` and empty strings
- :class:`RangeValidator`     — numeric min/max bounds (inclusive)
- :class:`LengthValidator`    — string / collection length bounds
- :class:`PatternValidator`   — regex pattern match
- :class:`CustomValidator`    — wraps any callable

Usage::

    from gui_do import (
        ValidationPipeline, ValidationResult,
        RequiredValidator, RangeValidator, LengthValidator, PatternValidator,
    )

    pipeline = ValidationPipeline([
        RequiredValidator("Name is required"),
        LengthValidator(min_length=2, max_length=64, message="2-64 characters"),
    ])

    result = pipeline.validate("Alice")
    print(result.ok)         # True
    print(result.errors)     # []

    result2 = pipeline.validate("")
    print(result2.ok)        # False
    print(result2.errors[0]) # "Name is required"

Cross-field validation::

    pipeline.add(DependentValidator(
        lambda v, context: "Username taken" if user_db.exists(v) else None,
    ))
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..scheduling.task_scheduler import TaskScheduler


# ---------------------------------------------------------------------------
# ValidationResult
# ---------------------------------------------------------------------------


@dataclass
class ValidationResult:
    """Outcome of running a :class:`ValidationPipeline` on a value.

    Attributes
    ----------
    ok:
        True when validation passed with no errors.
    errors:
        List of human-readable error messages collected during validation.
    """

    ok: bool
    errors: List[str] = field(default_factory=list)

    @classmethod
    def passed(cls) -> "ValidationResult":
        return cls(ok=True)

    @classmethod
    def failed(cls, *messages: str) -> "ValidationResult":
        return cls(ok=False, errors=list(messages))

    def __bool__(self) -> bool:
        return self.ok


# ---------------------------------------------------------------------------
# Validator protocol
# ---------------------------------------------------------------------------


ValidatorFn = Callable[[Any], Optional[str]]  # returns error message or None


class Validator:
    """Base class for a single validation rule.

    Subclass and override :meth:`check`, or use :class:`CustomValidator`
    to wrap a plain callable.
    """

    def check(self, value: Any) -> Optional[str]:
        """Return an error message string, or ``None`` if the value is valid."""
        return None  # pragma: no cover

    def __call__(self, value: Any) -> Optional[str]:
        return self.check(value)


# ---------------------------------------------------------------------------
# Built-in validators
# ---------------------------------------------------------------------------


class RequiredValidator(Validator):
    """Reject ``None`` and empty strings / collections."""

    def __init__(self, message: str = "This field is required.") -> None:
        self.message = str(message)

    def check(self, value: Any) -> Optional[str]:
        if value is None:
            return self.message
        if isinstance(value, (str, list, tuple, dict, set)) and len(value) == 0:
            return self.message
        return None


class RangeValidator(Validator):
    """Enforce numeric min/max bounds (inclusive).

    Parameters
    ----------
    min_value / max_value:
        Bounds (either may be ``None`` to skip that side).
    message:
        Custom error.  ``None`` auto-generates ``"Must be between X and Y"``.
    """

    def __init__(
        self,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        *,
        message: Optional[str] = None,
    ) -> None:
        self.min_value = min_value
        self.max_value = max_value
        self._message = message

    def check(self, value: Any) -> Optional[str]:
        try:
            v = float(value)
        except (TypeError, ValueError):
            return "Must be a number."
        if self.min_value is not None and v < self.min_value:
            return self._message or f"Must be at least {self.min_value}."
        if self.max_value is not None and v > self.max_value:
            return self._message or f"Must be at most {self.max_value}."
        return None


class LengthValidator(Validator):
    """Enforce string or collection length bounds.

    Parameters
    ----------
    min_length / max_length:
        Bounds (either may be ``None`` to skip).
    message:
        Custom error.
    """

    def __init__(
        self,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        *,
        message: Optional[str] = None,
    ) -> None:
        self.min_length = min_length
        self.max_length = max_length
        self._message = message

    def check(self, value: Any) -> Optional[str]:
        try:
            n = len(value)
        except TypeError:
            return "Value must have a length."
        if self.min_length is not None and n < self.min_length:
            return self._message or f"Must be at least {self.min_length} characters."
        if self.max_length is not None and n > self.max_length:
            return self._message or f"Must be at most {self.max_length} characters."
        return None


class PatternValidator(Validator):
    """Enforce a regex pattern match against a string value.

    Parameters
    ----------
    pattern:
        Regular expression string (compiled on first use).
    message:
        Error returned when the pattern does not match.
    full_match:
        If ``True`` (default) use ``re.fullmatch``; otherwise ``re.search``.
    """

    def __init__(
        self,
        pattern: str,
        *,
        message: str = "Invalid format.",
        full_match: bool = True,
    ) -> None:
        self._pattern = re.compile(str(pattern))
        self.message = str(message)
        self.full_match = full_match

    def check(self, value: Any) -> Optional[str]:
        text = str(value) if value is not None else ""
        fn = self._pattern.fullmatch if self.full_match else self._pattern.search
        if not fn(text):
            return self.message
        return None


class CustomValidator(Validator):
    """Wrap any callable as a :class:`Validator`.

    Parameters
    ----------
    fn:
        A callable ``(value) -> Optional[str]`` — return ``None`` for valid,
        a string error message for invalid.
    """

    def __init__(self, fn: ValidatorFn) -> None:
        if not callable(fn):
            raise TypeError("fn must be callable")
        self._fn = fn

    def check(self, value: Any) -> Optional[str]:
        return self._fn(value)


class DependentValidator(Validator):
    """Cross-field validator that receives the value and an optional context dict.

    Parameters
    ----------
    fn:
        A callable ``(value, context: dict) -> Optional[str]``.
    """

    def __init__(self, fn: Callable[[Any, dict], Optional[str]]) -> None:
        if not callable(fn):
            raise TypeError("fn must be callable")
        self._fn = fn

    def check(self, value: Any) -> Optional[str]:
        return self._fn(value, {})

    def check_with_context(self, value: Any, context: dict) -> Optional[str]:
        """Validate *value* with external *context* (e.g. other field values)."""
        return self._fn(value, context)


# ---------------------------------------------------------------------------
# ValidationPipeline
# ---------------------------------------------------------------------------


class ValidationPipeline:
    """Runs an ordered sequence of :class:`Validator` instances on a value.

    Parameters
    ----------
    validators:
        Ordered list of validators to apply.
    stop_on_first_error:
        If ``True`` (default) stop after the first failure.  Set to ``False``
        to collect all errors.

    Usage::

        p = ValidationPipeline([RequiredValidator(), RangeValidator(0, 100)])
        result = p.validate(42)    # ValidationResult(ok=True)
        result = p.validate(-1)    # ValidationResult(ok=False, errors=["Must be at least 0."])
    """

    def __init__(
        self,
        validators: Optional[List[Validator]] = None,
        *,
        stop_on_first_error: bool = True,
    ) -> None:
        self._validators: List[Validator] = list(validators) if validators else []
        self.stop_on_first_error = stop_on_first_error

    def add(self, validator: Validator) -> "ValidationPipeline":
        """Append *validator* to the pipeline and return ``self`` (fluent API)."""
        self._validators.append(validator)
        return self

    def validate(self, value: Any, *, context: Optional[dict] = None) -> ValidationResult:
        """Run all validators against *value* and return a :class:`ValidationResult`."""
        errors: List[str] = []
        for v in self._validators:
            if isinstance(v, DependentValidator) and context is not None:
                error = v.check_with_context(value, context)
            else:
                error = v.check(value)
            if error is not None:
                errors.append(error)
                if self.stop_on_first_error:
                    return ValidationResult(ok=False, errors=errors)
        if errors:
            return ValidationResult(ok=False, errors=errors)
        return ValidationResult(ok=True)

    def is_valid(self, value: Any, *, context: Optional[dict] = None) -> bool:
        """Convenience: return True iff *value* passes all validators."""
        return self.validate(value, context=context).ok

    @property
    def validators(self) -> List[Validator]:
        return list(self._validators)
