import unittest

from gui_do import EventBus


class EventBusScopeManagementTests(unittest.TestCase):
    def setUp(self) -> None:
        self.bus = EventBus()

    # --- subscriber_count ---

    def test_subscriber_count_zero_on_empty_bus(self) -> None:
        self.assertEqual(self.bus.subscriber_count(), 0)

    def test_subscriber_count_increases_with_subscriptions(self) -> None:
        self.bus.subscribe("topic", lambda p: None)
        self.bus.subscribe("topic", lambda p: None)
        self.bus.subscribe("other", lambda p: None)
        self.assertEqual(self.bus.subscriber_count(), 3)

    def test_subscriber_count_filtered_by_topic(self) -> None:
        self.bus.subscribe("a", lambda p: None)
        self.bus.subscribe("a", lambda p: None)
        self.bus.subscribe("b", lambda p: None)
        self.assertEqual(self.bus.subscriber_count("a"), 2)
        self.assertEqual(self.bus.subscriber_count("b"), 1)
        self.assertEqual(self.bus.subscriber_count("missing"), 0)

    def test_subscriber_count_decreases_after_unsubscribe(self) -> None:
        sub = self.bus.subscribe("topic", lambda p: None)
        self.assertEqual(self.bus.subscriber_count(), 1)
        self.bus.unsubscribe(sub)
        self.assertEqual(self.bus.subscriber_count(), 0)

    # --- unsubscribe_scope ---

    def test_unsubscribe_scope_removes_matching_subscriptions(self) -> None:
        self.bus.subscribe("a", lambda p: None, scope="scene1")
        self.bus.subscribe("b", lambda p: None, scope="scene1")
        self.bus.subscribe("a", lambda p: None, scope="scene2")

        removed = self.bus.unsubscribe_scope("scene1")

        self.assertEqual(removed, 2)
        self.assertEqual(self.bus.subscriber_count(), 1, "only scene2 subscription remains")

    def test_unsubscribe_scope_does_not_remove_unscoped_subscriptions(self) -> None:
        self.bus.subscribe("a", lambda p: None)           # no scope
        self.bus.subscribe("a", lambda p: None, scope="x")

        removed = self.bus.unsubscribe_scope("x")

        self.assertEqual(removed, 1)
        self.assertEqual(self.bus.subscriber_count(), 1, "unscoped subscription should survive")

    def test_unsubscribe_scope_returns_zero_when_no_match(self) -> None:
        self.bus.subscribe("a", lambda p: None, scope="other")
        removed = self.bus.unsubscribe_scope("nonexistent")
        self.assertEqual(removed, 0)
        self.assertEqual(self.bus.subscriber_count(), 1, "unmatched scope must not remove anything")

    def test_unsubscribe_scope_scoped_handlers_no_longer_receive_publishes(self) -> None:
        received = []
        self.bus.subscribe("evt", lambda p: received.append(p), scope="s")
        self.bus.publish("evt", "before", scope="s")
        self.assertEqual(received, ["before"])

        self.bus.unsubscribe_scope("s")
        self.bus.publish("evt", "after", scope="s")
        self.assertEqual(received, ["before"], "removed handler must not fire after unsubscribe_scope")

    def test_unsubscribe_scope_across_multiple_topics(self) -> None:
        received = []
        self.bus.subscribe("t1", lambda p: received.append(("t1", p)), scope="load")
        self.bus.subscribe("t2", lambda p: received.append(("t2", p)), scope="load")
        # No scope: fires for any publish regardless of scope argument
        self.bus.subscribe("t3", lambda p: received.append(("t3", p)))

        self.bus.unsubscribe_scope("load")

        self.bus.publish("t1", 1)
        self.bus.publish("t2", 2)
        self.bus.publish("t3", 3)

        # Only t3 (no scope) should have fired
        self.assertEqual(received, [("t3", 3)])

    def test_unsubscribe_scope_empty_bus_is_safe(self) -> None:
        # Should not raise on empty bus
        removed = self.bus.unsubscribe_scope("anything")
        self.assertEqual(removed, 0)

    # --- subscriber_count after scope removal ---

    def test_subscriber_count_reflects_scope_removal(self) -> None:
        self.bus.subscribe("a", lambda p: None, scope="s")
        self.bus.subscribe("b", lambda p: None, scope="s")
        self.bus.subscribe("c", lambda p: None)

        self.assertEqual(self.bus.subscriber_count(), 3)
        self.bus.unsubscribe_scope("s")
        self.assertEqual(self.bus.subscriber_count(), 1)

    # --- publish scope filter still applies after partial removal ---

    def test_publish_scope_filter_works_after_partial_scope_removal(self) -> None:
        received = []
        self.bus.subscribe("evt", lambda p: received.append(("s1", p)), scope="s1")
        self.bus.subscribe("evt", lambda p: received.append(("s2", p)), scope="s2")

        self.bus.unsubscribe_scope("s1")
        self.bus.publish("evt", 42, scope="s2")

        self.assertEqual(received, [("s2", 42)])


if __name__ == "__main__":
    unittest.main()
