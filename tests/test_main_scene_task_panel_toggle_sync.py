import unittest

from gui_do_demo import GuiDoDemo
from gui_do.features.feature_lifecycle import FeatureWindowPresentationModel


class _StubWindowParent:
    def __init__(self):
        self.raised = []

    def _raise_window(self, window):
        self.raised.append(window)


class _StubWindow:
    def __init__(self, control_id: str):
        self.control_id = str(control_id)
        self.visible = False
        self.parent = _StubWindowParent()


class _StubFeature:
    def __init__(self, control_id: str):
        self.window = _StubWindow(control_id)


class _StubToggle:
    def __init__(self, pushed: bool = False):
        self.pushed = bool(pushed)


class _StubApp:
    def __init__(self, *, tiling_enabled: bool = False):
        self.tile_windows_calls = 0
        self._tiling_enabled = bool(tiling_enabled)

    def tile_windows(self, *args, **kwargs) -> None:
        self.tile_windows_calls += 1

    def is_window_tiling_enabled(self, scene_name=None) -> bool:
        return self._tiling_enabled


class TestMainSceneTaskPanelToggleSync(unittest.TestCase):
    def _make_demo(self, *, tiling_enabled: bool = False):
        demo = GuiDoDemo.__new__(GuiDoDemo)
        demo.app = _StubApp(tiling_enabled=tiling_enabled)
        demo._life_feature = _StubFeature("life_window")
        demo._mandel_feature = _StubFeature("mandelbrot_window")
        demo._extra_feature = _StubFeature("extra_window")
        demo.life_toggle_window = _StubToggle(False)
        demo.mandel_toggle_window = _StubToggle(False)
        demo.extra_toggle_window = _StubToggle(False)
        demo.window_presentation = FeatureWindowPresentationModel(demo, tile_windows=demo.app.tile_windows)
        demo.window_presentation.register_feature_window(
            "life",
            feature_attribute_name="_life_feature",
            toggle_attribute_name="life_toggle_window",
        )
        demo.window_presentation.register_feature_window(
            "mandel",
            feature_attribute_name="_mandel_feature",
            toggle_attribute_name="mandel_toggle_window",
        )
        demo.window_presentation.register_feature_window(
            "extra",
            feature_attribute_name="_extra_feature",
            toggle_attribute_name="extra_toggle_window",
        )
        return demo

    def test_programmatic_visibility_syncs_all_task_panel_toggles(self):
        demo = self._make_demo(tiling_enabled=True)

        demo.window_presentation.set_visible("life", True)
        demo.window_presentation.set_visible("mandel", True)
        demo.window_presentation.set_visible("extra", True)

        self.assertTrue(demo._life_feature.window.visible)
        self.assertTrue(demo._mandel_feature.window.visible)
        self.assertTrue(demo._extra_feature.window.visible)
        self.assertTrue(demo.life_toggle_window.pushed)
        self.assertTrue(demo.mandel_toggle_window.pushed)
        self.assertTrue(demo.extra_toggle_window.pushed)
        self.assertEqual(3, demo.app.tile_windows_calls)

    def test_initial_visibility_uses_per_binding_startup_visibility(self):
        demo = self._make_demo()
        demo.window_presentation.register_feature_window(
            "opt_out_test",
            feature_attribute_name="_extra_feature",
            startup_visible=True,
        )

        demo.window_presentation.sync_initial_visibility()

        self.assertTrue(demo._extra_feature.window.visible)
        self.assertFalse(demo._life_feature.window.visible)
        self.assertFalse(demo._mandel_feature.window.visible)

    def test_from_toggle_path_does_not_overwrite_toggle_state(self):
        demo = self._make_demo()
        demo.life_toggle_window.pushed = False

        demo.window_presentation.set_visible("life", True, from_toggle=True)

        self.assertTrue(demo._life_feature.window.visible)
        self.assertFalse(demo.life_toggle_window.pushed)

    def test_menu_toggle_routes_by_window_control_id(self):
        demo = self._make_demo()

        handled = demo.window_presentation.handle_window_toggle(demo._extra_feature.window, True)

        self.assertTrue(handled)
        self.assertTrue(demo._extra_feature.window.visible)
        self.assertTrue(demo.extra_toggle_window.pushed)

    def test_show_raises_already_visible_window_in_parent(self):
        demo = self._make_demo()
        window = demo._life_feature.window
        window.visible = True

        demo.window_presentation.show("life")

        self.assertEqual([window], window.parent.raised)
        self.assertEqual(0, demo.app.tile_windows_calls)
        self.assertFalse(demo.life_toggle_window.pushed)

    def test_set_visible_hidden_window_raises_before_relayout(self):
        demo = self._make_demo(tiling_enabled=True)
        window = demo._life_feature.window
        window.visible = False

        demo.window_presentation.set_visible("life", True)

        self.assertEqual([window], window.parent.raised)
        self.assertEqual(1, demo.app.tile_windows_calls)
        self.assertTrue(window.visible)

    def test_show_raises_and_relayouts_already_visible_window_when_tiling_enabled(self):
        demo = self._make_demo(tiling_enabled=True)
        window = demo._life_feature.window
        window.visible = True

        demo.window_presentation.show("life")

        self.assertEqual([window], window.parent.raised)
        self.assertEqual(0, demo.app.tile_windows_calls)
        self.assertFalse(demo.life_toggle_window.pushed)


if __name__ == "__main__":
    unittest.main()
