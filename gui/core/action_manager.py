from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Callable, List, Optional

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

    def has_action(self, action_name: str) -> bool:
        """Return True if *action_name* has a registered handler."""
        return str(action_name) in self._actions

    def registered_actions(self) -> List[str]:
        """Return a sorted list of all registered action names."""
        return sorted(self._actions.keys())

    def bind_key(self, key: int, action_name: str, *, scene: str | None = None, window_only: bool = False) -> None:
        binding = KeyBinding(int(key), scene=scene, window_only=bool(window_only))
        names = self._keymap[binding]
        if action_name not in names:
            names.append(action_name)

    def unbind_key(self, key: int, action_name: str, *, scene: str | None = None, window_only: bool = False) -> bool:
        """Remove one specific key→action binding. Returns True if a binding was removed."""
        binding = KeyBinding(int(key), scene=scene, window_only=bool(window_only))
        names = self._keymap.get(binding)
        if not names or action_name not in names:
            return False
        names.remove(action_name)
        if not names:
            del self._keymap[binding]
        return True

    def bindings_for_action(self, action_name: str) -> List[KeyBinding]:
        """Return all key bindings that route to *action_name*."""
        return [binding for binding, names in self._keymap.items() if action_name in names]

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

    def binding_count(self) -> int:
        """Return the total number of key-to-action bindings registered."""
        return sum(len(names) for names in self._keymap.values())

    def clear_bindings_for_action(self, action_name: str) -> int:
        """Remove all key bindings that route to *action_name*. Returns the count removed."""
        removed = 0
        for binding in list(self._keymap.keys()):
            names = self._keymap[binding]
            if action_name in names:
                names.remove(action_name)
                removed += 1
                if not names:
                    del self._keymap[binding]
        return removed
