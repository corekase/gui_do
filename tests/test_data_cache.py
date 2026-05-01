"""Tests for DataCache (LRU cache) and CacheStats."""
import unittest

from gui_do.data.data_cache import DataCache, CacheStats


# ===========================================================================
# CacheStats
# ===========================================================================


class TestCacheStats(unittest.TestCase):
    def test_total_lookups(self):
        s = CacheStats(size=5, hits=3, misses=2, evictions=0, invalidations=0)
        self.assertEqual(5, s.total_lookups)

    def test_hit_rate(self):
        s = CacheStats(size=5, hits=3, misses=1, evictions=0, invalidations=0)
        self.assertAlmostEqual(0.75, s.hit_rate)

    def test_hit_rate_no_lookups(self):
        s = CacheStats(size=0, hits=0, misses=0, evictions=0, invalidations=0)
        self.assertEqual(0.0, s.hit_rate)


# ===========================================================================
# DataCache — initial state
# ===========================================================================


class TestDataCacheInitial(unittest.TestCase):
    def test_max_size_stored(self):
        cache: DataCache = DataCache(max_size=32)
        self.assertEqual(32, cache.max_size)

    def test_zero_max_size_raises(self):
        with self.assertRaises(ValueError):
            DataCache(max_size=0)

    def test_initial_stats(self):
        cache: DataCache = DataCache()
        s = cache.stats()
        self.assertEqual(0, s.size)
        self.assertEqual(0, s.hits)
        self.assertEqual(0, s.misses)
        self.assertEqual(0, s.evictions)


# ===========================================================================
# DataCache — put / get
# ===========================================================================


class TestDataCachePutGet(unittest.TestCase):
    def test_get_miss_returns_none(self):
        cache: DataCache = DataCache()
        self.assertIsNone(cache.get("missing"))

    def test_put_then_get(self):
        cache: DataCache = DataCache()
        cache.put("key", 42)
        self.assertEqual(42, cache.get("key"))

    def test_put_overwrites(self):
        cache: DataCache = DataCache()
        cache.put("k", 1)
        cache.put("k", 99)
        self.assertEqual(99, cache.get("k"))

    def test_hit_increments_hits(self):
        cache: DataCache = DataCache()
        cache.put("k", "v")
        cache.get("k")
        self.assertEqual(1, cache.stats().hits)

    def test_miss_increments_misses(self):
        cache: DataCache = DataCache()
        cache.get("nope")
        self.assertEqual(1, cache.stats().misses)


# ===========================================================================
# DataCache — LRU eviction
# ===========================================================================


class TestDataCacheLRUEviction(unittest.TestCase):
    def test_eviction_at_capacity(self):
        cache: DataCache = DataCache(max_size=2)
        cache.put("a", 1)
        cache.put("b", 2)
        cache.put("c", 3)  # "a" should be evicted
        self.assertIsNone(cache.get("a"))
        self.assertEqual(2, cache.get("b"))
        self.assertEqual(3, cache.get("c"))

    def test_eviction_increments_counter(self):
        cache: DataCache = DataCache(max_size=1)
        cache.put("a", 1)
        cache.put("b", 2)  # evicts "a"
        self.assertEqual(1, cache.stats().evictions)

    def test_recent_access_protects_from_eviction(self):
        cache: DataCache = DataCache(max_size=2)
        cache.put("a", 1)
        cache.put("b", 2)
        cache.get("a")      # refresh "a"
        cache.put("c", 3)   # should evict "b" (LRU)
        self.assertIsNotNone(cache.get("a"))
        self.assertIsNone(cache.get("b"))


# ===========================================================================
# DataCache — invalidate / invalidate_all
# ===========================================================================


class TestDataCacheInvalidate(unittest.TestCase):
    def test_invalidate_removes_key(self):
        cache: DataCache = DataCache()
        cache.put("k", "v")
        cache.invalidate("k")
        self.assertIsNone(cache.get("k"))

    def test_invalidate_returns_true_when_found(self):
        cache: DataCache = DataCache()
        cache.put("k", "v")
        self.assertTrue(cache.invalidate("k"))

    def test_invalidate_returns_false_when_missing(self):
        cache: DataCache = DataCache()
        self.assertFalse(cache.invalidate("nope"))

    def test_invalidate_all_clears_cache(self):
        cache: DataCache = DataCache()
        cache.put("a", 1)
        cache.put("b", 2)
        cache.invalidate_all()
        self.assertIsNone(cache.get("a"))
        self.assertIsNone(cache.get("b"))


# ===========================================================================
# DataCache — get_or_load
# ===========================================================================


class TestDataCacheGetOrLoad(unittest.TestCase):
    def test_get_or_load_miss_calls_loader(self):
        cache: DataCache = DataCache()
        val = cache.get_or_load("k", lambda: 99)
        self.assertEqual(99, val)

    def test_get_or_load_hit_skips_loader(self):
        cache: DataCache = DataCache()
        cache.put("k", 42)
        calls = []
        val = cache.get_or_load("k", lambda: calls.append(1) or 0)
        self.assertEqual(42, val)
        self.assertEqual([], calls)

    def test_get_or_load_no_loader_no_factory_raises(self):
        cache: DataCache = DataCache()
        with self.assertRaises(ValueError):
            cache.get_or_load("k")

    def test_get_or_load_uses_factory(self):
        cache: DataCache = DataCache(factory=lambda k: f"val:{k}")
        val = cache.get_or_load("mykey")
        self.assertEqual("val:mykey", val)


if __name__ == "__main__":
    unittest.main()
