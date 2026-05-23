"""Tests for ImageControl, RichLabelControl, AnimatedImageControl,
OverlayPanelControl, and CanvasControl/CanvasEventPacket."""
import unittest
from unittest import mock

import pygame
from pygame import Rect

from gui_do.controls.display.image_control import ImageControl
from gui_do.controls.display.rich_label_control import RichLabelControl
from gui_do.controls.display.animated_image_control import AnimatedImageControl
from gui_do.controls.display.label_control import LabelControl
from gui_do.controls.composite.panel_control import PanelControl
from gui_do.controls.composite.overlay_panel_control import OverlayPanelControl
from gui_do.controls.canvas.canvas_control import CanvasControl, CanvasEventPacket
from gui_do.graphics.sprite_sheet import SpriteSheet, FrameAnimation
from gui_do.events.gui_event import EventType, GuiEvent

pygame.init()
pygame.display.set_mode((1, 1))  # convert_alpha() requires a display surface


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _surface(w=64, h=64, alpha=False):
    surf = pygame.Surface((w, h))
    if alpha:
        surf = surf.convert_alpha()
    return surf


def _make_animation(fps=12, frames=(0,)):
    sheet_surf = pygame.Surface((64, 64))
    sheet = SpriteSheet(sheet_surf, 64, 64)
    return FrameAnimation(sheet, list(frames), fps)


# ===========================================================================
# ImageControl
# ===========================================================================


class TestImageControlInitial(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1))

    def test_scale_true_by_default(self):
        surf = _surface()
        ic = ImageControl("ic", Rect(0, 0, 100, 100), surf)
        self.assertTrue(ic.scale)

    def test_scale_false_stored(self):
        surf = _surface()
        ic = ImageControl("ic", Rect(0, 0, 100, 100), surf, scale=False)
        self.assertFalse(ic.scale)

    def test_accepts_surface_directly(self):
        surf = _surface()
        ic = ImageControl("ic", Rect(0, 0, 50, 50), surf)
        self.assertIsNotNone(ic._base_image)

    def test_rect_stored(self):
        surf = _surface()
        r = Rect(10, 20, 80, 60)
        ic = ImageControl("ic", r, surf)
        self.assertEqual(r, ic.rect)

    def test_accepts_mouse_focus_false(self):
        surf = _surface()
        ic = ImageControl("ic", Rect(0, 0, 80, 60), surf)
        self.assertFalse(ic.accepts_mouse_focus())


class TestImageControlSetImage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1))

    def test_set_image_replaces_base(self):
        surf1 = _surface(64, 64)
        surf2 = _surface(32, 32)
        ic = ImageControl("ic", Rect(0, 0, 64, 64), surf1)
        ic.set_image(surf2)
        self.assertIsNotNone(ic._base_image)

    def test_set_image_clears_scaled_cache(self):
        surf = _surface()
        ic = ImageControl("ic", Rect(0, 0, 64, 64), surf)
        ic._scaled_image = object()
        ic.set_image(_surface(32, 32))
        self.assertIsNone(ic._scaled_image)

    def test_invalid_path_raises(self):
        with self.assertRaises(Exception):
            ImageControl("ic", Rect(0, 0, 64, 64), "nonexistent_file.png")


# ===========================================================================
# RichLabelControl
# ===========================================================================


class TestRichLabelControlInitial(unittest.TestCase):
    def test_text_stored(self):
        rl = RichLabelControl("rl", Rect(0, 0, 300, 100), text="Hello")
        self.assertEqual("Hello", rl.text)

    def test_empty_text_by_default(self):
        rl = RichLabelControl("rl", Rect(0, 0, 300, 100))
        self.assertEqual("", rl.text)

    def test_font_role_default_body(self):
        rl = RichLabelControl("rl", Rect(0, 0, 300, 100))
        self.assertEqual("body", rl.font_role)

    def test_font_role_stored(self):
        rl = RichLabelControl("rl", Rect(0, 0, 300, 100), font_role="caption")
        self.assertEqual("caption", rl.font_role)

    def test_align_default_left(self):
        rl = RichLabelControl("rl", Rect(0, 0, 300, 100))
        self.assertEqual("left", rl.align)

    def test_align_center_stored(self):
        rl = RichLabelControl("rl", Rect(0, 0, 300, 100), align="center")
        self.assertEqual("center", rl.align)

    def test_align_invalid_falls_back_to_left(self):
        rl = RichLabelControl("rl", Rect(0, 0, 300, 100), align="diagonal")
        self.assertEqual("left", rl.align)

    def test_font_size_clamped_to_6(self):
        rl = RichLabelControl("rl", Rect(0, 0, 300, 100), font_size=2)
        self.assertEqual(6, rl.font_size)

    def test_font_size_stored(self):
        rl = RichLabelControl("rl", Rect(0, 0, 300, 100), font_size=20)
        self.assertEqual(20, rl.font_size)

    def test_accepts_mouse_focus_false(self):
        rl = RichLabelControl("rl", Rect(0, 0, 300, 100))
        self.assertFalse(rl.accepts_mouse_focus())


class TestRichLabelControlSetters(unittest.TestCase):
    def test_set_text(self):
        rl = RichLabelControl("rl", Rect(0, 0, 300, 100), text="A")
        rl.text = "B"
        self.assertEqual("B", rl.text)

    def test_set_same_text_idempotent(self):
        rl = RichLabelControl("rl", Rect(0, 0, 300, 100), text="A")
        rl.text = "A"  # should not raise

    def test_set_font_role(self):
        rl = RichLabelControl("rl", Rect(0, 0, 300, 100))
        rl.font_role = "heading"
        self.assertEqual("heading", rl.font_role)

    def test_set_align_right(self):
        rl = RichLabelControl("rl", Rect(0, 0, 300, 100))
        rl.align = "right"
        self.assertEqual("right", rl.align)

    def test_set_align_invalid_falls_back_to_left(self):
        rl = RichLabelControl("rl", Rect(0, 0, 300, 100), align="right")
        rl.align = "invalid"
        self.assertEqual("left", rl.align)

    def test_set_font_size(self):
        rl = RichLabelControl("rl", Rect(0, 0, 300, 100))
        rl.font_size = 18
        self.assertEqual(18, rl.font_size)

    def test_set_font_size_clamped(self):
        rl = RichLabelControl("rl", Rect(0, 0, 300, 100))
        rl.font_size = 1
        self.assertEqual(6, rl.font_size)


# ===========================================================================
# AnimatedImageControl
# ===========================================================================


class TestAnimatedImageControlInitial(unittest.TestCase):
    def test_animation_stored(self):
        anim = _make_animation()
        ctrl = AnimatedImageControl("a", Rect(0, 0, 64, 64), anim)
        self.assertIs(anim, ctrl.animation)

    def test_scale_true_by_default(self):
        ctrl = AnimatedImageControl("a", Rect(0, 0, 64, 64), _make_animation())
        self.assertTrue(ctrl.scale)

    def test_scale_false_stored(self):
        ctrl = AnimatedImageControl("a", Rect(0, 0, 64, 64), _make_animation(), scale=False)
        self.assertFalse(ctrl.scale)

    def test_accepts_mouse_focus_false(self):
        ctrl = AnimatedImageControl("a", Rect(0, 0, 64, 64), _make_animation())
        self.assertFalse(ctrl.accepts_mouse_focus())


class TestAnimatedImageControlSetters(unittest.TestCase):
    def test_animation_setter(self):
        anim1 = _make_animation(fps=12)
        anim2 = _make_animation(fps=24)
        ctrl = AnimatedImageControl("a", Rect(0, 0, 64, 64), anim1)
        ctrl.animation = anim2
        self.assertIs(anim2, ctrl.animation)

    def test_scale_setter(self):
        ctrl = AnimatedImageControl("a", Rect(0, 0, 64, 64), _make_animation())
        ctrl.scale = False
        self.assertFalse(ctrl.scale)

    def test_tick_advances_animation(self):
        anim = _make_animation(fps=1000, frames=[0])
        ctrl = AnimatedImageControl("a", Rect(0, 0, 64, 64), anim)
        ctrl.tick(0.016)  # should not raise

    def test_draw_reuses_scaled_frame_for_same_source_and_size(self):
        anim = _make_animation(fps=12, frames=[0])
        ctrl = AnimatedImageControl("a", Rect(0, 0, 32, 32), anim)
        surface = pygame.Surface((64, 64)).convert_alpha()

        with mock.patch("pygame.transform.smoothscale", wraps=pygame.transform.smoothscale) as smoothscale:
            ctrl.draw(surface, theme=None)
            ctrl.draw(surface, theme=None)

        self.assertEqual(1, smoothscale.call_count)


# ===========================================================================
# OverlayPanelControl
# ===========================================================================


class TestOverlayPanelControlInitial(unittest.TestCase):
    def test_is_overlay_true(self):
        opc = OverlayPanelControl("opc", Rect(0, 0, 400, 300))
        self.assertTrue(opc.is_overlay())

    def test_draw_background_default_true(self):
        opc = OverlayPanelControl("opc", Rect(0, 0, 400, 300))
        self.assertTrue(opc.draw_background)

    def test_draw_background_false(self):
        opc = OverlayPanelControl("opc", Rect(0, 0, 400, 300), draw_background=False)
        self.assertFalse(opc.draw_background)

    def test_control_id(self):
        opc = OverlayPanelControl("my_overlay", Rect(0, 0, 400, 300))
        self.assertEqual("my_overlay", opc.control_id)

    def test_children_empty(self):
        opc = OverlayPanelControl("opc", Rect(0, 0, 400, 300))
        self.assertEqual([], opc.children)

    def test_add_at_child_tracks_panel_move(self):
        opc = OverlayPanelControl("opc", Rect(10, 20, 200, 120))
        child = LabelControl("child", Rect(0, 0, 50, 20), "Item", align="left")
        opc.add_at(child, rel_x=8, rel_y=6)
        self.assertEqual((18, 26), child.rect.topleft)

        opc.set_rect(Rect(40, 70, 200, 120))
        self.assertEqual((48, 76), child.rect.topleft)

    def test_add_at_child_tracks_panel_set_pos(self):
        opc = OverlayPanelControl("opc", Rect(10, 20, 200, 120))
        child = LabelControl("child", Rect(0, 0, 50, 20), "Item", align="left")
        opc.add_at(child, rel_x=8, rel_y=6)
        self.assertEqual((18, 26), child.rect.topleft)

        opc.set_pos(40, 70)
        self.assertEqual((48, 76), child.rect.topleft)

        def test_nested_add_at_child_tracks_parent_panel_set_rect(self):
            parent = PanelControl("parent", Rect(0, 0, 400, 300), draw_background=False)
            overlay = OverlayPanelControl("overlay", Rect(0, 0, 120, 90), draw_background=False)
            child = LabelControl("child", Rect(0, 0, 50, 20), "Item", align="left")
            overlay.add_at(child, rel_x=8, rel_y=6)
            parent.add_at(overlay, rel_x=30, rel_y=40)

            self.assertEqual((38, 46), child.rect.topleft)

            parent.set_rect(Rect(100, 120, 400, 300))
            self.assertEqual((138, 166), child.rect.topleft)


class TestOverlayPanelControlInputConsumption(unittest.TestCase):
    """Test that overlays consume mouse input to prevent fall-through."""

    def test_overlay_consumes_mouse_click_within_bounds(self):
        """Overlay should consume (return True for) mouse click within its rect."""
        opc = OverlayPanelControl("opc", Rect(100, 100, 200, 150))
        event = GuiEvent(kind=EventType.MOUSE_BUTTON_DOWN, type=0, button=1, pos=(150, 125))

        # Create stub app with no children so dispatch doesn't process anything
        class StubApp:
            pass

        result = opc.handle_event(event, StubApp())
        self.assertTrue(result, "Overlay should consume click within its bounds")

    def test_overlay_rejects_mouse_click_outside_bounds(self):
        """Overlay should reject (return False for) mouse click outside its rect."""
        opc = OverlayPanelControl("opc", Rect(100, 100, 200, 150))
        event = GuiEvent(kind=EventType.MOUSE_BUTTON_DOWN, type=0, button=1, pos=(50, 50))

        class StubApp:
            pass

        result = opc.handle_event(event, StubApp())
        self.assertFalse(result, "Overlay should reject click outside its bounds")

    def test_overlay_consumes_click_at_edge(self):
        """Overlay should consume click at its edge boundary."""
        opc = OverlayPanelControl("opc", Rect(100, 100, 200, 150))
        event = GuiEvent(kind=EventType.MOUSE_BUTTON_DOWN, type=0, button=1, pos=(100, 100))

        class StubApp:
            pass

        result = opc.handle_event(event, StubApp())
        self.assertTrue(result, "Overlay should consume click at edge boundary")

    def test_overlay_ignores_other_button_clicks(self):
        """Overlay should not consume mouse clicks with non-left buttons."""
        opc = OverlayPanelControl("opc", Rect(100, 100, 200, 150))
        event = GuiEvent(kind=EventType.MOUSE_BUTTON_DOWN, type=0, button=3, pos=(150, 125))

        class StubApp:
            pass

        result = opc.handle_event(event, StubApp())
        self.assertFalse(result, "Overlay should not consume non-left button clicks")

    def test_overlay_ignores_non_mouse_events(self):
        """Overlay should not consume non-mouse events."""
        opc = OverlayPanelControl("opc", Rect(100, 100, 200, 150))
        event = GuiEvent(kind=EventType.MOUSE_MOTION, type=0, pos=(150, 125))

        class StubApp:
            pass

        result = opc.handle_event(event, StubApp())
        self.assertFalse(result, "Overlay should not consume motion events")


# ===========================================================================
# CanvasEventPacket
# ===========================================================================


class TestCanvasEventPacket(unittest.TestCase):
    def test_is_mouse_motion_true(self):
        p = CanvasEventPacket(kind=EventType.MOUSE_MOTION)
        self.assertTrue(p.is_mouse_motion())

    def test_is_mouse_motion_false(self):
        p = CanvasEventPacket(kind=EventType.MOUSE_BUTTON_DOWN, button=1)
        self.assertFalse(p.is_mouse_motion())

    def test_is_mouse_down_any(self):
        p = CanvasEventPacket(kind=EventType.MOUSE_BUTTON_DOWN, button=1)
        self.assertTrue(p.is_mouse_down())

    def test_is_mouse_down_specific_button(self):
        p = CanvasEventPacket(kind=EventType.MOUSE_BUTTON_DOWN, button=2)
        self.assertFalse(p.is_mouse_down(1))
        self.assertTrue(p.is_mouse_down(2))

    def test_is_mouse_up(self):
        p = CanvasEventPacket(kind=EventType.MOUSE_BUTTON_UP, button=1)
        self.assertTrue(p.is_mouse_up(1))

    def test_is_left_down(self):
        p = CanvasEventPacket(kind=EventType.MOUSE_BUTTON_DOWN, button=1)
        self.assertTrue(p.is_left_down())

    def test_is_left_up(self):
        p = CanvasEventPacket(kind=EventType.MOUSE_BUTTON_UP, button=1)
        self.assertTrue(p.is_left_up())

    def test_is_right_down(self):
        p = CanvasEventPacket(kind=EventType.MOUSE_BUTTON_DOWN, button=3)
        self.assertTrue(p.is_right_down())

    def test_is_right_up(self):
        p = CanvasEventPacket(kind=EventType.MOUSE_BUTTON_UP, button=3)
        self.assertTrue(p.is_right_up())

    def test_is_middle_down(self):
        p = CanvasEventPacket(kind=EventType.MOUSE_BUTTON_DOWN, button=2)
        self.assertTrue(p.is_middle_down())

    def test_is_middle_up(self):
        p = CanvasEventPacket(kind=EventType.MOUSE_BUTTON_UP, button=2)
        self.assertTrue(p.is_middle_up())

    def test_is_mouse_wheel(self):
        p = CanvasEventPacket(kind=EventType.MOUSE_WHEEL, wheel_delta=3)
        self.assertTrue(p.is_mouse_wheel())


# ===========================================================================
# CanvasControl
# ===========================================================================


class TestCanvasControlInitial(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1))

    def test_canvas_surface_created(self):
        cc = CanvasControl("cc", Rect(0, 0, 200, 150))
        self.assertIsNotNone(cc.canvas)

    def test_canvas_size_matches_rect(self):
        cc = CanvasControl("cc", Rect(0, 0, 200, 150))
        self.assertEqual((200, 150), cc.canvas.get_size())

    def test_coalesce_motion_true_by_default(self):
        cc = CanvasControl("cc", Rect(0, 0, 200, 150))
        self.assertTrue(cc.coalesce_motion_events)

    def test_overflow_mode_default(self):
        cc = CanvasControl("cc", Rect(0, 0, 200, 150))
        self.assertEqual("drop_oldest", cc.overflow_mode)

    def test_read_event_empty_returns_none(self):
        cc = CanvasControl("cc", Rect(0, 0, 200, 150))
        self.assertIsNone(cc.read_event())

    def test_max_events_custom(self):
        cc = CanvasControl("cc", Rect(0, 0, 200, 150), max_events=10)
        self.assertEqual(10, cc._events.maxlen)

    def test_get_canvas_surface(self):
        cc = CanvasControl("cc", Rect(0, 0, 200, 150))
        self.assertIs(cc.canvas, cc.get_canvas_surface())


class TestCanvasControlEventQueue(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1))

    def test_set_overflow_mode_valid(self):
        cc = CanvasControl("cc", Rect(0, 0, 200, 150))
        cc.set_overflow_mode("drop_newest")
        self.assertEqual("drop_newest", cc.overflow_mode)

    def test_set_overflow_mode_invalid_raises(self):
        cc = CanvasControl("cc", Rect(0, 0, 200, 150))
        with self.assertRaises(ValueError):
            cc.set_overflow_mode("keep_all")

    def test_set_motion_coalescing(self):
        cc = CanvasControl("cc", Rect(0, 0, 200, 150))
        cc.set_motion_coalescing(False)
        self.assertFalse(cc.coalesce_motion_events)

    def test_set_event_queue_limit(self):
        cc = CanvasControl("cc", Rect(0, 0, 200, 150), max_events=256)
        cc.set_event_queue_limit(8)
        self.assertEqual(8, cc._events.maxlen)

    def test_set_event_queue_limit_clamped_to_one(self):
        cc = CanvasControl("cc", Rect(0, 0, 200, 150))
        cc.set_event_queue_limit(0)
        self.assertEqual(1, cc._events.maxlen)

    def test_set_overflow_handler(self):
        cc = CanvasControl("cc", Rect(0, 0, 200, 150))
        handler = lambda dropped, total: None
        cc.set_overflow_handler(handler)
        self.assertIs(handler, cc.on_overflow)

    def test_motion_events_coalesce_to_latest_packet(self):
        cc = CanvasControl("cc", Rect(0, 0, 200, 150))

        first = GuiEvent(EventType.MOUSE_MOTION, pygame.MOUSEMOTION, pos=(10, 20), rel=(1, 2))
        second = GuiEvent(EventType.MOUSE_MOTION, pygame.MOUSEMOTION, pos=(30, 40), rel=(3, 4))

        self.assertTrue(cc.handle_event(first, None))
        self.assertTrue(cc.handle_event(second, None))
        self.assertEqual(1, len(cc._events))
        packet = cc.read_event()
        self.assertEqual((30, 40), packet.pos)
        self.assertEqual((30, 40), packet.local_pos)
        self.assertEqual((3, 4), packet.rel)

    def test_resize_reuses_backing_surface_when_shrinking(self):
        cc = CanvasControl("cc", Rect(0, 0, 200, 150))
        cc.canvas.fill((12, 34, 56, 255))
        backing_id = id(cc._canvas_backing)

        cc.rect.size = (120, 90)
        cc._ensure_canvas_size()

        self.assertEqual((120, 90), cc.canvas.get_size())
        self.assertEqual(backing_id, id(cc._canvas_backing))
        self.assertEqual((12, 34, 56, 255), cc.canvas.get_at((0, 0)))


if __name__ == "__main__":
    unittest.main()
