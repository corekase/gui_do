"""LayoutPass — formal measure/arrange two-pass layout protocol.

The *measure/arrange* pattern separates two concerns:

1. **Measure** — ask each node "how much space do you need?" given an
   available size.  Nodes return a *preferred size* that respects their
   content and constraints.
2. **Arrange** — tell each node its final rect and let it position children.

This two-pass approach allows parents to know children's natural sizes before
choosing their own size, enabling content-wrapping containers, correctly
centred dialogs of unknown height, auto-sized tooltips, and smooth
:class:`~gui_do.LayoutAnimator` transitions that need stable before/after rects.

Protocol
--------
Any class that implements :meth:`~LayoutPass.measure` and
:meth:`~LayoutPass.arrange` satisfies the :class:`LayoutPass` protocol.
Existing layout engines (:class:`~gui_do.FlexLayout`, :class:`~gui_do.GridLayout`,
:class:`~gui_do.ConstraintLayout`) can participate by implementing the protocol
methods as thin wrappers over their existing ``apply`` method.

Usage — standalone::

    from gui_do import LayoutRoot, LayoutPass

    class MyLayout:
        def measure(self, available: tuple[int, int]) -> tuple[int, int]:
            # Compute preferred size from children's natural sizes.
            return (available[0], 200)

        def arrange(self, rect: pygame.Rect) -> None:
            # Set children's rects using the final rect.
            for i, child in enumerate(self._children):
                child.rect = pygame.Rect(rect.x, rect.y + i * 40, rect.w, 40)

    root = LayoutRoot(layout=MyLayout(), invalidation=app.invalidation)
    root.mark_dirty()      # called whenever content changes
    root.update(container_rect)   # runs measure + arrange only when dirty

Usage — with dirty tracking::

    # Whenever a child is added, removed, or resized:
    layout_root.mark_dirty()

    # In the scene update:
    layout_root.update(panel.rect)
"""
from __future__ import annotations

from typing import Optional, Protocol, runtime_checkable, TYPE_CHECKING

from pygame import Rect

from .rect_source import RectSource, resolve_rect

if TYPE_CHECKING:
    from ..data.invalidation import InvalidationTracker


# ---------------------------------------------------------------------------
# MeasureContext / ArrangeContext
# ---------------------------------------------------------------------------


class MeasureContext:
    """Carries constraints for a measure pass.

    Attributes
    ----------
    available_width / available_height:
        Maximum available dimensions in pixels.  A value of ``-1`` means
        unconstrained (node may claim as much space as it needs).
    """

    __slots__ = ("available_width", "available_height")

    def __init__(self, available_width: int, available_height: int) -> None:
        self.available_width: int = int(available_width)
        self.available_height: int = int(available_height)

    @property
    def available_size(self) -> Tuple[int, int]:
        """``(width, height)`` tuple of the available space."""
        return (self.available_width, self.available_height)

    def __repr__(self) -> str:  # pragma: no cover
        return f"MeasureContext({self.available_width}x{self.available_height})"


class ArrangeContext:
    """Carries the final rect for an arrange pass.

    Attributes
    ----------
    rect:
        The final :class:`pygame.Rect` assigned to the layout.
    """

    __slots__ = ("rect",)

    def __init__(self, rect: Rect) -> None:
        self.rect: Rect = Rect(rect)

    def __repr__(self) -> str:  # pragma: no cover
        return f"ArrangeContext({self.rect})"


# ---------------------------------------------------------------------------
# LayoutPass protocol
# ---------------------------------------------------------------------------


@runtime_checkable
class LayoutPass(Protocol):
    """Protocol for two-pass layout engines.

    Both methods must be implemented.  ``measure`` is called first; the
    returned preferred size is used by the parent to finalize its own rect
    before calling ``arrange``.
    """

    def measure(self, context: MeasureContext) -> Tuple[int, int]:
        """Return the preferred ``(width, height)`` given *context*.

        Parameters
        ----------
        context:
            Carry-along struct with available dimensions.  Read
            ``context.available_width`` / ``context.available_height`` to
            respect parent constraints.

        Returns
        -------
        tuple[int, int]
            Preferred ``(width, height)`` in pixels.  May exceed the available
            dimensions when the content cannot shrink further.
        """
        ...

    def arrange(self, context: ArrangeContext) -> None:
        """Position children within the final *context.rect*.

        This is called after all preferred sizes are known and the parent
        has decided each child's final rect.
        """
        ...


# ---------------------------------------------------------------------------
# LayoutRoot
# ---------------------------------------------------------------------------


class LayoutRoot:
    """Drives the two-pass measure/arrange cycle for one layout engine.

    :class:`LayoutRoot` integrates with :class:`~gui_do.InvalidationTracker`
    to skip recomputation when nothing has changed.  Call :meth:`mark_dirty`
    whenever content changes; the next :meth:`update` call will run the full
    measure+arrange cycle.

    Parameters
    ----------
    layout:
        Any object that satisfies :class:`LayoutPass`.
    invalidation:
        Optional :class:`~gui_do.InvalidationTracker`.  When provided,
        :meth:`mark_dirty` also calls ``invalidation.invalidate_all()``.
    """

    def __init__(
        self,
        layout: LayoutPass,
        *,
        invalidation: Optional["InvalidationTracker"] = None,
    ) -> None:
        self._layout = layout
        self._invalidation = invalidation
        self._dirty: bool = True
        self._last_rect: Optional[Rect] = None
        self._last_preferred: Tuple[int, int] = (0, 0)

    @property
    def is_dirty(self) -> bool:
        """True when a layout pass is needed on the next :meth:`update`."""
        return self._dirty

    @property
    def preferred_size(self) -> Tuple[int, int]:
        """Preferred size from the most recent measure pass."""
        return self._last_preferred

    def mark_dirty(self) -> None:
        """Signal that content has changed and a new pass is required."""
        self._dirty = True
        if self._invalidation is not None:
            self._invalidation.invalidate_all()

    def update(self, container_rect: RectSource) -> bool:
        """Run measure + arrange if dirty or the container rect changed.

        Parameters
        ----------
        container_rect:
            The rect made available to the layout (typically the parent's
            content area).

        Returns
        -------
        bool
            ``True`` if a layout pass was executed, ``False`` if skipped.
        """
        rect = resolve_rect(container_rect)
        if not self._dirty and self._last_rect == rect:
            return False

        ctx_measure = MeasureContext(rect.width, rect.height)
        preferred = self._layout.measure(ctx_measure)
        self._last_preferred = (max(0, int(preferred[0])), max(0, int(preferred[1])))

        ctx_arrange = ArrangeContext(rect)
        self._layout.arrange(ctx_arrange)

        self._dirty = False
        self._last_rect = rect
        return True
