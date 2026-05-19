import unittest
from types import MethodType

import pygame
from pygame import Rect

from gui_do.app.gui_application import GuiApplication
from gui_do.controls.base.ui_node import UiNode
from gui_do.controls.chrome.task_panel_control import TaskPanelControl
from gui_do.controls.input.button_control import ButtonControl
from gui_do.events.gui_event import EventType, GuiEvent


pygame.init()


class _FocusableProbeNode(UiNode):
    def accepts_focus(self) -> bool:
        return True

    def draw(self, _surface, _theme) -> None:
        return None


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

    def test_switch_scene_does_not_draw_focused_control_from_outgoing_scene(self):
        app = GuiApplication(pygame.Surface((320, 240)))
        scene_a = app.create_scene("scene_a")
        scene_b = app.create_scene("scene_b")
        button_a = scene_a.add(_FocusableProbeNode("button_a", Rect(8, 8, 80, 24)))
        scene_b.add(_FocusableProbeNode("button_b", Rect(8, 8, 80, 24)))

        app.switch_scene("scene_a")
        app.focus.set_focus(button_a)

        draw_calls = []
        original_draw_screen_phase = button_a.draw_screen_phase

        def _record_draw(self, surface, theme, app=None):
            draw_calls.append(1)
            return original_draw_screen_phase(surface, theme, app=app)

        button_a.draw_screen_phase = MethodType(_record_draw, button_a)

        app.switch_scene("scene_b")
        app.update(1.0 / 60.0)
        app.draw()

        self.assertIsNone(app.focus.focused_node)
        self.assertEqual([], draw_calls)

    def test_switch_scene_suspends_and_restores_toasts(self):
        app = GuiApplication(pygame.Surface((320, 240)))
        app.create_scene("scene_a")
        app.create_scene("scene_b")

        fired = []

        app.switch_scene("scene_a")
        handle = app.toasts.show("toast", duration_seconds=5.0, on_click=lambda: fired.append("ok"))
        app.update(2.0)

        app.switch_scene("scene_b")
        self.assertFalse(handle.is_visible)
        self.assertEqual(0, app.toasts.visible_count)

        suspended_click = GuiEvent(
            kind=EventType.MOUSE_BUTTON_DOWN,
            type=pygame.MOUSEBUTTONDOWN,
            pos=(app.surface.get_width() - 24, app.surface.get_height() - 24),
            button=1,
        )
        self.assertFalse(app.toasts.route_event(suspended_click, app))
        self.assertEqual([], fired)

        app.update(10.0)
        app.switch_scene("scene_a")
        self.assertTrue(handle.is_visible)
        self.assertEqual(1, app.toasts.visible_count)

        app.update(2.9)
        self.assertEqual(1, app.toasts.visible_count)
        app.update(0.2)
        self.assertEqual(0, app.toasts.visible_count)


if __name__ == "__main__":
    unittest.main()
