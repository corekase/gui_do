"""Tests for DataGridControl and TextInputControl."""
import unittest

import pygame
from pygame import Rect

from gui_do.controls.data.data_grid_control import (
    DataGridControl, GridColumn, GridRow
)
from gui_do.controls.input.text_input_control import TextInputControl
from gui_do.events.gui_event import EventType, GuiEvent

pygame.init()


# ===========================================================================
# GridColumn / GridRow dataclasses
# ===========================================================================


class TestGridColumn(unittest.TestCase):
    def test_key_and_title_stored(self):
        col = GridColumn(key="name", title="Name")
        self.assertEqual("name", col.key)
        self.assertEqual("Name", col.title)

    def test_default_width(self):
        col = GridColumn(key="x", title="X")
        self.assertEqual(120, col.width)

    def test_sortable_default_true(self):
        col = GridColumn(key="x", title="X")
        self.assertTrue(col.sortable)

    def test_custom_width_and_min_width(self):
        col = GridColumn(key="x", title="X", width=200, min_width=40)
        self.assertEqual(200, col.width)
        self.assertEqual(40, col.min_width)


class TestGridRow(unittest.TestCase):
    def test_data_stored(self):
        row = GridRow(data={"name": "Alice"})
        self.assertEqual("Alice", row.data["name"])

    def test_row_id_default_none(self):
        row = GridRow(data={})
        self.assertIsNone(row.row_id)

    def test_row_id_stored(self):
        row = GridRow(data={}, row_id=42)
        self.assertEqual(42, row.row_id)


# ===========================================================================
# DataGridControl — initial state
# ===========================================================================


class TestDataGridControlInitial(unittest.TestCase):
    def _make(self, cols=None, rows=None):
        cols = cols or [GridColumn("name", "Name"), GridColumn("age", "Age")]
        rows = rows or [GridRow({"name": "Alice", "age": 30}),
                        GridRow({"name": "Bob",   "age": 25})]
        return DataGridControl("dg", Rect(0, 0, 500, 300), columns=cols, rows=rows)

    def test_row_count(self):
        dg = self._make()
        self.assertEqual(2, dg.row_count)

    def test_empty_rows_zero(self):
        dg = DataGridControl("dg", Rect(0, 0, 500, 300))
        self.assertEqual(0, dg.row_count)

    def test_selected_row_index_minus_one(self):
        dg = self._make()
        self.assertEqual(-1, dg.selected_row_index)

    def test_selected_row_none_initially(self):
        dg = self._make()
        self.assertIsNone(dg.selected_row)

    def test_sort_col_none(self):
        dg = self._make()
        self.assertIsNone(dg.sort_column)

    def test_sort_ascending_default_true(self):
        dg = self._make()
        self.assertTrue(dg.sort_ascending)

    def test_tab_index_zero(self):
        dg = self._make()
        self.assertEqual(0, dg.tab_index)

    def test_rows_returns_copy(self):
        dg = self._make()
        copy = dg.rows
        copy.clear()
        self.assertEqual(2, dg.row_count)


class TestDataGridControlSetRows(unittest.TestCase):
    def test_set_rows_replaces(self):
        dg = DataGridControl("dg", Rect(0, 0, 500, 300))
        dg.set_rows([GridRow({"a": 1}), GridRow({"a": 2})])
        self.assertEqual(2, dg.row_count)

    def test_set_rows_resets_selection(self):
        dg = DataGridControl("dg", Rect(0, 0, 500, 300),
                             rows=[GridRow({"a": 1})])
        dg._selected_row = 0
        dg.set_rows([GridRow({"a": 2})])
        self.assertEqual(-1, dg.selected_row_index)

    def test_append_row(self):
        dg = DataGridControl("dg", Rect(0, 0, 500, 300))
        dg.append_row(GridRow({"x": 1}))
        self.assertEqual(1, dg.row_count)

    def test_remove_row_returns_true(self):
        dg = DataGridControl("dg", Rect(0, 0, 500, 300),
                             rows=[GridRow({"a": 1}), GridRow({"a": 2})])
        self.assertTrue(dg.remove_row(0))

    def test_remove_row_out_of_range_returns_false(self):
        dg = DataGridControl("dg", Rect(0, 0, 500, 300))
        self.assertFalse(dg.remove_row(0))

    def test_remove_row_decrements(self):
        dg = DataGridControl("dg", Rect(0, 0, 500, 300),
                             rows=[GridRow({"a": 1}), GridRow({"a": 2})])
        dg.remove_row(0)
        self.assertEqual(1, dg.row_count)

    def test_clear_rows(self):
        dg = DataGridControl("dg", Rect(0, 0, 500, 300),
                             rows=[GridRow({"a": 1})])
        dg.clear_rows()
        self.assertEqual(0, dg.row_count)

    def test_clear_rows_resets_selection(self):
        dg = DataGridControl("dg", Rect(0, 0, 500, 300),
                             rows=[GridRow({"a": 1})])
        dg._selected_row = 0
        dg.clear_rows()
        self.assertEqual(-1, dg.selected_row_index)


class TestDataGridControlSetColumns(unittest.TestCase):
    def test_set_columns_replaces(self):
        dg = DataGridControl("dg", Rect(0, 0, 500, 300),
                             columns=[GridColumn("a", "A")])
        dg.set_columns([GridColumn("b", "B"), GridColumn("c", "C")])
        self.assertEqual(2, len(dg._columns))

    def test_set_columns_marks_offsets_dirty(self):
        dg = DataGridControl("dg", Rect(0, 0, 500, 300))
        dg._col_offsets_dirty = False
        dg.set_columns([GridColumn("a", "A")])
        self.assertTrue(dg._col_offsets_dirty)


class TestDataGridControlGeometry(unittest.TestCase):
    def test_header_rect_y_at_top(self):
        dg = DataGridControl("dg", Rect(10, 20, 500, 300))
        hdr = dg._header_rect()
        self.assertEqual(20, hdr.y)

    def test_content_rect_below_header(self):
        from gui_do.controls.data.data_grid_control import _HEADER_HEIGHT
        dg = DataGridControl("dg", Rect(0, 0, 500, 300))
        cr = dg._content_rect()
        self.assertEqual(_HEADER_HEIGHT, cr.y)

    def test_col_offsets_monotone_increasing(self):
        dg = DataGridControl("dg", Rect(0, 0, 500, 300), columns=[
            GridColumn("a", "A", width=100),
            GridColumn("b", "B", width=150),
        ])
        offsets = dg._col_x_offsets()
        self.assertEqual(3, len(offsets))
        self.assertEqual(0, offsets[0])
        self.assertEqual(100, offsets[1])
        self.assertEqual(250, offsets[2])


# ===========================================================================
# TextInputControl
# ===========================================================================


class TestTextInputControlInitial(unittest.TestCase):
    def test_value_stored(self):
        ti = TextInputControl("ti", Rect(0, 0, 300, 30), value="hello")
        self.assertEqual("hello", ti.value)

    def test_empty_value_by_default(self):
        ti = TextInputControl("ti", Rect(0, 0, 300, 30))
        self.assertEqual("", ti.value)

    def test_placeholder_stored(self):
        ti = TextInputControl("ti", Rect(0, 0, 300, 30), placeholder="Type here")
        self.assertEqual("Type here", ti._placeholder)

    def test_masked_false_by_default(self):
        ti = TextInputControl("ti", Rect(0, 0, 300, 30))
        self.assertFalse(ti._masked)

    def test_masked_true_stored(self):
        ti = TextInputControl("ti", Rect(0, 0, 300, 30), masked=True)
        self.assertTrue(ti._masked)

    def test_max_length_none_by_default(self):
        ti = TextInputControl("ti", Rect(0, 0, 300, 30))
        self.assertIsNone(ti._max_length)

    def test_tab_index_zero(self):
        ti = TextInputControl("ti", Rect(0, 0, 300, 30))
        self.assertEqual(0, ti.tab_index)

    def test_cursor_at_end_of_value(self):
        ti = TextInputControl("ti", Rect(0, 0, 300, 30), value="abc")
        self.assertEqual(3, ti._cursor_pos)

    def test_accepts_focus(self):
        ti = TextInputControl("ti", Rect(0, 0, 300, 30))
        self.assertTrue(ti.accepts_focus())

    def test_accepts_mouse_focus(self):
        ti = TextInputControl("ti", Rect(0, 0, 300, 30))
        self.assertTrue(ti.accepts_mouse_focus())


class TestTextInputControlSetValue(unittest.TestCase):
    def test_set_value(self):
        ti = TextInputControl("ti", Rect(0, 0, 300, 30))
        ti.set_value("world")
        self.assertEqual("world", ti.value)

    def test_set_value_no_callback(self):
        received = []
        ti = TextInputControl("ti", Rect(0, 0, 300, 30),
                              on_change=lambda v: received.append(v))
        ti.set_value("test")
        self.assertEqual([], received)

    def test_set_value_moves_cursor_to_end(self):
        ti = TextInputControl("ti", Rect(0, 0, 300, 30))
        ti.set_value("abcde")
        self.assertEqual(5, ti._cursor_pos)

    def test_set_value_respects_max_length(self):
        ti = TextInputControl("ti", Rect(0, 0, 300, 30), max_length=3)
        ti.set_value("hello")
        self.assertEqual("hel", ti.value)

    def test_value_setter(self):
        ti = TextInputControl("ti", Rect(0, 0, 300, 30))
        ti.value = "via setter"
        self.assertEqual("via setter", ti.value)

    def test_clear_selection(self):
        ti = TextInputControl("ti", Rect(0, 0, 300, 30), value="abc")
        ti.select_all()
        ti.clear_selection()
        self.assertIsNone(ti._sel_anchor)
        self.assertIsNone(ti._sel_active)


class TestTextInputControlMasked(unittest.TestCase):
    def test_get_display_value_masked(self):
        ti = TextInputControl("ti", Rect(0, 0, 300, 30), value="secret", masked=True)
        self.assertEqual("******", ti._get_display_value())

    def test_get_display_value_unmasked(self):
        ti = TextInputControl("ti", Rect(0, 0, 300, 30), value="hello")
        self.assertEqual("hello", ti._get_display_value())


class TestTextInputControlSelectAll(unittest.TestCase):
    def test_select_all_sets_anchors(self):
        ti = TextInputControl("ti", Rect(0, 0, 300, 30), value="abc")
        ti.select_all()
        self.assertEqual(0, ti._sel_anchor)
        self.assertEqual(3, ti._sel_active)


class TestTextInputControlFocusedKeyConsumption(unittest.TestCase):
    @staticmethod
    def _key_event(key: int, mod: int = 0) -> GuiEvent:
        return GuiEvent(kind=EventType.KEY_DOWN, type=pygame.KEYDOWN, key=key, mod=mod)

    def test_non_traversal_key_consumed_when_focused(self):
        ti = TextInputControl("ti", Rect(0, 0, 300, 30), value="abc")
        ti._focused = True

        consumed = ti.handle_event(self._key_event(pygame.K_SPACE), app=None)

        self.assertTrue(consumed)

    def test_tab_traversal_keys_not_consumed_when_focused(self):
        ti = TextInputControl("ti", Rect(0, 0, 300, 30), value="abc")
        ti._focused = True

        traversal_mods = (
            0,
            pygame.KMOD_SHIFT,
            pygame.KMOD_CTRL,
            pygame.KMOD_CTRL | pygame.KMOD_SHIFT,
        )
        for mod in traversal_mods:
            with self.subTest(mod=mod):
                consumed = ti.handle_event(self._key_event(pygame.K_TAB, mod=mod), app=None)
                self.assertFalse(consumed)

    def test_home_moves_to_start_of_current_logical_line(self):
        ti = TextInputControl("ti", Rect(0, 0, 300, 30), value="ab\ncd")
        ti._focused = True
        ti._cursor_pos = 4

        consumed = ti.handle_event(self._key_event(pygame.K_HOME), app=None)

        self.assertTrue(consumed)
        self.assertEqual(3, ti._cursor_pos)

    def test_end_moves_to_end_of_current_logical_line(self):
        ti = TextInputControl("ti", Rect(0, 0, 300, 30), value="ab\ncd")
        ti._focused = True
        ti._cursor_pos = 1

        consumed = ti.handle_event(self._key_event(pygame.K_END), app=None)

        self.assertTrue(consumed)
        self.assertEqual(2, ti._cursor_pos)


if __name__ == "__main__":
    unittest.main()
