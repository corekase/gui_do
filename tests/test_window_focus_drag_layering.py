import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
from pygame import Rect

from gui import ButtonControl, CanvasControl, GuiApplication, LabelControl, PanelControl, TaskPanelControl, WindowControl


class WindowFocusDragLayeringTest(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()
        self.surface = pygame.display.set_mode((500, 360))
        self.app = GuiApplication(self.surface)
        self.root = self.app.add(PanelControl("root", Rect(0, 0, 500, 360)))

    def tearDown(self) -> None:
        pygame.quit()

    def test_clicking_window_titlebar_sets_active_and_raises(self) -> None:
        win_a = self.root.add(WindowControl("win_a", Rect(20, 20, 180, 140), "A"))
        win_b = self.root.add(WindowControl("win_b", Rect(120, 40, 180, 140), "B"))

        self.assertEqual(self.root.children[-1], win_b)

        self.app.process_event(
            pygame.event.Event(
                pygame.MOUSEBUTTONDOWN,
                {
                    "pos": (30, 30),
                    "button": 1,
                },
            )
        )

        self.assertTrue(win_a.active)
        self.assertFalse(win_b.active)
        self.assertEqual(self.root.children[-1], win_a)

    def test_clicking_lower_widget_lowers_window(self) -> None:
        win_a = self.root.add(WindowControl("win_a", Rect(20, 20, 180, 140), "A"))
        win_b = self.root.add(WindowControl("win_b", Rect(120, 40, 180, 140), "B"))

        lower_pos = win_b.lower_widget_rect().center
        self.app.process_event(
            pygame.event.Event(
                pygame.MOUSEBUTTONDOWN,
                {
                    "pos": lower_pos,
                    "button": 1,
                },
            )
        )

        self.assertEqual(self.root.children[0], win_b)

        # Clicking another window should make it active again.
        self.app.process_event(
            pygame.event.Event(
                pygame.MOUSEBUTTONDOWN,
                {
                    "pos": (30, 30),
                    "button": 1,
                },
            )
        )
        self.assertTrue(win_a.active)

    def test_lower_widget_sets_active_to_new_top_window(self) -> None:
        win_a = self.root.add(WindowControl("win_a", Rect(20, 20, 180, 140), "A"))
        win_b = self.root.add(WindowControl("win_b", Rect(120, 40, 180, 140), "B"))

        self.assertEqual(self.root.children[-1], win_b)
        lower_pos = win_b.lower_widget_rect().center
        self.app.process_event(
            pygame.event.Event(
                pygame.MOUSEBUTTONDOWN,
                {
                    "pos": lower_pos,
                    "button": 1,
                },
            )
        )

        self.assertEqual(self.root.children[0], win_b)
        self.assertEqual(self.root.children[-1], win_a)
        self.assertTrue(win_a.active)
        self.assertFalse(win_b.active)

    def test_lower_widget_keeps_window_above_non_window_layers(self) -> None:
        bg = self.root.add(CanvasControl("bg", Rect(0, 0, 500, 360), max_events=1))
        win_a = self.root.add(WindowControl("win_a", Rect(20, 20, 180, 140), "A"))
        win_b = self.root.add(WindowControl("win_b", Rect(120, 40, 180, 140), "B"))

        self.assertLess(self.root.children.index(bg), self.root.children.index(win_a))
        lower_pos = win_b.lower_widget_rect().center
        self.app.process_event(
            pygame.event.Event(
                pygame.MOUSEBUTTONDOWN,
                {
                    "pos": lower_pos,
                    "button": 1,
                },
            )
        )

        self.assertLess(self.root.children.index(bg), self.root.children.index(win_b))

    def test_setting_window_active_deactivates_other_windows(self) -> None:
        win_a = self.root.add(WindowControl("win_a", Rect(20, 20, 180, 140), "A"))
        win_b = self.root.add(WindowControl("win_b", Rect(120, 40, 180, 140), "B"))

        win_a.active = True
        self.assertTrue(win_a.active)
        self.assertFalse(win_b.active)

        win_b.active = True
        self.assertFalse(win_a.active)
        self.assertTrue(win_b.active)

    def test_titlebar_drag_moves_window_and_children(self) -> None:
        win = self.root.add(WindowControl("win", Rect(40, 40, 220, 160), "Drag"))
        child = win.add(LabelControl("child", Rect(56, 80, 100, 20), "child"))

        start_win_pos = win.rect.topleft
        start_child_pos = child.rect.topleft
        drag_start = (win.rect.left + 10, win.rect.top + 10)

        self.app.process_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": drag_start, "button": 1}))
        self.app.process_event(
            pygame.event.Event(
                pygame.MOUSEMOTION,
                {
                    "pos": (drag_start[0] + 24, drag_start[1] + 18),
                    "rel": (24, 18),
                    "buttons": (1, 0, 0),
                },
            )
        )
        self.app.process_event(
            pygame.event.Event(
                pygame.MOUSEBUTTONUP,
                {
                    "pos": (drag_start[0] + 24, drag_start[1] + 18),
                    "button": 1,
                },
            )
        )

        self.assertEqual(win.rect.topleft, (start_win_pos[0] + 24, start_win_pos[1] + 18))
        self.assertEqual(child.rect.topleft, (start_child_pos[0] + 24, start_child_pos[1] + 18))
        self.assertIsNone(self.app.pointer_capture.owner_id)

    def test_window_becomes_top_when_made_visible(self) -> None:
        win_a = self.root.add(WindowControl("win_a", Rect(20, 20, 180, 140), "A"))
        win_b = self.root.add(WindowControl("win_b", Rect(120, 40, 180, 140), "B"))

        self.assertEqual(self.root.children[-1], win_b)
        win_a.visible = False
        self.assertNotEqual(self.root.children[-1], win_a)

        win_a.visible = True
        self.assertEqual(self.root.children[-1], win_a)

    def test_hiding_active_window_activates_next_top_window(self) -> None:
        win_a = self.root.add(WindowControl("win_a", Rect(20, 20, 180, 140), "A"))
        win_b = self.root.add(WindowControl("win_b", Rect(80, 40, 180, 140), "B"))
        win_c = self.root.add(WindowControl("win_c", Rect(140, 60, 180, 140), "C"))

        self.assertEqual(self.root.children[-1], win_c)
        win_c.active = True

        win_c.visible = False

        self.assertFalse(win_c.active)
        self.assertTrue(win_b.active)
        self.assertFalse(win_a.active)

    def test_hiding_last_visible_window_clears_active_window(self) -> None:
        win_a = self.root.add(WindowControl("win_a", Rect(20, 20, 180, 140), "A"))
        win_b = self.root.add(WindowControl("win_b", Rect(120, 40, 180, 140), "B"))

        win_b.visible = False
        win_a.active = True
        win_a.visible = False

        self.assertFalse(win_a.active)
        self.assertFalse(win_b.active)

    def test_clicking_non_window_background_clears_active_window(self) -> None:
        win = self.root.add(WindowControl("win", Rect(80, 60, 180, 140), "A"))
        win.active = True

        self.app.process_event(
            pygame.event.Event(
                pygame.MOUSEBUTTONDOWN,
                {
                    "pos": (10, 10),
                    "button": 1,
                },
            )
        )

        self.assertFalse(win.active)

    def test_task_panel_click_does_not_change_window_activation(self) -> None:
        win = self.root.add(WindowControl("win", Rect(80, 60, 180, 140), "A"))
        task_panel = self.app.add(TaskPanelControl("task_panel", Rect(0, 320, 500, 40), auto_hide=False, dock_bottom=True))
        task_panel.add(LabelControl("task_label", Rect(10, 330, 100, 20), "Task"))
        win.active = True

        self.app.process_event(
            pygame.event.Event(
                pygame.MOUSEBUTTONDOWN,
                {
                    "pos": (20, 335),
                    "button": 1,
                },
            )
        )

        self.assertTrue(win.active)


    def test_background_click_keeps_existing_focus_while_returning_to_screen_lifecycle(self) -> None:
        win = self.root.add(WindowControl("win", Rect(80, 60, 180, 140), "A"))
        btn = win.add(ButtonControl("btn", Rect(100, 90, 80, 30), "OK"))
        btn.set_tab_index(0)
        win.active = True
        self.app.focus.set_focus(btn, show_hint=False)
        self.assertIs(self.app.focus.focused_node, btn)

        self.app.process_event(
            pygame.event.Event(
                pygame.MOUSEBUTTONDOWN,
                {"pos": (10, 10), "button": 1},
            )
        )

        self.assertFalse(win.active)
        self.assertIs(self.app.focus.focused_node, btn)

    def test_background_click_is_idempotent_when_focus_already_screen_lifecycle(self) -> None:
        win = self.root.add(WindowControl("win", Rect(80, 60, 180, 140), "A"))
        win.active = True
        self.assertIsNone(self.app.focus.focused_node)

        self.app.process_event(
            pygame.event.Event(
                pygame.MOUSEBUTTONDOWN,
                {"pos": (10, 10), "button": 1},
            )
        )

        self.assertIsNone(self.app.focus.focused_node)


if __name__ == "__main__":
    unittest.main()
