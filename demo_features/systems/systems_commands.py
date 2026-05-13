"""Command-history command objects for systems feature workflows."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .systems_feature import SystemsFeature


class _StatusChangeCommand:
    def __init__(self, feature: SystemsFeature, new_index: int, description: str) -> None:
        self._feature = feature
        self._new_index = int(new_index)
        self._old_index = int(feature._history_stage_index)
        self._description = str(description)

    @property
    def description(self) -> str:
        return self._description

    def execute(self) -> None:
        self._feature._history_stage_index = self._new_index
        self._feature._refresh_history_labels()

    def undo(self) -> None:
        self._feature._history_stage_index = self._old_index
        self._feature._refresh_history_labels()


class _SetIndexCommand:
    def __init__(self, feature: SystemsFeature, attr_name: str, new_index: int, description: str) -> None:
        self._feature = feature
        self._attr_name = str(attr_name)
        self._new_index = int(new_index)
        self._old_index = int(getattr(feature, attr_name))
        self._description = str(description)

    @property
    def description(self) -> str:
        return self._description

    def execute(self) -> None:
        setattr(self._feature, self._attr_name, self._new_index)
        self._feature._refresh_state_labels()

    def undo(self) -> None:
        setattr(self._feature, self._attr_name, self._old_index)
        self._feature._refresh_state_labels()


__all__ = [
    "_SetIndexCommand",
    "_StatusChangeCommand",
]
