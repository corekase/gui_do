import unittest
from unittest.mock import patch

import pygame

from demo_features.main.main_feature import MainFeature
from demo_features.showcase.showcase_feature import ShowcaseFeature
from gui_do.events.gui_event import EventType
from gui_do.events.keyboard_manager import KeyboardManager


class _StubKeyEvent:
    def __init__(self, *, key: int, mod: int = 0):
        self.kind = EventType.KEY_DOWN
        self.key = int(key)
        self.mod = int(mod)
        self.default_prevented = False
        self.propagation_stopped = False

    def is_key_down(self, key: int) -> bool:
        return self.kind == EventType.KEY_DOWN and self.key == int(key)

    def prevent_default(self):
        self.default_prevented = True

    def stop_propagation(self):
        self.propagation_stopped = True


class _StubActions:
    def __init__(self):
        self._handlers = {}
        self._bound = {}
        self.trigger_calls = []
        self.register_calls = []
        self.bind_calls = []
        self.bind_global_calls = []

    def register_action(self, action_id: str, handler):
        self.register_calls.append((str(action_id), handler))
        self._handlers[str(action_id)] = handler

    def bind_key(self, key: int, action_id: str, *, scene=None):
        self.bind_calls.append((int(key), str(action_id), scene))
        self._bound[(scene, int(key))] = str(action_id)

    def bind_global_key(self, key: int, action_id: str, *, scene=None):
        self.bind_global_calls.append((int(key), str(action_id), scene))

    def trigger_from_event(self, event, app) -> bool:
        self.trigger_calls.append((event.key, app.active_scene_name))
        action_id = self._bound.get((app.active_scene_name, int(event.key)))
        if action_id is None:
            return False
        handler = self._handlers.get(action_id)
        return bool(handler is not None and handler(event))


class _StubTaskPanelFocus:
    def __init__(self, *, is_active: bool):
        self.is_active = bool(is_active)
        self.toggle_calls = []
        self.cycle_calls = []

    def toggle(self, scene, app):
        self.toggle_calls.append((scene, app))
        self.is_active = not self.is_active
        return True

    def cycle(self, scene, app, *, forward: bool):
        self.cycle_calls.append((scene, app, bool(forward)))
        return True


class _StubFocus:
    def __init__(self):
        self.focused_node = None
        self.route_calls = []
        self.route_result = False
        self.cycle_calls = []

    def route_key_event(self, event, app):
        self.route_calls.append((event, app))
        return bool(self.route_result)

    def cycle_focus(self, scene, *, forward: bool, window, pointer_pos):
        self.cycle_calls.append((scene, bool(forward), window, pointer_pos))
        return False


class _StubOverlay:
    def has_overlay(self, overlay_id: str) -> bool:
        return False


class _StubScene:
    def __init__(self, *, active_window=None):
        self._active_window = active_window

    def active_window(self):
        return self._active_window


class _StubWindow:
    def __init__(self):
        self.calls = []

    def handle_event(self, event, app):
        self.calls.append((event, app))
        return False


class _StubApp:
    def __init__(self, *, scene_name: str, task_panel_focus):
        self.active_scene_name = str(scene_name)
        self.scene = object()
        self.actions = _StubActions()
        self.overlay = _StubOverlay()
        self.task_panel_focus = task_panel_focus
        self.focus = _StubFocus()
        self._scheduler = _StubScheduler()

    def get_scene_scheduler(self, scene_name: str):
        return self._scheduler


class _StubScheduler:
    def set_message_dispatch_limit(self, limit: int):
        pass


class _StubHost:
    def __init__(self):
        self.app = _StubApp(
            scene_name="control_showcase",
            task_panel_focus=_StubTaskPanelFocus(is_active=True),
        )


class TestTaskPanelF1Toggle(unittest.TestCase):
    def test_keyboard_manager_allows_f1_action_while_task_panel_mode_active(self):
        scene = _StubScene()
        task_panel_focus = _StubTaskPanelFocus(is_active=True)
        app = _StubApp(scene_name="main", task_panel_focus=task_panel_focus)

        app.actions.register_action("toggle_task_panel_focus", lambda _event: task_panel_focus.toggle(scene, app))
        app.actions.bind_key(pygame.K_F1, "toggle_task_panel_focus", scene="main")

        manager = KeyboardManager()
        event = _StubKeyEvent(key=pygame.K_F1)

        consumed = manager.route_key_event(scene, event, app)

        self.assertTrue(consumed)
        self.assertTrue(event.default_prevented)
        self.assertTrue(event.propagation_stopped)
        self.assertEqual(1, len(task_panel_focus.toggle_calls))
        self.assertEqual([], task_panel_focus.cycle_calls)

    def test_control_showcase_binds_scene_owned_f1_toggle(self):
        host = _StubHost()
        feature = ShowcaseFeature()

        feature.bind_runtime(host)

        self.assertIn(
            (pygame.K_F1, "toggle_task_panel_focus_control_showcase", "control_showcase"),
            host.app.actions.bind_global_calls,
        )

        action_id, handler = host.app.actions.register_calls[-1]
        self.assertEqual("toggle_task_panel_focus_control_showcase", action_id)

        result = bool(handler(None))
        self.assertTrue(result)
        self.assertEqual(1, len(host.app.task_panel_focus.toggle_calls))

    def test_control_showcase_binds_scene_owned_escape_global_exit(self):
        host = _StubHost()
        feature = ShowcaseFeature()

        feature.bind_runtime(host)

        self.assertIn(
            (pygame.K_ESCAPE, "exit", "control_showcase"),
            host.app.actions.bind_global_calls,
        )

    def test_main_binds_scene_owned_escape_global_exit(self):
        host = _StubHost()
        feature = MainFeature()

        with patch("demo_features.main.main_feature.setup_routed_runtime"):
            feature.bind_runtime(host)

        self.assertIn(
            (pygame.K_ESCAPE, "exit", "main"),
            host.app.actions.bind_global_calls,
        )

    def test_accessibility_tab_is_consumed_by_focused_control(self):
        scene = _StubScene()
        task_panel_focus = _StubTaskPanelFocus(is_active=False)
        app = _StubApp(scene_name="main", task_panel_focus=task_panel_focus)
        app.focus.focused_node = object()

        manager = KeyboardManager()
        event = _StubKeyEvent(key=pygame.K_TAB)

        consumed = manager.route_key_event(scene, event, app)

        self.assertTrue(consumed)
        self.assertTrue(event.default_prevented)
        self.assertTrue(event.propagation_stopped)
        self.assertEqual(1, len(app.focus.cycle_calls))

    def test_non_accessible_key_routes_to_active_window_before_screen_handler(self):
        window = _StubWindow()
        scene = _StubScene(active_window=window)
        task_panel_focus = _StubTaskPanelFocus(is_active=False)
        app = _StubApp(scene_name="main", task_panel_focus=task_panel_focus)
        app.focus.route_result = False

        screen_calls = []

        def _screen_handler(_event):
            screen_calls.append(True)
            return True

        manager = KeyboardManager()
        event = _StubKeyEvent(key=pygame.K_F2)

        consumed = manager.route_key_event(scene, event, app, _screen_handler)

        self.assertTrue(consumed)
        self.assertEqual(1, len(window.calls))
        self.assertEqual([], screen_calls)

    def test_accessibility_down_is_consumed_by_focused_control_without_fallthrough(self):
        window = _StubWindow()
        scene = _StubScene(active_window=window)
        task_panel_focus = _StubTaskPanelFocus(is_active=False)
        app = _StubApp(scene_name="main", task_panel_focus=task_panel_focus)
        app.focus.focused_node = object()
        app.focus.route_result = False

        screen_calls = []

        def _screen_handler(_event):
            screen_calls.append(True)
            return True

        manager = KeyboardManager()
        event = _StubKeyEvent(key=pygame.K_DOWN)

        consumed = manager.route_key_event(scene, event, app, _screen_handler)

        self.assertTrue(consumed)
        self.assertTrue(event.default_prevented)
        self.assertTrue(event.propagation_stopped)
        self.assertEqual(1, len(app.focus.route_calls))
        self.assertEqual([], window.calls)
        self.assertEqual([], screen_calls)

    def test_arrow_left_is_consumed_and_routed_to_focused_control(self):
        window = _StubWindow()
        scene = _StubScene(active_window=window)
        task_panel_focus = _StubTaskPanelFocus(is_active=False)
        app = _StubApp(scene_name="main", task_panel_focus=task_panel_focus)
        app.focus.focused_node = object()
        app.focus.route_result = False

        screen_calls = []

        def _screen_handler(_event):
            screen_calls.append(True)
            return True

        manager = KeyboardManager()
        event = _StubKeyEvent(key=pygame.K_LEFT)

        consumed = manager.route_key_event(scene, event, app, _screen_handler)

        self.assertTrue(consumed)
        self.assertTrue(event.default_prevented)
        self.assertTrue(event.propagation_stopped)
        self.assertEqual(1, len(app.focus.route_calls))
        self.assertEqual([], window.calls)
        self.assertEqual([], screen_calls)

    def test_arrow_right_is_consumed_even_without_focus(self):
        window = _StubWindow()
        scene = _StubScene(active_window=window)
        task_panel_focus = _StubTaskPanelFocus(is_active=False)
        app = _StubApp(scene_name="main", task_panel_focus=task_panel_focus)

        screen_calls = []

        def _screen_handler(_event):
            screen_calls.append(True)
            return True

        manager = KeyboardManager()
        event = _StubKeyEvent(key=pygame.K_RIGHT)

        consumed = manager.route_key_event(scene, event, app, _screen_handler)

        self.assertTrue(consumed)
        self.assertTrue(event.default_prevented)
        self.assertTrue(event.propagation_stopped)
        self.assertEqual(1, len(app.focus.route_calls))
        self.assertEqual([], window.calls)
        self.assertEqual([], screen_calls)

    def test_non_accessible_key_routes_to_screen_handler_when_no_active_window(self):
        scene = _StubScene(active_window=None)
        task_panel_focus = _StubTaskPanelFocus(is_active=False)
        app = _StubApp(scene_name="main", task_panel_focus=task_panel_focus)
        app.focus.route_result = False

        screen_calls = []

        def _screen_handler(_event):
            screen_calls.append(True)
            return True

        manager = KeyboardManager()
        event = _StubKeyEvent(key=pygame.K_F2)

        consumed = manager.route_key_event(scene, event, app, _screen_handler)

        self.assertTrue(consumed)
        self.assertEqual([True], screen_calls)


if __name__ == "__main__":
    unittest.main()
