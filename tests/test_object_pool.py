"""Tests for ObjectPool — typed thread-safe object recycler."""
import unittest

from gui_do.data.object_pool import ObjectPool


# ===========================================================================
# Initial state
# ===========================================================================


class TestObjectPoolInitial(unittest.TestCase):
    def test_stats_initial(self):
        pool = ObjectPool(lambda: object())
        s = pool.stats()
        self.assertEqual(0, s["size"])
        self.assertEqual(0, s["hits"])
        self.assertEqual(0, s["misses"])
        self.assertEqual(0, s["discards"])

    def test_max_size_minimum_one(self):
        pool = ObjectPool(lambda: object(), max_size=0)
        # Should not raise — pool still has size >= 1
        pool.acquire()


# ===========================================================================
# Acquire / release
# ===========================================================================


class TestObjectPoolAcquireRelease(unittest.TestCase):
    def test_acquire_creates_new_object(self):
        created = []
        def factory():
            obj = object()
            created.append(obj)
            return obj
        pool = ObjectPool(factory)
        obj = pool.acquire()
        self.assertIn(obj, created)
        self.assertEqual(1, pool.stats()["misses"])

    def test_acquire_reuses_released_object(self):
        sentinel = object()
        pool = ObjectPool(lambda: sentinel)
        pool.release(sentinel)
        obj = pool.acquire()
        self.assertIs(sentinel, obj)
        self.assertEqual(1, pool.stats()["hits"])

    def test_release_calls_reset(self):
        reset_calls = []
        pool = ObjectPool(list, reset=lambda obj: reset_calls.append(True))
        obj = pool.acquire()
        pool.release(obj)
        self.assertEqual(1, len(reset_calls))

    def test_release_at_capacity_discards(self):
        pool = ObjectPool(list, max_size=1)
        a = pool.acquire()
        b = pool.acquire()
        pool.release(a)
        pool.release(b)  # pool already full → discard
        self.assertEqual(1, pool.stats()["discards"])

    def test_release_adds_to_pool_size(self):
        pool = ObjectPool(list)
        pool.release([])
        self.assertEqual(1, pool.stats()["size"])


# ===========================================================================
# Preallocate / clear
# ===========================================================================


class TestObjectPoolPreallocate(unittest.TestCase):
    def test_preallocate_fills_pool(self):
        pool = ObjectPool(list, max_size=10)
        pool.preallocate(5)
        self.assertEqual(5, pool.stats()["size"])

    def test_preallocate_respects_max_size(self):
        pool = ObjectPool(list, max_size=3)
        pool.preallocate(10)
        self.assertEqual(3, pool.stats()["size"])

    def test_clear_empties_pool(self):
        pool = ObjectPool(list)
        pool.preallocate(5)
        pool.clear()
        self.assertEqual(0, pool.stats()["size"])


# ===========================================================================
# Reset callback
# ===========================================================================


class TestObjectPoolReset(unittest.TestCase):
    def test_reset_applied_before_reuse(self):
        class Counter:
            value = 0

        def reset(obj):
            obj.value = 0

        pool = ObjectPool(Counter, reset=reset)
        obj = pool.acquire()
        obj.value = 42
        pool.release(obj)
        obj2 = pool.acquire()
        self.assertEqual(0, obj2.value)


if __name__ == "__main__":
    unittest.main()
