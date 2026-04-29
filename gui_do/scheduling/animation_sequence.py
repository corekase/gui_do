"""AnimationSequence — composable sequential and parallel animation builder."""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from .tween_manager import Easing, TweenManager


class AnimationHandle:
    """Handle returned from :meth:`AnimationSequence.start`.

    Use :meth:`cancel` to abort remaining steps.
    """

    def __init__(self) -> None:
        self._cancelled = False

    def cancel(self) -> None:
        """Cancel remaining steps.  Steps already in flight complete naturally."""
        self._cancelled = True

    @property
    def cancelled(self) -> bool:
        return self._cancelled


class AnimationSequence:
    """Build and run a chain of sequential and parallel tween animations.

    Steps are added with :meth:`then`, :meth:`parallel`, and :meth:`wait`.
    Call :meth:`start` to begin execution and receive a cancellable handle.

    Usage::

        seq = AnimationSequence(app.tweens)
        handle = (
            seq
            .then(target=ctrl, attr="alpha", end_value=1.0, duration_seconds=0.4)
            .wait(0.1)
            .parallel([
                dict(target=ctrl, attr="rect.x", end_value=200, duration_seconds=0.3),
                dict(target=ctrl, attr="rect.y", end_value=100, duration_seconds=0.3),
            ])
            .on_done(lambda: print("finished"))
            .start()
        )
        # Later:
        handle.cancel()
    """

    def __init__(self, manager: TweenManager) -> None:
        self._manager = manager
        self._steps: List[Dict[str, Any]] = []
        self._done_callback: Optional[Callable[[], None]] = None

    # ------------------------------------------------------------------
    # Builder methods
    # ------------------------------------------------------------------

    def then(
        self,
        *,
        target: object,
        attr: str,
        end_value: Any,
        duration_seconds: float,
        easing: Any = Easing.EASE_IN_OUT,
    ) -> "AnimationSequence":
        """Add a sequential animation step that runs after all previous steps."""
        self._steps.append(
            {
                "type": "seq",
                "target": target,
                "attr": attr,
                "end_value": end_value,
                "duration_seconds": duration_seconds,
                "easing": easing,
            }
        )
        return self

    def parallel(
        self, steps: List[Dict[str, Any]]
    ) -> "AnimationSequence":
        """Add a group of animations that all start simultaneously.

        Each entry in *steps* is a dict with keys ``target``, ``attr``,
        ``end_value``, ``duration_seconds``, and optionally ``easing``.
        The group completes when the last animation in the group finishes.
        """
        self._steps.append({"type": "par", "steps": list(steps)})
        return self

    def wait(self, seconds: float) -> "AnimationSequence":
        """Add a pause between steps."""
        self._steps.append({"type": "wait", "seconds": max(0.0, float(seconds))})
        return self

    def on_done(self, callback: Callable[[], None]) -> "AnimationSequence":
        """Register a callback to invoke once all steps complete."""
        self._done_callback = callback
        return self

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def start(self) -> AnimationHandle:
        """Begin executing the sequence and return a :class:`AnimationHandle`."""
        handle = AnimationHandle()
        self._run(list(self._steps), handle)
        return handle

    def _run(self, remaining: List[Dict[str, Any]], handle: AnimationHandle) -> None:
        if handle.cancelled:
            return
        if not remaining:
            if self._done_callback is not None:
                try:
                    self._done_callback()
                except Exception:
                    pass
            return

        step = remaining[0]
        rest = remaining[1:]

        def _next() -> None:
            if not handle.cancelled:
                self._run(rest, handle)

        stype = step["type"]

        if stype == "seq":
            self._manager.tween(
                target=step["target"],
                attr=step["attr"],
                end_value=step["end_value"],
                duration_seconds=step["duration_seconds"],
                easing=step.get("easing", Easing.EASE_IN_OUT),
                on_complete=_next,
            )

        elif stype == "par":
            sub_steps: List[Dict[str, Any]] = step.get("steps", [])
            if not sub_steps:
                _next()
                return
            remaining_count = [len(sub_steps)]

            def _on_sub_done() -> None:
                remaining_count[0] -= 1
                if remaining_count[0] <= 0:
                    _next()

            for sub in sub_steps:
                self._manager.tween(
                    target=sub["target"],
                    attr=sub["attr"],
                    end_value=sub["end_value"],
                    duration_seconds=sub["duration_seconds"],
                    easing=sub.get("easing", Easing.EASE_IN_OUT),
                    on_complete=_on_sub_done,
                )

        elif stype == "wait":
            self._manager.tween_fn(
                duration_seconds=step["seconds"],
                fn=lambda _t: None,
                on_complete=_next,
            )
