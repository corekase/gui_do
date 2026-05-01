"""Tests for SortFilterProxySource — pure-logic reactive sort/filter decorator."""
import unittest

from gui_do.data.sort_filter_proxy import SortFilterProxySource


class _ListSource:
    """Minimal VirtualItemSource backed by a plain list."""
    def __init__(self, items):
        self._items = list(items)

    def item_count(self):
        return len(self._items)

    def item_at(self, index):
        return self._items[index]


# ===========================================================================
# Initial state
# ===========================================================================


class TestSortFilterProxyInitial(unittest.TestCase):
    def test_item_count_no_filter(self):
        src = _ListSource([1, 2, 3])
        proxy = SortFilterProxySource(src)
        self.assertEqual(3, proxy.item_count())

    def test_item_at_no_filter(self):
        src = _ListSource(["a", "b", "c"])
        proxy = SortFilterProxySource(src)
        self.assertEqual("a", proxy.item_at(0))

    def test_works_with_plain_list(self):
        proxy = SortFilterProxySource([10, 20, 30])
        self.assertEqual(3, proxy.item_count())
        self.assertEqual(20, proxy.item_at(1))


# ===========================================================================
# Filter
# ===========================================================================


class TestSortFilterProxyFilter(unittest.TestCase):
    def test_filter_reduces_count(self):
        proxy = SortFilterProxySource([1, 2, 3, 4, 5])
        proxy.set_filter(lambda x: x % 2 == 0)
        self.assertEqual(2, proxy.item_count())

    def test_filter_returns_correct_items(self):
        proxy = SortFilterProxySource(["apple", "banana", "apricot"])
        proxy.set_filter(lambda s: s.startswith("a"))
        items = [proxy.item_at(i) for i in range(proxy.item_count())]
        self.assertIn("apple", items)
        self.assertIn("apricot", items)
        self.assertNotIn("banana", items)

    def test_clear_filter_restores_all(self):
        proxy = SortFilterProxySource([1, 2, 3])
        proxy.set_filter(lambda x: x > 10)
        self.assertEqual(0, proxy.item_count())
        proxy.set_filter(None)
        self.assertEqual(3, proxy.item_count())

    def test_filter_notifies_subscriber(self):
        calls = []
        proxy = SortFilterProxySource([1, 2, 3])
        proxy.subscribe(lambda: calls.append(1))
        proxy.set_filter(lambda x: x > 1)
        self.assertGreater(len(calls), 0)


# ===========================================================================
# Sort
# ===========================================================================


class TestSortFilterProxySort(unittest.TestCase):
    def test_sort_ascending(self):
        proxy = SortFilterProxySource([3, 1, 2])
        proxy.set_sort_key(lambda x: x)
        items = [proxy.item_at(i) for i in range(proxy.item_count())]
        self.assertEqual([1, 2, 3], items)

    def test_sort_descending(self):
        proxy = SortFilterProxySource([3, 1, 2])
        proxy.set_sort_key(lambda x: x, reverse=True)
        items = [proxy.item_at(i) for i in range(proxy.item_count())]
        self.assertEqual([3, 2, 1], items)

    def test_sort_strings(self):
        proxy = SortFilterProxySource(["banana", "apple", "cherry"])
        proxy.set_sort_key(lambda s: s)
        self.assertEqual("apple", proxy.item_at(0))

    def test_clear_sort_restores_order(self):
        proxy = SortFilterProxySource([3, 1, 2])
        proxy.set_sort_key(lambda x: x)
        proxy.set_sort_key(None)
        self.assertEqual(3, proxy.item_at(0))  # original order


# ===========================================================================
# Filter + sort combined
# ===========================================================================


class TestSortFilterProxyCombined(unittest.TestCase):
    def test_filter_then_sort(self):
        proxy = SortFilterProxySource([5, 2, 8, 1, 4])
        proxy.set_filter(lambda x: x > 3)
        proxy.set_sort_key(lambda x: x)
        items = [proxy.item_at(i) for i in range(proxy.item_count())]
        self.assertEqual([4, 5, 8], items)


# ===========================================================================
# Subscribe / unsubscribe
# ===========================================================================


class TestSortFilterProxySubscribe(unittest.TestCase):
    def test_subscribe_called_on_invalidate(self):
        calls = []
        proxy = SortFilterProxySource([1, 2, 3])
        proxy.subscribe(lambda: calls.append(1))
        proxy.invalidate()
        self.assertGreater(len(calls), 0)

    def test_unsubscribe_stops_notifications(self):
        calls = []
        proxy = SortFilterProxySource([1, 2, 3])
        unsub = proxy.subscribe(lambda: calls.append(1))
        unsub()
        proxy.invalidate()
        self.assertEqual(0, len(calls))


if __name__ == "__main__":
    unittest.main()
