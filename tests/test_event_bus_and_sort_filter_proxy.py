import unittest

from gui_do.events.event_bus import EventBus
from gui_do.data.sort_filter_proxy import SortFilterProxySource


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class _SimpleSource:
    """Minimal VirtualItemSource stub backed by a plain list."""

    def __init__(self, items):
        self._items = list(items)

    def item_count(self):
        return len(self._items)

    def item_at(self, index):
        return self._items[index]


# ---------------------------------------------------------------------------
# EventBus
# ---------------------------------------------------------------------------


class TestEventBus(unittest.TestCase):
    def test_subscribe_and_publish_delivers_payload(self):
        bus = EventBus()
        received = []
        bus.subscribe("click", received.append)

        bus.publish("click", "payload_a")

        self.assertEqual(["payload_a"], received)

    def test_publish_to_unknown_topic_is_noop(self):
        bus = EventBus()
        bus.publish("no_such_topic", "x")  # should not raise

    def test_unsubscribe_stops_delivery(self):
        bus = EventBus()
        received = []
        sub = bus.subscribe("click", received.append)

        bus.unsubscribe(sub)
        bus.publish("click", "x")

        self.assertEqual([], received)

    def test_multiple_subscribers_all_notified(self):
        bus = EventBus()
        a = []
        b = []
        bus.subscribe("ev", a.append)
        bus.subscribe("ev", b.append)

        bus.publish("ev", 1)

        self.assertEqual([1], a)
        self.assertEqual([1], b)

    def test_scoped_subscriber_receives_matching_scope(self):
        bus = EventBus()
        received = []
        bus.subscribe("ev", received.append, scope="scene_a")

        bus.publish("ev", "x", scope="scene_a")

        self.assertEqual(["x"], received)

    def test_scoped_subscriber_does_not_receive_different_scope(self):
        bus = EventBus()
        received = []
        bus.subscribe("ev", received.append, scope="scene_a")

        bus.publish("ev", "x", scope="scene_b")

        self.assertEqual([], received)

    def test_unscoped_subscriber_receives_all_publishes(self):
        bus = EventBus()
        received = []
        bus.subscribe("ev", received.append)

        bus.publish("ev", "x", scope="scene_a")
        bus.publish("ev", "y")

        self.assertEqual(["x", "y"], received)

    def test_unsubscribe_scope_removes_all_matching(self):
        bus = EventBus()
        a = []
        b = []
        bus.subscribe("ev", a.append, scope="s1")
        bus.subscribe("ev", b.append, scope="s1")

        count = bus.unsubscribe_scope("s1")

        self.assertEqual(2, count)
        bus.publish("ev", "x")
        self.assertEqual([], a)
        self.assertEqual([], b)

    def test_unsubscribe_scope_unknown_returns_zero(self):
        bus = EventBus()
        self.assertEqual(0, bus.unsubscribe_scope("no_such"))

    def test_subscriber_count_total(self):
        bus = EventBus()
        bus.subscribe("a", lambda p: None)
        bus.subscribe("a", lambda p: None)
        bus.subscribe("b", lambda p: None)

        self.assertEqual(3, bus.subscriber_count())

    def test_subscriber_count_filtered_by_topic(self):
        bus = EventBus()
        bus.subscribe("a", lambda p: None)
        bus.subscribe("b", lambda p: None)

        self.assertEqual(1, bus.subscriber_count("a"))

    def test_publish_none_payload_is_delivered(self):
        bus = EventBus()
        received = []
        bus.subscribe("ev", received.append)

        bus.publish("ev")

        self.assertEqual([None], received)

    def test_duplicate_unsubscribe_is_noop(self):
        bus = EventBus()
        sub = bus.subscribe("ev", lambda p: None)
        bus.unsubscribe(sub)
        bus.unsubscribe(sub)  # second unsubscribe — should not raise


# ---------------------------------------------------------------------------
# SortFilterProxySource
# ---------------------------------------------------------------------------


class TestSortFilterProxySource(unittest.TestCase):
    def _make(self, items):
        return SortFilterProxySource(_SimpleSource(items))

    def test_no_transforms_exposes_all_items_in_order(self):
        proxy = self._make(["a", "b", "c"])

        self.assertEqual(3, proxy.item_count())
        self.assertEqual(["a", "b", "c"], [proxy.item_at(i) for i in range(3)])

    def test_filter_reduces_visible_count(self):
        proxy = self._make([1, 2, 3, 4, 5])
        proxy.set_filter(lambda x: x % 2 == 0)

        self.assertEqual(2, proxy.item_count())
        self.assertEqual([2, 4], [proxy.item_at(i) for i in range(2)])

    def test_clear_filter_restores_all_items(self):
        proxy = self._make(["a", "b", "c"])
        proxy.set_filter(lambda x: x == "b")
        proxy.set_filter(None)

        self.assertEqual(3, proxy.item_count())

    def test_sort_key_reorders_items(self):
        proxy = self._make(["banana", "apple", "cherry"])
        proxy.set_sort_key(lambda x: x)

        self.assertEqual(["apple", "banana", "cherry"], [proxy.item_at(i) for i in range(3)])

    def test_sort_reverse_reverses_order(self):
        proxy = self._make([1, 2, 3])
        proxy.set_sort_key(lambda x: x, reverse=True)

        self.assertEqual([3, 2, 1], [proxy.item_at(i) for i in range(3)])

    def test_filter_and_sort_combined(self):
        proxy = self._make(["banana", "apple", "cherry", "avocado"])
        proxy.set_filter(lambda x: x.startswith("a"))
        proxy.set_sort_key(lambda x: x)

        self.assertEqual(2, proxy.item_count())
        self.assertEqual("apple", proxy.item_at(0))
        self.assertEqual("avocado", proxy.item_at(1))

    def test_subscriber_notified_on_set_filter(self):
        proxy = self._make([1, 2, 3])
        calls = []
        proxy.subscribe(lambda: calls.append(True))

        proxy.set_filter(lambda x: x > 1)

        self.assertEqual(1, len(calls))

    def test_subscriber_notified_on_set_sort_key(self):
        proxy = self._make([3, 1, 2])
        calls = []
        proxy.subscribe(lambda: calls.append(True))

        proxy.set_sort_key(lambda x: x)

        self.assertEqual(1, len(calls))

    def test_subscriber_notified_on_invalidate(self):
        proxy = self._make([1, 2])
        calls = []
        proxy.subscribe(lambda: calls.append(True))

        proxy.invalidate()

        self.assertEqual(1, len(calls))

    def test_unsubscribe_stops_notifications(self):
        proxy = self._make([1])
        calls = []
        unsub = proxy.subscribe(lambda: calls.append(True))

        unsub()
        proxy.invalidate()

        self.assertEqual([], calls)

    def test_plain_list_source_supported_via_len_and_getitem(self):
        raw = ["x", "y", "z"]
        proxy = SortFilterProxySource(raw)

        self.assertEqual(3, proxy.item_count())
        self.assertEqual("x", proxy.item_at(0))

    def test_empty_source_item_count_is_zero(self):
        proxy = self._make([])
        self.assertEqual(0, proxy.item_count())

    def test_filter_matching_nothing_gives_zero_count(self):
        proxy = self._make([1, 2, 3])
        proxy.set_filter(lambda x: False)
        self.assertEqual(0, proxy.item_count())


if __name__ == "__main__":
    unittest.main()
