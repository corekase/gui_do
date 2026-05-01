"""Tests for WizardFlow, WizardStep, and WizardHandle from forms.wizard_flow."""
import unittest

from gui_do.forms.wizard_flow import WizardFlow, WizardStep, WizardHandle


# ===========================================================================
# WizardStep dataclass
# ===========================================================================


class TestWizardStep(unittest.TestCase):
    def test_title_stored(self):
        s = WizardStep(title="Name")
        self.assertEqual("Name", s.title)

    def test_defaults(self):
        s = WizardStep(title="x")
        self.assertEqual([], s.fields)
        self.assertIsNone(s.on_validate)
        self.assertIsNone(s.on_enter)
        self.assertIsNone(s.on_leave)

    def test_custom_fields(self):
        s = WizardStep(title="Step", fields=["name", "email"])
        self.assertEqual(["name", "email"], s.fields)


# ===========================================================================
# WizardFlow — initial state
# ===========================================================================


class TestWizardFlowInitial(unittest.TestCase):
    def _make(self, on_complete=None):
        steps = [WizardStep("A"), WizardStep("B"), WizardStep("C")]
        return WizardFlow(steps, on_complete=on_complete or (lambda d: None))

    def test_empty_steps_raises(self):
        with self.assertRaises(ValueError):
            WizardFlow([], on_complete=lambda d: None)

    def test_step_index_zero(self):
        wf = self._make()
        self.assertEqual(0, wf.step_index)

    def test_current_step_is_first(self):
        wf = self._make()
        self.assertEqual("A", wf.current_step.title)

    def test_progress_zero(self):
        wf = self._make()
        self.assertEqual(0.0, wf.progress.value)

    def test_step_count(self):
        wf = self._make()
        self.assertEqual(3, wf.step_count)


# ===========================================================================
# WizardFlow — advance
# ===========================================================================


class TestWizardFlowAdvance(unittest.TestCase):
    def test_advance_returns_true(self):
        wf = WizardFlow([WizardStep("A"), WizardStep("B")], on_complete=lambda d: None)
        ok, errors = wf.advance({})
        self.assertTrue(ok)
        self.assertEqual([], errors)

    def test_advance_moves_to_next_step(self):
        wf = WizardFlow([WizardStep("A"), WizardStep("B")], on_complete=lambda d: None)
        wf.advance({})
        self.assertEqual(1, wf.step_index)

    def test_advance_with_data_collected(self):
        done = {}
        wf = WizardFlow([WizardStep("Only")], on_complete=lambda d: done.update(d))
        wf.advance({"name": "Alice"})
        self.assertEqual("Alice", done.get("name"))

    def test_validation_failure_blocks_advance(self):
        step = WizardStep("A", on_validate=lambda d: ["Required"])
        wf = WizardFlow([step, WizardStep("B")], on_complete=lambda d: None)
        ok, errors = wf.advance({})
        self.assertFalse(ok)
        self.assertIn("Required", errors)
        self.assertEqual(0, wf.step_index)

    def test_validation_pass_advances(self):
        step = WizardStep("A", on_validate=lambda d: [] if d.get("x") else ["Missing"])
        wf = WizardFlow([step, WizardStep("B")], on_complete=lambda d: None)
        ok, errors = wf.advance({"x": 1})
        self.assertTrue(ok)
        self.assertEqual(1, wf.step_index)

    def test_last_step_calls_on_complete(self):
        done = [False]
        wf = WizardFlow([WizardStep("Only")], on_complete=lambda d: done.__setitem__(0, True))
        wf.advance({})
        self.assertTrue(done[0])

    def test_progress_updated_after_advance(self):
        wf = WizardFlow([WizardStep("A"), WizardStep("B")], on_complete=lambda d: None)
        wf.advance({})
        self.assertGreater(wf.progress.value, 0.0)


# ===========================================================================
# WizardFlow — back
# ===========================================================================


class TestWizardFlowBack(unittest.TestCase):
    def test_back_from_first_returns_false(self):
        wf = WizardFlow([WizardStep("A"), WizardStep("B")], on_complete=lambda d: None)
        self.assertFalse(wf.back())

    def test_back_moves_to_previous_step(self):
        wf = WizardFlow([WizardStep("A"), WizardStep("B")], on_complete=lambda d: None)
        wf.advance({})
        wf.back()
        self.assertEqual(0, wf.step_index)

    def test_back_returns_true(self):
        wf = WizardFlow([WizardStep("A"), WizardStep("B")], on_complete=lambda d: None)
        wf.advance({})
        self.assertTrue(wf.back())


# ===========================================================================
# WizardFlow — cancel
# ===========================================================================


class TestWizardFlowCancel(unittest.TestCase):
    def test_cancel_calls_on_cancel(self):
        cancelled = [False]
        wf = WizardFlow(
            [WizardStep("A")],
            on_complete=lambda d: None,
            on_cancel=lambda: cancelled.__setitem__(0, True),
        )
        wf.cancel()
        self.assertTrue(cancelled[0])


# ===========================================================================
# WizardHandle
# ===========================================================================


class TestWizardHandle(unittest.TestCase):
    def test_not_cancelled_initially(self):
        wf = WizardFlow([WizardStep("A")], on_complete=lambda d: None)
        handle = WizardHandle(wf)
        self.assertFalse(handle.is_cancelled)

    def test_cancel_sets_cancelled(self):
        wf = WizardFlow([WizardStep("A")], on_complete=lambda d: None)
        handle = WizardHandle(wf)
        handle.cancel()
        self.assertTrue(handle.is_cancelled)

    def test_cancel_idempotent(self):
        calls = [0]
        wf = WizardFlow(
            [WizardStep("A")],
            on_complete=lambda d: None,
            on_cancel=lambda: calls.__setitem__(0, calls[0] + 1),
        )
        handle = WizardHandle(wf)
        handle.cancel()
        handle.cancel()
        self.assertEqual(1, calls[0])


if __name__ == "__main__":
    unittest.main()
