"""Tests for DataCache and CacheStats."""
import time
import unittest

from gui_do.data.data_cache import DataCache, CacheStats


class TestCacheStatsProperties(unittest.TestCase):
    def test_initial_stats_zero(self) -> None:
        cache: DataCache[str, int] = DataCache()
        s = cache.stats()
        self.assertEqual(s.hits, 0)
        self.assertEqual(s.misses, 0)
        self.assertEqual(s.evictions, 0)
        self.assertEqual(s.size, 0)

    def test_hit_rate_zero_when_no_lookups(self) -> None:
        s = CacheStats(size=0, hits=0, misses=0, evictions=0, invalidations=0)
        self.assertEqual(s.hit_rate, 0.0)

    def test_hit_rate_calculated_correctly(self) -> None:
        s = CacheStats(size=2, hits=8, misses=2, evictions=0, invalidations=0)
        self.assertAlmostEqual(s.hit_rate, 0.8)

    def test_total_lookups(self) -> None:
        s = CacheStats(size=0, hits=3, misses=7, evictions=0, invalidations=0)
        self.assertEqual(s.total_lookups, 10)


class TestPutAndGet(unittest.TestCase):
    def test_get_returns_value_after_put(self) -> None:
        cache: DataCache[str, int] = DataCache()
        cache.put("a", 1)
        self.assertEqual(cache.get("a"), 1)

    def test_get_returns_none_for_missing_key(self) -> None:
        cache: DataCache[str, int] = DataCache()
        self.assertIsNone(cache.get("missing"))

    def test_get_increments_hits_and_misses(self) -> None:
        cache: DataCache[str, int] = DataCache()
        cache.put("a", 10)
        cache.get("a")   # hit
        cache.get("b")   # miss
        s = cache.stats()
        self.assertEqual(s.hits, 1)
        self.assertEqual(s.misses, 1)


class TestContainsAndLen(unittest.TestCase):
    def test_contains_true_after_put(self) -> None:
        cache: DataCache[str, int] = DataCache()
        cache.put("k", 99)
        self.assertTrue(cache.contains("k"))

    def test_contains_false_for_missing(self) -> None:
        cache: DataCache[str, int] = DataCache()
        self.assertFalse(cache.contains("missing"))

    def test_len_grows_with_puts(self) -> None:
        cache: DataCache[str, int] = DataCache()
        self.assertEqual(len(cache), 0)
        cache.put("a", 1)
        cache.put("b", 2)
        self.assertEqual(len(cache), 2)


class TestLruEviction(unittest.TestCase):
    def test_oldest_evicted_when_max_size_exceeded(self) -> None:
        cache: DataCache[str, int] = DataCache(max_size=3)
        cache.put("a", 1)
        cache.put("b", 2)
        cache.put("c", 3)
        cache.put("d", 4)  # triggers eviction of 'a'
        self.assertFalse(cache.contains("a"))
        self.assertTrue(cache.contains("d"))
        self.assertEqual(len(cache), 3)

    def test_eviction_count_increments(self) -> None:
        cache: DataCache[str, int] = DataCache(max_size=2)
        cache.put("a", 1)
        cache.put("b", 2)
        cache.put("c", 3)
        self.assertEqual(cache.stats().evictions, 1)

    def test_access_refreshes_lru_order(self) -> None:
        cache: DataCache[str, int] = DataCache(max_size=2)
        cache.put("a", 1)
        cache.put("b", 2)
        cache.get("a")    # touch 'a', making 'b' the LRU
        cache.put("c", 3) # 'b' should be evicted
        self.assertFalse(cache.contains("b"))
        self.assertTrue(cache.contains("a"))


class TestInvalidate(unittest.TestCase):
    def test_invalidate_removes_key(self) -> None:
        cache: DataCache[str, int] = DataCache()
        cache.put("a", 1)
        cache.invalidate("a")
        self.assertFalse(cache.contains("a"))

    def test_invalidate_all_clears_cache(self) -> None:
        cache: DataCache[str, int] = DataCache()
        cache.put("a", 1)
        cache.put("b", 2)
        cache.invalidate_all()
        self.assertEqual(len(cache), 0)

    def test_invalidation_counter_increments(self) -> None:
        cache: DataCache[str, int] = DataCache()
        cache.put("x", 1)
        cache.invalidate("x")
        self.assertEqual(cache.stats().invalidations, 1)


class TestTtlExpiry(unittest.TestCase):
    def test_entry_missing_after_ttl(self) -> None:
        cache: DataCache[str, int] = DataCache(ttl_seconds=0.05)
        cache.put("a", 42)
        # Immediately available
        self.assertEqual(cache.get("a"), 42)
        time.sleep(0.1)
        # Should have expired
        self.assertIsNone(cache.get("a"))


class TestGetOrLoad(unittest.TestCase):
    def test_loads_when_missing(self) -> None:
        cache: DataCache[str, int] = DataCache()
        result = cache.get_or_load("a", lambda: 99)
        self.assertEqual(result, 99)
        self.assertEqual(cache.get("a"), 99)

    def test_returns_cached_without_calling_factory(self) -> None:
        cache: DataCache[str, int] = DataCache()
        cache.put("a", 7)
        calls = []
        result = cache.get_or_load("a", lambda: calls.append(1) or 99)
        self.assertEqual(result, 7)
        self.assertEqual(calls, [])

    def test_uses_default_factory_when_provided(self) -> None:
        cache: DataCache[str, int] = DataCache(factory=lambda k: len(k))
        result = cache.get_or_load("hello")
        self.assertEqual(result, 5)


class TestOnEvictedSignal(unittest.TestCase):
    def test_signal_fired_on_eviction(self) -> None:
        cache: DataCache[str, int] = DataCache(max_size=1)
        evicted = []
        cache.on_evicted.connect(lambda kv: evicted.append(kv))
        cache.put("a", 1)
        cache.put("b", 2)  # evicts 'a'
        self.assertEqual(len(evicted), 1)
        self.assertEqual(evicted[0][0], "a")


class TestOnInvalidatedSignal(unittest.TestCase):
    def test_signal_fired_on_invalidate(self) -> None:
        cache: DataCache[str, int] = DataCache()
        invalidated = []
        cache.on_invalidated.connect(lambda k: invalidated.append(k))
        cache.put("x", 10)
        cache.invalidate("x")
        self.assertEqual(invalidated, ["x"])
