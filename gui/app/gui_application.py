import pygame
from pathlib import Path
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
        default_theme = ColorTheme()
        default_factory = LegacyGraphicsFactory(default_theme)
        default_theme.graphics_factory = default_factory
        default_scene = Scene()
        default_window_tiling = WindowTilingManager(self, scene=default_scene)
        self._scenes = {
            "default": {
                "scene": default_scene,
                "scheduler": TaskScheduler(),
                "theme": default_theme,
                "graphics_factory": default_factory,
                "window_tiling": default_window_tiling,
            }
        }
        self._active_scene_name = "default"
        active_runtime = self._scenes[self._active_scene_name]
        self.scene = active_runtime["scene"]
        self.renderer = Renderer()
        self.scheduler = active_runtime["scheduler"]
        self.timers = Timers()
        self.layout = LayoutManager()
        self.window_tiling = active_runtime["window_tiling"]
        self.theme = active_runtime["theme"]
        self.graphics_factory = active_runtime["graphics_factory"]
        self.running = True
        self._logical_pointer_pos = tuple(map(int, pygame.mouse.get_pos()))
        self._last_dispatched_pointer_pos = self._logical_pointer_pos
        self.mouse_point_locked = False
        self.lock_point_pos = None
        self.locking_object = None
        self.lock_area = None
        self._point_lock_recenter_rect = self._build_point_lock_recenter_rect()
        self._lock_point_last_raw_pos = None
        self._cursor_assets = {}
        self._active_cursor_name = None
        self._screen_preamble: Optional[Callable[[], None]] = None
        self._screen_event_handler: Optional[Callable[[object], bool]] = None
        self._screen_postamble: Optional[Callable[[], None]] = None
        self._init_cursor_system()
        self._sync_scene_scheduler_activity(self._active_scene_name)

    @staticmethod
    def _load_pristine_surface(source):
        if source is None:
            return None
        if isinstance(source, pygame.Surface):
            return source.convert()
        if isinstance(source, (str, Path)):
            candidate = Path(source)
            if not candidate.is_absolute():
                root = Path(__file__).resolve().parents[2]
                candidate = root / "data" / "images" / str(source)
            return pygame.image.load(str(candidate)).convert()
        raise TypeError("pristine source must be a Surface or path-like string")

    def add(self, node, scene_name: Optional[str] = None):
        """Add a root node to the application scene."""
        if scene_name is None:
            return self.scene.add(node)
        target = self._scene_runtime(scene_name)
        return target["scene"].add(node)

    def create_scene(self, name: str) -> Scene:
        runtime = self._scene_runtime(name)
        return runtime["scene"]

    def switch_scene(self, name: str) -> None:
        if name not in self._scenes:
            raise ValueError(f"unknown scene: {name}")
        self._active_scene_name = name
        self._sync_scene_scheduler_activity(name)
        runtime = self._scenes[name]
        self.scene = runtime["scene"]
        self.scheduler = runtime["scheduler"]
        self.window_tiling = runtime["window_tiling"]
        self.theme = runtime["theme"]
        self.graphics_factory = runtime["graphics_factory"]

    @property
    def active_scene_name(self) -> str:
        return self._active_scene_name

    def get_scene_scheduler(self, name: str) -> TaskScheduler:
        return self._scene_runtime(name)["scheduler"]

    def get_scene_graphics_factory(self, name: str) -> LegacyGraphicsFactory:
        return self._scene_runtime(name)["graphics_factory"]

    def _create_scene_runtime(self):
        scene = Scene()
        theme = ColorTheme()
        factory = LegacyGraphicsFactory(theme)
        theme.graphics_factory = factory
        return {
            "scene": scene,
            "scheduler": TaskScheduler(),
            "theme": theme,
            "graphics_factory": factory,
            "window_tiling": WindowTilingManager(self, scene=scene),
            "screen_pristine": None,
            "screen_pristine_scaled": None,
            "screen_pristine_scaled_size": (0, 0),
            "scene_auto_suspended": set(),
        }

    def _scene_runtime(self, name: str):
        runtime = self._scenes.get(name)
        if runtime is None:
            runtime = self._create_scene_runtime()
            self._scenes[name] = runtime
        runtime.setdefault("screen_pristine", None)
        runtime.setdefault("screen_pristine_scaled", None)
        runtime.setdefault("screen_pristine_scaled_size", (0, 0))
        runtime.setdefault("scene_auto_suspended", set())
        if "window_tiling" not in runtime:
            runtime["window_tiling"] = WindowTilingManager(self, scene=runtime["scene"])
        return runtime

    def _sync_scene_scheduler_activity(self, active_scene_name: str) -> None:
        for scene_name, runtime in self._scenes.items():
            scheduler = runtime["scheduler"]
            auto_suspended = runtime.setdefault("scene_auto_suspended", set())
            if scene_name == active_scene_name:
                scheduler.set_execution_paused(False)
                if auto_suspended:
                    scheduler.resume_tasks(*tuple(auto_suspended))
                    auto_suspended.clear()
                continue

            scheduler.set_execution_paused(True)
            before = set(scheduler.read_suspended())
            scheduler.suspend_all()
            after = set(scheduler.read_suspended())
            auto_suspended.update(after.difference(before))

    def set_pristine(self, source, scene_name: Optional[str] = None) -> None:
        runtime = self._scenes[self._active_scene_name] if scene_name is None else self._scene_runtime(scene_name)
        runtime["screen_pristine"] = self._load_pristine_surface(source)
        runtime["screen_pristine_scaled"] = None
        runtime["screen_pristine_scaled_size"] = (0, 0)

    def restore_pristine(self, scene_name: Optional[str] = None, surface: Optional[pygame.Surface] = None) -> bool:
        runtime = self._scenes[self._active_scene_name] if scene_name is None else self._scene_runtime(scene_name)
        pristine = runtime.get("screen_pristine")
        if pristine is None:
            return False

        target = self.surface if surface is None else surface
        target_size = target.get_size()
        bitmap = pristine
        if pristine.get_size() != target_size:
            cached = runtime.get("screen_pristine_scaled")
            cached_size = runtime.get("screen_pristine_scaled_size", (0, 0))
            if cached is None or cached_size != target_size:
                cached = pygame.transform.smoothscale(pristine, target_size)
                runtime["screen_pristine_scaled"] = cached
                runtime["screen_pristine_scaled_size"] = target_size
            bitmap = cached
        target.blit(bitmap, (0, 0))
        return True

    def update(self, dt_seconds: float) -> None:
        """Update current scene."""
        if self._screen_preamble is not None:
            self._screen_preamble()
        self.timers.update(dt_seconds)
        runtime = self._scenes[self._active_scene_name]
        runtime["scheduler"].update()
        runtime["scene"].update(dt_seconds)
        if self._screen_postamble is not None:
            self._screen_postamble()

    def shutdown(self) -> None:
        """Release runtime services."""
        seen = set()
        for runtime in self._scenes.values():
            scheduler = runtime["scheduler"]
            marker = id(scheduler)
            if marker in seen:
                continue
            seen.add(marker)
            scheduler.shutdown()

    def process_event(self, event) -> bool:
        """Process one pygame event through input normalization and scene dispatch."""
        if event.type == pygame.QUIT:
            self.running = False
            return True
        self.input_state.update_from_event(event)
        raw_pos = getattr(event, "pos", None)
        if isinstance(raw_pos, tuple) and len(raw_pos) == 2:
            self._logical_pointer_pos = (int(raw_pos[0]), int(raw_pos[1]))
        elif event.type == pygame.MOUSEWHEEL:
            wheel_pos = pygame.mouse.get_pos()
            if isinstance(wheel_pos, tuple) and len(wheel_pos) == 2:
                self._logical_pointer_pos = (int(wheel_pos[0]), int(wheel_pos[1]))
                self.input_state.pointer_pos = self._logical_pointer_pos
        if self.lock_area is not None:
            self._logical_pointer_pos = self._clamp_to_rect(self._logical_pointer_pos, self.lock_area)
            self.input_state.pointer_pos = self._logical_pointer_pos
        if self.pointer_capture.lock_rect is not None:
            self._logical_pointer_pos = self.pointer_capture.clamp(self._logical_pointer_pos)
            self.input_state.pointer_pos = self._logical_pointer_pos
        if self.mouse_point_locked and self.lock_point_pos is not None:
            self._enforce_point_lock(event)
            self._logical_pointer_pos = (int(self.lock_point_pos[0]), int(self.lock_point_pos[1]))
            self.input_state.pointer_pos = self._logical_pointer_pos

        logical_event = self._logicalize_pointer_event(event)

        if self._screen_event_handler is not None and self._screen_event_handler(logical_event):
            return True
        return self.scene.dispatch(logical_event, self)

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
        if event_type != pygame.MOUSEMOTION:
            return
        raw_pos = getattr(event, "pos", None)
        if not (isinstance(raw_pos, tuple) and len(raw_pos) == 2):
            return
        if self._point_lock_recenter_rect.collidepoint(raw_pos):
            return
        pygame.mouse.set_pos(self.lock_point_pos)

    def set_lock_point(self, locking_object, point=None) -> None:
        if locking_object is None:
            if self.mouse_point_locked and self.lock_point_pos is not None:
                release_pos = (int(self.lock_point_pos[0]), int(self.lock_point_pos[1]))
                pygame.mouse.set_pos(release_pos)
                self._logical_pointer_pos = release_pos
                self.input_state.pointer_pos = release_pos
                self._last_dispatched_pointer_pos = release_pos
            self.mouse_point_locked = False
            self.lock_point_pos = None
            self.locking_object = None
            self._lock_point_last_raw_pos = None
            return
        self.locking_object = locking_object
        self._point_lock_recenter_rect = self._build_point_lock_recenter_rect()
        if point is None:
            point = self._point_lock_recenter_rect.center
        self.lock_point_pos = (int(point[0]), int(point[1]))
        self._logical_pointer_pos = self.lock_point_pos
        self.input_state.pointer_pos = self.lock_point_pos
        self._last_dispatched_pointer_pos = self.lock_point_pos
        self._lock_point_last_raw_pos = self.lock_point_pos
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
        raw_pos = getattr(event, "raw_pos", None)
        if raw_pos is None:
            raw_pos = getattr(event, "pos", None)
        if not (isinstance(raw_pos, tuple) and len(raw_pos) == 2):
            return None
        raw_pos = (int(raw_pos[0]), int(raw_pos[1]))
        if raw_pos == self.lock_point_pos:
            self._lock_point_last_raw_pos = raw_pos
            return (0, 0)
        if self._lock_point_last_raw_pos is None:
            self._lock_point_last_raw_pos = raw_pos
        dx = raw_pos[0] - self._lock_point_last_raw_pos[0]
        dy = raw_pos[1] - self._lock_point_last_raw_pos[1]
        self._lock_point_last_raw_pos = raw_pos
        if dx != 0 or dy != 0:
            return (dx, dy)
        rel = getattr(event, "raw_rel", None)
        if rel is None:
            rel = getattr(event, "rel", None)
        if isinstance(rel, tuple) and len(rel) == 2:
            return (int(rel[0]), int(rel[1]))
        return (0, 0)

    @property
    def logical_pointer_pos(self):
        return self._logical_pointer_pos

    def _logicalize_pointer_event(self, event):
        event_type = getattr(event, "type", None)
        if event_type not in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
            return event
        raw_pos = getattr(event, "pos", None)
        if not (isinstance(raw_pos, tuple) and len(raw_pos) == 2):
            return event

        logical_pos = (int(self._logical_pointer_pos[0]), int(self._logical_pointer_pos[1]))
        data = dict(getattr(event, "dict", {}))
        data["raw_pos"] = raw_pos
        data["pos"] = logical_pos

        if event_type == pygame.MOUSEMOTION:
            prev = self._last_dispatched_pointer_pos
            data["raw_rel"] = getattr(event, "rel", None)
            data["rel"] = (logical_pos[0] - prev[0], logical_pos[1] - prev[1])
        self._last_dispatched_pointer_pos = logical_pos
        return pygame.event.Event(event_type, data)

    def _init_cursor_system(self) -> None:
        pygame.mouse.set_visible(False)
        self.register_cursor("normal", "cursor.png", (1, 1))
        self.register_cursor("hand", "hand.png", (12, 12))
        if "normal" in self._cursor_assets:
            self._active_cursor_name = "normal"

    def register_cursor(self, name: str, filename: str, hotspot=(0, 0)) -> None:
        cursor_surface = None
        try:
            root = Path(__file__).resolve().parents[2]
            path = root / "data" / "cursors" / filename
            cursor_surface = pygame.image.load(str(path)).convert_alpha()
        except Exception:
            cursor_surface = None
        if cursor_surface is None:
            cursor_surface = pygame.Surface((12, 12), pygame.SRCALPHA)
            pygame.draw.line(cursor_surface, self.theme.text, (0, 0), (0, 11), 2)
            pygame.draw.line(cursor_surface, self.theme.text, (0, 0), (8, 4), 2)
        self._cursor_assets[name] = (cursor_surface, (int(hotspot[0]), int(hotspot[1])))

    def set_cursor(self, name: str) -> None:
        if name in self._cursor_assets:
            self._active_cursor_name = name

    def get_active_cursor(self):
        if self._active_cursor_name is None:
            return None
        return self._cursor_assets.get(self._active_cursor_name)

    def draw(self) -> None:
        """Render one frame."""
        runtime = self._scenes[self._active_scene_name]
        self.renderer.render(self.surface, runtime["scene"], runtime["theme"], app=self)

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
