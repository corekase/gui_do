import unittest

import pygame
from pygame import Rect

from gui_do.app.gui_application import GuiApplication
from gui_do.controls.chrome.task_panel_control import TaskPanelControl
from gui_do.controls.input.button_control import ButtonControl


pygame.init()


class TestTaskPanelSceneSwitchHoverReconcile(unittest.TestCase):
    def _make_scene_with_panel(self, app: GuiApplication, scene_name: str):
        scene = app.create_scene(scene_name)
        panel = TaskPanelControl(f"{scene_name}_task_panel", Rect(0, 0, 120, 80), auto_hide=False)
        button = panel.add(ButtonControl(f"{scene_name}_button", Rect(10, 10, 80, 24), "Action"))
        scene.add(panel)
        return panel, button

    def test_switch_scene_clears_outgoing_task_panel_hover_state(self):
        app = GuiApplication(pygame.Surface((320, 240)))
        panel_a, button_a = self._make_scene_with_panel(app, "scene_a")
        self._make_scene_with_panel(app, "scene_b")

        app.switch_scene("scene_a")
        panel_a.reconcile_hover(True)
        button_a.reconcile_hover(True)

        self.assertTrue(panel_a._hovered)
        self.assertTrue(button_a.hovered)

        app.switch_scene("scene_b")

        self.assertFalse(panel_a._hovered)
        self.assertFalse(button_a.hovered)

    def test_switch_scene_recomputes_incoming_task_panel_hover_from_pointer(self):
        app = GuiApplication(pygame.Surface((320, 240)))
        self._make_scene_with_panel(app, "scene_a")
        panel_b, button_b = self._make_scene_with_panel(app, "scene_b")

        app._logical_pointer_pos = (20, 20)
        panel_b.reconcile_hover(False)
        button_b.reconcile_hover(False)

        app.switch_scene("scene_b")

        self.assertTrue(panel_b._hovered)
        self.assertTrue(button_b.hovered)


if __name__ == "__main__":
    unittest.main()
