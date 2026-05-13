"""Tests for ListDiffCalculator, ObjectPool, SceneTimeline, and FixedItemSource."""
import unittest

from gui_do.data.list_diff import (
    ListDiffCalculator,
    ListDiff,
    DiffInsert,
    DiffRemove,
)
from gui_do.data.object_pool import ObjectPool
from gui_do.scheduling.scene_timeline import SceneTimeline
from gui_do.data.virtual_item_source import FixedItemSource, VirtualItemSource


# ===========================================================================
# ListDiffCalculator
# ===========================================================================


class TestListDiff(unittest.TestCase):
    def test_identical_lists_empty_diff(self):
        d = ListDiffCalculator.diff(["a", "b", "c"], ["a", "b", "c"])
        self.assertTrue(d.is_empty)

    def test_remove_first_item(self):
        d = ListDiffCalculator.diff(["a", "b", "c"], ["b", "c"])
        self.assertEqual(1, len(d.removes))
        self.assertEqual("a", d.removes[0].item)

    def test_insert_at_end(self):
        d = ListDiffCalculator.diff(["a", "b"], ["a", "b", "c"])
        self.assertEqual(1, len(d.inserts))
        self.assertEqual("c", d.inserts[0].item)

    def test_complete_replacement(self):
        d = ListDiffCalculator.diff(["x", "y"], ["a", "b"])
        self.assertEqual(2, len(d.removes))
        self.assertEqual(2, len(d.inserts))

    def test_empty_old_all_inserts(self):
        d = ListDiffCalculator.diff([], ["a", "b"])
        self.assertEqual(2, len(d.inserts))
        self.assertEqual(0, len(d.removes))

    def test_empty_new_all_removes(self):
        d = ListDiffCalculator.diff(["a", "b"], [])
        self.assertEqual(2, len(d.removes))
        self.assertEqual(0, len(d.inserts))

    def test_both_empty_is_empty(self):
        d = ListDiffCalculator.diff([], [])
        self.assertTrue(d.is_empty)

    def test_key_fn_used_for_comparison(self):
        old = [{"id": 1, "name": "A"}, {"id": 2, "name": "B"}]
        new = [{"id": 2, "name": "B"}, {"id": 3, "name": "C"}]
        d = ListDiffCalculator.diff(old, new, key_fn=lambda x: x["id"])
        remove_ids = {r.item["id"] for r in d.removes}
        insert_ids = {i.item["id"] for i in d.inserts}
        self.assertIn(1, remove_ids)
        self.assertIn(3, insert_ids)

    def test_apply_to_list_remove(self):
        target = ["a", "b", "c"]
        d = ListDiffCalculator.diff(["a", "b", "c"], ["b", "c"])
        ListDiffCalculator.apply_to_list(target, d)
        self.assertEqual(["b", "c"], target)

    def test_apply_to_list_insert(self):
        target = ["a", "b"]
        d = ListDiffCalculator.diff(["a", "b"], ["a", "b", "z"])
        ListDiffCalculator.apply_to_list(target, d)
        self.assertEqual(["a", "b", "z"], target)

    def test_apply_to_list_replace_all(self):
        target = ["x", "y"]
        d = ListDiffCalculator.diff(["x", "y"], ["a", "b"])
        ListDiffCalculator.apply_to_list(target, d)
        self.assertEqual(["a", "b"], target)

    def test_is_empty_false_when_has_diff(self):
        d = ListDiffCalculator.diff(["a"], ["b"])
        self.assertFalse(d.is_empty)

    def test_diff_result_types(self):
        d = ListDiffCalculator.diff(["a", "b"], ["b", "c"])
        self.assertIsInstance(d, ListDiff)
        self.assertTrue(all(isinstance(r, DiffRemove) for r in d.removes))
        self.assertTrue(all(isinstance(i, DiffInsert) for i in d.inserts))


# ===========================================================================
# ObjectPool
# ===========================================================================


class TestObjectPool(unittest.TestCase):
    def _pool(self, **kw):
        counter = [0]

        def factory():
            counter[0] += 1
            return {"n": counter[0]}

        return ObjectPool(factory, **kw), counter

    def test_acquire_creates_new_when_empty(self):
        pool, counter = self._pool()
        obj = pool.acquire()
        self.assertIsNotNone(obj)
        self.assertEqual(1, counter[0])

    def test_release_then_acquire_reuses_object(self):
        pool, counter = self._pool()
        obj = pool.acquire()
        pool.release(obj)
        obj2 = pool.acquire()
        self.assertIs(obj, obj2)
        self.assertEqual(1, counter[0])  # no new allocation

    def test_stats_hits_increments_on_reuse(self):
        pool, _ = self._pool()
        obj = pool.acquire()
        pool.release(obj)
        pool.acquire()
        s = pool.stats()
        self.assertEqual(1, s["hits"])

    def test_stats_misses_increments_on_fresh(self):
        pool, _ = self._pool()
        pool.acquire()
        s = pool.stats()
        self.assertEqual(1, s["misses"])

    def test_stats_discards_when_pool_full(self):
        pool, _ = self._pool(max_size=1)
        a = pool.acquire()
        b = pool.acquire()
        pool.release(a)
        pool.release(b)  # pool full → discarded
        s = pool.stats()
        self.assertEqual(1, s["discards"])

    def test_reset_called_on_release(self):
        reset_log = []
        pool = ObjectPool(dict, reset=lambda o: reset_log.append(o))
        obj = pool.acquire()
        pool.release(obj)
        self.assertEqual([obj], reset_log)

    def test_preallocate_fills_pool(self):
        pool, _ = self._pool()
        pool.preallocate(5)
        s = pool.stats()
        self.assertEqual(5, s["size"])

    def test_preallocate_respects_max_size(self):
        pool, _ = self._pool(max_size=3)
        pool.preallocate(10)
        s = pool.stats()
        self.assertLessEqual(s["size"], 3)

    def test_clear_empties_pool(self):
        pool, _ = self._pool()
        pool.preallocate(4)
        pool.clear()
        s = pool.stats()
        self.assertEqual(0, s["size"])

    def test_max_size_property(self):
        pool, _ = self._pool(max_size=32)
        self.assertEqual(32, pool.max_size)

    def test_stats_returns_correct_keys(self):
        pool, _ = self._pool()
        s = pool.stats()
        self.assertIn("size", s)
        self.assertIn("hits", s)
        self.assertIn("misses", s)
        self.assertIn("discards", s)
        self.assertIn("max_size", s)


# ===========================================================================
# SceneTimeline
# ===========================================================================


class TestSceneTimeline(unittest.TestCase):
    def test_is_not_playing_initially(self):
        tl = SceneTimeline()
        self.assertFalse(tl.is_playing)

    def test_play_sets_playing(self):
        tl = SceneTimeline()
        tl.play()
        self.assertTrue(tl.is_playing)

    def test_pause_clears_playing(self):
        tl = SceneTimeline()
        tl.play()
        tl.pause()
        self.assertFalse(tl.is_playing)

    def test_update_does_not_advance_when_paused(self):
        tl = SceneTimeline()
        tl.update(1.0)
        self.assertAlmostEqual(0.0, tl.current_time)

    def test_update_advances_current_time(self):
        tl = SceneTimeline()
        tl.play()
        tl.update(0.5)
        self.assertAlmostEqual(0.5, tl.current_time)

    def test_at_fires_callback_at_given_time(self):
        fired = []
        tl = SceneTimeline()
        tl.at(1.0, lambda: fired.append(True))
        tl.play()
        tl.update(0.5)
        self.assertEqual([], fired)
        tl.update(0.6)
        self.assertEqual([True], fired)

    def test_at_fires_exactly_once(self):
        fired = []
        tl = SceneTimeline()
        tl.at(0.5, lambda: fired.append(True))
        tl.play()
        tl.update(1.0)
        tl.update(1.0)
        self.assertEqual([True], fired)

    def test_on_complete_fires_when_duration_reached(self):
        done = []
        tl = SceneTimeline(duration=1.0)
        tl.on_complete(lambda: done.append(True))
        tl.play()
        tl.update(1.5)
        self.assertEqual([True], done)
        self.assertFalse(tl.is_playing)

    def test_loop_every_fires_repeatedly(self):
        ticks = []
        tl = SceneTimeline()
        tl.loop_every(0.5, lambda: ticks.append(True))
        tl.play()
        tl.update(1.6)
        self.assertGreaterEqual(len(ticks), 3)

    def test_between_fires_on_enter_and_exit(self):
        enters = []
        exits = []
        tl = SceneTimeline(duration=2.0)
        tl.between(0.5, 1.5, on_enter=lambda: enters.append(True), on_exit=lambda: exits.append(True))
        tl.play()
        tl.update(0.6)  # inside
        self.assertEqual([True], enters)
        tl.update(1.0)  # exits
        self.assertEqual([True], exits)

    def test_label_and_seek_to_label(self):
        fired = []
        tl = SceneTimeline()
        tl.at(1.0, lambda: fired.append(True))
        tl.label("mid", t=0.5)
        tl.play()
        tl.seek_to_label("mid")
        tl.update(0.6)
        self.assertEqual([True], fired)

    def test_seek_forward_fires_events_in_range(self):
        fired = []
        tl = SceneTimeline()
        tl.at(1.0, lambda: fired.append(True))
        tl.seek(1.5)
        self.assertEqual([True], fired)

    def test_seek_backward_resets_fired_state(self):
        fired = []
        tl = SceneTimeline()
        tl.at(1.0, lambda: fired.append(True))
        tl.play()
        tl.update(1.5)  # fires event; auto-duration=1.0 so playback stops here
        tl.seek(0.0)    # backward seek clears fired state for t > 0.0
        tl.play()       # resume (stopped by duration completion)
        tl.update(1.5)  # should fire again
        self.assertEqual([True, True], fired)

    def test_reset_clears_time_and_fired(self):
        fired = []
        tl = SceneTimeline()
        tl.at(0.5, lambda: fired.append(True))
        tl.play()
        tl.update(1.0)
        tl.reset()
        tl.play()
        tl.update(1.0)
        self.assertEqual([True, True], fired)

    def test_duration_auto_computed_from_at(self):
        tl = SceneTimeline()
        tl.at(3.0, lambda: None)
        self.assertAlmostEqual(3.0, tl.duration)

    def test_explicit_duration_respected(self):
        tl = SceneTimeline(duration=5.0)
        self.assertAlmostEqual(5.0, tl.duration)

    def test_after_fires_relative_to_play_start(self):
        fired = []
        tl = SceneTimeline()
        tl.after(0.5, lambda: fired.append(True))
        tl.play()
        tl.update(0.3)
        self.assertEqual([], fired)
        tl.update(0.3)
        self.assertEqual([True], fired)

    def test_chaining_returns_self(self):
        tl = SceneTimeline()
        result = tl.at(1.0, lambda: None).on_complete(lambda: None)
        self.assertIs(tl, result)


# ===========================================================================
# FixedItemSource / VirtualItemSource
# ===========================================================================


class TestFixedItemSource(unittest.TestCase):
    def test_item_count_matches_initial_list(self):
        src = FixedItemSource(["a", "b", "c"])
        self.assertEqual(3, src.item_count())

    def test_item_at_returns_correct_item(self):
        src = FixedItemSource(["x", "y", "z"])
        self.assertEqual("y", src.item_at(1))

    def test_item_at_out_of_range_raises(self):
        src = FixedItemSource(["a"])
        with self.assertRaises(IndexError):
            src.item_at(5)

    def test_append_increases_count(self):
        src = FixedItemSource([1, 2])
        src.append(3)
        self.assertEqual(3, src.item_count())
        self.assertEqual(3, src.item_at(2))

    def test_insert_at_index(self):
        src = FixedItemSource([1, 3])
        src.insert(1, 2)
        self.assertEqual([1, 2, 3], src.snapshot())

    def test_remove_at_decrements_count(self):
        src = FixedItemSource([1, 2, 3])
        src.remove_at(1)
        self.assertEqual([1, 3], src.snapshot())

    def test_replace_item(self):
        src = FixedItemSource([1, 2, 3])
        src.replace(1, 99)
        self.assertEqual(99, src.item_at(1))

    def test_set_items_replaces_all(self):
        src = FixedItemSource([1, 2])
        src.set_items([10, 20, 30])
        self.assertEqual(3, src.item_count())

    def test_clear_empties_source(self):
        src = FixedItemSource([1, 2, 3])
        src.clear()
        self.assertEqual(0, src.item_count())

    def test_snapshot_returns_copy(self):
        src = FixedItemSource([1, 2])
        snap = src.snapshot()
        snap.append(99)
        self.assertEqual(2, src.item_count())

    def test_item_height_default_zero(self):
        src = FixedItemSource(["a"])
        self.assertEqual(0, src.item_height(0))

    def test_item_height_custom(self):
        src = FixedItemSource(["a", "b"], row_height=32)
        self.assertEqual(32, src.item_height(0))

    def test_empty_source_starts_empty(self):
        src = FixedItemSource()
        self.assertEqual(0, src.item_count())

    def test_satisfies_virtual_item_source_protocol(self):
        src = FixedItemSource([1, 2, 3])
        self.assertIsInstance(src, VirtualItemSource)


if __name__ == "__main__":
    unittest.main()
