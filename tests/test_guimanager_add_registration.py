import unittest

from gui_manager_test_factory import build_gui_manager_stub
from gui.utility.events import GuiError
from gui.utility.gui_manager import GuiManager
from gui.utility.intermediates.widget import Widget
from gui.widgets.window import Window


class GuiManagerAddRegistrationTests(unittest.TestCase):
    def _build_manager_stub(self):
        return build_gui_manager_stub(surface=object())

    def _build_widget_stub(self, widget_id="w"):
        widget = Widget.__new__(Widget)
        widget.id = widget_id
        widget.window = None
        widget.surface = None
        return widget

    def _build_window_stub(self):
        window = Window.__new__(Window)
        window.widgets = []
        window.surface = object()
        return window

    def test_add_rejects_none_and_unknown_types(self) -> None:
        gui = self._build_manager_stub()

        with self.assertRaises(GuiError):
            GuiManager.add(gui, None)
        with self.assertRaises(GuiError):
            GuiManager.add(gui, object())  # type: ignore[arg-type]

    def test_add_window_registers_and_sets_active_object(self) -> None:
        gui = self._build_manager_stub()
        window = self._build_window_stub()

        returned = GuiManager.add(gui, window)

        self.assertIs(returned, window)
        self.assertIn(window, gui.windows)
        self.assertIs(gui.workspace_state.active_object, window)

    def test_add_rejects_duplicate_widget_id(self) -> None:
        gui = self._build_manager_stub()
        first = self._build_widget_stub("same-id")
        second = self._build_widget_stub("same-id")

        GuiManager.add(gui, first)

        with self.assertRaises(GuiError):
            GuiManager.add(gui, second)

    def test_add_rolls_back_screen_widget_when_post_add_fails(self) -> None:
        gui = self._build_manager_stub()
        widget = self._build_widget_stub("broken-screen")

        def fail_post_add():
            raise RuntimeError("boom")

        widget.on_added_to_gui = fail_post_add

        with self.assertRaises(RuntimeError):
            GuiManager.add(gui, widget)

        self.assertNotIn(widget, gui.widgets)
        self.assertIsNone(widget.window)
        self.assertIsNone(widget.surface)

    def test_add_rolls_back_window_widget_when_post_add_fails(self) -> None:
        gui = self._build_manager_stub()
        window = self._build_window_stub()
        gui.windows.append(window)
        gui.workspace_state.active_object = window

        widget = self._build_widget_stub("broken-window")

        def fail_post_add():
            raise RuntimeError("boom")

        widget.on_added_to_gui = fail_post_add

        with self.assertRaises(RuntimeError):
            GuiManager.add(gui, widget)

        self.assertNotIn(widget, window.widgets)
        self.assertIsNone(widget.window)
        self.assertIsNone(widget.surface)


if __name__ == "__main__":
    unittest.main()
