import unittest
from types import SimpleNamespace

from pygame import Rect

from gui.utility.renderer import Renderer


class _SurfaceSpy:
    def __init__(self):
        self.blit_calls = []

    def blit(self, bitmap, rect):
        self.blit_calls.append((bitmap, rect))


class _WidgetStub:
    def __init__(self, rect: Rect, visible: bool = True) -> None:
        self.draw_rect = rect
        self.visible = visible
        self.draw_calls = 0

    def draw(self) -> None:
        self.draw_calls += 1


class _WindowStub:
    def __init__(self, name: str, rect: Rect, visible: bool = True) -> None:
        self.name = name
        self._rect = rect
        self.visible = visible
        self.widgets = []
        self.x = rect.x
        self.y = rect.y
        self.surface = object()
        self.active_calls = 0
        self.inactive_calls = 0
        self.draw_window_calls = 0

    def get_window_rect(self):
        return Rect(self._rect)

    def draw_title_bar_active(self):
        self.active_calls += 1

    def draw_title_bar_inactive(self):
        self.inactive_calls += 1

    def draw_window(self):
        self.draw_window_calls += 1


class _TaskPanelStub:
    def __init__(self, rect: Rect, visible: bool = True):
        self._rect = rect
        self.visible = visible
        self.widgets = []
        self.surface = object()
        self.x = rect.x
        self.y = rect.y
        self.background_calls = 0

    def get_rect(self):
        return Rect(self._rect)

    def draw_background(self):
        self.background_calls += 1


class RendererAdditionalPathTests(unittest.TestCase):
    def _base_gui(self):
        gui = SimpleNamespace()
        gui.buffered = True
        gui.widgets = []
        gui.windows = []
        gui.task_panel = None
        gui.mouse_locked = False
        gui.mouse_pos = (0, 0)
        gui.mouse_point_locked = False
        gui.lock_point_pos = None
        gui.cursor_image = None
        gui.cursor_hotspot = None
        gui.cursor_rect = None
        gui.surface = _SurfaceSpy()
        gui.copy_graphic_area_calls = []
        gui.copy_graphic_area = lambda _surface, rect: gui.copy_graphic_area_calls.append(Rect(rect)) or object()
        gui.lock_area = lambda pos: pos
        return gui

    def test_draw_renders_windows_with_active_top_and_task_panel(self) -> None:
        gui = self._base_gui()
        w1 = _WindowStub("w1", Rect(10, 20, 30, 10), visible=True)
        w2 = _WindowStub("w2", Rect(15, 25, 40, 12), visible=True)
        w2.widgets = [_WidgetStub(Rect(1, 1, 2, 2), True), _WidgetStub(Rect(1, 1, 2, 2), False)]
        panel = _TaskPanelStub(Rect(0, 90, 100, 10), visible=True)
        panel.widgets = [_WidgetStub(Rect(1, 1, 2, 2), True)]
        gui.windows = [w1, w2]
        gui.task_panel = panel

        renderer = Renderer(gui)
        renderer.draw()

        self.assertEqual(w1.inactive_calls, 1)
        self.assertEqual(w1.active_calls, 0)
        self.assertEqual(w2.active_calls, 1)
        self.assertEqual(w2.inactive_calls, 0)
        self.assertEqual(w1.draw_window_calls, 1)
        self.assertEqual(w2.draw_window_calls, 1)
        self.assertEqual(panel.background_calls, 1)
        self.assertEqual(w2.widgets[0].draw_calls, 1)
        self.assertEqual(w2.widgets[1].draw_calls, 0)
        self.assertEqual(panel.widgets[0].draw_calls, 1)
        self.assertGreaterEqual(len(gui.copy_graphic_area_calls), 3)

    def test_draw_skips_buffer_snapshots_for_zero_sized_regions(self) -> None:
        gui = self._base_gui()
        gui.widgets = [_WidgetStub(Rect(1, 2, 0, 4), True)]
        gui.windows = [_WindowStub("w", Rect(0, 0, 0, 10), visible=True)]
        gui.task_panel = _TaskPanelStub(Rect(0, 0, 0, 10), visible=True)

        renderer = Renderer(gui)
        renderer.draw()

        self.assertEqual(gui.copy_graphic_area_calls, [])

    def test_draw_mouse_locked_updates_mouse_pos_via_lock_area(self) -> None:
        gui = self._base_gui()
        gui.mouse_locked = True
        gui.mouse_pos = (100, 200)
        gui.lock_area = lambda pos: (pos[0] - 1, pos[1] - 2)

        renderer = Renderer(gui)
        renderer.draw()

        self.assertEqual(gui.mouse_pos, (99, 198))

    def test_draw_cursor_captures_snapshot_and_blits(self) -> None:
        gui = self._base_gui()
        gui.cursor_image = object()
        gui.cursor_hotspot = (1, 2)
        gui.cursor_rect = Rect(0, 0, 5, 6)
        gui.mouse_pos = (11, 13)

        renderer = Renderer(gui)
        renderer.draw()

        self.assertEqual(gui.cursor_rect.topleft, (10, 11))
        self.assertIn(Rect(10, 11, 5, 6), gui.copy_graphic_area_calls)
        self.assertEqual(gui.surface.blit_calls[-1], (gui.cursor_image, gui.cursor_rect))

    def test_draw_cursor_initializes_rect_when_missing(self) -> None:
        class _CursorImage:
            def get_rect(self):
                return Rect(0, 0, 4, 4)

        gui = self._base_gui()
        gui.cursor_image = _CursorImage()
        gui.cursor_hotspot = (0, 0)
        gui.cursor_rect = None
        gui.mouse_pos = (3, 4)

        renderer = Renderer(gui)
        renderer.draw()

        self.assertEqual(gui.cursor_rect, Rect(3, 4, 4, 4))


if __name__ == "__main__":
    unittest.main()
