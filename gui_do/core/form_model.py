"""FormModel — reactive form fields with validation and dirty tracking."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Generic, List, Optional, Sequence, Tuple, TypeVar

from .presentation_model import ObservableValue


T = TypeVar("T")

# A ValidationRule accepts a value and returns an error string (or None if valid).
ValidationRule = Callable[[Any], Optional[str]]


@dataclass
class FieldError:
    """Holds a validation error for a named field."""

    field_name: str
    message: str


class FormField(Generic[T]):
    """A single form field wrapping an :class:`ObservableValue` with validators.

    Tracks dirty state, exposes validate / commit / reset operations, and
    notifies listeners on error-state changes.
    """

    def __init__(
        self,
        name: str,
        initial_value: T,
        *,
        validators: Optional[Sequence[ValidationRule]] = None,
        required: bool = False,
    ) -> None:
        self._name: str = name
        self._committed_value: T = initial_value
        self.value: ObservableValue[T] = ObservableValue(initial_value)
        self._validators: List[ValidationRule] = list(validators or [])
        self._required: bool = required
        self._errors: List[str] = []
        self._on_errors_changed: List[Callable[[List[str]], None]] = []

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def name(self) -> str:
        return self._name

    @property
    def is_dirty(self) -> bool:
        return self.value.value != self._committed_value

    @property
    def is_valid(self) -> bool:
        return len(self._errors) == 0

    @property
    def errors(self) -> List[str]:
        return list(self._errors)

    @property
    def first_error(self) -> Optional[str]:
        return self._errors[0] if self._errors else None

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def add_validator(self, rule: ValidationRule) -> None:
        """Append a validator to this field."""
        self._validators.append(rule)

    def validate(self) -> bool:
        """Run all validators against the current value.  Returns True if valid."""
        errors: List[str] = []
        current = self.value.value
        if self._required and not current:
            errors.append("This field is required.")
        for rule in self._validators:
            try:
                result = rule(current)
            except Exception:
                result = "Validator error."
            if result is not None:
                errors.append(result)
        old_errors = self._errors
        self._errors = errors
        if old_errors != errors:
            for cb in list(self._on_errors_changed):
                try:
                    cb(self._errors)
                except Exception:
                    pass
        return len(self._errors) == 0

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def commit(self) -> None:
        """Accept the current value as the new committed baseline."""
        self._committed_value = self.value.value

    def reset(self) -> None:
        """Revert to the last committed value, clearing any errors."""
        self.value.value = self._committed_value
        old_errors = self._errors
        self._errors = []
        if old_errors:
            for cb in list(self._on_errors_changed):
                try:
                    cb(self._errors)
                except Exception:
                    pass

    # ------------------------------------------------------------------
    # Subscriptions
    # ------------------------------------------------------------------

    def on_errors_changed(self, callback: Callable[[List[str]], None]) -> Callable[[], None]:
        """Subscribe to error-list changes.  Returns an unsubscribe callable."""
        self._on_errors_changed.append(callback)

        def _unsubscribe() -> None:
            if callback in self._on_errors_changed:
                self._on_errors_changed.remove(callback)

        return _unsubscribe


class FormModel:
    """Collection of :class:`FormField` instances with cross-field validation.

    Typical usage::

        form = FormModel()
        name = form.add_field("name", "", required=True)
        age  = form.add_field("age", 0)

        form.validate_all()
        if form.is_valid:
            form.commit_all()
    """

    def __init__(self) -> None:
        self._fields: dict[str, FormField[Any]] = {}
        self._cross_validators: List[Callable[["FormModel"], Optional[List[FieldError]]]] = []
        self._cross_errors: List[FieldError] = []

    # ------------------------------------------------------------------
    # Field management
    # ------------------------------------------------------------------

    def add_field(
        self,
        name: str,
        initial_value: T,
        *,
        validators: Optional[Sequence[ValidationRule]] = None,
        required: bool = False,
    ) -> "FormField[T]":
        """Create, register, and return a new :class:`FormField`."""
        f: FormField[T] = FormField(
            name,
            initial_value,
            validators=validators,
            required=required,
        )
        self._fields[name] = f
        return f

    def field(self, name: str) -> FormField[Any]:
        """Return the :class:`FormField` registered under *name*."""
        return self._fields[name]

    @property
    def fields(self) -> dict[str, FormField[Any]]:
        return dict(self._fields)

    # ------------------------------------------------------------------
    # Cross-field validation
    # ------------------------------------------------------------------

    def add_cross_validator(
        self, rule: Callable[["FormModel"], Optional[List[FieldError]]]
    ) -> None:
        """Register a cross-field validator.

        The callable receives this :class:`FormModel` and returns either
        ``None`` (no errors) or a list of :class:`FieldError` instances.
        """
        self._cross_validators.append(rule)

    # ------------------------------------------------------------------
    # Aggregate state
    # ------------------------------------------------------------------

    @property
    def is_valid(self) -> bool:
        """True when all fields are valid and no cross errors exist."""
        return all(f.is_valid for f in self._fields.values()) and not self._cross_errors

    @property
    def is_dirty(self) -> bool:
        """True when any field has an uncommitted change."""
        return any(f.is_dirty for f in self._fields.values())

    @property
    def cross_errors(self) -> List[FieldError]:
        return list(self._cross_errors)

    # ------------------------------------------------------------------
    # Operations
    # ------------------------------------------------------------------

    def validate_all(self) -> bool:
        """Validate every field and run cross validators.  Returns True if valid."""
        field_ok = all(f.validate() for f in self._fields.values())
        cross: List[FieldError] = []
        for rule in self._cross_validators:
            try:
                result = rule(self)
            except Exception:
                result = None
            if result:
                cross.extend(result)
        self._cross_errors = cross
        return field_ok and not self._cross_errors

    def commit_all(self) -> None:
        """Commit all fields, resetting dirty state."""
        for f in self._fields.values():
            f.commit()

    def reset_all(self) -> None:
        """Reset all fields to their last committed values."""
        self._cross_errors = []
        for f in self._fields.values():
            f.reset()

    def get_values(self) -> dict[str, Any]:
        """Return a snapshot dict of {field_name: current_value}."""
        return {name: f.value.value for name, f in self._fields.items()}

    def get_errors(self) -> List[FieldError]:
        """Return all field errors plus cross-field errors."""
        errors: List[FieldError] = []
        for f in self._fields.values():
            for msg in f.errors:
                errors.append(FieldError(f.name, msg))
        errors.extend(self._cross_errors)
        return errors
