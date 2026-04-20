import unittest
import pygame

from pygame import Rect
from pygame.locals import MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION, MOUSEWHEEL
from types import SimpleNamespace

from gui.utility.event_dispatcher import EventDispatcher
from gui.utility.focus_state import FocusStateController
from gui.utility.input.input_emitter import InputEventEmitter
from gui.utility.input.drag_state_controller import DragStateController
from gui.utility.input.lock_state_controller import LockStateController
from gui.utility.gui_utils.lock_state_model import LockState


class WindowStub:
    def __init__(self, x: int, y: int, w: int, h: int, visible: bool = True) -> None:
        self.visible = visible
        self._rect = Rect(x, y, w, h)
        self.widgets = []

    def get_window_rect(self):
        return self._rect


class TaskPanelStub:
    def __init__(self, x: int, y: int, w: int, h: int, visible: bool = True) -> None:
        self.visible = visible
        self._rect = Rect(x, y, w, h)

    def get_rect(self):
        return self._rect


class ActiveWindowGuiStub:
    def __init__(self) -> None:
        self._lock_state = LockState()
        self.dragging = False
        self.dragging_window = None
        self.mouse_delta = None
        self.locking_object = None
        self.task_panel = None
        self.active_window = None
        self.windows = []
        self.widgets = []
        self.mouse_locked = False
        self.mouse_pos = (0, 0)
        self.input_providers = SimpleNamespace(mouse_get_pos=lambda: self.mouse_pos)
        self.lock_area_rect = None
        self.lock_point_pos = None
        self.lock_point_recenter_pending = False
        self.lock_point_tolerance_rect = None
        self.input_emitter = InputEventEmitter(self)
        self.drag_state = DragStateController(self)
        self.focus_state = FocusStateController(self)
        self.lock_state = LockStateController(self)
        self.lock_state.clamp_position = lambda pos: pos

    def _resolve_locking_state(self):
        return self.locking_object

    def get_mouse_pos(self):
        return self.mouse_pos

    def _get_mouse_pos(self):
        return self.mouse_pos

    def lock_area(self, pos):
        return pos

    def enforce_point_lock(self, _pos):
        return None

    def event(self, _event_type, **_kwargs):
        return None

    def update_focus(self, _widget):
        return None

    def update_active_window(self):
        self.focus_state.update_active_window()

    def convert_to_window(self, point, _window):
        return point

    def _convert_to_window(self, point, _window):
        return point

    def handle_widget(self, _widget, _event, _window=None):
        return False

    def raise_window(self, _window):
        return None

    def lower_window(self, _window):
        return None

    def set_lock_area(self, _locking_object, _area=None):
        self.locking_object = None

    def set_mouse_pos(self, pos, _update_physical_coords=True):
        self.mouse_pos = pos


class EventDispatcherActiveWindowRefreshBatch5Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.gui = ActiveWindowGuiStub()
        self.dispatcher = EventDispatcher(self.gui)

    def test_activate_window_at_pointer_chooses_topmost_visible_colliding_window(self) -> None:
        back = WindowStub(0, 0, 100, 100, visible=True)
        front = WindowStub(0, 0, 100, 100, visible=True)
        self.gui.windows = [back, front]
        self.gui.mouse_pos = (10, 10)

        self.gui.focus_state.activate_window_at_pointer()

        self.assertIs(self.gui.active_window, front)

    def test_activate_window_at_pointer_skips_invisible_colliding_window(self) -> None:
        visible = WindowStub(0, 0, 100, 100, visible=True)
        hidden_top = WindowStub(0, 0, 100, 100, visible=False)
        self.gui.windows = [visible, hidden_top]
        self.gui.mouse_pos = (5, 5)

        self.gui.focus_state.activate_window_at_pointer()

        self.assertIs(self.gui.active_window, visible)

    def test_activate_window_at_pointer_clears_active_when_pointer_not_over_any_window(self) -> None:
        active = WindowStub(0, 0, 100, 100, visible=True)
        other = WindowStub(200, 200, 100, 100, visible=True)
        self.gui.windows = [active, other]
        self.gui.active_window = active
        self.gui.mouse_pos = (150, 150)

        self.gui.focus_state.activate_window_at_pointer()

        self.assertIsNone(self.gui.active_window)

    def test_activate_window_at_pointer_keeps_active_when_click_is_on_task_panel(self) -> None:
        active = WindowStub(0, 0, 100, 100, visible=True)
        self.gui.windows = [active]
        self.gui.active_window = active
        self.gui.task_panel = TaskPanelStub(0, 120, 300, 40, visible=True)
        self.gui.mouse_pos = (10, 130)

        self.gui.focus_state.activate_window_at_pointer()

        self.assertIs(self.gui.active_window, active)

    def test_button_down_uses_event_pos_for_task_panel_hit_when_mouse_pos_is_stale(self) -> None:
        active = WindowStub(0, 0, 100, 100, visible=True)
        self.gui.windows = [active]
        self.gui.active_window = active
        self.gui.task_panel = TaskPanelStub(0, 120, 300, 40, visible=True)
        # Stale logical pointer is outside panel and windows.
        self.gui.mouse_pos = (400, 20)

        event = pygame.event.Event(MOUSEBUTTONDOWN, {'button': 1, 'pos': (10, 130)})
        self.dispatcher.router._sync_pointer_from_mouse_event(event)
        self.gui.focus_state.activate_window_at_pointer()

        self.assertIs(self.gui.active_window, active)

    def test_mousewheel_syncs_pointer_from_physical_cursor_for_hit_testing(self) -> None:
        active = WindowStub(0, 0, 100, 100, visible=True)
        self.gui.windows = [active]
        self.gui.active_window = active
        self.gui.task_panel = TaskPanelStub(0, 120, 300, 40, visible=True)
        # Stale logical pointer is outside panel and windows.
        self.gui.mouse_pos = (400, 20)
        # Current physical pointer is over task panel.
        self.gui.input_providers = SimpleNamespace(mouse_get_pos=lambda: (10, 130))

        event = pygame.event.Event(MOUSEWHEEL, {'y': 1})
        self.dispatcher.router._sync_pointer_from_mouse_event(event)
        self.gui.focus_state.activate_window_at_pointer()

        self.assertIs(self.gui.active_window, active)

    def test_button_down_sync_clamps_event_position_when_lock_area_active(self) -> None:
        self.gui.lock_state.clamp_position = lambda pos: (min(max(pos[0], 0), 99), min(max(pos[1], 0), 49))
        self.gui.mouse_pos = (10, 10)

        event = pygame.event.Event(MOUSEBUTTONDOWN, {'button': 1, 'pos': (140, 80)})
        self.dispatcher.router._sync_pointer_from_mouse_event(event)

        self.assertEqual(self.gui.mouse_pos, (99, 49))

    def test_button_up_sync_clamps_event_position_when_lock_area_active(self) -> None:
        self.gui.lock_state.clamp_position = lambda pos: (min(max(pos[0], 0), 99), min(max(pos[1], 0), 49))
        self.gui.mouse_pos = (10, 10)

        event = pygame.event.Event(MOUSEBUTTONUP, {'button': 1, 'pos': (140, 80)})
        self.dispatcher.router._sync_pointer_from_mouse_event(event)

        self.assertEqual(self.gui.mouse_pos, (99, 49))

    def test_first_motion_after_release_is_not_sticky_clamped_after_unlock(self) -> None:
        def clamp_with_optional_lock(position):
            rect = self.gui.lock_area_rect
            if rect is None:
                return position
            return (min(max(position[0], rect.left), rect.right - 1), min(max(position[1], rect.top), rect.bottom - 1))

        self.gui.lock_state.clamp_position = clamp_with_optional_lock
        self.gui.mouse_locked = True
        self.gui.mouse_point_locked = False
        self.gui.lock_area_rect = Rect(0, 0, 100, 50)
        self.gui.mouse_pos = (20, 20)

        release = pygame.event.Event(MOUSEBUTTONUP, {'button': 1, 'pos': (140, 80)})
        self.dispatcher.router._sync_pointer_from_mouse_event(release)
        self.assertEqual(self.gui.mouse_pos, (99, 49))

        self.gui.mouse_locked = False
        self.gui.lock_area_rect = None

        motion = pygame.event.Event(MOUSEMOTION, {'pos': (140, 80), 'rel': (0, 0)})
        self.dispatcher.router._handle_mouse_motion(motion)
        self.assertEqual(self.gui.mouse_pos, (140, 80))

    def test_update_active_window_does_not_switch_when_mouse_moves_over_other_window(self) -> None:
        active = WindowStub(0, 0, 100, 100, visible=True)
        hovered = WindowStub(120, 0, 100, 100, visible=True)
        self.gui.windows = [active, hovered]
        self.gui.active_window = active
        self.gui.mouse_pos = (130, 10)

        self.dispatcher.router._update_active_window()

        self.assertIs(self.gui.active_window, active)

    def test_update_active_window_keeps_current_when_mouse_not_over_any_window(self) -> None:
        active = WindowStub(0, 0, 100, 100, visible=True)
        self.gui.windows = [active]
        self.gui.active_window = active
        self.gui.mouse_pos = (150, 150)

        self.dispatcher.router._update_active_window()

        self.assertIs(self.gui.active_window, active)

    def test_update_active_window_clears_when_current_is_invalid(self) -> None:
        stale_active = WindowStub(0, 0, 100, 100, visible=True)
        other = WindowStub(200, 200, 50, 50, visible=True)
        self.gui.windows = [other]
        self.gui.active_window = stale_active
        self.gui.mouse_pos = (10, 10)

        self.dispatcher.router._update_active_window()

        self.assertIsNone(self.gui.active_window)


if __name__ == "__main__":
    unittest.main()
