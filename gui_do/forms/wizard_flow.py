"""WizardFlow — multi-step form wizard with per-step validation.

Coordinates a sequence of :class:`WizardStep` objects, validating each step
via the existing :class:`~gui_do.ValidationPipeline` before advancing.
Progress is tracked as an :class:`~gui_do.ObservableValue` so any bound UI
element (e.g. a progress bar) updates automatically.

Usage::

    from gui_do import WizardFlow, WizardStep, WizardHandle

    steps = [
        WizardStep(
            title="Name",
            fields=["first_name", "last_name"],
            on_validate=lambda d: [] if d.get("first_name") else ["First name required"],
        ),
        WizardStep(title="Email", fields=["email"]),
        WizardStep(title="Confirm", fields=[]),
    ]

    def _on_done(data):
        print("Collected:", data)

    wizard = WizardFlow(steps, on_complete=_on_done, on_cancel=lambda: None)

    # Advance from step 0 → 1:
    ok, errors = wizard.advance({"first_name": "Alice", "last_name": "Smith"})

    # Advance from step 1 → 2:
    ok, errors = wizard.advance({"email": "alice@example.com"})

    # Last step calls on_complete:
    ok, errors = wizard.advance({})

    # Go back:
    wizard.back()

    # Observe progress:
    wizard.progress.subscribe(lambda v: update_progress_bar(v))

    # Cancel:
    wizard.cancel()
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from ..data.presentation_model import ObservableValue


@dataclass
class WizardStep:
    """Metadata and optional lifecycle hooks for a single wizard step.

    Attributes
    ----------
    title:
        Human-readable step name (e.g. for a header label).
    fields:
        List of data key names expected on this step.
    on_validate:
        Optional callable ``(data_dict) -> List[str]`` returning validation
        error messages.  Return an empty list (or ``None``) to pass.
    on_enter:
        Optional callable ``(collected_data_so_far) -> None`` called when this
        step becomes active.
    on_leave:
        Optional callable ``(step_data, direction) -> None`` called when
        leaving this step.  *direction* is ``"forward"`` or ``"back"``.
    """

    title: str
    fields: List[str] = field(default_factory=list)
    on_validate: Optional[Callable[[Dict[str, Any]], List[str]]] = None
    on_enter: Optional[Callable[[Dict[str, Any]], None]] = None
    on_leave: Optional[Callable[[Dict[str, Any], str], None]] = None


class WizardHandle:
    """Cancellable handle returned from :class:`WizardFlow`.

    Mirrors the pattern of ``DialogHandle`` and ``OverlayHandle`` already
    used in the package.
    """

    def __init__(self, flow: "WizardFlow") -> None:
        self._flow = flow
        self._cancelled = False

    def cancel(self) -> None:
        """Cancel the wizard flow (calls ``on_cancel`` if provided)."""
        if not self._cancelled:
            self._cancelled = True
            self._flow.cancel()

    @property
    def is_cancelled(self) -> bool:
        return self._cancelled

    @property
    def flow(self) -> "WizardFlow":
        return self._flow


class WizardFlow:
    """Coordinator for a multi-step form wizard.

    Parameters
    ----------
    steps:
        Ordered list of :class:`WizardStep` objects.  Must contain at least
        one step.
    on_complete:
        Called with ``(collected_data: dict)`` when the last step is advanced
        successfully.
    on_cancel:
        Optional callback with no arguments, called when :meth:`cancel` is
        invoked.
    """

    def __init__(
        self,
        steps: List[WizardStep],
        *,
        on_complete: Callable[[Dict[str, Any]], None],
        on_cancel: Optional[Callable[[], None]] = None,
    ) -> None:
        if not steps:
            raise ValueError("WizardFlow requires at least one step")
        self._steps = list(steps)
        self._on_complete = on_complete
        self._on_cancel = on_cancel
        self._index: int = 0
        self._data: Dict[str, Any] = {}
        self._cancelled: bool = False
        self._progress: ObservableValue[float] = ObservableValue(0.0)
        self._step_data: List[Optional[Dict[str, Any]]] = [None] * len(self._steps)

        # Notify enter callback for step 0
        self._fire_enter(0)

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def advance(
        self,
        data: Dict[str, Any],
    ) -> Tuple[bool, List[str]]:
        """Validate *data* and advance to the next step if valid.

        Parameters
        ----------
        data:
            Key-value pairs for the current step's fields.

        Returns
        -------
        ok:
            ``True`` if validation passed and the step was advanced (or
            completed).
        errors:
            List of validation error messages.  Empty on success.
        """
        step = self._steps[self._index]
        errors: List[str] = []

        if step.on_validate is not None:
            result = step.on_validate(data)
            if result:
                errors = list(result)

        if errors:
            return False, errors

        # Persist step data
        self._step_data[self._index] = dict(data)
        self._data.update(data)

        # Leave callback
        self._fire_leave(self._index, "forward", data)

        if self._index >= len(self._steps) - 1:
            # Last step — complete
            self._update_progress(1.0)
            try:
                self._on_complete(dict(self._data))
            except Exception:
                pass
            return True, []

        # Advance
        self._index += 1
        self._update_progress(self._index / len(self._steps))
        self._fire_enter(self._index)
        return True, []

    def back(self) -> bool:
        """Move to the previous step.

        Returns
        -------
        bool
            ``True`` if the step was changed; ``False`` if already at step 0.
        """
        if self._index <= 0:
            return False

        self._fire_leave(self._index, "back", {})
        self._index -= 1
        self._update_progress(self._index / len(self._steps))

        self._fire_enter(self._index)
        return True

    def cancel(self) -> None:
        """Cancel the wizard flow."""
        self._cancelled = True
        if self._on_cancel is not None:
            try:
                self._on_cancel()
            except Exception:
                pass

    def handle(self) -> WizardHandle:
        """Return a :class:`WizardHandle` tied to this flow."""
        return WizardHandle(self)

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    @property
    def current_step(self) -> WizardStep:
        """The currently active :class:`WizardStep`."""
        return self._steps[self._index]

    @property
    def step_index(self) -> int:
        """Zero-based index of the current step."""
        return self._index

    @property
    def step_count(self) -> int:
        """Total number of steps."""
        return len(self._steps)

    @property
    def progress(self) -> ObservableValue:
        """``ObservableValue[float]`` in [0.0, 1.0] tracking completion."""
        return self._progress

    @property
    def collected_data(self) -> Dict[str, Any]:
        """All data collected so far (merged across steps)."""
        return dict(self._data)

    @property
    def is_cancelled(self) -> bool:
        return self._cancelled

    def step_data(self, index: int) -> Optional[Dict[str, Any]]:
        """Return the data submitted for step *index*, or ``None`` if not yet visited."""
        return self._step_data[index]

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _update_progress(self, value: float) -> None:
        self._progress.value = round(float(value), 6)

    def _fire_enter(self, index: int) -> None:
        step = self._steps[index]
        if step.on_enter is not None:
            try:
                step.on_enter(dict(self._data))
            except Exception:
                pass

    def _fire_leave(self, index: int, direction: str, data: Dict[str, Any]) -> None:
        step = self._steps[index]
        if step.on_leave is not None:
            try:
                step.on_leave(data, direction)
            except Exception:
                pass
