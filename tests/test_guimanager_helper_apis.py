import unittest
from types import SimpleNamespace

from gui.utility.constants import GuiError
from gui.utility.guimanager import GuiManager
from gui.utility.widget import Widget


class GuiManagerHelperApiTests(unittest.TestCase):
    def _build_manager_stub(self):
        gui = GuiManager.__new__(GuiManager)
        gui.windows = []
        gui.task_panel = None
        gui.lock_area = lambda point: point
        gui._screen_preamble = None
        gui._screen_event_handler = None
        gui._screen_postamble = None
        return gui

    def _build_widget_stub(self, visible=True):
        widget = Widget.__new__(Widget)
        widget._visible = visible
        return widget

    def test_hide_and_show_widgets_toggle_visibility(self) -> None:
        gui = self._build_manager_stub()
        w1 = self._build_widget_stub(True)
        w2 = self._build_widget_stub(False)

        GuiManager.hide_widgets(gui, w1, w2)
        self.assertFalse(w1.visible)
        self.assertFalse(w2.visible)

        GuiManager.show_widgets(gui, w1, w2)
        self.assertTrue(w1.visible)
        self.assertTrue(w2.visible)

    def test_hide_and_show_widgets_reject_non_widget_inputs(self) -> None:
        gui = self._build_manager_stub()
        widget = self._build_widget_stub(True)

        with self.assertRaises(GuiError):
            GuiManager.hide_widgets(gui, widget, object())  # type: ignore[arg-type]
        with self.assertRaises(GuiError):
            GuiManager.show_widgets(gui, object())  # type: ignore[arg-type]

    def test_convert_to_screen_and_window_apply_window_offsets(self) -> None:
        gui = self._build_manager_stub()
        window = SimpleNamespace(x=100, y=50)
        gui.windows = [window]

        screen_point = GuiManager.convert_to_screen(gui, (5, 7), window)
        window_point = GuiManager.convert_to_window(gui, (105, 57), window)

        self.assertEqual(screen_point, (105, 57))
        self.assertEqual(window_point, (5, 7))

    def test_convert_helpers_fallback_when_window_unregistered(self) -> None:
        gui = self._build_manager_stub()
        window = SimpleNamespace(x=100, y=50)

        screen_point = GuiManager.convert_to_screen(gui, (5, 7), window)
        window_point = GuiManager.convert_to_window(gui, (105, 57), window)

        self.assertEqual(screen_point, (5, 7))
        self.assertEqual(window_point, (105, 57))

    def test_convert_helpers_validate_point_shape(self) -> None:
        gui = self._build_manager_stub()

        with self.assertRaises(GuiError):
            GuiManager.convert_to_screen(gui, (1,), None)  # type: ignore[arg-type]
        with self.assertRaises(GuiError):
            GuiManager.convert_to_window(gui, "bad", None)  # type: ignore[arg-type]

    def test_set_screen_lifecycle_validates_callables(self) -> None:
        gui = self._build_manager_stub()

        with self.assertRaises(GuiError):
            GuiManager.set_screen_lifecycle(gui, preamble="nope")  # type: ignore[arg-type]
        with self.assertRaises(GuiError):
            GuiManager.set_screen_lifecycle(gui, event_handler=123)  # type: ignore[arg-type]
        with self.assertRaises(GuiError):
            GuiManager.set_screen_lifecycle(gui, postamble=[])  # type: ignore[arg-type]

        pre = lambda: None
        ev = lambda _event: None
        post = lambda: None
        GuiManager.set_screen_lifecycle(gui, preamble=pre, event_handler=ev, postamble=post)

        self.assertIs(gui._screen_preamble, pre)
        self.assertIs(gui._screen_event_handler, ev)
        self.assertIs(gui._screen_postamble, post)

    def test_set_task_panel_lifecycle_requires_existing_task_panel(self) -> None:
        gui = self._build_manager_stub()

        with self.assertRaises(GuiError):
            GuiManager.set_task_panel_lifecycle(gui)

    def test_set_task_panel_lifecycle_validates_callables(self) -> None:
        gui = self._build_manager_stub()
        panel = SimpleNamespace(_preamble=None, _event_handler=None, _postamble=None)
        gui.task_panel = panel

        with self.assertRaises(GuiError):
            GuiManager.set_task_panel_lifecycle(gui, preamble=1)  # type: ignore[arg-type]
        with self.assertRaises(GuiError):
            GuiManager.set_task_panel_lifecycle(gui, event_handler=1)  # type: ignore[arg-type]
        with self.assertRaises(GuiError):
            GuiManager.set_task_panel_lifecycle(gui, postamble=1)  # type: ignore[arg-type]

        pre = lambda: None
        ev = lambda _event: None
        post = lambda: None
        GuiManager.set_task_panel_lifecycle(gui, preamble=pre, event_handler=ev, postamble=post)

        self.assertIs(panel._preamble, pre)
        self.assertIs(panel._event_handler, ev)
        self.assertIs(panel._postamble, post)


if __name__ == "__main__":
    unittest.main()
