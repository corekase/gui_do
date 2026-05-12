"""Tests for CollectionView, CollectionViewQuery, validate_value_change_callback, dispatch_value_change."""
import unittest

from gui_do.data.collection_view import CollectionView, CollectionViewQuery
from gui_do.events.value_change import (
    ValueChangeReason,
    dispatch_value_change,
    validate_value_change_callback,
)


# ===========================================================================
# validate_value_change_callback
# ===========================================================================


class TestValidateValueChangeCallback(unittest.TestCase):
    def test_none_is_ok(self):
        validate_value_change_callback(None)  # should not raise

    def test_callable_is_ok(self):
        validate_value_change_callback(lambda v, r: None)  # should not raise

    def test_non_callable_raises(self):
        with self.assertRaises(TypeError):
            validate_value_change_callback("not_callable")


# ===========================================================================
# dispatch_value_change
# ===========================================================================


class TestDispatchValueChange(unittest.TestCase):
    def test_none_callback_no_op(self):
        dispatch_value_change(None, 42, ValueChangeReason.PROGRAMMATIC)  # no raise

    def test_calls_callback_with_value_and_reason(self):
        calls = []
        dispatch_value_change(
            lambda v, r: calls.append((v, r)),
            99,
            ValueChangeReason.KEYBOARD,
        )
        self.assertEqual([(99, ValueChangeReason.KEYBOARD)], calls)


# ===========================================================================
# CollectionViewQuery
# ===========================================================================


class TestCollectionViewQuery(unittest.TestCase):
    def test_defaults(self):
        q = CollectionViewQuery()
        self.assertEqual([], q.filters)
        self.assertIsNone(q.sort_key)
        self.assertFalse(q.reverse)
        self.assertIsNone(q.projector)


# ===========================================================================
# CollectionView — initial state
# ===========================================================================


class TestCollectionViewInitial(unittest.TestCase):
    def test_items_from_list_source(self):
        cv = CollectionView([1, 2, 3])
        self.assertEqual([1, 2, 3], cv.items)

    def test_count(self):
        cv = CollectionView([10, 20])
        self.assertEqual(2, cv.count())

    def test_callable_source(self):
        cv = CollectionView(lambda: [4, 5, 6])
        self.assertEqual([4, 5, 6], cv.items)

    def test_items_returns_copy(self):
        cv = CollectionView([1, 2, 3])
        copy = cv.items
        copy.append(99)
        self.assertEqual([1, 2, 3], cv.items)


# ===========================================================================
# CollectionView — filter
# ===========================================================================


class TestCollectionViewFilter(unittest.TestCase):
    def test_single_filter(self):
        q = CollectionViewQuery(filters=[lambda x: x > 2])
        cv = CollectionView([1, 2, 3, 4], query=q)
        self.assertEqual([3, 4], cv.items)

    def test_multiple_filters(self):
        q = CollectionViewQuery(filters=[lambda x: x > 1, lambda x: x < 4])
        cv = CollectionView([1, 2, 3, 4], query=q)
        self.assertEqual([2, 3], cv.items)


# ===========================================================================
# CollectionView — sort
# ===========================================================================


class TestCollectionViewSort(unittest.TestCase):
    def test_sort_ascending(self):
        q = CollectionViewQuery(sort_key=lambda x: x)
        cv = CollectionView([3, 1, 2], query=q)
        self.assertEqual([1, 2, 3], cv.items)

    def test_sort_descending(self):
        q = CollectionViewQuery(sort_key=lambda x: x, reverse=True)
        cv = CollectionView([3, 1, 2], query=q)
        self.assertEqual([3, 2, 1], cv.items)


# ===========================================================================
# CollectionView — projector
# ===========================================================================


class TestCollectionViewProjector(unittest.TestCase):
    def test_projector_transforms_items(self):
        q = CollectionViewQuery(projector=lambda x: x * 10)
        cv = CollectionView([1, 2, 3], query=q)
        self.assertEqual([10, 20, 30], cv.items)


# ===========================================================================
# CollectionView — refresh / set_source / subscribe
# ===========================================================================


class TestCollectionViewRefresh(unittest.TestCase):
    def test_refresh_notifies_subscribers(self):
        calls = []
        cv = CollectionView([1, 2, 3])
        cv.subscribe(lambda: calls.append(1))
        cv.refresh()
        self.assertEqual(1, len(calls))

    def test_unsubscribe_stops_notifications(self):
        calls = []
        cv = CollectionView([1, 2, 3])
        unsub = cv.subscribe(lambda: calls.append(1))
        unsub()
        cv.refresh()
        self.assertEqual(0, len(calls))

    def test_set_source_updates_items(self):
        cv = CollectionView([1, 2, 3])
        cv.set_source([10, 20])
        self.assertEqual([10, 20], cv.items)


if __name__ == "__main__":
    unittest.main()
