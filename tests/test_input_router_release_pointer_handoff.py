import unittest
from types import SimpleNamespace

import pygame
from pygame import Rect, SRCALPHA
from pygame.locals import MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION

from gui.utility.events import Orientation, ArrowPosition
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

    def build_frame_visuals(self, rect: Rect):
        idle = pygame.Surface((rect.width, rect.height), SRCALPHA)
        hover = pygame.Surface((rect.width, rect.height), SRCALPHA)
        armed = pygame.Surface((rect.width, rect.height), SRCALPHA)
        disabled = pygame.Surface((rect.width, rect.height), SRCALPHA)
        return SimpleNamespace(idle=idle, hover=hover, armed=armed, disabled=disabled)


class _ReleaseRouterGuiStub:
    def __init__(self, *, mouse_pos=(0, 0)) -> None:
        self.mouse_pos = mouse_pos
        self.dragging = False
        self.dragging_window = None
        self.mouse_delta = None
        self.locking_object = None
        self.mouse_locked = False
        self.mouse_point_locked = False
        self.lock_area_rect = None
        self.task_panel = None
        self.active_window = None
        self.windows = []
        self.widgets = []
        self.graphics_factory = _FakeGraphicsFactory()
        self.object_registry = SimpleNamespace(is_registered_object=lambda _obj: True)
        self.focus_state = SimpleNamespace(activate_window_at_pointer=lambda: None)
        self.drag_state = SimpleNamespace(
            start_if_possible=lambda _event, _normalized: None,
            handle_drag_event=lambda _event, _normalized: SimpleNamespace(builder=None),
            reset=lambda: None,
        )
        self._lock_state = SimpleNamespace(release_pointer_hint=None)
        self._lock_state.set_release_pointer_hint = lambda pos: setattr(self._lock_state, 'release_pointer_hint', pos)
        self._lock_state.consume_release_pointer_hint = lambda: self._consume_lock_state_hint()
        self.lock_flow = SimpleNamespace(consume_release_pointer_hint=lambda: self._consume_lock_state_hint())
        self._physical_calls = []
        self.pointer = SimpleNamespace(set_physical_mouse_pos=lambda pos: self._physical_calls.append(pos))
        self.input_providers = SimpleNamespace(mouse_get_pos=lambda: self.mouse_pos)
        self.lock_state = SimpleNamespace(
            resolve=lambda: None,
            clamp_position=self._clamp_position,
            enforce_point_lock=lambda _pos: None,
        )

    @property
    def release_pointer_hint(self):
        return self._lock_state.release_pointer_hint

    @release_pointer_hint.setter
    def release_pointer_hint(self, pos) -> None:
        self._lock_state.set_release_pointer_hint(pos)

    def _consume_lock_state_hint(self):
        hint_pos = self._lock_state.release_pointer_hint
        self._lock_state.release_pointer_hint = None
        return hint_pos

    def _clamp_position(self, pos):
        if not self.mouse_locked or self.lock_area_rect is None:
            return pos
        x, y = pos
        max_x = self.lock_area_rect.right - 1
        max_y = self.lock_area_rect.bottom - 1
        if x < self.lock_area_rect.left:
            x = self.lock_area_rect.left
        elif x > max_x:
            x = max_x
        if y < self.lock_area_rect.top:
            y = self.lock_area_rect.top
        elif y > max_y:
            y = max_y
        return (x, y)

    def _set_mouse_pos(self, pos, _update_physical_coords=False):
        self.mouse_pos = self._clamp_position(pos)

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

    def set_lock_area(self, locking_object, area=None):
        if locking_object is None or area is None:
            self.locking_object = None
            self.mouse_locked = False
            self.mouse_point_locked = False
            self.lock_area_rect = None
            return
        self.locking_object = locking_object
        self.mouse_locked = True
        self.mouse_point_locked = False
        self.lock_area_rect = area

    def event(self, event_type, **kwargs):
        return SimpleNamespace(type=event_type, **kwargs)


class InputRouterReleasePointerHandoffTests(unittest.TestCase):
    def test_slider_release_preserves_release_event_position_without_router_reposition(self) -> None:
        gui = _ReleaseRouterGuiStub()
        slider = Slider(
            gui,
            "release-slider",
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
        router = InputRouter(gui)

        start = slider._handle_area().center
        outside = (slider.draw_rect.right + 40, slider.draw_rect.centery)
        release_inside = (slider.draw_rect.centerx, slider.draw_rect.centery)

        gui.mouse_pos = start
        router.route(pygame.event.Event(MOUSEBUTTONDOWN, {"button": 1, "pos": start}))

        gui.mouse_pos = outside
        router.route(pygame.event.Event(MOUSEMOTION, {"pos": outside, "rel": (400, 0)}))

        gui.mouse_pos = outside
        router.route(pygame.event.Event(MOUSEBUTTONUP, {"button": 1, "pos": release_inside}))

        self.assertEqual(gui.mouse_pos, release_inside)
        self.assertEqual(gui._physical_calls, [])

    def test_scrollbar_release_preserves_release_event_position_without_router_reposition(self) -> None:
        gui = _ReleaseRouterGuiStub(mouse_pos=(25, 15))
        scrollbar = Scrollbar(
            gui,
            "release-scrollbar",
            Rect(0, 0, 220, 30),
            Orientation.Horizontal,
            style=ArrowPosition.Skip,
            total_range=100,
            start_pos=10,
            bar_size=25,
            inc_size=5,
            wheel_positive_to_max=True,
        )
        gui.widgets = [scrollbar]
        router = InputRouter(gui)

        start = scrollbar._handle_area().center
        outside = (scrollbar.draw_rect.right + 50, scrollbar.draw_rect.centery)
        release_inside = (scrollbar.draw_rect.centerx, scrollbar.draw_rect.centery)

        gui.mouse_pos = start
        router.route(pygame.event.Event(MOUSEBUTTONDOWN, {"button": 1, "pos": start}))

        gui.mouse_pos = outside
        router.route(pygame.event.Event(MOUSEMOTION, {"pos": outside, "rel": (500, 0)}))

        gui.mouse_pos = outside
        router.route(pygame.event.Event(MOUSEBUTTONUP, {"button": 1, "pos": release_inside}))

        self.assertEqual(gui.mouse_pos, release_inside)
        self.assertEqual(gui._physical_calls, [])

    def test_slider_boundary_touch_release_uses_release_event_position_without_reposition(self) -> None:
        gui = _ReleaseRouterGuiStub()
        slider = Slider(
            gui,
            "boundary-slider",
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
        router = InputRouter(gui)

        start = slider._handle_area().center
        edge_touch = (slider._graphic_rect.right + slider._drag_anchor_offset, slider.draw_rect.centery)
        release_inside = (slider.draw_rect.centerx, slider.draw_rect.centery)

        gui.mouse_pos = start
        router.route(pygame.event.Event(MOUSEBUTTONDOWN, {"button": 1, "pos": start}))

        gui.mouse_pos = edge_touch
        router.route(pygame.event.Event(MOUSEMOTION, {"pos": edge_touch, "rel": (500, 0)}))

        # No re-entry motion event before release: finalization must honor release event pos.
        gui.mouse_pos = (slider.draw_rect.right - 1, slider.draw_rect.centery)
        router.route(pygame.event.Event(MOUSEBUTTONUP, {"button": 1, "pos": release_inside}))

        self.assertEqual(gui.mouse_pos, release_inside)
        self.assertEqual(gui._physical_calls, [])

    def test_scrollbar_boundary_touch_release_uses_release_event_position_without_reposition(self) -> None:
        gui = _ReleaseRouterGuiStub(mouse_pos=(25, 15))
        scrollbar = Scrollbar(
            gui,
            "boundary-scrollbar",
            Rect(0, 0, 220, 30),
            Orientation.Horizontal,
            style=ArrowPosition.Skip,
            total_range=100,
            start_pos=10,
            bar_size=25,
            inc_size=5,
            wheel_positive_to_max=True,
        )
        gui.widgets = [scrollbar]
        router = InputRouter(gui)

        start = scrollbar._handle_area().center
        edge_touch = (scrollbar._graphic_rect.right - 1, scrollbar.draw_rect.centery)
        release_inside = (scrollbar.draw_rect.centerx, scrollbar.draw_rect.centery)

        gui.mouse_pos = start
        router.route(pygame.event.Event(MOUSEBUTTONDOWN, {"button": 1, "pos": start}))

        gui.mouse_pos = edge_touch
        router.route(pygame.event.Event(MOUSEMOTION, {"pos": edge_touch, "rel": (500, 0)}))

        # No re-entry motion event before release: finalization must honor release event pos.
        gui.mouse_pos = (scrollbar.draw_rect.right - 1, scrollbar.draw_rect.centery)
        router.route(pygame.event.Event(MOUSEBUTTONUP, {"button": 1, "pos": release_inside}))

        self.assertEqual(gui.mouse_pos, release_inside)
        self.assertEqual(gui._physical_calls, [])


if __name__ == "__main__":
    unittest.main()
