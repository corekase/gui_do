"""WindowFocusManager — Ctrl+Tab window cycling with focus hint display.

Tracks which scene window currently holds "window focus" (distinct from the
per-control keyboard focus tracked by :class:`~gui_do.FocusManager`) and
drives the visual hint drawn around that window.

Usage
-----
*  ``app.window_focus.cycle(scene, forward=True)``  — invoked by
   :class:`~gui_do.KeyboardManager` on Ctrl+Tab / Ctrl+Shift+Tab.
*  ``app.window_focus.update(dt_seconds)``  — advance the hint timer each
   frame; called from :meth:`GuiApplication.update`.
*  ``app.window_focus.revalidate(scene)``   — if the focused window has
   become hidden or disabled, advance focus to the next available window or
   clear it; called from :meth:`GuiApplication.update`.
*  ``app.window_focus.should_draw_window_focus_hint()`` — queried by
   :class:`~gui_do.FocusVisualizer` before drawing the hint.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from .focus_hint_constants import FOCUS_TRAVERSAL_HINT_TIMEOUT_SECONDS

if TYPE_CHECKING:
    from ..app.scene import Scene
    from ..app.gui_application import GuiApplication


class WindowFocusManager:
    """Manages Ctrl+Tab window-cycling focus and its visual hint.

    The *window focus* is independent of the per-control focus tracked by
    :class:`~gui_do.FocusManager`.  It selects which scene window the user
    intends to interact with next, surfaced via a dashed-rectangle hint
    drawn around the focused window using the same timeout as the control
    focus hint.

    Cycle list
    ----------
    The candidate list is derived on demand from the scene graph: every
    node for which ``is_window()`` returns ``True`` and that is both
    visible and enabled is included.  The list is sorted by
    ``(control_id,)`` for a stable, deterministic order.

    Visibility changes
    ------------------
    ``revalidate(scene)`` (called once per frame from
    :meth:`GuiApplication.update`) advances focus to the next candidate
    whenever the focused window has become invisible or disabled, and clears
    focus when no candidates remain.
    """

    def __init__(self) -> None:
        self._focused_window = None
        self._hint_visible: bool = False
        self._hint_elapsed_seconds: float = 0.0

    # ------------------------------------------------------------------
    # Public read API
    # ------------------------------------------------------------------

    @property
    def focused_window(self):
        """The currently window-focused window node, or ``None``."""
        return self._focused_window

    def should_draw_window_focus_hint(self) -> bool:
        """Return True when the window focus hint should be rendered."""
        return bool(self._hint_visible and self._focused_window is not None)

    # ------------------------------------------------------------------
    # Cycling
    # ------------------------------------------------------------------

    def cycle(
        self,
        scene: "Scene",
        *,
        forward: bool = True,
        app: "Optional[GuiApplication]" = None,
        cached_walk_nodes=None,
    ) -> bool:
        """Cycle window focus forward or backward through visible scene windows.

        Returns ``True`` when the event was handled (even if the candidate
        list has only one entry — the hint is still shown), ``False`` when
        there are no windows to cycle through.

        First invocation with an existing focused window but no visible hint
        just reveals the hint; subsequent invocations within the timeout
        window advance focus to the next/previous window.
        """
        candidates = self._candidate_windows(scene, cached_walk_nodes=cached_walk_nodes)
        if not candidates:
            self._focused_window = None
            self._hint_visible = False
            return False

        focused = self._focused_window

        # No current focus or focus is stale — jump to first candidate.
        if focused is None or focused not in candidates:
            self._focused_window = candidates[0]
            self._hint_visible = True
            self._hint_elapsed_seconds = 0.0
            self._activate_window(scene, app)
            return True

        # First Ctrl+Tab with existing focus but no visible hint: show hint.
        if not self._hint_visible:
            self._hint_visible = True
            self._hint_elapsed_seconds = 0.0
            self._activate_window(scene, app)
            return True

        # Advance focus.
        current_index = next(
            (i for i, w in enumerate(candidates) if w is focused), 0
        )
        offset = 1 if forward else -1
        next_index = (current_index + offset) % len(candidates)
        self._focused_window = candidates[next_index]
        self._hint_visible = True
        self._hint_elapsed_seconds = 0.0
        self._activate_window(scene, app)
        return True

    # ------------------------------------------------------------------
    # Per-frame lifecycle
    # ------------------------------------------------------------------

    def update(self, dt_seconds: float) -> None:
        """Advance the hint timer by *dt_seconds*."""
        if dt_seconds <= 0.0:
            return
        if self._hint_visible:
            self._hint_elapsed_seconds += float(dt_seconds)
            if self._hint_elapsed_seconds >= FOCUS_TRAVERSAL_HINT_TIMEOUT_SECONDS:
                self._hint_visible = False

    def revalidate(self, scene: "Scene", cached_walk_nodes=None) -> None:
        """If the focused window is no longer valid advance to next or clear.

        Called once per frame so that closing or hiding a window
        automatically moves window focus to the next available window.

        Args:
            scene: Scene to search
            cached_walk_nodes: Optional pre-computed BFS walk list from scene._get_cached_bfs_walk()
        """
        if self._focused_window is None:
            return
        if self._focused_window.visible and self._focused_window.enabled:
            return

        candidates = self._candidate_windows(scene, cached_walk_nodes=cached_walk_nodes)
        if candidates:
            self._focused_window = candidates[0]
            # Preserve current hint visibility so the user sees the transition.
        else:
            self._focused_window = None
            self._hint_visible = False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _candidate_windows(self, scene: "Scene", cached_walk_nodes=None) -> List:
        """Return sorted Ctrl+Tab targets: windows plus screen-level menubars.

        Args:
            scene: Scene to search
            cached_walk_nodes: Optional pre-computed BFS walk list from scene._get_cached_bfs_walk()
        """
        walk_source = cached_walk_nodes if cached_walk_nodes is not None else scene._walk_nodes()
        targets = [
            node
            for node in walk_source
            if self._is_window_cycle_target(node)
        ]
        targets.sort(key=lambda node: str(getattr(node, "control_id", "")))
        return targets

    @staticmethod
    def _is_window_cycle_target(node) -> bool:
        if not (node.visible and node.enabled):
            return False
        if node.is_window():
            return True
        # Include scene-level menu strips (not hosted inside a window) so
        # Ctrl+Tab can move to them when they are part of screen chrome.
        if getattr(node, "accessibility_role", "") != "menubar":
            return False
        current = getattr(node, "parent", None)
        while current is not None:
            if current.is_window():
                return False
            current = getattr(current, "parent", None)
        return True

    def _activate_window(self, scene: "Scene", app: "Optional[GuiApplication]") -> None:
        window = self._focused_window
        if window is None or app is None:
            return

        if not window.is_window():
            focus = getattr(app, "focus", None)
            if focus is not None:
                focus.set_focus(window, via_keyboard=True)
            return

        parent = getattr(window, "parent", None)
        raise_window = getattr(app, "raise_window", None)
        if callable(raise_window):
            raise_window(window)
        else:
            raise_window = getattr(parent, "_raise_window", None)
            if callable(raise_window):
                raise_window(window)

        focus = getattr(app, "focus", None)
        if focus is not None:
            focus.restore_remembered_focus_for_window(scene, window)
