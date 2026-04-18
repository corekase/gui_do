import unittest

from pygame import Rect

from gui.utility.constants import GuiError
from gui.widgets.window import Window


class WindowBehaviourTests(unittest.TestCase):
    def _build_window_stub(self):
        window = Window.__new__(Window)
        window.x = 100
        window.y = 200
        window.width = 300
        window.height = 150
        window.titlebar_size = 20
        window.window_widget_lower_bitmap = type("BitmapStub", (), {"get_rect": lambda self: Rect(0, 0, 16, 16)})()
        return window

    def test_get_title_bar_rect_uses_position_and_titlebar_size(self) -> None:
        window = self._build_window_stub()

        rect = Window.get_title_bar_rect(window)

        self.assertEqual(rect, Rect(100, 180, 300, 20))

    def test_get_window_rect_includes_titlebar_region(self) -> None:
        window = self._build_window_stub()

        rect = Window.get_window_rect(window)

        self.assertEqual(rect, Rect(100, 179, 300, 169))

    def test_get_widget_rect_is_anchored_to_top_right_control_area(self) -> None:
        window = self._build_window_stub()

        rect = Window.get_widget_rect(window)

        self.assertEqual(rect, Rect(382, 181, 16, 16))

    def test_position_property_validates_tuple_shape(self) -> None:
        window = self._build_window_stub()

        with self.assertRaises(GuiError):
            Window.position.fset(window, "invalid")  # type: ignore[arg-type]
        with self.assertRaises(GuiError):
            Window.position.fset(window, (1,))  # type: ignore[arg-type]

        Window.position.fset(window, (120, 220))
        self.assertEqual(window.position, (120, 220))

    def test_visible_property_requires_bool(self) -> None:
        window = self._build_window_stub()

        with self.assertRaises(GuiError):
            Window.visible.fset(window, "yes")  # type: ignore[arg-type]

        Window.visible.fset(window, True)
        self.assertTrue(window.visible)

    def test_lifecycle_and_event_handlers_invoke_configured_callbacks(self) -> None:
        window = self._build_window_stub()
        calls = []

        window._preamble = lambda: calls.append("preamble")
        window._postamble = lambda: calls.append("postamble")
        window._event_handler = lambda event: calls.append(("event", event))

        Window.run_preamble(window)
        Window.handle_event(window, "evt")
        Window.run_postamble(window)

        self.assertEqual(calls, ["preamble", ("event", "evt"), "postamble"])


if __name__ == "__main__":
    unittest.main()
