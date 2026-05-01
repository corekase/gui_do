import unittest

from gui_do.actions.action_manager import ActionManager
from gui_do.app.gui_application import GuiApplication
from gui_do.events.gui_event import EventType, GuiEvent
from gui_do.focus.window_focus_manager import WindowFocusManager


class _StubNode:
    def __init__(self, control_id: str, *, is_window: bool = True, visible: bool = True, enabled: bool = True):
        self.control_id = str(control_id)
        self.visible = bool(visible)
        self.enabled = bool(enabled)
        self._is_window = bool(is_window)

    def is_window(self) -> bool:
        return self._is_window


class _StubSceneForFocus:
    def __init__(self, nodes):
        self._nodes = list(nodes)

    def _walk_nodes(self):
        return list(self._nodes)


class _StubSceneForActions:
    def __init__(self, *, has_window: bool):
        self._has_window = bool(has_window)

    def active_window(self):
        return object() if self._has_window else None


class _StubAppForActions:
    def __init__(self, *, scene_name: str, has_window: bool):
        self.active_scene_name = str(scene_name)
        self.scene = _StubSceneForActions(has_window=has_window)


class TestRuntimeGuaranteesAndDeterminism(unittest.TestCase):
    def test_scheduler_dispatch_budget_clamps_to_min_and_max(self):
        app = GuiApplication.__new__(GuiApplication)

        self.assertEqual(0.5, app._compute_scheduler_dispatch_budget_ms(-1.0))
        self.assertEqual(0.5, app._compute_scheduler_dispatch_budget_ms(0.0))
        self.assertEqual(4.0, app._compute_scheduler_dispatch_budget_ms(1.0))

    def test_scheduler_dispatch_budget_scales_in_midrange(self):
        app = GuiApplication.__new__(GuiApplication)

        budget_ms = app._compute_scheduler_dispatch_budget_ms(0.020)

        self.assertAlmostEqual(2.4, budget_ms, places=7)

    def test_window_focus_candidate_windows_are_sorted_deterministically(self):
        manager = WindowFocusManager()
        scene = _StubSceneForFocus(
            [
                _StubNode("window_z"),
                _StubNode("window_b"),
                _StubNode("window_a"),
                _StubNode("hidden_window", visible=False),
                _StubNode("disabled_window", enabled=False),
                _StubNode("not_a_window", is_window=False),
            ]
        )

        candidates = manager._candidate_windows(scene)

        self.assertEqual(["window_a", "window_b", "window_z"], [node.control_id for node in candidates])

    def test_action_precedence_prefers_scene_window_binding(self):
        manager = ActionManager()
        app = _StubAppForActions(scene_name="scene_a", has_window=True)
        event = GuiEvent(kind=EventType.KEY_DOWN, type=0, key=42)
        calls = []

        def _handler(name, consumed=True):
            def _run(_event):
                calls.append(name)
                return consumed
            return _run

        manager.register_action("scene_window", _handler("scene_window", consumed=True))
        manager.register_action("scene_screen", _handler("scene_screen", consumed=True))
        manager.register_action("global_window", _handler("global_window", consumed=True))
        manager.register_action("global_screen", _handler("global_screen", consumed=True))

        manager.bind_key(42, "scene_window", scene="scene_a", window_only=True)
        manager.bind_key(42, "scene_screen", scene="scene_a", window_only=False)
        manager.bind_key(42, "global_window", scene=None, window_only=True)
        manager.bind_key(42, "global_screen", scene=None, window_only=False)

        consumed = manager.trigger_from_event(event, app)

        self.assertTrue(consumed)
        self.assertEqual(["scene_window"], calls)

    def test_action_precedence_without_active_window_skips_window_only_bindings(self):
        manager = ActionManager()
        app = _StubAppForActions(scene_name="scene_b", has_window=False)
        event = GuiEvent(kind=EventType.KEY_DOWN, type=0, key=77)
        calls = []

        def _handler(name, consumed=True):
            def _run(_event):
                calls.append(name)
                return consumed
            return _run

        manager.register_action("scene_window", _handler("scene_window", consumed=True))
        manager.register_action("scene_screen", _handler("scene_screen", consumed=True))
        manager.register_action("global_window", _handler("global_window", consumed=True))
        manager.register_action("global_screen", _handler("global_screen", consumed=True))

        manager.bind_key(77, "scene_window", scene="scene_b", window_only=True)
        manager.bind_key(77, "scene_screen", scene="scene_b", window_only=False)
        manager.bind_key(77, "global_window", scene=None, window_only=True)
        manager.bind_key(77, "global_screen", scene=None, window_only=False)

        consumed = manager.trigger_from_event(event, app)

        self.assertTrue(consumed)
        self.assertEqual(["scene_screen"], calls)


if __name__ == "__main__":
    unittest.main()
