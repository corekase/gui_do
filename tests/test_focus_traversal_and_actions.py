import unittest

import pygame
from pygame import Rect, Surface

from gui.app.gui_application import GuiApplication
from gui.controls.panel_control import PanelControl
from gui.controls.window_control import WindowControl
from gui.core.ui_node import UiNode


class _FocusableProbe(UiNode):
    def __init__(self, control_id: str, rect: Rect, tab_index: int) -> None:
        super().__init__(control_id, rect)
        self.set_tab_index(tab_index)
        self.key_hits = 0

    def handle_event(self, event, _app) -> bool:
        if event.is_key_down(pygame.K_RETURN):
            self.key_hits += 1
            return True
        return False


class FocusTraversalAndActionsTests(unittest.TestCase):
    def test_tab_cycles_focus_within_active_window(self) -> None:
        pygame.init()
        try:
            app = GuiApplication(Surface((320, 180)))
            root = app.add(PanelControl("root", Rect(0, 0, 320, 180)))
            win = root.add(WindowControl("win", Rect(10, 10, 240, 140), "Win"))
            first = win.add(_FocusableProbe("first", Rect(20, 40, 80, 20), tab_index=0))
            second = win.add(_FocusableProbe("second", Rect(20, 70, 80, 20), tab_index=1))
            win.active = True

            app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_TAB, "mod": 0}))
            self.assertIs(app.focus.focused_node, first)

            app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_TAB, "mod": 0}))
            self.assertIs(app.focus.focused_node, second)

            app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_TAB, "mod": pygame.KMOD_SHIFT}))
            self.assertIs(app.focus.focused_node, first)
        finally:
            pygame.quit()

    def test_bound_action_executes_before_screen_handler(self) -> None:
        pygame.init()
        try:
            app = GuiApplication(Surface((320, 180)))
            seen = {"action": 0, "screen": 0}

            def action_handler(_event) -> bool:
                seen["action"] += 1
                return True

            def screen_handler(_event) -> bool:
                seen["screen"] += 1
                return True

            app.actions.register_action("quit", action_handler)
            app.actions.bind_key(pygame.K_ESCAPE, "quit")
            app.set_screen_lifecycle(event_handler=screen_handler)

            consumed = app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_ESCAPE}))

            self.assertTrue(consumed)
            self.assertEqual(seen["action"], 1)
            self.assertEqual(seen["screen"], 0)
        finally:
            pygame.quit()

    def test_key_action_prevent_default_blocks_screen_handler(self) -> None:
        pygame.init()
        try:
            app = GuiApplication(Surface((320, 180)))
            seen = {"action": 0, "screen": 0}

            def action_handler(event) -> bool:
                seen["action"] += 1
                event.prevent_default()
                return False

            def screen_handler(_event) -> bool:
                seen["screen"] += 1
                return True

            app.actions.register_action("noop", action_handler)
            app.actions.bind_key(pygame.K_ESCAPE, "noop")
            app.set_screen_lifecycle(event_handler=screen_handler)

            consumed = app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_ESCAPE}))

            self.assertTrue(consumed)
            self.assertEqual(seen["action"], 1)
            self.assertEqual(seen["screen"], 0)
        finally:
            pygame.quit()


if __name__ == "__main__":
    unittest.main()
