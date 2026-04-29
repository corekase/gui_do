"""ProgressBarControl — determinate and indeterminate progress indicator.

Displays a horizontal or vertical progress bar.  In *indeterminate* mode a
marquee stripe animates continuously when :meth:`tick` is called each frame.

Binds directly to :class:`~gui_do.ObservableValue` via :meth:`bind_to` for
reactive updates.

Usage::

    from gui_do import ProgressBarControl
    from pygame import Rect

    # Determinate (0–1):
    bar = ProgressBarControl("progress", Rect(10, 10, 300, 20), value=0.0)
    bar.value = 0.65

    # Indeterminate (animated marquee):
    spinner_bar = ProgressBarControl(
        "loading", Rect(10, 40, 300, 20), indeterminate=True
    )
    spinner_bar.tick(dt)  # call each frame to animate

    # Reactive binding:
    obs = ObservableValue(0.0)
    unsub = bar.bind_to(obs)
    obs.value = 0.8   # bar updates automatically
"""
from __future__ import annotations

from typing import Callable, Optional, TYPE_CHECKING

import pygame
from pygame import Rect

from ..base.ui_node import UiNode

if TYPE_CHECKING:
    from ...theme.color_theme import ColorTheme
    from ...data.presentation_model import ObservableValue

_MARQUEE_SPEED = 1.5   # full widths per second
_MARQUEE_WIDTH = 0.35  # fraction of bar width


class ProgressBarControl(UiNode):
    """Horizontal or vertical progress bar.

    Parameters
    ----------
    control_id:
        Unique node identifier.
    rect:
        Bounding rect.
    value:
        Initial progress value in ``[0.0, 1.0]``.  Clamped automatically.
    indeterminate:
        When ``True`` a marquee stripe animates; *value* is ignored visually.
    orientation:
        ``"horizontal"`` (default) or ``"vertical"``.
    """

    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"

    def __init__(
        self,
        control_id: str,
        rect: Rect,
        *,
        value: float = 0.0,
        indeterminate: bool = False,
        orientation: str = HORIZONTAL,
    ) -> None:
        super().__init__(control_id, rect)
        if orientation not in (self.HORIZONTAL, self.VERTICAL):
            raise ValueError(f"orientation must be 'horizontal' or 'vertical', got {orientation!r}")
        self._value = max(0.0, min(1.0, float(value)))
        self._indeterminate = bool(indeterminate)
        self._orientation = orientation
        self._marquee_pos: float = 0.0
        self._binding_unsub: Optional[Callable[[], None]] = None

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def value(self) -> float:
        """Current progress in ``[0.0, 1.0]``."""
        return self._value

    @value.setter
    def value(self, v: float) -> None:
        clamped = max(0.0, min(1.0, float(v)))
        if self._value == clamped:
            return
        self._value = clamped
        self.invalidate()

    @property
    def indeterminate(self) -> bool:
        return self._indeterminate

    @indeterminate.setter
    def indeterminate(self, v: bool) -> None:
        self._indeterminate = bool(v)
        self._marquee_pos = 0.0
        self.invalidate()

    @property
    def orientation(self) -> str:
        return self._orientation

    def accepts_mouse_focus(self) -> bool:
        return False

    # ------------------------------------------------------------------
    # Binding
    # ------------------------------------------------------------------

    def bind_to(self, observable: "ObservableValue[float]") -> Callable[[], None]:
        """Bind this bar's value to *observable*.

        Returns an unsubscribe callable.  Previous binding (if any) is
        replaced.
        """
        if self._binding_unsub is not None:
            self._binding_unsub()
        def _on_change(v: float) -> None:
            self.value = v
        unsub = observable.subscribe(_on_change)
        self._binding_unsub = unsub
        self.value = observable.value
        return unsub

    # ------------------------------------------------------------------
    # Animation
    # ------------------------------------------------------------------

    def tick(self, dt: float) -> None:
        """Advance the marquee animation by *dt* seconds.

        Only relevant in *indeterminate* mode.  Call each frame.
        """
        if not self._indeterminate:
            return
        self._marquee_pos = (self._marquee_pos + _MARQUEE_SPEED * dt) % 1.0
        self.invalidate()

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------

    def draw(self, surface: pygame.Surface, theme: "ColorTheme") -> None:
        if not self.visible:
            return

        r = self.rect
        bg_color = theme.surface_bg
        fill_color = theme.accent
        border_color = theme.border

        # Background
        pygame.draw.rect(surface, bg_color, r)

        if self._indeterminate:
            self._draw_marquee(surface, r, fill_color)
        else:
            self._draw_fill(surface, r, fill_color)

        # Border
        pygame.draw.rect(surface, border_color, r, 1)

    def _draw_fill(
        self,
        surface: pygame.Surface,
        r: Rect,
        color: tuple,
    ) -> None:
        if self._orientation == self.HORIZONTAL:
            fill_w = max(0, int(r.width * self._value))
            if fill_w > 0:
                pygame.draw.rect(surface, color, Rect(r.x, r.y, fill_w, r.height))
        else:
            fill_h = max(0, int(r.height * self._value))
            if fill_h > 0:
                pygame.draw.rect(surface, color, Rect(r.x, r.bottom - fill_h, r.width, fill_h))

    def _draw_marquee(
        self,
        surface: pygame.Surface,
        r: Rect,
        color: tuple,
    ) -> None:
        if self._orientation == self.HORIZONTAL:
            span = r.width
            mw = max(4, int(span * _MARQUEE_WIDTH))
            x = int(r.x + (span + mw) * self._marquee_pos - mw)
            # Draw the marquee stripe (clipped to bar bounds)
            left = max(r.x, x)
            right = min(r.right, x + mw)
            if right > left:
                pygame.draw.rect(surface, color, Rect(left, r.y, right - left, r.height))
        else:
            span = r.height
            mh = max(4, int(span * _MARQUEE_WIDTH))
            y = int(r.y + (span + mh) * self._marquee_pos - mh)
            top = max(r.y, y)
            bottom = min(r.bottom, y + mh)
            if bottom > top:
                pygame.draw.rect(surface, color, Rect(r.x, top, r.width, bottom - top))
