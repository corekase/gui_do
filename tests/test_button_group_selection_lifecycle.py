import unittest

from pygame import Rect

from gui_do.controls.button_group_control import ButtonGroupControl
from gui_do.controls.panel_control import PanelControl


class ButtonGroupSelectionLifecycleTests(unittest.TestCase):
    def setUp(self) -> None:
        ButtonGroupControl._selection_by_group.clear()

    def tearDown(self) -> None:
        ButtonGroupControl._selection_by_group.clear()

    def test_removing_selected_button_promotes_remaining_peer(self) -> None:
        panel = PanelControl("panel", Rect(0, 0, 200, 100))
        selected = panel.add(ButtonGroupControl("a", Rect(0, 0, 40, 20), group="g", text="A", selected=True))
        peer = panel.add(ButtonGroupControl("b", Rect(50, 0, 40, 20), group="g", text="B", selected=False))

        removed = panel.remove(selected)

        self.assertTrue(removed)
        self.assertEqual(peer.button_id, "b")
        self.assertIn("g", ButtonGroupControl._selection_by_group)
        self.assertEqual(ButtonGroupControl._selection_by_group.get("g"), "b")
        self.assertTrue(peer.pushed)

    def test_removing_non_selected_button_keeps_selected_mapping(self) -> None:
        panel = PanelControl("panel", Rect(0, 0, 200, 100))
        selected = panel.add(ButtonGroupControl("a", Rect(0, 0, 40, 20), group="g", text="A", selected=True))
        other = panel.add(ButtonGroupControl("b", Rect(50, 0, 40, 20), group="g", text="B", selected=False))

        removed = panel.remove(other)

        self.assertTrue(removed)
        self.assertEqual(selected.button_id, "a")
        self.assertEqual(ButtonGroupControl._selection_by_group.get("g"), "a")

    def test_first_added_button_auto_selects_when_group_has_no_explicit_selected(self) -> None:
        panel = PanelControl("panel", Rect(0, 0, 200, 100))
        first = panel.add(ButtonGroupControl("a", Rect(0, 0, 40, 20), group="g", text="A", selected=False))
        second = panel.add(ButtonGroupControl("b", Rect(50, 0, 40, 20), group="g", text="B", selected=False))

        self.assertTrue(first.pushed)
        self.assertFalse(second.pushed)
        self.assertEqual(ButtonGroupControl._selection_by_group.get("g"), "a")

    def test_stale_group_mapping_does_not_block_first_added_auto_selection(self) -> None:
        ButtonGroupControl._selection_by_group["g"] = "stale-id"
        panel = PanelControl("panel", Rect(0, 0, 200, 100))

        first = panel.add(ButtonGroupControl("a", Rect(0, 0, 40, 20), group="g", text="A", selected=False))
        second = panel.add(ButtonGroupControl("b", Rect(50, 0, 40, 20), group="g", text="B", selected=False))

        self.assertTrue(first.pushed)
        self.assertFalse(second.pushed)
        self.assertEqual(ButtonGroupControl._selection_by_group.get("g"), "a")


    # ------------------------------------------------------------------
    # Creation-time (init-level) auto-arm behaviour
    # ------------------------------------------------------------------

    def test_first_created_button_is_armed_at_init_time(self) -> None:
        first = ButtonGroupControl("a", Rect(0, 0, 40, 20), group="g", text="A", selected=False)

        self.assertTrue(first.pushed)
        self.assertEqual(ButtonGroupControl._selection_by_group.get("g"), "a")

    def test_second_created_button_does_not_displace_armed_state(self) -> None:
        first = ButtonGroupControl("a", Rect(0, 0, 40, 20), group="g", text="A", selected=False)
        second = ButtonGroupControl("b", Rect(50, 0, 40, 20), group="g", text="B", selected=False)

        self.assertTrue(first.pushed)
        self.assertFalse(second.pushed)
        self.assertEqual(ButtonGroupControl._selection_by_group.get("g"), "a")

    def test_multiple_groups_each_arm_their_first_button(self) -> None:
        a1 = ButtonGroupControl("a1", Rect(0, 0, 40, 20), group="alpha", text="A1", selected=False)
        b1 = ButtonGroupControl("b1", Rect(0, 30, 40, 20), group="beta", text="B1", selected=False)
        a2 = ButtonGroupControl("a2", Rect(50, 0, 40, 20), group="alpha", text="A2", selected=False)
        b2 = ButtonGroupControl("b2", Rect(50, 30, 40, 20), group="beta", text="B2", selected=False)

        self.assertTrue(a1.pushed)
        self.assertFalse(a2.pushed)
        self.assertTrue(b1.pushed)
        self.assertFalse(b2.pushed)
        self.assertEqual(ButtonGroupControl._selection_by_group.get("alpha"), "a1")
        self.assertEqual(ButtonGroupControl._selection_by_group.get("beta"), "b1")

    def test_explicit_selected_true_does_not_double_arm_on_second_button(self) -> None:
        first = ButtonGroupControl("a", Rect(0, 0, 40, 20), group="g", text="A", selected=True)
        second = ButtonGroupControl("b", Rect(50, 0, 40, 20), group="g", text="B", selected=False)

        self.assertTrue(first.pushed)
        self.assertFalse(second.pushed)
        self.assertEqual(ButtonGroupControl._selection_by_group.get("g"), "a")

    def test_group_entry_created_in_registry_at_init_time(self) -> None:
        self.assertNotIn("g", ButtonGroupControl._selection_by_group)
        ButtonGroupControl("a", Rect(0, 0, 40, 20), group="g", text="A", selected=False)
        self.assertIn("g", ButtonGroupControl._selection_by_group)


if __name__ == "__main__":
    unittest.main()
