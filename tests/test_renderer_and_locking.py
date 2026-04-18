import unittest

import pygame
from pygame import Rect

from gui.utility.guimanager import GuiManager
from gui.utility.input_state import LockStateController
from gui.utility.renderer import Renderer
from gui.utility.widget import Widget


class WidgetStub:
    def __init__(self) -> None:
        self.visible = True
        self.draw_rect = Rect(1, 2, 3, 4)
        self.draw_calls = 0

    def draw(self) -> None:
        self.draw_calls += 1


class SurfaceSpy:
    def __init__(self) -> None:
        self.blit_calls = []

    def blit(self, bitmap, rect):
        self.blit_calls.append((bitmap, rect))


class RendererTests(unittest.TestCase):
    def test_draw_uses_widget_draw_rect_for_buffer_snapshot(self) -> None:
        gui = type("GuiStub", (), {})()
        gui.buffered = True
        gui.widgets = [WidgetStub()]
        gui.windows = []
        gui.task_panel = None
        gui.mouse_locked = False
        gui.mouse_pos = (0, 0)
        gui.mouse_point_locked = False
        gui.lock_point_pos = None
        gui.cursor_image = None
        gui.cursor_hotspot = None
        gui.cursor_rect = None
        gui.surface = pygame.Surface((30, 30))
        copied_rects = []

        def copy_graphic_area(_surface, rect):
            copied_rects.append(Rect(rect))
            return pygame.Surface((rect.width, rect.height))

        gui.copy_graphic_area = copy_graphic_area

        renderer = Renderer(gui)
        renderer.draw()

        self.assertEqual(copied_rects, [Rect(1, 2, 3, 4)])
        self.assertEqual(gui.widgets[0].draw_calls, 1)

    def test_draw_places_cursor_at_lock_point_when_point_locked(self) -> None:
        gui = type("GuiStub", (), {})()
        gui.buffered = False
        gui.widgets = []
        gui.windows = []
        gui.task_panel = None
        gui.mouse_locked = False
        gui.mouse_pos = (50, 60)
        gui.mouse_point_locked = True
        gui.lock_point_pos = (10, 11)
        gui.cursor_image = pygame.Surface((4, 4))
        gui.cursor_hotspot = (1, 2)
        gui.cursor_rect = None
        gui.surface = pygame.Surface((40, 40))

        renderer = Renderer(gui)
        renderer.draw()

        self.assertIsNotNone(gui.cursor_rect)
        self.assertEqual(gui.cursor_rect.topleft, (9, 9))

    def test_undraw_restores_bitmaps_in_reverse_order(self) -> None:
        gui = type("GuiStub", (), {})()
        gui.surface = SurfaceSpy()

        renderer = Renderer(gui)
        b1 = object()
        b2 = object()
        r1 = Rect(1, 1, 2, 2)
        r2 = Rect(3, 3, 4, 4)
        renderer._bitmaps = [(b1, r1), (b2, r2)]

        renderer.undraw()

        self.assertEqual(gui.surface.blit_calls, [(b2, r2), (b1, r1)])
        self.assertEqual(renderer._bitmaps, [])


class LockingBehaviourTests(unittest.TestCase):
    def _build_manager_for_locking(self):
        gui = GuiManager.__new__(GuiManager)
        gui.locking_object = Widget.__new__(Widget)
        gui._is_registered_object = lambda _obj: True
        gui.mouse_locked = True
        gui.mouse_point_locked = False
        gui.lock_area_rect = Rect(10, 20, 5, 6)
        gui.lock_point_pos = None
        gui.lock_point_recenter_pending = False
        gui.lock_point_tolerance_rect = None
        gui.lock_state = LockStateController(gui)
        return gui

    def test_lock_area_clamps_to_rect_bounds(self) -> None:
        gui = self._build_manager_for_locking()

        self.assertEqual(gui.lock_area((0, 0)), (10, 20))
        self.assertEqual(gui.lock_area((999, 999)), (14, 25))
        self.assertEqual(gui.lock_area((12, 23)), (12, 23))

    def test_enforce_point_lock_recenters_once_until_back_inside(self) -> None:
        gui = GuiManager.__new__(GuiManager)
        gui.lock_point_pos = (40, 40)
        gui.lock_point_recenter_pending = False
        gui.point_lock_recenter_rect = Rect(25, 25, 30, 30)
        gui.lock_state = LockStateController(gui)
        set_calls = []
        gui._set_physical_mouse_pos = lambda pos: set_calls.append(pos)

        # Outside recenter rect triggers one recenter and marks pending.
        GuiManager.enforce_point_lock(gui, (0, 0))
        self.assertEqual(set_calls, [gui.point_lock_recenter_rect.center])
        self.assertTrue(gui.lock_point_recenter_pending)

        # Remaining outside while pending should not recenter again.
        GuiManager.enforce_point_lock(gui, (0, 0))
        self.assertEqual(set_calls, [gui.point_lock_recenter_rect.center])

        # Re-entering clears pending state.
        GuiManager.enforce_point_lock(gui, gui.point_lock_recenter_rect.center)
        self.assertFalse(gui.lock_point_recenter_pending)


if __name__ == "__main__":
    unittest.main()
