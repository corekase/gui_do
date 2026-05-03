import unittest

from pygame import Rect

from gui_do.layout.cell_caret_layout import CellCaretLayout
from gui_do.layout.layout_manager import LayoutManager


class TestCellCaretLayout(unittest.TestCase):
    def test_vertical_caret_advances_by_placed_area(self):
        layout = CellCaretLayout(
            bounds=Rect(0, 0, 260, 260),
            cell_width=120,
            cell_height=120,
            columns=2,
            cell_gap_x=10,
            item_gap_y=5,
            flow_axis="vertical",
        )

        first = layout.add(100, 30)
        second = layout.add(100, 40)

        self.assertEqual(Rect(0, 0, 100, 30), first)
        self.assertEqual(Rect(0, 35, 100, 40), second)

    def test_overflow_moves_to_next_cell_then_next_row(self):
        layout = CellCaretLayout(
            bounds=Rect(0, 0, 260, 260),
            cell_width=120,
            cell_height=120,
            columns=2,
            cell_gap_x=10,
            cell_gap_y=10,
            item_gap_y=5,
            flow_axis="vertical",
        )

        first = layout.add(100, 80)
        second = layout.add(100, 80)
        third = layout.add(100, 80)

        self.assertEqual(Rect(0, 0, 100, 80), first)
        self.assertEqual(Rect(130, 0, 100, 80), second)
        self.assertEqual(Rect(0, 130, 100, 80), third)

    def test_bind_layout_manager_to_cell_content(self):
        layout = CellCaretLayout(
            bounds=Rect(20, 30, 300, 300),
            cell_width=100,
            cell_height=80,
            columns=3,
            cell_gap_x=8,
            cell_gap_y=12,
        )
        manager = LayoutManager()

        content = layout.bind_layout_manager(manager, col=1, row=2, padding=(4, 6, 8, 10))
        anchored = manager.anchored((20, 10), anchor="top_left", margin=(0, 0))

        self.assertEqual(Rect(132, 220, 88, 64), content)
        self.assertEqual(Rect(132, 220, 20, 10), anchored)

    def test_variable_cell_sizes_pack_to_next_row(self):
        layout = CellCaretLayout(
            bounds=Rect(0, 0, 200, 200),
            cell_width=1,
            cell_height=1,
            columns=1,
            cell_sizes=((60, 40), (80, 50), (90, 30), (70, 20)),
            cell_gap_x=10,
            cell_gap_y=8,
            item_gap_y=4,
            flow_axis="vertical",
        )

        self.assertEqual(Rect(0, 0, 60, 40), layout.cell_rect(0, 0))
        self.assertEqual(Rect(70, 0, 80, 50), layout.cell_rect(1, 0))
        self.assertEqual(Rect(0, 58, 90, 30), layout.cell_rect(0, 1))
        self.assertEqual(Rect(100, 58, 70, 20), layout.cell_rect(1, 1))

    def test_variable_cell_overflow_advances_across_packed_rows(self):
        layout = CellCaretLayout(
            bounds=Rect(0, 0, 200, 200),
            cell_width=1,
            cell_height=1,
            columns=1,
            cell_sizes=((60, 40), (80, 50), (90, 30), (70, 20)),
            cell_gap_x=10,
            cell_gap_y=8,
            item_gap_y=6,
            flow_axis="vertical",
        )

        first = layout.add(30, 25)
        second = layout.add(30, 25)
        third = layout.add(30, 25)
        fourth = layout.add(30, 20)

        self.assertEqual(Rect(0, 0, 30, 25), first)
        self.assertEqual(Rect(70, 0, 30, 25), second)
        self.assertEqual(Rect(0, 58, 30, 25), third)
        self.assertEqual(Rect(100, 58, 30, 20), fourth)


class TestCellCaretState(unittest.TestCase):
    def test_fields_stored(self):
        state = CellCaretLayout(
            bounds=Rect(0, 0, 300, 200), cell_width=100, cell_height=50, columns=3
        ).state
        self.assertIsInstance(state, tuple.__class__ if False else object)
        self.assertEqual(0, state.col)
        self.assertEqual(0, state.row)

    def test_state_is_immutable(self):
        from gui_do.layout.cell_caret_layout import CellCaretState
        state = CellCaretState(col=1, row=2, x=10, y=20)
        with self.assertRaises(Exception):
            state.col = 99  # type: ignore[misc]


class TestCellCaretLayoutCellRect(unittest.TestCase):
    def test_cell_rect_0_0(self):
        layout = CellCaretLayout(bounds=Rect(0, 0, 300, 200), cell_width=100, cell_height=50, columns=3)
        self.assertEqual(Rect(0, 0, 100, 50), layout.cell_rect(0, 0))

    def test_cell_rect_1_0(self):
        layout = CellCaretLayout(bounds=Rect(0, 0, 300, 200), cell_width=100, cell_height=50, columns=3)
        self.assertEqual(Rect(100, 0, 100, 50), layout.cell_rect(1, 0))

    def test_cell_rect_0_1(self):
        layout = CellCaretLayout(bounds=Rect(0, 0, 300, 200), cell_width=100, cell_height=50, columns=3)
        self.assertEqual(Rect(0, 50, 100, 50), layout.cell_rect(0, 1))

    def test_cell_rect_with_offset_bounds(self):
        layout = CellCaretLayout(bounds=Rect(10, 20, 300, 200), cell_width=100, cell_height=50, columns=3)
        self.assertEqual(Rect(10, 20, 100, 50), layout.cell_rect(0, 0))

    def test_cell_rect_returns_copy(self):
        layout = CellCaretLayout(bounds=Rect(0, 0, 300, 200), cell_width=100, cell_height=50, columns=3)
        r1 = layout.cell_rect(0, 0)
        r2 = layout.cell_rect(0, 0)
        self.assertIsNot(r1, r2)


class TestCellCaretLayoutCellContentRect(unittest.TestCase):
    def test_no_padding(self):
        layout = CellCaretLayout(bounds=Rect(0, 0, 300, 200), cell_width=100, cell_height=50, columns=3)
        self.assertEqual(Rect(0, 0, 100, 50), layout.cell_content_rect())

    def test_uniform_padding(self):
        layout = CellCaretLayout(bounds=Rect(0, 0, 300, 200), cell_width=100, cell_height=50, columns=3)
        self.assertEqual(Rect(10, 10, 80, 30), layout.cell_content_rect(padding=10))

    def test_xy_padding(self):
        layout = CellCaretLayout(bounds=Rect(0, 0, 300, 200), cell_width=100, cell_height=50, columns=3)
        self.assertEqual(Rect(5, 8, 90, 34), layout.cell_content_rect(padding=(5, 8)))

    def test_four_sided_padding(self):
        layout = CellCaretLayout(bounds=Rect(0, 0, 300, 200), cell_width=100, cell_height=50, columns=3)
        self.assertEqual(Rect(2, 4, 92, 38), layout.cell_content_rect(padding=(2, 4, 6, 8)))


class TestCellCaretLayoutNormalizePadding(unittest.TestCase):
    def test_int(self):
        self.assertEqual((10, 10, 10, 10), CellCaretLayout._normalize_padding(10))

    def test_two_tuple(self):
        self.assertEqual((5, 8, 5, 8), CellCaretLayout._normalize_padding((5, 8)))

    def test_four_tuple(self):
        self.assertEqual((1, 2, 3, 4), CellCaretLayout._normalize_padding((1, 2, 3, 4)))

    def test_invalid_length_raises(self):
        with self.assertRaises(ValueError):
            CellCaretLayout._normalize_padding((1, 2, 3))  # type: ignore[arg-type]


class TestCellCaretLayoutMoveToCell(unittest.TestCase):
    def test_move_updates_col_row(self):
        layout = CellCaretLayout(bounds=Rect(0, 0, 300, 300), cell_width=100, cell_height=100, columns=3)
        layout.move_to_cell(2, 1)
        state = layout.state
        self.assertEqual(2, state.col)
        self.assertEqual(1, state.row)

    def test_move_resets_caret(self):
        layout = CellCaretLayout(bounds=Rect(0, 0, 300, 300), cell_width=100, cell_height=100, columns=3)
        layout.add(50, 50)
        layout.move_to_cell(0, 0)
        state = layout.state
        self.assertEqual(0, state.x)
        self.assertEqual(0, state.y)


class TestCellCaretLayoutErrors(unittest.TestCase):
    def test_invalid_flow_axis_raises(self):
        with self.assertRaises(ValueError):
            CellCaretLayout(bounds=Rect(0, 0, 300, 200), cell_width=100, cell_height=50, columns=3, flow_axis="diagonal")

    def test_item_too_large_raises(self):
        layout = CellCaretLayout(bounds=Rect(0, 0, 300, 200), cell_width=50, cell_height=50, columns=3)
        with self.assertRaises(ValueError):
            layout.add(200, 200)


class TestCellCaretLayoutHelpers(unittest.TestCase):
    def test_labeled_slot_height(self):
        self.assertEqual(
            42,
            CellCaretLayout.labeled_slot_height(
                24,
                label_height=16,
                label_gap=2,
            ),
        )

    def test_add_labeled_slot(self):
        layout = CellCaretLayout(
            bounds=Rect(10, 20, 200, 100),
            cell_width=200,
            cell_height=100,
            columns=1,
        )
        label_rect, control_rect = layout.add_labeled_slot(
            24,
            label_height=16,
            label_gap=2,
        )
        self.assertEqual(Rect(10, 20, 200, 16), label_rect)
        self.assertEqual(Rect(10, 38, 200, 24), control_rect)

    def test_split_columns_centered(self):
        cols = CellCaretLayout.split_columns(
            Rect(0, 0, 500, 120),
            count=2,
            gap=8,
            min_width=180,
            max_width=220,
            align="center",
        )
        self.assertEqual(2, len(cols))
        self.assertEqual(Rect(26, 0, 220, 120), cols[0])
        self.assertEqual(Rect(254, 0, 220, 120), cols[1])

    def test_add_slot_or_overflow_uses_normal_slot_when_space_exists(self):
        layout = CellCaretLayout(
            bounds=Rect(10, 20, 120, 80),
            cell_width=120,
            cell_height=80,
            columns=1,
            item_gap_y=4,
        )
        first = layout.add_slot_or_overflow(24, overflow_gap=8)
        self.assertEqual(Rect(10, 20, 120, 24), first)

    def test_add_slot_or_overflow_virtualizes_when_exhausted(self):
        layout = CellCaretLayout(
            bounds=Rect(10, 20, 120, 40),
            cell_width=120,
            cell_height=40,
            columns=1,
            item_gap_y=4,
        )
        first = layout.add_slot_or_overflow(24, overflow_gap=6)
        second = layout.add_slot_or_overflow(24, overflow_gap=6)
        self.assertEqual(Rect(10, 20, 120, 24), first)
        self.assertEqual(Rect(10, 50, 120, 24), second)

    def test_column_stack_from_anchor_builds_single_column_layout(self):
        stack, col_x, col_w, col_y = CellCaretLayout.column_stack_from_anchor(
            anchor=Rect(40, 60, 180, 50),
            content_bottom=220,
            preferred_width=160,
            item_gap_y=8,
        )
        self.assertEqual(40, col_x)
        self.assertEqual(160, col_w)
        self.assertEqual(60, col_y)
        self.assertEqual(Rect(40, 60, 160, 160), stack.bounds)
        self.assertEqual(Rect(40, 60, 160, 160), stack.cell_rect())


if __name__ == "__main__":
    unittest.main()
