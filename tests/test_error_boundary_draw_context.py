"""Tests for ErrorBoundary and DrawContext/DrawPhase."""
import unittest

import pygame
from pygame import Rect, Surface

from gui_do.controls.composite.error_boundary import ErrorBoundary
from gui_do.controls.base.ui_node import UiNode
from gui_do.graphics.draw_context import DrawContext, DrawPhase

pygame.init()


# ===========================================================================
# Helpers
# ===========================================================================

class _SimpleNode(UiNode):
    def __init__(self, rect=None):
        super().__init__("simple", rect or Rect(10, 20, 200, 100))

    def draw(self, surface, theme=None):
        pass

    def handle_event(self, event, app=None, theme=None):
        return False


class _BrokenNode(UiNode):
    def __init__(self):
        super().__init__("broken", Rect(10, 20, 200, 100))

    def draw(self, surface, theme=None):
        raise RuntimeError("draw failed")

    def handle_event(self, event, app=None, theme=None):
        raise RuntimeError("event failed")

    def update(self, dt):
        raise RuntimeError("update failed")


# ===========================================================================
# ErrorBoundary — initial state
# ===========================================================================


class TestErrorBoundaryInitial(unittest.TestCase):
    def test_has_error_false_initially(self):
        child = _SimpleNode()
        eb = ErrorBoundary(child)
        self.assertFalse(eb.has_error)

    def test_error_none_initially(self):
        child = _SimpleNode()
        eb = ErrorBoundary(child)
        self.assertIsNone(eb.error)

    def test_child_not_none_required(self):
        with self.assertRaises((ValueError, TypeError)):
            ErrorBoundary(None)

    def test_rect_matches_child(self):
        child = _SimpleNode(Rect(5, 10, 150, 80))
        eb = ErrorBoundary(child)
        self.assertEqual(Rect(5, 10, 150, 80), eb.rect)

    def test_child_in_children_list(self):
        child = _SimpleNode()
        eb = ErrorBoundary(child)
        self.assertIn(child, eb.children)

    def test_error_text_stored(self):
        child = _SimpleNode()
        eb = ErrorBoundary(child, error_text="Widget unavailable")
        self.assertEqual("Widget unavailable", eb._error_text)

    def test_on_error_callback_stored(self):
        child = _SimpleNode()
        cb = lambda e: None
        eb = ErrorBoundary(child, on_error=cb)
        self.assertIs(cb, eb._on_error)


class TestErrorBoundaryRecover(unittest.TestCase):
    def test_recover_clears_error(self):
        child = _BrokenNode()
        eb = ErrorBoundary(child)
        eb._error = RuntimeError("forced")
        eb.recover()
        self.assertFalse(eb.has_error)
        self.assertIsNone(eb.error)

    def test_recover_on_mount_clears_error(self):
        child = _BrokenNode()
        eb = ErrorBoundary(child, recover_on_scene_change=True)
        eb._error = RuntimeError("forced")
        eb.on_mount(None)
        self.assertFalse(eb.has_error)

    def test_no_recover_on_mount_if_disabled(self):
        child = _SimpleNode()
        eb = ErrorBoundary(child, recover_on_scene_change=False)
        eb._error = RuntimeError("forced")
        eb.on_mount(None)
        self.assertTrue(eb.has_error)


class TestErrorBoundaryUpdateError(unittest.TestCase):
    def test_update_catches_exception(self):
        child = _BrokenNode()
        eb = ErrorBoundary(child)
        eb.update(0.016)
        self.assertTrue(eb.has_error)
        self.assertIsInstance(eb.error, RuntimeError)

    def test_update_skipped_when_errored(self):
        child = _SimpleNode()
        eb = ErrorBoundary(child)
        eb._error = RuntimeError("forced")
        # Should not raise even though child is fine
        eb.update(0.016)
        self.assertTrue(eb.has_error)

    def test_on_error_callback_called(self):
        received = []
        child = _BrokenNode()
        eb = ErrorBoundary(child, on_error=lambda e: received.append(e))
        eb.update(0.016)
        self.assertEqual(1, len(received))
        self.assertIsInstance(received[0], RuntimeError)


# ===========================================================================
# DrawPhase
# ===========================================================================


class TestDrawPhase(unittest.TestCase):
    def test_values(self):
        self.assertEqual("background", DrawPhase.BACKGROUND.value)
        self.assertEqual("foreground", DrawPhase.FOREGROUND.value)
        self.assertEqual("overlay", DrawPhase.OVERLAY.value)
        self.assertEqual("debug", DrawPhase.DEBUG.value)


# ===========================================================================
# DrawContext — initial state
# ===========================================================================


class TestDrawContextInitial(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1))
        cls.surf = Surface((200, 200))

    def _make(self, phase=DrawPhase.FOREGROUND, opacity=1.0, offset=(0, 0)):
        return DrawContext(
            self.surf,
            Rect(0, 0, 200, 200),
            phase=phase,
            opacity=opacity,
            local_offset=offset,
        )

    def test_surface_stored(self):
        ctx = self._make()
        self.assertIs(self.surf, ctx.surface)

    def test_clip_rect_stored(self):
        ctx = self._make()
        self.assertEqual(Rect(0, 0, 200, 200), ctx.clip_rect)

    def test_phase_stored(self):
        ctx = self._make(phase=DrawPhase.OVERLAY)
        self.assertEqual(DrawPhase.OVERLAY, ctx.phase)

    def test_opacity_clamped_low(self):
        ctx = self._make(opacity=-0.5)
        self.assertEqual(0.0, ctx.opacity)

    def test_opacity_clamped_high(self):
        ctx = self._make(opacity=2.0)
        self.assertEqual(1.0, ctx.opacity)

    def test_local_offset_stored(self):
        ctx = self._make(offset=(10, 20))
        self.assertEqual((10, 20), ctx.local_offset)

    def test_default_phase_foreground(self):
        ctx = DrawContext(self.surf, Rect(0, 0, 200, 200))
        self.assertEqual(DrawPhase.FOREGROUND, ctx.phase)


class TestDrawContextPhaseHelpers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1))
        cls.surf = Surface((200, 200))

    def _ctx(self, phase):
        return DrawContext(self.surf, Rect(0, 0, 200, 200), phase=phase)

    def test_is_background(self):
        self.assertTrue(self._ctx(DrawPhase.BACKGROUND).is_background)
        self.assertFalse(self._ctx(DrawPhase.FOREGROUND).is_background)

    def test_is_foreground(self):
        self.assertTrue(self._ctx(DrawPhase.FOREGROUND).is_foreground)

    def test_is_overlay(self):
        self.assertTrue(self._ctx(DrawPhase.OVERLAY).is_overlay)

    def test_is_debug(self):
        self.assertTrue(self._ctx(DrawPhase.DEBUG).is_debug)

    def test_is_visible_phase_not_debug(self):
        self.assertTrue(self._ctx(DrawPhase.FOREGROUND).is_visible_phase)
        self.assertTrue(self._ctx(DrawPhase.BACKGROUND).is_visible_phase)
        self.assertTrue(self._ctx(DrawPhase.OVERLAY).is_visible_phase)

    def test_is_visible_phase_false_for_debug(self):
        self.assertFalse(self._ctx(DrawPhase.DEBUG).is_visible_phase)


class TestDrawContextDerivedContexts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1))
        cls.surf = Surface((200, 200))

    def test_clip_to_intersects(self):
        ctx = DrawContext(self.surf, Rect(0, 0, 200, 200))
        sub = ctx.clip_to(Rect(50, 50, 100, 100))
        self.assertEqual(Rect(50, 50, 100, 100), sub.clip_rect)

    def test_clip_to_clamps(self):
        ctx = DrawContext(self.surf, Rect(0, 0, 100, 100))
        sub = ctx.clip_to(Rect(80, 80, 100, 100))
        # Intersection should be clamped to parent
        self.assertEqual(20, sub.clip_rect.width)
        self.assertEqual(20, sub.clip_rect.height)

    def test_clip_to_inherits_phase(self):
        ctx = DrawContext(self.surf, Rect(0, 0, 200, 200), phase=DrawPhase.DEBUG)
        sub = ctx.clip_to(Rect(0, 0, 100, 100))
        self.assertEqual(DrawPhase.DEBUG, sub.phase)

    def test_clip_to_override_opacity(self):
        ctx = DrawContext(self.surf, Rect(0, 0, 200, 200), opacity=1.0)
        sub = ctx.clip_to(Rect(0, 0, 100, 100), opacity=0.5)
        self.assertAlmostEqual(0.5, sub.opacity)

    def test_with_offset_accumulates(self):
        ctx = DrawContext(self.surf, Rect(0, 0, 200, 200), local_offset=(10, 20))
        child = ctx.with_offset(5, 3)
        self.assertEqual((15, 23), child.local_offset)

    def test_with_phase(self):
        ctx = DrawContext(self.surf, Rect(0, 0, 200, 200), phase=DrawPhase.FOREGROUND)
        debug = ctx.with_phase(DrawPhase.DEBUG)
        self.assertEqual(DrawPhase.DEBUG, debug.phase)
        self.assertEqual(DrawPhase.FOREGROUND, ctx.phase)  # original unchanged

    def test_with_opacity(self):
        ctx = DrawContext(self.surf, Rect(0, 0, 200, 200), opacity=1.0)
        half = ctx.with_opacity(0.5)
        self.assertAlmostEqual(0.5, half.opacity)
        self.assertAlmostEqual(1.0, ctx.opacity)

    def test_local_rect(self):
        ctx = DrawContext(self.surf, Rect(100, 100, 50, 50), local_offset=(10, 20))
        lr = ctx.local_rect
        self.assertEqual(90, lr.x)
        self.assertEqual(80, lr.y)


if __name__ == "__main__":
    unittest.main()
