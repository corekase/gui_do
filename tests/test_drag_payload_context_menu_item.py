"""Tests for pure-data types: DragPayload, ContextMenuItem, ContextMenuHandle."""
import unittest

from gui_do.overlays.drag_drop_manager import DragPayload
from gui_do.overlays.context_menu_manager import ContextMenuItem


# ===========================================================================
# DragPayload
# ===========================================================================


class TestDragPayload(unittest.TestCase):
    def test_drag_id_stored(self):
        payload = DragPayload(drag_id="my-drag")
        self.assertEqual("my-drag", payload.drag_id)

    def test_data_default_none(self):
        payload = DragPayload(drag_id="x")
        self.assertIsNone(payload.data)

    def test_ghost_surface_default_none(self):
        payload = DragPayload(drag_id="x")
        self.assertIsNone(payload.ghost_surface)

    def test_ghost_offset_default(self):
        payload = DragPayload(drag_id="x")
        self.assertEqual((0, 0), payload.ghost_offset)

    def test_data_stored(self):
        payload = DragPayload(drag_id="x", data={"key": "value"})
        self.assertEqual({"key": "value"}, payload.data)

    def test_ghost_offset_stored(self):
        payload = DragPayload(drag_id="x", ghost_offset=(10, 20))
        self.assertEqual((10, 20), payload.ghost_offset)


# ===========================================================================
# ContextMenuItem
# ===========================================================================


class TestContextMenuItem(unittest.TestCase):
    def test_label_stored(self):
        item = ContextMenuItem(label="Cut")
        self.assertEqual("Cut", item.label)

    def test_action_default_none(self):
        item = ContextMenuItem(label="Copy")
        self.assertIsNone(item.action)

    def test_enabled_default_true(self):
        item = ContextMenuItem(label="Paste")
        self.assertTrue(item.enabled)

    def test_separator_default_false(self):
        item = ContextMenuItem(label="")
        self.assertFalse(item.separator)

    def test_icon_default_none(self):
        item = ContextMenuItem(label="Delete")
        self.assertIsNone(item.icon)

    def test_action_stored(self):
        called = []
        action = lambda: called.append(True)
        item = ContextMenuItem(label="Do it", action=action)
        item.action()
        self.assertTrue(called)

    def test_separator_item(self):
        item = ContextMenuItem(label="", separator=True)
        self.assertTrue(item.separator)

    def test_disabled_item(self):
        item = ContextMenuItem(label="Undo", enabled=False)
        self.assertFalse(item.enabled)


if __name__ == "__main__":
    unittest.main()
