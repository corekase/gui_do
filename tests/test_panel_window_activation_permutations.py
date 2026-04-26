import itertools
import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
from pygame import Rect

from gui_do import GuiApplication, PanelControl, WindowControl


class PanelWindowActivationPermutationsTests(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()
        self.surface = pygame.display.set_mode((500, 360))

    def tearDown(self) -> None:
        pygame.quit()

    def _new_panel_with_two_windows(self):
        app = GuiApplication(self.surface)
        panel = app.add(PanelControl("root", Rect(0, 0, 500, 360)))
        win_a = panel.add(WindowControl("a", Rect(20, 20, 120, 100), "A"))
        win_b = panel.add(WindowControl("b", Rect(60, 40, 120, 100), "B"))
        win_b.active = True
        return panel, win_a, win_b

    @staticmethod
    def _assert_activation_invariants(panel: PanelControl, *windows: WindowControl) -> None:
        active_windows = [window for window in windows if window.active]
        if len(active_windows) > 1:
            raise AssertionError("more than one active window")
        if active_windows:
            active = active_windows[0]
            if not active.visible:
                raise AssertionError("active window must be visible")
            if not active.enabled:
                raise AssertionError("active window must be enabled")
        else:
            top = panel._top_visible_window()
            if top is not None and getattr(top, "active", False):
                raise AssertionError("top visible window cannot be active when active set is empty")

    def test_guard_transition_permutations_keep_activation_valid(self) -> None:
        operation_names = ["hide_a", "disable_a", "activate_a", "show_a", "enable_a"]

        for sequence in itertools.permutations(operation_names, 3):
            with self.subTest(sequence=sequence):
                panel, win_a, win_b = self._new_panel_with_two_windows()
                for op_name in sequence:
                    if op_name == "hide_a":
                        win_a.visible = False
                    elif op_name == "disable_a":
                        win_a.enabled = False
                    elif op_name == "activate_a":
                        win_a.active = True
                    elif op_name == "show_a":
                        win_a.visible = True
                    elif op_name == "enable_a":
                        win_a.enabled = True
                    else:
                        raise AssertionError(f"unknown operation: {op_name}")
                    self._assert_activation_invariants(panel, win_a, win_b)

    def test_ordering_transition_permutations_keep_activation_valid(self) -> None:
        operation_names = ["raise_a", "lower_a", "activate_a", "activate_b"]

        for sequence in itertools.permutations(operation_names, 3):
            with self.subTest(sequence=sequence):
                panel, win_a, win_b = self._new_panel_with_two_windows()
                for op_name in sequence:
                    if op_name == "raise_a":
                        panel._raise_window(win_a)
                    elif op_name == "lower_a":
                        panel._lower_window(win_a)
                    elif op_name == "activate_a":
                        win_a.active = True
                    elif op_name == "activate_b":
                        win_b.active = True
                    else:
                        raise AssertionError(f"unknown operation: {op_name}")
                    self._assert_activation_invariants(panel, win_a, win_b)


if __name__ == "__main__":
    unittest.main()
