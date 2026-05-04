"""Small undoable command used by the systems demo feature."""

from __future__ import annotations


class SetIntCommand:
    """Small demo command used by the New Arch tab undo context demo."""

    def __init__(self, target: dict[str, int], key: str, new_value: int, description: str) -> None:
        self._target = target
        self._key = key
        self._new_value = int(new_value)
        self._old_value = int(target.get(key, 0))
        self._description = str(description)

    @property
    def description(self) -> str:
        return self._description

    def execute(self) -> None:
        self._target[self._key] = self._new_value

    def undo(self) -> None:
        self._target[self._key] = self._old_value


__all__ = ["SetIntCommand"]
