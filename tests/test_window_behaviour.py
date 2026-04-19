import unittest
from types import SimpleNamespace

from pygame import Rect

from gui.utility.events import GuiError
from gui.widgets.window import Window


class WindowBehaviourTests(unittest.TestCase):
    def _build_window_stub(self):
        window = Window.__new__(Window)
        window.x = 100
        window.y = 200
        window.width = 300
        window.height = 150
        window.titlebar_size = 20
        window._visible = True
        window.gui = SimpleNamespace(
            windows=[window],
            active_window=window,
            workspace_state=SimpleNamespace(active_object=window),
            raise_window=lambda _window: None,
        )
        window.window_widget_lower_bitmap = type("BitmapStub", (), {"get_rect": lambda self: Rect(0, 0, 16, 16)})()
        return window

    def test_get_title_bar_rect_uses_position_and_titlebar_size(self) -> None:
        window = self._build_window_stub()

        rect = Window.get_title_bar_rect(window)

        self.assertEqual(rect, Rect(100, 180, 300, 20))

    def test_get_window_rect_includes_titlebar_region(self) -> None:
        window = self._build_window_stub()

        rect = Window.get_window_rect(window)

        self.assertEqual(rect, Rect(100, 180, 300, 170))

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

    def test_visible_true_activates_and_raises_registered_window(self) -> None:
        window = self._build_window_stub()
        other = self._build_window_stub()
        other._visible = True
        window._visible = False
        gui = SimpleNamespace()
        gui.windows = [window, other]
        gui.active_window = other
        gui.workspace_state = SimpleNamespace(active_object=other)

        def _raise_window(target):
            gui.windows.remove(target)
            gui.windows.append(target)

        gui.raise_window = _raise_window
        window.gui = gui

        Window.visible.fset(window, True)

        self.assertTrue(window.visible)
        self.assertIs(gui.active_window, window)
        self.assertIs(gui.workspace_state.active_object, window)
        self.assertEqual(gui.windows[-1], window)

    def test_hiding_active_window_selects_next_top_visible_window(self) -> None:
        window = self._build_window_stub()
        lower_visible = self._build_window_stub()
        lower_hidden = self._build_window_stub()
        window._visible = True
        lower_visible._visible = True
        lower_hidden._visible = False
        gui = SimpleNamespace()
        gui.windows = [lower_hidden, lower_visible, window]
        gui.active_window = window
        gui.workspace_state = SimpleNamespace(active_object=window)
        gui.raise_window = lambda _target: None
        window.gui = gui

        Window.visible.fset(window, False)

        self.assertFalse(window.visible)
        self.assertIs(gui.active_window, lower_visible)
        self.assertIs(gui.workspace_state.active_object, lower_visible)

    def test_hiding_window_promotes_top_visible_when_active_pointer_is_stale(self) -> None:
        window = self._build_window_stub()
        lower_visible = self._build_window_stub()
        window._visible = True
        lower_visible._visible = True
        gui = SimpleNamespace()
        gui.windows = [lower_visible, window]
        gui.active_window = None
        gui.workspace_state = SimpleNamespace(active_object=None)
        gui.raise_window = lambda _target: None
        window.gui = gui

        Window.visible.fset(window, False)

        self.assertFalse(window.visible)
        self.assertIs(gui.active_window, lower_visible)
        self.assertIs(gui.workspace_state.active_object, lower_visible)


if __name__ == "__main__":
    unittest.main()
