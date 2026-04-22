import itertools
import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
from pygame import Rect

from gui import GuiApplication, PanelControl, WindowControl


class PanelWindowDispatchPermutationsTests(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()
        self.surface = pygame.display.set_mode((500, 360))

    def tearDown(self) -> None:
        pygame.quit()

    def _new_runtime(self):
        app = GuiApplication(self.surface)
        panel = app.add(PanelControl("root", Rect(0, 0, 500, 360)))
        win_a = panel.add(WindowControl("a", Rect(20, 20, 180, 140), "A"))
        win_b = panel.add(WindowControl("b", Rect(120, 40, 180, 140), "B"))
        win_b.active = True
        return app, panel, win_a, win_b

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

    def _dispatch_left_click(self, app: GuiApplication, pos: tuple[int, int]) -> None:
        app.process_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": pos, "button": 1}))

    def test_click_and_guard_transition_permutations_keep_activation_valid(self) -> None:
        operation_names = ["click_a", "hide_a", "show_a", "disable_a", "enable_a"]

        for sequence in itertools.permutations(operation_names, 3):
            with self.subTest(sequence=sequence):
                app, panel, win_a, win_b = self._new_runtime()
                for op_name in sequence:
                    if op_name == "click_a":
                        self._dispatch_left_click(app, win_a.title_bar_rect().center)
                    elif op_name == "hide_a":
                        win_a.visible = False
                    elif op_name == "show_a":
                        win_a.visible = True
                    elif op_name == "disable_a":
                        win_a.enabled = False
                    elif op_name == "enable_a":
                        win_a.enabled = True
                    else:
                        raise AssertionError(f"unknown operation: {op_name}")
                    self._assert_activation_invariants(panel, win_a, win_b)

    def test_multi_click_and_state_permutations_keep_activation_valid(self) -> None:
        operation_names = ["click_a", "click_b", "disable_b", "enable_b"]

        for sequence in itertools.permutations(operation_names, 3):
            with self.subTest(sequence=sequence):
                app, panel, win_a, win_b = self._new_runtime()
                for op_name in sequence:
                    if op_name == "click_a":
                        self._dispatch_left_click(app, win_a.title_bar_rect().center)
                    elif op_name == "click_b":
                        self._dispatch_left_click(app, win_b.title_bar_rect().center)
                    elif op_name == "disable_b":
                        win_b.enabled = False
                    elif op_name == "enable_b":
                        win_b.enabled = True
                    else:
                        raise AssertionError(f"unknown operation: {op_name}")
                    self._assert_activation_invariants(panel, win_a, win_b)


if __name__ == "__main__":
    unittest.main()
