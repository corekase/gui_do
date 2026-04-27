"""Tests for DataGridControl — multi-column virtualized table."""
import unittest
from unittest.mock import MagicMock

import pygame
from pygame import Rect

from gui_do.controls.data_grid_control import DataGridControl, GridColumn, GridRow


def _make_grid(**kwargs) -> DataGridControl:
    cols = [
        GridColumn(key="name", title="Name", width=100),
        GridColumn(key="age", title="Age", width=60),
    ]
    rows = [
        GridRow(data={"name": "Alice", "age": 30}),
        GridRow(data={"name": "Bob", "age": 25}),
        GridRow(data={"name": "Carol", "age": 40}),
    ]
    return DataGridControl("grid", Rect(0, 0, 300, 200), cols, rows, **kwargs)


class TestDataGridDefaults(unittest.TestCase):
    def test_row_count(self) -> None:
        g = _make_grid()
        self.assertEqual(g.row_count, 3)

    def test_no_initial_selection(self) -> None:
        g = _make_grid()
        self.assertEqual(g.selected_row_index, -1)
        self.assertIsNone(g.selected_row)

    def test_no_initial_sort(self) -> None:
        g = _make_grid()
        self.assertIsNone(g.sort_column)
        self.assertTrue(g.sort_ascending)


class TestDataGridGridColumnDataclass(unittest.TestCase):
    def test_grid_column_defaults(self) -> None:
        col = GridColumn(key="x", title="X")
        self.assertEqual(col.width, 120)
        self.assertTrue(col.sortable)

    def test_grid_column_custom(self) -> None:
        col = GridColumn(key="y", title="Y", width=80, sortable=False, min_width=30)
        self.assertFalse(col.sortable)
        self.assertEqual(col.min_width, 30)


class TestDataGridGridRowDataclass(unittest.TestCase):
    def test_grid_row_data(self) -> None:
        row = GridRow(data={"col": "val"}, row_id=42)
        self.assertEqual(row.data["col"], "val")
        self.assertEqual(row.row_id, 42)


class TestDataGridMutations(unittest.TestCase):
    def test_append_row(self) -> None:
        g = _make_grid()
        g.append_row(GridRow(data={"name": "Dave", "age": 20}))
        self.assertEqual(g.row_count, 4)

    def test_remove_row(self) -> None:
        g = _make_grid()
        ok = g.remove_row(1)
        self.assertTrue(ok)
        self.assertEqual(g.row_count, 2)

    def test_remove_row_out_of_range(self) -> None:
        g = _make_grid()
        self.assertFalse(g.remove_row(99))

    def test_clear_rows(self) -> None:
        g = _make_grid()
        g.clear_rows()
        self.assertEqual(g.row_count, 0)
        self.assertEqual(g.selected_row_index, -1)

    def test_set_columns(self) -> None:
        g = _make_grid()
        g.set_columns([GridColumn(key="z", title="Z")])
        # No assertion on count but must not raise

    def test_set_rows(self) -> None:
        g = _make_grid()
        g.set_rows([GridRow(data={"name": "Only", "age": 1})])
        self.assertEqual(g.row_count, 1)
        self.assertEqual(g.selected_row_index, -1)


class TestDataGridGeometry(unittest.TestCase):
    def test_pane_rects_do_not_raise(self) -> None:
        g = _make_grid()
        hr = g._header_rect()
        cr = g._content_rect()
        self.assertEqual(hr.y, g.rect.y)
        self.assertEqual(cr.y, g.rect.y + 28)  # HEADER_HEIGHT

    def test_col_x_offsets_length(self) -> None:
        g = _make_grid()
        offsets = g._col_x_offsets()
        self.assertEqual(len(offsets), 3)  # N cols + 1

    def test_col_x_offsets_uses_cache_instance_until_invalidated(self) -> None:
        g = _make_grid()
        first = g._col_x_offsets()
        second = g._col_x_offsets()
        self.assertIs(first, second)

        g.set_columns([
            GridColumn(key="name", title="Name", width=120),
            GridColumn(key="age", title="Age", width=60),
        ])
        third = g._col_x_offsets()
        self.assertIsNot(first, third)

    def test_resize_motion_invalidates_offset_cache(self) -> None:
        g = _make_grid()
        _ = g._col_x_offsets()
        g._resize_col = 0
        g._resize_start_x = 0
        g._resize_start_w = g._columns[0].width

        evt = MagicMock()
        evt.pos = (25, 0)
        g._handle_mouse_motion(evt)

        self.assertTrue(g._col_offsets_dirty)


class TestDataGridEventHandling(unittest.TestCase):
    def _make_event(self, kind, **kwargs):
        from unittest.mock import MagicMock
        evt = MagicMock()
        evt.kind = kind
        evt.phase = None
        for k, v in kwargs.items():
            setattr(evt, k, v)
        return evt

    def _app(self):
        from unittest.mock import MagicMock
        return MagicMock()

    def test_mouse_click_in_content_selects_row(self) -> None:
        from gui_do.core.gui_event import EventType
        g = _make_grid()
        cr = g._content_rect()
        # Click first visible row
        evt = self._make_event(EventType.MOUSE_BUTTON_DOWN, button=1, pos=(cr.x + 10, cr.y + 5))
        consumed = g.handle_event(evt, self._app())
        self.assertTrue(consumed)
        self.assertEqual(g.selected_row_index, 0)

    def test_on_select_callback_fired(self) -> None:
        from gui_do.core.gui_event import EventType
        selected = []
        g = DataGridControl(
            "g", Rect(0, 0, 300, 200),
            [GridColumn(key="x", title="X")],
            [GridRow(data={"x": "A"}), GridRow(data={"x": "B"})],
            on_select=lambda i, r: selected.append((i, r)),
        )
        cr = g._content_rect()
        evt = self._make_event(EventType.MOUSE_BUTTON_DOWN, button=1, pos=(cr.x + 10, cr.y + 5))
        g.handle_event(evt, self._app())
        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0][0], 0)

    def test_keyboard_down_moves_selection(self) -> None:
        from gui_do.core.gui_event import EventType
        g = _make_grid()
        g._selected_row = 0
        g._focused = True
        evt = self._make_event(EventType.KEY_DOWN, key=pygame.K_DOWN)
        consumed = g.handle_event(evt, self._app())
        self.assertTrue(consumed)
        self.assertEqual(g.selected_row_index, 1)

    def test_keyboard_up_moves_selection(self) -> None:
        from gui_do.core.gui_event import EventType
        g = _make_grid()
        g._selected_row = 2
        g._focused = True
        evt = self._make_event(EventType.KEY_DOWN, key=pygame.K_UP)
        g.handle_event(evt, self._app())
        self.assertEqual(g.selected_row_index, 1)

    def test_keyboard_home_goes_to_first(self) -> None:
        from gui_do.core.gui_event import EventType
        g = _make_grid()
        g._selected_row = 2
        g._focused = True
        evt = self._make_event(EventType.KEY_DOWN, key=pygame.K_HOME)
        g.handle_event(evt, self._app())
        self.assertEqual(g.selected_row_index, 0)

    def test_keyboard_end_goes_to_last(self) -> None:
        from gui_do.core.gui_event import EventType
        g = _make_grid()
        g._selected_row = 0
        g._focused = True
        evt = self._make_event(EventType.KEY_DOWN, key=pygame.K_END)
        g.handle_event(evt, self._app())
        self.assertEqual(g.selected_row_index, 2)

    def test_on_sort_callback_fired_on_header_click(self) -> None:
        from gui_do.core.gui_event import EventType
        sorts = []
        g = DataGridControl(
            "g", Rect(0, 0, 300, 200),
            [GridColumn(key="name", title="Name", width=150, sortable=True)],
            [],
            on_sort=lambda col, asc: sorts.append((col, asc)),
        )
        hr = g._header_rect()
        evt = self._make_event(EventType.MOUSE_BUTTON_DOWN, button=1, pos=(hr.x + 10, hr.y + 5))
        g.handle_event(evt, MagicMock())
        self.assertEqual(len(sorts), 1)
        self.assertEqual(sorts[0][0], "name")
        self.assertTrue(sorts[0][1])  # ascending first click

    def test_sort_toggle_on_second_header_click(self) -> None:
        from gui_do.core.gui_event import EventType
        from unittest.mock import MagicMock
        sorts = []
        g = DataGridControl(
            "g", Rect(0, 0, 300, 200),
            [GridColumn(key="name", title="Name", width=150, sortable=True)],
            [],
            on_sort=lambda col, asc: sorts.append(asc),
        )
        hr = g._header_rect()
        pos = (hr.x + 10, hr.y + 5)
        for _ in range(2):
            evt = self._make_event(EventType.MOUSE_BUTTON_DOWN, button=1, pos=pos)
            g.handle_event(evt, MagicMock())
        self.assertFalse(sorts[-1])  # second click → descending


class TestDataGridDisabled(unittest.TestCase):
    def test_disabled_grid_ignores_events(self) -> None:
        from gui_do.core.gui_event import EventType
        from unittest.mock import MagicMock
        g = _make_grid()
        g.enabled = False
        evt = MagicMock()
        evt.kind = EventType.MOUSE_BUTTON_DOWN
        evt.button = 1
        evt.pos = (10, 50)
        consumed = g.handle_event(evt, MagicMock())
        self.assertFalse(consumed)


class TestDataGridAcceptsFocus(unittest.TestCase):
    def test_accepts_focus_when_enabled_and_visible(self) -> None:
        g = _make_grid()
        self.assertTrue(g.accepts_focus())

    def test_not_accepts_focus_when_disabled(self) -> None:
        g = _make_grid()
        g.enabled = False
        self.assertFalse(g.accepts_focus())


if __name__ == "__main__":
    unittest.main()
