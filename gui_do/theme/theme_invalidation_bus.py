"""ThemeInvalidationBus — automatic visual cache flush on theme switch.

Connects :class:`~gui_do.ThemeManager` to the rendering pipeline so that
switching themes invalidates every registered control's bitmap cache in one
coordinated pass instead of requiring per-control :class:`~gui_do.ThemeManager`
subscriptions.

The bus sits between ``ThemeManager.active_tokens`` and the renderer:

1. Controls register their ``invalidate`` callable at mount time.
2. ``ThemeInvalidationBus`` subscribes once to ``ThemeManager.active_tokens``.
3. On theme change:
   a. The graphics factory cache is flushed (re-renders styled bitmaps).
   b. The font manager cache is flushed (re-renders glyphs at theme sizes).
   c. All registered ``invalidate`` callables are fired.
   d. ``DirtyRegionTracker.mark_all_dirty()`` is called so the next frame
      repaints everything.

Usage::

    from gui_do import ThemeInvalidationBus

    # Created once per application (wired by bootstrap_host_application):
    bus = ThemeInvalidationBus(
        theme_manager=app.theme,
        dirty_tracker=app.dirty_tracker,
        graphics_factory=app.graphics_factory,
        font_manager=app.theme.fonts,
    )

    # In scene mount — for every control that caches styled surfaces:
    bus.register(button, button.invalidate)

    # In scene unmount:
    bus.unregister(button)

    # Switch theme — all registered controls invalidate automatically:
    app.theme.switch("light")
"""
from __future__ import annotations

from typing import Callable, Dict, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from ..theme.theme_manager import ThemeManager, DesignTokens
    from ..graphics.dirty_region import DirtyRegionTracker


# ---------------------------------------------------------------------------
# ThemeInvalidationBus
# ---------------------------------------------------------------------------


class ThemeInvalidationBus:
    """Coordinates theme-switch cache invalidation for all registered controls.

    Parameters
    ----------
    theme_manager:
        The application :class:`~gui_do.ThemeManager`.  The bus subscribes to
        ``theme_manager.active_tokens`` automatically on construction.
    dirty_tracker:
        Optional :class:`~gui_do.DirtyRegionTracker`.  When provided,
        :meth:`~DirtyRegionTracker.mark_all_dirty` is called after flushing
        caches so the renderer knows to repaint the full screen.
    graphics_factory:
        Optional graphics factory object.  If it exposes a ``flush_cache()``
        method, that method is called on theme change.
    font_manager:
        Optional font manager.  If it exposes a ``flush_cache()`` method,
        that method is called on theme change.
    screen_rect:
        The full-screen rect passed to
        :meth:`~gui_do.DirtyRegionTracker.mark_all_dirty`.  If ``None``,
        ``mark_all_dirty`` is not called even when a dirty tracker is set.
    """

    def __init__(
        self,
        *,
        theme_manager: object,
        dirty_tracker: Optional["DirtyRegionTracker"] = None,
        graphics_factory: Optional[object] = None,
        font_manager: Optional[object] = None,
        screen_rect: Optional[object] = None,
    ) -> None:
        self._theme_manager = theme_manager
        self._dirty_tracker = dirty_tracker
        self._graphics_factory = graphics_factory
        self._font_manager = font_manager
        self._screen_rect = screen_rect

        # widget id -> (widget, invalidate_fn)
        self._registrations: Dict[int, Tuple[object, Callable[[], None]]] = {}

        self._active_tokens = getattr(theme_manager, "active_tokens", None)
        self._unsubscribe: Callable[[], None] = lambda: None

        # Subscribe to theme changes when a ThemeManager-like source is provided.
        if self._active_tokens is not None:
            subscribe = getattr(self._active_tokens, "subscribe", None)
            if callable(subscribe):
                try:
                    self._unsubscribe = subscribe(self._on_theme_changed)
                except Exception:
                    self._unsubscribe = lambda: None

    # ------------------------------------------------------------------
    # Control registration
    # ------------------------------------------------------------------

    def register(self, widget: object, invalidate_fn: Callable[[], None]) -> None:
        """Register *widget* so its *invalidate_fn* is called on theme change.

        Idempotent: re-registering the same widget replaces the invalidate_fn.
        """
        self._registrations[id(widget)] = (widget, invalidate_fn)

    def unregister(self, widget: object) -> None:
        """Remove *widget*'s registration.  No-op if not registered."""
        self._registrations.pop(id(widget), None)

    def clear(self) -> None:
        """Remove all registered controls."""
        self._registrations.clear()

    @property
    def registered_count(self) -> int:
        return len(self._registrations)

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    def set_screen_rect(self, rect: object) -> None:
        """Update the screen rect used for full-screen dirty marking."""
        self._screen_rect = rect

    # ------------------------------------------------------------------
    # Theme change handler
    # ------------------------------------------------------------------

    def _on_theme_changed(self, tokens: object = None) -> None:
        """Flush caches and invalidate all registered controls."""
        # 1. Flush graphics factory bitmap cache
        if self._graphics_factory is not None:
            flush = getattr(self._graphics_factory, "flush_cache", None)
            if flush is not None:
                try:
                    flush()
                except Exception:
                    pass

        # 2. Flush font manager glyph cache
        if self._font_manager is not None:
            flush = getattr(self._font_manager, "flush_cache", None)
            if flush is not None:
                try:
                    flush()
                except Exception:
                    pass

        # 3. Invalidate all registered controls
        for _widget, fn in list(self._registrations.values()):
            try:
                fn()
            except Exception:
                pass

        # 4. Mark full screen dirty
        if self._dirty_tracker is not None and self._screen_rect is not None:
            try:
                self._dirty_tracker.mark_all_dirty(self._screen_rect)
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def dispose(self) -> None:
        """Unsubscribe from the theme manager and clear all registrations."""
        try:
            self._unsubscribe()
        except Exception:
            pass
        self._registrations.clear()

    def trigger_invalidation(self) -> None:
        """Manually trigger invalidation of all registered controls.

        Useful for forcing a redraw when non-theme visual properties change
        globally (e.g. font size scaling, accessibility high-contrast mode).
        """
        if self._active_tokens is not None and hasattr(self._active_tokens, "value"):
            self._on_theme_changed(self._active_tokens.value)
            return
        self._on_theme_changed(None)
