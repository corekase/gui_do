import unittest

from pygame import Rect

from gui.controls.task_panel_control import TaskPanelControl
from gui.core.ui_node import UiNode


class TaskPanelOffsetTests(unittest.TestCase):
    def test_remove_clears_child_offset_tracking(self) -> None:
        panel = TaskPanelControl("panel", Rect(0, 0, 100, 30), auto_hide=False)
        child = panel.add(UiNode("child", Rect(10, 5, 20, 10)))

        self.assertIn(child, panel._child_local_offsets)
        removed = panel.remove(child)

        self.assertTrue(removed)
        self.assertNotIn(child, panel._child_local_offsets)

    def test_readd_child_uses_fresh_offset_after_removal(self) -> None:
        panel = TaskPanelControl("panel", Rect(0, 0, 100, 30), auto_hide=False)
        child = panel.add(UiNode("child", Rect(10, 5, 20, 10)))
        panel.remove(child)

        panel.rect.topleft = (50, 40)
        child.rect.topleft = (70, 80)
        panel.add(child)

        panel.update(0.0)

        self.assertEqual(child.rect.topleft, (70, 80))


if __name__ == "__main__":
    unittest.main()
