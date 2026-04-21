import unittest

from pygame import Rect

from gui.controls.button_group_control import ButtonGroupControl
from gui.controls.panel_control import PanelControl


class ButtonGroupSelectionLifecycleTests(unittest.TestCase):
    def setUp(self) -> None:
        ButtonGroupControl._selection_by_group.clear()

    def tearDown(self) -> None:
        ButtonGroupControl._selection_by_group.clear()

    def test_removing_selected_button_clears_group_selection(self) -> None:
        panel = PanelControl("panel", Rect(0, 0, 200, 100))
        selected = panel.add(ButtonGroupControl("a", Rect(0, 0, 40, 20), group="g", text="A", selected=True))
        peer = panel.add(ButtonGroupControl("b", Rect(50, 0, 40, 20), group="g", text="B", selected=False))

        removed = panel.remove(selected)

        self.assertTrue(removed)
        self.assertEqual(peer.button_id, "b")
        self.assertNotIn("g", ButtonGroupControl._selection_by_group)

    def test_removing_non_selected_button_keeps_selected_mapping(self) -> None:
        panel = PanelControl("panel", Rect(0, 0, 200, 100))
        selected = panel.add(ButtonGroupControl("a", Rect(0, 0, 40, 20), group="g", text="A", selected=True))
        other = panel.add(ButtonGroupControl("b", Rect(50, 0, 40, 20), group="g", text="B", selected=False))

        removed = panel.remove(other)

        self.assertTrue(removed)
        self.assertEqual(selected.button_id, "a")
        self.assertEqual(ButtonGroupControl._selection_by_group.get("g"), "a")


if __name__ == "__main__":
    unittest.main()
