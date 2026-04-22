import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
from pygame import Rect

from gui import ButtonGroupControl, GuiApplication, PanelControl


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


if __name__ == "__main__":
    unittest.main()
