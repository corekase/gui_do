import pygame
from collections import deque
from pathlib import Path
from dataclasses import replace
import os
from time import perf_counter
from typing import Callable, Optional
from pygame import Rect

from ..events.gui_event import EventType
from ..events.input_processing import EventManager, InputState
from ..events.pointer_capture import PointerCapture
from ..events.keyboard_manager import KeyboardManager
from ..focus.focus_manager import FocusManager
from ..actions.action_manager import ActionManager
from ..events.event_bus import EventBus
from ..data.invalidation import InvalidationTracker
from .scene import Scene
from .renderer import Renderer
from .first_frame_profiler import first_frame_profiler
from ..telemetry.telemetry import configure_telemetry
from ..telemetry.telemetry import telemetry_collector
from ..graphics.built_in_factory import BuiltInGraphicsFactory
from ..graphics import load_pristine_surface
from ..focus.focus_visualizer import FocusVisualizer
from ..focus.window_focus_manager import WindowFocusManager
from ..focus.task_panel_focus_manager import TaskPanelFocusManager
from ..scheduling.task_scheduler import TaskScheduler
from ..scheduling.timers import Timers
from ..layout.anchor_layout import AnchorLayout
from ..layout.window_layout_handler import WindowLayoutHandler
from ..theme.color_theme import ColorTheme
from ..features.feature_lifecycle import FeatureManager
from .error_handling import logical_error, report_nonfatal_error
from .input_event_kinds import LOGICALIZE_KINDS, POINTER_EVENT_KINDS
from .runtime_entries import _FallthroughEntry, _SceneRuntime, _ScreenLifecycleEntry
from ..scheduling.tween_manager import TweenManager
from ..overlays.overlay_manager import OverlayManager
from ..overlays.toast_manager import ToastManager
from ..overlays.dialog_manager import DialogManager
from ..overlays.drag_drop_manager import DragDropManager
from ..persistence.workspace_persistence import WorkspacePersistenceManager, DEFAULT_WORKSPACE_STATE_PATH

class GuiApplication:
    """Application runtime coordinator for scene, input, capture, and rendering."""

    _SCHEDULER_DISPATCH_BUDGET_FRACTION = 0.10
    _SCHEDULER_DISPATCH_BUDGET_MIN_MS = 0.35
    _SCHEDULER_DISPATCH_BUDGET_MAX_MS = 2.5
    _DEFERRED_PREWARM_BUDGET_FRACTION = 0.02
    _DEFERRED_PREWARM_BUDGET_MIN_MS = 0.10
    _DEFERRED_PREWARM_BUDGET_MAX_MS = 0.35
    _DEFERRED_PREWARM_MAX_STEPS_PER_FRAME = 1

    def __init__(self, surface: pygame.Surface, font_roles=None) -> None:
        self.surface = surface
        self.font_roles = font_roles
        self.input_state = InputState()
        self.event_manager = EventManager()
        self.pointer_capture = PointerCapture()
        self.keyboard = KeyboardManager()
        self.focus_visualizer = FocusVisualizer(self)
        self.focus = FocusManager()
        self.focus.add_focus_change_listener(self._on_focus_changed)
        self.window_focus = WindowFocusManager()
        self.task_panel_focus = TaskPanelFocusManager()
        self._last_active_window = None
        self.actions = ActionManager()
        self.events = EventBus()
        self.invalidation = InvalidationTracker()
        self._scenes = {"default": self._create_scene_runtime()}
        self._scene_pretty_names = {"default": "default"}
        self._active_scene_name = "default"
        active_runtime = self._scenes[self._active_scene_name]
        self.scene = active_runtime.scene
        self.renderer = Renderer()
        self.scheduler = active_runtime.scheduler
        self.timers = active_runtime.timers
        self.tweens = active_runtime.tweens
        self.overlay = active_runtime.overlay
        self.drag_drop = active_runtime.drag_drop
        self.layout = AnchorLayout()
        self.window_tiling = active_runtime.window_tiling
        self.theme = active_runtime.theme
        self.graphics_factory = active_runtime.graphics_factory
        self.features = FeatureManager(self)
        self.toasts = ToastManager(self.surface.get_rect())
        self.events.subscribe("toast", self.toasts.on_event_bus_message)
        self.running = True
        self._logical_pointer_pos = (0, 0)
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
        self._screen_lifecycle_base = _ScreenLifecycleEntry()
        self._screen_lifecycle_layers: list[_ScreenLifecycleEntry] = []
        self._screen_lifecycle_next_layer_id = 1
        self._screen_lifecycle_active = False
        self._fallthrough_handlers: list[_FallthroughEntry] = []
        self._fallthrough_next_id = 1
        self._init_cursor_system()
        self.configure_first_frame_profiling(enabled=os.getenv("GUI_DO_PROFILE_FIRST_OPEN", "").strip().lower() in {"1", "true", "yes", "on"})
        self._sync_scene_scheduler_activity(self._active_scene_name)
        self._dialogs: Optional[DialogManager] = None
        self._startup_scene_prewarm_jobs: deque[tuple[str, bool]] = deque()
        self._startup_scene_prewarm_job_keys: set[str] = set()
        self._scene_deferred_prewarm_jobs: dict[str, deque[tuple[str, Callable[[pygame.Surface, "ColorTheme"], None]]]] = {}
        self._scene_deferred_prewarm_job_keys: dict[str, set[str]] = {}
        self._startup_prewarm_overlay_armed = True
        self._startup_prewarm_overlay_started = False
        self._startup_prewarm_overlay_visible = False
        self._startup_prewarm_completed_startup_steps = 0
        self._startup_prewarm_completed_deferred_steps = 0
        self._startup_prewarm_total_steps = 0
        self._scheduler_backlog_ema: float = 0.0
        # Wire the invalidation tracker into the initial active scene so that
        # per-control invalidate() calls register dirty rects immediately.
        self.invalidation.set_screen_size(self.surface.get_size())
        self.scene.set_invalidation_tracker(self.invalidation)

    def _ensure_startup_prewarm_state(self) -> None:
        if not hasattr(self, "_startup_scene_prewarm_jobs"):
            self._startup_scene_prewarm_jobs = deque()
        if not hasattr(self, "_startup_scene_prewarm_job_keys"):
            self._startup_scene_prewarm_job_keys = set()

    def _ensure_startup_prewarm_overlay_state(self) -> None:
        if not hasattr(self, "_startup_prewarm_overlay_armed"):
            self._startup_prewarm_overlay_armed = True
        if not hasattr(self, "_startup_prewarm_overlay_started"):
            self._startup_prewarm_overlay_started = False
        if not hasattr(self, "_startup_prewarm_overlay_visible"):
            self._startup_prewarm_overlay_visible = False
        if not hasattr(self, "_startup_prewarm_completed_startup_steps"):
            self._startup_prewarm_completed_startup_steps = 0
        if not hasattr(self, "_startup_prewarm_completed_deferred_steps"):
            self._startup_prewarm_completed_deferred_steps = 0
        if not hasattr(self, "_startup_prewarm_total_steps"):
            self._startup_prewarm_total_steps = 0

    def _startup_prewarm_overlay_pending(self) -> bool:
        self._ensure_startup_prewarm_state()
        self._ensure_deferred_prewarm_state()
        startup_pending = bool(self._startup_scene_prewarm_jobs)
        active_deferred_pending = bool(self._scene_deferred_prewarm_jobs.get(self._active_scene_name))
        return startup_pending or active_deferred_pending

    def _update_startup_prewarm_overlay_state(self, dt_seconds: float) -> None:
        self._ensure_startup_prewarm_overlay_state()
        if not self._startup_prewarm_overlay_armed:
            self._startup_prewarm_overlay_visible = False
            return

        pending = self._startup_prewarm_overlay_pending()
        if pending:
            self._startup_prewarm_overlay_started = True
            self._startup_prewarm_overlay_visible = True
            _ = dt_seconds
            return

        self._startup_prewarm_overlay_visible = False
        if self._startup_prewarm_overlay_started:
            self._startup_prewarm_overlay_armed = False

    def _draw_startup_prewarm_overlay(self, surface: pygame.Surface, theme: "ColorTheme") -> None:
        self._ensure_startup_prewarm_overlay_state()
        if not self._startup_prewarm_overlay_visible:
            return

        width, height = surface.get_size()
        dim = pygame.Surface((width, height), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 88))
        surface.blit(dim, (0, 0))

        frame_width = max(260, min(460, width - 48))
        frame_height = 126
        frame_rect = Rect(
            (width - frame_width) // 2,
            (height - frame_height) // 2,
            frame_width,
            frame_height,
        )
        pygame.draw.rect(surface, theme.dark, frame_rect, border_radius=10)
        pygame.draw.rect(surface, theme.light, frame_rect, width=2, border_radius=10)

        title_surface = None
        try:
            title_surface = theme.render_text("Prewarming", role="heading", size=22, shadow=False)
        except Exception:
            title_surface = None
        if title_surface is None:
            fallback_font = pygame.font.Font(None, 28)
            title_surface = fallback_font.render("Prewarming", True, theme.text)

        title_rect = title_surface.get_rect(midtop=(frame_rect.centerx, frame_rect.top + 14))
        surface.blit(title_surface, title_rect)

        track_rect = Rect(frame_rect.left + 22, frame_rect.top + 68, frame_rect.width - 44, 28)
        pygame.draw.rect(surface, theme.background, track_rect, border_radius=7)
        pygame.draw.rect(surface, theme.light, track_rect, width=1, border_radius=7)

        known_total = max(1, int(self._startup_prewarm_total_steps))
        completed = self._startup_prewarm_completed_startup_steps + self._startup_prewarm_completed_deferred_steps
        progress_ratio = max(0.0, min(1.0, float(completed) / float(known_total)))
        inner = track_rect.inflate(-6, -6)
        fill_width = int(round(inner.width * progress_ratio))
        if fill_width > 0:
            fill_rect = Rect(inner.left, inner.top, fill_width, inner.height)
            pygame.draw.rect(surface, theme.highlight, fill_rect, border_radius=5)

    def queue_scene_prewarm(self, scene_name: Optional[str] = None, *, force: bool = False) -> bool:
        target_scene = self._active_scene_name if scene_name is None else str(scene_name)
        self._ensure_startup_prewarm_state()
        self._ensure_startup_prewarm_overlay_state()
        if target_scene in self._startup_scene_prewarm_job_keys:
            return False
        self._startup_scene_prewarm_jobs.append((target_scene, bool(force)))
        self._startup_scene_prewarm_job_keys.add(target_scene)
        self._startup_prewarm_total_steps += 1
        return True

    def _run_startup_scene_prewarm_jobs(self, *, max_steps: Optional[int] = None) -> int:
        self._ensure_startup_prewarm_state()
        self._ensure_startup_prewarm_overlay_state()
        if not self._startup_scene_prewarm_jobs:
            return 0

        steps = 0
        while self._startup_scene_prewarm_jobs:
            if max_steps is not None and steps >= int(max_steps):
                break
            scene_name, force = self._startup_scene_prewarm_jobs.popleft()
            try:
                self.prewarm_scene(scene_name, force=force)
            finally:
                self._startup_scene_prewarm_job_keys.discard(scene_name)
            steps += 1
            self._startup_prewarm_completed_startup_steps += 1

        return steps

    def _ensure_deferred_prewarm_state(self) -> None:
        if not hasattr(self, "_scene_deferred_prewarm_jobs"):
            self._scene_deferred_prewarm_jobs = {}
        if not hasattr(self, "_scene_deferred_prewarm_job_keys"):
            self._scene_deferred_prewarm_job_keys = {}

    def _enqueue_scene_deferred_prewarm_job(
        self,
        scene_name: str,
        key: str,
        job: Callable[[pygame.Surface, "ColorTheme"], None],
    ) -> bool:
        self._ensure_deferred_prewarm_state()
        self._ensure_startup_prewarm_overlay_state()
        scene_key = str(scene_name)
        keys = self._scene_deferred_prewarm_job_keys.setdefault(scene_key, set())
        if key in keys:
            return False
        queue = self._scene_deferred_prewarm_jobs.setdefault(scene_key, deque())
        queue.append((str(key), job))
        keys.add(str(key))
        self._startup_prewarm_total_steps += 1
        return True

    def _run_deferred_scene_prewarm_jobs(
        self,
        scene_name: str,
        surface: pygame.Surface,
        theme: "ColorTheme",
        *,
        budget_ms: Optional[float] = None,
        max_steps: Optional[int] = None,
    ) -> int:
        self._ensure_deferred_prewarm_state()
        self._ensure_startup_prewarm_overlay_state()
        scene_key = str(scene_name)
        queue = self._scene_deferred_prewarm_jobs.get(scene_key)
        if not queue:
            return 0

        steps = 0
        start = perf_counter()
        while queue:
            if max_steps is not None and steps >= int(max_steps):
                break
            if budget_ms is not None and steps > 0:
                elapsed_ms = (perf_counter() - start) * 1000.0
                if elapsed_ms >= float(budget_ms):
                    break
            key, job = queue.popleft()
            try:
                job(surface, theme)
            except Exception as exc:
                report_nonfatal_error(
                    "deferred scene prewarm job failed",
                    kind="logical",
                    subsystem="gui.application",
                    operation="GuiApplication._run_deferred_scene_prewarm_jobs",
                    cause=exc,
                    details={"scene_name": scene_key, "job_key": key},
                    source_skip_frames=1,
                )
            finally:
                keys = self._scene_deferred_prewarm_job_keys.get(scene_key)
                if keys is not None:
                    keys.discard(key)
            steps += 1
            self._startup_prewarm_completed_deferred_steps += 1

        if not queue:
            self._scene_deferred_prewarm_jobs.pop(scene_key, None)
            self._scene_deferred_prewarm_job_keys.pop(scene_key, None)
        return steps

    def _draw_window_content_only(self, window, surface: pygame.Surface, theme: "ColorTheme") -> None:
        children = list(getattr(window, "children", ()) or ())
        if not children:
            draw = getattr(window, "draw", None)
            if callable(draw):
                draw(surface, theme)
            return

        previous_clip = surface.get_clip()
        content_rect_fn = getattr(window, "content_rect", None)
        if callable(content_rect_fn):
            clip_rect = previous_clip.clip(content_rect_fn())
            surface.set_clip(clip_rect)
        try:
            for child in children:
                if not bool(getattr(child, "visible", False)):
                    continue
                draw = getattr(child, "draw", None)
                if callable(draw):
                    draw(surface, theme)
        finally:
            surface.set_clip(previous_clip)

    def _schedule_hidden_window_child_prewarm(self, scene_name: str, window) -> int:
        find_descendants_of_type = getattr(window, "find_descendants_of_type", None)
        if not callable(find_descendants_of_type):
            return 0

        try:
            from ..controls.data.tab_control import TabControl
        except Exception:
            return 0

        tab_controls = list(find_descendants_of_type(TabControl))
        if not tab_controls:
            return 0

        scheduled = 0
        for tab_control in tab_controls:
            items_fn = getattr(tab_control, "items", None)
            select_fn = getattr(tab_control, "select", None)
            if not callable(items_fn) or not callable(select_fn):
                continue

            original_key = getattr(tab_control, "selected_key", None)
            enabled_keys = [
                str(item.key)
                for item in items_fn()
                if bool(getattr(item, "enabled", False))
            ]
            warm_keys = [key for key in enabled_keys if key != original_key]
            if not warm_keys:
                continue

            window_id = id(window)
            tab_id = id(tab_control)
            for key in warm_keys:
                job_key = f"window:{window_id}:tab:{tab_id}:select:{key}"

                def _warm_tab(surface, theme, tab=tab_control, target_key=key, host_window=window):
                    tab.select(target_key)
                    self._draw_window_content_only(host_window, surface, theme)

                if self._enqueue_scene_deferred_prewarm_job(scene_name, job_key, _warm_tab):
                    scheduled += 1

            if original_key is not None:
                restore_key = str(original_key)
                restore_job_key = f"window:{window_id}:tab:{tab_id}:restore:{restore_key}"

                def _restore_tab(_surface, _theme, tab=tab_control, key=restore_key):
                    tab.select(key)

                if self._enqueue_scene_deferred_prewarm_job(scene_name, restore_job_key, _restore_tab):
                    scheduled += 1

        return scheduled

    def _on_focus_changed(self, _previous, current) -> None:
        focused_id = current.control_id if current is not None else None
        dismissed = self.overlay.dismiss_for_focus(focused_id)
        if dismissed:
            self.invalidation.invalidate_all()

    @property
    def dialogs(self) -> "DialogManager":
        """Per-application dialog manager (lazy-initialised)."""
        if self._dialogs is None:
            self._dialogs = DialogManager(self)
        return self._dialogs

    def add(self, node, scene_name: Optional[str] = None):
        """Add a root node to the application scene."""
        if scene_name is None:
            return self.scene.add(node)
        target = self._scene_runtime(scene_name)
        return target.scene.add(node)

    def style_label(self, label, size: int = 16, role: str = "body"):
        """Apply consistent demo-friendly defaults to a label-like control."""
        label.font_role = str(role)
        label.font_size = int(size)
        return label

    def create_scene(self, name: str, *, pretty_name: Optional[str] = None) -> Scene:
        runtime = self._scene_runtime(name)
        if pretty_name is not None:
            normalized = str(pretty_name).strip()
            self._scene_pretty_names[name] = normalized if normalized else name
        elif name not in self._scene_pretty_names:
            self._scene_pretty_names[name] = name
        # --- Automatically apply all font roles for this scene if a registry exists ---
        if self.font_roles is not None:
            try:
                self.font_roles.apply(self, scene_name=name)
            except Exception:
                pass  # Don't block scene creation if font role registration fails
        return runtime.scene

    def switch_scene(self, name: str) -> None:
        collector = telemetry_collector()
        runtime = self._scenes.get(name)
        if runtime is None:
            raise logical_error(
                f"unknown scene: {name}",
                subsystem="gui.application",
                operation="GuiApplication.switch_scene",
                exc_type=ValueError,
                details={"scene_name": name},
                source_skip_frames=1,
            )
        with collector.span("gui_application", "switch_scene", metadata={"scene_name": str(name)}):
            outgoing_scene = self.scene
            if self.task_panel_focus.is_active:
                # Exit task-panel focus mode before swapping runtime references so
                # remembered scope and hover teardown apply to the outgoing scene.
                self.task_panel_focus.exit(outgoing_scene, self)
            self._reconcile_task_panel_hover_state(outgoing_scene, force_idle=True)
            self._snap_autohide_task_panels_lowered(outgoing_scene)
            self._active_scene_name = name
            self._sync_scene_scheduler_activity(name)
            self.scene = runtime.scene
            self.scheduler = runtime.scheduler
            self.timers = runtime.timers
            self.tweens = runtime.tweens
            if self.overlay is not runtime.overlay:
                self.overlay.hide_all()
            self.overlay = runtime.overlay
            self.drag_drop = runtime.drag_drop
            self.window_tiling = runtime.window_tiling
            self.theme = runtime.theme
            self.graphics_factory = runtime.graphics_factory
            # Re-wire the global invalidation tracker into the incoming scene so
            # that all nodes registered to it emit dirty rects on invalidate().
            self.scene.set_invalidation_tracker(self.invalidation)
            # --- Automatically apply all font roles for this scene if a registry exists ---
            if self.font_roles is not None:
                try:
                    self.font_roles.apply(self, scene_name=name)
                except Exception:
                    pass  # Don't block scene switch if font role registration fails
            self._reconcile_task_panel_hover_state(self.scene, pointer_pos=self._logical_pointer_pos)
            self._apply_screen_lifecycle_chain()

    def _reconcile_task_panel_hover_state(self, scene: Scene, *, pointer_pos=None, force_idle: bool = False) -> None:
        if scene is None:
            return
        probe = None
        if not force_idle and isinstance(pointer_pos, tuple) and len(pointer_pos) == 2:
            probe = (int(pointer_pos[0]), int(pointer_pos[1]))
        for node in scene._walk_nodes():
            if not node.is_task_panel():
                continue
            wants_hover = False
            if probe is not None and node.visible and node.enabled:
                wants_hover = bool(node.rect.collidepoint(probe))
            node.reconcile_hover(wants_hover)
            # Walk the subtree inline (BFS) without materializing a result list.
            queue = list(node.children)
            i = 0
            while i < len(queue):
                child = queue[i]
                i += 1
                child_wants_hover = False
                if probe is not None and child.visible and child.enabled:
                    child_wants_hover = bool(child.rect.collidepoint(probe))
                child.reconcile_hover(child_wants_hover)
                if child.children:
                    queue.extend(child.children)

    def _reconcile_scene_hover_state(self, scene: Scene, *, pointer_pos=None, force_idle: bool = False) -> None:
        """Normalize scene-wide hover flags for all nodes.

        Used by top-layer input consumers (for example toasts) to keep
        underlying controls from retaining stale hover visuals when pointer
        events are intentionally intercepted before scene dispatch.
        """
        if scene is None:
            return
        probe = None
        if not force_idle and isinstance(pointer_pos, tuple) and len(pointer_pos) == 2:
            probe = (int(pointer_pos[0]), int(pointer_pos[1]))
        for node in scene._walk_nodes():
            wants_hover = False
            if probe is not None and node.visible and node.enabled:
                wants_hover = bool(node.rect.collidepoint(probe))
            node.reconcile_hover(wants_hover)

    def _snap_autohide_task_panels_lowered(self, scene) -> None:
        """Snap every autohide task panel in *scene* to its fully-lowered position.

        Called during scene transitions so a raised autohide panel does not
        visually linger mid-slide when the incoming scene is displayed.
        """
        if scene is None:
            return
        for node in scene._walk_nodes():
            if node.is_task_panel() and getattr(node, "auto_hide", False):
                node.snap_to_lowered()

    @property
    def active_scene_name(self) -> str:
        return self._active_scene_name

    def scene_names(self) -> list:
        """Return a list of all registered scene names (including the active one)."""
        return list(self._scenes.keys())

    def scene_pretty_name(self, name: str) -> str:
        """Return display-friendly scene label for *name*."""
        return str(self._scene_pretty_names.get(name, name))

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
            runtime.scheduler.shutdown()
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
        return self._scene_runtime(name).scheduler

    def _create_scene_runtime(self) -> "_SceneRuntime":
        scene = Scene()
        # Always use the global font_roles registry for every scene
        theme = ColorTheme()
        factory = BuiltInGraphicsFactory(theme)
        theme.graphics_factory = factory
        pristine = pygame.Surface(self.surface.get_size())
        pristine.fill((0, 0, 0))
        scheduler = TaskScheduler(max_workers=TaskScheduler.recommended_worker_count())
        # Seed with the nominal 60 FPS frame budget; update() recalculates per-frame.
        scheduler.set_message_dispatch_time_budget_ms(self._compute_scheduler_dispatch_budget_ms(1.0 / 60.0))
        return _SceneRuntime(
            scene=scene,
            scheduler=scheduler,
            timers=Timers(),
            theme=theme,
            graphics_factory=factory,
            window_tiling=WindowLayoutHandler(self, scene=scene),
            tweens=TweenManager(),
            overlay=OverlayManager(),
            drag_drop=DragDropManager(),
            screen_pristine=pristine,
            screen_pristine_scaled=None,
            screen_pristine_scaled_size=(0, 0),
            scene_auto_suspended=set(),
        )

    def _scene_runtime(self, name: str):
        runtime = self._scenes.get(name)
        if runtime is None:
            runtime = self._create_scene_runtime()
            self._scenes[name] = runtime
            self._scene_pretty_names.setdefault(name, name)
        return runtime

    def _sync_scene_scheduler_activity(self, active_scene_name: str) -> None:
        for scene_name, runtime in self._scenes.items():
            scheduler = runtime.scheduler
            auto_suspended = runtime.scene_auto_suspended
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
        runtime.screen_pristine = load_pristine_surface(source)
        runtime.screen_pristine_scaled = None
        runtime.screen_pristine_scaled_size = (0, 0)

    def restore_pristine(self, scene_name: Optional[str] = None, surface: Optional[pygame.Surface] = None) -> bool:
        runtime = self._scenes[self._active_scene_name] if scene_name is None else self._scene_runtime(scene_name)
        pristine = runtime.screen_pristine
        if pristine is None:
            return False

        target = self.surface if surface is None else surface
        target_size = target.get_size()
        bitmap = pristine
        if pristine.get_size() != target_size:
            cached = runtime.screen_pristine_scaled
            cached_size = runtime.screen_pristine_scaled_size
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
                runtime.screen_pristine_scaled = cached
                runtime.screen_pristine_scaled_size = target_size
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
            self.window_focus.update(dt_seconds)
            self.timers.update(dt_seconds)
            self.tweens.update(dt_seconds)
            self.toasts.update(dt_seconds, self.tweens)
            self.scheduler.set_message_dispatch_time_budget_ms(self._compute_scheduler_dispatch_budget_ms(dt_seconds))
            self.scheduler.update()
            self.features.update_direct_features(dt_seconds)
            self.scene.update(dt_seconds)
            self.invalidation.invalidate_all()
            # Cache the full BFS walk once to use across all revalidation methods.
            # This eliminates redundant O(n_nodes) walks across focus, window_focus,
            # and task_panel_focus revalidation in a single frame.
            cached_walk = self.scene._get_cached_bfs_walk()
            self.focus.revalidate_focus(self.scene, cached_walk_nodes=cached_walk)
            self.window_focus.revalidate(self.scene, cached_walk_nodes=cached_walk)
            self.task_panel_focus.revalidate(self.scene, self)
            active_window = self.scene.active_window()
            if active_window is not self._last_active_window:
                self._last_active_window = active_window
                if active_window is not None:
                    self.focus.restore_remembered_focus_for_window(self.scene, active_window)
            if self._screen_lifecycle_active and self._screen_postamble is not None:
                self._screen_postamble()
            self.features.update_features()
            runtime = self._scenes[self._active_scene_name]
            self._update_startup_prewarm_overlay_state(dt_seconds)
            if self._startup_scene_prewarm_jobs:
                self._run_startup_scene_prewarm_jobs(max_steps=1)
            if self._scene_deferred_prewarm_jobs.get(self._active_scene_name):
                warm_surface = pygame.Surface(self.surface.get_size(), pygame.SRCALPHA)
                self._run_deferred_scene_prewarm_jobs(
                    self._active_scene_name,
                    warm_surface,
                    runtime.theme,
                    budget_ms=self._compute_deferred_prewarm_budget_ms(dt_seconds),
                    max_steps=self._DEFERRED_PREWARM_MAX_STEPS_PER_FRAME,
                )
            self._update_startup_prewarm_overlay_state(dt_seconds)

    def _compute_scheduler_dispatch_budget_ms(self, dt_seconds: float) -> float:
        dt_ms = (dt_seconds if dt_seconds > 0.0 else 0.0) * 1000.0
        target_ms = dt_ms * self._SCHEDULER_DISPATCH_BUDGET_FRACTION
        scheduler = getattr(self, "scheduler", None)
        if scheduler is not None:
            pressure = 0.0
            try:
                pending = float(scheduler.pending_count())
                running = float(scheduler.running_count())
                pressure = pending + max(0.0, running - 1.0)
            except Exception:
                pressure = 0.0
            self._scheduler_backlog_ema = (self._scheduler_backlog_ema * 0.8) + (pressure * 0.2)
            target_ms += min(1.0, self._scheduler_backlog_ema * 0.08)
        min_ms = self._SCHEDULER_DISPATCH_BUDGET_MIN_MS
        max_ms = self._SCHEDULER_DISPATCH_BUDGET_MAX_MS
        if target_ms < min_ms:
            return min_ms
        if target_ms > max_ms:
            return max_ms
        return target_ms

    def _compute_deferred_prewarm_budget_ms(self, dt_seconds: float) -> float:
        dt_ms = (dt_seconds if dt_seconds > 0.0 else 0.0) * 1000.0
        target_ms = dt_ms * self._DEFERRED_PREWARM_BUDGET_FRACTION
        min_ms = self._DEFERRED_PREWARM_BUDGET_MIN_MS
        max_ms = self._DEFERRED_PREWARM_BUDGET_MAX_MS
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
                scheduler = runtime.scheduler
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
                can_sync_from_hardware = (
                    not self.mouse_point_locked
                    and not (
                        self.pointer_capture.lock_rect is not None
                        and self.pointer_capture.use_relative_motion
                    )
                )
                # Always use logical pointer position for GUI logic
                pass
            raw_pos = gui_event.pos
            normalized_raw_pos = None
            if isinstance(raw_pos, tuple) and len(raw_pos) == 2:
                normalized_raw_pos = (int(raw_pos[0]), int(raw_pos[1]))
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
        elif gui_event.kind == EventType.MOUSE_MOTION and self._pending_warp_target is not None and normalized_raw_pos is not None:
            tx, ty = int(self._pending_warp_target[0]), int(self._pending_warp_target[1])
            rx, ry = normalized_raw_pos
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
        elif normalized_raw_pos is not None:
            self._logical_pointer_pos = normalized_raw_pos
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
        is_pointer_event = logical_event.kind in POINTER_EVENT_KINDS

        # Toasts render above overlays/scene. Pointer hits on toast bounds are
        # consumed so pointer state does not fall through to underlying controls.
        if is_pointer_event and self.toasts.route_event(logical_event, self):
            self._reconcile_scene_hover_state(self.scene, force_idle=True)
            self.invalidation.invalidate_all()
            return True

        if self.task_panel_focus.should_exit_for_pointer_event(logical_event, self):
            self.task_panel_focus.exit(self.scene, self)

        pointer_event_in_window = False
        pointer_focus_target = None
        if is_pointer_event:
            pointer_event_in_window, pointer_focus_target = self.scene.pointer_context_at(logical_event.pos)

        if is_pointer_event:
            is_lmb_down = logical_event.is_mouse_down(1)
            # IMPORTANT: for mouse-down clicks inside an open overlay, route the overlay
            # BEFORE changing scene-graph focus.  Setting focus first triggers
            # on_focus_changed(False) on the focused control (e.g. a menu bar), which
            # dismisses any open flyout before the click can reach it.
            click_in_overlay = (
                is_lmb_down
                and self.overlay.point_in_any_overlay(logical_event.pos)
            )
            if click_in_overlay:
                # Overlay click: route to overlay first, defer focus change.
                overlay_consumed = self.overlay.route_event(logical_event, self)
                if overlay_consumed:
                    self.invalidation.invalidate_all()
                    return True
                # Click was inside overlay rect but not consumed (e.g. padding area);
                # fall through to normal focus change + scene dispatch.
                if pointer_focus_target is not None:
                    self.focus.set_focus(pointer_focus_target)
            else:
                # Normal path: for mouse-down, apply focus first (background clicks
                # intentionally do not mutate focus state).
                if is_lmb_down and pointer_focus_target is not None:
                    self.focus.set_focus(pointer_focus_target)
                overlay_consumed = self.overlay.route_event(logical_event, self)
                if overlay_consumed:
                    self.invalidation.invalidate_all()
                    return True

        if self.keyboard.is_key_event(logical_event):
            # Give overlays first chance to handle key events (e.g. ESC to dismiss)
            if self.overlay.route_event(logical_event, self):
                self.invalidation.invalidate_all()
                return True
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
        consumed = self.scene.dispatch(logical_event, self, theme=self.theme)
        if consumed or logical_event.default_prevented or logical_event.propagation_stopped:
            self.invalidation.invalidate_all()
            return True
        active_scene = self._active_scene_name
        for ft_entry in self._fallthrough_handlers:
            if ft_entry.scene_name is not None and ft_entry.scene_name != active_scene:
                continue
            if bool(ft_entry.event_handler(logical_event)):
                self.invalidation.invalidate_all()
                return True
        return False

    def process_events(self, events) -> int:
        """Process a batch of events and return the number of consumed events."""
        consumed_count = 0
        for event in events:
            if self.process_event(event):
                consumed_count += 1
            if not self.running:
                break
        return consumed_count

    def set_screen_lifecycle(self, preamble=None, event_handler=None, postamble=None, scene_name: Optional[str] = None) -> None:
        self._screen_lifecycle_base = _ScreenLifecycleEntry(
            preamble=preamble,
            event_handler=event_handler,
            postamble=postamble,
            scene_name=scene_name,
        )
        self._screen_lifecycle_layers.clear()
        self._apply_screen_lifecycle_chain()

    def chain_screen_fallthrough(self, event_handler, *, scene_name: Optional[str] = None):
        """Register a handler that fires only when no earlier handler consumed an event.

        The *event_handler* is called at the very end of :meth:`process_event`,
        after the scene graph dispatch, only if the event is still unconsumed.
        Returns a disposer callable that removes this handler when invoked.
        """
        layer_id = self._fallthrough_next_id
        self._fallthrough_next_id += 1
        entry = _FallthroughEntry(event_handler=event_handler, scene_name=scene_name, entry_id=layer_id)
        self._fallthrough_handlers.append(entry)

        def _dispose() -> bool:
            removed = False
            retained = []
            for h in self._fallthrough_handlers:
                if h.entry_id == layer_id:
                    removed = True
                    continue
                retained.append(h)
            if removed:
                self._fallthrough_handlers = retained
            return removed

        return _dispose

    def chain_screen_lifecycle(self, preamble=None, event_handler=None, postamble=None, scene_name: Optional[str] = None):
        """Compose additional lifecycle callbacks without replacing existing ones.

        Returns a disposer callback that removes this layer when invoked.
        """
        layer_id = self._screen_lifecycle_next_layer_id
        self._screen_lifecycle_next_layer_id += 1
        self._screen_lifecycle_layers.append(
            _ScreenLifecycleEntry(
                preamble=preamble,
                event_handler=event_handler,
                postamble=postamble,
                scene_name=scene_name,
                entry_id=layer_id,
            )
        )
        self._apply_screen_lifecycle_chain()

        def _dispose() -> bool:
            removed = False
            retained_layers = []
            for layer in self._screen_lifecycle_layers:
                if layer.entry_id == layer_id:
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

        preambles = [entry.preamble for entry in callbacks if callable(entry.preamble)]
        if not preambles:
            self._screen_preamble = None
        elif len(preambles) == 1:
            self._screen_preamble = preambles[0]
        else:
            def _composed_preamble() -> None:
                for callback in preambles:
                    callback()

            self._screen_preamble = _composed_preamble

        handlers = [entry.event_handler for entry in callbacks if callable(entry.event_handler)]
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

        postambles = [entry.postamble for entry in callbacks if callable(entry.postamble)]
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

    def _screen_callback_matches_scene(self, callback_entry: "_ScreenLifecycleEntry") -> bool:
        scene_name = callback_entry.scene_name
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
        point_x = int(point[0])
        point_y = int(point[1])
        if window is None:
            return (point_x, point_y)
        rect = window.rect
        return (point_x - int(rect.left), point_y - int(rect.top))

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
        if event.kind not in LOGICALIZE_KINDS:
            return event
        raw_pos = event.pos
        if not (isinstance(raw_pos, tuple) and len(raw_pos) == 2):
            return event

        logical_pos = self._logical_pointer_pos
        if event.kind is EventType.MOUSE_MOTION:
            prev = self._last_dispatched_pointer_pos
            logical_event = replace(
                event,
                raw_pos=raw_pos,
                pos=logical_pos,
                raw_rel=event.rel,
                rel=(logical_pos[0] - prev[0], logical_pos[1] - prev[1]),
            )
        else:
            logical_event = replace(event, raw_pos=raw_pos, pos=logical_pos)
        self._last_dispatched_pointer_pos = logical_pos
        return logical_event

    def _init_cursor_system(self) -> None:
        if pygame.display.get_init():
            pygame.mouse.set_visible(False)

    def register_cursor(self, name: str, path: str | Path, hotspot=(0, 0)) -> None:
        """Register a named cursor image. *path* is resolved relative to the application CWD."""
        cursor_surface = None
        resolved_path = None
        try:
            resolved_path = Path(path) if Path(path).is_absolute() else Path.cwd() / path
            loaded = pygame.image.load(str(resolved_path))
            try:
                cursor_surface = loaded.convert_alpha()
            except pygame.error:
                cursor_surface = loaded
        except Exception as exc:
            report_nonfatal_error(
                "failed to load cursor asset; using fallback cursor",
                kind="io",
                subsystem="gui.application",
                operation="GuiApplication.register_cursor",
                cause=exc,
                path=None if resolved_path is None else str(resolved_path),
                details={"cursor_name": name, "path": str(path)},
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

    def draw(self):
        """Render one frame. Returns list of dirty rects or None (full redraw)."""
        collector = telemetry_collector()
        with collector.span("gui_application", "draw", metadata={"scene_name": self._active_scene_name}):
            first_frame_profiler().begin_frame(self._active_scene_name)
            runtime = self._scenes[self._active_scene_name]
            dirty = self.renderer.render(self.surface, runtime.scene, runtime.theme, app=self)
            self.features.draw(self.surface, runtime.theme)
            transition_mgr = getattr(self, "_scene_transition_manager", None)
            if transition_mgr is not None:
                transition_mgr.draw(self.surface)
            self._draw_startup_prewarm_overlay(self.surface, runtime.theme)
            return dirty

    def prewarm_scene(self, scene_name: Optional[str] = None, *, force: bool = False, host=None) -> int:
        """Run one-time feature prewarm hooks for a scene using an offscreen surface.

        When ``host`` is omitted, each feature's registered host context is used.
        """
        target_scene = self._active_scene_name if scene_name is None else str(scene_name)
        runtime = self._scene_runtime(target_scene)
        warm_surface = pygame.Surface(self.surface.get_size(), pygame.SRCALPHA)
        # Prime per-scene pristine scaling cache so first visible draw of a
        # non-initial scene does not pay smoothscale cost during transition.
        self.restore_pristine(scene_name=target_scene, surface=warm_surface)
        warmed = self.features.prewarm_features(
            host,
            warm_surface,
            runtime.theme,
            scene_name=target_scene,
            force=force,
        )

        # Run one synthetic scene frame to warm lazy control internals that are
        # initialized in update()/draw() rather than feature prewarm hooks.
        runtime.scene.update(0.0)
        runtime.scene.draw(warm_surface, runtime.theme)
        self._prewarm_hidden_windows(runtime.scene, warm_surface, runtime.theme, scene_name=target_scene)
        return warmed

    def _prewarm_hidden_windows(
        self,
        scene: "Scene",
        surface: pygame.Surface,
        theme: "ColorTheme",
        *,
        scene_name: Optional[str] = None,
    ) -> int:
        """Draw hidden windows once so first user show does not hitch on lazy visuals."""
        query_windows = getattr(scene, "_window_query_nodes", None)
        if not callable(query_windows):
            return 0

        target_scene = self._active_scene_name if scene_name is None else str(scene_name)
        windows, _task_panels = query_windows()
        warmed = 0
        for window in windows:
            if bool(getattr(window, "visible", False)):
                continue
            draw = getattr(window, "draw", None)
            if not callable(draw):
                continue
            draw(surface, theme)
            self._schedule_hidden_window_child_prewarm(target_scene, window)
            warmed += 1
        return warmed

    def draw_screen_features(self, surface, theme) -> None:
        """Render dedicated screen features behind scene controls each frame."""
        self.features.draw_direct_features(surface, theme)

    def set_window_tiling_enabled(self, enabled: bool, relayout: bool = True, scene_name: Optional[str] = None) -> None:
        tiling = self._scenes[self._active_scene_name].window_tiling if scene_name is None else self._scene_runtime(scene_name).window_tiling
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
        tiling = self._scenes[self._active_scene_name].window_tiling if scene_name is None else self._scene_runtime(scene_name).window_tiling
        tiling.configure(
            gap=gap,
            padding=padding,
            avoid_task_panel=avoid_task_panel,
            center_on_failure=center_on_failure,
            relayout=relayout,
        )

    def tile_windows(self, newly_visible=None) -> None:
        self.window_tiling.arrange_windows(newly_visible=newly_visible)

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
        # Always update the FontManager for the correct scene
        if scene_name is not None:
            runtime = self._scene_runtime(scene_name)
        else:
            runtime = self._scenes[self._active_scene_name]
        runtime.theme.register_font_role(
            role_name,
            size=size,
            file_path=file_path,
            system_name=system_name,
            bold=bold,
            italic=italic,
        )
        self.invalidation.invalidate_all()

    # --- Convenience helpers ---

    def run(self, target_fps: int = 60, max_frames: Optional[int] = None) -> int:
        """Run the managed GUI lifecycle loop via UiEngine.

        This keeps lifecycle ownership at the application layer while still
        reusing the engine implementation for frame processing.
        """
        from .ui_engine import UiEngine

        return UiEngine(self, target_fps=target_fps).run(max_frames=max_frames)

    def run_entrypoint(
        self,
        target_fps: int = 120,
        *,
        WORKSPACE_SAVE: bool = False,
        workspace_manager: Optional[WorkspacePersistenceManager] = None,
        workspace_path: str | Path = DEFAULT_WORKSPACE_STATE_PATH,
    ) -> int:
        """Run app loop with final-layer exception handling and pygame shutdown.

        This helper is intended for top-level script entrypoints. It ensures
        that any unhandled runtime error is routed through gui_do's built-in
        nonfatal error reporting before terminating the process with an OS
        exit code.
        """
        save_workspace = bool(WORKSPACE_SAVE)
        manager = workspace_manager if workspace_manager is not None else WorkspacePersistenceManager()
        exit_code = 0
        try:
            if save_workspace:
                try:
                    self.load_workspace(manager, workspace_path)
                except Exception:
                    # Missing/invalid workspace state should not block app startup.
                    pass
            self.run(target_fps=target_fps)
        except Exception as exc:
            report_nonfatal_error(
                "top-level application run failed",
                kind="runtime",
                subsystem="app",
                operation="run_entrypoint",
                cause=exc,
                details={"target_fps": int(target_fps)},
            )
            exit_code = 1
        finally:
            if save_workspace:
                try:
                    self.save_workspace(manager, workspace_path)
                except Exception:
                    pass
            pygame.quit()
        raise SystemExit(exit_code)

    def quit(self) -> None:
        """Signal the engine to exit the run loop at the end of the current frame."""
        self.running = False

    def capture_workspace(self, workspace_manager, *, metadata: Optional[dict] = None):
        """Capture a coordinated workspace state using the registered features."""
        return workspace_manager.capture(self, feature_manager=self.features, metadata=metadata)

    def restore_workspace(self, workspace_manager, state):
        """Restore workspace state and return the manager's structured report."""
        return workspace_manager.restore(state, self, feature_manager=self.features)

    def save_workspace(self, workspace_manager, path: str | Path, *, metadata: Optional[dict] = None):
        """Capture and save a workspace state to disk."""
        state = self.capture_workspace(workspace_manager, metadata=metadata)
        state.save(path)
        return state

    def load_workspace(self, workspace_manager, path: str | Path):
        """Load and restore a workspace state from disk."""
        from ..persistence.workspace_persistence import WorkspaceState

        state = WorkspaceState.load(path)
        return self.restore_workspace(workspace_manager, state)

    def find(self, control_id: str, scene_name: Optional[str] = None):
        """Find the first node with *control_id* in the active (or named) scene.

        Shorthand for ``app.scene.find(control_id)``.
        Returns the node, or ``None`` if not found.
        """
        scene = self.scene if scene_name is None else self._scene_runtime(scene_name).scene
        return scene.find(control_id)

    def find_all(self, predicate, scene_name: Optional[str] = None) -> list:
        """Return all nodes in the active (or named) scene that satisfy *predicate*.

        Shorthand for ``app.scene.find_all(predicate)``.
        """
        scene = self.scene if scene_name is None else self._scene_runtime(scene_name).scene
        return scene.find_all(predicate)

    def focus_on(self, control_id: str, scene_name: Optional[str] = None) -> bool:
        """Focus the first focusable node with *control_id* in the active (or named) scene.

        Shorthand for ``app.focus.set_focus_by_id(app.scene, control_id)``.
        Returns ``True`` when a matching focusable node was found and focused.
        """
        scene = self.scene if scene_name is None else self._scene_runtime(scene_name).scene
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
            runtime.window_tiling.prime_registration()

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

    def configure_features_accessibility(self, host, tab_index_start: int) -> int:
        """Call optional configure_accessibility(host, index) on features in order."""
        return self.features.configure_accessibility(host, tab_index_start)
