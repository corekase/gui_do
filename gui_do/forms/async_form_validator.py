"""AsyncFormValidator — debounced cross-field reactive validation pipeline.

Each :class:`AsyncFieldValidator` wraps one :class:`~gui_do.FormField` with:
- Synchronous local validation rules run immediately on each field change.
- An optional async validator function run in a background thread.
- A simple elapsed-time debounce so rapid typing doesn't hammer the backend.
- ``is_validating: ObservableValue[bool]`` for spinner display.
- ``async_error: ObservableValue[Optional[str]]`` for the async result.

:class:`AsyncFormValidator` collects one or more :class:`AsyncFieldValidator`
instances and exposes:
- ``is_any_validating: ObservableValue[bool]``
- ``is_valid``: all local + async checks pass for all fields
- ``validate_all_local()``: run synchronous validators for every field immediately
- ``update(dt_seconds)``: must be called once per frame to advance debounce timers

The async check is run in a ``threading.Thread`` (daemon).  Results are
deposited into a thread-safe result slot and collected on the next
:meth:`update` call on the main thread — so ``ObservableValue`` mutations
always happen on the UI thread.

Usage::

    from gui_do import (
        AsyncFormValidator, AsyncFieldValidator,
        FormField,
    )

    username_field = FormField("username", "")

    def check_username_available(value: str) -> Optional[str]:
        # Runs in background thread — no pygame calls here.
        if user_exists(value):
            return "Username already taken"
        return None

    uname_validator = AsyncFieldValidator(
        field=username_field,
        local_rules=[lambda v: None if v else "Required"],
        async_check=check_username_available,
        debounce_ms=400,
    )

    form_validator = AsyncFormValidator([uname_validator])

    # Subscribe to state changes:
    uname_validator.is_validating.subscribe(lambda v: spinner.set_visible(v))
    uname_validator.async_error.subscribe(lambda e: error_label.set_text(e or ""))

    # Call once per frame (passing frame delta in seconds):
    form_validator.update(dt_seconds)

    # Final check before submit:
    if form_validator.is_valid:
        submit()
"""
from __future__ import annotations

import threading
from typing import Callable, List, Optional, Tuple, TYPE_CHECKING

from ..data.presentation_model import ObservableValue

if TYPE_CHECKING:
    from ..forms.form_model import FormField

# A ValidationRule: callable(value) -> Optional[str] (None = valid).
ValidationRule = Callable[[object], Optional[str]]


# ---------------------------------------------------------------------------
# AsyncFieldValidator
# ---------------------------------------------------------------------------


class AsyncFieldValidator:
    """Wraps a single :class:`~gui_do.FormField` with sync + async validation.

    Parameters
    ----------
    field:
        The :class:`~gui_do.FormField` to validate.
    local_rules:
        Synchronous validation callables: ``(value) -> Optional[str]``.
        Run immediately on each field change.
    async_check:
        Optional callable ``(value) -> Optional[str]`` run in a daemon thread.
        Returns an error string on failure, ``None`` on success.
    debounce_ms:
        Milliseconds to wait after the last field change before launching the
        async check.  Default 400 ms.
    """

    def __init__(
        self,
        *,
        field: "FormField",
        local_rules: Optional[List[ValidationRule]] = None,
        async_check: Optional[Callable[[object], Optional[str]]] = None,
        debounce_ms: int = 400,
    ) -> None:
        self._field = field
        self._local_rules: List[ValidationRule] = list(local_rules or [])
        self._async_check = async_check
        self._debounce_s: float = max(0.0, int(debounce_ms)) / 1000.0

        # Observable state (mutated on the main thread only)
        self.is_validating: ObservableValue[bool] = ObservableValue(False)
        self.async_error: ObservableValue[Optional[str]] = ObservableValue(None)
        self.local_error: ObservableValue[Optional[str]] = ObservableValue(None)

        # Debounce elapsed timer
        self._time_since_change: float = 0.0
        self._pending_async: bool = False

        # Thread-safe result slot: (generation, result_or_error, is_error)
        self._result_lock = threading.Lock()
        self._result_slot: Optional[Tuple[int, object, bool]] = None

        # Generation counter for stale-response rejection
        self._generation: int = 0

        # Subscribe to field value changes
        self._unsub = field.value.subscribe(self._on_value_changed)

    # ------------------------------------------------------------------
    # Sync validation
    # ------------------------------------------------------------------

    def validate_local(self) -> bool:
        """Run synchronous rules against the current field value immediately.

        Returns ``True`` if all rules pass.
        """
        value = self._field.value.value
        for rule in self._local_rules:
            try:
                error = rule(value)
            except Exception as exc:
                error = str(exc)
            if error is not None:
                self.local_error.value = str(error)
                return False
        self.local_error.value = None
        return True

    @property
    def is_locally_valid(self) -> bool:
        return self.local_error.value is None

    @property
    def is_valid(self) -> bool:
        """``True`` when local and async checks both pass (and no check is in flight)."""
        return (
            self.local_error.value is None
            and self.async_error.value is None
            and not self.is_validating.value
            and not self._pending_async
        )

    # ------------------------------------------------------------------
    # Field change handler
    # ------------------------------------------------------------------

    def _on_value_changed(self, _value: object) -> None:
        self.validate_local()
        if self._async_check is not None:
            # Reset debounce timer
            self._time_since_change = 0.0
            self._pending_async = True

    # ------------------------------------------------------------------
    # Per-frame update
    # ------------------------------------------------------------------

    def update(self, dt_seconds: float) -> None:
        """Advance the debounce timer and collect async results.

        Must be called once per frame from the UI thread.
        """
        # Collect any completed async result from the background thread
        self._collect_result()

        # Advance debounce timer
        if self._pending_async and self._async_check is not None:
            self._time_since_change += float(dt_seconds)
            if self._time_since_change >= self._debounce_s:
                self._pending_async = False
                self._launch_async_check()

    # ------------------------------------------------------------------
    # Async check
    # ------------------------------------------------------------------

    def _launch_async_check(self) -> None:
        """Launch a background thread for the async check."""
        self._generation += 1
        my_gen = self._generation
        value = self._field.value.value
        async_check = self._async_check

        self.is_validating.value = True
        self.async_error.value = None

        def _run() -> None:
            try:
                result = async_check(value)  # type: ignore[misc]
                with self._result_lock:
                    self._result_slot = (my_gen, result, False)
            except Exception as exc:
                with self._result_lock:
                    self._result_slot = (my_gen, exc, True)

        t = threading.Thread(target=_run, daemon=True)
        t.start()

    def _collect_result(self) -> None:
        """Collect and process a completed async result (if any)."""
        with self._result_lock:
            slot = self._result_slot
            self._result_slot = None
        if slot is None:
            return
        gen, payload, is_error = slot
        if gen != self._generation:
            return  # Stale response — discard
        self.is_validating.value = False
        if is_error:
            self.async_error.value = f"Validation error: {payload}"
        else:
            self.async_error.value = payload  # None = valid, str = error

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def dispose(self) -> None:
        """Unsubscribe from the field.  In-flight threads are daemon and expire on app exit."""
        self._unsub()
        # Invalidate any in-flight result by bumping the generation
        self._generation += 1


# ---------------------------------------------------------------------------
# AsyncFormValidator
# ---------------------------------------------------------------------------


class AsyncFormValidator:
    """Aggregates multiple :class:`AsyncFieldValidator` instances.

    Parameters
    ----------
    field_validators:
        The field validators to manage.
    """

    def __init__(self, field_validators: List[AsyncFieldValidator]) -> None:
        self._validators: List[AsyncFieldValidator] = list(field_validators)
        self.is_any_validating: ObservableValue[bool] = ObservableValue(False)

        # Subscribe each validator's is_validating to update aggregate
        self._unsubs = [
            v.is_validating.subscribe(self._sync_aggregate)
            for v in self._validators
        ]

    # ------------------------------------------------------------------
    # Per-frame update
    # ------------------------------------------------------------------

    def update(self, dt_seconds: float) -> None:
        """Advance all field validator debouncers.  Call once per frame."""
        for v in self._validators:
            v.update(dt_seconds)

    # ------------------------------------------------------------------
    # State queries
    # ------------------------------------------------------------------

    @property
    def is_valid(self) -> bool:
        """``True`` when all field validators report valid."""
        return all(v.is_valid for v in self._validators)

    @property
    def is_validating(self) -> bool:
        """``True`` when any field validator has an in-flight async check."""
        return any(v.is_validating.value for v in self._validators)

    def validate_all_local(self) -> bool:
        """Run synchronous validators for all fields immediately.

        Returns ``True`` if all fields pass local validation.
        """
        results = [v.validate_local() for v in self._validators]
        return all(results)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _sync_aggregate(self, _: object) -> None:
        self.is_any_validating.value = self.is_validating

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def dispose(self) -> None:
        """Dispose all field validators and unsubscribe aggregation."""
        for unsub in self._unsubs:
            try:
                unsub()
            except Exception:
                pass
        for v in self._validators:
            v.dispose()
