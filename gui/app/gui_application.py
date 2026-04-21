import pygame

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

    def add(self, node):
        """Add a root node to the application scene."""
        return self.scene.add(node)

    def update(self, dt_seconds: float) -> None:
        """Update current scene."""
        self.timers.update(dt_seconds)
        self.scheduler.update()
        self.scene.update(dt_seconds)

    def shutdown(self) -> None:
        """Release runtime services."""
        self.scheduler.shutdown()

    def process_event(self, event) -> bool:
        """Process one pygame event through input normalization and scene dispatch."""
        if event.type == pygame.QUIT:
            self.running = False
            return True
        self.input_state.update_from_event(event)
        if self.pointer_capture.lock_rect is not None:
            self.input_state.pointer_pos = self.pointer_capture.clamp(self.input_state.pointer_pos)
        return self.scene.dispatch(event, self)

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
