"""Tests for DropdownControl, RangeSliderControl, and ListViewControl."""
import unittest

import pygame
from pygame import Rect

from gui_do.controls.input.dropdown_control import DropdownControl, DropdownOption
from gui_do.controls.input.range_slider_control import RangeSliderControl
from gui_do.controls.data.list_view_control import ListViewControl, ListItem

pygame.init()


# ===========================================================================
# DropdownOption
# ===========================================================================


class TestDropdownOption(unittest.TestCase):
    def test_value_defaults_to_label(self):
        opt = DropdownOption(label="Alpha")
        self.assertEqual("Alpha", opt.value)

    def test_value_explicit(self):
        opt = DropdownOption(label="Alpha", value=42)
        self.assertEqual(42, opt.value)

    def test_enabled_default_true(self):
        opt = DropdownOption(label="X")
        self.assertTrue(opt.enabled)

    def test_data_default_none(self):
        opt = DropdownOption(label="X")
        self.assertIsNone(opt.data)


# ===========================================================================
# DropdownControl — initial state
# ===========================================================================


class TestDropdownControlInitial(unittest.TestCase):
    def test_empty_options_selected_index_minus_one(self):
        dd = DropdownControl("dd", Rect(0, 0, 200, 30))
        self.assertEqual(-1, dd.selected_index)

    def test_with_options_auto_selects_first(self):
        dd = DropdownControl("dd", Rect(0, 0, 200, 30), options=[
            DropdownOption("A"),
            DropdownOption("B"),
        ])
        self.assertEqual(0, dd.selected_index)

    def test_initial_selected_index_set(self):
        dd = DropdownControl("dd", Rect(0, 0, 200, 30), options=[
            DropdownOption("A"),
            DropdownOption("B"),
        ], selected_index=1)
        self.assertEqual(1, dd.selected_index)

    def test_initial_selected_index_out_of_range_defaults_to_first(self):
        dd = DropdownControl("dd", Rect(0, 0, 200, 30), options=[
            DropdownOption("A"),
        ], selected_index=99)
        self.assertEqual(0, dd.selected_index)

    def test_is_open_false_initially(self):
        dd = DropdownControl("dd", Rect(0, 0, 200, 30))
        self.assertFalse(dd.is_open)

    def test_tab_index_zero(self):
        dd = DropdownControl("dd", Rect(0, 0, 200, 30))
        self.assertEqual(0, dd.tab_index)

    def test_placeholder_stored(self):
        dd = DropdownControl("dd", Rect(0, 0, 200, 30), placeholder="Choose…")
        self.assertEqual("Choose…", dd._placeholder)


class TestDropdownControlSelectedOption(unittest.TestCase):
    def test_selected_option_none_when_empty(self):
        dd = DropdownControl("dd", Rect(0, 0, 200, 30))
        self.assertIsNone(dd.selected_option)

    def test_selected_option_returns_item(self):
        opts = [DropdownOption("A"), DropdownOption("B")]
        dd = DropdownControl("dd", Rect(0, 0, 200, 30), options=opts, selected_index=1)
        self.assertIs(opts[1], dd.selected_option)

    def test_selected_index_setter_in_range(self):
        dd = DropdownControl("dd", Rect(0, 0, 200, 30), options=[
            DropdownOption("A"), DropdownOption("B"),
        ])
        dd.selected_index = 1
        self.assertEqual(1, dd.selected_index)

    def test_selected_index_setter_out_of_range_falls_back_to_first(self):
        dd = DropdownControl("dd", Rect(0, 0, 200, 30), options=[
            DropdownOption("A"), DropdownOption("B"),
        ])
        dd.selected_index = 99
        # _ensure_selection_invariant: out of range → -1, then auto→0
        self.assertEqual(0, dd.selected_index)


class TestDropdownControlSetOptions(unittest.TestCase):
    def test_set_options_replaces(self):
        dd = DropdownControl("dd", Rect(0, 0, 200, 30), options=[DropdownOption("Old")])
        dd.set_options([DropdownOption("New1"), DropdownOption("New2")])
        self.assertEqual(2, len(dd._options))

    def test_set_options_resets_selection_to_first(self):
        dd = DropdownControl("dd", Rect(0, 0, 200, 30), options=[DropdownOption("X")])
        dd.selected_index = 0
        dd.set_options([DropdownOption("A"), DropdownOption("B")])
        self.assertEqual(0, dd.selected_index)

    def test_set_options_empty_clears_selection(self):
        dd = DropdownControl("dd", Rect(0, 0, 200, 30), options=[DropdownOption("X")])
        dd.set_options([])
        self.assertEqual(-1, dd.selected_index)


class TestDropdownControlAcceptsFocus(unittest.TestCase):
    def test_accepts_focus_when_visible_enabled(self):
        dd = DropdownControl("dd", Rect(0, 0, 200, 30))
        dd.visible = True
        dd.enabled = True
        self.assertTrue(dd.accepts_focus())

    def test_accepts_focus_false_when_disabled(self):
        dd = DropdownControl("dd", Rect(0, 0, 200, 30))
        dd.enabled = False
        self.assertFalse(dd.accepts_focus())


# ===========================================================================
# RangeSliderControl
# ===========================================================================


class TestRangeSliderControlInitial(unittest.TestCase):
    def test_default_low_equals_min(self):
        rs = RangeSliderControl("rs", Rect(0, 0, 300, 28), min_value=0, max_value=100)
        self.assertAlmostEqual(0.0, rs.low_value)

    def test_default_high_equals_max(self):
        rs = RangeSliderControl("rs", Rect(0, 0, 300, 28), min_value=0, max_value=100)
        self.assertAlmostEqual(100.0, rs.high_value)

    def test_initial_low_high_stored(self):
        rs = RangeSliderControl("rs", Rect(0, 0, 300, 28),
                                min_value=0, max_value=100,
                                low_value=20, high_value=80)
        self.assertAlmostEqual(20.0, rs.low_value)
        self.assertAlmostEqual(80.0, rs.high_value)

    def test_min_max_degenerate_max_bumped(self):
        rs = RangeSliderControl("rs", Rect(0, 0, 300, 28), min_value=50, max_value=50)
        self.assertGreater(rs._max, rs._min)

    def test_tab_index_zero(self):
        rs = RangeSliderControl("rs", Rect(0, 0, 300, 28))
        self.assertEqual(0, rs.tab_index)

    def test_accepts_focus(self):
        rs = RangeSliderControl("rs", Rect(0, 0, 300, 28))
        rs.visible = True
        rs.enabled = True
        self.assertTrue(rs.accepts_focus())


class TestRangeSliderControlSetValues(unittest.TestCase):
    def test_set_values(self):
        rs = RangeSliderControl("rs", Rect(0, 0, 300, 28), min_value=0, max_value=100)
        rs.set_values(10, 90)
        self.assertAlmostEqual(10.0, rs.low_value)
        self.assertAlmostEqual(90.0, rs.high_value)

    def test_set_values_clamped_to_range(self):
        rs = RangeSliderControl("rs", Rect(0, 0, 300, 28), min_value=0, max_value=100)
        rs.set_values(-50, 200)
        self.assertAlmostEqual(0.0, rs.low_value)
        self.assertAlmostEqual(100.0, rs.high_value)

    def test_set_values_inverted_gets_swapped(self):
        rs = RangeSliderControl("rs", Rect(0, 0, 300, 28), min_value=0, max_value=100)
        rs.set_values(80, 20)
        # _clamp_values swaps if low > high
        self.assertLessEqual(rs.low_value, rs.high_value)

    def test_set_values_fires_no_callback(self):
        """set_values does not fire on_change."""
        received = []
        rs = RangeSliderControl("rs", Rect(0, 0, 300, 28),
                                on_change=lambda lo, hi, r: received.append((lo, hi)))
        rs.set_values(10, 90)
        self.assertEqual([], received)

    def test_low_cannot_exceed_high(self):
        rs = RangeSliderControl("rs", Rect(0, 0, 300, 28),
                                min_value=0, max_value=100,
                                low_value=90, high_value=80)
        # After clamping+swap, invariant holds
        self.assertLessEqual(rs.low_value, rs.high_value)


class TestRangeSliderControlSnap(unittest.TestCase):
    def test_snap_to_step(self):
        rs = RangeSliderControl("rs", Rect(0, 0, 300, 28), min_value=0, max_value=100, step=10)
        snapped = rs._snap(37.0)
        self.assertAlmostEqual(40.0, snapped)

    def test_snap_clamped_to_max(self):
        rs = RangeSliderControl("rs", Rect(0, 0, 300, 28), min_value=0, max_value=100, step=10)
        snapped = rs._snap(105.0)
        self.assertAlmostEqual(100.0, snapped)

    def test_snap_clamped_to_min(self):
        rs = RangeSliderControl("rs", Rect(0, 0, 300, 28), min_value=0, max_value=100, step=10)
        snapped = rs._snap(-5.0)
        self.assertAlmostEqual(0.0, snapped)


# ===========================================================================
# ListItem
# ===========================================================================


class TestListItem(unittest.TestCase):
    def test_value_defaults_to_label(self):
        item = ListItem(label="Hello")
        self.assertEqual("Hello", item.value)

    def test_value_explicit(self):
        item = ListItem(label="Hello", value=99)
        self.assertEqual(99, item.value)

    def test_enabled_default_true(self):
        item = ListItem(label="X")
        self.assertTrue(item.enabled)

    def test_data_default_none(self):
        item = ListItem(label="X")
        self.assertIsNone(item.data)


# ===========================================================================
# ListViewControl — initial state
# ===========================================================================


class TestListViewControlInitial(unittest.TestCase):
    def test_empty_list(self):
        lv = ListViewControl("lv", Rect(0, 0, 300, 200))
        self.assertEqual(0, lv.item_count())

    def test_with_items(self):
        items = [ListItem("A"), ListItem("B"), ListItem("C")]
        lv = ListViewControl("lv", Rect(0, 0, 300, 200), items=items)
        self.assertEqual(3, lv.item_count())

    def test_auto_selects_first_when_items_present(self):
        lv = ListViewControl("lv", Rect(0, 0, 300, 200),
                             items=[ListItem("A"), ListItem("B")])
        self.assertEqual(0, lv.selected_index)

    def test_selected_index_parameter(self):
        lv = ListViewControl("lv", Rect(0, 0, 300, 200),
                             items=[ListItem("A"), ListItem("B")],
                             selected_index=1)
        self.assertEqual(1, lv.selected_index)

    def test_selected_item_returns_item(self):
        items = [ListItem("A"), ListItem("B")]
        lv = ListViewControl("lv", Rect(0, 0, 300, 200), items=items, selected_index=1)
        self.assertIs(items[1], lv.selected_item)

    def test_selected_item_none_when_empty(self):
        lv = ListViewControl("lv", Rect(0, 0, 300, 200))
        self.assertIsNone(lv.selected_item)

    def test_items_returns_copy(self):
        items = [ListItem("A")]
        lv = ListViewControl("lv", Rect(0, 0, 300, 200), items=items)
        copy = lv.items
        copy.clear()
        self.assertEqual(1, lv.item_count())

    def test_tab_index_zero(self):
        lv = ListViewControl("lv", Rect(0, 0, 300, 200))
        self.assertEqual(0, lv.tab_index)


class TestListViewControlMutation(unittest.TestCase):
    def test_set_items_replaces(self):
        lv = ListViewControl("lv", Rect(0, 0, 300, 200), items=[ListItem("Old")])
        lv.set_items([ListItem("New1"), ListItem("New2")])
        self.assertEqual(2, lv.item_count())

    def test_set_items_resets_selection_to_first(self):
        lv = ListViewControl("lv", Rect(0, 0, 300, 200))
        lv.set_items([ListItem("A"), ListItem("B")])
        self.assertEqual(0, lv.selected_index)

    def test_set_items_empty_clears_selection(self):
        lv = ListViewControl("lv", Rect(0, 0, 300, 200), items=[ListItem("X")])
        lv.set_items([])
        self.assertEqual(-1, lv.selected_index)

    def test_append_item(self):
        lv = ListViewControl("lv", Rect(0, 0, 300, 200))
        lv.append_item(ListItem("A"))
        self.assertEqual(1, lv.item_count())

    def test_remove_item_returns_true(self):
        lv = ListViewControl("lv", Rect(0, 0, 300, 200), items=[ListItem("A"), ListItem("B")])
        self.assertTrue(lv.remove_item(0))

    def test_remove_item_out_of_range_returns_false(self):
        lv = ListViewControl("lv", Rect(0, 0, 300, 200))
        self.assertFalse(lv.remove_item(0))

    def test_remove_item_decrements_count(self):
        lv = ListViewControl("lv", Rect(0, 0, 300, 200),
                             items=[ListItem("A"), ListItem("B")])
        lv.remove_item(0)
        self.assertEqual(1, lv.item_count())


class TestListViewControlSelect(unittest.TestCase):
    def test_select_fires_on_select(self):
        received = []
        items = [ListItem("A"), ListItem("B")]
        lv = ListViewControl("lv", Rect(0, 0, 300, 200),
                             items=items,
                             on_select=lambda idx, item: received.append((idx, item.label)))
        lv.select(1)
        self.assertEqual([(1, "B")], received)

    def test_select_out_of_range_no_effect(self):
        lv = ListViewControl("lv", Rect(0, 0, 300, 200),
                             items=[ListItem("A")])
        lv.select(99)
        self.assertEqual(0, lv.selected_index)

    def test_select_updates_selected_index(self):
        lv = ListViewControl("lv", Rect(0, 0, 300, 200),
                             items=[ListItem("A"), ListItem("B")])
        lv.select(1)
        self.assertEqual(1, lv.selected_index)

    def test_selected_index_setter(self):
        lv = ListViewControl("lv", Rect(0, 0, 300, 200),
                             items=[ListItem("A"), ListItem("B")])
        lv.selected_index = 1
        self.assertEqual(1, lv.selected_index)

    def test_selected_index_setter_out_of_range_uses_first(self):
        lv = ListViewControl("lv", Rect(0, 0, 300, 200),
                             items=[ListItem("A"), ListItem("B")])
        lv.selected_index = 99
        self.assertEqual(0, lv.selected_index)


class TestListViewControlMultiSelect(unittest.TestCase):
    def test_multi_select_allows_multiple(self):
        lv = ListViewControl("lv", Rect(0, 0, 300, 200),
                             items=[ListItem("A"), ListItem("B"), ListItem("C")],
                             multi_select=True)
        lv.select(0, scroll_to=False)
        lv.select(2, scroll_to=False)
        self.assertIn(0, lv.selected_indices)
        self.assertIn(2, lv.selected_indices)

    def test_single_select_replaces(self):
        lv = ListViewControl("lv", Rect(0, 0, 300, 200),
                             items=[ListItem("A"), ListItem("B"), ListItem("C")])
        lv.select(0, scroll_to=False)
        lv.select(2, scroll_to=False)
        self.assertEqual([2], lv.selected_indices)


if __name__ == "__main__":
    unittest.main()
