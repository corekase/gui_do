from __future__ import annotations

from typing import Callable, Optional

import pygame

from .gui_event import EventType


class KeyboardManager:
    """Routes key events through focused window-first keyboard dispatch."""

    @classmethod
    def is_key_event(cls, event) -> bool:
        return event.kind in (EventType.KEY_DOWN, EventType.KEY_UP, EventType.TEXT_INPUT, EventType.TEXT_EDITING)

    def route_key_event(self, scene, event, app, screen_event_handler: Optional[Callable[[object], bool]] = None) -> bool:
        overlay = getattr(app, "overlay", None)
        has_overlay = getattr(overlay, "has_overlay", None)
        has_command_palette = callable(has_overlay) and has_overlay("__command_palette__")
        task_panel_focus = getattr(app, "task_panel_focus", None)

        if task_panel_focus is not None and task_panel_focus.is_active:
            # Keep task-panel mode keyboard-only, but allow scene-owned F1 toggles
            # so users can exit/enter the mode without a mouse.
            if event.is_key_down(pygame.K_F1):
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

        # Ctrl+Tab / Ctrl+Shift+Tab — window focus cycling.
        if event.is_key_down(pygame.K_TAB) and bool(event.mod & pygame.KMOD_CTRL):
            if has_command_palette:
                event.prevent_default()
                event.stop_propagation()
                return True
            shift_pressed = bool(event.mod & pygame.KMOD_SHIFT)
            window_focus = getattr(app, "window_focus", None)
            if window_focus is not None:
                window_focus.cycle(scene, forward=not shift_pressed, app=app)
            event.prevent_default()
            event.stop_propagation()
            return True

        if event.is_key_down(pygame.K_TAB):
            if has_command_palette:
                event.prevent_default()
                event.stop_propagation()
                return True
            shift_pressed = bool(event.mod & pygame.KMOD_SHIFT)
            focus_scope = scene.active_window()
            pointer_pos = tuple(map(int, pygame.mouse.get_pos()))
            if app.focus.cycle_focus(scene, forward=not shift_pressed, window=focus_scope, pointer_pos=pointer_pos):
                event.prevent_default()
                event.stop_propagation()
                return True
        if app.actions.trigger_from_event(event, app):
            event.prevent_default()
            event.stop_propagation()
            return True
        if event.default_prevented or event.propagation_stopped:
            return True
        if app.focus.route_key_event(event, app):
            event.prevent_default()
            event.stop_propagation()
            return True
        if event.default_prevented or event.propagation_stopped:
            return True
        active_window = scene.active_window()
        if active_window is not None:
            # Focused windows own keyboard input; do not bubble key events to screen while focused.
            active_window.handle_event(event, app)
            event.prevent_default()
            event.stop_propagation()
            return True
        if screen_event_handler is not None:
            consumed = bool(screen_event_handler(event))
            if consumed:
                event.prevent_default()
                event.stop_propagation()
            return consumed
        return False
