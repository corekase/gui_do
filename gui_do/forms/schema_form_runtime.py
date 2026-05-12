"""SchemaFormRuntime — schema-driven form with dependency graph and validation policies.

Adds richer semantics on top of ``FormModel``:

* :class:`FieldSchema` — per-field declaration with ``depends_on`` and
  ``visible_when`` expressions
* :class:`FieldGraphSchema` — ordered field list with dependency resolution
* :class:`ValidationPolicy` — when validation runs (on-change / on-blur / on-submit)
* :class:`SchemaFormRuntime` — creates fields, wires dependencies, evaluates
  visibility, and runs the selected validation policy
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Sequence, Set

__all__ = [
    "FieldSchema",
    "FieldGraphSchema",
    "ValidationPolicy",
    "SchemaFormRuntime",
]


# ---------------------------------------------------------------------------
# ValidationPolicy
# ---------------------------------------------------------------------------


class ValidationPolicy(Enum):
    """Controls *when* field validation is triggered."""

    ON_CHANGE = auto()  # validate immediately on every value change
    ON_BLUR = auto()    # validate when the field loses focus
    ON_SUBMIT = auto()  # validate only when the form is submitted


# ---------------------------------------------------------------------------
# FieldSchema
# ---------------------------------------------------------------------------

ValidatorFn = Callable[[Any], Optional[str]]
"""``(value) -> error_message_or_None``"""


@dataclass
class FieldSchema:
    """Declarative specification for a single form field.

    Parameters
    ----------
    name:
        Unique field identifier.
    field_type:
        Python type (``str``, ``int``, ``bool``, …).  Used for coercion hints.
    default:
        Initial value.
    label:
        Human-readable display label.
    required:
        Whether a non-empty value is required.
    validators:
        Sequence of ``(value) -> error_message_or_None`` callables.
    depends_on:
        List of field names whose values feed into the ``visible_when``
        expression and can affect this field's derived value.
    visible_when:
        Callable ``(values: dict) -> bool`` evaluated against the current
        form values dict.  ``None`` means always visible.
    """

    name: str
    field_type: type = str
    default: Any = ""
    label: str = ""
    required: bool = False
    validators: List[ValidatorFn] = field(default_factory=list)
    depends_on: List[str] = field(default_factory=list)
    visible_when: Optional[Callable[[Dict[str, Any]], bool]] = None


# ---------------------------------------------------------------------------
# FieldGraphSchema
# ---------------------------------------------------------------------------


class FieldGraphSchema:
    """Ordered collection of :class:`FieldSchema` objects with dependency awareness.

    Validates uniqueness of field names and exposes topological ordering.
    """

    def __init__(self, fields: Sequence[FieldSchema]) -> None:
        names = [f.name for f in fields]
        if len(names) != len(set(names)):
            raise ValueError("FieldGraphSchema: field names must be unique")
        # Validate dependency references
        name_set = set(names)
        for fs in fields:
            for dep in fs.depends_on:
                if dep not in name_set:
                    raise ValueError(
                        f"Field {fs.name!r} depends on unknown field {dep!r}"
                    )
        self._fields: List[FieldSchema] = list(fields)

    @property
    def fields(self) -> List[FieldSchema]:
        return list(self._fields)

    def __len__(self) -> int:
        return len(self._fields)


# ---------------------------------------------------------------------------
# SchemaFormRuntime
# ---------------------------------------------------------------------------


class FieldState:
    """Mutable runtime state for a single field."""

    __slots__ = ("schema", "value", "errors", "visible", "dirty")

    def __init__(self, schema: FieldSchema) -> None:
        self.schema = schema
        self.value: Any = schema.default
        self.errors: List[str] = []
        self.visible: bool = True
        self.dirty: bool = False


class SchemaFormRuntime:
    """Manages field state, validation, and dependency evaluation for a
    :class:`FieldGraphSchema`.

    Parameters
    ----------
    schema:
        The field graph describing the form.
    policy:
        Determines when validation runs.  Defaults to ``ON_CHANGE``.
    """

    def __init__(
        self,
        schema: FieldGraphSchema,
        policy: ValidationPolicy = ValidationPolicy.ON_CHANGE,
    ) -> None:
        self._schema = schema
        self._policy = policy
        self._fields: Dict[str, FieldState] = {
            fs.name: FieldState(fs) for fs in schema.fields
        }
        self._dependents: Dict[str, Set[str]] = {}
        for fs in schema.fields:
            self._dependents.setdefault(fs.name, set())
            for dep in fs.depends_on:
                self._dependents.setdefault(dep, set()).add(fs.name)
        self._change_callbacks: List[Callable[[str, Any], None]] = []
        # Evaluate initial visibility
        self._update_visibility()

    # ------------------------------------------------------------------
    # Field access
    # ------------------------------------------------------------------

    def field_names(self) -> List[str]:
        return [fs.name for fs in self._schema.fields]

    def get_value(self, name: str) -> Any:
        return self._fields[name].value

    def get_errors(self, name: str) -> List[str]:
        return list(self._fields[name].errors)

    def is_visible(self, name: str) -> bool:
        return self._fields[name].visible

    # ------------------------------------------------------------------
    # Value mutation
    # ------------------------------------------------------------------

    def set_value(self, name: str, value: Any) -> None:
        """Update *name* to *value*, then update visibility and maybe validate."""
        state = self._fields[name]
        state.value = value
        state.dirty = True
        self._update_visibility(changed_name=name)
        for cb in list(self._change_callbacks):
            cb(name, value)
        if self._policy == ValidationPolicy.ON_CHANGE:
            self._validate_field(name)

    def blur(self, name: str) -> None:
        """Notify that *name* lost focus — triggers validation if ON_BLUR."""
        if self._policy == ValidationPolicy.ON_BLUR:
            self._validate_field(name)

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate_all(self) -> bool:
        """Run validation on all fields.  Returns ``True`` if the form is valid."""
        for name in self._fields:
            self._validate_field(name)
        return self.is_valid()

    def is_valid(self) -> bool:
        """``True`` if all visible fields have no errors."""
        for name, state in self._fields.items():
            if state.visible and state.errors:
                return False
        return True

    def _validate_field(self, name: str) -> None:
        state = self._fields[name]
        errors: List[str] = []
        value = state.value
        schema = state.schema
        # Required check
        if schema.required and (value is None or value == "" or value == []):
            errors.append(f"{schema.label or name} is required")
        # Custom validators
        for validator in schema.validators:
            msg = validator(value)
            if msg is not None:
                errors.append(msg)
        state.errors = errors

    # ------------------------------------------------------------------
    # Visibility
    # ------------------------------------------------------------------

    def _dependent_closure(self, start: str) -> Set[str]:
        """Return fields affected by a change to *start* (including *start*)."""
        seen: Set[str] = set()
        stack: List[str] = [start]
        while stack:
            field_name = stack.pop()
            if field_name in seen:
                continue
            seen.add(field_name)
            stack.extend(self._dependents.get(field_name, ()))
        return seen

    def _update_visibility(self, changed_name: Optional[str] = None) -> None:
        values = {n: s.value for n, s in self._fields.items()}
        affected: Optional[Set[str]] = None
        if changed_name is not None:
            affected = self._dependent_closure(changed_name)
        for name, state in self._fields.items():
            if affected is not None and name not in affected:
                continue
            if state.schema.visible_when is not None:
                state.visible = state.schema.visible_when(values)
            else:
                state.visible = True

    # ------------------------------------------------------------------
    # Observers
    # ------------------------------------------------------------------

    def on_change(
        self, callback: Callable[[str, Any], None]
    ) -> Callable[[], None]:
        """Subscribe to any field value change.

        Returns an unsubscribe callable.
        """
        self._change_callbacks.append(callback)

        def _unsub() -> None:
            try:
                self._change_callbacks.remove(callback)
            except ValueError:
                pass

        return _unsub

    # ------------------------------------------------------------------
    # Snapshot / restore
    # ------------------------------------------------------------------

    def values_snapshot(self) -> Dict[str, Any]:
        """Return a copy of all current field values."""
        return {n: s.value for n, s in self._fields.items()}

    def restore_values(self, values: Dict[str, Any]) -> None:
        """Set multiple field values at once (bypasses on-change policy)."""
        for name, value in values.items():
            if name in self._fields:
                self._fields[name].value = value
        self._update_visibility()
