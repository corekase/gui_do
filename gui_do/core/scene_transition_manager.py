"""SceneTransitionManager — animated transitions between scenes via Router."""
from __future__ import annotations

from enum import Enum
from typing import Callable, Dict, Optional, Tuple, TYPE_CHECKING

import pygame

from .tween_manager import Easing

if TYPE_CHECKING:
    from ..app.gui_application import GuiApplication


class SceneTransitionStyle(Enum):
    """Visual style for a :class:`SceneTransitionManager` animated transition.

    Members:
        NONE: Instant switch — no animation.
        FADE: Cross-dissolve; old scene fades out while new scene fades in.
        SLIDE_LEFT: Incoming scene slides in from the right edge.
        SLIDE_RIGHT: Incoming scene slides in from the left edge.
        SLIDE_UP: Incoming scene slides in from the bottom edge.
        SLIDE_DOWN: Incoming scene slides in from the top edge.
    """

    NONE = "none"
    FADE = "fade"
    SLIDE_LEFT = "slide_left"
    SLIDE_RIGHT = "slide_right"
    SLIDE_UP = "slide_up"
    SLIDE_DOWN = "slide_down"


class SceneTransitionManager:
    """Animated wrapper around :meth:`~GuiApplication.switch_scene`.

    Register a default transition style and optional per-route overrides, then
    call :meth:`go` instead of ``app.switch_scene(...)`` to get an animated
    cross-scene transition driven by the active scene's :class:`~TweenManager`.

    The transition works in three steps:

    1. Snapshot the current scene surface.
    2. Switch the scene immediately (so the new scene begins updating).
    3. Use a tween to animate an overlay: the snapshot slides/fades out while
       the live rendering of the new scene becomes progressively visible.

    Usage::

        transitions = SceneTransitionManager(app)
        transitions.set_default(SceneTransitionStyle.FADE, duration=0.35)
        transitions.set_style("editor", SceneTransitionStyle.SLIDE_LEFT)

        # Instead of app.switch_scene("editor"):
        transitions.go("editor")
    """

    def __init__(
        self,
        app: "GuiApplication",
        *,
        default_style: SceneTransitionStyle = SceneTransitionStyle.FADE,
        default_duration: float = 0.30,
        easing: Easing = Easing.EASE_IN_OUT,
    ) -> None:
        self._app = app
        self._default_style: SceneTransitionStyle = default_style
        self._default_duration: float = float(default_duration)
        self._easing: Easing = easing
        # Per-scene overrides: scene_name -> (style, duration)
        self._overrides: Dict[str, Tuple[SceneTransitionStyle, float]] = {}
        # Active animation state
        self._snapshot: Optional[pygame.Surface] = None
        self._active: bool = False
        self._style: SceneTransitionStyle = SceneTransitionStyle.NONE

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    def set_default(
        self,
        style: SceneTransitionStyle,
        *,
        duration: Optional[float] = None,
    ) -> None:
        """Set the default transition style and optional duration."""
        self._default_style = style
        if duration is not None:
            self._default_duration = max(0.0, float(duration))

    def set_style(
        self,
        scene_name: str,
        style: SceneTransitionStyle,
        *,
        duration: Optional[float] = None,
    ) -> None:
        """Set a per-scene transition override for the named scene."""
        dur = self._default_duration if duration is None else max(0.0, float(duration))
        self._overrides[str(scene_name)] = (style, dur)

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def go(
        self,
        scene_name: str,
        *,
        style: Optional[SceneTransitionStyle] = None,
        duration: Optional[float] = None,
        on_complete: Optional[Callable[[], None]] = None,
    ) -> None:
        """Switch to *scene_name* with an animated transition.

        If *style* is ``None``, the per-scene override (registered via
        :meth:`set_style`) is used, falling back to the default style.
        """
        if self._active:
            # If a transition is already running, cancel it and cut immediately
            self._snapshot = None
            self._active = False

        effective_style = style
        effective_dur = duration

        if effective_style is None:
            override = self._overrides.get(scene_name)
            if override is not None:
                effective_style, ov_dur = override
                if effective_dur is None:
                    effective_dur = ov_dur
            else:
                effective_style = self._default_style
        if effective_dur is None:
            effective_dur = self._default_duration

        if effective_style is SceneTransitionStyle.NONE or effective_dur <= 0.0:
            self._app.switch_scene(scene_name)
            if on_complete:
                try:
                    on_complete()
                except Exception:
                    pass
            return

        # Snapshot the current rendered surface before switching
        try:
            snap = self._app.surface.copy()
            # Trim to actual display if subsurface is used
        except Exception:
            snap = None

        # Switch the scene now (new scene starts receiving updates)
        self._app.switch_scene(scene_name)

        if snap is None:
            # Could not snapshot — just switch without animation
            if on_complete:
                try:
                    on_complete()
                except Exception:
                    pass
            return

        # Give the snapshot an alpha channel for FADE support
        if effective_style is SceneTransitionStyle.FADE:
            try:
                snap = snap.convert_alpha()
            except Exception:
                pass  # fall back to non-alpha surface in headless/test contexts
        self._snapshot = snap
        self._style = effective_style
        self._active = True

        app = self._app
        snapshot_ref = [self._snapshot]

        def _animate(t: float) -> None:
            if not snapshot_ref[0]:
                return
            snap_surf = snapshot_ref[0]
            screen = app.surface
            sr = screen.get_rect()
            w, h = sr.width, sr.height

            if effective_style is SceneTransitionStyle.FADE:
                alpha = int(255 * (1.0 - t))
                snap_surf.set_alpha(alpha)
                screen.blit(snap_surf, (0, 0))

            elif effective_style is SceneTransitionStyle.SLIDE_LEFT:
                # Snapshot slides out to the left; new scene comes from right
                offset_x = int(-w * t)
                screen.blit(snap_surf, (offset_x, 0))

            elif effective_style is SceneTransitionStyle.SLIDE_RIGHT:
                offset_x = int(w * t)
                screen.blit(snap_surf, (offset_x, 0))

            elif effective_style is SceneTransitionStyle.SLIDE_UP:
                offset_y = int(-h * t)
                screen.blit(snap_surf, (0, offset_y))

            elif effective_style is SceneTransitionStyle.SLIDE_DOWN:
                offset_y = int(h * t)
                screen.blit(snap_surf, (0, offset_y))

        def _done() -> None:
            self._snapshot = None
            snapshot_ref[0] = None
            self._active = False
            if on_complete:
                try:
                    on_complete()
                except Exception:
                    pass

        # Drive with the active scene's TweenManager so it updates each frame
        app.tweens.tween_fn(
            effective_dur,
            _animate,
            easing=self._easing,
            on_complete=_done,
        )

    # ------------------------------------------------------------------
    # Frame hook
    # ------------------------------------------------------------------

    @property
    def is_animating(self) -> bool:
        """True while a transition animation is in progress."""
        return self._active
