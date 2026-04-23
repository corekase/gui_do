import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
from pygame import Rect

from gui import ButtonGroupControl, GuiApplication, PanelControl
from gui.core.focus_hint_constants import FOCUS_TRAVERSAL_HINT_TIMEOUT_SECONDS


class ButtonGroupRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()
        self.surface = pygame.display.set_mode((260, 140))
        ButtonGroupControl._selection_by_group.clear()
        self.app = GuiApplication(self.surface)
        self.panel = self.app.add(PanelControl("root", Rect(0, 0, 260, 140)))

    def tearDown(self) -> None:
        ButtonGroupControl._selection_by_group.clear()
        pygame.quit()

    def test_clicking_selected_button_keeps_it_selected(self) -> None:
        selected = self.panel.add(ButtonGroupControl("a", Rect(10, 10, 50, 24), group="g", text="A", selected=True))
        other = self.panel.add(ButtonGroupControl("b", Rect(70, 10, 50, 24), group="g", text="B", selected=False))

        consumed = self.app.process_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": selected.rect.center, "button": 1}))

        self.assertTrue(consumed)
        self.assertTrue(selected.pushed)
        self.assertFalse(other.pushed)
        self.assertEqual(ButtonGroupControl._selection_by_group.get("g"), "a")

    def test_clicking_peer_switches_selection_and_clears_previous(self) -> None:
        first = self.panel.add(ButtonGroupControl("a", Rect(10, 10, 50, 24), group="g", text="A", selected=True))
        second = self.panel.add(ButtonGroupControl("b", Rect(70, 10, 50, 24), group="g", text="B", selected=False))

        consumed = self.app.process_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": second.rect.center, "button": 1}))

        self.assertTrue(consumed)
        self.assertFalse(first.pushed)
        self.assertTrue(second.pushed)
        self.assertEqual(ButtonGroupControl._selection_by_group.get("g"), "b")

    def test_keyboard_activation_when_focused_switches_selection(self) -> None:
        first = self.panel.add(ButtonGroupControl("a", Rect(10, 10, 50, 24), group="g", text="A", selected=True))
        second = self.panel.add(ButtonGroupControl("b", Rect(70, 10, 50, 24), group="g", text="B", selected=False))
        first.set_tab_index(0)
        second.set_tab_index(1)
        self.app.focus.set_focus(second)

        consumed = self.app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RETURN}))

        self.assertTrue(consumed)
        self.assertFalse(first.pushed)
        self.assertTrue(second.pushed)
        self.assertEqual(ButtonGroupControl._selection_by_group.get("g"), "b")

    def test_keyboard_activation_ignored_when_not_focused(self) -> None:
        first = self.panel.add(ButtonGroupControl("a", Rect(10, 10, 50, 24), group="g", text="A", selected=True))
        second = self.panel.add(ButtonGroupControl("b", Rect(70, 10, 50, 24), group="g", text="B", selected=False))
        first.set_tab_index(0)
        second.set_tab_index(1)
        self.app.focus.set_focus(first)

        consumed = second.handle_event(
            self.app.event_manager.to_gui_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RETURN})),
            self.app,
        )

        self.assertFalse(consumed)
        self.assertTrue(first.pushed)
        self.assertFalse(second.pushed)
        self.assertEqual(ButtonGroupControl._selection_by_group.get("g"), "a")

    def test_set_on_activate_called_on_keyboard_activation(self) -> None:
        fired = []
        first = self.panel.add(ButtonGroupControl("a", Rect(10, 10, 50, 24), group="g", text="A", selected=True))
        second = self.panel.add(ButtonGroupControl("b", Rect(70, 10, 50, 24), group="g", text="B", selected=False))
        second.set_tab_index(0)
        second.set_on_activate(lambda: fired.append("hit"))
        self.app.focus.set_focus(second)

        consumed = self.app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_SPACE}))

        self.assertTrue(consumed)
        self.assertFalse(first.pushed)
        self.assertTrue(second.pushed)
        self.assertEqual(fired, ["hit"])

    def test_keyboard_activation_refreshes_focus_hint_with_shared_timeout(self) -> None:
        first = self.panel.add(ButtonGroupControl("a", Rect(10, 10, 50, 24), group="g", text="A", selected=True))
        second = self.panel.add(ButtonGroupControl("b", Rect(70, 10, 50, 24), group="g", text="B", selected=False))
        first.set_tab_index(0)
        second.set_tab_index(1)

        self.app.focus.set_focus(second, show_hint=False)
        self.assertIsNone(self.app.focus_visualizer._current_hint_node)

        consumed = self.app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_SPACE}))

        self.assertTrue(consumed)
        self.assertFalse(first.pushed)
        self.assertTrue(second.pushed)
        self.assertIs(self.app.focus_visualizer._current_hint_node, second)
        self.assertEqual(self.app.focus_visualizer._current_hint_elapsed, 0.0)

        almost_timeout = FOCUS_TRAVERSAL_HINT_TIMEOUT_SECONDS - 0.01
        self.app.focus_visualizer.update(almost_timeout)
        self.assertIs(self.app.focus_visualizer._current_hint_node, second)

        self.app.focus_visualizer.update(0.02)
        self.assertIsNone(self.app.focus_visualizer._current_hint_node)


if __name__ == "__main__":
    unittest.main()
