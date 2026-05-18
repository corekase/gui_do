import unittest

from gui_do.app.gui_application import GuiApplication


class _OverlayStub:
    def __init__(self, *, palette_open: bool):
        self._palette_open = bool(palette_open)

    def has_overlay(self, owner_id: str) -> bool:
        return self._palette_open and str(owner_id) == "__command_palette__"


class _FocusStub:
    def __init__(self, focused_node=None):
        self.focused_node = focused_node


class TestGuiApplicationCommandPaletteFocusGate(unittest.TestCase):
    def test_should_restore_active_window_focus_false_when_palette_open(self):
        app = GuiApplication.__new__(GuiApplication)
        app.overlay = _OverlayStub(palette_open=True)

        self.assertFalse(app._should_restore_active_window_focus(object()))

    def test_should_restore_active_window_focus_true_when_palette_closed(self):
        app = GuiApplication.__new__(GuiApplication)
        app.overlay = _OverlayStub(palette_open=False)

        self.assertTrue(app._should_restore_active_window_focus(object()))

    def test_should_restore_active_window_focus_false_for_missing_window(self):
        app = GuiApplication.__new__(GuiApplication)
        app.overlay = _OverlayStub(palette_open=False)

        self.assertFalse(app._should_restore_active_window_focus(None))


if __name__ == "__main__":
    unittest.main()
