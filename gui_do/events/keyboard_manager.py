from __future__ import annotations

from typing import Callable, Optional

import pygame

from .gui_event import EventType


class KeyboardManager:
    """Routes key events through focused window-first keyboard dispatch."""

    @classmethod
    def is_key_event(cls, event) -> bool:
        return event.kind in (EventType.KEY_DOWN, EventType.KEY_UP, EventType.TEXT_INPUT, EventType.TEXT_EDITING)

    @staticmethod
    def _is_accessibility_key_event(event) -> bool:
        # Accessibility navigation keys handled at focused-control scope.
        return bool(
            event.kind == EventType.KEY_DOWN
            and event.key in (pygame.K_TAB,)
        )

    @staticmethod
    def _is_arrow_key_event(event) -> bool:
        return bool(
            event.kind == EventType.KEY_DOWN
            and event.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN)
        )

    def route_key_event(self, scene, event, app, screen_event_handler: Optional[Callable[[object], bool]] = None) -> bool:
        def _end_drag_if_any() -> bool:
            ended = False
            for node in getattr(scene, "nodes", ()):
                end_drag = getattr(node, "end_window_drag", None)
                if callable(end_drag):
                    ended = bool(end_drag(app)) or ended
            return ended

        overlay = getattr(app, "overlay", None)
        has_overlay = getattr(overlay, "has_overlay", None)
        has_command_palette = callable(has_overlay) and has_overlay("__command_palette__")
        # End window drag if command palette is open
        if has_command_palette:
            _end_drag_if_any()
        task_panel_focus = getattr(app, "task_panel_focus", None)

        # Global keys are tested first — before task-panel focus, accessibility keys,
        # focused widget, and active window.  They are per-scene and user-definable.
        # Typical use: command palette activation key registered via SceneCommandPaletteSpec.
        _trigger_global = getattr(app.actions, "trigger_global_key_from_event", None)
        if _trigger_global is not None and _trigger_global(event, app):
            event.prevent_default()
            event.stop_propagation()
            return True

        if task_panel_focus is not None and task_panel_focus.is_active:
            # While task-panel focus is active, let user-declared actions (e.g. the
            # toggle key) fire first so any configured key exits the mode — not just
            # the hardcoded F1. Tab still cycles within the panel.
            if app.actions.trigger_from_event(event, app):
                event.prevent_default()
                event.stop_propagation()
                return True
            if event.is_key_down(pygame.K_TAB):
                shift_pressed = bool(event.mod & pygame.KMOD_SHIFT)
                if task_panel_focus.cycle(scene, app, forward=not shift_pressed):
                    event.prevent_default()
                    event.stop_propagation()
                    return True
            if app.focus.route_key_event(event, app):
                event.prevent_default()
                event.stop_propagation()
                return True
            event.prevent_default()
            event.stop_propagation()
            return True

        if self._is_arrow_key_event(event):
            # Arrow keys are always scoped to the currently focused control.
            # Whether handled or not, they must not fall through to active-window,
            # screen, scene, or action handlers.
            app.focus.route_key_event(event, app)
            event.prevent_default()
            event.stop_propagation()
            return True

        if self._is_accessibility_key_event(event):
            # End window drag if window cycle (Ctrl+Tab or Ctrl+Shift+Tab)
            if bool(event.mod & pygame.KMOD_CTRL) and event.key == pygame.K_TAB:
                _end_drag_if_any()
            if has_command_palette:
                event.prevent_default()
                event.stop_propagation()
                return True

            # Accessibility keys are reserved for focus traversal behavior and
            # must not bubble to actions/window/screen handlers.
            cached_walk_nodes_getter = getattr(scene, "_get_cached_bfs_walk", None)
            cached_walk_nodes = cached_walk_nodes_getter() if callable(cached_walk_nodes_getter) else None
            if bool(event.mod & pygame.KMOD_CTRL):
                shift_pressed = bool(event.mod & pygame.KMOD_SHIFT)
                window_focus = getattr(app, "window_focus", None)
                if window_focus is not None:
                    try:
                        window_focus.cycle(
                            scene,
                            forward=not shift_pressed,
                            app=app,
                            cached_walk_nodes=cached_walk_nodes,
                        )
                    except TypeError:
                        window_focus.cycle(scene, forward=not shift_pressed, app=app)
            else:
                shift_pressed = bool(event.mod & pygame.KMOD_SHIFT)
                focus_scope = scene.active_window()
                pointer_pos = getattr(app, "logical_pointer_pos", (0, 0))
                try:
                    app.focus.cycle_focus(
                        scene,
                        forward=not shift_pressed,
                        window=focus_scope,
                        pointer_pos=pointer_pos,
                        cached_walk_nodes=cached_walk_nodes,
                    )
                except TypeError:
                    app.focus.cycle_focus(
                        scene,
                        forward=not shift_pressed,
                        window=focus_scope,
                        pointer_pos=pointer_pos,
                    )
            event.prevent_default()
            event.stop_propagation()
            return True

        if app.focus.route_key_event(event, app):
            event.prevent_default()
            event.stop_propagation()
            return True
        if event.default_prevented or event.propagation_stopped:
            return True

        # When the command palette is open, unhandled keys must not leak to
        # active-window handlers. Global keys have already been processed above.
        if has_command_palette:
            event.prevent_default()
            event.stop_propagation()
            return True

        active_window = scene.active_window()
        if active_window is not None:
            # Non-accessibility keys route to active window before any screen lifecycle handling.
            active_window.handle_event(event, app)
            event.prevent_default()
            event.stop_propagation()
            return True

        if screen_event_handler is not None:
            consumed = bool(screen_event_handler(event))
            if consumed:
                event.prevent_default()
                event.stop_propagation()
                return True
            if event.default_prevented or event.propagation_stopped:
                return True

        if app.actions.trigger_from_event(event, app):
            event.prevent_default()
            event.stop_propagation()
            return True
        if event.default_prevented or event.propagation_stopped:
            return True

        return False
