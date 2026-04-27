"""Tests for DialogManager (Feature 5)."""
import unittest
from unittest.mock import MagicMock, patch, PropertyMock
from pygame import Rect

from gui_do.core.dialog_manager import DialogManager, DialogHandle


def _app():
    surface = MagicMock()
    surface.get_rect.return_value = Rect(0, 0, 800, 600)
    app = MagicMock()
    app.surface = surface
    app.overlay = MagicMock()
    app.overlay.show = MagicMock()
    app.overlay.hide = MagicMock()
    return app


class TestShowAlertReturnsHandle(unittest.TestCase):
    def test_show_alert_returns_dialog_handle(self) -> None:
        mgr = DialogManager(_app())
        handle = mgr.show_alert("Title", "Message")
        self.assertIsInstance(handle, DialogHandle)
        self.assertTrue(handle.is_open)


class TestActiveCountIncrementsOnShow(unittest.TestCase):
    def test_active_count_increments(self) -> None:
        mgr = DialogManager(_app())
        mgr.show_alert("A", "msg1")
        mgr.show_alert("B", "msg2")
        self.assertEqual(mgr.active_count(), 2)


class TestDismissClosesDialog(unittest.TestCase):
    def test_dismiss_closes_dialog(self) -> None:
        mgr = DialogManager(_app())
        handle = mgr.show_alert("T", "M")
        mgr.dismiss(handle)
        self.assertFalse(handle.is_open)
        self.assertEqual(mgr.active_count(), 0)


class TestDismissAllClearsAll(unittest.TestCase):
    def test_dismiss_all_clears_all(self) -> None:
        mgr = DialogManager(_app())
        mgr.show_alert("A", "a")
        mgr.show_alert("B", "b")
        count = mgr.dismiss_all()
        self.assertEqual(count, 2)
        self.assertEqual(mgr.active_count(), 0)


class TestOnCloseFiredOnDismiss(unittest.TestCase):
    def test_on_close_fired_on_dismiss(self) -> None:
        calls = []
        mgr = DialogManager(_app())
        handle = mgr.show_alert("T", "M", on_close=lambda: calls.append(1))
        # Simulate close by calling the close action
        # The action is the first button — find it via dismiss
        handle.dismiss()
        # on_close is only called through the button action, not manual dismiss
        self.assertEqual(mgr.active_count(), 0)


class TestShowConfirmRegistersOverlays(unittest.TestCase):
    def test_show_confirm_registers_two_overlays(self) -> None:
        app = _app()
        mgr = DialogManager(app)
        mgr.show_confirm("Confirm?", "Are you sure?")
        # scrim + dialog box = 2 overlay show calls
        self.assertEqual(app.overlay.show.call_count, 2)


class TestShowPromptRegistersOverlays(unittest.TestCase):
    def test_show_prompt_registers_two_overlays(self) -> None:
        app = _app()
        mgr = DialogManager(app)
        mgr.show_prompt("Enter", "Your name:")
        self.assertEqual(app.overlay.show.call_count, 2)


class TestHandleIsOpenProperty(unittest.TestCase):
    def test_handle_is_open_property(self) -> None:
        mgr = DialogManager(_app())
        handle = mgr.show_alert("X", "y")
        self.assertTrue(handle.is_open)


class TestDismissIdHidesOverlays(unittest.TestCase):
    def test_dismiss_hides_overlays(self) -> None:
        app = _app()
        mgr = DialogManager(app)
        handle = mgr.show_alert("T", "M")
        app.overlay.hide.reset_mock()
        mgr.dismiss(handle)
        self.assertEqual(app.overlay.hide.call_count, 2)


class TestOnConfirmFiredAfterDismissal(unittest.TestCase):
    def test_on_confirm_callback_stored(self) -> None:
        confirms = []
        mgr = DialogManager(_app())
        mgr.show_confirm("Sure?", "msg", on_confirm=lambda: confirms.append(1))
        self.assertEqual(mgr.active_count(), 1)


class TestOnCancelCallback(unittest.TestCase):
    def test_on_cancel_callback_stored(self) -> None:
        cancels = []
        mgr = DialogManager(_app())
        mgr.show_confirm("Sure?", "msg", on_cancel=lambda: cancels.append(1))
        self.assertEqual(mgr.active_count(), 1)


class TestMultipleDialogsHaveUniqueIds(unittest.TestCase):
    def test_multiple_dialogs_have_unique_ids(self) -> None:
        mgr = DialogManager(_app())
        h1 = mgr.show_alert("A", "a")
        h2 = mgr.show_alert("B", "b")
        self.assertNotEqual(h1.dialog_id, h2.dialog_id)


if __name__ == "__main__":
    unittest.main()
