import unittest

import pygame
from pygame import Rect

from gui_do.app.gui_application import GuiApplication
from gui_do.controls.chrome.menu_bar_control import MenuStripControl
from gui_do.controls.chrome.task_panel_control import TaskPanelControl
from gui_do.controls.chrome.window_control import WindowControl
from gui_do.controls.composite.panel_control import PanelControl
from gui_do.events.gui_event import EventType, GuiEvent


class _StubTaskPanelFocus:
    def is_active_for(self, _panel) -> bool:
        return False


class _StubOverlay:
    def has_overlay(self, _control_id: str) -> bool:
        return False


class _StubApp:
    def __init__(self) -> None:
        self.task_panel_focus = _StubTaskPanelFocus()
        self.overlay = _StubOverlay()
        self.logical_pointer_pos = (0, 0)


class TestSceneChromeContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not pygame.get_init():
            pygame.init()
        if not pygame.font.get_init():
            pygame.font.init()

    def test_scene_menu_bar_snaps_to_top_and_full_width(self):
        app = GuiApplication(pygame.Surface((800, 600)))
        menu = MenuStripControl("menu")

        app.add(menu)

        self.assertEqual(Rect(0, 0, 800, MenuStripControl.preferred_height()), menu.rect)
        self.assertEqual(MenuStripControl.preferred_height(), app.scene_menu_bar_height())

    def test_window_menu_bar_snaps_to_top_of_window_scope(self):
        window = WindowControl("win", Rect(100, 100, 300, 200), "Window")
        menu = MenuStripControl("menu")

        window.add(menu)

        self.assertEqual(window.content_rect().x, menu.rect.x)
        self.assertEqual(window.content_rect().y, menu.rect.y)
        self.assertEqual(window.content_rect().width, menu.rect.width)

    def test_second_scene_task_panel_raises_logical_error(self):
        app = GuiApplication(pygame.Surface((800, 600)))
        app.add(TaskPanelControl("task_a", Rect(0, 0, 100, 56), auto_hide=False))

        with self.assertRaises(ValueError) as ctx:
            app.add(TaskPanelControl("task_b", Rect(0, 0, 100, 56), auto_hide=False))

        self.assertIn("can only have one task panel in this scope", str(ctx.exception))

    def test_task_panel_cannot_be_added_to_window(self):
        window = WindowControl("win", Rect(40, 40, 320, 220), "Window")

        with self.assertRaises(ValueError) as ctx:
            window.add(TaskPanelControl("task", Rect(0, 0, 320, 48), auto_hide=False))

        self.assertIn("task panel cannot be added to a window", str(ctx.exception))

    def test_task_panel_reserved_height_depends_on_autohide(self):
        hidden = TaskPanelControl(
            "hidden",
            Rect(0, 540, 800, 60),
            auto_hide=True,
            hidden_peek_pixels=7,
            dock_bottom=True,
        )
        shown = TaskPanelControl("shown", Rect(0, 540, 800, 60), auto_hide=False)

        self.assertEqual(7, hidden.reserved_height())
        self.assertEqual(60, shown.reserved_height())

    def test_task_panel_consumes_pointer_events_inside_panel(self):
        panel = TaskPanelControl("task", Rect(0, 540, 800, 60), auto_hide=False)
        app = _StubApp()

        event = GuiEvent(
            kind=EventType.MOUSE_MOTION,
            type=pygame.MOUSEMOTION,
            pos=(100, 560),
            rel=(0, 0),
        )
        consumed = panel.handle_event(event, app, theme=None)

        self.assertTrue(consumed)
        self.assertTrue(event.default_prevented)
        self.assertTrue(event.propagation_stopped)

    def test_bounded_area_excludes_menu_and_task_panel_reserved_heights(self):
        app = GuiApplication(pygame.Surface((800, 600)))
        app.add(MenuStripControl("menu"))
        app.add(
            TaskPanelControl(
                "task",
                Rect(0, 520, 800, 80),
                auto_hide=True,
                hidden_peek_pixels=6,
                dock_bottom=True,
            )
        )

        bounded = app.bounded_area_rect()

        self.assertEqual(0, bounded.x)
        self.assertEqual(MenuStripControl.preferred_height(), bounded.y)
        self.assertEqual(800, bounded.width)
        self.assertEqual(600 - MenuStripControl.preferred_height() - 6, bounded.height)

    def test_window_drag_limits_follow_application_bounded_area_rect(self):
        panel = PanelControl("panel", Rect(0, 0, 800, 600))
        window = WindowControl("win", Rect(0, 0, 200, 100), "Window")
        panel.add(window)

        class _BoundedAreaApp:
            def __init__(self) -> None:
                self.surface = pygame.Surface((800, 600))

            def bounded_area_rect(self, scene_name=None):
                return Rect(100, 50, 400, 300)

        app = _BoundedAreaApp()

        self.assertEqual((100, 300, 50, 250), panel._window_drag_limits(window, app))
        self.assertEqual((100, 50), panel._clamp_window_drag_target(window, -20, -10, app))
        self.assertEqual((300, 250), panel._clamp_window_drag_target(window, 1000, 1000, app))

    def test_scene_root_task_panel_occludes_window_lower_control_pointer_events(self):
        app = GuiApplication(pygame.Surface((800, 600)))
        window = WindowControl("win", Rect(560, 540, 220, 140), "W")
        task_panel = TaskPanelControl(
            "task",
            Rect(0, 520, 800, 80),
            auto_hide=True,
            hidden_peek_pixels=6,
            animation_step_px=200,
            dock_bottom=True,
        )
        app.add(window)
        app.add(task_panel)

        task_panel.set_focus_mode(True)
        task_panel.update(0.0)
        pos = window.lower_control_rect().center
        self.assertTrue(task_panel.rect.collidepoint(pos))

        event = GuiEvent(
            kind=EventType.MOUSE_MOTION,
            type=pygame.MOUSEMOTION,
            pos=pos,
            rel=(0, 0),
            raw_rel=(0, 0),
        )
        consumed = app.scene.dispatch(event, app, theme=app.theme)

        self.assertTrue(consumed)
        self.assertFalse(window._lower_control_button.hovered)

    def test_scene_root_task_panel_clears_stale_lower_control_hover_on_update(self):
        app = GuiApplication(pygame.Surface((800, 600)))
        window = WindowControl("win", Rect(560, 500, 220, 140), "W")
        task_panel = TaskPanelControl(
            "task",
            Rect(0, 520, 800, 80),
            auto_hide=True,
            hidden_peek_pixels=6,
            animation_step_px=200,
            dock_bottom=True,
        )
        app.add(window)
        app.add(task_panel)

        task_panel.set_focus_mode(True)
        task_panel.update(0.0)
        pos = (window.lower_control_rect().centerx, int(task_panel._shown_y + 4))
        window._lower_control_button.hovered = True
        app.set_logical_pointer_position(pos, apply_constraints=False)

        app.update(0.0)

        self.assertFalse(window._lower_control_button.hovered)


if __name__ == "__main__":
    unittest.main()
