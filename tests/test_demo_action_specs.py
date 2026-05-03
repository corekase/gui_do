import unittest

from gui_do import declare_host_actions
from demo_features.demo_config import ACTION_SPECS


class _StubActionRegistry:
    def __init__(self):
        self.declarations = []

    def declare(self, action_id: str, label: str, handler, category=None):
        self.declarations.append(
            {
                "action_id": str(action_id),
                "label": str(label),
                "handler": handler,
                "category": category,
            }
        )


class _StubWindowPresentation:
    def __init__(self):
        self.declare_calls = []

    def declare_actions(self, registry, *, category: str):
        self.declare_calls.append((registry, str(category)))


class _StubSceneTransitions:
    def __init__(self):
        self.go_calls = []

    def go(self, scene_name: str):
        self.go_calls.append(str(scene_name))


class _StubPaletteManager:
    def __init__(self):
        self.show_calls = []

    def show(self, app):
        self.show_calls.append(app)


class _StubApp:
    def __init__(self):
        self.running = True


class _StubHost:
    def __init__(self):
        self.action_registry = _StubActionRegistry()
        self.window_presentation = _StubWindowPresentation()
        self.scene_transitions = _StubSceneTransitions()
        self._palette_manager = _StubPaletteManager()
        self.app = _StubApp()


class TestDemoActionSpecs(unittest.TestCase):
    def _make_host(self):
        return _StubHost()

    def _declarations_by_id(self, host):
        return {item["action_id"]: item for item in host.action_registry.declarations}

    def test_register_app_actions_declares_expected_metadata(self):
        host = self._make_host()

        declare_host_actions(host, ACTION_SPECS)

        by_id = self._declarations_by_id(host)
        self.assertEqual(
            ["nav_main", "nav_showcase", "exit", "palette_open"],
            [d["action_id"] for d in host.action_registry.declarations],
        )
        self.assertEqual("Exit", by_id["exit"]["label"])
        self.assertEqual("File", by_id["exit"]["category"])
        self.assertEqual("Go to Main Scene", by_id["nav_main"]["label"])
        self.assertEqual("Scenes", by_id["nav_main"]["category"])
        self.assertEqual("Go to Controls Showcase", by_id["nav_showcase"]["label"])
        self.assertEqual("Scenes", by_id["nav_showcase"]["category"])
        self.assertEqual("Open Command Palette (F5)", by_id["palette_open"]["label"])
        self.assertIsNone(by_id["palette_open"]["category"])

        self.assertEqual(1, len(host.window_presentation.declare_calls))
        self.assertEqual("Windows", host.window_presentation.declare_calls[0][1])

    def test_registered_handlers_preserve_behavior(self):
        host = self._make_host()

        declare_host_actions(host, ACTION_SPECS)
        by_id = self._declarations_by_id(host)

        self.assertTrue(by_id["exit"]["handler"](None, None))
        self.assertFalse(host.app.running)

        self.assertTrue(by_id["nav_main"]["handler"](None, None))
        self.assertTrue(by_id["nav_showcase"]["handler"](None, None))
        self.assertEqual(["main", "control_showcase"], host.scene_transitions.go_calls)

        self.assertTrue(by_id["palette_open"]["handler"](None, None))
        self.assertEqual([host.app], host._palette_manager.show_calls)


if __name__ == "__main__":
    unittest.main()
