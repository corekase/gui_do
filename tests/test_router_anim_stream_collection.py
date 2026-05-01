import unittest

from gui_do.state.router import Router, RouteEntry
from gui_do.scheduling.animation_sequence import AnimationSequence, AnimationHandle
from gui_do.scheduling.tween_manager import TweenManager, Easing
from gui_do.data.observable_stream import ObservableStream
from gui_do.data.collection_view import CollectionView, CollectionViewQuery


# ===========================================================================
# Router
# ===========================================================================


class TestRouter(unittest.TestCase):
    def setUp(self):
        self.r = Router()
        self.r.register("/home", "home_scene")
        self.r.register("/editor", "editor_scene")

    def test_scene_for_returns_scene_name(self):
        self.assertEqual("home_scene", self.r.scene_for("/home"))

    def test_scene_for_unknown_returns_none(self):
        self.assertIsNone(self.r.scene_for("/nope"))

    def test_push_appends_to_history(self):
        self.r.push("/home")
        self.assertEqual("/home", self.r.current_route)

    def test_push_returns_true_on_success(self):
        self.assertTrue(self.r.push("/home"))

    def test_push_records_params(self):
        self.r.push("/editor", {"id": 42})
        self.assertEqual({"id": 42}, self.r.current_params)

    def test_current_route_none_when_empty(self):
        self.assertIsNone(self.r.current_route)

    def test_current_params_empty_when_no_history(self):
        self.assertEqual({}, self.r.current_params)

    def test_history_grows_with_each_push(self):
        self.r.push("/home")
        self.r.push("/editor")
        self.assertEqual(2, len(self.r.history))

    def test_history_returns_copy(self):
        self.r.push("/home")
        h = self.r.history
        h.append("extra")
        self.assertEqual(1, len(self.r.history))

    def test_can_pop_false_when_single_entry(self):
        self.r.push("/home")
        self.assertFalse(self.r.can_pop())

    def test_can_pop_true_when_two_entries(self):
        self.r.push("/home")
        self.r.push("/editor")
        self.assertTrue(self.r.can_pop())

    def test_pop_navigates_back(self):
        self.r.push("/home")
        self.r.push("/editor")
        result = self.r.pop()
        self.assertTrue(result)
        self.assertEqual("/home", self.r.current_route)

    def test_pop_returns_false_when_history_too_short(self):
        self.r.push("/home")
        self.assertFalse(self.r.pop())

    def test_replace_swaps_current_entry(self):
        self.r.push("/home")
        self.r.replace("/editor")
        self.assertEqual("/editor", self.r.current_route)
        self.assertEqual(1, len(self.r.history))

    def test_replace_on_empty_history_creates_entry(self):
        self.r.replace("/home")
        self.assertEqual("/home", self.r.current_route)

    def test_on_route_change_fires_on_push(self):
        events = []
        self.r.on_route_change(events.append)
        self.r.push("/home")
        self.assertEqual(1, len(events))
        self.assertEqual("/home", events[0].route)

    def test_on_route_change_unsubscribe_stops_callbacks(self):
        events = []
        unsub = self.r.on_route_change(events.append)
        unsub()
        self.r.push("/home")
        self.assertEqual([], events)

    def test_guard_can_block_navigation(self):
        self.r.add_guard(lambda frm, to, p: False)
        result = self.r.push("/home")
        self.assertFalse(result)
        self.assertIsNone(self.r.current_route)

    def test_guard_allows_navigation_when_returning_true(self):
        self.r.add_guard(lambda frm, to, p: True)
        result = self.r.push("/home")
        self.assertTrue(result)

    def test_guard_receives_from_and_to_routes(self):
        calls = []
        self.r.add_guard(lambda frm, to, p: calls.append((frm, to)) or True)
        self.r.push("/home")
        self.r.push("/editor")
        self.assertEqual(("/home", "/editor"), calls[-1])

    def test_register_empty_route_raises(self):
        with self.assertRaises(ValueError):
            self.r.register("", "scene")

    def test_register_empty_scene_raises(self):
        with self.assertRaises(ValueError):
            self.r.register("/x", "")

    def test_add_guard_non_callable_raises(self):
        with self.assertRaises(ValueError):
            self.r.add_guard("not_callable")

    def test_on_route_change_non_callable_raises(self):
        with self.assertRaises(ValueError):
            self.r.on_route_change("not_callable")


# ===========================================================================
# AnimationSequence
# ===========================================================================


class _Obj:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class TestAnimationSequence(unittest.TestCase):
    def _mgr(self):
        return TweenManager()

    def test_then_returns_self_for_chaining(self):
        mgr = self._mgr()
        obj = _Obj(x=0.0)
        seq = AnimationSequence(mgr)
        result = seq.then(target=obj, attr="x", end_value=1.0, duration_seconds=1.0)
        self.assertIs(seq, result)

    def test_wait_returns_self_for_chaining(self):
        mgr = self._mgr()
        seq = AnimationSequence(mgr)
        self.assertIs(seq, seq.wait(0.1))

    def test_on_done_returns_self_for_chaining(self):
        mgr = self._mgr()
        seq = AnimationSequence(mgr)
        self.assertIs(seq, seq.on_done(lambda: None))

    def test_single_step_zero_duration_completes(self):
        mgr = self._mgr()
        obj = _Obj(x=0.0)
        done = []
        AnimationSequence(mgr).then(
            target=obj, attr="x", end_value=10.0, duration_seconds=0.0
        ).on_done(lambda: done.append(True)).start()
        self.assertEqual([True], done)
        self.assertAlmostEqual(10.0, obj.x)

    def test_sequential_steps_run_in_order(self):
        mgr = self._mgr()
        obj = _Obj(x=0.0, y=0.0)
        done = []
        AnimationSequence(mgr).then(
            target=obj, attr="x", end_value=5.0, duration_seconds=0.0
        ).then(
            target=obj, attr="y", end_value=7.0, duration_seconds=0.0
        ).on_done(lambda: done.append(True)).start()
        self.assertAlmostEqual(5.0, obj.x)
        self.assertAlmostEqual(7.0, obj.y)
        self.assertEqual([True], done)

    def test_parallel_group_starts_all_tweens(self):
        mgr = self._mgr()
        a = _Obj(x=0.0)
        b = _Obj(x=0.0)
        done = []
        AnimationSequence(mgr).parallel([
            dict(target=a, attr="x", end_value=1.0, duration_seconds=0.0),
            dict(target=b, attr="x", end_value=2.0, duration_seconds=0.0),
        ]).on_done(lambda: done.append(True)).start()
        self.assertAlmostEqual(1.0, a.x)
        self.assertAlmostEqual(2.0, b.x)
        self.assertEqual([True], done)

    def test_wait_zero_still_runs_next_step(self):
        mgr = self._mgr()
        obj = _Obj(x=0.0)
        done = []
        AnimationSequence(mgr).wait(0.0).then(
            target=obj, attr="x", end_value=3.0, duration_seconds=0.0
        ).on_done(lambda: done.append(True)).start()
        self.assertAlmostEqual(3.0, obj.x)
        self.assertEqual([True], done)

    def test_cancel_prevents_subsequent_steps(self):
        mgr = self._mgr()
        obj = _Obj(x=0.0, y=0.0)
        seq = AnimationSequence(mgr)
        seq.then(
            target=obj, attr="x", end_value=1.0, duration_seconds=1.0
        ).then(
            target=obj, attr="y", end_value=9.0, duration_seconds=0.0
        )
        handle = seq.start()
        handle.cancel()
        # Advance the first tween to completion; second step should not run
        mgr.update(2.0)
        self.assertAlmostEqual(0.0, obj.y)

    def test_start_returns_animation_handle(self):
        mgr = self._mgr()
        seq = AnimationSequence(mgr)
        h = seq.start()
        self.assertIsInstance(h, AnimationHandle)

    def test_animation_handle_cancelled_property(self):
        h = AnimationHandle()
        self.assertFalse(h.cancelled)
        h.cancel()
        self.assertTrue(h.cancelled)

    def test_on_done_fires_without_steps(self):
        mgr = self._mgr()
        done = []
        AnimationSequence(mgr).on_done(lambda: done.append(True)).start()
        self.assertEqual([True], done)

    def test_non_zero_duration_step_runs_via_update(self):
        mgr = self._mgr()
        obj = _Obj(x=0.0)
        done = []
        AnimationSequence(mgr).then(
            target=obj, attr="x", end_value=1.0, duration_seconds=0.5,
            easing=Easing.LINEAR
        ).on_done(lambda: done.append(True)).start()
        mgr.update(0.5)
        self.assertAlmostEqual(1.0, obj.x, places=3)
        self.assertEqual([True], done)


# ===========================================================================
# ObservableStream
# ===========================================================================


class _ManualSource:
    """Simple push source for testing."""

    def __init__(self):
        self._callbacks = []

    def subscribe(self, cb):
        self._callbacks.append(cb)
        return lambda: self._callbacks.remove(cb)

    def emit(self, value):
        for cb in list(self._callbacks):
            cb(value)


class TestObservableStream(unittest.TestCase):
    def test_subscribe_receives_emitted_values(self):
        src = _ManualSource()
        stream = ObservableStream(src)
        received = []
        stream.subscribe(received.append)
        src.emit(42)
        self.assertEqual([42], received)

    def test_unsubscribe_stops_delivery(self):
        src = _ManualSource()
        stream = ObservableStream(src)
        received = []
        unsub = stream.subscribe(received.append)
        unsub()
        src.emit(99)
        self.assertEqual([], received)

    def test_map_transforms_values(self):
        src = _ManualSource()
        stream = ObservableStream(src).map(lambda v: v * 2)
        received = []
        stream.subscribe(received.append)
        src.emit(5)
        self.assertEqual([10], received)

    def test_filter_suppresses_non_matching(self):
        src = _ManualSource()
        stream = ObservableStream(src).filter(lambda v: v > 3)
        received = []
        stream.subscribe(received.append)
        src.emit(2)
        src.emit(4)
        self.assertEqual([4], received)

    def test_distinct_until_changed_skips_repeat(self):
        src = _ManualSource()
        stream = ObservableStream(src).distinct_until_changed()
        received = []
        stream.subscribe(received.append)
        src.emit(1)
        src.emit(1)
        src.emit(2)
        self.assertEqual([1, 2], received)

    def test_merge_emits_from_both(self):
        src1 = _ManualSource()
        src2 = _ManualSource()
        stream = ObservableStream(src1).merge(ObservableStream(src2))
        received = []
        stream.subscribe(received.append)
        src1.emit("a")
        src2.emit("b")
        self.assertEqual(["a", "b"], received)

    def test_zip_emits_only_when_both_have_value(self):
        src1 = _ManualSource()
        src2 = _ManualSource()
        stream = ObservableStream(src1).zip(ObservableStream(src2))
        received = []
        stream.subscribe(received.append)
        src1.emit(1)
        self.assertEqual([], received)
        src2.emit(2)
        self.assertEqual([(1, 2)], received)

    def test_zip_consumes_buffers_in_order(self):
        src1 = _ManualSource()
        src2 = _ManualSource()
        stream = ObservableStream(src1).zip(ObservableStream(src2))
        received = []
        stream.subscribe(received.append)
        src1.emit(10)
        src1.emit(20)
        src2.emit(100)
        src2.emit(200)
        self.assertEqual([(10, 100), (20, 200)], received)

    def test_take_stops_after_n(self):
        src = _ManualSource()
        stream = ObservableStream(src).take(2)
        received = []
        stream.subscribe(received.append)
        src.emit(1)
        src.emit(2)
        src.emit(3)
        self.assertEqual([1, 2], received)

    def test_pairwise_emits_pairs(self):
        src = _ManualSource()
        stream = ObservableStream(src).pairwise()
        received = []
        stream.subscribe(received.append)
        src.emit(1)
        src.emit(2)
        src.emit(3)
        self.assertEqual([(1, 2), (2, 3)], received)

    def test_pairwise_skips_first_emission(self):
        src = _ManualSource()
        stream = ObservableStream(src).pairwise()
        received = []
        stream.subscribe(received.append)
        src.emit("only")
        self.assertEqual([], received)

    def test_take_until_stops_on_stop_signal(self):
        src = _ManualSource()
        stop = _ManualSource()
        stream = ObservableStream(src).take_until(ObservableStream(stop))
        received = []
        stream.subscribe(received.append)
        src.emit(1)
        stop.emit(None)
        src.emit(2)
        self.assertEqual([1], received)

    def test_of_constructor_emits_synchronously(self):
        received = []
        ObservableStream.of(10, 20, 30).subscribe(received.append)
        self.assertEqual([10, 20, 30], received)

    def test_map_then_filter_pipeline(self):
        src = _ManualSource()
        stream = ObservableStream(src).map(lambda v: v * 3).filter(lambda v: v > 5)
        received = []
        stream.subscribe(received.append)
        src.emit(1)  # → 3, filtered out
        src.emit(2)  # → 6, passes
        self.assertEqual([6], received)

    def test_invalid_source_raises(self):
        with self.assertRaises(TypeError):
            ObservableStream(42)


# ===========================================================================
# CollectionView
# ===========================================================================


class TestCollectionView(unittest.TestCase):
    def test_items_returns_all_source_items(self):
        cv = CollectionView([1, 2, 3])
        self.assertEqual([1, 2, 3], cv.items)

    def test_count_matches_items_length(self):
        cv = CollectionView([1, 2])
        self.assertEqual(2, cv.count())

    def test_add_filter_removes_non_matching(self):
        cv = CollectionView([1, 2, 3, 4])
        cv.add_filter(lambda x: x % 2 == 0)
        self.assertEqual([2, 4], cv.items)

    def test_clear_filters_restores_all_items(self):
        cv = CollectionView([1, 2, 3])
        cv.add_filter(lambda x: x > 1)
        cv.clear_filters()
        self.assertEqual([1, 2, 3], cv.items)

    def test_set_sort_sorts_items(self):
        cv = CollectionView([3, 1, 2])
        cv.set_sort(lambda x: x)
        self.assertEqual([1, 2, 3], cv.items)

    def test_set_sort_reverse(self):
        cv = CollectionView([3, 1, 2])
        cv.set_sort(lambda x: x, reverse=True)
        self.assertEqual([3, 2, 1], cv.items)

    def test_set_sort_none_removes_sort(self):
        cv = CollectionView([3, 1, 2])
        cv.set_sort(lambda x: x)
        cv.set_sort(None)
        self.assertEqual([3, 1, 2], cv.items)

    def test_set_projector_transforms_items(self):
        cv = CollectionView([1, 2, 3])
        cv.set_projector(lambda x: x * 10)
        self.assertEqual([10, 20, 30], cv.items)

    def test_set_projector_none_removes_projection(self):
        cv = CollectionView([1, 2])
        cv.set_projector(lambda x: x * 10)
        cv.set_projector(None)
        self.assertEqual([1, 2], cv.items)

    def test_set_source_replaces_data(self):
        cv = CollectionView([1, 2])
        cv.set_source([10, 20, 30])
        self.assertEqual([10, 20, 30], cv.items)

    def test_callable_source_is_called_each_refresh(self):
        data = [1, 2]
        cv = CollectionView(lambda: data)
        data.append(3)
        cv.refresh()
        self.assertEqual([1, 2, 3], cv.items)

    def test_subscribe_fires_on_refresh(self):
        cv = CollectionView([1])
        calls = []
        cv.subscribe(lambda: calls.append(True))
        cv.refresh()
        self.assertEqual([True], calls)

    def test_unsubscribe_stops_callbacks(self):
        cv = CollectionView([1])
        calls = []
        unsub = cv.subscribe(lambda: calls.append(True))
        unsub()
        cv.refresh()
        self.assertEqual([], calls)

    def test_multiple_filters_applied_in_order(self):
        cv = CollectionView([1, 2, 3, 4, 5])
        cv.add_filter(lambda x: x > 1)  # removes 1
        cv.add_filter(lambda x: x < 5)  # removes 5
        self.assertEqual([2, 3, 4], cv.items)

    def test_snapshot_is_alias_for_items(self):
        cv = CollectionView([7, 8])
        self.assertEqual(cv.items, cv.snapshot())

    def test_refresh_returns_items(self):
        cv = CollectionView([1, 2, 3])
        result = cv.refresh()
        self.assertEqual([1, 2, 3], result)

    def test_query_accessible_via_property(self):
        q = CollectionViewQuery()
        cv = CollectionView([1], query=q)
        self.assertIs(q, cv.query)

    def test_filter_sort_project_combined(self):
        cv = CollectionView([5, 1, 3, 2, 4])
        cv.add_filter(lambda x: x % 2 != 0)  # keep odds: 5, 1, 3
        cv.set_sort(lambda x: x)             # sort: 1, 3, 5
        cv.set_projector(lambda x: x * 100)  # project: 100, 300, 500
        self.assertEqual([100, 300, 500], cv.items)


if __name__ == "__main__":
    unittest.main()
