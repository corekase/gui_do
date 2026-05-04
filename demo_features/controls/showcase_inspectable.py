"""Inspectable sample object used by the controls showcase feature."""

from __future__ import annotations

from gui_do import ui_property


class ShowcaseInspectable:
    """Simple object with @ui_property decorators for the PropertyInspectorPanel showcase."""

    def __init__(self) -> None:
        self._label: str = "Showcase"
        self._value: float = 0.5
        self._active: bool = True
        self._priority: int = 1

    @property
    @ui_property(label="Label", type="str", group="Display")
    def label(self) -> str:
        return self._label

    @label.setter
    def label(self, v: str) -> None:
        self._label = str(v)

    @property
    @ui_property(label="Value", type="float", min=0.0, max=1.0, group="Display")
    def value(self) -> float:
        return self._value

    @value.setter
    def value(self, v: float) -> None:
        self._value = float(v)

    @property
    @ui_property(label="Active", type="bool", group="State")
    def active(self) -> bool:
        return self._active

    @active.setter
    def active(self, v: bool) -> None:
        self._active = bool(v)

    @property
    @ui_property(label="Priority", type="int", min=1, max=10, group="State")
    def priority(self) -> int:
        return self._priority

    @priority.setter
    def priority(self, v: int) -> None:
        self._priority = int(v)


__all__ = ["ShowcaseInspectable"]
