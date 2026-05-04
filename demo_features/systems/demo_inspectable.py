"""Inspectable sample object used by the systems demo feature."""

from __future__ import annotations

from gui_do import ui_property


class DemoInspectable:
    """Simple object decorated with ``@ui_property`` for PropertyInspectorPanel demo."""

    def __init__(self) -> None:
        self._opacity: float = 1.0
        self._speed: int = 50
        self._label: str = "demo"
        self._active: bool = True

    @property
    @ui_property(label="Opacity", type="float", min=0.0, max=1.0, group="Appearance")
    def opacity(self) -> float:
        return self._opacity

    @opacity.setter
    def opacity(self, v: float) -> None:
        self._opacity = float(v)

    @property
    @ui_property(label="Speed", type="int", min=0, max=200, group="Behaviour")
    def speed(self) -> int:
        return self._speed

    @speed.setter
    def speed(self, v: int) -> None:
        self._speed = int(v)

    @property
    @ui_property(label="Label", type="str", group="Content")
    def label(self) -> str:
        return self._label

    @label.setter
    def label(self, v: str) -> None:
        self._label = str(v)

    @property
    @ui_property(label="Active", type="bool", group="Behaviour")
    def active(self) -> bool:
        return self._active

    @active.setter
    def active(self, v: bool) -> None:
        self._active = bool(v)


__all__ = ["DemoInspectable"]
