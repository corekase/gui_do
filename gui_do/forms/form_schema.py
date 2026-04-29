"""Form schema — declarative field definitions that build FormModel instances."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Sequence

from .form_model import FieldError, FormModel, ValidationRule


@dataclass(slots=True)
class SchemaField:
    name: str
    default: Any
    label: str = ""
    required: bool = False
    validators: Sequence[ValidationRule] = field(default_factory=tuple)


class FormSchema:
    """Declarative schema for reusable, validated forms."""

    def __init__(self, fields: Sequence[SchemaField]) -> None:
        normalized = list(fields)
        names = [field.name for field in normalized]
        if len(names) != len(set(names)):
            raise ValueError("FormSchema field names must be unique")
        self._fields = normalized

    @property
    def fields(self) -> List[SchemaField]:
        return list(self._fields)

    def build_form(self) -> FormModel:
        form = FormModel()
        for schema_field in self._fields:
            form.add_field(
                schema_field.name,
                schema_field.default,
                validators=schema_field.validators,
                required=schema_field.required,
            )
        return form

    def validate_values(self, values: dict[str, Any]) -> List[FieldError]:
        form = self.build_form()
        for field_name, value in dict(values).items():
            if field_name in form.fields:
                form.field(field_name).value.value = value
        for frm_field in form.fields.values():
            frm_field.validate()
        return form.get_errors()

    def defaults(self) -> dict[str, Any]:
        return {field.name: field.default for field in self._fields}

    # ------------------------------------------------------------------
    # FormModel helpers
    # ------------------------------------------------------------------

    def apply_to(self, form: FormModel, values: dict[str, Any]) -> None:
        """Write *values* into an existing *form* without rebuilding it.

        Only keys declared in this schema and present in *form* are applied.
        Missing keys in *values* are silently skipped.
        """
        for schema_field in self._fields:
            if schema_field.name not in values:
                continue
            if schema_field.name not in form.fields:
                continue
            form.field(schema_field.name).value.value = values[schema_field.name]

    def extract_from(self, form: FormModel) -> dict[str, Any]:
        """Read the current values of all schema fields from *form*.

        Fields declared in the schema but absent from *form* are omitted.
        """
        result: dict[str, Any] = {}
        for schema_field in self._fields:
            if schema_field.name in form.fields:
                result[schema_field.name] = form.field(schema_field.name).value.value
        return result
