import unittest

from gui_do_demo import GuiDoDemo
from gui_do.features.feature_lifecycle import FeatureWindowPresentationModel


class _StubWindow:
    def __init__(self, control_id: str):
        self.control_id = str(control_id)
        self.visible = False


class _StubFeature:
    def __init__(self, control_id: str):
        self.window = _StubWindow(control_id)


class _StubToggle:
    def __init__(self, pushed: bool = False):
        self.pushed = bool(pushed)


class _StubApp:
    def __init__(self):
        self.tile_windows_calls = 0

    def tile_windows(self) -> None:
        self.tile_windows_calls += 1


class TestMainSceneTaskPanelToggleSync(unittest.TestCase):
    def _make_demo(self):
        demo = GuiDoDemo.__new__(GuiDoDemo)
        demo.app = _StubApp()
        demo._life_feature = _StubFeature("life_window")
        demo._mandel_feature = _StubFeature("mandelbrot_window")
        demo._systems_feature = _StubFeature("systems_window")
        demo.life_toggle_window = _StubToggle(False)
        demo.mandel_toggle_window = _StubToggle(False)
        demo.systems_toggle_window = _StubToggle(False)
        demo.window_presentation = FeatureWindowPresentationModel(demo, tile_windows=demo.app.tile_windows)
        demo.window_presentation.register_feature_window(
            "life",
            feature_attr="_life_feature",
            toggle_attr="life_toggle_window",
        )
        demo.window_presentation.register_feature_window(
            "mandel",
            feature_attr="_mandel_feature",
            toggle_attr="mandel_toggle_window",
        )
        demo.window_presentation.register_feature_window(
            "systems",
            feature_attr="_systems_feature",
            toggle_attr="systems_toggle_window",
        )
        return demo

    def test_programmatic_visibility_syncs_all_task_panel_toggles(self):
        demo = self._make_demo()

        demo.window_presentation.set_visible("life", True)
        demo.window_presentation.set_visible("mandel", True)
        demo.window_presentation.set_visible("systems", True)

        self.assertTrue(demo._life_feature.window.visible)
        self.assertTrue(demo._mandel_feature.window.visible)
        self.assertTrue(demo._systems_feature.window.visible)
        self.assertTrue(demo.life_toggle_window.pushed)
        self.assertTrue(demo.mandel_toggle_window.pushed)
        self.assertTrue(demo.systems_toggle_window.pushed)
        self.assertEqual(3, demo.app.tile_windows_calls)

    def test_from_toggle_path_does_not_overwrite_toggle_state(self):
        demo = self._make_demo()
        demo.life_toggle_window.pushed = False

        demo.window_presentation.set_visible("life", True, from_toggle=True)

        self.assertTrue(demo._life_feature.window.visible)
        self.assertFalse(demo.life_toggle_window.pushed)

    def test_menu_toggle_routes_by_window_control_id(self):
        demo = self._make_demo()

        handled = demo.window_presentation.handle_window_toggle(demo._systems_feature.window, True)

        self.assertTrue(handled)
        self.assertTrue(demo._systems_feature.window.visible)
        self.assertTrue(demo.systems_toggle_window.pushed)


if __name__ == "__main__":
    unittest.main()
