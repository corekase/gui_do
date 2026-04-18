from pygame import Rect
from pygame.event import Event as PygameEvent
from pygame.locals import MOUSEBUTTONUP, MOUSEMOTION
from typing import Optional, Tuple, TYPE_CHECKING
from .constants import GuiError
from .drag_state_model import DragState
from .input_actions import InputAction
from .lock_state_model import LockState
from .widget import Widget

if TYPE_CHECKING:
    from .guimanager import GuiManager


class LockStateController:
    """Encapsulates input-lock lifecycle and clamping semantics."""

    def __init__(self, gui_manager: "GuiManager") -> None:
        self.gui: "GuiManager" = gui_manager

    @property
    def state(self):
        ensure_state = getattr(self.gui, '_ensure_lock_state_data', None)
        if callable(ensure_state):
            return ensure_state()
        state = getattr(self.gui, 'lock_state_data', None)
        if state is None:
            state = LockState(
                locking_object=getattr(self.gui, 'locking_object', None),
                mouse_locked=bool(getattr(self.gui, 'mouse_locked', False)),
                mouse_point_locked=bool(getattr(self.gui, 'mouse_point_locked', False)),
                lock_area_rect=getattr(self.gui, 'lock_area_rect', None),
                lock_point_pos=getattr(self.gui, 'lock_point_pos', None),
                lock_point_recenter_pending=bool(getattr(self.gui, 'lock_point_recenter_pending', False)),
                lock_point_tolerance_rect=getattr(self.gui, 'lock_point_tolerance_rect', None),
            )
            setattr(self.gui, 'lock_state_data', state)
        return state

    def _sync_legacy_lock_fields(self) -> None:
        state = self.state
        self.gui.locking_object = state.locking_object
        self.gui.mouse_locked = state.mouse_locked
        self.gui.mouse_point_locked = state.mouse_point_locked
        self.gui.lock_area_rect = state.lock_area_rect
        self.gui.lock_point_pos = state.lock_point_pos
        self.gui.lock_point_recenter_pending = state.lock_point_recenter_pending
        self.gui.lock_point_tolerance_rect = state.lock_point_tolerance_rect

    def _is_registered_object(self, value: Widget) -> bool:
        registry = getattr(self.gui, 'object_registry', None)
        if registry is not None and hasattr(registry, 'is_registered_object'):
            return bool(registry.is_registered_object(value))
        return False

    def set_area(self, locking_object: Optional[Widget], area: Optional[Rect] = None) -> None:
        if area is not None:
            if not isinstance(area, Rect):
                raise GuiError('lock area must be a Rect')
            if locking_object is None:
                raise GuiError('locking_object is required when setting a lock area')
            if not isinstance(locking_object, Widget):
                raise GuiError('locking_object must be a widget')
            if not self._is_registered_object(locking_object):
                raise GuiError('locking_object must be a registered widget')
            if area.width <= 0 or area.height <= 0:
                raise GuiError('lock area dimensions must be positive')
            self.state.locking_object = locking_object
            self.state.mouse_locked = True
            self.state.mouse_point_locked = False
            self.state.lock_point_pos = None
            self.state.lock_point_recenter_pending = False
            self.state.lock_point_tolerance_rect = None
        else:
            if self.state.mouse_locked:
                if self.state.mouse_point_locked and self.state.lock_point_pos is not None:
                    self.gui.pointer.set_physical_mouse_pos(self.state.lock_point_pos)
                    self.gui.mouse_pos = self.state.lock_point_pos
                else:
                    self.gui.pointer.set_physical_mouse_pos(self.gui.mouse_pos)
            self.clear()
        self.state.lock_area_rect = area
        self._sync_legacy_lock_fields()

    def set_point(self, locking_object: Optional[Widget], point: Optional[Tuple[int, int]] = None) -> None:
        if locking_object is None:
            self.set_area(None)
            return
        if not isinstance(locking_object, Widget):
            raise GuiError('locking_object must be a widget')
        if not self._is_registered_object(locking_object):
            raise GuiError('locking_object must be a registered widget')
        if point is None:
            point = self.gui.input_providers.mouse_get_pos()
        if not isinstance(point, tuple) or len(point) != 2:
            raise GuiError(f'point must be a tuple of (x, y), got: {point}')
        self.state.locking_object = locking_object
        self.state.mouse_locked = True
        self.state.mouse_point_locked = True
        self.state.lock_area_rect = None
        self.state.lock_point_pos = point
        self.state.lock_point_tolerance_rect = None
        self.state.lock_point_recenter_pending = False
        self._sync_legacy_lock_fields()

    def resolve(self) -> Optional[Widget]:
        locking_object = self.state.locking_object
        if locking_object is None:
            if self.state.mouse_locked or self.state.lock_area_rect is not None or self.state.lock_point_pos is not None:
                self.clear()
            return None
        if not isinstance(locking_object, Widget):
            self.clear()
            return None
        if not self._is_registered_object(locking_object):
            self.clear()
            return None
        if self.state.lock_area_rect is None and self.state.lock_point_pos is None:
            self.clear()
            return None
        return locking_object

    def clamp_position(self, position: Tuple[int, int]) -> Tuple[int, int]:
        if not isinstance(position, tuple) or len(position) != 2:
            raise GuiError(f'position must be a tuple of (x, y), got: {position}')
        self.resolve()
        lock_area_rect = self.state.lock_area_rect
        if lock_area_rect is None:
            return position
        x, y = position
        max_x = lock_area_rect.right - 1
        max_y = lock_area_rect.bottom - 1
        if x < lock_area_rect.left:
            x = lock_area_rect.left
        elif x > max_x:
            x = max_x
        if y < lock_area_rect.top:
            y = lock_area_rect.top
        elif y > max_y:
            y = max_y
        return (x, y)

    def enforce_point_lock(self, hardware_position: Tuple[int, int]) -> None:
        if self.state.lock_point_pos is None:
            self.state.lock_point_recenter_pending = False
            return
        if not isinstance(hardware_position, tuple) or len(hardware_position) != 2:
            raise GuiError(f'hardware_position must be a tuple of (x, y), got: {hardware_position}')
        in_recenter_rect = self.gui.point_lock_recenter_rect.collidepoint(hardware_position)
        if self.state.lock_point_recenter_pending:
            if in_recenter_rect:
                self.state.lock_point_recenter_pending = False
                self._sync_legacy_lock_fields()
            return
        if not in_recenter_rect:
            self.gui.pointer.set_physical_mouse_pos(self.gui.point_lock_recenter_rect.center)
            self.state.lock_point_recenter_pending = True
            self._sync_legacy_lock_fields()

    def clear(self) -> None:
        self.state.locking_object = None
        self.state.mouse_locked = False
        self.state.mouse_point_locked = False
        self.state.lock_area_rect = None
        self.state.lock_point_pos = None
        self.state.lock_point_recenter_pending = False
        self.state.lock_point_tolerance_rect = None
        self._sync_legacy_lock_fields()


class DragStateController:
    """Encapsulates window drag state transitions and movement updates."""

    def __init__(self, gui_manager: "GuiManager") -> None:
        self.gui: "GuiManager" = gui_manager

    @property
    def state(self) -> DragState:
        ensure_state = getattr(self.gui, '_ensure_drag_state_data', None)
        if callable(ensure_state):
            return ensure_state()
        state = getattr(self.gui, 'drag_state_data', None)
        if state is None:
            state = DragState(
                dragging=bool(getattr(self.gui, 'dragging', False)),
                dragging_window=getattr(self.gui, 'dragging_window', None),
                mouse_delta=getattr(self.gui, 'mouse_delta', None),
            )
            setattr(self.gui, 'drag_state_data', state)
        return state

    def _pass_event(self) -> InputAction:
        return InputAction.pass_event()

    def _sync_legacy_drag_fields(self) -> None:
        state = self.state
        self.gui.dragging = state.dragging
        self.gui.dragging_window = state.dragging_window
        self.gui.mouse_delta = state.mouse_delta

    def reset(self) -> None:
        self.state.dragging = False
        self.state.dragging_window = None
        self.state.mouse_delta = None
        self._sync_legacy_drag_fields()

    def start_if_possible(self, event: PygameEvent) -> None:
        event_pos = getattr(event, 'pos', self.gui.get_mouse_pos())
        if self.gui.active_window and self.gui.active_window.get_title_bar_rect().collidepoint(self.gui.lock_area(event_pos)):
            if self.gui.active_window.get_widget_rect().collidepoint(self.gui.lock_area(event_pos)):
                self.gui.lower_window(self.gui.active_window)
                self.gui.active_window = self.gui.windows[-1] if self.gui.windows else None
            else:
                self.state.dragging = True
                self.state.dragging_window = self.gui.active_window
                self.state.mouse_delta = (
                    self.state.dragging_window.x - self.gui.mouse_pos[0],
                    self.state.dragging_window.y - self.gui.mouse_pos[1],
                )
                self._sync_legacy_drag_fields()

    def handle_drag_event(self, event: PygameEvent) -> InputAction:
        if (
            self.state.dragging_window is None
            or self.state.dragging_window not in self.gui.windows
            or self.state.mouse_delta is None
        ):
            self.reset()
            return self._pass_event()
        if event.type == MOUSEBUTTONUP and getattr(event, 'button', None) == 1:
            self.state.dragging = False
            self.state.dragging_window.position = (self.state.dragging_window.x, self.state.dragging_window.y)
            self.gui.set_mouse_pos(
                (
                    self.state.dragging_window.x - self.state.mouse_delta[0],
                    self.state.dragging_window.y - self.state.mouse_delta[1],
                )
            )
            self.state.dragging_window = None
            self.state.mouse_delta = None
            self._sync_legacy_drag_fields()
        elif event.type == MOUSEMOTION and self.state.dragging:
            rel = getattr(event, 'rel', (0, 0))
            x = self.state.dragging_window.x + rel[0]
            y = self.state.dragging_window.y + rel[1]
            self.gui.set_mouse_pos((x - self.state.mouse_delta[0], y - self.state.mouse_delta[1]), False)
            self.state.dragging_window.position = (x, y)
            self._sync_legacy_drag_fields()
        return self._pass_event()
