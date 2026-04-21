from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Callable, Optional

from .gui_event import EventType


ActionHandler = Callable[[object], bool]


@dataclass(frozen=True)
class KeyBinding:
    key: int
    scene: Optional[str] = None
    window_only: bool = False


class ActionManager:
    """Resolves key events into named actions across scoped keymaps."""

    def __init__(self) -> None:
        self._actions: dict[str, ActionHandler] = {}
        self._keymap: dict[KeyBinding, list[str]] = defaultdict(list)

    def register_action(self, action_name: str, handler: ActionHandler) -> None:
        self._actions[str(action_name)] = handler

    def unregister_action(self, action_name: str) -> None:
        self._actions.pop(str(action_name), None)

    def bind_key(self, key: int, action_name: str, *, scene: str | None = None, window_only: bool = False) -> None:
        binding = KeyBinding(int(key), scene=scene, window_only=bool(window_only))
        names = self._keymap[binding]
        if action_name not in names:
            names.append(action_name)

    def clear_bindings(self) -> None:
        self._keymap.clear()

    def trigger_from_event(self, event, app) -> bool:
        if event.kind is not EventType.KEY_DOWN or event.key is None:
            return False
        scene_name = getattr(app, "active_scene_name", None)
        has_window = bool(app.scene.active_window())

        candidates = [
            KeyBinding(int(event.key), scene=scene_name, window_only=has_window),
            KeyBinding(int(event.key), scene=scene_name, window_only=False),
            KeyBinding(int(event.key), scene=None, window_only=has_window),
            KeyBinding(int(event.key), scene=None, window_only=False),
        ]
        seen_bindings = set()
        for binding in candidates:
            if binding in seen_bindings:
                continue
            seen_bindings.add(binding)
            for action_name in self._keymap.get(binding, ()):
                handler = self._actions.get(action_name)
                if handler is not None and bool(handler(event)):
                    return True
        return False
