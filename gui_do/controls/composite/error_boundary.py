"""ErrorBoundary — subtree exception containment for resilient rendering.

An :class:`ErrorBoundary` wraps a single *child* :class:`~gui_do.UiNode` and
silently catches exceptions thrown during ``draw`` or ``handle_event``.  When
an error is caught the child is replaced by an error-placeholder visual so
the rest of the scene continues rendering normally.

This is modelled loosely on React error boundaries — the purpose is to prevent
one misbehaving control from crashing the entire application frame loop.

Usage::

    from gui_do import ErrorBoundary

    boundary = ErrorBoundary(
        child=my_control,
        on_error=lambda exc: logger.error("Control error", exc_info=exc),
        error_text="Control unavailable",
    )
    scene.add(boundary)

Recovering from an error::

    if boundary.has_error:
        boundary.recover()     # clears the error state and re-enables the child

"""
from __future__ import annotations

from typing import TYPE_CHECKING

from pygame import Rect

from ..base.ui_node import UiNode
from ...app.error_handling import report_nonfatal_error

if TYPE_CHECKING:
    import pygame
    from ...theme.color_theme import ColorTheme
    from ...events.gui_event import GuiEvent


# ---------------------------------------------------------------------------
# ErrorBoundary
# ---------------------------------------------------------------------------


class ErrorBoundary(UiNode):
    """A transparent wrapper around a child :class:`UiNode` that isolates errors.

    Parameters
    ----------
    child:
        The :class:`~gui_do.UiNode` to protect.  Must not be ``None``.
    on_error:
        Optional callback invoked with the caught exception whenever an error
        is first encountered.  Called once per unique error event (not every
        frame).
    error_text:
        Short description shown in the error placeholder visual.  Defaults to
        ``"Error"``.
    recover_on_scene_change:
        If True (default) the boundary automatically clears its error state
        when ``on_mount`` is called (i.e. when a new scene mounts the node).
    """

    _FALLBACK_BG = (60, 0, 0)       # dark red background
    _FALLBACK_FG = (255, 80, 80)    # pinkish text
    _FALLBACK_BORDER = (200, 40, 40)
    _FALLBACK_FONT_ROLE = "error_boundary.placeholder"
    _FONT_SCALE: float = 0.75   # 12/16 — small diagnostic text in error placeholder

    def __init__(
        self,
        child: UiNode,
        *,
        on_error: Optional[Callable[[BaseException], None]] = None,
        error_text: str = "Error",
        recover_on_scene_change: bool = True,
    ) -> None:
        if child is None:
            raise ValueError("ErrorBoundary child must not be None")
        super().__init__(f"_error_boundary_{id(child)}", Rect(child.rect))
        self._child: UiNode = child
        self._on_error: Optional[Callable[[BaseException], None]] = on_error
        self._error_text: str = str(error_text)
        self._recover_on_mount: bool = bool(recover_on_scene_change)
        self._error: Optional[BaseException] = None
        self._draw_font_role: str = self._FALLBACK_FONT_ROLE

        # Adopt the child
        self.children.append(child)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def has_error(self) -> bool:
        """Return True if the boundary is currently showing an error placeholder."""
        return self._error is not None

    @property
    def error(self) -> Optional[BaseException]:
        """The most recent caught exception, or ``None``."""
        return self._error

    def recover(self) -> None:
        """Clear the error state so the child renders normally again."""
        self._error = None
        self.invalidate()

    # ------------------------------------------------------------------
    # UiNode lifecycle
    # ------------------------------------------------------------------

    def on_mount(self, parent: "UiNode | None") -> None:
        if self._recover_on_mount:
            self._error = None
        self._child.on_mount(self)

    def on_unmount(self, parent: "UiNode | None") -> None:
        self._child.on_unmount(self)

    def update(self, dt_seconds: float) -> None:
        if self._error is not None:
            return
        try:
            self._child.update(dt_seconds)
        except Exception as exc:
            self._handle_error(exc, operation="update")

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def draw(self, surface: "pygame.Surface", theme: "ColorTheme") -> None:
        # Keep our rect in sync with the child
        self.rect = Rect(self._child.rect)

        if self._error is not None:
            self._draw_placeholder(surface)
            return

        try:
            self._child.draw(surface, theme)
        except Exception as exc:
            self._handle_error(exc, operation="draw")
            self._draw_placeholder(surface)

    def draw_screen_phase(self, surface: "pygame.Surface", theme: "ColorTheme", app=None) -> None:
        self.rect = Rect(self._child.rect)
        if self._error is not None:
            self._draw_placeholder(surface)
            return
        try:
            self._child.draw_screen_phase(surface, theme, app=app)
        except Exception as exc:
            self._handle_error(exc, operation="draw_screen_phase")
            self._draw_placeholder(surface)

    def draw_window_phase(self, surface: "pygame.Surface", theme: "ColorTheme", app=None) -> None:
        if self._error is not None:
            return
        try:
            self._child.draw_window_phase(surface, theme, app)
        except Exception as exc:
            self._handle_error(exc, operation="draw_window_phase")

    # ------------------------------------------------------------------
    # Event handling
    # ------------------------------------------------------------------

    def handle_event(self, event: "GuiEvent", app, theme=None) -> bool:
        if self._error is not None:
            return False
        try:
            return bool(self._child.handle_event(event, app, theme=theme))
        except Exception as exc:
            self._handle_error(exc, operation="handle_event")
            return False

    def on_event_capture(self, event: "GuiEvent", app, theme=None) -> bool:
        if self._error is not None:
            return False
        try:
            return bool(self._child.on_event_capture(event, app, theme=theme))
        except Exception as exc:
            self._handle_error(exc, operation="on_event_capture")
            return False

    def on_event_bubble(self, event: "GuiEvent", app, theme=None) -> bool:
        if self._error is not None:
            return False
        try:
            return bool(self._child.on_event_bubble(event, app, theme=theme))
        except Exception as exc:
            self._handle_error(exc, operation="on_event_bubble")
            return False

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _handle_error(self, exc: BaseException, *, operation: str) -> None:
        """Record the first error and notify."""
        if self._error is not None:
            return  # already in error state; don't repeat
        self._error = exc
        report_nonfatal_error(
            reason=str(exc),
            kind="runtime_error",
            subsystem="error_boundary",
            operation=operation,
            cause=exc,
        )
        if self._on_error is not None:
            try:
                self._on_error(exc)
            except Exception:
                pass
        self.invalidate()

    def _draw_placeholder(self, surface: "pygame.Surface", theme=None) -> None:
        """Render an error placeholder in the child's rect area using a standard font role."""
        import pygame  # deferred import — keep top-level importable without display init

        r = Rect(self._child.rect)
        if r.width <= 0 or r.height <= 0:
            return

        pygame.draw.rect(surface, self._FALLBACK_BG, r)
        pygame.draw.rect(surface, self._FALLBACK_BORDER, r, 2)

        # Use theme-based font role resolution only (centralized)
        if not (theme and hasattr(theme, "fonts")):
            raise RuntimeError("ErrorBoundary requires theme with centralized font roles.")
        font = theme.fonts.font_instance(self._draw_font_role, size=theme.fonts.scaled_size(self._FONT_SCALE))
        render_text = lambda text, color: font._font.render(text, True, color) if hasattr(font, "_font") else font.render(text, True, color)

        lines = [self._error_text]
        if self._error is not None:
            lines.append(type(self._error).__name__)

        y = r.y + 6
        for line in lines:
            if y + 14 > r.bottom:
                break
            text_surf = render_text(line[:60], self._FALLBACK_FG)
            surface.blit(text_surf, (r.x + 6, y))
            y += 16
