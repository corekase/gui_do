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
            and event.key in (pygame.K_TAB, pygame.K_UP, pygame.K_DOWN)
        )

    def route_key_event(self, scene, event, app, screen_event_handler: Optional[Callable[[object], bool]] = None) -> bool:
        overlay = getattr(app, "overlay", None)
        has_overlay = getattr(overlay, "has_overlay", None)
        has_command_palette = callable(has_overlay) and has_overlay("__command_palette__")
        task_panel_focus = getattr(app, "task_panel_focus", None)

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

        if self._is_accessibility_key_event(event):
            if has_command_palette:
                event.prevent_default()
                event.stop_propagation()
                return True

            if event.key in (pygame.K_UP, pygame.K_DOWN):
                focused_node = getattr(app.focus, "focused_node", None)
                if focused_node is not None:
                    # Let the focused control react first, then consume so this
                    # accessibility key cannot fall through to scene-level handlers.
                    app.focus.route_key_event(event, app)
                    event.prevent_default()
                    event.stop_propagation()
                    return True

            # Accessibility keys are reserved for focus traversal behavior and
            # must not bubble to actions/window/screen handlers.
            if bool(event.mod & pygame.KMOD_CTRL):
                shift_pressed = bool(event.mod & pygame.KMOD_SHIFT)
                window_focus = getattr(app, "window_focus", None)
                if window_focus is not None:
                    window_focus.cycle(scene, forward=not shift_pressed, app=app)
            else:
                shift_pressed = bool(event.mod & pygame.KMOD_SHIFT)
                focus_scope = scene.active_window()
                try:
                    pointer_pos = tuple(map(int, pygame.mouse.get_pos()))
                except pygame.error:
                    pointer_pos = (0, 0)
                app.focus.cycle_focus(scene, forward=not shift_pressed, window=focus_scope, pointer_pos=pointer_pos)
            event.prevent_default()
            event.stop_propagation()
            return True

        if app.focus.route_key_event(event, app):
            event.prevent_default()
            event.stop_propagation()
            return True
        if event.default_prevented or event.propagation_stopped:
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
