from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable, Optional

if TYPE_CHECKING:
    import pygame

    from ..app.scene import Scene
    from ..graphics.built_in_graphics_factory import BuiltInGraphicsFactory
    from ..layout.window_layout_handler import WindowLayoutHandler
    from ..overlays.drag_drop_manager import DragDropManager
    from ..overlays.overlay_manager import OverlayManager
    from ..scheduling.task_scheduler import TaskScheduler
    from ..scheduling.timers import Timers
    from ..scheduling.tween_manager import TweenManager
    from ..theme.color_theme import ColorTheme


@dataclass
class _SceneRuntime:
    scene: "Scene"
    scheduler: "TaskScheduler"
    timers: "Timers"
    theme: "ColorTheme"
    graphics_factory: "BuiltInGraphicsFactory"
    window_tiling: "WindowLayoutHandler"
    tweens: "TweenManager"
    overlay: "OverlayManager"
    drag_drop: "DragDropManager"
    screen_pristine: "Optional[pygame.Surface]"
    screen_pristine_scaled: "Optional[pygame.Surface]"
    screen_pristine_scaled_size: tuple
    scene_auto_suspended: set


@dataclass
class _ScreenLifecycleEntry:
    preamble: "Optional[Callable[[], None]]" = None
    event_handler: "Optional[Callable[[object], bool]]" = None
    postamble: "Optional[Callable[[], None]]" = None
    scene_name: "Optional[str]" = None
    entry_id: int = 0


@dataclass
class _FallthroughEntry:
    """Handler invoked only when the full event pipeline returns unconsumed."""

    event_handler: "Callable[[object], bool]"
    scene_name: "Optional[str]" = None
    entry_id: int = 0
