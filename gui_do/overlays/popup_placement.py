"""PopupPlacement — portable anchor-relative popup rect computation.

Computes where a transient popup (dropdown, tooltip, context menu, command
palette, toast, nested menu) should be placed relative to an *anchor rect*
so it:

- Appears on the *preferred_side* of the anchor.
- Stays fully inside *screen_bounds*.
- Flips to the opposite side when clipped (controlled by *flip_axes*).
- Is nudged horizontally/vertically when it still overflows after a flip.

All computation is pure rect arithmetic — no OS APIs, no display queries.

Usage::

    from gui_do import PopupPlacement, Side

    placement = PopupPlacement(
        preferred_side=Side.BOTTOM,
        alignment=Alignment.START,
        offset=4,
    )

    result = placement.compute(
        anchor_rect=button.rect,
        popup_size=(200, 120),
        screen_bounds=pygame.Rect(0, 0, 1280, 720),
    )
    popup_panel.set_rect(result.rect)

Or use the standalone helper::

    from gui_do import compute_popup_rect, Side

    rect = compute_popup_rect(
        anchor=button.rect,
        popup_size=(200, 120),
        screen_bounds=pygame.display.get_surface().get_rect(),
        preferred_side=Side.BOTTOM,
    )
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from pygame import Rect


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class Side(Enum):
    """Which side of the anchor the popup should appear on."""

    TOP = "top"
    BOTTOM = "bottom"
    LEFT = "left"
    RIGHT = "right"


class Alignment(Enum):
    """How the popup aligns to the anchor on its secondary axis."""

    START = "start"    # left-align (BOTTOM/TOP) or top-align (LEFT/RIGHT)
    CENTER = "center"
    END = "end"        # right-align or bottom-align


# ---------------------------------------------------------------------------
# PlacementResult
# ---------------------------------------------------------------------------


@dataclass
class PlacementResult:
    """Output of :meth:`PopupPlacement.compute`.

    Attributes
    ----------
    rect:
        Final positioned popup rect (always clipped inside *screen_bounds*).
    actual_side:
        The side that was used after any flip.
    was_flipped:
        True when the preferred side caused overflow and the popup was moved
        to the opposite side.
    was_nudged:
        True when the popup was shifted on the secondary axis to remain inside
        *screen_bounds*.
    """

    rect: Rect
    actual_side: Side
    was_flipped: bool = False
    was_nudged: bool = False


# ---------------------------------------------------------------------------
# PopupPlacement descriptor
# ---------------------------------------------------------------------------


@dataclass
class PopupPlacement:
    """Reusable popup placement descriptor.

    Parameters
    ----------
    preferred_side:
        Which side of the anchor to try first.
    alignment:
        Secondary-axis alignment against the anchor edge (default START).
    offset:
        Gap in pixels between anchor and popup edge (default 0).
    flip_axes:
        When True (default), flip to the opposite side on overflow before
        nudging.  Set False to only nudge.
    """

    preferred_side: Side = Side.BOTTOM
    alignment: Alignment = Alignment.START
    offset: int = 0
    flip_axes: bool = True

    def compute(
        self,
        anchor_rect: Rect,
        popup_size: Tuple[int, int],
        screen_bounds: Rect,
    ) -> PlacementResult:
        """Compute the best popup rect given the anchor and screen bounds.

        Parameters
        ----------
        anchor_rect:
            The widget/region the popup is anchored to.
        popup_size:
            ``(width, height)`` of the popup in pixels.
        screen_bounds:
            Full usable screen area (used for overflow detection and nudging).

        Returns
        -------
        PlacementResult
        """
        return compute_popup_rect(
            anchor=anchor_rect,
            popup_size=popup_size,
            screen_bounds=screen_bounds,
            preferred_side=self.preferred_side,
            alignment=self.alignment,
            offset=self.offset,
            flip_axes=self.flip_axes,
        )


# ---------------------------------------------------------------------------
# Standalone helper
# ---------------------------------------------------------------------------


def compute_popup_rect(
    anchor: Rect,
    popup_size: Tuple[int, int],
    screen_bounds: Rect,
    *,
    preferred_side: Side = Side.BOTTOM,
    alignment: Alignment = Alignment.START,
    offset: int = 0,
    flip_axes: bool = True,
) -> PlacementResult:
    """Compute the best positioned :class:`pygame.Rect` for a popup.

    Parameters
    ----------
    anchor:
        The rect the popup is anchored to (e.g. a button, menu item, cell).
    popup_size:
        ``(width, height)`` of the popup.
    screen_bounds:
        Usable screen area.  The result rect is guaranteed to start inside
        this area; it is nudged but never cropped.
    preferred_side:
        Which side of the anchor to try first.
    alignment:
        Secondary-axis alignment (START / CENTER / END).
    offset:
        Gap in pixels between anchor edge and popup edge.
    flip_axes:
        When True, flip to the opposite side on overflow before nudging.

    Returns
    -------
    PlacementResult
        Contains the final ``rect``, the ``actual_side`` used, and flags
        ``was_flipped`` / ``was_nudged``.
    """
    pw, ph = int(popup_size[0]), int(popup_size[1])
    off = int(offset)

    def _place(side: Side) -> Tuple[int, int]:
        """Return (x, y) top-left for the popup on *side*."""
        ax, ay, aw, ah = anchor.x, anchor.y, anchor.width, anchor.height
        if side == Side.BOTTOM:
            py = ay + ah + off
            px = _align_secondary(ax, aw, pw, alignment, horizontal=True)
        elif side == Side.TOP:
            py = ay - ph - off
            px = _align_secondary(ax, aw, pw, alignment, horizontal=True)
        elif side == Side.RIGHT:
            px = ax + aw + off
            py = _align_secondary(ay, ah, ph, alignment, horizontal=False)
        else:  # LEFT
            px = ax - pw - off
            py = _align_secondary(ay, ah, ph, alignment, horizontal=False)
        return px, py

    def _fits(x: int, y: int) -> bool:
        return (
            x >= screen_bounds.left
            and y >= screen_bounds.top
            and x + pw <= screen_bounds.right
            and y + ph <= screen_bounds.bottom
        )

    x, y = _place(preferred_side)
    actual_side = preferred_side
    was_flipped = False

    if not _fits(x, y) and flip_axes:
        opposite = _opposite_side(preferred_side)
        fx, fy = _place(opposite)
        if _fits(fx, fy):
            x, y = fx, fy
            actual_side = opposite
            was_flipped = True

    # Nudge to stay inside screen_bounds
    was_nudged = False
    nx = _clamp(x, screen_bounds.left, screen_bounds.right - pw)
    ny = _clamp(y, screen_bounds.top, screen_bounds.bottom - ph)
    if nx != x or ny != y:
        x, y = nx, ny
        was_nudged = True

    return PlacementResult(
        rect=Rect(x, y, pw, ph),
        actual_side=actual_side,
        was_flipped=was_flipped,
        was_nudged=was_nudged,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _align_secondary(
    anchor_origin: int,
    anchor_span: int,
    popup_span: int,
    alignment: Alignment,
    *,
    horizontal: bool,  # noqa: ARG001  (kept for clarity)
) -> int:
    if alignment == Alignment.START:
        return anchor_origin
    if alignment == Alignment.END:
        return anchor_origin + anchor_span - popup_span
    # CENTER
    return anchor_origin + (anchor_span - popup_span) // 2


def _opposite_side(side: Side) -> Side:
    return {
        Side.TOP: Side.BOTTOM,
        Side.BOTTOM: Side.TOP,
        Side.LEFT: Side.RIGHT,
        Side.RIGHT: Side.LEFT,
    }[side]


def _clamp(value: int, lo: int, hi: int) -> int:
    return max(lo, min(value, hi))
