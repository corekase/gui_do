"""ResponsiveLayout — breakpoint-driven layout manager selection.

Wraps any set of existing layout managers
(:class:`~gui_do.FlexLayout`, :class:`~gui_do.GridLayout`,
:class:`~gui_do.ConstraintLayout`) and hot-swaps the active one based on the
current container width.  When the container is resized (e.g. via
:class:`~gui_do.ResizeManager` or :class:`~gui_do.WindowTilingManager`) call
:meth:`update` with the new width; the active layout switches automatically
and :attr:`active_breakpoint` notifies reactive subscribers.

Usage::

    from gui_do import ResponsiveLayout, Breakpoint, FlexLayout, GridLayout
    from gui_do import FlexDirection

    narrow_layout = FlexLayout(FlexDirection.COLUMN, gap=4)
    wide_layout   = GridLayout(columns=3, gap=8)

    responsive = ResponsiveLayout(default_layout=narrow_layout)
    responsive.add_breakpoint(Breakpoint("medium", min_width=480, layout=wide_layout))
    responsive.add_breakpoint(Breakpoint("narrow", min_width=0,   layout=narrow_layout))

    # Subscribe to breakpoint changes:
    responsive.active_breakpoint.subscribe(lambda name: print("Layout →", name))

    # Per resize event:
    new_width = panel.rect.width
    if responsive.update(new_width):
        do_layout_pass(responsive.active_layout)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Optional

from ..data.presentation_model import ObservableValue


# ---------------------------------------------------------------------------
# Breakpoint
# ---------------------------------------------------------------------------


@dataclass
class Breakpoint:
    """A named layout breakpoint.

    Parameters
    ----------
    name:
        Identifier string (e.g. ``"narrow"``, ``"medium"``, ``"wide"``).
    min_width:
        The :class:`ResponsiveLayout` activates this breakpoint when the
        container width is at least *min_width* pixels.
    layout:
        The layout manager (or any object) to activate at this breakpoint.
    """

    name: str
    min_width: int
    layout: Any


# ---------------------------------------------------------------------------
# ResponsiveLayout
# ---------------------------------------------------------------------------


class ResponsiveLayout:
    """Breakpoint-based layout selector.

    Parameters
    ----------
    default_layout:
        Layout used when no breakpoint's ``min_width`` matches the current
        container width.  Typically a narrow-column or single-column layout.
    """

    def __init__(self, default_layout: Any = None) -> None:
        self._breakpoints: List[Breakpoint] = []
        self._default_layout = default_layout
        self._current_width: int = 0
        self._active_name = ObservableValue("default")
        self._active_layout = default_layout

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    def add_breakpoint(self, breakpoint: Breakpoint) -> None:
        """Register a breakpoint.

        Breakpoints are automatically sorted by ``min_width`` descending so
        the widest matching breakpoint wins.
        """
        if not isinstance(breakpoint, Breakpoint):
            raise TypeError("breakpoint must be a Breakpoint instance")
        self._breakpoints.append(breakpoint)
        self._breakpoints.sort(key=lambda b: b.min_width, reverse=True)

    def set_default_layout(self, layout: Any) -> None:
        """Replace the default (fallback) layout."""
        self._default_layout = layout
        if self._active_name.value == "default":
            self._active_layout = layout

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, container_width: int) -> bool:
        """Evaluate breakpoints for *container_width*.

        Returns ``True`` when the active breakpoint changed (i.e. a layout
        swap occurred).  Subscribers of :attr:`active_breakpoint` are notified
        automatically on change.
        """
        self._current_width = int(container_width)
        new_bp = self._resolve(self._current_width)
        new_name = new_bp.name if new_bp is not None else "default"
        new_layout = new_bp.layout if new_bp is not None else self._default_layout

        if new_name == self._active_name.value:
            return False

        self._active_name.value = new_name
        self._active_layout = new_layout
        return True

    def _resolve(self, width: int) -> Optional[Breakpoint]:
        """Return the widest breakpoint whose min_width ≤ *width*, or None."""
        for bp in self._breakpoints:
            if width >= bp.min_width:
                return bp
        return None

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def active_breakpoint(self) -> ObservableValue:
        """Observable name of the currently active breakpoint (``"default"`` if none matches)."""
        return self._active_name

    @property
    def active_layout(self) -> Any:
        """The layout manager for the currently active breakpoint."""
        return self._active_layout

    @property
    def current_width(self) -> int:
        """Last width passed to :meth:`update`."""
        return self._current_width

    @property
    def breakpoints(self) -> List[Breakpoint]:
        """All registered breakpoints, sorted widest-first."""
        return list(self._breakpoints)
