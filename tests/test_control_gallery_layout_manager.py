import unittest
from unittest.mock import MagicMock, patch

from pygame import Rect

from demo_features.showcase.showcase_feature import (
    _build_grid_specs,
    category_for_row,
)


class TestBuildGridSpecs(unittest.TestCase):
    """Tests for the _build_grid_specs grid layout helper."""

    def _make_def(self, name, row_index, control_height=30):
        from gui_do import ControlDefinition
        ctrl = MagicMock()
        ctrl.rect = Rect(0, 0, 1, 1)
        return ControlDefinition(
            name,
            name.replace("_", " ").title(),
            control_height,
            row_index,
            lambda c=ctrl: c,
            focusable=True,
        )

    def _slot_h(self, h):
        return h + 22

    def _build(self, defs, num_cols=3, bounds=None, content_bottom=None):
        b = bounds or Rect(0, 0, 600, 500)
        cb = content_bottom or b.bottom
        with patch(
            "demo_features.showcase.showcase_feature.build_specs_from_column_section",
        ) as mock_build, patch(
            "demo_features.showcase.showcase_feature.CellCaretLayout.split_columns",
        ) as mock_split, patch(
            "demo_features.showcase.showcase_feature.CellCaretLayout.column_stack_from_anchor",
        ) as mock_stack:
            col_rects = [Rect(i * 200, 0, 200, 500) for i in range(num_cols)]
            mock_split.return_value = col_rects
            mock_stack.return_value = (MagicMock(), None, None, None)
            # Return one spec per definition per column call
            call_count = [0]
            def _fake_build(col_d, stack, slot_height_for, overflow_gap):
                specs = []
                for d in col_d:
                    s = MagicMock()
                    s.row_index = d.row_index
                    s.name = d.name
                    specs.append(s)
                return tuple(specs), 100
            mock_build.side_effect = _fake_build

            return _build_grid_specs(
                defs,
                bounds=b,
                num_cols=num_cols,
                content_bottom=cb,
                row_gap=4,
                slot_height_for=self._slot_h,
            )

    def test_empty_definitions_returns_empty(self):
        result, bottom = self._build([], num_cols=3)
        self.assertEqual((), result)

    def test_zero_cols_returns_empty(self):
        defs = [self._make_def("button", 0)]
        result, bottom = _build_grid_specs(
            defs,
            bounds=Rect(0, 0, 300, 200),
            num_cols=0,
            content_bottom=200,
            row_gap=4,
            slot_height_for=self._slot_h,
        )
        self.assertEqual((), result)

    def test_single_col_order_preserved(self):
        defs = [
            self._make_def("a", 0),
            self._make_def("b", 1),
            self._make_def("c", 2),
        ]
        result, _ = self._build(defs, num_cols=1)
        names = [s.name for s in result]
        self.assertEqual(["a", "b", "c"], names)

    def test_reading_order_interleaving_three_columns(self):
        """With 3 columns, items should be interleaved: col0[0], col1[0], col2[0], col0[1], ..."""
        defs = [
            self._make_def("a", 0),   # → col 0
            self._make_def("b", 1),   # → col 1
            self._make_def("c", 2),   # → col 2
            self._make_def("d", 3),   # → col 0
            self._make_def("e", 4),   # → col 1
            self._make_def("f", 5),   # → col 2
        ]
        result, _ = self._build(defs, num_cols=3)
        names = [s.name for s in result]
        # Reading order: a, b, c, d, e, f
        self.assertEqual(["a", "b", "c", "d", "e", "f"], names)

    def test_uneven_column_distribution(self):
        """With 4 items and 3 columns: col0=[a,d], col1=[b], col2=[c]. Reading order: a,b,c,d."""
        defs = [
            self._make_def("a", 0),
            self._make_def("b", 1),
            self._make_def("c", 2),
            self._make_def("d", 3),
        ]
        result, _ = self._build(defs, num_cols=3)
        names = [s.name for s in result]
        self.assertEqual(["a", "b", "c", "d"], names)

    def test_correct_column_count(self):
        """Result count equals number of definitions."""
        defs = [self._make_def(f"ctrl_{i}", i) for i in range(9)]
        result, _ = self._build(defs, num_cols=3)
        self.assertEqual(9, len(result))


if __name__ == "__main__":
    unittest.main()
