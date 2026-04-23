import unittest

from pygame import Rect

from gui.controls.button_group_control import ButtonGroupControl
from gui.controls.panel_control import PanelControl


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


if __name__ == "__main__":
    unittest.main()
