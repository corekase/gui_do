from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Callable, Iterable, List, Optional

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
    mod: int = 0


@dataclass(frozen=True)
class PointerBinding:
    button: int
    scene: Optional[str] = None


class ActionManager:
    """Resolves key events into named actions across scoped keymaps."""

    def __init__(self) -> None:
        self._actions: dict[str, ActionHandler] = {}
        self._keymap: dict[KeyBinding, list[str]] = defaultdict(list)
        self._keymap_fast: dict[tuple[int, str | None, bool, int], list[str]] = {}
        self._bindings_by_action: dict[str, list[KeyBinding]] = defaultdict(list)
        self._global_keymap: dict[KeyBinding, list[str]] = defaultdict(list)
        self._global_keymap_fast: dict[tuple[int, str | None, bool, int], list[str]] = {}
        self._global_pointer_map: dict[PointerBinding, list[str]] = defaultdict(list)
        self._global_pointer_map_fast: dict[tuple[int, str | None], list[str]] = {}
        self._middlewares: List[ActionMiddleware] = []

    @staticmethod
    def _binding_key(binding: KeyBinding) -> tuple[int, str | None, bool, int]:
        return (int(binding.key), binding.scene, bool(binding.window_only), int(binding.mod))

    @staticmethod
    def _mod_matches(required: int, event_mod: int) -> bool:
        required = int(required)
        if required == 0:
            return True
        if (int(event_mod) & required) == required:
            return True
        try:
            live_mod = int(pygame.key.get_mods())
        except Exception:
            live_mod = 0
        return (live_mod & required) == required

    @staticmethod
    def _key_matches(bound_key: int, event_key: int) -> bool:
        """Return True when event key should satisfy a bound key.

        On some keyboard layouts the physical grave/backquote key can be
        reported as quote; treat them as equivalent for binding resolution.
        """
        bk = int(bound_key)
        ek = int(event_key)
        if bk == ek:
            return True
        quote_key = int(getattr(pygame, "K_QUOTE", -1))
        backquote_key = int(getattr(pygame, "K_BACKQUOTE", -1))
        if bk == backquote_key and ek == quote_key:
            return True
        if bk == quote_key and ek == backquote_key:
            return True
        return False

    @staticmethod
    def _pointer_binding_key(binding: PointerBinding) -> tuple[int, str | None]:
        return (int(binding.button), binding.scene)

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

    def bind_key(
        self,
        key: int,
        action_name: str,
        *,
        scene: str | None = None,
        window_only: bool = False,
        mod: int = 0,
    ) -> None:
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
        binding = KeyBinding(key, scene=scene, window_only=bool(window_only), mod=int(mod))
        names = self._keymap[binding]
        if action_name not in names:
            names.append(action_name)
            self._keymap_fast[self._binding_key(binding)] = names
            bindings = self._bindings_by_action[action_name]
            if binding not in bindings:
                bindings.append(binding)

    def unbind_key(
        self,
        key: int,
        action_name: str,
        *,
        scene: str | None = None,
        window_only: bool = False,
        mod: int = 0,
    ) -> bool:
        """Remove one specific key→action binding. Returns True if a binding was removed."""
        action_name = str(action_name)
        binding = KeyBinding(int(key), scene=scene, window_only=bool(window_only), mod=int(mod))
        names = self._keymap.get(binding)
        if not names or action_name not in names:
            return False
        names.remove(action_name)
        if not names:
            del self._keymap[binding]
            self._keymap_fast.pop(self._binding_key(binding), None)
        bindings = self._bindings_by_action.get(action_name)
        if bindings and binding in bindings:
            bindings.remove(binding)
            if not bindings:
                del self._bindings_by_action[action_name]
        return True

    def bind_global_key(self, key: int, action_name: str, *, scene: str | None = None, mod: int = 0) -> None:
        """Bind a global key tested first in routing — before focus, windows, and all other handlers.

        Global keys fire regardless of focused widget or active-window state.
        Use this for per-scene commands like the command palette activation key that
        must be reachable even when a window is receiving keyboard input.

        *scene* scopes the binding to a specific scene name; ``None`` applies to every scene.
        Tab and other reserved accessibility keys cannot be registered as global keys.
        """
        key = int(key)
        action_name = str(action_name)
        if key in _RESERVED_ACCESSIBILITY_KEYS:
            raise logical_error(
                f"Key {pygame.key.name(key)!r} is reserved for accessibility focus traversal "
                f"and cannot be bound as a global key.",
                subsystem="gui_do.actions",
                operation="ActionManager.bind_global_key",
                source_skip_frames=1,
            )
        binding = KeyBinding(key, scene=scene, window_only=False, mod=int(mod))
        names = self._global_keymap[binding]
        if action_name not in names:
            names.append(action_name)
            self._global_keymap_fast[self._binding_key(binding)] = names

    def unbind_global_key(self, key: int, action_name: str, *, scene: str | None = None, mod: int = 0) -> bool:
        """Remove a global key binding.  Returns ``True`` if it existed."""
        binding = KeyBinding(int(key), scene=scene, window_only=False, mod=int(mod))
        names = self._global_keymap.get(binding)
        if not names or str(action_name) not in names:
            return False
        names.remove(str(action_name))
        if not names:
            del self._global_keymap[binding]
            self._global_keymap_fast.pop(self._binding_key(binding), None)
        return True

    def bind_global_pointer_button(self, button: int, action_name: str, *, scene: str | None = None) -> None:
        """Bind a mouse button tested first in routing for pointer button-down events."""
        binding = PointerBinding(int(button), scene=scene)
        names = self._global_pointer_map[binding]
        normalized = str(action_name)
        if normalized not in names:
            names.append(normalized)
            self._global_pointer_map_fast[self._pointer_binding_key(binding)] = names

    def unbind_global_pointer_button(self, button: int, action_name: str, *, scene: str | None = None) -> bool:
        """Remove a global pointer-button binding. Returns ``True`` if removed."""
        binding = PointerBinding(int(button), scene=scene)
        names = self._global_pointer_map.get(binding)
        normalized = str(action_name)
        if not names or normalized not in names:
            return False
        names.remove(normalized)
        if not names:
            del self._global_pointer_map[binding]
            self._global_pointer_map_fast.pop(self._pointer_binding_key(binding), None)
        return True

    def trigger_global_key_from_event(self, event, app) -> bool:
        """Fire the first matching global-key action for *event*, if any.

        Called at the very start of key routing — before focus, active-window, and
        screen-event handlers — so that per-scene commands like the command palette
        are always reachable regardless of UI state.
        """
        if event.kind is not EventType.KEY_DOWN or event.key is None:
            return False
        scene_name = app.active_scene_name
        key = int(event.key)
        event_mod = int(getattr(event, "mod", 0) or 0)
        if event_mod == 0:
            try:
                event_mod = int(pygame.key.get_mods())
            except Exception:
                event_mod = 0

        def _run_for_scope(scope_scene: str | None) -> bool:
            for binding, action_names in self._global_keymap.items():
                if not self._key_matches(int(binding.key), key):
                    continue
                if binding.scene != scope_scene:
                    continue
                required = int(getattr(binding, "mod", 0) or 0)
                if not self._mod_matches(required, event_mod):
                    continue
                for action_name in action_names:
                    handler = self._actions.get(action_name)
                    if handler is not None and self._dispatch(action_name, handler, event):
                        return True
            return False

        if _run_for_scope(scene_name):
            return True
        if _run_for_scope(None):
            return True
        return False

    def trigger_global_pointer_from_event(self, event, app) -> bool:
        """Fire the first matching global pointer action for *event*, if any."""
        if event.kind is not EventType.MOUSE_BUTTON_DOWN or event.button is None:
            return False
        scene_name = app.active_scene_name
        button = int(event.button)
        fast = self._global_pointer_map_fast
        for action_name in fast.get((button, scene_name), ()):
            handler = self._actions.get(action_name)
            if handler is not None and self._dispatch(action_name, handler, event):
                return True
        for action_name in fast.get((button, None), ()):
            handler = self._actions.get(action_name)
            if handler is not None and self._dispatch(action_name, handler, event):
                return True
        return False

    def bindings_for_action(self, action_name: str) -> List[KeyBinding]:
        """Return all key bindings that route to *action_name*."""
        return list(self._bindings_by_action.get(str(action_name), ()))

    def replace_bindings_for_action(
        self,
        action_name: str,
        bindings: "Iterable[KeyBinding]",
    ) -> int:
        """Replace all key bindings for *action_name* with *bindings*.

        Returns the number of bindings added.
        """
        normalized = str(action_name)
        # Clear old bindings in one pass through the previous binding list.
        for binding in self._bindings_by_action.pop(normalized, ()):
            names = self._keymap.get(binding)
            if not names:
                continue
            try:
                names.remove(normalized)
            except ValueError:
                continue
            if not names:
                del self._keymap[binding]
                self._keymap_fast.pop(self._binding_key(binding), None)

        added = 0
        new_bindings: list[KeyBinding] = []
        seen: set[KeyBinding] = set()
        for binding in bindings:
            if binding in seen:
                continue
            seen.add(binding)
            if int(binding.key) in _RESERVED_ACCESSIBILITY_KEYS:
                raise logical_error(
                    f"Key {pygame.key.name(int(binding.key))!r} is reserved for accessibility focus traversal "
                    f"(Tab/Shift+Tab, Ctrl+Tab/Ctrl+Shift+Tab) and cannot be bound to user actions.",
                    subsystem="gui_do.actions",
                    operation="ActionManager.replace_bindings_for_action",
                    source_skip_frames=1,
                )
            new_bindings.append(binding)
            names = self._keymap[binding]
            if normalized not in names:
                names.append(normalized)
                self._keymap_fast[self._binding_key(binding)] = names
            added += 1

        if new_bindings:
            self._bindings_by_action[normalized] = new_bindings
        return added

    def clear_bindings(self) -> None:
        self._keymap.clear()
        self._keymap_fast.clear()
        self._bindings_by_action.clear()

    def trigger_from_event(self, event, app) -> bool:
        if event.kind is not EventType.KEY_DOWN or event.key is None:
            return False
        scene_name = app.active_scene_name
        has_window = bool(app.scene.active_window())
        key = int(event.key)
        event_mod = int(getattr(event, "mod", 0) or 0)
        if event_mod == 0:
            try:
                event_mod = int(pygame.key.get_mods())
            except Exception:
                event_mod = 0

        if has_window:
            candidate_scopes = (
                (scene_name, True),
                (scene_name, False),
                (None, True),
                (None, False),
            )
        else:
            candidate_scopes = (
                (scene_name, False),
                (None, False),
            )

        for scope_scene, scope_window_only in candidate_scopes:
            for binding, action_names in self._keymap.items():
                if not self._key_matches(int(binding.key), key):
                    continue
                if binding.scene != scope_scene:
                    continue
                if bool(binding.window_only) != bool(scope_window_only):
                    continue
                required = int(getattr(binding, "mod", 0) or 0)
                if not self._mod_matches(required, event_mod):
                    continue
                for action_name in action_names:
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
                self._keymap_fast.pop(self._binding_key(binding), None)
        if action_name in self._bindings_by_action:
            del self._bindings_by_action[action_name]
        return removed
