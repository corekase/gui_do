"""Tests for SelectionModel and SelectionMode."""
import unittest

from gui_do.data.selection_model import SelectionModel, SelectionMode


# ===========================================================================
# SelectionModel — initial state
# ===========================================================================


class TestSelectionModelInitial(unittest.TestCase):
    def test_mode_default_single(self):
        m = SelectionModel(item_count=10)
        self.assertEqual(SelectionMode.SINGLE, m.mode)

    def test_item_count_stored(self):
        m = SelectionModel(item_count=5)
        self.assertEqual(5, m.item_count)

    def test_selected_indices_empty(self):
        m = SelectionModel(item_count=5)
        self.assertEqual(frozenset(), m.selected_indices)

    def test_selected_index_minus_one(self):
        m = SelectionModel(item_count=5)
        self.assertEqual(-1, m.selected_index)

    def test_anchor_none(self):
        m = SelectionModel(item_count=5)
        self.assertIsNone(m.anchor)

    def test_active_end_none(self):
        m = SelectionModel(item_count=5)
        self.assertIsNone(m.active_end)


# ===========================================================================
# SelectionModel — SINGLE mode
# ===========================================================================


class TestSelectionModelSingle(unittest.TestCase):
    def test_select_item(self):
        m = SelectionModel(item_count=5)
        m.select(2)
        self.assertEqual(frozenset({2}), m.selected_indices)

    def test_select_replaces_previous(self):
        m = SelectionModel(item_count=5)
        m.select(1)
        m.select(3)
        self.assertEqual(frozenset({3}), m.selected_indices)

    def test_select_invalid_out_of_range(self):
        m = SelectionModel(item_count=5)
        m.select(10)
        self.assertEqual(frozenset(), m.selected_indices)

    def test_deselect(self):
        m = SelectionModel(item_count=5)
        m.select(2)
        m.deselect(2)
        self.assertEqual(frozenset(), m.selected_indices)

    def test_deselect_not_selected_no_error(self):
        m = SelectionModel(item_count=5)
        m.deselect(2)  # should not raise

    def test_is_selected_true(self):
        m = SelectionModel(item_count=5)
        m.select(2)
        self.assertTrue(m.is_selected(2))

    def test_is_selected_false(self):
        m = SelectionModel(item_count=5)
        m.select(2)
        self.assertFalse(m.is_selected(3))

    def test_selected_index_lowest(self):
        m = SelectionModel(item_count=5)
        m.select(4)
        self.assertEqual(4, m.selected_index)

    def test_clear(self):
        m = SelectionModel(item_count=5)
        m.select(2)
        m.clear()
        self.assertEqual(frozenset(), m.selected_indices)

    def test_select_all(self):
        m = SelectionModel(item_count=3)
        m.select_all()
        self.assertEqual(frozenset({0, 1, 2}), m.selected_indices)


# ===========================================================================
# SelectionModel — MULTI mode
# ===========================================================================


class TestSelectionModelMulti(unittest.TestCase):
    def test_multiple_selected(self):
        m = SelectionModel(mode=SelectionMode.MULTI, item_count=10)
        m.select(1)
        m.select(3)
        m.select(5)
        self.assertEqual(frozenset({1, 3, 5}), m.selected_indices)

    def test_toggle_adds(self):
        m = SelectionModel(mode=SelectionMode.MULTI, item_count=10)
        m.toggle(2)
        self.assertIn(2, m.selected_indices)

    def test_toggle_removes(self):
        m = SelectionModel(mode=SelectionMode.MULTI, item_count=10)
        m.toggle(2)
        m.toggle(2)
        self.assertNotIn(2, m.selected_indices)

    def test_select_all_multi(self):
        m = SelectionModel(mode=SelectionMode.MULTI, item_count=3)
        m.select_all()
        self.assertEqual(3, len(m.selected_indices))


# ===========================================================================
# SelectionModel — RANGE mode
# ===========================================================================


class TestSelectionModelRange(unittest.TestCase):
    def test_range_anchor_to_active(self):
        m = SelectionModel(mode=SelectionMode.RANGE, item_count=20)
        m.set_anchor(3)
        m.set_active(7)
        self.assertEqual(frozenset(range(3, 8)), m.selected_indices)

    def test_range_reverse_order(self):
        m = SelectionModel(mode=SelectionMode.RANGE, item_count=20)
        m.set_anchor(7)
        m.set_active(3)
        self.assertEqual(frozenset(range(3, 8)), m.selected_indices)

    def test_anchor_stored(self):
        m = SelectionModel(mode=SelectionMode.RANGE, item_count=20)
        m.set_anchor(5)
        self.assertEqual(5, m.anchor)

    def test_active_stored(self):
        m = SelectionModel(mode=SelectionMode.RANGE, item_count=20)
        m.set_anchor(5)
        m.set_active(8)
        self.assertEqual(8, m.active_end)

    def test_single_item_range(self):
        m = SelectionModel(mode=SelectionMode.RANGE, item_count=10)
        m.set_anchor(4)
        m.set_active(4)
        self.assertEqual(frozenset({4}), m.selected_indices)


# ===========================================================================
# SelectionModel — mutation and callbacks
# ===========================================================================


class TestSelectionModelCallbacks(unittest.TestCase):
    def test_on_change_called_on_select(self):
        called = []
        m = SelectionModel(item_count=10, on_change=lambda model: called.append(1))
        m.select(2)
        self.assertEqual([1], called)

    def test_subscribe_called(self):
        called = []
        m = SelectionModel(item_count=10)
        m.subscribe(lambda model: called.append(1))
        m.select(3)
        self.assertEqual([1], called)

    def test_unsubscribe(self):
        called = []
        m = SelectionModel(item_count=10)
        unsub = m.subscribe(lambda model: called.append(1))
        unsub()
        m.select(3)
        self.assertEqual([], called)

    def test_set_item_count_prunes_selection(self):
        m = SelectionModel(mode=SelectionMode.MULTI, item_count=10)
        m.select(8)
        m.set_item_count(5)
        self.assertNotIn(8, m.selected_indices)
        self.assertEqual(5, m.item_count)

    def test_mode_change_clears_selection(self):
        m = SelectionModel(item_count=10)
        m.select(3)
        m.mode = SelectionMode.MULTI
        self.assertEqual(frozenset(), m.selected_indices)


if __name__ == "__main__":
    unittest.main()
