from pygame import Rect
from pygame.event import Event as PygameEvent
from pygame.locals import MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION
from typing import Optional, Tuple, TYPE_CHECKING
from .constants import Event, GuiError
from .widget import Widget

if TYPE_CHECKING:
    from .guimanager import GuiEvent, GuiManager


class LockStateController:
    """Encapsulates input-lock lifecycle and clamping semantics."""

    def __init__(self, gui_manager: "GuiManager") -> None:
        self.gui: "GuiManager" = gui_manager

    def set_area(self, locking_object: Optional[Widget], area: Optional[Rect] = None) -> None:
        if area is not None:
            if not isinstance(area, Rect):
                raise GuiError('lock area must be a Rect')
            if locking_object is None:
                raise GuiError('locking_object is required when setting a lock area')
            if not isinstance(locking_object, Widget):
                raise GuiError('locking_object must be a widget')
            if not self.gui._is_registered_object(locking_object):
                raise GuiError('locking_object must be a registered widget')
            if area.width <= 0 or area.height <= 0:
                raise GuiError('lock area dimensions must be positive')
            self.gui.locking_object = locking_object
            self.gui.mouse_locked = True
            self.gui.mouse_point_locked = False
            self.gui.lock_point_pos = None
            self.gui.lock_point_recenter_pending = False
            self.gui.lock_point_tolerance_rect = None
        else:
            if getattr(self.gui, 'mouse_locked', False):
                if getattr(self.gui, 'mouse_point_locked', False) and getattr(self.gui, 'lock_point_pos', None) is not None:
                    self.gui._set_physical_mouse_pos(self.gui.lock_point_pos)
                    self.gui.mouse_pos = self.gui.lock_point_pos
                else:
                    self.gui._set_physical_mouse_pos(getattr(self.gui, 'mouse_pos', (0, 0)))
            self.clear()
        self.gui.lock_area_rect = area

    def set_point(self, locking_object: Optional[Widget], point: Optional[Tuple[int, int]] = None) -> None:
        if locking_object is None:
            self.set_area(None)
            return
        if not isinstance(locking_object, Widget):
            raise GuiError('locking_object must be a widget')
        if not self.gui._is_registered_object(locking_object):
            raise GuiError('locking_object must be a registered widget')
        if point is None:
            point = self.gui._mouse_get_pos()
        if not isinstance(point, tuple) or len(point) != 2:
            raise GuiError(f'point must be a tuple of (x, y), got: {point}')
        self.gui.locking_object = locking_object
        self.gui.mouse_locked = True
        self.gui.mouse_point_locked = True
        self.gui.lock_area_rect = None
        self.gui.lock_point_pos = point
        self.gui.lock_point_tolerance_rect = None
        self.gui.lock_point_recenter_pending = False

    def resolve(self) -> Optional[Widget]:
        locking_object = getattr(self.gui, 'locking_object', None)
        if locking_object is None:
            if getattr(self.gui, 'mouse_locked', False) or getattr(self.gui, 'lock_area_rect', None) is not None or getattr(self.gui, 'lock_point_pos', None) is not None:
                self.clear()
            return None
        if not isinstance(locking_object, Widget):
            self.clear()
            return None
        if not self.gui._is_registered_object(locking_object):
            self.clear()
            return None
        if getattr(self.gui, 'lock_area_rect', None) is None and getattr(self.gui, 'lock_point_pos', None) is None:
            self.clear()
            return None
        return locking_object

    def clamp_position(self, position: Tuple[int, int]) -> Tuple[int, int]:
        if not isinstance(position, tuple) or len(position) != 2:
            raise GuiError(f'position must be a tuple of (x, y), got: {position}')
        self.resolve()
        lock_area_rect = getattr(self.gui, 'lock_area_rect', None)
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
        if self.gui.lock_point_pos is None:
            self.gui.lock_point_recenter_pending = False
            return
        if not isinstance(hardware_position, tuple) or len(hardware_position) != 2:
            raise GuiError(f'hardware_position must be a tuple of (x, y), got: {hardware_position}')
        in_recenter_rect = self.gui.point_lock_recenter_rect.collidepoint(hardware_position)
        if self.gui.lock_point_recenter_pending:
            if in_recenter_rect:
                self.gui.lock_point_recenter_pending = False
            return
        if not in_recenter_rect:
            self.gui._set_physical_mouse_pos(self.gui.point_lock_recenter_rect.center)
            self.gui.lock_point_recenter_pending = True

    def clear(self) -> None:
        self.gui.locking_object = None
        self.gui.mouse_locked = False
        self.gui.mouse_point_locked = False
        self.gui.lock_area_rect = None
        self.gui.lock_point_pos = None
        self.gui.lock_point_recenter_pending = False
        self.gui.lock_point_tolerance_rect = None


class DragStateController:
    """Encapsulates window drag state transitions and movement updates."""

    def __init__(self, gui_manager: "GuiManager") -> None:
        self.gui: "GuiManager" = gui_manager

    def _pass_event(self) -> "GuiEvent":
        emitter = getattr(self.gui, 'input_emitter', None)
        if emitter is not None:
            return emitter.pass_event()
        return self.gui.event(Event.Pass)

    def reset(self) -> None:
        self.gui.dragging = False
        self.gui.dragging_window = None
        self.gui.mouse_delta = None

    def start_if_possible(self, event: PygameEvent) -> None:
        event_pos = getattr(event, 'pos', self.gui.get_mouse_pos())
        if self.gui.active_window and self.gui.active_window.get_title_bar_rect().collidepoint(self.gui.lock_area(event_pos)):
            if self.gui.active_window.get_widget_rect().collidepoint(self.gui.lock_area(event_pos)):
                self.gui.lower_window(self.gui.active_window)
                self.gui.active_window = self.gui.windows[-1] if self.gui.windows else None
            else:
                self.gui.dragging = True
                self.gui.dragging_window = self.gui.active_window
                self.gui.mouse_delta = (
                    self.gui.dragging_window.x - self.gui.mouse_pos[0],
                    self.gui.dragging_window.y - self.gui.mouse_pos[1],
                )

    def handle_drag_event(self, event: PygameEvent) -> "GuiEvent":
        if (
            self.gui.dragging_window is None
            or self.gui.dragging_window not in self.gui.windows
            or self.gui.mouse_delta is None
        ):
            self.reset()
            return self._pass_event()
        if event.type == MOUSEBUTTONUP and getattr(event, 'button', None) == 1:
            self.gui.dragging = False
            self.gui.dragging_window.position = (self.gui.dragging_window.x, self.gui.dragging_window.y)
            self.gui.set_mouse_pos(
                (
                    self.gui.dragging_window.x - self.gui.mouse_delta[0],
                    self.gui.dragging_window.y - self.gui.mouse_delta[1],
                )
            )
            self.gui.dragging_window = None
            self.gui.mouse_delta = None
        elif event.type == MOUSEMOTION and self.gui.dragging:
            rel = getattr(event, 'rel', (0, 0))
            x = self.gui.dragging_window.x + rel[0]
            y = self.gui.dragging_window.y + rel[1]
            self.gui.set_mouse_pos((x - self.gui.mouse_delta[0], y - self.gui.mouse_delta[1]), False)
            self.gui.dragging_window.position = (x, y)
        return self._pass_event()
