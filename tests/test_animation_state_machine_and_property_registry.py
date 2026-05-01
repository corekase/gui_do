"""Tests for AnimationStateMachine, PropertyRegistry/ui_property, PropertyInspectorModel."""
import unittest

from gui_do.scheduling.animation_state_machine import (
    AnimationStateMachine,
    AnimationTransitionMode,
)
from gui_do.scheduling.tween_manager import TweenManager
from gui_do.introspection.property_registry import (
    PropertyDescriptor,
    PropertyRegistry,
    ui_property,
)
from gui_do.introspection.property_inspector import PropertyInspectorModel


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class _FakeTarget:
    """Plain object whose attributes can be tweened."""
    x: float = 0.0
    y: float = 0.0


def _empty_builder(seq) -> None:
    """Builder with no steps — sequence completes synchronously on start."""
    pass


def _x_builder(tweens_target, duration: float = 0.5):
    """Return a builder that animates target.x to 1.0 (non-empty → async)."""
    def _builder(seq) -> None:
        seq.then(
            target=tweens_target,
            attr="x",
            end_value=1.0,
            duration_seconds=duration,
        )
    return _builder


# ===========================================================================
# AnimationStateMachine
# ===========================================================================


class TestAnimationStateMachine(unittest.TestCase):
    def setUp(self):
        self.tweens = TweenManager()
        self.asm = AnimationStateMachine(self.tweens)

    # ------------------------------------------------------------------
    # Construction and registration
    # ------------------------------------------------------------------

    def test_current_state_none_by_default(self):
        self.assertIsNone(self.asm.current_state)

    def test_initial_state_constructor(self):
        asm = AnimationStateMachine(self.tweens, initial_state="idle")
        self.assertEqual("idle", asm.current_state)

    def test_register_and_set_state(self):
        self.asm.register_state("active", _empty_builder)
        self.asm.set_state("active")
        self.assertEqual("active", self.asm.current_state)

    def test_unknown_state_raises_key_error(self):
        with self.assertRaises(KeyError):
            self.asm.set_state("nonexistent")

    def test_set_same_state_is_noop(self):
        self.asm.register_state("idle", _empty_builder)
        self.asm.set_state("idle")
        events = []
        self.asm.on_state_changed(events.append)
        self.asm.set_state("idle")   # same state — no callback
        self.assertEqual([], events)

    # ------------------------------------------------------------------
    # State changed callbacks
    # ------------------------------------------------------------------

    def test_on_state_changed_fires(self):
        events = []
        self.asm.on_state_changed(events.append)
        self.asm.register_state("hover", _empty_builder)
        self.asm.set_state("hover")
        self.assertIn("hover", events)

    def test_on_state_changed_multiple_callbacks(self):
        a, b = [], []
        self.asm.on_state_changed(a.append)
        self.asm.on_state_changed(b.append)
        self.asm.register_state("press", _empty_builder)
        self.asm.set_state("press")
        self.assertIn("press", a)
        self.assertIn("press", b)

    def test_on_state_changed_unsub_stops_events(self):
        events = []
        unsub = self.asm.on_state_changed(events.append)
        unsub()
        self.asm.register_state("s", _empty_builder)
        self.asm.set_state("s")
        self.assertEqual([], events)

    # ------------------------------------------------------------------
    # Transitioning / in-flight detection
    # ------------------------------------------------------------------

    def test_handle_assigned_after_synchronous_empty_sequence(self):
        """Empty builder fires _done_callback before _current_handle is assigned.
        The handle is then set after _on_sequence_done() ran; it is not cancelled."""
        self.asm.register_state("idle", _empty_builder)
        self.asm.set_state("idle")
        # _on_sequence_done ran (synchronously) before the assignment;
        # _current_handle is the returned handle — not None, not cancelled.
        self.assertTrue(self.asm.is_transitioning())

    def test_is_transitioning_true_with_running_tween(self):
        target = _FakeTarget()
        self.asm.register_state("run", _x_builder(target, 1.0))
        self.asm.set_state("run")
        self.assertTrue(self.asm.is_transitioning())

    def test_is_transitioning_false_after_tween_completes(self):
        target = _FakeTarget()
        self.asm.register_state("run", _x_builder(target, 0.5))
        self.asm.set_state("run")
        self.tweens.update(0.6)  # advance past end
        self.assertFalse(self.asm.is_transitioning())

    # ------------------------------------------------------------------
    # reset
    # ------------------------------------------------------------------

    def test_reset_clears_current_state(self):
        self.asm.register_state("a", _empty_builder)
        self.asm.set_state("a")
        self.asm.reset()
        self.assertIsNone(self.asm.current_state)

    def test_reset_cancels_in_flight_tween(self):
        target = _FakeTarget()
        self.asm.register_state("run", _x_builder(target, 1.0))
        self.asm.set_state("run")
        self.assertTrue(self.asm.is_transitioning())
        self.asm.reset()
        self.assertFalse(self.asm.is_transitioning())

    # ------------------------------------------------------------------
    # Transition modes
    # ------------------------------------------------------------------

    def test_interrupt_mode_switches_immediately(self):
        target = _FakeTarget()
        self.asm.register_state("a", _x_builder(target, 2.0))
        self.asm.register_state("b", _empty_builder)
        self.asm.set_state("a")
        self.assertEqual("a", self.asm.current_state)
        self.asm.set_state("b")   # INTERRUPT is default
        self.assertEqual("b", self.asm.current_state)

    def test_complete_then_transition_queues_state(self):
        target = _FakeTarget()
        self.asm.register_state("a", _x_builder(target, 0.5))
        self.asm.register_state("b", _empty_builder)
        self.asm.register_transition("a", "b", mode=AnimationTransitionMode.COMPLETE_THEN_TRANSITION)

        self.asm.set_state("a")
        self.assertEqual("a", self.asm.current_state)

        # Request "b" while "a" is still running — should be queued, not applied yet
        self.asm.set_state("b")
        self.assertEqual("a", self.asm.current_state)

    def test_complete_then_transition_applied_after_tween_done(self):
        target = _FakeTarget()
        self.asm.register_state("a", _x_builder(target, 0.5))
        self.asm.register_state("b", _empty_builder)
        self.asm.register_transition("a", "b", mode=AnimationTransitionMode.COMPLETE_THEN_TRANSITION)

        self.asm.set_state("a")
        self.asm.set_state("b")           # queued
        self.tweens.update(0.6)           # "a" tween completes → "b" starts
        self.assertEqual("b", self.asm.current_state)

    def test_wildcard_transition_mode(self):
        target = _FakeTarget()
        self.asm.register_state("x", _x_builder(target, 1.0))
        self.asm.register_state("y", _empty_builder)
        # wildcard: any state → "y" uses COMPLETE_THEN_TRANSITION
        self.asm.register_transition("*", "y", mode=AnimationTransitionMode.COMPLETE_THEN_TRANSITION)

        self.asm.set_state("x")
        self.asm.set_state("y")           # queued via wildcard rule
        self.assertEqual("x", self.asm.current_state)
        self.tweens.update(1.1)
        self.assertEqual("y", self.asm.current_state)

    def test_reverse_then_transition_falls_back_to_interrupt(self):
        target = _FakeTarget()
        self.asm.register_state("a", _x_builder(target, 2.0))
        self.asm.register_state("b", _empty_builder)
        self.asm.register_transition("a", "b", mode=AnimationTransitionMode.REVERSE_THEN_TRANSITION)

        self.asm.set_state("a")
        self.asm.set_state("b")
        # REVERSE falls back to interrupt — "b" should already be active
        self.assertEqual("b", self.asm.current_state)

    # ------------------------------------------------------------------
    # Multiple sequential transitions
    # ------------------------------------------------------------------

    def test_multiple_transitions_between_states(self):
        events = []
        self.asm.on_state_changed(events.append)
        for state in ("idle", "hover", "press", "idle"):
            self.asm.register_state(state, _empty_builder)
        self.asm.set_state("idle")
        self.asm.set_state("hover")
        self.asm.set_state("press")
        self.asm.set_state("idle")
        self.assertEqual(["idle", "hover", "press", "idle"], events)


# ===========================================================================
# PropertyRegistry + ui_property
# ===========================================================================


class _WidgetA:
    def __init__(self):
        self._alpha = 1.0
        self._label = "hello"

    @property
    @ui_property(label="Opacity", type="float", min=0.0, max=1.0, group="Appearance")
    def alpha(self) -> float:
        return self._alpha

    @alpha.setter
    def alpha(self, v: float) -> None:
        self._alpha = float(v)

    @property
    @ui_property(label="Label", type="str", group="Content", read_only=True)
    def label(self) -> str:
        return self._label


class _WidgetB(_WidgetA):
    """Subclass inherits descriptors from _WidgetA."""

    def __init__(self):
        super().__init__()
        self._count = 0

    @property
    @ui_property(label="Count", type="int", min=0, max=100, group="Data")
    def count(self) -> int:
        return self._count

    @count.setter
    def count(self, v: int) -> None:
        self._count = int(v)


class TestPropertyRegistry(unittest.TestCase):
    def setUp(self):
        self.reg = PropertyRegistry()

    def test_descriptors_for_class(self):
        descs = self.reg.descriptors_for(_WidgetA)
        names = [d.name for d in descs]
        self.assertIn("alpha", names)
        self.assertIn("label", names)

    def test_descriptors_for_instance(self):
        obj = _WidgetA()
        descs = self.reg.descriptors_for(obj)
        names = [d.name for d in descs]
        self.assertIn("alpha", names)

    def test_descriptor_label(self):
        descs = self.reg.descriptors_for(_WidgetA)
        alpha = next(d for d in descs if d.name == "alpha")
        self.assertEqual("Opacity", alpha.label)

    def test_descriptor_type(self):
        descs = self.reg.descriptors_for(_WidgetA)
        alpha = next(d for d in descs if d.name == "alpha")
        self.assertEqual("float", alpha.type)

    def test_descriptor_min_max(self):
        descs = self.reg.descriptors_for(_WidgetA)
        alpha = next(d for d in descs if d.name == "alpha")
        self.assertEqual(0.0, alpha.min)
        self.assertEqual(1.0, alpha.max)

    def test_descriptor_group(self):
        descs = self.reg.descriptors_for(_WidgetA)
        alpha = next(d for d in descs if d.name == "alpha")
        self.assertEqual("Appearance", alpha.group)

    def test_descriptor_read_only(self):
        descs = self.reg.descriptors_for(_WidgetA)
        label_d = next(d for d in descs if d.name == "label")
        self.assertTrue(label_d.read_only)

    def test_subclass_inherits_base_descriptors(self):
        descs = self.reg.descriptors_for(_WidgetB)
        names = [d.name for d in descs]
        self.assertIn("alpha", names)
        self.assertIn("label", names)
        self.assertIn("count", names)

    def test_subclass_own_descriptor_metadata(self):
        descs = self.reg.descriptors_for(_WidgetB)
        count_d = next(d for d in descs if d.name == "count")
        self.assertEqual("int", count_d.type)
        self.assertEqual(100, count_d.max)

    def test_manual_register(self):
        reg = PropertyRegistry()
        d = PropertyDescriptor(name="custom", label="Custom Prop", type="str")
        reg.register(_WidgetA, d)
        descs = reg.descriptors_for(_WidgetA)
        names = [x.name for x in descs]
        self.assertIn("custom", names)

    def test_all_classes_includes_registered(self):
        reg = PropertyRegistry()
        d = PropertyDescriptor(name="p", label="P")
        reg.register(_WidgetA, d)
        self.assertIn(_WidgetA, reg.all_classes())

    def test_caching_returns_consistent_results(self):
        descs1 = self.reg.descriptors_for(_WidgetA)
        descs2 = self.reg.descriptors_for(_WidgetA)
        names1 = {d.name for d in descs1}
        names2 = {d.name for d in descs2}
        self.assertEqual(names1, names2)


# ===========================================================================
# PropertyInspectorModel
# ===========================================================================


class TestPropertyInspectorModel(unittest.TestCase):
    def setUp(self):
        self.obj = _WidgetA()
        self.model = PropertyInspectorModel(self.obj)

    def test_target_property(self):
        self.assertIs(self.obj, self.model.target)

    def test_properties_returns_list(self):
        props = self.model.properties()
        self.assertIsInstance(props, list)
        self.assertTrue(len(props) >= 2)

    def test_properties_names(self):
        names = [p.descriptor.name for p in self.model.properties()]
        self.assertIn("alpha", names)
        self.assertIn("label", names)

    def test_properties_values_reflect_object(self):
        self.obj._alpha = 0.5
        props = self.model.properties()
        alpha_p = next(p for p in props if p.descriptor.name == "alpha")
        self.assertAlmostEqual(0.5, alpha_p.value)

    def test_grouped_organizes_by_group(self):
        grouped = self.model.grouped()
        self.assertIn("Appearance", grouped)
        self.assertIn("Content", grouped)

    def test_get_value_returns_attribute(self):
        self.obj._alpha = 0.75
        self.assertAlmostEqual(0.75, self.model.get_value("alpha"))

    def test_set_value_updates_attribute(self):
        self.model.set_value("alpha", 0.3)
        self.assertAlmostEqual(0.3, self.obj.alpha)

    def test_set_value_coerces_float(self):
        self.model.set_value("alpha", "0.6")
        self.assertAlmostEqual(0.6, self.obj.alpha)

    def test_set_value_clamps_to_max(self):
        self.model.set_value("alpha", 9999.0)
        self.assertLessEqual(self.obj.alpha, 1.0)

    def test_set_value_clamps_to_min(self):
        self.model.set_value("alpha", -5.0)
        self.assertGreaterEqual(self.obj.alpha, 0.0)

    def test_set_value_read_only_raises(self):
        with self.assertRaises(ValueError):
            self.model.set_value("label", "new")

    def test_get_value_unknown_property_raises(self):
        with self.assertRaises(AttributeError):
            self.model.get_value("does_not_exist")

    def test_set_value_int_coercion(self):
        obj = _WidgetB()
        model = PropertyInspectorModel(obj)
        model.set_value("count", "7")
        self.assertEqual(7, obj.count)


if __name__ == "__main__":
    unittest.main()
