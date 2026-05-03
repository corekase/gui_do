from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Callable, List, Optional

import pygame

from ..app.error_handling import logical_error
from ..events.gui_event import EventType
from .action_middleware import ActionContext, ActionMiddleware, build_middleware_chain


ActionHandler = Callable[[object], bool]

# Keys permanently reserved for accessibility focus traversal.
# Tab drives Tab/Shift+Tab (control focus) and Ctrl+Tab/Ctrl+Shift+Tab (window focus).
# These routes are handled unconditionally by KeyboardManager before any user actions.
_RESERVED_ACCESSIBILITY_KEYS: frozenset[int] = frozenset((
    pygame.K_TAB,
))


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
        self._bindings_by_action: dict[str, list[KeyBinding]] = defaultdict(list)
        self._middlewares: List[ActionMiddleware] = []

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
        key = int(key)
        action_name = str(action_name)
        if key in _RESERVED_ACCESSIBILITY_KEYS:
            raise logical_error(
                f"Key {pygame.key.name(key)!r} is reserved for accessibility focus traversal "
                f"(Tab/Shift+Tab, Ctrl+Tab/Ctrl+Shift+Tab) and cannot be bound to user actions.",
                subsystem="gui_do.actions",
                operation="ActionManager.bind_key",
                source_skip_frames=1,
            )
        binding = KeyBinding(key, scene=scene, window_only=bool(window_only))
        names = self._keymap[binding]
        if action_name not in names:
            names.append(action_name)
            bindings = self._bindings_by_action[action_name]
            if binding not in bindings:
                bindings.append(binding)

    def unbind_key(self, key: int, action_name: str, *, scene: str | None = None, window_only: bool = False) -> bool:
        """Remove one specific key→action binding. Returns True if a binding was removed."""
        action_name = str(action_name)
        binding = KeyBinding(int(key), scene=scene, window_only=bool(window_only))
        names = self._keymap.get(binding)
        if not names or action_name not in names:
            return False
        names.remove(action_name)
        if not names:
            del self._keymap[binding]
        bindings = self._bindings_by_action.get(action_name)
        if bindings and binding in bindings:
            bindings.remove(binding)
            if not bindings:
                del self._bindings_by_action[action_name]
        return True

    def bindings_for_action(self, action_name: str) -> List[KeyBinding]:
        """Return all key bindings that route to *action_name*."""
        return list(self._bindings_by_action.get(str(action_name), ()))

    def clear_bindings(self) -> None:
        self._keymap.clear()
        self._bindings_by_action.clear()

    def trigger_from_event(self, event, app) -> bool:
        if event.kind is not EventType.KEY_DOWN or event.key is None:
            return False
        scene_name = app.active_scene_name
        has_window = bool(app.scene.active_window())
        key = int(event.key)

        if has_window:
            candidates = (
                KeyBinding(key, scene=scene_name, window_only=True),
                KeyBinding(key, scene=scene_name, window_only=False),
                KeyBinding(key, scene=None, window_only=True),
                KeyBinding(key, scene=None, window_only=False),
            )
        else:
            candidates = (
                KeyBinding(key, scene=scene_name, window_only=False),
                KeyBinding(key, scene=None, window_only=False),
            )

        for binding in candidates:
            for action_name in self._keymap.get(binding, ()):
                handler = self._actions.get(action_name)
                if handler is not None and self._dispatch(action_name, handler, event):
                    return True
        return False

    def _dispatch(self, action_name: str, handler: ActionHandler, event) -> bool:
        """Run *handler* through the middleware pipeline and return consumed flag."""
        if not self._middlewares:
            return bool(handler(event))
        ctx = ActionContext(action_name=action_name, event=event)

        def _terminal(c: ActionContext) -> bool:
            return bool(handler(c.event))

        chain = build_middleware_chain(self._middlewares, _terminal)
        return bool(chain(ctx))

    # ------------------------------------------------------------------
    # Middleware management
    # ------------------------------------------------------------------

    def add_middleware(self, middleware: ActionMiddleware) -> None:
        """Append *middleware* to the pipeline.

        Middlewares are called in LIFO order: the most recently added
        middleware runs first on every dispatch.
        """
        self._middlewares.append(middleware)

    def remove_middleware(self, middleware: ActionMiddleware) -> bool:
        """Remove a previously registered *middleware*.

        Returns ``True`` if found and removed, ``False`` if not registered.
        """
        try:
            self._middlewares.remove(middleware)
            return True
        except ValueError:
            return False

    def clear_middlewares(self) -> None:
        """Remove all registered middlewares."""
        self._middlewares.clear()

    def middleware_count(self) -> int:
        """Return the number of registered middlewares."""
        return len(self._middlewares)

    def binding_count(self) -> int:
        """Return the total number of key-to-action bindings registered."""
        return sum(len(names) for names in self._keymap.values())

    def clear_bindings_for_action(self, action_name: str) -> int:
        """Remove all key bindings that route to *action_name*. Returns the count removed."""
        action_name = str(action_name)
        bindings = list(self._bindings_by_action.get(action_name, ()))
        removed = 0
        for binding in bindings:
            names = self._keymap.get(binding)
            if not names or action_name not in names:
                continue
            names.remove(action_name)
            removed += 1
            if not names:
                del self._keymap[binding]
        if action_name in self._bindings_by_action:
            del self._bindings_by_action[action_name]
        return removed

    def register_and_bind(self, action_name: str, key: int, handler: ActionHandler, *, scene: str | None = None, window_only: bool = False) -> None:
        """Register an action handler and bind a key to it in one call.

        Equivalent to calling ``register_action(action_name, handler)`` followed by
        ``bind_key(key, action_name, scene=scene, window_only=window_only)``.
        """
        self.register_action(action_name, handler)
        self.bind_key(key, action_name, scene=scene, window_only=window_only)
