"""Tests for gui_do.state.undo_context_manager (S6)."""
import unittest
from unittest.mock import MagicMock, patch

from gui_do.state.undo_context_manager import UndoContextManager


def _mock_history(*, can_undo=True, can_redo=True):
    h = MagicMock()
    h.can_undo = can_undo
    h.can_redo = can_redo
    return h


class TestUndoContextManagerRegistration(unittest.TestCase):

    def test_initially_empty(self):
        mgr = UndoContextManager()
        self.assertEqual(len(mgr), 0)
        self.assertIsNone(mgr.active_key)
        self.assertIsNone(mgr.active)

    def test_register_increases_len(self):
        mgr = UndoContextManager()
        mgr.register("doc1", _mock_history())
        self.assertEqual(len(mgr), 1)

    def test_register_make_active(self):
        mgr = UndoContextManager()
        h = _mock_history()
        mgr.register("doc1", h, make_active=True)
        self.assertEqual(mgr.active_key, "doc1")
        self.assertIs(mgr.active, h)

    def test_register_default_key_auto_activates(self):
        mgr = UndoContextManager(default_key="canvas")
        h = _mock_history()
        mgr.register("canvas", h)
        self.assertEqual(mgr.active_key, "canvas")

    def test_unregister_removes_key(self):
        mgr = UndoContextManager()
        mgr.register("doc1", _mock_history())
        result = mgr.unregister("doc1")
        self.assertTrue(result)
        self.assertEqual(len(mgr), 0)

    def test_unregister_unknown_returns_false(self):
        mgr = UndoContextManager()
        self.assertFalse(mgr.unregister("ghost"))

    def test_unregister_active_key_clears_active(self):
        mgr = UndoContextManager()
        mgr.register("doc1", _mock_history(), make_active=True)
        mgr.unregister("doc1")
        self.assertIsNone(mgr.active_key)
        self.assertIsNone(mgr.active)

    def test_contains(self):
        mgr = UndoContextManager()
        mgr.register("x", _mock_history())
        self.assertIn("x", mgr)
        self.assertNotIn("y", mgr)

    def test_registered_keys_sorted(self):
        mgr = UndoContextManager()
        mgr.register("z", _mock_history())
        mgr.register("a", _mock_history())
        mgr.register("m", _mock_history())
        self.assertEqual(mgr.registered_keys(), ["a", "m", "z"])

    def test_get_returns_history(self):
        mgr = UndoContextManager()
        h = _mock_history()
        mgr.register("x", h)
        self.assertIs(mgr.get("x"), h)

    def test_get_unknown_returns_none(self):
        mgr = UndoContextManager()
        self.assertIsNone(mgr.get("missing"))


class TestUndoContextManagerActivation(unittest.TestCase):

    def test_set_active_known_key(self):
        mgr = UndoContextManager()
        h = _mock_history()
        mgr.register("x", h)
        mgr.set_active("x")
        self.assertEqual(mgr.active_key, "x")
        self.assertIs(mgr.active, h)

    def test_set_active_none_deactivates(self):
        mgr = UndoContextManager()
        mgr.register("x", _mock_history(), make_active=True)
        mgr.set_active(None)
        self.assertIsNone(mgr.active_key)

    def test_set_active_unknown_raises_key_error(self):
        mgr = UndoContextManager()
        with self.assertRaises(KeyError):
            mgr.set_active("unknown")


class TestUndoContextManagerUndoRedo(unittest.TestCase):

    def test_undo_routes_to_active_stack(self):
        mgr = UndoContextManager()
        h = _mock_history(can_undo=True)
        mgr.register("doc", h, make_active=True)
        result = mgr.undo()
        self.assertTrue(result)
        h.undo.assert_called_once()

    def test_undo_returns_false_when_no_active(self):
        mgr = UndoContextManager()
        self.assertFalse(mgr.undo())

    def test_undo_returns_false_when_cannot_undo(self):
        mgr = UndoContextManager()
        h = _mock_history(can_undo=False)
        mgr.register("doc", h, make_active=True)
        self.assertFalse(mgr.undo())
        h.undo.assert_not_called()

    def test_redo_routes_to_active_stack(self):
        mgr = UndoContextManager()
        h = _mock_history(can_redo=True)
        mgr.register("doc", h, make_active=True)
        result = mgr.redo()
        self.assertTrue(result)
        h.redo.assert_called_once()

    def test_redo_returns_false_when_no_active(self):
        mgr = UndoContextManager()
        self.assertFalse(mgr.redo())

    def test_redo_returns_false_when_cannot_redo(self):
        mgr = UndoContextManager()
        h = _mock_history(can_redo=False)
        mgr.register("doc", h, make_active=True)
        self.assertFalse(mgr.redo())
        h.redo.assert_not_called()

    def test_can_undo_property(self):
        mgr = UndoContextManager()
        h = _mock_history(can_undo=True)
        mgr.register("d", h, make_active=True)
        self.assertTrue(mgr.can_undo)

    def test_can_undo_false_when_no_active(self):
        mgr = UndoContextManager()
        self.assertFalse(mgr.can_undo)

    def test_can_redo_property(self):
        mgr = UndoContextManager()
        h = _mock_history(can_redo=True)
        mgr.register("d", h, make_active=True)
        self.assertTrue(mgr.can_redo)

    def test_switch_routes_to_new_active(self):
        mgr = UndoContextManager()
        h1 = _mock_history(can_undo=True)
        h2 = _mock_history(can_undo=True)
        mgr.register("doc1", h1, make_active=True)
        mgr.register("doc2", h2)
        mgr.undo()
        h1.undo.assert_called_once()
        h2.undo.assert_not_called()

        mgr.set_active("doc2")
        mgr.undo()
        h2.undo.assert_called_once()


class TestUndoContextManagerObservers(unittest.TestCase):

    def test_subscribe_notified_on_set_active(self):
        mgr = UndoContextManager()
        mgr.register("x", _mock_history())
        received = []
        mgr.subscribe_context_change(received.append)
        mgr.set_active("x")
        self.assertEqual(received, ["x"])

    def test_subscribe_notified_on_none(self):
        mgr = UndoContextManager()
        mgr.register("x", _mock_history(), make_active=True)
        received = []
        mgr.subscribe_context_change(received.append)
        mgr.set_active(None)
        self.assertEqual(received, [None])

    def test_unsubscribe(self):
        mgr = UndoContextManager()
        mgr.register("x", _mock_history())
        received = []
        unsub = mgr.subscribe_context_change(received.append)
        unsub()
        mgr.set_active("x")
        self.assertEqual(received, [])

    def test_subscribe_exception_does_not_propagate(self):
        mgr = UndoContextManager()
        mgr.register("x", _mock_history())

        def bad(key):
            raise RuntimeError("oops")

        mgr.subscribe_context_change(bad)
        mgr.set_active("x")  # Should not raise

    def test_no_notification_if_key_unchanged(self):
        mgr = UndoContextManager()
        mgr.register("x", _mock_history(), make_active=True)
        received = []
        mgr.subscribe_context_change(received.append)
        mgr.set_active("x")  # Same key — no change
        self.assertEqual(received, [])


class TestUndoContextManagerExports(unittest.TestCase):

    def test_importable_from_gui_do(self):
        import gui_do
        self.assertTrue(hasattr(gui_do, "UndoContextManager"))


if __name__ == "__main__":
    unittest.main()
