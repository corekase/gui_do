"""Tests for TabPanelManager from feature_lifecycle."""
import unittest

from gui_do.features.feature_lifecycle import TabPanelManager


class _MockControl:
    def __init__(self, name):
        self.name = name
        self.visible = True


class _MockDirtyControl(_MockControl):
    def __init__(self, name):
        super().__init__(name)
        self.clear_dirty_calls = 0

    def clear_dirty(self):
        self.clear_dirty_calls += 1


# ===========================================================================
# TabPanelManager — initial state
# ===========================================================================


class TestTabPanelManagerInitial(unittest.TestCase):
    def test_active_key_none(self):
        mgr = TabPanelManager()
        self.assertIsNone(mgr.active_key)

    def test_keys_empty(self):
        mgr = TabPanelManager()
        self.assertEqual([], mgr.keys())

    def test_controls_for_unknown(self):
        mgr = TabPanelManager()
        self.assertEqual([], mgr.controls_for("missing"))


# ===========================================================================
# TabPanelManager.register
# ===========================================================================


class TestTabPanelManagerRegister(unittest.TestCase):
    def test_register_hides_controls(self):
        mgr = TabPanelManager()
        ctrl = _MockControl("a")
        ctrl.visible = True
        mgr.register("tab1", [ctrl])
        self.assertFalse(ctrl.visible)

    def test_register_stores_controls(self):
        mgr = TabPanelManager()
        ctrl = _MockControl("a")
        mgr.register("tab1", [ctrl])
        self.assertIn(ctrl, mgr.controls_for("tab1"))

    def test_register_adds_key(self):
        mgr = TabPanelManager()
        mgr.register("tab2", [])
        self.assertIn("tab2", mgr.keys())

    def test_register_single_control_as_iterable(self):
        mgr = TabPanelManager()
        ctrl = _MockControl("x")
        mgr.register("t", [ctrl])
        self.assertEqual([ctrl], mgr.controls_for("t"))

    def test_register_after_activate_keeps_active_panel_visible(self):
        mgr = TabPanelManager()
        mgr.activate("tab1")
        ctrl = _MockControl("a")
        mgr.register("tab1", [ctrl])
        self.assertTrue(ctrl.visible)


# ===========================================================================
# TabPanelManager.activate
# ===========================================================================


class TestTabPanelManagerActivate(unittest.TestCase):
    def test_activate_shows_correct_tab(self):
        mgr = TabPanelManager()
        a = _MockControl("a")
        b = _MockControl("b")
        mgr.register("tab1", [a])
        mgr.register("tab2", [b])
        mgr.activate("tab1")
        self.assertTrue(a.visible)
        self.assertFalse(b.visible)

    def test_activate_hides_other_tabs(self):
        mgr = TabPanelManager()
        a = _MockControl("a")
        b = _MockControl("b")
        mgr.register("tab1", [a])
        mgr.register("tab2", [b])
        mgr.activate("tab2")
        self.assertFalse(a.visible)
        self.assertTrue(b.visible)

    def test_activate_sets_active_key(self):
        mgr = TabPanelManager()
        mgr.register("tab1", [])
        mgr.activate("tab1")
        self.assertEqual("tab1", mgr.active_key)

    def test_activate_fires_callback(self):
        mgr = TabPanelManager()
        mgr.register("tab1", [])
        called = []
        mgr.on_activate("tab1", lambda: called.append(1))
        mgr.activate("tab1")
        self.assertEqual([1], called)

    def test_activate_does_not_fire_other_callbacks(self):
        mgr = TabPanelManager()
        mgr.register("tab1", [])
        mgr.register("tab2", [])
        called = []
        mgr.on_activate("tab2", lambda: called.append(2))
        mgr.activate("tab1")
        self.assertEqual([], called)

    def test_multiple_callbacks_all_fired(self):
        mgr = TabPanelManager()
        mgr.register("tab1", [])
        called = []
        mgr.on_activate("tab1", lambda: called.append("a"))
        mgr.on_activate("tab1", lambda: called.append("b"))
        mgr.activate("tab1")
        self.assertEqual(["a", "b"], called)

    def test_activate_coerces_key_to_string(self):
        mgr = TabPanelManager()
        ctrl = _MockControl("a")
        mgr.register("1", [ctrl])
        mgr.activate(1)
        self.assertEqual("1", mgr.active_key)
        self.assertTrue(ctrl.visible)

    def test_activate_does_not_clear_dirty_state_on_show(self):
        mgr = TabPanelManager()
        ctrl = _MockDirtyControl("a")
        mgr.register("tab1", [ctrl])
        mgr.activate("tab1")
        self.assertEqual(0, ctrl.clear_dirty_calls)

    def test_activate_unknown_key_keeps_existing_visibility(self):
        mgr = TabPanelManager()
        a = _MockControl("a")
        b = _MockControl("b")
        mgr.register("tab1", [a])
        mgr.register("tab2", [b])
        mgr.activate("tab1")

        mgr.activate("missing")

        self.assertEqual("tab1", mgr.active_key)
        self.assertTrue(a.visible)
        self.assertFalse(b.visible)


# ===========================================================================
# TabPanelManager.append_to / remove_from
# ===========================================================================


class TestTabPanelManagerAppendRemove(unittest.TestCase):
    def test_append_to_existing(self):
        mgr = TabPanelManager()
        a = _MockControl("a")
        mgr.register("tab1", [a])
        mgr.activate("tab1")
        b = _MockControl("b")
        mgr.append_to("tab1", b)
        self.assertIn(b, mgr.controls_for("tab1"))

    def test_append_to_active_makes_visible(self):
        mgr = TabPanelManager()
        mgr.register("tab1", [])
        mgr.activate("tab1")
        ctrl = _MockControl("x")
        ctrl.visible = False
        mgr.append_to("tab1", ctrl)
        self.assertTrue(ctrl.visible)

    def test_append_to_inactive_stays_hidden(self):
        mgr = TabPanelManager()
        mgr.register("tab1", [])
        mgr.register("tab2", [])
        mgr.activate("tab2")
        ctrl = _MockControl("x")
        ctrl.visible = True
        mgr.append_to("tab1", ctrl)
        self.assertFalse(ctrl.visible)

    def test_remove_from_panel(self):
        mgr = TabPanelManager()
        ctrl = _MockControl("c")
        mgr.register("tab1", [ctrl])
        mgr.remove_from("tab1", ctrl)
        self.assertNotIn(ctrl, mgr.controls_for("tab1"))

    def test_remove_from_hides_control(self):
        mgr = TabPanelManager()
        ctrl = _MockControl("c")
        mgr.register("tab1", [ctrl])
        mgr.activate("tab1")
        mgr.remove_from("tab1", ctrl)
        self.assertFalse(ctrl.visible)


if __name__ == "__main__":
    unittest.main()
