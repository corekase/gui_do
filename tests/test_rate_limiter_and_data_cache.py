import time
import unittest

from gui_do.scheduling.rate_limiter import Debouncer, Throttler
from gui_do.data.data_cache import DataCache


# ---------------------------------------------------------------------------
# Fake Timers — records add_once / remove_timer calls so we can fire them
# deterministically without real time passing.
# ---------------------------------------------------------------------------


class _FakeTimers:
    """Minimal Timers stub for Debouncer / Throttler testing."""

    def __init__(self):
        # {timer_id: callback}
        self._pending = {}

    def add_once(self, timer_id, delay_s, callback):
        self._pending[timer_id] = callback

    def remove_timer(self, timer_id):
        self._pending.pop(timer_id, None)

    def fire(self, timer_id):
        """Manually fire a scheduled timer (simulates elapsed time)."""
        cb = self._pending.pop(timer_id, None)
        if cb is not None:
            cb()

    def has_timer(self, timer_id):
        return timer_id in self._pending


# ---------------------------------------------------------------------------
# Debouncer
# ---------------------------------------------------------------------------


class TestDebouncer(unittest.TestCase):
    def _make(self, cb, *, timer_id="t"):
        self.timers = _FakeTimers()
        return Debouncer(delay_ms=200, callback=cb, timers=self.timers, timer_id=timer_id)

    def test_call_registers_timer(self):
        received = []
        d = self._make(received.append)
        d.call("x")
        self.assertTrue(self.timers.has_timer("t"))

    def test_callback_not_invoked_until_timer_fires(self):
        received = []
        d = self._make(received.append)
        d.call("x")
        self.assertEqual([], received)

    def test_callback_invoked_when_timer_fires(self):
        received = []
        d = self._make(received.append)
        d.call("x")
        self.timers.fire("t")
        self.assertEqual(["x"], received)

    def test_subsequent_calls_reset_timer(self):
        received = []
        d = self._make(received.append)
        d.call("first")
        d.call("second")
        # Only one timer should be active
        self.assertTrue(self.timers.has_timer("t"))
        self.timers.fire("t")
        # Callback fires with latest args
        self.assertEqual(["second"], received)

    def test_is_pending_true_after_call(self):
        d = self._make(lambda x: None)
        d.call("x")
        self.assertTrue(d.is_pending)

    def test_is_pending_false_after_timer_fires(self):
        d = self._make(lambda x: None)
        d.call("x")
        self.timers.fire("t")
        self.assertFalse(d.is_pending)

    def test_cancel_clears_pending_and_removes_timer(self):
        received = []
        d = self._make(received.append)
        d.call("x")
        d.cancel()
        self.assertFalse(d.is_pending)
        self.assertFalse(self.timers.has_timer("t"))

    def test_cancel_on_idle_debouncer_is_noop(self):
        d = self._make(lambda x: None)
        d.cancel()  # should not raise

    def test_flush_fires_immediately_and_clears_timer(self):
        received = []
        d = self._make(received.append)
        d.call("x")
        d.flush()
        self.assertEqual(["x"], received)
        self.assertFalse(self.timers.has_timer("t"))
        self.assertFalse(d.is_pending)

    def test_flush_on_idle_debouncer_is_noop(self):
        received = []
        d = self._make(received.append)
        d.flush()
        self.assertEqual([], received)

    def test_callback_receives_kwargs(self):
        received = []
        d = self._make(lambda **kw: received.append(kw))
        d.call(key="val")
        self.timers.fire("t")
        self.assertEqual([{"key": "val"}], received)

    def test_invalid_delay_raises(self):
        with self.assertRaises(ValueError):
            Debouncer(delay_ms=0, callback=lambda: None, timers=_FakeTimers())

    def test_non_callable_callback_raises(self):
        with self.assertRaises(ValueError):
            Debouncer(delay_ms=100, callback="not_callable", timers=_FakeTimers())


# ---------------------------------------------------------------------------
# Throttler
# ---------------------------------------------------------------------------


class TestThrottler(unittest.TestCase):
    def _make(self, cb, *, timer_id="t", leading=True):
        self.timers = _FakeTimers()
        return Throttler(interval_ms=100, callback=cb, timers=self.timers,
                         timer_id=timer_id, leading=leading)

    def test_first_call_fires_immediately_leading_true(self):
        received = []
        th = self._make(received.append)
        th.call("a")
        self.assertEqual(["a"], received)

    def test_second_call_within_interval_is_buffered(self):
        received = []
        th = self._make(received.append)
        th.call("a")
        th.call("b")
        # "b" not yet fired — buffered for trailing edge
        self.assertEqual(["a"], received)

    def test_trailing_edge_fires_buffered_call(self):
        received = []
        th = self._make(received.append)
        th.call("a")
        th.call("b")
        # Simulate interval end
        self.timers.fire("t")
        # trailing-edge call fires "b" (leading) then interval ends again
        self.assertIn("b", received)

    def test_only_most_recent_buffered_call_fires(self):
        received = []
        th = self._make(received.append)
        th.call("a")
        th.call("b")
        th.call("c")  # overwrites "b"
        self.timers.fire("t")
        # "c" fires as trailing-edge, "b" is discarded
        self.assertIn("c", received)
        self.assertNotIn("b", received)

    def test_is_locked_true_within_interval(self):
        th = self._make(lambda x: None)
        th.call("a")
        self.assertTrue(th.is_locked)

    def test_is_locked_false_after_interval_with_no_queued_call(self):
        th = self._make(lambda x: None)
        th.call("a")
        self.timers.fire("t")  # no queued call → unlocks
        self.assertFalse(th.is_locked)

    def test_cancel_resets_lock(self):
        received = []
        th = self._make(received.append)
        th.call("a")
        th.call("b")
        th.cancel()
        self.assertFalse(th.is_locked)
        self.assertFalse(self.timers.has_timer("t"))

    def test_cancel_discards_buffered_call(self):
        received = []
        th = self._make(received.append)
        th.call("a")
        th.call("b")
        th.cancel()
        # Simulate interval end (timer was removed, so fire is a no-op)
        self.timers.fire("t")
        self.assertEqual(["a"], received)

    def test_leading_false_does_not_fire_on_first_call(self):
        received = []
        th = self._make(received.append, leading=False)
        th.call("x")
        self.assertEqual([], received)

    def test_leading_false_buffers_until_second_window(self):
        # With leading=False, _on_interval_end re-enters call() which buffers
        # again; the callback fires when a subsequent trailing call is provided.
        received = []
        th = self._make(received.append, leading=False)
        th.call("x")                 # starts window, buffers "x"
        self.timers.fire("t")        # _on_interval_end re-calls call("x") → buffers, new timer
        # The callback has NOT fired yet — still buffered for next interval
        self.assertEqual([], received)
        # A second explicit call overrides the buffer with "y"
        th.call("y")                 # overwrites queued (already locked)
        th.cancel()                  # clean up
        self.assertFalse(th.is_locked)

    def test_invalid_interval_raises(self):
        with self.assertRaises(ValueError):
            Throttler(interval_ms=0, callback=lambda: None, timers=_FakeTimers())

    def test_non_callable_raises(self):
        with self.assertRaises(ValueError):
            Throttler(interval_ms=100, callback=42, timers=_FakeTimers())


# ---------------------------------------------------------------------------
# DataCache
# ---------------------------------------------------------------------------


class TestDataCache(unittest.TestCase):
    def test_get_miss_returns_none(self):
        cache = DataCache(max_size=10)
        self.assertIsNone(cache.get("missing"))

    def test_put_and_get_returns_value(self):
        cache = DataCache(max_size=10)
        cache.put("k", "v")
        self.assertEqual("v", cache.get("k"))

    def test_get_updates_stats_hit(self):
        cache = DataCache(max_size=10)
        cache.put("k", "v")
        cache.get("k")
        self.assertEqual(1, cache.stats().hits)
        self.assertEqual(0, cache.stats().misses)

    def test_get_miss_updates_stats_miss(self):
        cache = DataCache(max_size=10)
        cache.get("no")
        self.assertEqual(1, cache.stats().misses)
        self.assertEqual(0, cache.stats().hits)

    def test_invalidate_removes_key(self):
        cache = DataCache(max_size=10)
        cache.put("k", "v")
        result = cache.invalidate("k")
        self.assertTrue(result)
        self.assertIsNone(cache.get("k"))

    def test_invalidate_missing_key_returns_false(self):
        cache = DataCache(max_size=10)
        self.assertFalse(cache.invalidate("no"))

    def test_invalidate_all_clears_cache(self):
        cache = DataCache(max_size=10)
        cache.put("a", 1)
        cache.put("b", 2)
        removed = cache.invalidate_all()
        self.assertEqual(2, removed)
        self.assertEqual(0, len(cache))

    def test_on_invalidated_signal_fires(self):
        cache = DataCache(max_size=10)
        cache.put("k", "v")
        fired = []
        cache.on_invalidated.connect(fired.append)
        cache.invalidate("k")
        self.assertEqual(["k"], fired)

    def test_on_evicted_signal_fires_on_lru_eviction(self):
        cache = DataCache(max_size=2)
        evicted = []
        cache.on_evicted.connect(evicted.append)
        cache.put("a", 1)
        cache.put("b", 2)
        cache.put("c", 3)  # "a" evicted
        self.assertEqual(1, len(evicted))
        self.assertEqual("a", evicted[0][0])

    def test_lru_evicts_least_recently_used(self):
        cache = DataCache(max_size=2)
        cache.put("a", 1)
        cache.put("b", 2)
        cache.get("a")   # promote "a"
        cache.put("c", 3)  # "b" should be evicted now
        self.assertIsNone(cache.get("b"))
        self.assertEqual(1, cache.get("a"))

    def test_get_or_load_on_miss_uses_loader(self):
        cache = DataCache(max_size=10)
        val = cache.get_or_load("k", lambda: "loaded")
        self.assertEqual("loaded", val)

    def test_get_or_load_on_hit_skips_loader(self):
        cache = DataCache(max_size=10)
        cache.put("k", "existing")
        loader_calls = []
        val = cache.get_or_load("k", lambda: loader_calls.append(True) or "new")
        self.assertEqual("existing", val)
        self.assertEqual([], loader_calls)

    def test_get_or_load_with_factory(self):
        cache = DataCache(max_size=10, factory=lambda k: f"computed_{k}")
        val = cache.get_or_load("foo")
        self.assertEqual("computed_foo", val)

    def test_get_or_load_no_loader_no_factory_raises(self):
        cache = DataCache(max_size=10)
        with self.assertRaises(ValueError):
            cache.get_or_load("k")

    def test_contains_true_for_present_key(self):
        cache = DataCache(max_size=10)
        cache.put("k", "v")
        self.assertTrue(cache.contains("k"))

    def test_contains_false_for_missing_key(self):
        cache = DataCache(max_size=10)
        self.assertFalse(cache.contains("k"))

    def test_len_reflects_entry_count(self):
        cache = DataCache(max_size=10)
        cache.put("a", 1)
        cache.put("b", 2)
        self.assertEqual(2, len(cache))

    def test_stats_eviction_count(self):
        cache = DataCache(max_size=1)
        cache.put("a", 1)
        cache.put("b", 2)  # evicts "a"
        self.assertEqual(1, cache.stats().evictions)

    def test_stats_invalidation_count(self):
        cache = DataCache(max_size=10)
        cache.put("a", 1)
        cache.invalidate("a")
        self.assertEqual(1, cache.stats().invalidations)

    def test_stats_hit_rate_zero_when_no_lookups(self):
        cache = DataCache(max_size=10)
        self.assertEqual(0.0, cache.stats().hit_rate)

    def test_max_size_property(self):
        cache = DataCache(max_size=64)
        self.assertEqual(64, cache.max_size)

    def test_zero_max_size_raises(self):
        with self.assertRaises(ValueError):
            DataCache(max_size=0)

    def test_ttl_expires_entry(self):
        cache = DataCache(max_size=10, ttl_seconds=0.01)
        cache.put("k", "v")
        time.sleep(0.02)
        self.assertIsNone(cache.get("k"))

    def test_ttl_entry_still_valid_before_expiry(self):
        cache = DataCache(max_size=10, ttl_seconds=10.0)
        cache.put("k", "v")
        self.assertEqual("v", cache.get("k"))


if __name__ == "__main__":
    unittest.main()
