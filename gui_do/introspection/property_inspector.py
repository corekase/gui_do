"""Property inspector — grouped editable view over PropertyRegistry metadata."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from .property_registry import PropertyDescriptor, property_registry


@dataclass(slots=True)
class InspectedProperty:
    descriptor: PropertyDescriptor
    value: Any


class PropertyInspectorModel:
    """Queryable/editable property view for one inspected object."""

    def __init__(self, target: object) -> None:
        self._target = target

    @property
    def target(self) -> object:
        return self._target

    def properties(self) -> List[InspectedProperty]:
        result: List[InspectedProperty] = []
        for descriptor in property_registry.descriptors_for(self._target):
            result.append(InspectedProperty(descriptor=descriptor, value=getattr(self._target, descriptor.name)))
        return result

    def grouped(self) -> Dict[str, List[InspectedProperty]]:
        result: Dict[str, List[InspectedProperty]] = {}
        for item in self.properties():
            result.setdefault(item.descriptor.group, []).append(item)
        return result

    def get_value(self, name: str) -> Any:
        return getattr(self._target, str(name))

    def set_value(self, name: str, value: Any) -> None:
        descriptor = self._descriptor_for(name)
        if descriptor.read_only:
            raise ValueError(f"Property is read-only: {name!r}")
        coerced = self._coerce_value(descriptor, value)
        setattr(self._target, descriptor.name, coerced)

    def _descriptor_for(self, name: str) -> PropertyDescriptor:
        target_name = str(name)
        for descriptor in property_registry.descriptors_for(self._target):
            if descriptor.name == target_name:
                return descriptor
        raise KeyError(f"Inspectable property not found: {name!r}")

    @staticmethod
    def _coerce_value(descriptor: PropertyDescriptor, value: Any) -> Any:
        coerced = value
        if descriptor.type == "int":
            coerced = int(value)
        elif descriptor.type == "float":
            coerced = float(value)
        elif descriptor.type == "bool":
            coerced = bool(value)
        elif descriptor.type == "str":
            coerced = str(value)
        if descriptor.min is not None and isinstance(coerced, (int, float)):
            coerced = max(coerced, descriptor.min)
        if descriptor.max is not None and isinstance(coerced, (int, float)):
            coerced = min(coerced, descriptor.max)
        return coerced
