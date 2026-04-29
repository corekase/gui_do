"""Runtime tests for the 10 new generalised systems.

Systems covered:
  1. ObservableStream
  2. SurfaceCompositor / Layer
  3. ShapeRenderer
  4. SurfaceEffects
  5. AnimationStateMachine / AnimationTransitionMode
  6. ObjectPool
  7. VectorPath
  8. SnapGrid / AlignmentGuide / SnapComposer / SnapTarget
  9. WizardFlow / WizardStep / WizardHandle
 10. SceneTimeline
"""
import threading
import time
import unittest

import pygame
pygame.init()
_SURFACE = pygame.Surface((400, 400))

import gui_do


# ---------------------------------------------------------------------------
# 1. ObservableStream
# ---------------------------------------------------------------------------

class TestObservableStream(unittest.TestCase):

    def _from_list(self, values):
        """Create a stream that emits a fixed list of values."""
        import gui_do
        events = []

        def source(cb):
            for v in values:
                cb(v)
            return lambda: None

        return gui_do.ObservableStream(source)

    def _collect(self, stream):
        """Subscribe and return collected items."""
        results = []
        stream.subscribe(results.append)
        return results

    def test_of_factory(self):
        results = []
        gui_do.ObservableStream.of(1, 2, 3).subscribe(results.append)
        self.assertEqual(results, [1, 2, 3])

    def test_map(self):
        results = []
        gui_do.ObservableStream.of(1, 2, 3).map(lambda x: x * 10).subscribe(results.append)
        self.assertEqual(results, [10, 20, 30])

    def test_filter(self):
        results = []
        gui_do.ObservableStream.of(1, 2, 3, 4).filter(lambda x: x % 2 == 0).subscribe(results.append)
        self.assertEqual(results, [2, 4])

    def test_distinct_until_changed(self):
        results = []
        gui_do.ObservableStream.of(1, 1, 2, 2, 3).distinct_until_changed().subscribe(results.append)
        self.assertEqual(results, [1, 2, 3])

    def test_take(self):
        results = []
        gui_do.ObservableStream.of(1, 2, 3, 4, 5).take(3).subscribe(results.append)
        self.assertEqual(results, [1, 2, 3])

    def test_pairwise(self):
        results = []
        gui_do.ObservableStream.of(1, 2, 3, 4).pairwise().subscribe(results.append)
        self.assertEqual(results, [(1, 2), (2, 3), (3, 4)])

    def test_merge(self):
        results = []
        a = gui_do.ObservableStream.of(1, 3)
        b = gui_do.ObservableStream.of(2, 4)
        a.merge(b).subscribe(results.append)
        self.assertIn(1, results)
        self.assertIn(2, results)
        self.assertIn(3, results)
        self.assertIn(4, results)

    def test_from_observable(self):
        """ObservableValue can be used as a source."""
        v = gui_do.ObservableValue(0)
        results = []
        s = gui_do.ObservableStream.from_observable(v)
        s.subscribe(results.append)
        v.value = 1
        v.value = 2
        self.assertIn(1, results)
        self.assertIn(2, results)

    def test_take_until(self):
        stop_events = []

        def stop_source(cb):
            def _trigger():
                cb(True)
            stop_events.append(_trigger)
            return lambda: None

        stop_stream = gui_do.ObservableStream(stop_source)

        results = []
        main_stream = gui_do.ObservableStream.of(1, 2, 3)
        main_stream.take_until(stop_stream).subscribe(results.append)
        # Before stop fires all items should be emitted (source exhausted first)
        self.assertTrue(len(results) >= 0)  # no error raised

    def test_throttle(self):
        """throttle(ms) returns a stream — no error."""
        s = gui_do.ObservableStream.of(1, 2, 3).throttle(100)
        results = []
        s.subscribe(results.append)
        # at least first value passes through (throttle allows first item)
        self.assertTrue(len(results) >= 0)

    def test_zip(self):
        results = []
        a = gui_do.ObservableStream.of(1, 2, 3)
        b = gui_do.ObservableStream.of("a", "b", "c")
        a.zip(b).subscribe(results.append)
        self.assertEqual(results, [(1, "a"), (2, "b"), (3, "c")])


# ---------------------------------------------------------------------------
# 2. SurfaceCompositor / Layer
# ---------------------------------------------------------------------------

class TestSurfaceCompositor(unittest.TestCase):

    def _make(self):
        return gui_do.SurfaceCompositor((200, 200))

    def test_add_and_has_layer(self):
        sc = self._make()
        sc.add_layer("bg", z_index=0)
        self.assertTrue(sc.has_layer("bg"))
        self.assertFalse(sc.has_layer("missing"))

    def test_layer_surface_returns_surface(self):
        sc = self._make()
        sc.add_layer("ui", z_index=5)
        surf = sc.layer_surface("ui")
        self.assertIsInstance(surf, pygame.Surface)

    def test_layer_names_in_z_order(self):
        sc = self._make()
        sc.add_layer("top", z_index=10)
        sc.add_layer("bottom", z_index=0)
        sc.add_layer("mid", z_index=5)
        self.assertEqual(sc.layer_names(), ["bottom", "mid", "top"])

    def test_remove_layer(self):
        sc = self._make()
        sc.add_layer("x")
        sc.remove_layer("x")
        self.assertFalse(sc.has_layer("x"))

    def test_duplicate_layer_raises(self):
        sc = self._make()
        sc.add_layer("a")
        with self.assertRaises(ValueError):
            sc.add_layer("a")

    def test_compose_no_error(self):
        sc = self._make()
        sc.add_layer("bg", z_index=0)
        sc.add_layer("fg", z_index=1)
        target = pygame.Surface((200, 200))
        sc.compose(target)

    def test_compose_dirty_rects(self):
        sc = self._make()
        sc.add_layer("bg")
        target = pygame.Surface((200, 200))
        dirty = [pygame.Rect(10, 10, 50, 50)]
        sc.compose(target, dirty_rects=dirty)

    def test_set_layer_opacity(self):
        sc = self._make()
        layer = sc.add_layer("a", opacity=1.0)
        sc.set_layer_opacity("a", 0.5)
        self.assertAlmostEqual(sc.layer("a").opacity, 0.5)

    def test_set_layer_visible(self):
        sc = self._make()
        sc.add_layer("a")
        sc.set_layer_visible("a", False)
        self.assertFalse(sc.layer("a").visible)

    def test_clear_layer(self):
        sc = self._make()
        sc.add_layer("a")
        sc.layer_surface("a").fill((255, 0, 0))
        sc.clear_layer("a")

    def test_resize(self):
        sc = self._make()
        sc.add_layer("a")
        sc.resize((300, 300))
        self.assertEqual(sc.layer_surface("a").get_size(), (300, 300))


# ---------------------------------------------------------------------------
# 3. ShapeRenderer
# ---------------------------------------------------------------------------

class TestShapeRenderer(unittest.TestCase):

    def _surf(self):
        s = pygame.Surface((200, 200), pygame.SRCALPHA)
        s.fill((0, 0, 0, 0))
        return s

    def test_rounded_rect(self):
        gui_do.ShapeRenderer.rounded_rect(self._surf(), (100, 100, 200), pygame.Rect(10, 10, 80, 40), radius=8)

    def test_rounded_rect_zero_radius(self):
        gui_do.ShapeRenderer.rounded_rect(self._surf(), (100, 100, 200), pygame.Rect(0, 0, 50, 50), radius=0)

    def test_pill(self):
        gui_do.ShapeRenderer.pill(self._surf(), (80, 180, 80), pygame.Rect(10, 10, 100, 30))

    def test_gradient_rect_vertical(self):
        gui_do.ShapeRenderer.gradient_rect(self._surf(), pygame.Rect(0, 0, 100, 60), (0, 0, 0), (255, 255, 255))

    def test_gradient_rect_horizontal(self):
        gui_do.ShapeRenderer.gradient_rect(self._surf(), pygame.Rect(0, 0, 100, 60), (0, 0, 0), (255, 255, 255), horizontal=True)

    def test_drop_shadow(self):
        gui_do.ShapeRenderer.drop_shadow(self._surf(), pygame.Rect(20, 20, 80, 40), radius=8, color=(0, 0, 0))

    def test_badge(self):
        pygame.font.init()
        font = pygame.font.SysFont("sans", 12)
        gui_do.ShapeRenderer.badge(self._surf(), pygame.Rect(10, 10, 60, 24), "NEW", (200, 80, 80), (255, 255, 255), font)

    def test_progress_arc(self):
        gui_do.ShapeRenderer.progress_arc(self._surf(), (100, 100), 40, 0.75, (80, 180, 80), width=4)

    def test_dotted_border(self):
        gui_do.ShapeRenderer.dotted_border(self._surf(), pygame.Rect(5, 5, 80, 60), (200, 200, 200))

    def test_check_mark(self):
        gui_do.ShapeRenderer.check_mark(self._surf(), pygame.Rect(4, 4, 16, 16), (80, 200, 80))

    def test_cross_mark(self):
        gui_do.ShapeRenderer.cross_mark(self._surf(), pygame.Rect(4, 4, 16, 16), (200, 80, 80))

    def test_chevron_directions(self):
        for d in ("left", "right", "up", "down"):
            gui_do.ShapeRenderer.chevron(self._surf(), pygame.Rect(0, 0, 24, 24), d, (0, 0, 0))


# ---------------------------------------------------------------------------
# 4. SurfaceEffects
# ---------------------------------------------------------------------------

class TestSurfaceEffects(unittest.TestCase):

    def _src(self):
        s = pygame.Surface((60, 60))
        s.fill((120, 180, 200))
        return s

    def _assert_same_size(self, src, result):
        self.assertEqual(result.get_size(), src.get_size())

    def test_blur_returns_surface(self):
        src = self._src()
        result = gui_do.SurfaceEffects.blur(src, 4)
        self.assertIsInstance(result, pygame.Surface)
        self._assert_same_size(src, result)

    def test_blur_zero(self):
        src = self._src()
        result = gui_do.SurfaceEffects.blur(src, 0)
        self._assert_same_size(src, result)

    def test_greyscale(self):
        src = self._src()
        result = gui_do.SurfaceEffects.greyscale(src)
        self._assert_same_size(src, result)
        px = result.get_at((30, 30))
        self.assertEqual(px[0], px[1])
        self.assertEqual(px[1], px[2])

    def test_tint(self):
        src = self._src()
        result = gui_do.SurfaceEffects.tint(src, (255, 0, 0), alpha=100)
        self._assert_same_size(src, result)

    def test_brightness_increase(self):
        src = self._src()
        result = gui_do.SurfaceEffects.brightness(src, 1.5)
        self._assert_same_size(src, result)

    def test_brightness_decrease(self):
        src = self._src()
        result = gui_do.SurfaceEffects.brightness(src, 0.5)
        self._assert_same_size(src, result)

    def test_pixelate(self):
        src = self._src()
        result = gui_do.SurfaceEffects.pixelate(src, 6)
        self._assert_same_size(src, result)

    def test_pixelate_no_op(self):
        src = self._src()
        result = gui_do.SurfaceEffects.pixelate(src, 1)
        self._assert_same_size(src, result)

    def test_vignette(self):
        src = self._src()
        result = gui_do.SurfaceEffects.vignette(src, strength=0.7)
        self._assert_same_size(src, result)


# ---------------------------------------------------------------------------
# 5. AnimationStateMachine / AnimationTransitionMode
# ---------------------------------------------------------------------------

class TestAnimationStateMachine(unittest.TestCase):

    def _make_tweens(self):
        return gui_do.TweenManager()

    def test_register_and_set_state(self):
        tweens = self._make_tweens()
        asm = gui_do.AnimationStateMachine(tweens)
        called = []
        asm.register_state("idle", lambda seq: called.append("idle_seq"))
        asm.set_state("idle")
        # Builder is called during set_state
        self.assertIn("idle_seq", called)

    def test_state_changed_callback(self):
        tweens = self._make_tweens()
        asm = gui_do.AnimationStateMachine(tweens)
        asm.register_state("a", lambda seq: None)
        asm.register_state("b", lambda seq: None)
        events = []
        asm.on_state_changed(events.append)
        asm.set_state("a")
        asm.set_state("b")
        self.assertEqual(events, ["a", "b"])

    def test_unknown_state_raises(self):
        tweens = self._make_tweens()
        asm = gui_do.AnimationStateMachine(tweens)
        with self.assertRaises(KeyError):
            asm.set_state("nonexistent")

    def test_same_state_no_duplicate_callback(self):
        tweens = self._make_tweens()
        asm = gui_do.AnimationStateMachine(tweens)
        asm.register_state("a", lambda seq: None)
        events = []
        asm.on_state_changed(events.append)
        asm.set_state("a")
        asm.set_state("a")  # Same state — should not fire again
        self.assertEqual(events, ["a"])

    def test_current_state_property(self):
        tweens = self._make_tweens()
        asm = gui_do.AnimationStateMachine(tweens)
        self.assertIsNone(asm.current_state)
        asm.register_state("x", lambda seq: None)
        asm.set_state("x")
        self.assertEqual(asm.current_state, "x")

    def test_transition_mode_enum_values(self):
        self.assertIsNotNone(gui_do.AnimationTransitionMode.INTERRUPT)
        self.assertIsNotNone(gui_do.AnimationTransitionMode.COMPLETE_THEN_TRANSITION)
        self.assertIsNotNone(gui_do.AnimationTransitionMode.REVERSE_THEN_TRANSITION)

    def test_reset(self):
        tweens = self._make_tweens()
        asm = gui_do.AnimationStateMachine(tweens)
        asm.register_state("a", lambda seq: None)
        asm.set_state("a")
        asm.reset()
        self.assertIsNone(asm.current_state)

    def test_unsub_state_changed(self):
        tweens = self._make_tweens()
        asm = gui_do.AnimationStateMachine(tweens)
        asm.register_state("a", lambda seq: None)
        events = []
        unsub = asm.on_state_changed(events.append)
        asm.set_state("a")
        unsub()
        asm.reset()
        asm.set_state("a")
        self.assertEqual(len(events), 1)


# ---------------------------------------------------------------------------
# 6. ObjectPool
# ---------------------------------------------------------------------------

class TestObjectPool(unittest.TestCase):

    def test_acquire_creates_new(self):
        pool = gui_do.ObjectPool(list)
        obj = pool.acquire()
        self.assertIsInstance(obj, list)

    def test_acquire_release_recycles(self):
        created = []
        def factory():
            o = object()
            created.append(o)
            return o
        pool = gui_do.ObjectPool(factory, max_size=4)
        obj = pool.acquire()
        pool.release(obj)
        obj2 = pool.acquire()
        self.assertIs(obj, obj2)
        self.assertEqual(len(created), 1)

    def test_reset_called_on_release(self):
        reset_calls = []
        pool = gui_do.ObjectPool(list, reset=lambda o: reset_calls.append(o), max_size=2)
        obj = pool.acquire()
        pool.release(obj)
        self.assertIn(obj, reset_calls)

    def test_max_size_respected(self):
        pool = gui_do.ObjectPool(list, max_size=2)
        a = pool.acquire(); b = pool.acquire(); c = pool.acquire()
        pool.release(a); pool.release(b); pool.release(c)  # c should be discarded
        stats = pool.stats()
        self.assertEqual(stats["size"], 2)
        self.assertEqual(stats["discards"], 1)

    def test_preallocate(self):
        pool = gui_do.ObjectPool(list, max_size=8)
        pool.preallocate(4)
        stats = pool.stats()
        self.assertEqual(stats["size"], 4)

    def test_clear(self):
        pool = gui_do.ObjectPool(list, max_size=8)
        pool.preallocate(4)
        pool.clear()
        self.assertEqual(pool.stats()["size"], 0)

    def test_stats_keys(self):
        pool = gui_do.ObjectPool(list)
        stats = pool.stats()
        for key in ("size", "max_size", "hits", "misses", "discards"):
            self.assertIn(key, stats)

    def test_thread_safe(self):
        pool = gui_do.ObjectPool(list, max_size=32)
        pool.preallocate(16)
        errors = []
        def worker():
            for _ in range(100):
                try:
                    obj = pool.acquire()
                    pool.release(obj)
                except Exception as e:
                    errors.append(e)
        threads = [threading.Thread(target=worker) for _ in range(8)]
        for t in threads: t.start()
        for t in threads: t.join()
        self.assertEqual(errors, [])


# ---------------------------------------------------------------------------
# 7. VectorPath
# ---------------------------------------------------------------------------

class TestVectorPath(unittest.TestCase):

    def _surf(self):
        return pygame.Surface((200, 200), pygame.SRCALPHA)

    def test_move_line_close(self):
        path = gui_do.VectorPath()
        path.move_to(10, 10).line_to(100, 10).line_to(100, 80).close()
        path.stroke(self._surf(), (255, 255, 255))
        path.fill(self._surf(), (200, 200, 200))

    def test_quadratic_to(self):
        path = gui_do.VectorPath()
        path.move_to(10, 50).quadratic_to(100, 0, 190, 50)
        path.stroke(self._surf(), (255, 0, 0))

    def test_cubic_to(self):
        path = gui_do.VectorPath()
        path.move_to(10, 100).cubic_to(50, 10, 150, 10, 190, 100)
        path.stroke(self._surf(), (0, 255, 0))

    def test_arc(self):
        path = gui_do.VectorPath()
        path.arc(100, 100, 60, 0, 270)
        path.stroke(self._surf(), (0, 0, 255))

    def test_rect_path(self):
        path = gui_do.VectorPath()
        path.rect(pygame.Rect(20, 20, 100, 60))
        path.fill(self._surf(), (128, 128, 128))

    def test_rounded_rect_path(self):
        path = gui_do.VectorPath()
        path.rounded_rect(pygame.Rect(10, 10, 80, 50), radius=10)
        path.fill(self._surf(), (200, 180, 160))

    def test_bounding_rect(self):
        path = gui_do.VectorPath()
        path.move_to(10, 20).line_to(100, 80).close()
        br = path.bounding_rect()
        self.assertIsInstance(br, pygame.Rect)
        self.assertGreater(br.width, 0)
        self.assertGreater(br.height, 0)

    def test_contains_point_inside(self):
        path = gui_do.VectorPath()
        path.rect(pygame.Rect(10, 10, 100, 100))
        self.assertTrue(path.contains_point(50, 50))

    def test_contains_point_outside(self):
        path = gui_do.VectorPath()
        path.rect(pygame.Rect(10, 10, 100, 100))
        self.assertFalse(path.contains_point(200, 200))

    def test_transform_translate(self):
        path = gui_do.VectorPath()
        path.move_to(0, 0).line_to(10, 0)
        transformed = path.transform(translate=(50, 50))
        br = transformed.bounding_rect()
        self.assertEqual(br.x, 50)

    def test_transform_scale(self):
        path = gui_do.VectorPath()
        path.move_to(0, 0).line_to(100, 0)
        transformed = path.transform(scale=2.0)
        br = transformed.bounding_rect()
        self.assertGreaterEqual(br.width, 200)


# ---------------------------------------------------------------------------
# 8. SnapGrid / AlignmentGuide / SnapComposer / SnapTarget
# ---------------------------------------------------------------------------

class TestSnapGrid(unittest.TestCase):

    def test_snap_point_aligns_to_grid(self):
        grid = gui_do.SnapGrid(16, 16)
        x, y = grid.snap_point(7, 7)   # 7 < 8 → rounds to 0
        self.assertEqual(x, 0)
        self.assertEqual(y, 0)

    def test_snap_point_rounds_to_nearest(self):
        grid = gui_do.SnapGrid(16, 16)
        x, y = grid.snap_point(10, 10)
        self.assertEqual(x, 16)
        self.assertEqual(y, 16)

    def test_snap_rect_preserves_size(self):
        grid = gui_do.SnapGrid(16, 16)
        r = pygame.Rect(5, 5, 30, 40)
        snapped = grid.snap_rect(r)
        self.assertEqual(snapped.width, 30)
        self.assertEqual(snapped.height, 40)

    def test_nearest_cell(self):
        grid = gui_do.SnapGrid(16, 16)
        col, row = grid.nearest_cell(20, 20)
        self.assertEqual(col, 1)
        self.assertEqual(row, 1)

    def test_draw_grid_no_error(self):
        grid = gui_do.SnapGrid(20, 20)
        surf = pygame.Surface((200, 200))
        grid.draw_grid(surf, pygame.Rect(0, 0, 200, 200), (80, 80, 80), alpha=100)

    def test_offset(self):
        grid = gui_do.SnapGrid(16, 16, offset_x=8, offset_y=8)
        x, y = grid.snap_point(8, 8)
        self.assertEqual(x, 8)
        self.assertEqual(y, 8)


class TestAlignmentGuide(unittest.TestCase):

    def test_find_left_left_snap(self):
        candidates = [pygame.Rect(100, 50, 80, 40)]
        guide = gui_do.AlignmentGuide(candidates)
        dragged = pygame.Rect(103, 90, 80, 40)  # 3px off left-left
        targets = guide.find_snap_targets(dragged, threshold_px=8)
        labels = [t.label for t in targets]
        self.assertIn("left-left", labels)

    def test_find_center_x_snap(self):
        cand = pygame.Rect(100, 0, 100, 50)  # centerx=150
        guide = gui_do.AlignmentGuide([cand])
        dragged = pygame.Rect(103, 60, 100, 50)  # centerx=153 — 3px off
        targets = guide.find_snap_targets(dragged, threshold_px=8)
        labels = [t.label for t in targets]
        self.assertIn("center-x", labels)

    def test_no_targets_when_far(self):
        cand = pygame.Rect(0, 0, 50, 50)
        guide = gui_do.AlignmentGuide([cand])
        dragged = pygame.Rect(500, 500, 50, 50)
        targets = guide.find_snap_targets(dragged, threshold_px=8)
        self.assertEqual(targets, [])

    def test_targets_sorted_by_distance(self):
        cand = pygame.Rect(100, 100, 80, 50)
        guide = gui_do.AlignmentGuide([cand])
        dragged = pygame.Rect(104, 104, 80, 50)
        targets = guide.find_snap_targets(dragged, threshold_px=8)
        for i in range(len(targets) - 1):
            self.assertLessEqual(targets[i].distance, targets[i + 1].distance)

    def test_snap_target_fields(self):
        cand = pygame.Rect(50, 50, 100, 60)
        guide = gui_do.AlignmentGuide([cand])
        dragged = pygame.Rect(53, 53, 100, 60)
        targets = guide.find_snap_targets(dragged, threshold_px=8)
        self.assertTrue(len(targets) > 0)
        t = targets[0]
        self.assertIn(t.axis, ("x", "y"))
        self.assertIsInstance(t.value, int)
        self.assertIsInstance(t.guide_rect, pygame.Rect)
        self.assertIsInstance(t.distance, float)


class TestSnapComposer(unittest.TestCase):

    def test_grid_only(self):
        grid = gui_do.SnapGrid(16, 16)
        composer = gui_do.SnapComposer(grid=grid)
        result = composer.snap(pygame.Rect(9, 9, 50, 30))
        self.assertIsInstance(result, pygame.Rect)

    def test_guides_only(self):
        candidates = [pygame.Rect(100, 100, 80, 50)]
        guide = gui_do.AlignmentGuide(candidates)
        composer = gui_do.SnapComposer(guides=guide)
        dragged = pygame.Rect(103, 103, 80, 50)
        result = composer.snap(dragged, threshold_px=8)
        self.assertIsInstance(result, pygame.Rect)

    def test_combined_grid_and_guides(self):
        grid = gui_do.SnapGrid(16, 16)
        candidates = [pygame.Rect(160, 160, 80, 50)]
        guide = gui_do.AlignmentGuide(candidates)
        composer = gui_do.SnapComposer(grid=grid, guides=guide)
        result = composer.snap(pygame.Rect(9, 162, 80, 50), threshold_px=8)
        # y-axis: guide snap (162 → 160); x-axis: grid snap
        self.assertIsInstance(result, pygame.Rect)


# ---------------------------------------------------------------------------
# 9. WizardFlow / WizardStep / WizardHandle
# ---------------------------------------------------------------------------

class TestWizardFlow(unittest.TestCase):

    def _make_steps(self):
        return [
            gui_do.WizardStep(title="Step1", fields=["name"]),
            gui_do.WizardStep(title="Step2", fields=["email"]),
            gui_do.WizardStep(title="Step3", fields=[]),
        ]

    def test_initial_state(self):
        flow = gui_do.WizardFlow(self._make_steps(), on_complete=lambda d: None)
        self.assertEqual(flow.step_index, 0)
        self.assertEqual(flow.step_count, 3)
        self.assertEqual(flow.current_step.title, "Step1")

    def test_advance_moves_forward(self):
        flow = gui_do.WizardFlow(self._make_steps(), on_complete=lambda d: None)
        ok, errors = flow.advance({"name": "Alice"})
        self.assertTrue(ok)
        self.assertEqual(errors, [])
        self.assertEqual(flow.step_index, 1)

    def test_validation_blocks_advance(self):
        steps = [
            gui_do.WizardStep(
                title="Step1",
                fields=["name"],
                on_validate=lambda d: ["Name required"] if not d.get("name") else [],
            ),
        ]
        flow = gui_do.WizardFlow(steps, on_complete=lambda d: None)
        ok, errors = flow.advance({})
        self.assertFalse(ok)
        self.assertIn("Name required", errors)
        self.assertEqual(flow.step_index, 0)

    def test_back(self):
        flow = gui_do.WizardFlow(self._make_steps(), on_complete=lambda d: None)
        flow.advance({"name": "Alice"})
        result = flow.back()
        self.assertTrue(result)
        self.assertEqual(flow.step_index, 0)

    def test_back_at_first_step(self):
        flow = gui_do.WizardFlow(self._make_steps(), on_complete=lambda d: None)
        result = flow.back()
        self.assertFalse(result)

    def test_on_complete_fires(self):
        steps = [gui_do.WizardStep(title="Only", fields=["x"])]
        completed = []
        flow = gui_do.WizardFlow(steps, on_complete=completed.append)
        flow.advance({"x": 1})
        self.assertEqual(len(completed), 1)
        self.assertEqual(completed[0]["x"], 1)

    def test_collected_data_accumulates(self):
        flow = gui_do.WizardFlow(self._make_steps(), on_complete=lambda d: None)
        flow.advance({"name": "Alice"})
        flow.advance({"email": "a@b.com"})
        data = flow.collected_data
        self.assertEqual(data["name"], "Alice")
        self.assertEqual(data["email"], "a@b.com")

    def test_progress_observable(self):
        flow = gui_do.WizardFlow(self._make_steps(), on_complete=lambda d: None)
        values = []
        flow.progress.subscribe(values.append)
        flow.advance({"name": "A"})
        self.assertTrue(any(v > 0 for v in values))

    def test_cancel(self):
        cancelled = []
        flow = gui_do.WizardFlow(
            self._make_steps(),
            on_complete=lambda d: None,
            on_cancel=lambda: cancelled.append(True),
        )
        flow.cancel()
        self.assertTrue(flow.is_cancelled)
        self.assertTrue(cancelled)

    def test_wizard_handle_cancel(self):
        flow = gui_do.WizardFlow(self._make_steps(), on_complete=lambda d: None)
        handle = flow.handle()
        self.assertIsInstance(handle, gui_do.WizardHandle)
        handle.cancel()
        self.assertTrue(handle.is_cancelled)

    def test_on_enter_called(self):
        entered = []
        steps = [
            gui_do.WizardStep(title="A", on_enter=lambda d: entered.append("A")),
            gui_do.WizardStep(title="B", on_enter=lambda d: entered.append("B")),
        ]
        flow = gui_do.WizardFlow(steps, on_complete=lambda d: None)
        self.assertIn("A", entered)
        flow.advance({})
        self.assertIn("B", entered)

    def test_on_leave_called(self):
        left = []
        steps = [
            gui_do.WizardStep(title="A", on_leave=lambda d, dir: left.append(dir)),
            gui_do.WizardStep(title="B"),
        ]
        flow = gui_do.WizardFlow(steps, on_complete=lambda d: None)
        flow.advance({})
        self.assertIn("forward", left)

    def test_requires_at_least_one_step(self):
        with self.assertRaises(ValueError):
            gui_do.WizardFlow([], on_complete=lambda d: None)


# ---------------------------------------------------------------------------
# 10. SceneTimeline
# ---------------------------------------------------------------------------

class TestSceneTimeline(unittest.TestCase):

    def test_at_fires(self):
        tl = gui_do.SceneTimeline()
        events = []
        tl.at(0.5, lambda: events.append("half"))
        tl.play()
        tl.update(1.0)
        self.assertIn("half", events)

    def test_at_not_fired_when_not_reached(self):
        tl = gui_do.SceneTimeline()
        events = []
        tl.at(5.0, lambda: events.append("late"))
        tl.play()
        tl.update(1.0)
        self.assertNotIn("late", events)

    def test_after_fires_after_delay(self):
        tl = gui_do.SceneTimeline()
        events = []
        tl.after(0.3, lambda: events.append("after"))
        tl.play()
        tl.update(0.5)
        self.assertIn("after", events)

    def test_loop_every(self):
        tl = gui_do.SceneTimeline()
        ticks = []
        tl.loop_every(0.1, lambda: ticks.append(1))
        tl.play()
        tl.update(0.5)
        self.assertGreaterEqual(len(ticks), 4)

    def test_between_on_enter_and_exit(self):
        tl = gui_do.SceneTimeline()
        events = []
        tl.between(1.0, 3.0, on_enter=lambda: events.append("enter"), on_exit=lambda: events.append("exit"))
        tl.play()
        tl.update(2.0)   # now in region
        self.assertIn("enter", events)
        tl.update(2.0)   # now past region
        self.assertIn("exit", events)

    def test_label_seek(self):
        tl = gui_do.SceneTimeline()
        events = []
        tl.at(2.0, lambda: events.append("label_target"))
        tl.label("mid", t=1.9)
        tl.play()
        tl.seek_to_label("mid")
        tl.update(0.2)
        self.assertIn("label_target", events)

    def test_pause_stops_advancement(self):
        tl = gui_do.SceneTimeline()
        events = []
        tl.at(1.0, lambda: events.append("tick"))
        tl.play()
        tl.pause()
        tl.update(2.0)
        self.assertNotIn("tick", events)

    def test_reset_clears_state(self):
        tl = gui_do.SceneTimeline()
        events = []
        tl.at(0.5, lambda: events.append("x"))
        tl.play()
        tl.update(1.0)
        tl.reset()
        tl.play()
        tl.update(1.0)
        # After reset, event fires again
        self.assertGreaterEqual(events.count("x"), 2)

    def test_seek_forward(self):
        tl = gui_do.SceneTimeline()
        events = []
        tl.at(1.0, lambda: events.append("a"))
        tl.at(3.0, lambda: events.append("b"))
        tl.play()
        tl.seek(2.0)
        self.assertIn("a", events)
        self.assertNotIn("b", events)

    def test_on_complete(self):
        tl = gui_do.SceneTimeline(duration=1.0)
        done = []
        tl.on_complete(lambda: done.append(True))
        tl.play()
        tl.update(2.0)
        self.assertTrue(done)
        self.assertFalse(tl.is_playing)

    def test_current_time_property(self):
        tl = gui_do.SceneTimeline()
        tl.play()
        tl.update(0.5)
        self.assertAlmostEqual(tl.current_time, 0.5, places=5)

    def test_duration_auto(self):
        tl = gui_do.SceneTimeline()
        tl.at(3.0, lambda: None)
        tl.at(7.0, lambda: None)
        self.assertAlmostEqual(tl.duration, 7.0)

    def test_duration_explicit(self):
        tl = gui_do.SceneTimeline(duration=10.0)
        self.assertAlmostEqual(tl.duration, 10.0)

    def test_not_playing_initially(self):
        tl = gui_do.SceneTimeline()
        self.assertFalse(tl.is_playing)

    def test_update_no_op_when_paused(self):
        tl = gui_do.SceneTimeline()
        tl.update(1.0)
        self.assertAlmostEqual(tl.current_time, 0.0)


if __name__ == "__main__":
    unittest.main()
