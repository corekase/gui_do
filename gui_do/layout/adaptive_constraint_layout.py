"""AdaptiveConstraintLayout — declarative constraint-based layout engine v2.

Provides a richer constraint model than the original ``AnchorConstraint``
with:

* :class:`LayoutConstraint` — named, priority-tagged edge/size relationship
* :class:`ConstraintSet` — collision-detecting constraint collection
* :class:`ConstraintLayoutEngine` — Cassowary-style greedy solver
* :class:`AdaptivePolicy` — viewport-size-adaptive constraint groups
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Sequence, Dict, List

from pygame import Rect

__all__ = [
    "ConstraintAttr",
    "LayoutConstraint",
    "ConstraintSet",
    "ConstraintLayoutEngine",
    "AdaptivePolicy",
]


# ---------------------------------------------------------------------------
# ConstraintAttr
# ---------------------------------------------------------------------------


class ConstraintAttr(str, Enum):
    """Addressable attributes of a widget rect that constraints can target."""

    LEFT = "left"
    RIGHT = "right"
    TOP = "top"
    BOTTOM = "bottom"
    WIDTH = "width"
    HEIGHT = "height"
    CENTER_X = "center_x"
    CENTER_Y = "center_y"


# ---------------------------------------------------------------------------
# LayoutConstraint
# ---------------------------------------------------------------------------


@dataclass
class LayoutConstraint:
    """A single declarative constraint relating a widget attribute to a value.

    Parameters
    ----------
    target_id:
        Logical widget identifier this constraint is applied to.
    attribute:
        Which geometric property is being constrained.
    value:
        Pixel value or fraction (``is_fraction=True``) of the container
        dimension.
    is_fraction:
        If ``True``, *value* is multiplied by the relevant container dimension
        at solve time (e.g. ``0.5`` → half the container width for
        :attr:`ConstraintAttr.LEFT`).
    priority:
        Larger numbers win when constraints conflict (default 1000 = required).
    name:
        Optional human-readable label for debugging.
    """

    target_id: str
    attribute: ConstraintAttr
    value: float
    is_fraction: bool = False
    priority: int = 1000
    name: str = ""

    def resolve(self, container: Rect) -> float:
        """Return the concrete pixel value given *container*."""
        if not self.is_fraction:
            return self.value
        if self.attribute in (
            ConstraintAttr.LEFT,
            ConstraintAttr.RIGHT,
            ConstraintAttr.CENTER_X,
            ConstraintAttr.WIDTH,
        ):
            return self.value * container.width
        return self.value * container.height


# ---------------------------------------------------------------------------
# ConstraintSet
# ---------------------------------------------------------------------------


class ConstraintSet:
    """Ordered collection of :class:`LayoutConstraint` with conflict detection.

    A *conflict* occurs when two constraints target the same (target_id,
    attribute) pair.  :meth:`add` raises ``ValueError`` if the set already
    contains a constraint with equal or higher priority for that slot;
    lower-priority constraints silently replace higher-priority ones.
    """

    def __init__(self) -> None:
        self._constraints: List[LayoutConstraint] = []

    def add(self, constraint: LayoutConstraint) -> None:
        """Add *constraint*, detecting and handling conflicts.

        If an existing constraint targets the same (id, attr) with the same
        priority a ``ValueError`` is raised.  If the existing has lower
        priority the new constraint replaces it; if higher priority, the new
        constraint is ignored.
        """
        key = (constraint.target_id, constraint.attribute)
        for i, existing in enumerate(self._constraints):
            if (existing.target_id, existing.attribute) == key:
                if existing.priority == constraint.priority:
                    raise ValueError(
                        f"Conflicting constraints for {key!r} at priority "
                        f"{constraint.priority}"
                    )
                if constraint.priority > existing.priority:
                    self._constraints[i] = constraint
                # else: existing has higher priority, ignore new one
                return
        self._constraints.append(constraint)

    def remove(self, target_id: str, attribute: ConstraintAttr) -> None:
        """Remove the constraint targeting (target_id, attribute), if present."""
        self._constraints = [
            c
            for c in self._constraints
            if not (c.target_id == target_id and c.attribute == attribute)
        ]

    def for_target(self, target_id: str) -> List[LayoutConstraint]:
        """Return all constraints for *target_id*."""
        return [c for c in self._constraints if c.target_id == target_id]

    @property
    def all_constraints(self) -> List[LayoutConstraint]:
        return list(self._constraints)

    def __len__(self) -> int:
        return len(self._constraints)


# ---------------------------------------------------------------------------
# ConstraintLayoutEngine
# ---------------------------------------------------------------------------


class ConstraintLayoutEngine:
    """Greedy constraint solver that maps widget IDs to ``pygame.Rect`` objects.

    The engine resolves constraints in *priority* order (highest first).
    For each widget it gathers LEFT/RIGHT/TOP/BOTTOM/WIDTH/HEIGHT/CENTER_X/
    CENTER_Y constraints and derives a ``pygame.Rect`` against the supplied
    *container*.

    Initial rects (provided via :meth:`set_initial_rect`) act as fallback
    values for any unconstrained attribute.

    Usage::

        engine = ConstraintLayoutEngine()
        engine.set_initial_rect("btn", pygame.Rect(0, 0, 100, 30))

        cs = ConstraintSet()
        cs.add(LayoutConstraint("btn", ConstraintAttr.LEFT, 10))
        cs.add(LayoutConstraint("btn", ConstraintAttr.TOP, 20))

        results = engine.solve(cs, container=pygame.Rect(0, 0, 800, 600))
        btn_rect = results["btn"]
    """

    def __init__(self) -> None:
        self._initial_rects: Dict[str, Rect] = {}

    def set_initial_rect(self, target_id: str, rect: Rect) -> None:
        """Set the fallback rect for *target_id*."""
        self._initial_rects[target_id] = rect.copy()

    def solve(
        self,
        constraint_set: ConstraintSet,
        container: Rect,
    ) -> Dict[str, Rect]:
        """Solve all constraints in *constraint_set* against *container*.

        Returns a dict mapping target IDs to resolved ``pygame.Rect`` objects.
        """
        # Build a per-target group in a single O(m) pass, sorted descending by priority.
        # This replaces the O(K*m) pattern of calling for_target() per target.
        by_target: Dict[str, list] = {}
        for c in constraint_set._constraints:
            bucket = by_target.get(c.target_id)
            if bucket is None:
                by_target[c.target_id] = [c]
            else:
                bucket.append(c)
        for bucket in by_target.values():
            bucket.sort(key=lambda c: -c.priority)

        # Collect all target IDs (constraints + initial rects)
        target_ids = by_target.keys() | self._initial_rects.keys()

        results: Dict[str, Rect] = {}

        for tid in sorted(target_ids):
            base = self._initial_rects.get(tid, Rect(0, 0, 0, 0)).copy()
            constraints = by_target.get(tid, [])
            left = float(base.left)
            top = float(base.top)
            width = float(base.width)
            height = float(base.height)

            for c in constraints:
                v = c.resolve(container)
                if c.attribute == ConstraintAttr.LEFT:
                    left = container.left + v
                elif c.attribute == ConstraintAttr.RIGHT:
                    left = container.right - v - width
                elif c.attribute == ConstraintAttr.TOP:
                    top = container.top + v
                elif c.attribute == ConstraintAttr.BOTTOM:
                    top = container.bottom - v - height
                elif c.attribute == ConstraintAttr.WIDTH:
                    width = v
                elif c.attribute == ConstraintAttr.HEIGHT:
                    height = v
                elif c.attribute == ConstraintAttr.CENTER_X:
                    left = container.left + v - width / 2.0
                elif c.attribute == ConstraintAttr.CENTER_Y:
                    top = container.top + v - height / 2.0

            results[tid] = Rect(int(left), int(top), int(width), int(height))

        return results


# ---------------------------------------------------------------------------
# AdaptivePolicy
# ---------------------------------------------------------------------------


@dataclass
class AdaptivePolicy:
    """A named set of :class:`LayoutConstraint` objects active above a minimum viewport size.

    Policies are sorted by :attr:`min_width` (descending) and the first
    matching one is selected by :meth:`ConstraintLayoutEngine.solve_adaptive`.

    Parameters
    ----------
    name:
        Descriptive label (e.g. ``"desktop"``, ``"tablet"``, ``"mobile"``).
    min_width:
        Minimum container width (inclusive) for this policy to be active.
        Use ``0`` for a catch-all fallback.
    constraints:
        The constraints to apply when this policy is active.
    """

    name: str
    min_width: int
    constraints: List[LayoutConstraint] = field(default_factory=list)

    def build_constraint_set(self) -> ConstraintSet:
        """Return a :class:`ConstraintSet` populated with this policy's constraints."""
        cs = ConstraintSet()
        for c in self.constraints:
            cs.add(c)
        return cs


def resolve_adaptive_policy(
    policies: Sequence[AdaptivePolicy],
    container: Rect,
) -> Optional[AdaptivePolicy]:
    """Return the most-specific policy whose ``min_width`` <= container width.

    Policies are tried in descending ``min_width`` order.  If *policies* is
    already sorted (descending) the sort is effectively free (timsort is O(n)
    on a sorted input).
    """
    sorted_policies = sorted(policies, key=lambda p: -p.min_width)
    for policy in sorted_policies:
        if container.width >= policy.min_width:
            return policy
    return None
