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


if __name__ == "__main__":
    unittest.main()
