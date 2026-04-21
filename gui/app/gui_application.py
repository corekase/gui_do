import pygame
from typing import Callable, Optional
from pygame import Rect

from ..core.input_state import InputState
from ..core.pointer_capture import PointerCapture
from ..core.scene import Scene
from ..core.renderer import Renderer
from ..graphics.legacy_factory import LegacyGraphicsFactory
from ..core.task_scheduler import TaskScheduler
from ..core.timers import Timers
from ..layout.layout_manager import LayoutManager
from ..layout.window_tiling_manager import WindowTilingManager
from ..theme.color_theme import ColorTheme


class GuiApplication:
    """Application facade for scene, input, capture, and rendering."""

    def __init__(self, surface: pygame.Surface) -> None:
        self.surface = surface
        self.input_state = InputState()
        self.pointer_capture = PointerCapture()
        self.scene = Scene()
        self.renderer = Renderer()
        self.scheduler = TaskScheduler()
        self.timers = Timers()
        self.layout = LayoutManager()
        self.window_tiling = WindowTilingManager(self)
        self.theme = ColorTheme()
        self.graphics_factory = LegacyGraphicsFactory(self.theme)
        self.theme.graphics_factory = self.graphics_factory
        self.running = True
        self.mouse_point_locked = False
        self.lock_point_pos = None
        self.locking_object = None
        self.lock_area = None
        self._point_lock_recenter_rect = self._build_point_lock_recenter_rect()
        self._screen_preamble: Optional[Callable[[], None]] = None
        self._screen_event_handler: Optional[Callable[[object], bool]] = None
        self._screen_postamble: Optional[Callable[[], None]] = None

    def add(self, node):
        """Add a root node to the application scene."""
        return self.scene.add(node)

    def update(self, dt_seconds: float) -> None:
        """Update current scene."""
        if self._screen_preamble is not None:
            self._screen_preamble()
        self.timers.update(dt_seconds)
        self.scheduler.update()
        self.scene.update(dt_seconds)
        if self._screen_postamble is not None:
            self._screen_postamble()

    def shutdown(self) -> None:
        """Release runtime services."""
        self.scheduler.shutdown()

    def process_event(self, event) -> bool:
        """Process one pygame event through input normalization and scene dispatch."""
        if event.type == pygame.QUIT:
            self.running = False
            return True
        self.input_state.update_from_event(event)
        if self.lock_area is not None:
            self.input_state.pointer_pos = self._clamp_to_rect(self.input_state.pointer_pos, self.lock_area)
        if self.pointer_capture.lock_rect is not None:
            self.input_state.pointer_pos = self.pointer_capture.clamp(self.input_state.pointer_pos)
        if self.mouse_point_locked and self.lock_point_pos is not None:
            self._enforce_point_lock(event)
            self.input_state.pointer_pos = self.lock_point_pos
        if self._screen_event_handler is not None and self._screen_event_handler(event):
            return True
        return self.scene.dispatch(event, self)

    def set_screen_lifecycle(self, preamble=None, event_handler=None, postamble=None) -> None:
        self._screen_preamble = preamble
        self._screen_event_handler = event_handler
        self._screen_postamble = postamble

    @staticmethod
    def _clamp_to_rect(pos, rect: Rect):
        x = min(max(int(pos[0]), rect.left), rect.right - 1)
        y = min(max(int(pos[1]), rect.top), rect.bottom - 1)
        return (x, y)

    def _build_point_lock_recenter_rect(self) -> Rect:
        bounds = self.surface.get_rect()
        width = max(1, int(bounds.width * 0.8))
        height = max(1, int(bounds.height * 0.8))
        rect = Rect(0, 0, width, height)
        rect.center = bounds.center
        return rect

    def _enforce_point_lock(self, event) -> None:
        if self.lock_point_pos is None:
            return
        event_type = getattr(event, "type", None)
        if event_type not in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
            return
        raw_pos = getattr(event, "pos", None)
        if not (isinstance(raw_pos, tuple) and len(raw_pos) == 2):
            return
        if self._point_lock_recenter_rect.collidepoint(raw_pos):
            return
        pygame.mouse.set_pos(self.lock_point_pos)

    def set_lock_point(self, locking_object, point=None) -> None:
        if locking_object is None:
            self.mouse_point_locked = False
            self.lock_point_pos = None
            self.locking_object = None
            return
        self.locking_object = locking_object
        self._point_lock_recenter_rect = self._build_point_lock_recenter_rect()
        if point is None:
            point = self._point_lock_recenter_rect.center
        clamped = self._clamp_to_rect(point, self._point_lock_recenter_rect)
        self.lock_point_pos = (int(clamped[0]), int(clamped[1]))
        self.mouse_point_locked = True

    def set_lock_area(self, lock_rect) -> None:
        if lock_rect is None:
            self.lock_area = None
            return
        self.lock_area = Rect(lock_rect)

    def convert_to_window(self, point, window):
        if window is None:
            return (int(point[0]), int(point[1]))
        return (int(point[0]) - int(window.rect.left), int(point[1]) - int(window.rect.top))

    def get_lock_point_motion_delta(self, event):
        if not self.mouse_point_locked or self.lock_point_pos is None:
            return None
        if getattr(event, "type", None) != pygame.MOUSEMOTION:
            return None
        raw_pos = getattr(event, "pos", None)
        if not (isinstance(raw_pos, tuple) and len(raw_pos) == 2):
            return None
        dx = int(raw_pos[0]) - int(self.lock_point_pos[0])
        dy = int(raw_pos[1]) - int(self.lock_point_pos[1])
        if dx != 0 or dy != 0:
            pygame.mouse.set_pos(self.lock_point_pos)
            return (dx, dy)
        rel = getattr(event, "rel", None)
        if isinstance(rel, tuple) and len(rel) == 2:
            return (int(rel[0]), int(rel[1]))
        return (0, 0)

    def draw(self) -> None:
        """Render one frame."""
        self.renderer.render(self.surface, self.scene, self.theme)

    def set_window_tiling_enabled(self, enabled: bool, relayout: bool = True) -> None:
        self.window_tiling.set_enabled(enabled, relayout=relayout)

    def configure_window_tiling(
        self,
        *,
        gap=None,
        padding=None,
        avoid_task_panel=None,
        center_on_failure=None,
        relayout: bool = True,
    ) -> None:
        self.window_tiling.configure(
            gap=gap,
            padding=padding,
            avoid_task_panel=avoid_task_panel,
            center_on_failure=center_on_failure,
            relayout=relayout,
        )

    def tile_windows(self, newly_visible=None) -> None:
        self.window_tiling.arrange_windows(newly_visible=newly_visible)

    def read_window_tiling_settings(self):
        return self.window_tiling.read_settings()
