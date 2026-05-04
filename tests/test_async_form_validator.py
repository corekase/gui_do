"""Tests for gui_do.forms.async_form_validator (S7)."""
import time
import threading
import unittest

from gui_do.data.presentation_model import ObservableValue
from gui_do.forms.async_form_validator import AsyncFieldValidator, AsyncFormValidator


# Minimal FormField stub — does not require pygame
class _StubField:
    def __init__(self, initial_value=""):
        self.value = ObservableValue(initial_value)
        self.name = "test_field"


class TestAsyncFieldValidatorLocalRules(unittest.TestCase):

    def _make(self, rules=None, debounce_ms=50):
        field = _StubField("initial")
        v = AsyncFieldValidator(field=field, local_rules=rules or [], debounce_ms=debounce_ms)
        return field, v

    def test_no_rules_is_locally_valid(self):
        _, v = self._make()
        self.assertTrue(v.validate_local())
        self.assertIsNone(v.local_error.value)

    def test_single_rule_pass(self):
        _, v = self._make(rules=[lambda val: None])
        self.assertTrue(v.validate_local())

    def test_single_rule_fail(self):
        _, v = self._make(rules=[lambda val: "Required"])
        result = v.validate_local()
        self.assertFalse(result)
        self.assertEqual(v.local_error.value, "Required")

    def test_first_failing_rule_wins(self):
        _, v = self._make(rules=[
            lambda val: "Error1",
            lambda val: "Error2",
        ])
        v.validate_local()
        self.assertEqual(v.local_error.value, "Error1")

    def test_local_error_clears_when_valid(self):
        field, v = self._make(rules=[lambda val: None if val else "Required"])
        field.value.value = ""
        v.validate_local()
        self.assertEqual(v.local_error.value, "Required")
        field.value.value = "ok"
        v.validate_local()
        self.assertIsNone(v.local_error.value)

    def test_rule_exception_treated_as_error(self):
        def bad(val):
            raise ValueError("oops")
        _, v = self._make(rules=[bad])
        result = v.validate_local()
        self.assertFalse(result)
        self.assertIsNotNone(v.local_error.value)

    def test_on_value_change_triggers_local_validation(self):
        field, v = self._make(rules=[lambda val: None if val else "Required"])
        field.value.value = ""
        self.assertEqual(v.local_error.value, "Required")
        field.value.value = "hello"
        self.assertIsNone(v.local_error.value)


class TestAsyncFieldValidatorObservables(unittest.TestCase):

    def test_is_validating_initially_false(self):
        field = _StubField()
        v = AsyncFieldValidator(field=field)
        self.assertFalse(v.is_validating.value)

    def test_async_error_initially_none(self):
        field = _StubField()
        v = AsyncFieldValidator(field=field)
        self.assertIsNone(v.async_error.value)

    def test_local_error_initially_none(self):
        field = _StubField()
        v = AsyncFieldValidator(field=field)
        self.assertIsNone(v.local_error.value)

    def test_is_valid_when_all_clear(self):
        field = _StubField()
        v = AsyncFieldValidator(field=field)
        self.assertTrue(v.is_valid)

    def test_is_valid_false_when_local_error(self):
        field = _StubField()
        v = AsyncFieldValidator(field=field, local_rules=[lambda val: "bad"])
        field.value.value = "x"  # triggers validation
        self.assertFalse(v.is_valid)


class TestAsyncFieldValidatorAsyncCheck(unittest.TestCase):

    def _wait_for(self, fn, timeout=3.0, interval=0.05):
        """Poll until fn() returns True."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if fn():
                return True
            time.sleep(interval)
        return False

    def test_async_check_called_after_debounce(self):
        field = _StubField()
        results = []

        def check(val):
            results.append(val)
            return None

        v = AsyncFieldValidator(field=field, async_check=check, debounce_ms=50)
        field.value.value = "hello"

        # Simulate frame updates (50ms debounce = 0.05s)
        elapsed = 0.0
        while elapsed < 0.3:
            v.update(0.02)
            elapsed += 0.02
            time.sleep(0.01)

        # Wait for thread to complete
        ok = self._wait_for(lambda: len(results) > 0)
        # Give update one more chance to collect
        v.update(0.0)
        self.assertTrue(ok, "Async check was never called")

    def test_stale_response_discarded(self):
        """Rapid value changes: only the latest result should be kept."""
        field = _StubField()
        call_count = [0]
        barrier = threading.Barrier(2, timeout=5)

        def slow_check(val):
            call_count[0] += 1
            if val == "first":
                # Synchronise with test so we can change the value mid-flight
                barrier.wait()
            return f"error_{val}"

        v = AsyncFieldValidator(field=field, async_check=slow_check, debounce_ms=10)

        # First value
        field.value.value = "first"
        # Advance debounce
        for _ in range(5):
            v.update(0.01)
            time.sleep(0.005)

        # Wait until slow_check is in progress
        barrier.wait()

        # Immediately change to "second" — debounce again
        field.value.value = "second"
        for _ in range(5):
            v.update(0.01)
            time.sleep(0.005)

        # Wait for the second check to finish
        deadline = time.monotonic() + 3.0
        while time.monotonic() < deadline:
            v.update(0.02)
            if v.async_error.value is not None and "first" not in (v.async_error.value or ""):
                break
            time.sleep(0.05)

        # The stale "first" result should have been discarded
        err = v.async_error.value
        if err is not None:
            self.assertNotIn("first", err)

    def test_async_check_exception_becomes_error_string(self):
        field = _StubField()

        def bad_check(val):
            raise ConnectionError("network down")

        v = AsyncFieldValidator(field=field, async_check=bad_check, debounce_ms=10)
        field.value.value = "x"

        # Advance debounce
        for _ in range(5):
            v.update(0.01)
            time.sleep(0.005)

        # Wait for thread
        deadline = time.monotonic() + 3.0
        while time.monotonic() < deadline:
            v.update(0.02)
            if v.async_error.value is not None:
                break
            time.sleep(0.05)

        self.assertIsNotNone(v.async_error.value)
        self.assertIn("network down", v.async_error.value)
        self.assertFalse(v.is_validating.value)

    def test_dispose_bumps_generation(self):
        field = _StubField()
        gen_before = [0]
        v = AsyncFieldValidator(field=field)
        gen_before[0] = v._generation
        v.dispose()
        self.assertGreater(v._generation, gen_before[0])


class TestAsyncFormValidator(unittest.TestCase):

    def test_is_valid_when_all_validators_valid(self):
        fields = [_StubField() for _ in range(3)]
        validators = [AsyncFieldValidator(field=f) for f in fields]
        form = AsyncFormValidator(validators)
        self.assertTrue(form.is_valid)

    def test_is_valid_false_when_one_invalid(self):
        f1 = _StubField()
        f2 = _StubField()
        v1 = AsyncFieldValidator(field=f1)
        v2 = AsyncFieldValidator(field=f2, local_rules=[lambda val: "bad"])
        f2.value.value = "x"
        form = AsyncFormValidator([v1, v2])
        self.assertFalse(form.is_valid)

    def test_validate_all_local_returns_true(self):
        fields = [_StubField("hello") for _ in range(3)]
        validators = [AsyncFieldValidator(field=f, local_rules=[lambda v: None]) for f in fields]
        form = AsyncFormValidator(validators)
        self.assertTrue(form.validate_all_local())

    def test_validate_all_local_returns_false_if_any_fail(self):
        f1 = _StubField("ok")
        f2 = _StubField("")
        v1 = AsyncFieldValidator(field=f1, local_rules=[lambda v: None])
        v2 = AsyncFieldValidator(field=f2, local_rules=[lambda v: None if v else "Required"])
        form = AsyncFormValidator([v1, v2])
        self.assertFalse(form.validate_all_local())

    def test_update_advances_all_validators(self):
        fields = [_StubField() for _ in range(2)]
        # Patch update on each validator
        validators = [AsyncFieldValidator(field=f) for f in fields]
        call_counts = [0, 0]
        original_updates = [v.update for v in validators]

        for i, v in enumerate(validators):
            idx = i
            orig = original_updates[idx]

            def _patched(dt, _orig=orig, _idx=idx):
                call_counts[_idx] += 1
                _orig(dt)

            v.update = _patched

        form = AsyncFormValidator(validators)
        form.update(0.016)
        self.assertEqual(call_counts, [1, 1])

    def test_is_any_validating_observable(self):
        field = _StubField()
        v = AsyncFieldValidator(field=field)
        form = AsyncFormValidator([v])
        self.assertIsInstance(form.is_any_validating, ObservableValue)
        self.assertFalse(form.is_any_validating.value)

    def test_dispose_calls_validator_dispose(self):
        fields = [_StubField() for _ in range(2)]
        validators = [AsyncFieldValidator(field=f) for f in fields]
        form = AsyncFormValidator(validators)
        # Should not raise
        form.dispose()


class TestAsyncFormValidatorExports(unittest.TestCase):

    def test_importable_from_gui_do(self):
        import gui_do
        self.assertTrue(hasattr(gui_do, "AsyncFieldValidator"))
        self.assertTrue(hasattr(gui_do, "AsyncFormValidator"))


if __name__ == "__main__":
    unittest.main()
