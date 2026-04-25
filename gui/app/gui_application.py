import pygame
from pathlib import Path
from dataclasses import dataclass, replace
import os
from time import perf_counter
from typing import Callable, Optional
from pygame import Rect

from ..core.event_manager import EventManager
from ..core.gui_event import EventType
from ..core.input_state import InputState
from ..core.pointer_capture import PointerCapture
from ..core.keyboard_manager import KeyboardManager
from ..core.focus_manager import FocusManager
from ..core.action_manager import ActionManager
from ..core.event_bus import EventBus
from ..core.invalidation import InvalidationTracker
from ..core.scene import Scene
from ..core.renderer import Renderer
from ..core.first_frame_profiler import first_frame_profiler
from ..core.telemetry import configure_telemetry
from ..core.telemetry import telemetry_collector
from ..graphics.built_in_factory import BuiltInGraphicsFactory
from ..graphics import load_pristine_surface
from ..core.focus_visualizer import FocusVisualizer
from ..core.task_scheduler import TaskScheduler
from ..core.timers import Timers
from ..layout.layout_manager import LayoutManager
from ..layout.window_tiling_manager import WindowTilingManager
from ..layout.layout_axis import LayoutAxis
from ..controls.window_control import WindowControl
from ..controls.label_control import LabelControl
from ..controls.button_control import ButtonControl
from ..controls.canvas_control import CanvasControl
from ..controls.slider_control import SliderControl
from ..controls.toggle_control import ToggleControl
from ..controls.button_group_control import ButtonGroupControl
from ..controls.arrow_box_control import ArrowBoxControl
from ..controls.frame_control import FrameControl
from ..controls.image_control import ImageControl
from ..controls.scrollbar_control import ScrollbarControl
from ..controls.panel_control import PanelControl
from ..theme.color_theme import ColorTheme
from shared.feature_lifecycle import FeatureManager
from shared.error_handling import logical_error, report_nonfatal_error


@dataclass(frozen=True)
class FeatureUiTypes:
    window_control_cls: type
    label_control_cls: type
    button_control_cls: type
    canvas_control_cls: type
    slider_control_cls: type
    toggle_control_cls: type
    layout_axis_cls: type
    button_group_control_cls: type
    arrow_box_control_cls: type
    frame_control_cls: type
    image_control_cls: type
    scrollbar_control_cls: type
    panel_control_cls: type


class GuiApplication:
    """Application runtime coordinator for scene, input, capture, and rendering."""

    _SCHEDULER_DISPATCH_BUDGET_FRACTION = 0.12
    _SCHEDULER_DISPATCH_BUDGET_MIN_MS = 0.5
    _SCHEDULER_DISPATCH_BUDGET_MAX_MS = 4.0

    def __init__(self, surface: pygame.Surface) -> None:
        self.surface = surface
        self.input_state = InputState()
        self.event_manager = EventManager()
        self.pointer_capture = PointerCapture()
        self.keyboard = KeyboardManager()
        self.focus_visualizer = FocusVisualizer(self)
        self.focus = FocusManager()
        self.actions = ActionManager()
        self.events = EventBus()
        self.invalidation = InvalidationTracker()
        self._scenes = {"default": self._create_scene_runtime()}
        self._active_scene_name = "default"
        active_runtime = self._scenes[self._active_scene_name]
        self.scene = active_runtime["scene"]
        self.renderer = Renderer()
        self.scheduler = active_runtime["scheduler"]
        self.timers = active_runtime["timers"]
        self.layout = LayoutManager()
        self.window_tiling = active_runtime["window_tiling"]
        self.theme = active_runtime["theme"]
        self.graphics_factory = active_runtime["graphics_factory"]
        self._feature_ui_types = FeatureUiTypes(
            window_control_cls=WindowControl,
            label_control_cls=LabelControl,
            button_control_cls=ButtonControl,
            canvas_control_cls=CanvasControl,
            slider_control_cls=SliderControl,
            toggle_control_cls=ToggleControl,
            layout_axis_cls=LayoutAxis,
            button_group_control_cls=ButtonGroupControl,
            arrow_box_control_cls=ArrowBoxControl,
            frame_control_cls=FrameControl,
            image_control_cls=ImageControl,
            scrollbar_control_cls=ScrollbarControl,
            panel_control_cls=PanelControl,
        )
        self.features = FeatureManager(self)
        self.running = True
        self._logical_pointer_pos = tuple(map(int, pygame.mouse.get_pos()))
        self._last_dispatched_pointer_pos = self._logical_pointer_pos
        self._pending_warp_target = None
        self._pending_warp_ignore_budget = 0
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
        self._screen_lifecycle_base = {
            "preamble": None,
            "event_handler": None,
            "postamble": None,
        }
        self._screen_lifecycle_layers = []
        self._screen_lifecycle_next_layer_id = 1
        self._screen_lifecycle_active = False
        self._init_cursor_system()
        self.configure_first_frame_profiling(enabled=os.getenv("GUI_DO_PROFILE_FIRST_OPEN", "").strip().lower() in {"1", "true", "yes", "on"})
        self._sync_scene_scheduler_activity(self._active_scene_name)

    def add(self, node, scene_name: Optional[str] = None):
        """Add a root node to the application scene."""
        if scene_name is None:
            return self.scene.add(node)
        target = self._scene_runtime(scene_name)
        return target["scene"].add(node)

    def read_feature_ui_types(self) -> FeatureUiTypes:
        """Return GUI constructor classes used by feature build routines."""
        return self._feature_ui_types

    def style_label(self, label, size: int = 16, role: str = "body"):
        """Apply consistent demo-friendly defaults to a label-like control."""
        label.font_role = str(role)
        label.font_size = int(size)
        return label

    def create_scene(self, name: str) -> Scene:
        runtime = self._scene_runtime(name)
        return runtime["scene"]

    def switch_scene(self, name: str) -> None:
        collector = telemetry_collector()
        if name not in self._scenes:
            raise logical_error(
                f"unknown scene: {name}",
                subsystem="gui.application",
                operation="GuiApplication.switch_scene",
                exc_type=ValueError,
                details={"scene_name": name},
                source_skip_frames=1,
            )
        with collector.span("gui_application", "switch_scene", metadata={"scene_name": str(name)}):
            self._active_scene_name = name
            self._sync_scene_scheduler_activity(name)
            runtime = self._scenes[name]
            self.scene = runtime["scene"]
            self.scheduler = runtime["scheduler"]
            self.timers = runtime["timers"]
            self.window_tiling = runtime["window_tiling"]
            self.theme = runtime["theme"]
            self.graphics_factory = runtime["graphics_factory"]
            self._apply_screen_lifecycle_chain()

    @property
    def active_scene_name(self) -> str:
        return self._active_scene_name

    def scene_names(self) -> list:
        """Return a list of all registered scene names (including the active one)."""
        return list(self._scenes.keys())

    def has_scene(self, name: str) -> bool:
        """Return True when a scene with *name* has been registered or accessed."""
        return name in self._scenes

    def remove_scene(self, name: str) -> bool:
        """Remove a non-active scene and shut down its scheduler.

        Returns False if the scene does not exist or is the currently active scene
        (active scenes cannot be removed).
        """
        if name not in self._scenes:
            return False
        if name == self._active_scene_name:
            return False
        runtime = self._scenes.pop(name)
        try:
            runtime["scheduler"].shutdown()
        except Exception as exc:
            report_nonfatal_error(
                "scene scheduler shutdown failed during remove_scene",
                kind="logical",
                subsystem="gui.application",
                operation="GuiApplication.remove_scene",
                cause=exc,
                details={"scene_name": name},
                source_skip_frames=1,
            )
        return True

    def get_scene_scheduler(self, name: str) -> TaskScheduler:
        return self._scene_runtime(name)["scheduler"]

    def get_scene_graphics_factory(self, name: str) -> BuiltInGraphicsFactory:
        return self._scene_runtime(name)["graphics_factory"]

    def _create_scene_runtime(self):
        scene = Scene()
        theme = ColorTheme()
        factory = BuiltInGraphicsFactory(theme)
        theme.graphics_factory = factory
        pristine = pygame.Surface(self.surface.get_size())
        pristine.fill((0, 0, 0))
        scheduler = TaskScheduler(max_workers=TaskScheduler.recommended_worker_count())
        # Seed with the nominal 60 FPS frame budget; update() recalculates per-frame.
        scheduler.set_message_dispatch_time_budget_ms(self._compute_scheduler_dispatch_budget_ms(1.0 / 60.0))
        return {
            "scene": scene,
            "scheduler": scheduler,
            "timers": Timers(),
            "theme": theme,
            "graphics_factory": factory,
            "window_tiling": WindowTilingManager(self, scene=scene),
            "screen_pristine": pristine,
            "screen_pristine_scaled": None,
            "screen_pristine_scaled_size": (0, 0),
            "scene_auto_suspended": set(),
        }

    def _scene_runtime(self, name: str):
        runtime = self._scenes.get(name)
        if runtime is None:
            runtime = self._create_scene_runtime()
            self._scenes[name] = runtime
        return runtime

    def _sync_scene_scheduler_activity(self, active_scene_name: str) -> None:
        for scene_name, runtime in self._scenes.items():
            scheduler = runtime["scheduler"]
            auto_suspended = runtime["scene_auto_suspended"]
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
        runtime["screen_pristine"] = load_pristine_surface(source)
        runtime["screen_pristine_scaled"] = None
        runtime["screen_pristine_scaled_size"] = (0, 0)

    def restore_pristine(self, scene_name: Optional[str] = None, surface: Optional[pygame.Surface] = None) -> bool:
        runtime = self._scenes[self._active_scene_name] if scene_name is None else self._scene_runtime(scene_name)
        pristine = runtime["screen_pristine"]
        if pristine is None:
            return False

        target = self.surface if surface is None else surface
        target_size = target.get_size()
        bitmap = pristine
        if pristine.get_size() != target_size:
            cached = runtime["screen_pristine_scaled"]
            cached_size = runtime["screen_pristine_scaled_size"]
            if cached is None or cached_size != target_size:
                scale_start = perf_counter()
                cached = pygame.transform.smoothscale(pristine, target_size)
                scale_elapsed_ms = (perf_counter() - scale_start) * 1000.0
                profiler = first_frame_profiler()
                profiler.record_once(
                    "pristine.scale",
                    f"{self._active_scene_name}:{target_size[0]}x{target_size[1]}",
                    scale_elapsed_ms,
                    detail="restore_pristine smoothscale",
                )
                runtime["screen_pristine_scaled"] = cached
                runtime["screen_pristine_scaled_size"] = target_size
            bitmap = cached
        target.blit(bitmap, (0, 0))
        return True

    def configure_first_frame_profiling(
        self,
        *,
        enabled: bool,
        min_ms: float = 0.25,
        logger: Optional[Callable[[str], None]] = None,
    ) -> None:
        """Enable or disable first-open hotspot profiling.

        Profiling is low-overhead and records one-time expensive operations
        such as font loads and first visual-surface generation.
        """
        profiler = first_frame_profiler()
        profiler.configure(enabled=enabled, min_ms=min_ms, logger=logger)

    def update(self, dt_seconds: float) -> None:
        """Update current scene."""
        collector = telemetry_collector()
        with collector.span("gui_application", "update", metadata={"scene_name": self._active_scene_name}):
            if self._screen_lifecycle_active and self._screen_preamble is not None:
                self._screen_preamble()
            self.focus.update(dt_seconds)
            runtime = self._scenes[self._active_scene_name]
            runtime["timers"].update(dt_seconds)
            runtime["scheduler"].set_message_dispatch_time_budget_ms(self._compute_scheduler_dispatch_budget_ms(dt_seconds))
            runtime["scheduler"].update()
            self.features.update_direct_features(dt_seconds)
            runtime["scene"].update(dt_seconds)
            self.invalidation.invalidate_all()
            self.focus.revalidate_focus(runtime["scene"])
            if self._screen_lifecycle_active and self._screen_postamble is not None:
                self._screen_postamble()
            self.features.update_features()

    def _compute_scheduler_dispatch_budget_ms(self, dt_seconds: float) -> float:
        dt_ms = max(0.0, float(dt_seconds)) * 1000.0
        target_ms = dt_ms * self._SCHEDULER_DISPATCH_BUDGET_FRACTION
        min_ms = self._SCHEDULER_DISPATCH_BUDGET_MIN_MS
        max_ms = self._SCHEDULER_DISPATCH_BUDGET_MAX_MS
        if target_ms < min_ms:
            return min_ms
        if target_ms > max_ms:
            return max_ms
        return target_ms

    def shutdown(self) -> None:
        """Release runtime services."""
        collector = telemetry_collector()
        with collector.span("gui_application", "shutdown"):
            self.features.shutdown_runtime()
            seen = set()
            for runtime in self._scenes.values():
                scheduler = runtime["scheduler"]
                marker = id(scheduler)
                if marker in seen:
                    continue
                seen.add(marker)
                scheduler.shutdown()
        collector.shutdown()

    def process_event(self, event) -> bool:
        """Process one event through normalization and scene dispatch."""
        collector = telemetry_collector()
        with collector.span("gui_application", "process_event"):
            gui_event = self.event_manager.to_gui_event(event, pointer_pos=self._logical_pointer_pos)
            if gui_event.kind == EventType.QUIT:
                self.running = False
                return True
            self.input_state.update_from_event(gui_event)
            if gui_event.kind == EventType.MOUSE_WHEEL:
                wheel_pos = pygame.mouse.get_pos()
                self._logical_pointer_pos = (int(wheel_pos[0]), int(wheel_pos[1]))
                self.input_state.pointer_pos = self._logical_pointer_pos
                gui_event = replace(gui_event, pos=self._logical_pointer_pos, raw_pos=self._logical_pointer_pos)
            raw_pos = gui_event.pos
            if gui_event.kind == EventType.MOUSE_BUTTON_DOWN:
                self._pending_warp_target = None
                self._pending_warp_ignore_budget = 0

        if (
            gui_event.kind == EventType.MOUSE_MOTION
            and self.pointer_capture.lock_rect is not None
            and self.pointer_capture.use_relative_motion
            and isinstance(gui_event.rel, tuple)
            and len(gui_event.rel) == 2
        ):
            # During active pointer capture, treat logical cursor as a virtual cursor
            # advanced by deltas and clamped by lock bounds. This avoids raw absolute
            # overshoot movement debt while retaining lock-rect constraints.
            self._logical_pointer_pos = (
                int(self._logical_pointer_pos[0]) + int(gui_event.rel[0]),
                int(self._logical_pointer_pos[1]) + int(gui_event.rel[1]),
            )
        elif (
            gui_event.kind == EventType.MOUSE_BUTTON_UP
            and self.pointer_capture.lock_rect is not None
            and self.pointer_capture.use_relative_motion
        ):
            # In relative-motion capture mode, hardware cursor may be physically
            # offset from logical drag position. Keep logical position stable on
            # release so controls do not jump on drag-end.
            self._logical_pointer_pos = (int(self._logical_pointer_pos[0]), int(self._logical_pointer_pos[1]))
        elif gui_event.kind == EventType.MOUSE_MOTION and self._pending_warp_target is not None and isinstance(raw_pos, tuple) and len(raw_pos) == 2:
            tx, ty = int(self._pending_warp_target[0]), int(self._pending_warp_target[1])
            rx, ry = int(raw_pos[0]), int(raw_pos[1])
            # After a release-time cursor warp, OS/event queues may emit several stale
            # absolute positions. Keep logical pointer pinned to the warp target
            # until packets converge (or budget expires) so no position debt accrues.
            if abs(rx - tx) <= 1 and abs(ry - ty) <= 1:
                self._pending_warp_target = None
                self._pending_warp_ignore_budget = 0
                self._logical_pointer_pos = (rx, ry)
            elif self._pending_warp_ignore_budget > 0:
                self._pending_warp_ignore_budget -= 1
                self._logical_pointer_pos = (tx, ty)
            else:
                self._pending_warp_target = None
                self._pending_warp_ignore_budget = 0
                self._logical_pointer_pos = (rx, ry)
        elif isinstance(raw_pos, tuple) and len(raw_pos) == 2:
            self._logical_pointer_pos = (int(raw_pos[0]), int(raw_pos[1]))
        if self.lock_area is not None:
            self._logical_pointer_pos = self._clamp_to_rect(self._logical_pointer_pos, self.lock_area)
            self.input_state.pointer_pos = self._logical_pointer_pos
        if self.pointer_capture.lock_rect is not None:
            self._logical_pointer_pos = self.pointer_capture.clamp(self._logical_pointer_pos)
            self.input_state.pointer_pos = self._logical_pointer_pos
        if self.mouse_point_locked and self.lock_point_pos is not None:
            self._enforce_point_lock(gui_event)
            self._logical_pointer_pos = (int(self.lock_point_pos[0]), int(self.lock_point_pos[1]))
            self.input_state.pointer_pos = self._logical_pointer_pos

        logical_event = self._logicalize_pointer_event(gui_event)

        pointer_event_in_window = False
        if logical_event.kind in (EventType.MOUSE_BUTTON_DOWN, EventType.MOUSE_BUTTON_UP, EventType.MOUSE_MOTION, EventType.MOUSE_WHEEL):
            pos = logical_event.pos
            if isinstance(pos, tuple) and len(pos) == 2 and self.scene.top_window_at(pos) is not None:
                pointer_event_in_window = True

        if logical_event.is_mouse_down(1):
            # Mouse click focus: only change focus when a valid mouse-focus target exists.
            # Background clicks intentionally do not mutate focus state.
            target = self.scene.top_focus_target_at(logical_event.pos)
            if target is not None:
                self.focus.set_focus(target)

        if self.keyboard.is_key_event(logical_event):
            with collector.span("gui_application", "route_key_event"):
                consumed = self.keyboard.route_key_event(self.scene, logical_event, self, self._screen_event_handler)
            if consumed or logical_event.default_prevented or logical_event.propagation_stopped:
                self.invalidation.invalidate_all()
                return True

        screen_consumed = False
        if not pointer_event_in_window and self.features.handle_direct_event(logical_event):
            self.invalidation.invalidate_all()
            return True
        if self.features.handle_event(logical_event):
            self.invalidation.invalidate_all()
            return True
        if not pointer_event_in_window and self._screen_lifecycle_active and self._screen_event_handler is not None:
            screen_consumed = bool(self._screen_event_handler(logical_event))
        if screen_consumed or logical_event.default_prevented or logical_event.propagation_stopped:
            self.invalidation.invalidate_all()
            return True
        consumed = self.scene.dispatch(logical_event, self)
        if consumed or logical_event.default_prevented or logical_event.propagation_stopped:
            self.invalidation.invalidate_all()
            return True
        return False

    def set_screen_lifecycle(self, preamble=None, event_handler=None, postamble=None, scene_name: Optional[str] = None) -> None:
        self._screen_lifecycle_base = {
            "preamble": preamble,
            "event_handler": event_handler,
            "postamble": postamble,
            "scene_name": scene_name,
        }
        self._screen_lifecycle_layers.clear()
        self._apply_screen_lifecycle_chain()

    def chain_screen_lifecycle(self, preamble=None, event_handler=None, postamble=None, scene_name: Optional[str] = None):
        """Compose additional lifecycle callbacks without replacing existing ones.

        Returns a disposer callback that removes this layer when invoked.
        """
        layer_id = self._screen_lifecycle_next_layer_id
        self._screen_lifecycle_next_layer_id += 1
        self._screen_lifecycle_layers.append(
            {
                "id": layer_id,
                "preamble": preamble,
                "event_handler": event_handler,
                "postamble": postamble,
                "scene_name": scene_name,
            }
        )
        self._apply_screen_lifecycle_chain()

        def _dispose() -> bool:
            removed = False
            retained_layers = []
            for layer in self._screen_lifecycle_layers:
                if layer.get("id") == layer_id:
                    removed = True
                    continue
                retained_layers.append(layer)
            if removed:
                self._screen_lifecycle_layers = retained_layers
                self._apply_screen_lifecycle_chain()
            return removed

        return _dispose

    def _apply_screen_lifecycle_chain(self) -> None:
        callbacks = [
            entry
            for entry in [self._screen_lifecycle_base, *self._screen_lifecycle_layers]
            if self._screen_callback_matches_scene(entry)
        ]

        preambles = [entry.get("preamble") for entry in callbacks if callable(entry.get("preamble"))]
        if not preambles:
            self._screen_preamble = None
        elif len(preambles) == 1:
            self._screen_preamble = preambles[0]
        else:
            def _composed_preamble() -> None:
                for callback in preambles:
                    callback()

            self._screen_preamble = _composed_preamble

        handlers = [entry.get("event_handler") for entry in callbacks if callable(entry.get("event_handler"))]
        if not handlers:
            self._screen_event_handler = None
        elif len(handlers) == 1:
            self._screen_event_handler = handlers[0]
        else:
            def _composed_event_handler(event) -> bool:
                for callback in handlers:
                    if bool(callback(event)):
                        return True
                return False

            self._screen_event_handler = _composed_event_handler

        postambles = [entry.get("postamble") for entry in callbacks if callable(entry.get("postamble"))]
        if not postambles:
            self._screen_postamble = None
        elif len(postambles) == 1:
            self._screen_postamble = postambles[0]
        else:
            def _composed_postamble() -> None:
                for callback in postambles:
                    callback()

            self._screen_postamble = _composed_postamble

        self._screen_lifecycle_active = bool(preambles or handlers or postambles)

    def _screen_callback_matches_scene(self, callback_entry) -> bool:
        scene_name = callback_entry.get("scene_name")
        if scene_name is None:
            return True
        return str(scene_name) == str(self._active_scene_name)

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
        if not event.is_mouse_motion():
            return
        raw_pos = event.pos
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
        if not event.is_mouse_motion():
            return None
        raw_pos = event.raw_pos
        if not (isinstance(raw_pos, tuple) and len(raw_pos) == 2):
            return None
        raw_pos = (int(raw_pos[0]), int(raw_pos[1]))
        if raw_pos == self.lock_point_pos:
            self._lock_point_last_raw_pos = raw_pos
            rel = event.raw_rel
            if isinstance(rel, tuple) and len(rel) == 2:
                return (int(rel[0]), int(rel[1]))
            return (0, 0)
        if self._lock_point_last_raw_pos is None:
            self._lock_point_last_raw_pos = raw_pos
        dx = raw_pos[0] - self._lock_point_last_raw_pos[0]
        dy = raw_pos[1] - self._lock_point_last_raw_pos[1]
        self._lock_point_last_raw_pos = raw_pos
        if dx != 0 or dy != 0:
            return (dx, dy)
        rel = event.raw_rel
        if isinstance(rel, tuple) and len(rel) == 2:
            return (int(rel[0]), int(rel[1]))
        return (0, 0)

    @property
    def logical_pointer_pos(self):
        return self._logical_pointer_pos

    def set_logical_pointer_position(self, pos, *, apply_constraints: bool = True) -> None:
        """Set logical pointer position and input state pointer in one place."""
        if not (isinstance(pos, tuple) and len(pos) == 2):
            return
        logical = (int(pos[0]), int(pos[1]))
        if apply_constraints:
            if self.lock_area is not None:
                logical = self._clamp_to_rect(logical, self.lock_area)
            if self.pointer_capture.lock_rect is not None:
                logical = self.pointer_capture.clamp(logical)
        self._logical_pointer_pos = logical
        self.input_state.pointer_pos = logical
        self._last_dispatched_pointer_pos = logical

    def sync_pointer_to_logical_position(self, pos) -> None:
        """Align both logical pointer state and hidden hardware cursor."""
        if not (isinstance(pos, tuple) and len(pos) == 2):
            return
        logical = (int(pos[0]), int(pos[1]))
        # Release uses final in-drag logical position as source of truth.
        self.set_logical_pointer_position(logical, apply_constraints=False)
        self._pending_warp_target = logical
        # Ignore a short burst of stale absolute packets after warp.
        self._pending_warp_ignore_budget = 8
        try:
            pygame.mouse.set_pos(logical)
        except Exception as exc:
            report_nonfatal_error(
                "failed to sync hardware pointer to logical pointer position",
                kind="logical",
                subsystem="gui.application",
                operation="GuiApplication.sync_pointer_to_logical_position",
                cause=exc,
                details={"logical": logical},
                source_skip_frames=1,
            )

    def _logicalize_pointer_event(self, event):
        if not event.is_kind(EventType.MOUSE_MOTION, EventType.MOUSE_BUTTON_DOWN, EventType.MOUSE_BUTTON_UP):
            return event
        raw_pos = event.pos
        if not (isinstance(raw_pos, tuple) and len(raw_pos) == 2):
            return event

        logical_pos = (int(self._logical_pointer_pos[0]), int(self._logical_pointer_pos[1]))
        logical_event = replace(event, raw_pos=raw_pos, pos=logical_pos)
        if event.is_mouse_motion():
            prev = self._last_dispatched_pointer_pos
            logical_event = replace(
                logical_event,
                raw_rel=event.rel,
                rel=(logical_pos[0] - prev[0], logical_pos[1] - prev[1]),
            )
        self._last_dispatched_pointer_pos = logical_pos
        return logical_event

    def _init_cursor_system(self) -> None:
        pygame.mouse.set_visible(False)
        self.register_cursor("normal", "cursor.png", (1, 1))
        self.register_cursor("hand", "hand.png", (12, 12))
        if "normal" in self._cursor_assets:
            self._active_cursor_name = "normal"

    def register_cursor(self, name: str, filename: str, hotspot=(0, 0)) -> None:
        cursor_surface = None
        path = None
        try:
            root = Path(__file__).resolve().parents[2]
            path = root / "data" / "cursors" / filename
            cursor_surface = pygame.image.load(str(path)).convert_alpha()
        except Exception as exc:
            report_nonfatal_error(
                "failed to load cursor asset; using fallback cursor",
                kind="io",
                subsystem="gui.application",
                operation="GuiApplication.register_cursor",
                cause=exc,
                path=None if path is None else str(path),
                details={"cursor_name": name, "filename": filename},
                source_skip_frames=1,
            )
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
        collector = telemetry_collector()
        with collector.span("gui_application", "draw", metadata={"scene_name": self._active_scene_name}):
            first_frame_profiler().begin_frame(self._active_scene_name)
            runtime = self._scenes[self._active_scene_name]
            self.renderer.render(self.surface, runtime["scene"], runtime["theme"], app=self)
            self.features.draw(self.surface, runtime["theme"])

    def prewarm_scene(self, scene_name: Optional[str] = None, *, force: bool = False, host=None) -> int:
        """Run one-time feature prewarm hooks for a scene using an offscreen surface.

        When ``host`` is omitted, each feature's registered host context is used.
        """
        target_scene = self._active_scene_name if scene_name is None else str(scene_name)
        runtime = self._scene_runtime(target_scene)
        warm_surface = pygame.Surface(self.surface.get_size(), pygame.SRCALPHA)
        return self.features.prewarm_features(
            host,
            warm_surface,
            runtime["theme"],
            scene_name=target_scene,
            force=force,
        )

    def draw_screen_features(self, surface, theme) -> None:
        """Render dedicated screen features behind scene controls each frame."""
        self.features.draw_direct_features(surface, theme)

    def set_window_tiling_enabled(self, enabled: bool, relayout: bool = True, scene_name: Optional[str] = None) -> None:
        tiling = self._scenes[self._active_scene_name]["window_tiling"] if scene_name is None else self._scene_runtime(scene_name)["window_tiling"]
        tiling.set_enabled(enabled, relayout=relayout)

    def configure_window_tiling(
        self,
        *,
        gap=None,
        padding=None,
        avoid_task_panel=None,
        center_on_failure=None,
        relayout: bool = True,
        scene_name: Optional[str] = None,
    ) -> None:
        tiling = self._scenes[self._active_scene_name]["window_tiling"] if scene_name is None else self._scene_runtime(scene_name)["window_tiling"]
        tiling.configure(
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

    def register_font_role(
        self,
        role_name: str,
        *,
        size: int,
        file_path: Optional[str] = None,
        system_name: Optional[str] = None,
        bold: bool = False,
        italic: bool = False,
        scene_name: Optional[str] = None,
    ) -> None:
        runtime = self._scenes[self._active_scene_name] if scene_name is None else self._scene_runtime(scene_name)
        runtime["theme"].register_font_role(
            role_name,
            size=size,
            file_path=file_path,
            system_name=system_name,
            bold=bold,
            italic=italic,
        )
        self.invalidation.invalidate_all()

    def font_roles(self, scene_name: Optional[str] = None) -> tuple[str, ...]:
        runtime = self._scenes[self._active_scene_name] if scene_name is None else self._scene_runtime(scene_name)
        return runtime["theme"].font_roles()

    # --- Convenience helpers ---

    def run(self, target_fps: int = 60, max_frames: Optional[int] = None) -> int:
        """Run the managed GUI lifecycle loop via UiEngine.

        This keeps lifecycle ownership at the application layer while still
        reusing the engine implementation for frame processing.
        """
        from ..loop.ui_engine import UiEngine

        return UiEngine(self, target_fps=target_fps).run(max_frames=max_frames)

    def quit(self) -> None:
        """Signal the engine to exit the run loop at the end of the current frame."""
        self.running = False

    def find(self, control_id: str, scene_name: Optional[str] = None):
        """Find the first node with *control_id* in the active (or named) scene.

        Shorthand for ``app.scene.find(control_id)``.
        Returns the node, or ``None`` if not found.
        """
        scene = self.scene if scene_name is None else self._scene_runtime(scene_name)["scene"]
        return scene.find(control_id)

    def find_all(self, predicate, scene_name: Optional[str] = None) -> list:
        """Return all nodes in the active (or named) scene that satisfy *predicate*.

        Shorthand for ``app.scene.find_all(predicate)``.
        """
        scene = self.scene if scene_name is None else self._scene_runtime(scene_name)["scene"]
        return scene.find_all(predicate)

    def focus_on(self, control_id: str, scene_name: Optional[str] = None) -> bool:
        """Focus the first focusable node with *control_id* in the active (or named) scene.

        Shorthand for ``app.focus.set_focus_by_id(app.scene, control_id)``.
        Returns ``True`` when a matching focusable node was found and focused.
        """
        scene = self.scene if scene_name is None else self._scene_runtime(scene_name)["scene"]
        return self.focus.set_focus_by_id(scene, control_id)

    # --- Feature helpers ---

    def register_feature(self, feature, host=None):
        """Register a Feature with optional host context.

        Returns the registered feature instance.
        """
        return self.features.register(feature, host=host)

    def unregister_feature(self, name: str, host=None) -> bool:
        """Unregister a Feature by name, returning True when it existed."""
        return self.features.unregister(name, host=host)

    def get_feature(self, name: str):
        """Return a registered Feature by name, or None when absent."""
        return self.features.get(name)

    def feature_names(self) -> tuple[str, ...]:
        """Return registered Feature names in registration order."""
        return self.features.names()

    def send_feature_message(self, sender_name: str, target_feature_name: str, message: dict) -> bool:
        """Send dictionary message between registered features by name."""
        return self.features.send_message(sender_name, target_feature_name, message)

    def bind_feature_logic(self, consumer_feature_name: str, logic_feature_name: str, *, alias: str = "default") -> None:
        """Bind a consumer Feature to a LogicFeature provider under an alias."""
        self.features.bind_logic(consumer_feature_name, logic_feature_name, alias=alias)

    def unbind_feature_logic(self, consumer_feature_name: str, *, alias: str = "default") -> bool:
        """Remove one logic binding alias from a consumer Feature."""
        return self.features.unbind_logic(consumer_feature_name, alias=alias)

    def get_feature_logic(self, consumer_feature_name: str, *, alias: str = "default"):
        """Return a bound LogicFeature provider name for a consumer alias, or None."""
        return self.features.bound_logic_name(consumer_feature_name, alias=alias)

    def send_feature_logic_message(self, consumer_feature_name: str, message: dict, *, alias: str = "default") -> bool:
        """Send a message from a consumer Feature to its bound LogicFeature alias."""
        return self.features.send_logic_message(consumer_feature_name, message, alias=alias)

    def register_feature_runnable(self, feature_name: str, runnable_name: str, runnable) -> None:
        """Register a callable runnable under a registered feature name."""
        self.features.register_runnable(feature_name, runnable_name, runnable)

    def run_feature_runnable(self, feature_name: str, runnable_name: str, *args, **kwargs):
        """Execute a previously registered runnable for a feature."""
        return self.features.run(feature_name, runnable_name, *args, **kwargs)

    def build_features(self, host) -> None:
        """Call optional build(host) on all registered features."""
        collector = telemetry_collector()
        with collector.span("gui_application", "build_features"):
            self.features.build_features(host)
            self._prime_scene_window_tiling_registrations()

    def _prime_scene_window_tiling_registrations(self) -> None:
        """Prime per-scene window registration order without forcing relayout."""
        for runtime in self._scenes.values():
            runtime["window_tiling"].prime_registration()

    def bind_features_runtime(self, host) -> None:
        """Call optional bind_runtime(host) on all registered features."""
        with telemetry_collector().span("gui_application", "bind_features_runtime"):
            self.features.bind_runtime(host)

    def configure_telemetry(
        self,
        *,
        enabled: Optional[bool] = None,
        live_analysis_enabled: Optional[bool] = None,
        file_logging_enabled: Optional[bool] = None,
        min_duration_ms: Optional[float] = None,
        log_directory: Optional[str] = None,
    ):
        """Configure process-wide telemetry collection and optional file logging."""
        return configure_telemetry(
            enabled=enabled,
            live_analysis_enabled=live_analysis_enabled,
            file_logging_enabled=file_logging_enabled,
            min_duration_ms=min_duration_ms,
            log_directory=log_directory,
        )

    def set_telemetry_system_enabled(self, system: str, enabled: bool) -> None:
        """Enable or disable telemetry for one system namespace."""
        telemetry_collector().set_system_enabled(system, enabled)

    def set_telemetry_point_enabled(self, system: str, point: str, enabled: bool) -> None:
        """Enable or disable telemetry for one specific telemetry point."""
        telemetry_collector().set_point_enabled(system, point, enabled)

    def telemetry_summary(self, *, top_n: int = 12):
        """Return collated telemetry hotspot analysis for currently captured samples."""
        return telemetry_collector().summary(top_n=top_n)

    def write_telemetry_report(self, *, top_n: int = 12, output_path: Optional[str] = None) -> Optional[str]:
        """Write a ranked telemetry report and return the generated file path."""
        return telemetry_collector().write_report(top_n=top_n, output_path=output_path)

    def configure_features_accessibility(self, host, tab_index_start: int) -> int:
        """Call optional configure_accessibility(host, index) on features in order."""
        return self.features.configure_accessibility(host, tab_index_start)
