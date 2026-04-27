"""LayoutAnimator — tween-driven animated transitions between layout states.

When a :class:`~gui_do.ConstraintLayout` or :class:`~gui_do.FlexLayout` is
re-applied after a constraint change (resize, child insertion, visibility
toggle), child nodes jump to their new positions instantly.
:class:`LayoutAnimator` intercepts that jump: it snapshots current rects,
asks the layout to compute target rects, then uses the scene's
:class:`~gui_do.TweenManager` to interpolate each child smoothly from current
to target.

Usage::

    animator = LayoutAnimator(app.tweens, duration=0.25, easing=Easing.EASE_OUT)

    # Animate a FlexLayout reflow after adding a child:
    panel.children.append(new_button)
    animator.apply_flex(flex_layout, items, container_rect)

    # Animate a ConstraintLayout reflow after a resize:
    animator.apply_constraint(constraint_layout, parent_rect)

    # Cancel any in-flight layout animation:
    animator.cancel()

All animation is done through :class:`~gui_do.TweenManager` using
``target.rect.x`` / ``target.rect.y`` / ``target.rect.width`` /
``target.rect.height`` attribute tweens — no custom rendering code.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, TYPE_CHECKING

from pygame import Rect

from ..core.tween_manager import Easing, TweenHandle, TweenManager

if TYPE_CHECKING:
    from ..layout.constraint_layout import ConstraintLayout
    from ..layout.flex_layout import FlexItem, FlexLayout
    from ..core.ui_node import UiNode


_DEFAULT_DURATION = 0.22
_DEFAULT_EASING = Easing.EASE_IN_OUT


class LayoutAnimator:
    """Animates layout transitions via the :class:`~gui_do.TweenManager`.

    Parameters
    ----------
    tweens:
        The active scene's :class:`~gui_do.TweenManager`.
    duration:
        Animation duration in seconds (default ``0.22``).
    easing:
        Easing function / :class:`~gui_do.Easing` member (default
        ``EASE_IN_OUT``).
    """

    def __init__(
        self,
        tweens: TweenManager,
        *,
        duration: float = _DEFAULT_DURATION,
        easing: Any = _DEFAULT_EASING,
    ) -> None:
        self._tweens = tweens
        self._duration = max(0.0, float(duration))
        self._easing = easing
        self._handles: List[TweenHandle] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def apply_flex(
        self,
        layout: "FlexLayout",
        items: "Sequence[FlexItem]",
        container_rect: Rect,
    ) -> None:
        """Animate children to the positions computed by *layout*.

        Calls :meth:`~gui_do.FlexLayout.apply` to obtain target rects, then
        tweens each child from its current rect to the computed target.
        """
        # Snapshot current rects
        nodes = [item.node for item in items]
        snapshots = {id(node): Rect(node.rect) for node in nodes}

        # Apply layout to compute targets (mutates node rects in-place)
        layout.apply(items, container_rect)
        targets = {id(node): Rect(node.rect) for node in nodes}

        # Restore old rects and animate to targets
        for node in nodes:
            node.rect = Rect(snapshots[id(node)])

        self._animate_to_targets(nodes, targets)

    def apply_constraint(
        self,
        layout: "ConstraintLayout",
        parent_rect: Rect,
    ) -> None:
        """Animate nodes to the positions computed by *layout*.

        Calls :meth:`~gui_do.ConstraintLayout.apply` with *parent_rect* to
        obtain target rects, then tweens each registered node from its current
        rect to the computed target.
        """
        nodes = list(layout._nodes)
        snapshots = {id(node): Rect(node.rect) for node in nodes}

        layout.apply(parent_rect)
        targets = {id(node): Rect(node.rect) for node in nodes}

        for node in nodes:
            node.rect = Rect(snapshots[id(node)])

        self._animate_to_targets(nodes, targets)

    def apply_targets(
        self,
        node_rect_pairs: "Sequence[tuple[UiNode, Rect]]",
    ) -> None:
        """Animate each node to the supplied target rect directly.

        This is the low-level entry point for custom layout strategies.

        Example::

            animator.apply_targets([
                (panel_a, Rect(0, 0, 400, 300)),
                (panel_b, Rect(400, 0, 400, 300)),
            ])
        """
        nodes = [node for node, _ in node_rect_pairs]
        targets = {id(node): Rect(target) for node, target in node_rect_pairs}
        self._animate_to_targets(nodes, targets)

    def cancel(self) -> None:
        """Cancel all in-flight layout tweens immediately."""
        for handle in self._handles:
            handle.cancel()
        self._handles.clear()

    @property
    def is_animating(self) -> bool:
        """Return True while any layout tween is still in progress."""
        self._handles = [h for h in self._handles if not h.is_complete]
        return bool(self._handles)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _animate_to_targets(
        self,
        nodes: "List[UiNode]",
        targets: "Dict[int, Rect]",
    ) -> None:
        """Cancel previous layout tweens then start new ones for each node."""
        self.cancel()

        if self._duration <= 0.0:
            # Instant application — no tweening, just place directly
            for node in nodes:
                target = targets.get(id(node))
                if target is not None:
                    node.rect = Rect(target)
                    node.invalidate()
            return

        for node in nodes:
            target = targets.get(id(node))
            if target is None:
                continue
            current = Rect(node.rect)
            if current == target:
                continue  # already at target; skip

            # Capture values for the closure
            start_x, start_y = float(current.x), float(current.y)
            start_w, start_h = float(current.width), float(current.height)
            end_x, end_y = float(target.x), float(target.y)
            end_w, end_h = float(target.width), float(target.height)
            _node = node

            def _apply(t: float, n=_node, sx=start_x, sy=start_y, sw=start_w, sh=start_h,
                       ex=end_x, ey=end_y, ew=end_w, eh=end_h) -> None:
                n.rect.x = int(sx + (ex - sx) * t)
                n.rect.y = int(sy + (ey - sy) * t)
                n.rect.width = int(sw + (ew - sw) * t)
                n.rect.height = int(sh + (eh - sh) * t)
                n.invalidate()

            handle = self._tweens.tween_fn(
                self._duration,
                _apply,
                easing=self._easing,
            )
            self._handles.append(handle)
