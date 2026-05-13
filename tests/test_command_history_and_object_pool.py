import unittest

from gui_do.state.command_history import CommandHistory
from gui_do.data.object_pool import ObjectPool


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class _CountCommand:
    """Simple reversible counter command for testing."""

    def __init__(self, counter: list, description: str = "count"):
        self._counter = counter
        self._description = description

    @property
    def description(self) -> str:
        return self._description

    def execute(self) -> None:
        self._counter.append(1)

    def undo(self) -> None:
        self._counter.pop()


# ---------------------------------------------------------------------------
# CommandHistory
# ---------------------------------------------------------------------------


class TestCommandHistory(unittest.TestCase):
    def test_initially_cannot_undo_or_redo(self):
        h = CommandHistory()
        self.assertFalse(h.can_undo)
        self.assertFalse(h.can_redo)

    def test_push_executes_command_and_enables_undo(self):
        h = CommandHistory()
        counter = []
        h.push(_CountCommand(counter))

        self.assertEqual([1], counter)
        self.assertTrue(h.can_undo)

    def test_undo_reverses_command(self):
        h = CommandHistory()
        counter = []
        h.push(_CountCommand(counter))

        h.undo()

        self.assertEqual([], counter)
        self.assertFalse(h.can_undo)
        self.assertTrue(h.can_redo)

    def test_redo_re_executes_command(self):
        h = CommandHistory()
        counter = []
        h.push(_CountCommand(counter))
        h.undo()
        h.redo()

        self.assertEqual([1], counter)
        self.assertTrue(h.can_undo)
        self.assertFalse(h.can_redo)

    def test_new_push_clears_redo_stack(self):
        h = CommandHistory()
        counter = []
        h.push(_CountCommand(counter))
        h.undo()
        h.push(_CountCommand(counter))

        self.assertFalse(h.can_redo)

    def test_undo_on_empty_stack_returns_false(self):
        h = CommandHistory()
        self.assertFalse(h.undo())

    def test_redo_on_empty_stack_returns_false(self):
        h = CommandHistory()
        self.assertFalse(h.redo())

    def test_undo_description_reflects_top_of_stack(self):
        h = CommandHistory()
        counter = []
        h.push(_CountCommand(counter, "rename"))
        self.assertEqual("rename", h.undo_description)

    def test_redo_description_reflects_top_of_redo_stack(self):
        h = CommandHistory()
        counter = []
        h.push(_CountCommand(counter, "delete"))
        h.undo()
        self.assertEqual("delete", h.redo_description)

    def test_undo_stack_size_matches_pushes(self):
        h = CommandHistory()
        counter = []
        h.push(_CountCommand(counter))
        h.push(_CountCommand(counter))
        self.assertEqual(2, h.undo_stack_size)

    def test_max_size_limits_undo_stack_depth(self):
        h = CommandHistory(max_size=3)
        counter = []
        for _ in range(5):
            h.push(_CountCommand(counter))
        self.assertEqual(3, h.undo_stack_size)

    def test_subscribe_notified_on_push(self):
        h = CommandHistory()
        events = []
        h.subscribe(events.append)
        h.push(_CountCommand([]))
        self.assertIn("push", events)

    def test_subscribe_notified_on_undo(self):
        h = CommandHistory()
        events = []
        h.push(_CountCommand([]))
        h.subscribe(events.append)
        h.undo()
        self.assertIn("undo", events)

    def test_subscribe_notified_on_redo(self):
        h = CommandHistory()
        events = []
        h.push(_CountCommand([]))
        h.undo()
        h.subscribe(events.append)
        h.redo()
        self.assertIn("redo", events)

    def test_unsubscribe_stops_notifications(self):
        h = CommandHistory()
        events = []
        unsub = h.subscribe(events.append)
        unsub()
        h.push(_CountCommand([]))
        self.assertEqual([], events)

    def test_transaction_groups_commands_as_single_undo(self):
        h = CommandHistory()
        counter = []
        with h.transaction("bulk"):
            h.push(_CountCommand(counter))
            h.push(_CountCommand(counter))

        self.assertEqual(2, len(counter))
        h.undo()
        self.assertEqual([], counter)
        self.assertEqual(1, h.redo_stack_size)

    def test_abort_transaction_discards_it(self):
        h = CommandHistory()
        h.begin_transaction("t")
        h.abort_transaction()
        self.assertFalse(h.can_undo)

    def test_nested_transaction_raises(self):
        h = CommandHistory()
        h.begin_transaction("outer")
        with self.assertRaises(RuntimeError):
            h.begin_transaction("inner")
        h.abort_transaction()

    def test_end_transaction_without_begin_raises(self):
        h = CommandHistory()
        with self.assertRaises(RuntimeError):
            h.end_transaction()

    def test_push_without_execute_does_not_call_execute(self):
        h = CommandHistory()
        counter = []
        h.push(_CountCommand(counter), execute=False)
        self.assertEqual([], counter)
        self.assertTrue(h.can_undo)


# ---------------------------------------------------------------------------
# ObjectPool
# ---------------------------------------------------------------------------


class TestObjectPool(unittest.TestCase):
    def _make_pool(self, max_size=10, reset=None):
        return ObjectPool(list, reset=reset, max_size=max_size)

    def test_acquire_creates_new_object_when_pool_empty(self):
        pool = ObjectPool(lambda: {"new": True})
        obj = pool.acquire()
        self.assertTrue(obj["new"])

    def test_release_and_acquire_recycles_object(self):
        objs = [object(), object()]
        idx = [0]

        def factory():
            o = objs[idx[0]]
            idx[0] += 1
            return o

        pool = ObjectPool(factory, max_size=5)
        a = pool.acquire()
        pool.release(a)
        b = pool.acquire()
        self.assertIs(a, b)

    def test_reset_called_on_release(self):
        reset_calls = []
        pool = ObjectPool(list, reset=lambda obj: reset_calls.append(obj), max_size=5)
        obj = pool.acquire()
        pool.release(obj)
        self.assertEqual([obj], reset_calls)

    def test_pool_at_capacity_discards_released_objects(self):
        pool = ObjectPool(list, max_size=2)
        a, b, c = pool.acquire(), pool.acquire(), pool.acquire()
        pool.release(a)
        pool.release(b)
        pool.release(c)  # should be discarded

        stats = pool.stats()
        self.assertEqual(2, stats["size"])
        self.assertEqual(1, stats["discards"])

    def test_preallocate_warms_pool(self):
        pool = ObjectPool(list, max_size=10)
        pool.preallocate(5)
        stats = pool.stats()
        self.assertEqual(5, stats["size"])

    def test_preallocate_does_not_exceed_max_size(self):
        pool = ObjectPool(list, max_size=3)
        pool.preallocate(10)
        self.assertEqual(3, pool.stats()["size"])

    def test_stats_tracks_hits_and_misses(self):
        pool = ObjectPool(list, max_size=5)
        a = pool.acquire()       # miss
        pool.release(a)
        pool.acquire()           # hit

        stats = pool.stats()
        self.assertEqual(1, stats["hits"])
        self.assertEqual(1, stats["misses"])

    def test_clear_empties_pool(self):
        pool = ObjectPool(list, max_size=5)
        pool.preallocate(3)
        pool.clear()
        self.assertEqual(0, pool.stats()["size"])

    def test_max_size_property(self):
        pool = ObjectPool(list, max_size=42)
        self.assertEqual(42, pool.max_size)

    def test_acquire_after_release_does_not_create_new_object(self):
        created = [0]
        def factory():
            created[0] += 1
            return object()
        pool = ObjectPool(factory, max_size=5)
        obj = pool.acquire()    # creates 1
        pool.release(obj)
        pool.acquire()          # recycles
        self.assertEqual(1, created[0])


if __name__ == "__main__":
    unittest.main()
