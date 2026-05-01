"""Tests for InputBinding / InputMap and ChordStep / KeyChord."""
import unittest

from gui_do.actions.input_map import InputBinding, InputMap
from gui_do.actions.key_chord_manager import ChordStep, KeyChord


# ===========================================================================
# InputBinding dataclass
# ===========================================================================


class TestInputBinding(unittest.TestCase):
    def test_required_fields_stored(self):
        b = InputBinding(action="edit.copy", key=67)
        self.assertEqual("edit.copy", b.action)
        self.assertEqual(67, b.key)

    def test_defaults(self):
        b = InputBinding(action="edit.copy", key=67)
        self.assertEqual(0, b.mod)
        self.assertEqual("", b.label)
        self.assertTrue(b.is_default)

    def test_custom_values(self):
        b = InputBinding(action="a", key=65, mod=64, label="Act", is_default=False)
        self.assertEqual(64, b.mod)
        self.assertEqual("Act", b.label)
        self.assertFalse(b.is_default)


# ===========================================================================
# InputMap — initial state
# ===========================================================================


class TestInputMapInitial(unittest.TestCase):
    def test_bindings_empty(self):
        m = InputMap()
        self.assertEqual(0, len(m))

    def test_get_returns_none_for_unknown(self):
        m = InputMap()
        self.assertIsNone(m.binding_for("missing"))


# ===========================================================================
# InputMap.declare
# ===========================================================================


class TestInputMapDeclare(unittest.TestCase):
    def test_declare_creates_binding(self):
        m = InputMap()
        m.declare("edit.copy", key=67, mod=64, label="Copy")
        binding = m.binding_for("edit.copy")
        self.assertIsNotNone(binding)
        self.assertEqual(67, binding.key)

    def test_declare_marks_as_default(self):
        m = InputMap()
        m.declare("edit.copy", key=67)
        self.assertTrue(m.binding_for("edit.copy").is_default)

    def test_declare_second_call_ignored(self):
        m = InputMap()
        m.declare("edit.copy", key=67)
        m.declare("edit.copy", key=99)
        self.assertEqual(67, m.binding_for("edit.copy").key)

    def test_declare_empty_action_raises(self):
        m = InputMap()
        with self.assertRaises(ValueError):
            m.declare("", key=67)


# ===========================================================================
# InputMap.bind
# ===========================================================================


class TestInputMapBind(unittest.TestCase):
    def test_bind_creates_binding(self):
        m = InputMap()
        m.bind("edit.paste", key=86, mod=64)
        binding = m.binding_for("edit.paste")
        self.assertIsNotNone(binding)
        self.assertEqual(86, binding.key)

    def test_bind_marks_not_default(self):
        m = InputMap()
        m.declare("edit.copy", key=67)
        m.bind("edit.copy", key=99)
        self.assertFalse(m.binding_for("edit.copy").is_default)

    def test_bind_preserves_label(self):
        m = InputMap()
        m.declare("edit.copy", key=67, label="Copy")
        m.bind("edit.copy", key=99)
        self.assertEqual("Copy", m.binding_for("edit.copy").label)

    def test_bind_empty_action_raises(self):
        m = InputMap()
        with self.assertRaises(ValueError):
            m.bind("", key=67)


# ===========================================================================
# InputMap.unbind
# ===========================================================================


class TestInputMapUnbind(unittest.TestCase):
    def test_unbind_existing_returns_true(self):
        m = InputMap()
        m.declare("edit.copy", key=67)
        self.assertTrue(m.unbind("edit.copy"))

    def test_unbind_removes_binding(self):
        m = InputMap()
        m.declare("edit.copy", key=67)
        m.unbind("edit.copy")
        self.assertIsNone(m.binding_for("edit.copy"))

    def test_unbind_missing_returns_false(self):
        m = InputMap()
        self.assertFalse(m.unbind("not.registered"))


# ===========================================================================
# InputMap.reset_to_default
# ===========================================================================


class TestInputMapResetToDefault(unittest.TestCase):
    def test_reset_not_needed_returns_false(self):
        m = InputMap()
        m.declare("edit.copy", key=67)
        self.assertFalse(m.reset_to_default("edit.copy"))

    def test_reset_overridden_returns_true(self):
        m = InputMap()
        m.declare("edit.copy", key=67)
        m.bind("edit.copy", key=99)
        self.assertTrue(m.reset_to_default("edit.copy"))

    def test_reset_restores_is_default_flag(self):
        m = InputMap()
        m.declare("edit.copy", key=67)
        m.bind("edit.copy", key=99)
        m.reset_to_default("edit.copy")
        self.assertTrue(m.binding_for("edit.copy").is_default)

    def test_reset_unknown_returns_false(self):
        m = InputMap()
        self.assertFalse(m.reset_to_default("not.here"))


# ===========================================================================
# ChordStep dataclass
# ===========================================================================


class TestChordStep(unittest.TestCase):
    def test_key_stored(self):
        step = ChordStep(key=75)
        self.assertEqual(75, step.key)

    def test_mod_default_zero(self):
        step = ChordStep(key=75)
        self.assertEqual(0, step.mod)

    def test_custom_mod(self):
        step = ChordStep(key=75, mod=64)
        self.assertEqual(64, step.mod)

    def test_is_frozen(self):
        step = ChordStep(key=75)
        with self.assertRaises(Exception):
            step.key = 99  # type: ignore[misc]


# ===========================================================================
# KeyChord
# ===========================================================================


class TestKeyChord(unittest.TestCase):
    def test_single_step(self):
        chord = KeyChord([ChordStep(key=75)])
        self.assertEqual(1, len(chord))

    def test_two_steps(self):
        chord = KeyChord([ChordStep(key=75), ChordStep(key=67)])
        self.assertEqual(2, len(chord))

    def test_indexing(self):
        steps = [ChordStep(key=75), ChordStep(key=67)]
        chord = KeyChord(steps)
        self.assertEqual(75, chord[0].key)
        self.assertEqual(67, chord[1].key)

    def test_empty_steps_raises(self):
        with self.assertRaises(ValueError):
            KeyChord([])

    def test_is_frozen(self):
        chord = KeyChord([ChordStep(key=75)])
        with self.assertRaises(Exception):
            chord.steps = ()  # type: ignore[misc]

    def test_steps_stored_as_tuple(self):
        chord = KeyChord([ChordStep(key=75)])
        self.assertIsInstance(chord.steps, tuple)


if __name__ == "__main__":
    unittest.main()
