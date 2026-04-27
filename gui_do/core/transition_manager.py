"""TransitionManager — declarative animated state-change hooks for controls.

Connects control state transitions (show, hide, enable, disable) to
:class:`~gui_do.TweenManager`-driven animations without requiring each control
to write tween choreography manually.

Usage::

    from gui_do import TransitionManager, TransitionSpec, TransitionEvent

    tm = TransitionManager(app.tweens)

    # Fade an overlay panel in and out:
    tm.register(
        overlay_panel,
        TransitionEvent.SHOW,
        TransitionSpec(attr="alpha", start_value=0.0, end_value=1.0,
                       duration_seconds=0.25, easing="ease_out"),
    )
    tm.register(
        overlay_panel,
        TransitionEvent.HIDE,
        TransitionSpec(attr="alpha", start_value=1.0, end_value=0.0,
                       duration_seconds=0.2),
    )

    # In the control's _on_visibility_changed hook:
    def _on_visibility_changed(self, old_visible, new_visible):
        super()._on_visibility_changed(old_visible, new_visible)
        if new_visible:
            transition_manager.on_show(self)
        else:
            transition_manager.on_hide(self)

Multiple :class:`TransitionSpec` objects can be registered for the same event
to animate different attributes simultaneously.

TransitionSpec.start_value
    Set to a concrete value to always start the tween from that value.
    Set to ``None`` (default) to read the current attribute value at trigger
    time — useful for interrupting an in-progress animation gracefully.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..core.tween_manager import TweenManager


# ---------------------------------------------------------------------------
# TransitionEvent
# ---------------------------------------------------------------------------


class TransitionEvent(Enum):
    """The control state-change event that triggers a :class:`TransitionSpec`."""

    SHOW = "show"       # visible False → True
    HIDE = "hide"       # visible True → False
    ENABLE = "enable"   # enabled False → True
    DISABLE = "disable" # enabled True → False


# ---------------------------------------------------------------------------
# TransitionSpec
# ---------------------------------------------------------------------------


@dataclass
class TransitionSpec:
    """Describes one animated property transition triggered by a state change.

    Parameters
    ----------
    attr:
        Name of the attribute to tween on the target node
        (e.g. ``"alpha"``, ``"rect.x"``).
    end_value:
        Value the attribute should reach at the end of the tween.
    duration_seconds:
        How long the animation runs (default 0.2 s).
    easing:
        Easing name or :class:`~gui_do.Easing` member (default ``"ease_in_out"``).
    on_done:
        Optional callback invoked when the tween completes.
    start_value:
        If not ``None`` the attribute is set to this value immediately before
        the tween begins.  ``None`` (default) reads the current value so
        interrupted tweens resume from wherever they are.
    """

    attr: str
    end_value: Any
    duration_seconds: float = 0.2
    easing: Any = "ease_in_out"
    on_done: Optional[Callable[[], None]] = None
    start_value: Any = None


# ---------------------------------------------------------------------------
# TransitionManager
# ---------------------------------------------------------------------------

_SpecMap = Dict[TransitionEvent, List[TransitionSpec]]


class TransitionManager:
    """Runs :class:`TransitionSpec` animations in response to control state changes.

    Parameters
    ----------
    tween_manager:
        The :class:`~gui_do.TweenManager` instance that drives animations
        (one per scene, available as ``app.tweens``).
    """

    def __init__(self, tween_manager: "TweenManager") -> None:
        self._tweens: "TweenManager" = tween_manager
        self._specs: Dict[str, _SpecMap] = {}

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(
        self,
        node: Any,
        event: TransitionEvent,
        spec: TransitionSpec,
    ) -> None:
        """Attach a :class:`TransitionSpec` to *node* for *event*.

        Multiple specs for the same ``(node, event)`` pair are accumulated
        and all triggered simultaneously when the event fires.
        """
        event = TransitionEvent(event) if isinstance(event, str) else event
        nid = _node_key(node)
        self._specs.setdefault(nid, {}).setdefault(event, []).append(spec)

    def unregister(self, node: Any) -> None:
        """Remove all transition specs registered for *node*."""
        self._specs.pop(_node_key(node), None)

    def unregister_event(self, node: Any, event: TransitionEvent) -> None:
        """Remove all transition specs for a specific ``(node, event)`` pair."""
        event = TransitionEvent(event) if isinstance(event, str) else event
        nid = _node_key(node)
        spec_map = self._specs.get(nid)
        if spec_map is not None:
            spec_map.pop(event, None)

    # ------------------------------------------------------------------
    # Trigger API
    # ------------------------------------------------------------------

    def on_show(self, node: Any) -> None:
        """Trigger the ``SHOW`` transition for *node*."""
        self._fire(node, TransitionEvent.SHOW)

    def on_hide(self, node: Any) -> None:
        """Trigger the ``HIDE`` transition for *node*."""
        self._fire(node, TransitionEvent.HIDE)

    def on_enable(self, node: Any) -> None:
        """Trigger the ``ENABLE`` transition for *node*."""
        self._fire(node, TransitionEvent.ENABLE)

    def on_disable(self, node: Any) -> None:
        """Trigger the ``DISABLE`` transition for *node*."""
        self._fire(node, TransitionEvent.DISABLE)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _fire(self, node: Any, event: TransitionEvent) -> None:
        nid = _node_key(node)
        specs = self._specs.get(nid, {}).get(event, [])
        for spec in specs:
            # Optionally override the start value before tweening.
            if spec.start_value is not None:
                try:
                    setattr(node, spec.attr, spec.start_value)
                except (AttributeError, TypeError):
                    pass
            # tween() reads start_value from current getattr(target, attr).
            try:
                self._tweens.tween(
                    target=node,
                    attr=spec.attr,
                    end_value=spec.end_value,
                    duration_seconds=spec.duration_seconds,
                    easing=spec.easing,
                    on_complete=spec.on_done,
                )
            except Exception:
                pass  # Gracefully skip if target attr not accessible.


def _node_key(node: Any) -> str:
    """Derive a stable string key for *node*."""
    try:
        return str(node.control_id)
    except AttributeError:
        return str(id(node))
