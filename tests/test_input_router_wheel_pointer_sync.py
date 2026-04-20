import unittest
from types import SimpleNamespace

import pygame
from pygame import Rect, SRCALPHA
from pygame.locals import MOUSEWHEEL

from gui.utility.events import InteractiveState, Orientation
from gui.utility.input.input_router import InputRouter
from gui.widgets.scrollbar import Scrollbar
from gui.widgets.slider import Slider


class _FakeGraphicsFactory:
    def centre(self, bigger: int, smaller: int) -> int:
        return int((bigger / 2) - (smaller / 2))

    def build_disabled_bitmap(self, idle_bitmap):
        return idle_bitmap.copy()

    def draw_radio_bitmap(self, size: int, _col1, _col2):
        return pygame.Surface((size, size), SRCALPHA)


class _RouterGuiStub:
    def __init__(self, *, logical_mouse_pos, physical_mouse_pos) -> None:
        self.mouse_pos = logical_mouse_pos
        self._physical_mouse_pos = physical_mouse_pos
        self.dragging = False
        self.dragging_window = None
        self.mouse_delta = None
        self.locking_object = None
        self.task_panel = None
        self.active_window = None
        self.windows = []
        self.widgets = []
        self.graphics_factory = _FakeGraphicsFactory()
        self.input_providers = SimpleNamespace(mouse_get_pos=lambda: self._physical_mouse_pos)
        self.object_registry = SimpleNamespace(is_registered_object=lambda _obj: True)
        self.lock_state = SimpleNamespace(
            resolve=lambda: None,
            clamp_position=lambda pos: pos,
            enforce_point_lock=lambda _pos: None,
        )
        self.focus_state = SimpleNamespace(activate_window_at_pointer=lambda: None)

    def _get_mouse_pos(self):
        return self.mouse_pos

    def _convert_to_window(self, point, _window):
        return point

    def _convert_to_screen(self, point, _window):
        return point

    def update_active_window(self):
        return None

    def update_focus(self, _widget):
        return None

    def handle_widget(self, widget, event, window=None):
        return widget.handle_event(event, window)

    def raise_window(self, _window):
        return None

    def set_lock_area(self, _locking_object, _area=None):
        return None

    def event(self, event_type, **kwargs):
        return SimpleNamespace(type=event_type, **kwargs)


class _WindowStub:
    def __init__(self, widgets, rect: Rect) -> None:
        self.widgets = widgets
        self.visible = True
        self._rect = rect
        self.x = rect.x
        self.y = rect.y

    def get_window_rect(self):
        return self._rect


class InputRouterWheelPointerSyncTests(unittest.TestCase):
    def _build_scrollbar_stub(self, gui: _RouterGuiStub) -> Scrollbar:
        scrollbar = Scrollbar.__new__(Scrollbar)
        scrollbar.gui = gui
        scrollbar.id = "wheel-scrollbar"
        scrollbar._disabled = False
        scrollbar._visible = True
        scrollbar._dragging = False
        scrollbar._hit = False
        scrollbar.state = InteractiveState.Idle
        scrollbar.draw_rect = Rect(0, 0, 180, 24)
        scrollbar.hit_rect = None
        scrollbar._total_range = 100
        scrollbar._start_pos = 10
        scrollbar._bar_size = 20
        scrollbar._inc_size = 5
        scrollbar._wheel_positive_to_max = True
        scrollbar._registered = []
        return scrollbar

    def test_wheel_over_slider_uses_physical_pointer_when_logical_pointer_is_stale(self) -> None:
        gui = _RouterGuiStub(logical_mouse_pos=(999, 999), physical_mouse_pos=(40, 10))
        slider = Slider(
            gui,
            "wheel-slider",
            Rect(0, 0, 120, 20),
            Orientation.Horizontal,
            10,
            5.0,
            False,
            5.0,
            True,
            None,
        )
        gui.widgets = [slider]
        # Ensure physical pointer is inside the wheel-hit corridor.
        gui._physical_mouse_pos = slider._wheel_hit_area().center

        router = InputRouter(gui)
        action = router.route(pygame.event.Event(MOUSEWHEEL, {"y": 1}))

        self.assertAlmostEqual(slider.value, 6.0, places=2)
        self.assertEqual(gui.mouse_pos, slider._wheel_hit_area().center)
        self.assertIsNotNone(action.builder)

    def test_wheel_over_scrollbar_uses_physical_pointer_when_logical_pointer_is_stale(self) -> None:
        gui = _RouterGuiStub(logical_mouse_pos=(999, 999), physical_mouse_pos=(8, 8))
        scrollbar = self._build_scrollbar_stub(gui)
        gui.widgets = [scrollbar]

        router = InputRouter(gui)
        action = router.route(pygame.event.Event(MOUSEWHEEL, {"y": 1}))

        self.assertEqual(scrollbar.start_pos, 15)
        self.assertEqual(gui.mouse_pos, (8, 8))
        self.assertIsNotNone(action.builder)

    def test_wheel_over_window_hosted_slider_uses_physical_pointer_when_logical_pointer_is_stale(self) -> None:
        gui = _RouterGuiStub(logical_mouse_pos=(999, 999), physical_mouse_pos=(40, 10))
        slider = Slider(
            gui,
            "wheel-slider-window",
            Rect(0, 0, 120, 20),
            Orientation.Horizontal,
            10,
            5.0,
            False,
            5.0,
            True,
            None,
        )
        window = _WindowStub([slider], Rect(0, 0, 200, 120))
        gui.windows = [window]
        gui.active_window = window
        gui._physical_mouse_pos = slider._wheel_hit_area().center

        router = InputRouter(gui)
        action = router.route(pygame.event.Event(MOUSEWHEEL, {"y": 1}))

        self.assertAlmostEqual(slider.value, 6.0, places=2)
        self.assertEqual(gui.mouse_pos, slider._wheel_hit_area().center)
        self.assertIsNotNone(action.builder)

    def test_wheel_over_window_hosted_scrollbar_uses_physical_pointer_when_logical_pointer_is_stale(self) -> None:
        gui = _RouterGuiStub(logical_mouse_pos=(999, 999), physical_mouse_pos=(8, 8))
        scrollbar = self._build_scrollbar_stub(gui)
        window = _WindowStub([scrollbar], Rect(0, 0, 220, 140))
        gui.windows = [window]
        gui.active_window = window

        router = InputRouter(gui)
        action = router.route(pygame.event.Event(MOUSEWHEEL, {"y": 1}))

        self.assertEqual(scrollbar.start_pos, 15)
        self.assertEqual(gui.mouse_pos, (8, 8))
        self.assertIsNotNone(action.builder)


if __name__ == "__main__":
    unittest.main()
