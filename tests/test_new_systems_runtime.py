"""Tests for the 10 new generalized systems (Ranks 1-10)."""
import unittest
from unittest.mock import MagicMock, patch
from pygame import Rect


# ---------------------------------------------------------------------------
# 1. DirtyRegionTracker
# ---------------------------------------------------------------------------

class TestDirtyRegionTracker(unittest.TestCase):

    def _make(self):
        from gui_do import DirtyRegionTracker
        return DirtyRegionTracker()

    def test_initially_not_dirty(self):
        t = self._make()
        self.assertFalse(t.has_dirty)
        self.assertIsNone(t.dirty_union())

    def test_mark_dirty_accumulates(self):
        t = self._make()
        t.mark_dirty(Rect(0, 0, 10, 10))
        t.mark_dirty(Rect(20, 20, 10, 10))
        self.assertTrue(t.has_dirty)

    def test_consume_clears(self):
        t = self._make()
        t.mark_dirty(Rect(0, 0, 50, 50))
        rects = t.consume_dirty_regions()
        self.assertEqual(len(rects), 1)
        self.assertFalse(t.has_dirty)

    def test_mark_all_dirty_overrides_individual(self):
        t = self._make()
        t.mark_dirty(Rect(0, 0, 10, 10))
        t.mark_all_dirty(Rect(0, 0, 800, 600))
        rects = t.consume_dirty_regions()
        self.assertEqual(len(rects), 1)
        self.assertEqual(rects[0], Rect(0, 0, 800, 600))

    def test_overlaps_dirty_returns_true_for_intersecting(self):
        t = self._make()
        t.mark_dirty(Rect(50, 50, 100, 100))
        self.assertTrue(t.overlaps_dirty(Rect(0, 0, 100, 100)))

    def test_overlaps_dirty_returns_false_for_non_intersecting(self):
        t = self._make()
        t.mark_dirty(Rect(0, 0, 10, 10))
        self.assertFalse(t.overlaps_dirty(Rect(200, 200, 10, 10)))

    def test_zero_size_rect_ignored(self):
        t = self._make()
        t.mark_dirty(Rect(0, 0, 0, 0))
        self.assertFalse(t.has_dirty)

    def test_dirty_union_computed_correctly(self):
        t = self._make()
        t.mark_dirty(Rect(0, 0, 10, 10))
        t.mark_dirty(Rect(20, 20, 10, 10))
        union = t.dirty_union()
        self.assertIsNotNone(union)
        self.assertEqual(union.left, 0)
        self.assertEqual(union.right, 30)


# ---------------------------------------------------------------------------
# 2. InputSnapshot
# ---------------------------------------------------------------------------

class TestInputSnapshot(unittest.TestCase):

    def _make_empty(self):
        from gui_do import InputSnapshot
        return InputSnapshot.empty()

    def test_empty_snapshot_defaults(self):
        snap = self._make_empty()
        self.assertEqual(snap.pointer_pos, (0, 0))
        self.assertEqual(snap.buttons_held, frozenset())
        self.assertEqual(snap.accumulated_wheel_delta, 0.0)
        self.assertEqual(snap.hover_chain, ())

    def test_is_button_held(self):
        from gui_do import InputSnapshot
        snap = InputSnapshot(buttons_held=frozenset([1]))
        self.assertTrue(snap.is_button_held(1))
        self.assertFalse(snap.is_button_held(3))

    def test_is_button_just_pressed(self):
        from gui_do import InputSnapshot
        snap = InputSnapshot(buttons_just_pressed=frozenset([1]))
        self.assertTrue(snap.is_button_just_pressed(1))

    def test_is_key_down_modifiers(self):
        import pygame
        from gui_do import InputSnapshot
        snap = InputSnapshot(modifiers=pygame.KMOD_SHIFT)
        self.assertTrue(snap.is_key_down(pygame.KMOD_SHIFT))
        self.assertFalse(snap.is_key_down(pygame.KMOD_CTRL))

    def test_topmost_hovered_id(self):
        from gui_do import InputSnapshot
        snap = InputSnapshot(hover_chain=("panel", "button"))
        self.assertEqual(snap.topmost_hovered_id, "button")

    def test_with_hover_chain_returns_copy(self):
        from gui_do import InputSnapshot
        snap = InputSnapshot(pointer_pos=(100, 200))
        snap2 = snap.with_hover_chain(("a", "b"))
        self.assertEqual(snap2.pointer_pos, (100, 200))
        self.assertEqual(snap2.hover_chain, ("a", "b"))
        self.assertEqual(snap.hover_chain, ())

    def test_build_from_empty_events(self):
        from gui_do import InputSnapshot
        snap = InputSnapshot.build(events=[], previous=None)
        self.assertIsInstance(snap, InputSnapshot)
        self.assertEqual(snap.accumulated_wheel_delta, 0.0)


# ---------------------------------------------------------------------------
# 3. DrawContext / DrawPhase
# ---------------------------------------------------------------------------

class TestDrawContext(unittest.TestCase):

    def _make_surface(self, w=100, h=100):
        import pygame
        pygame.display.init()
        return pygame.Surface((w, h))

    def test_phases_enum_members(self):
        from gui_do import DrawPhase
        self.assertEqual(DrawPhase.BACKGROUND.value, "background")
        self.assertEqual(DrawPhase.FOREGROUND.value, "foreground")
        self.assertEqual(DrawPhase.OVERLAY.value, "overlay")
        self.assertEqual(DrawPhase.DEBUG.value, "debug")

    def test_default_phase_is_foreground(self):
        import pygame
        pygame.display.init()
        from gui_do import DrawContext, DrawPhase
        surf = pygame.Surface((100, 100))
        ctx = DrawContext(surf, Rect(0, 0, 100, 100))
        self.assertEqual(ctx.phase, DrawPhase.FOREGROUND)
        self.assertTrue(ctx.is_foreground)
        self.assertFalse(ctx.is_debug)

    def test_opacity_clamped(self):
        import pygame
        pygame.display.init()
        from gui_do import DrawContext
        surf = pygame.Surface((100, 100))
        ctx1 = DrawContext(surf, Rect(0, 0, 100, 100), opacity=-0.5)
        self.assertEqual(ctx1.opacity, 0.0)
        ctx2 = DrawContext(surf, Rect(0, 0, 100, 100), opacity=2.0)
        self.assertEqual(ctx2.opacity, 1.0)

    def test_clip_to_returns_intersected_rect(self):
        import pygame
        pygame.display.init()
        from gui_do import DrawContext
        surf = pygame.Surface((200, 200))
        ctx = DrawContext(surf, Rect(0, 0, 100, 100))
        child = ctx.clip_to(Rect(50, 50, 100, 100))
        self.assertEqual(child.clip_rect, Rect(50, 50, 50, 50))

    def test_with_phase_returns_new_context(self):
        import pygame
        pygame.display.init()
        from gui_do import DrawContext, DrawPhase
        surf = pygame.Surface((100, 100))
        ctx = DrawContext(surf, Rect(0, 0, 100, 100))
        debug_ctx = ctx.with_phase(DrawPhase.DEBUG)
        self.assertEqual(debug_ctx.phase, DrawPhase.DEBUG)
        self.assertEqual(ctx.phase, DrawPhase.FOREGROUND)

    def test_with_offset(self):
        import pygame
        pygame.display.init()
        from gui_do import DrawContext
        surf = pygame.Surface((100, 100))
        ctx = DrawContext(surf, Rect(0, 0, 100, 100), local_offset=(0, 0))
        shifted = ctx.with_offset(10, 20)
        self.assertEqual(shifted.local_offset, (10, 20))


# ---------------------------------------------------------------------------
# 4. Composable Validator Pipeline
# ---------------------------------------------------------------------------

class TestValidationPipeline(unittest.TestCase):

    def test_required_validator_rejects_none(self):
        from gui_do import RequiredValidator
        v = RequiredValidator("required")
        self.assertEqual(v.check(None), "required")
        self.assertIsNone(v.check("hello"))

    def test_required_validator_rejects_empty_string(self):
        from gui_do import RequiredValidator
        v = RequiredValidator()
        self.assertIsNotNone(v.check(""))
        self.assertIsNone(v.check("x"))

    def test_range_validator_bounds(self):
        from gui_do import RangeValidator
        v = RangeValidator(0, 100)
        self.assertIsNone(v.check(50))
        self.assertIsNotNone(v.check(-1))
        self.assertIsNotNone(v.check(101))

    def test_length_validator(self):
        from gui_do import LengthValidator
        v = LengthValidator(min_length=2, max_length=5)
        self.assertIsNone(v.check("ab"))
        self.assertIsNotNone(v.check("a"))
        self.assertIsNotNone(v.check("toolong"))

    def test_pattern_validator(self):
        from gui_do import PatternValidator
        v = PatternValidator(r"\d{4}", message="4 digits required")
        self.assertIsNone(v.check("1234"))
        self.assertEqual(v.check("abc"), "4 digits required")

    def test_custom_validator(self):
        from gui_do import CustomValidator
        v = CustomValidator(lambda x: None if x > 0 else "must be positive")
        self.assertIsNone(v.check(5))
        self.assertIsNotNone(v.check(-1))

    def test_validation_pipeline_passes(self):
        from gui_do import ValidationPipeline, RequiredValidator, RangeValidator, ValidationResult
        p = ValidationPipeline([RequiredValidator(), RangeValidator(0, 100)])
        result = p.validate(50)
        self.assertTrue(result.ok)
        self.assertEqual(result.errors, [])

    def test_validation_pipeline_fails_first_error(self):
        from gui_do import ValidationPipeline, RequiredValidator
        p = ValidationPipeline([RequiredValidator()])
        result = p.validate(None)
        self.assertFalse(result.ok)
        self.assertTrue(len(result.errors) >= 1)

    def test_pipeline_collects_all_errors_when_no_short_circuit(self):
        from gui_do import ValidationPipeline, RequiredValidator, LengthValidator
        p = ValidationPipeline(
            [RequiredValidator("req"), LengthValidator(min_length=5, message="len")],
            stop_on_first_error=False,
        )
        result = p.validate("")
        self.assertFalse(result.ok)
        self.assertIn("req", result.errors)
        self.assertIn("len", result.errors)

    def test_dependent_validator_with_context(self):
        from gui_do import DependentValidator
        v = DependentValidator(lambda val, ctx: "duplicate" if ctx.get("existing") == val else None)
        self.assertIsNone(v.check_with_context("alice", {"existing": "bob"}))
        self.assertEqual(v.check_with_context("alice", {"existing": "alice"}), "duplicate")

    def test_validation_result_bool(self):
        from gui_do import ValidationResult
        self.assertTrue(bool(ValidationResult.passed()))
        self.assertFalse(bool(ValidationResult.failed("err")))


# ---------------------------------------------------------------------------
# 5. Viewport
# ---------------------------------------------------------------------------

class TestViewport(unittest.TestCase):

    def _make(self, content=(1000, 800), viewport=(400, 300)):
        from gui_do import Viewport
        return Viewport(content_size=content, viewport_size=viewport)

    def test_initial_scroll_is_zero(self):
        vp = self._make()
        self.assertEqual(vp.scroll_offset, (0.0, 0.0))

    def test_scroll_to_and_clamp(self):
        vp = self._make()
        vp.scroll_to(100, 50)
        self.assertEqual(vp.scroll_x, 100.0)
        self.assertEqual(vp.scroll_y, 50.0)

    def test_scroll_clamps_to_max(self):
        vp = self._make(content=(100, 100), viewport=(200, 200))
        vp.scroll_to(500, 500)
        # viewport bigger than content — should clamp to 0
        self.assertEqual(vp.scroll_x, 0.0)

    def test_scroll_by_accumulates(self):
        vp = self._make()
        vp.scroll_by(50, 30)
        vp.scroll_by(10, 5)
        self.assertAlmostEqual(vp.scroll_x, 60.0)
        self.assertAlmostEqual(vp.scroll_y, 35.0)

    def test_zoom_sets_factor(self):
        vp = self._make()
        vp.set_zoom(2.0)
        self.assertAlmostEqual(vp.zoom, 2.0)

    def test_zoom_clamped_to_bounds(self):
        vp = self._make(content=(1000, 800), viewport=(400, 300))
        vp.set_zoom(0.0)   # below min
        self.assertGreaterEqual(vp.zoom, 0.1)
        vp2 = self._make()
        vp2.set_zoom(9999.0)
        self.assertLessEqual(vp2.zoom, 32.0)

    def test_screen_to_local_at_zero_scroll(self):
        vp = self._make()
        lx, ly = vp.screen_to_local((100, 50))
        self.assertAlmostEqual(lx, 100.0)
        self.assertAlmostEqual(ly, 50.0)

    def test_local_to_screen_roundtrip(self):
        vp = self._make()
        vp.scroll_to(20, 10)
        pt = (200.0, 150.0)
        screen_pt = vp.local_to_screen(pt)
        recovered = vp.screen_to_local(screen_pt)
        self.assertAlmostEqual(recovered[0], pt[0], places=4)
        self.assertAlmostEqual(recovered[1], pt[1], places=4)

    def test_visible_rect(self):
        vp = self._make(content=(1000, 800), viewport=(400, 300))
        vis = vp.visible_rect()
        self.assertEqual(vis.x, 0)
        self.assertEqual(vis.width, 400)

    def test_subscriber_notified_on_scroll(self):
        vp = self._make()
        calls = []
        vp.subscribe(lambda: calls.append(1))
        vp.scroll_to(50, 50)
        self.assertGreater(len(calls), 0)

    def test_unsub_stops_notifications(self):
        vp = self._make()
        calls = []
        unsub = vp.subscribe(lambda: calls.append(1))
        unsub()
        vp.scroll_to(50, 50)
        self.assertEqual(calls, [])


# ---------------------------------------------------------------------------
# 6. HierarchicalStateMachine
# ---------------------------------------------------------------------------

class TestHierarchicalStateMachine(unittest.TestCase):

    def test_flat_trigger_still_works(self):
        from gui_do import HierarchicalStateMachine
        sm = HierarchicalStateMachine("idle")
        sm.add_transition("idle", "running", trigger="start")
        self.assertTrue(sm.trigger("start"))
        self.assertEqual(sm.current.value, "running")

    def test_composite_state_enters_initial(self):
        from gui_do import HierarchicalStateMachine, StateMachine
        inner = StateMachine("sub_idle")
        inner.add_state("sub_busy")
        inner.add_transition("sub_idle", "sub_busy", trigger="work")

        outer = HierarchicalStateMachine("home")
        outer.add_composite("active", inner, initial="sub_idle")
        outer.add_transition("home", "active", trigger="go")

        outer.trigger("go")
        self.assertEqual(outer.current.value, "active")
        self.assertEqual(outer.sub_current("active"), "sub_idle")

    def test_sub_trigger_advances_inner(self):
        from gui_do import HierarchicalStateMachine, StateMachine
        inner = StateMachine("a")
        inner.add_transition("a", "b", trigger="next")

        outer = HierarchicalStateMachine("home")
        outer.add_composite("active", inner, initial="a")
        outer.add_transition("home", "active", trigger="go")

        outer.trigger("go")
        outer.sub_trigger("active", "next")
        self.assertEqual(outer.sub_current("active"), "b")

    def test_history_state_resumes_after_exit(self):
        from gui_do import HierarchicalStateMachine, StateMachine
        inner = StateMachine("page1")
        inner.add_state("page2")
        inner.add_transition("page1", "page2", trigger="next")

        outer = HierarchicalStateMachine("home")
        outer.add_history("wizard", inner, initial="page1")
        outer.add_transition("home", "wizard", trigger="open")
        outer.add_transition("wizard", "home", trigger="close")

        outer.trigger("open")
        outer.sub_trigger("wizard", "next")
        self.assertEqual(outer.sub_current("wizard"), "page2")
        outer.trigger("close")
        outer.trigger("open")
        # History state should resume page2
        self.assertEqual(outer.sub_current("wizard"), "page2")

    def test_trigger_to_directly_changes_state(self):
        from gui_do import HierarchicalStateMachine
        sm = HierarchicalStateMachine("a")
        sm.add_state("b")
        sm.trigger_to("b")
        self.assertEqual(sm.current.value, "b")

    def test_trigger_to_raises_on_unknown_state(self):
        from gui_do import HierarchicalStateMachine
        sm = HierarchicalStateMachine("a")
        with self.assertRaises(ValueError):
            sm.trigger_to("nonexistent")


# ---------------------------------------------------------------------------
# 7. AssetRegistry
# ---------------------------------------------------------------------------

class TestAssetRegistry(unittest.TestCase):

    def test_stats_empty(self):
        from gui_do import AssetRegistry
        reg = AssetRegistry()
        s = reg.stats()
        self.assertEqual(s["surfaces"], 0)
        self.assertEqual(s["fonts"], 0)

    def test_clear(self):
        from gui_do import AssetRegistry
        reg = AssetRegistry()
        reg.clear()
        self.assertEqual(reg.stats()["surfaces"], 0)

    def test_has_surface_false_initially(self):
        from gui_do import AssetRegistry
        reg = AssetRegistry()
        self.assertFalse(reg.has_surface("any.png"))

    def test_hot_reload_disabled_by_default(self):
        from gui_do import AssetRegistry
        reg = AssetRegistry()
        # Hot reload disabled by default
        if hasattr(reg, 'hot_reload_enabled'):
            self.assertFalse(reg.hot_reload_enabled)
        else:
            self.assertFalse(reg._hot_reload)

    def test_hot_reload_no_eviction_without_changes(self, ):
        from gui_do import AssetRegistry
        reg = AssetRegistry(enable_hot_reload=True)
        # Nothing to evict — returns False
        self.assertFalse(reg.check_hot_reload())


# ---------------------------------------------------------------------------
# 8. Signal
# ---------------------------------------------------------------------------

class TestSignal(unittest.TestCase):

    def _make_class(self):
        from gui_do import Signal

        class Emitter:
            value_changed: Signal = Signal()

        return Emitter

    def test_connect_and_emit(self):
        Emitter = self._make_class()
        e = Emitter()
        received = []
        e.value_changed.connect(lambda v: received.append(v))
        e.value_changed.emit(42)
        self.assertEqual(received, [42])

    def test_disconnect(self):
        Emitter = self._make_class()
        e = Emitter()
        received = []
        cb = lambda v: received.append(v)
        conn = e.value_changed.connect(cb)
        conn.disconnect()
        e.value_changed.emit(99)
        self.assertEqual(received, [])

    def test_connect_once_fires_once(self):
        Emitter = self._make_class()
        e = Emitter()
        received = []
        e.value_changed.connect_once(lambda v: received.append(v))
        e.value_changed.emit(1)
        e.value_changed.emit(2)
        self.assertEqual(received, [1])

    def test_disconnect_by_callable(self):
        Emitter = self._make_class()
        e = Emitter()
        received = []
        cb = lambda v: received.append(v)
        e.value_changed.connect(cb)
        e.value_changed.disconnect(cb)
        e.value_changed.emit(10)
        self.assertEqual(received, [])

    def test_per_instance_isolation(self):
        Emitter = self._make_class()
        a = Emitter()
        b = Emitter()
        recv_a, recv_b = [], []
        a.value_changed.connect(lambda v: recv_a.append(v))
        b.value_changed.connect(lambda v: recv_b.append(v))
        a.value_changed.emit(1)
        self.assertEqual(recv_a, [1])
        self.assertEqual(recv_b, [])

    def test_signal_reassignment_raises(self):
        Emitter = self._make_class()
        e = Emitter()
        with self.assertRaises(AttributeError):
            e.value_changed = "not allowed"

    def test_connection_count(self):
        Emitter = self._make_class()
        e = Emitter()
        self.assertEqual(e.value_changed.connection_count, 0)
        e.value_changed.connect(lambda v: None)
        self.assertEqual(e.value_changed.connection_count, 1)


# ---------------------------------------------------------------------------
# 9. FocusRing
# ---------------------------------------------------------------------------

class TestFocusRing(unittest.TestCase):

    def _make(self, ids, **kw):
        from gui_do import FocusRing
        return FocusRing(ids, **kw)

    def test_advance_forward(self):
        ring = self._make(["a", "b", "c"])
        self.assertEqual(ring.advance("a", forward=True), "b")
        self.assertEqual(ring.advance("b", forward=True), "c")

    def test_advance_backward(self):
        ring = self._make(["a", "b", "c"])
        self.assertEqual(ring.advance("c", forward=False), "b")

    def test_wrap_forward(self):
        ring = self._make(["a", "b", "c"], wrap=True)
        self.assertEqual(ring.advance("c", forward=True), "a")

    def test_wrap_backward(self):
        ring = self._make(["a", "b", "c"], wrap=True)
        self.assertEqual(ring.advance("a", forward=False), "c")

    def test_trap_never_escapes(self):
        ring = self._make(["x", "y"], trap=True, wrap=False)
        # At boundary of trap ring should still wrap
        self.assertEqual(ring.advance("y", forward=True), "x")
        self.assertEqual(ring.advance("x", forward=False), "y")

    def test_no_wrap_no_trap_returns_none_at_boundary(self):
        ring = self._make(["a", "b"], wrap=False, trap=False)
        self.assertIsNone(ring.advance("b", forward=True))
        self.assertIsNone(ring.advance("a", forward=False))

    def test_chained_ring_delegates_at_boundary(self):
        from gui_do import FocusRing
        parent = FocusRing(["p1", "p2"], wrap=True)
        child = FocusRing(["c1", "c2"], wrap=False, parent=parent)
        # At boundary, delegate to parent
        result = child.advance("c2", forward=True)
        # parent advances from "c2" (not in parent) → returns p1
        self.assertEqual(result, "p1")

    def test_contains(self):
        ring = self._make(["a", "b"])
        self.assertTrue(ring.contains("a"))
        self.assertFalse(ring.contains("z"))

    def test_insert_after(self):
        ring = self._make(["a", "c"])
        ring.insert("b", after="a")
        self.assertEqual(ring.node_ids, ["a", "b", "c"])

    def test_insert_before(self):
        ring = self._make(["a", "c"])
        ring.insert("b", before="c")
        self.assertEqual(ring.node_ids, ["a", "b", "c"])

    def test_remove(self):
        ring = self._make(["a", "b", "c"])
        removed = ring.remove("b")
        self.assertTrue(removed)
        self.assertEqual(ring.node_ids, ["a", "c"])

    def test_remove_nonexistent_returns_false(self):
        ring = self._make(["a"])
        self.assertFalse(ring.remove("z"))

    def test_none_current_returns_first(self):
        ring = self._make(["a", "b", "c"])
        self.assertEqual(ring.advance(None, forward=True), "a")

    def test_empty_ring_returns_none(self):
        ring = self._make([])
        self.assertIsNone(ring.advance(None, forward=True))


# ---------------------------------------------------------------------------
# 10. DebugOverlay (basic instantiation / toggle)
# ---------------------------------------------------------------------------

class TestDebugOverlay(unittest.TestCase):

    def test_disabled_by_default(self):
        from gui_do import DebugOverlay
        overlay = DebugOverlay()
        self.assertFalse(overlay.enabled)

    def test_toggle(self):
        from gui_do import DebugOverlay
        overlay = DebugOverlay()
        result = overlay.toggle()
        self.assertTrue(result)
        self.assertTrue(overlay.enabled)
        result2 = overlay.toggle()
        self.assertFalse(result2)

    def test_log_event(self):
        from gui_do import DebugOverlay
        overlay = DebugOverlay()
        overlay.log_event("MOUSE_DOWN")
        overlay.log_event("MOUSE_UP")
        # No error; internal deque contains events
        self.assertEqual(list(overlay._event_log), ["MOUSE_DOWN", "MOUSE_UP"])

    def test_clear_event_log(self):
        from gui_do import DebugOverlay
        overlay = DebugOverlay()
        overlay.log_event("X")
        overlay.clear_event_log()
        self.assertEqual(list(overlay._event_log), [])

    def test_draw_noop_when_disabled(self):
        import pygame
        pygame.display.init()
        from gui_do import DebugOverlay
        surf = pygame.Surface((100, 100))
        overlay = DebugOverlay()
        overlay.enabled = False
        # Should not raise; surface unchanged
        overlay.draw(surf, None, fps=60.0)

    def test_feed_dirty_rects(self):
        from gui_do import DebugOverlay
        overlay = DebugOverlay()
        overlay.feed_dirty_rects([Rect(0, 0, 10, 10), Rect(20, 20, 5, 5)])
        self.assertEqual(len(overlay._dirty_flash), 2)


if __name__ == "__main__":
    unittest.main()
