import unittest

from gui_do_demo import GuiDoDemo


class _StubWindow:
    def __init__(self):
        self.visible = False


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
        demo.life_window = _StubWindow()
        demo.mandel_window = _StubWindow()
        demo.systems_window = _StubWindow()
        demo.life_toggle_window = _StubToggle(False)
        demo.mandel_toggle_window = _StubToggle(False)
        demo.systems_toggle_window = _StubToggle(False)
        return demo

    def test_programmatic_visibility_syncs_all_task_panel_toggles(self):
        demo = self._make_demo()

        demo.set_life_window_visible(True)
        demo.set_mandel_window_visible(True)
        demo.set_systems_window_visible(True)

        self.assertTrue(demo.life_window.visible)
        self.assertTrue(demo.mandel_window.visible)
        self.assertTrue(demo.systems_window.visible)
        self.assertTrue(demo.life_toggle_window.pushed)
        self.assertTrue(demo.mandel_toggle_window.pushed)
        self.assertTrue(demo.systems_toggle_window.pushed)
        self.assertEqual(3, demo.app.tile_windows_calls)

    def test_from_toggle_path_does_not_overwrite_toggle_state(self):
        demo = self._make_demo()
        demo.life_toggle_window.pushed = False

        demo.set_life_window_visible(True, from_toggle=True)

        self.assertTrue(demo.life_window.visible)
        self.assertFalse(demo.life_toggle_window.pushed)


if __name__ == "__main__":
    unittest.main()
