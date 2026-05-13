"""Tests for CooperativeScheduler, TransitionManager, LocaleRegistry/StringTable,
and NumericFormatter/PatternFormatter."""
import unittest

from gui_do.scheduling.cooperative_scheduler import (
    CooperativeScheduler,
    CoroutineHandle,
    Pause,
    Sleep,
    WaitUntil,
    WaitForAll,
    WaitForSignal,
)
from gui_do.scheduling.transition_manager import (
    TransitionManager,
    TransitionSpec,
    TransitionEvent,
)
from gui_do.scheduling.tween_manager import TweenManager
from gui_do.text.localization import StringTable, LocaleRegistry
from gui_do.text.text_formatter import NumericFormatter, PatternFormatter


# ===========================================================================
# CooperativeScheduler
# ===========================================================================


class TestCooperativeScheduler(unittest.TestCase):
    def test_simple_coroutine_runs_to_completion(self):
        steps = []

        def _gen():
            steps.append("a")
            yield Pause()
            steps.append("b")

        sched = CooperativeScheduler()
        h = sched.start(_gen())
        self.assertIn("a", steps)
        sched.update(0.016)
        self.assertIn("b", steps)
        self.assertTrue(h.is_complete)

    def test_start_returns_coroutine_handle(self):
        def _gen():
            yield Pause()

        sched = CooperativeScheduler()
        h = sched.start(_gen())
        self.assertIsInstance(h, CoroutineHandle)

    def test_handle_is_running_while_active(self):
        def _gen():
            yield Pause()
            yield Pause()

        sched = CooperativeScheduler()
        h = sched.start(_gen())
        self.assertTrue(h.is_running)

    def test_handle_is_complete_after_exhaustion(self):
        def _gen():
            return
            yield  # make it a generator

        sched = CooperativeScheduler()
        h = sched.start(_gen())
        self.assertTrue(h.is_complete)
        self.assertFalse(h.is_running)

    def test_cancel_stops_coroutine(self):
        steps = []

        def _gen():
            yield Pause()
            steps.append("should_not_reach")

        sched = CooperativeScheduler()
        h = sched.start(_gen())
        h.cancel()
        sched.update(0.016)
        self.assertTrue(h.is_cancelled)
        self.assertNotIn("should_not_reach", steps)

    def test_sleep_waits_required_time(self):
        steps = []

        def _gen():
            yield Sleep(0.5)
            steps.append("awake")

        sched = CooperativeScheduler()
        sched.start(_gen())
        sched.update(0.3)
        self.assertNotIn("awake", steps)
        sched.update(0.3)
        self.assertIn("awake", steps)

    def test_sleep_negative_raises(self):
        with self.assertRaises(ValueError):
            Sleep(-0.1)

    def test_wait_until_resumes_when_predicate_true(self):
        flag = [False]
        done = []

        def _gen():
            yield WaitUntil(lambda: flag[0])
            done.append(True)

        sched = CooperativeScheduler()
        sched.start(_gen())
        sched.update(0.016)
        self.assertEqual([], done)
        flag[0] = True
        sched.update(0.016)
        self.assertEqual([True], done)

    def test_wait_for_all_waits_until_all_complete(self):
        done = []

        def _child():
            yield Pause()
            yield Pause()

        def _parent(c1, c2):
            yield WaitForAll([c1, c2])
            done.append(True)

        sched = CooperativeScheduler()
        c1 = sched.start(_child())
        c2 = sched.start(_child())
        sched.start(_parent(c1, c2))

        sched.update(0.016)  # one Pause each
        self.assertEqual([], done)
        sched.update(0.016)  # children complete
        self.assertEqual([True], done)

    def test_coroutine_count_decrements_on_completion(self):
        def _gen():
            return
            yield

        sched = CooperativeScheduler()
        sched.start(_gen())
        # starts + completes before first update returns (runs to first yield in start())
        sched.update(0.016)
        self.assertEqual(0, sched.coroutine_count)

    def test_cancel_all_clears_all_coroutines(self):
        def _gen():
            yield Pause()
            yield Pause()

        sched = CooperativeScheduler()
        sched.start(_gen())
        sched.start(_gen())
        sched.cancel_all()
        self.assertEqual(0, sched.coroutine_count)

    def test_multiple_coroutines_run_concurrently(self):
        log = []

        def _a():
            log.append("a1")
            yield Pause()
            log.append("a2")

        def _b():
            log.append("b1")
            yield Pause()
            log.append("b2")

        sched = CooperativeScheduler()
        sched.start(_a())
        sched.start(_b())
        sched.update(0.016)
        self.assertIn("a2", log)
        self.assertIn("b2", log)

    def test_wait_for_signal_resumes_on_fire(self):
        # WaitForSignal requires a source with .subscribe(cb)->unsub contract.
        # ObservableValue satisfies that contract.
        from gui_do.data.presentation_model import ObservableValue

        ov = ObservableValue(0)
        done = []

        def _gen():
            yield WaitForSignal(ov)
            done.append(True)

        sched = CooperativeScheduler()
        sched.start(_gen())
        sched.update(0.016)
        self.assertEqual([], done)
        ov.value = 1  # triggers the observable → sets _wait_triggered
        sched.update(0.016)
        self.assertEqual([True], done)


# ===========================================================================
# TransitionManager
# ===========================================================================


class _Node:
    """Minimal stand-in for a GUI control node."""

    def __init__(self, alpha=1.0):
        self.alpha = alpha


class TestTransitionManager(unittest.TestCase):
    def _make(self):
        mgr = TweenManager()
        tm = TransitionManager(mgr)
        return mgr, tm

    def test_on_show_fires_registered_tween(self):
        mgr, tm = self._make()
        node = _Node(alpha=0.0)
        tm.register(node, TransitionEvent.SHOW,
                    TransitionSpec(attr="alpha", end_value=1.0, duration_seconds=0.0))
        tm.on_show(node)
        self.assertAlmostEqual(1.0, node.alpha)

    def test_on_hide_fires_registered_tween(self):
        mgr, tm = self._make()
        node = _Node(alpha=1.0)
        tm.register(node, TransitionEvent.HIDE,
                    TransitionSpec(attr="alpha", end_value=0.0, duration_seconds=0.0))
        tm.on_hide(node)
        self.assertAlmostEqual(0.0, node.alpha)

    def test_on_enable_fires_registered_tween(self):
        mgr, tm = self._make()
        node = _Node(alpha=0.3)
        tm.register(node, TransitionEvent.ENABLE,
                    TransitionSpec(attr="alpha", end_value=1.0, duration_seconds=0.0))
        tm.on_enable(node)
        self.assertAlmostEqual(1.0, node.alpha)

    def test_on_disable_fires_registered_tween(self):
        mgr, tm = self._make()
        node = _Node(alpha=1.0)
        tm.register(node, TransitionEvent.DISABLE,
                    TransitionSpec(attr="alpha", end_value=0.3, duration_seconds=0.0))
        tm.on_disable(node)
        self.assertAlmostEqual(0.3, node.alpha)

    def test_start_value_applied_before_tween(self):
        mgr, tm = self._make()
        node = _Node(alpha=0.5)
        tm.register(node, TransitionEvent.SHOW,
                    TransitionSpec(attr="alpha", end_value=1.0,
                                   duration_seconds=0.0, start_value=0.0))
        tm.on_show(node)
        # Zero-duration tween → immediately set to end_value=1.0
        self.assertAlmostEqual(1.0, node.alpha)

    def test_multiple_specs_for_same_event_all_fire(self):
        mgr, tm = self._make()

        class _MultiNode:
            alpha = 0.0
            scale = 0.0

        node = _MultiNode()
        tm.register(node, TransitionEvent.SHOW,
                    TransitionSpec(attr="alpha", end_value=1.0, duration_seconds=0.0))
        tm.register(node, TransitionEvent.SHOW,
                    TransitionSpec(attr="scale", end_value=2.0, duration_seconds=0.0))
        tm.on_show(node)
        self.assertAlmostEqual(1.0, node.alpha)
        self.assertAlmostEqual(2.0, node.scale)

    def test_unregister_removes_all_specs(self):
        mgr, tm = self._make()
        node = _Node(alpha=0.0)
        tm.register(node, TransitionEvent.SHOW,
                    TransitionSpec(attr="alpha", end_value=1.0, duration_seconds=0.0))
        tm.unregister(node)
        tm.on_show(node)
        self.assertAlmostEqual(0.0, node.alpha)  # unchanged

    def test_unregister_event_removes_specific_event(self):
        mgr, tm = self._make()
        node = _Node(alpha=0.0)
        tm.register(node, TransitionEvent.SHOW,
                    TransitionSpec(attr="alpha", end_value=1.0, duration_seconds=0.0))
        tm.register(node, TransitionEvent.HIDE,
                    TransitionSpec(attr="alpha", end_value=0.0, duration_seconds=0.0))
        tm.unregister_event(node, TransitionEvent.SHOW)
        tm.on_show(node)
        self.assertAlmostEqual(0.0, node.alpha)  # show was unregistered

    def test_on_done_callback_fires_on_zero_duration(self):
        mgr, tm = self._make()
        node = _Node()
        done = []
        tm.register(node, TransitionEvent.SHOW,
                    TransitionSpec(attr="alpha", end_value=1.0,
                                   duration_seconds=0.0, on_done=lambda: done.append(True)))
        tm.on_show(node)
        self.assertEqual([True], done)

    def test_firing_unregistered_node_is_noop(self):
        _, tm = self._make()
        node = _Node()
        # Should not raise
        tm.on_show(node)

    def test_string_event_coercion(self):
        mgr, tm = self._make()
        node = _Node(alpha=0.0)
        # register via string value
        tm.register(node, "show",
                    TransitionSpec(attr="alpha", end_value=1.0, duration_seconds=0.0))
        tm.on_show(node)
        self.assertAlmostEqual(1.0, node.alpha)


# ===========================================================================
# StringTable / LocaleRegistry
# ===========================================================================


class TestStringTable(unittest.TestCase):
    def setUp(self):
        self.t = StringTable("en", {"app.title": "My App", "btn.ok": "OK"})

    def test_locale_id_property(self):
        self.assertEqual("en", self.t.locale_id)

    def test_get_known_key(self):
        self.assertEqual("My App", self.t.get("app.title"))

    def test_get_unknown_returns_fallback(self):
        self.assertEqual("default", self.t.get("missing", "default"))

    def test_has_returns_true_for_known(self):
        self.assertTrue(self.t.has("btn.ok"))

    def test_has_returns_false_for_unknown(self):
        self.assertFalse(self.t.has("nope"))

    def test_keys_sorted(self):
        self.assertEqual(["app.title", "btn.ok"], self.t.keys())

    def test_len(self):
        self.assertEqual(2, len(self.t))

    def test_empty_locale_id_raises(self):
        with self.assertRaises(ValueError):
            StringTable("", {})

    def test_non_dict_entries_raises(self):
        with self.assertRaises(TypeError):
            StringTable("en", "bad")


class TestLocaleRegistry(unittest.TestCase):
    def setUp(self):
        self.reg = LocaleRegistry(default_locale="en", fallback_locale="en")
        self.reg.register(StringTable("en", {"btn.ok": "OK", "btn.cancel": "Cancel"}))
        self.reg.register(StringTable("es", {"btn.ok": "Aceptar"}))

    def test_t_returns_active_locale_value(self):
        self.assertEqual("OK", self.reg.t("btn.ok"))

    def test_t_falls_back_to_fallback_locale(self):
        self.reg.set_locale("es")
        # "btn.cancel" not in "es" — should fall back to "en"
        self.assertEqual("Cancel", self.reg.t("btn.cancel"))

    def test_t_returns_fallback_arg_when_missing_everywhere(self):
        self.assertEqual("--", self.reg.t("not.here", fallback="--"))

    def test_t_explicit_locale_override(self):
        self.assertEqual("Aceptar", self.reg.t("btn.ok", locale="es"))

    def test_set_locale_changes_active(self):
        self.reg.set_locale("es")
        self.assertEqual("es", self.reg.active_locale)
        self.assertEqual("Aceptar", self.reg.t("btn.ok"))

    def test_current_locale_observable_notifies(self):
        changes = []
        self.reg.current_locale.subscribe(changes.append)
        self.reg.set_locale("es")
        self.assertIn("es", changes)

    def test_registered_locales_sorted(self):
        self.assertEqual(["en", "es"], self.reg.registered_locales)

    def test_len_returns_locale_count(self):
        self.assertEqual(2, len(self.reg))

    def test_has_returns_true_for_existing_key(self):
        self.assertTrue(self.reg.has("btn.ok"))

    def test_has_returns_false_for_missing_key(self):
        self.assertFalse(self.reg.has("not.here"))

    def test_register_non_string_table_raises(self):
        with self.assertRaises(TypeError):
            self.reg.register("not_a_table")

    def test_register_replaces_existing_locale(self):
        self.reg.register(StringTable("en", {"btn.ok": "Yep"}))
        self.assertEqual("Yep", self.reg.t("btn.ok"))


# ===========================================================================
# NumericFormatter
# ===========================================================================


class TestNumericFormatter(unittest.TestCase):
    def test_format_integer(self):
        fmt = NumericFormatter(decimals=0)
        self.assertEqual("42", fmt.format("42"))

    def test_format_float_two_decimals(self):
        fmt = NumericFormatter(decimals=2)
        self.assertEqual("3.14", fmt.format("3.14159"))

    def test_format_with_thousands_sep(self):
        fmt = NumericFormatter(decimals=0, thousands_sep=",")
        self.assertEqual("1,000", fmt.format("1000"))

    def test_format_invalid_raw_returns_raw(self):
        fmt = NumericFormatter(decimals=0)
        self.assertEqual("abc", fmt.format("abc"))

    def test_parse_strips_thousands_sep(self):
        fmt = NumericFormatter(decimals=0, thousands_sep=",")
        self.assertEqual("1000", fmt.parse("1,000"))

    def test_parse_returns_integer_string(self):
        fmt = NumericFormatter(decimals=0)
        self.assertEqual("7", fmt.parse("7"))

    def test_validate_in_range(self):
        fmt = NumericFormatter(decimals=0, min_value=0, max_value=100)
        self.assertTrue(fmt.validate("50"))

    def test_validate_below_min_returns_false(self):
        fmt = NumericFormatter(decimals=0, min_value=10)
        self.assertFalse(fmt.validate("5"))

    def test_validate_above_max_returns_false(self):
        fmt = NumericFormatter(decimals=0, max_value=100)
        self.assertFalse(fmt.validate("200"))

    def test_validate_non_numeric_returns_false(self):
        fmt = NumericFormatter(decimals=0)
        self.assertFalse(fmt.validate("abc"))

    def test_validate_no_bounds_any_number(self):
        fmt = NumericFormatter(decimals=2)
        self.assertTrue(fmt.validate("999.99"))

    def test_adjust_cursor_moves_forward(self):
        fmt = NumericFormatter(decimals=0)
        self.assertEqual(3, fmt.adjust_cursor("42", 2, "x"))

    def test_negative_value_format(self):
        fmt = NumericFormatter(decimals=0)
        self.assertEqual("-5", fmt.format("-5"))


# ===========================================================================
# PatternFormatter
# ===========================================================================


class TestPatternFormatter(unittest.TestCase):
    def setUp(self):
        self.fmt = PatternFormatter("(###) ###-####")

    def test_slot_count(self):
        self.assertEqual(10, self.fmt.slot_count)

    def test_mask_property(self):
        self.assertEqual("(###) ###-####", self.fmt.mask)

    def test_format_full_digits(self):
        self.assertEqual("(123) 456-7890", self.fmt.format("1234567890"))

    def test_format_partial_digits_uses_fill(self):
        result = self.fmt.format("123")
        self.assertIn("1", result)
        self.assertIn("_", result)

    def test_parse_extracts_digits(self):
        self.assertEqual("1234567890", self.fmt.parse("(123) 456-7890"))

    def test_parse_ignores_literals(self):
        self.assertEqual("9876543210", self.fmt.parse("(987) 654-3210"))

    def test_validate_full_returns_true(self):
        self.assertTrue(self.fmt.validate("1234567890"))

    def test_validate_partial_returns_false(self):
        self.assertFalse(self.fmt.validate("123"))

    def test_format_partial_shows_only_entered_digits(self):
        result = self.fmt.format_partial("123")
        # Should not contain fill chars; only entered digits and mask literals
        self.assertNotIn("_", result)
        self.assertIn("1", result)

    def test_custom_fill_char(self):
        fmt = PatternFormatter("##-##", fill_char="*")
        self.assertEqual("12-**", fmt.format("12"))

    def test_adjust_cursor_returns_slot_position(self):
        pos = self.fmt.adjust_cursor("123", 3, "4")
        self.assertIsInstance(pos, int)
        self.assertGreater(pos, 0)


if __name__ == "__main__":
    unittest.main()
