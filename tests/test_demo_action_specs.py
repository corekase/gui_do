import unittest

from gui_do_demo import GuiDoDemo


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


class TestDemoActionSpecs(unittest.TestCase):
    def _make_demo(self):
        demo = GuiDoDemo.__new__(GuiDoDemo)
        demo.action_registry = _StubActionRegistry()
        demo.window_presentation = _StubWindowPresentation()
        demo.scene_transitions = _StubSceneTransitions()
        demo._palette_manager = _StubPaletteManager()
        demo.app = _StubApp()
        return demo

    def _declarations_by_id(self, demo):
        return {item["action_id"]: item for item in demo.action_registry.declarations}

    def test_register_app_actions_declares_expected_metadata(self):
        demo = self._make_demo()

        demo._register_app_actions()

        by_id = self._declarations_by_id(demo)
        self.assertEqual(
            ["exit", "nav_main", "nav_showcase", "palette_open"],
            [d["action_id"] for d in demo.action_registry.declarations],
        )
        self.assertEqual("Exit", by_id["exit"]["label"])
        self.assertEqual("File", by_id["exit"]["category"])
        self.assertEqual("Go to Main Scene", by_id["nav_main"]["label"])
        self.assertEqual("Scenes", by_id["nav_main"]["category"])
        self.assertEqual("Go to Controls Showcase", by_id["nav_showcase"]["label"])
        self.assertEqual("Scenes", by_id["nav_showcase"]["category"])
        self.assertEqual("Open Command Palette (F5)", by_id["palette_open"]["label"])
        self.assertIsNone(by_id["palette_open"]["category"])

        self.assertEqual(1, len(demo.window_presentation.declare_calls))
        self.assertEqual("Windows", demo.window_presentation.declare_calls[0][1])

    def test_registered_handlers_preserve_behavior(self):
        demo = self._make_demo()

        demo._register_app_actions()
        by_id = self._declarations_by_id(demo)

        self.assertTrue(by_id["exit"]["handler"](None, None))
        self.assertFalse(demo.app.running)

        self.assertTrue(by_id["nav_main"]["handler"](None, None))
        self.assertTrue(by_id["nav_showcase"]["handler"](None, None))
        self.assertEqual(["main", "control_showcase"], demo.scene_transitions.go_calls)

        self.assertTrue(by_id["palette_open"]["handler"](None, None))
        self.assertEqual([demo.app], demo._palette_manager.show_calls)


if __name__ == "__main__":
    unittest.main()
