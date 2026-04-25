import itertools
import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
from pygame import Rect

from gui import GuiApplication, PanelControl, WindowControl


class PanelWindowDragDispatchPermutationsTests(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()
        self.surface = pygame.display.set_mode((500, 360))

    def tearDown(self) -> None:
        pygame.quit()

    def _new_runtime(self):
        app = GuiApplication(self.surface)
        panel = app.add(PanelControl("root", Rect(0, 0, 500, 360)))
        win = panel.add(WindowControl("win", Rect(40, 40, 200, 140), "W"))
        other = panel.add(WindowControl("other", Rect(260, 40, 180, 140), "O"))
        return app, panel, win, other

    @staticmethod
    def _assert_activation_invariants(*windows: WindowControl) -> None:
        active_windows = [window for window in windows if window.active]
        if len(active_windows) > 1:
            raise AssertionError("more than one active window")
        if active_windows:
            active = active_windows[0]
            if not active.visible or not active.enabled:
                raise AssertionError("active window must be visible and enabled")

    @staticmethod
    def _assert_drag_state_consistency(panel: PanelControl, app: GuiApplication) -> None:
        if panel._drag_window is None and panel._drag_last_pos is not None:
            raise AssertionError("drag last position must be cleared when no drag window exists")
        if panel._drag_window is not None and not app.pointer_capture.is_owned_by(panel._drag_window.control_id):
            raise AssertionError("active drag window must own pointer capture")

    def _dispatch_drag_start(self, app: GuiApplication, win: WindowControl) -> None:
        app.process_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": win.title_bar_rect().center, "button": 1}))

    @staticmethod
    def _dispatch_drag_move(app: GuiApplication, win: WindowControl) -> None:
        center = win.title_bar_rect().center
        app.process_event(
            pygame.event.Event(
                pygame.MOUSEMOTION,
                {"pos": (center[0] + 10, center[1] + 8), "rel": (10, 8), "buttons": (1, 0, 0)},
            )
        )

    @staticmethod
    def _dispatch_drag_release(app: GuiApplication, win: WindowControl) -> None:
        app.process_event(pygame.event.Event(pygame.MOUSEBUTTONUP, {"pos": win.title_bar_rect().center, "button": 1}))

    @staticmethod
    def _dispatch_flush_motion(app: GuiApplication) -> None:
        app.process_event(pygame.event.Event(pygame.MOUSEMOTION, {"pos": (5, 5), "rel": (0, 0), "buttons": (0, 0, 0)}))

    def test_transition_permutations_cleanup_capture_after_flush(self) -> None:
        transition_ops = ["hide", "disable", "remove"]

        for sequence in itertools.permutations(transition_ops, 2):
            with self.subTest(sequence=sequence):
                app, panel, win, other = self._new_runtime()
                self._dispatch_drag_start(app, win)
                self.assertTrue(app.pointer_capture.is_owned_by("win"))

                for op_name in sequence:
                    if op_name == "hide":
                        win.visible = False
                    elif op_name == "disable":
                        win.enabled = False
                    elif op_name == "remove":
                        panel.remove(win)
                    else:
                        raise AssertionError(f"unknown operation: {op_name}")
                    self._assert_drag_state_consistency(panel, app)
                    self._assert_activation_invariants(win, other)

                self._dispatch_flush_motion(app)
                self.assertFalse(app.pointer_capture.is_owned_by("win"))
                self._assert_drag_state_consistency(panel, app)
                self._assert_activation_invariants(win, other)

    def test_drag_dispatch_permutations_keep_invariants(self) -> None:
        operation_names = ["move", "release", "hide", "disable", "remove"]

        for sequence in itertools.permutations(operation_names, 3):
            with self.subTest(sequence=sequence):
                app, panel, win, other = self._new_runtime()
                self._dispatch_drag_start(app, win)

                for op_name in sequence:
                    if op_name == "move":
                        self._dispatch_drag_move(app, win)
                    elif op_name == "release":
                        self._dispatch_drag_release(app, win)
                    elif op_name == "hide":
                        win.visible = False
                    elif op_name == "disable":
                        win.enabled = False
                    elif op_name == "remove":
                        panel.remove(win)
                    else:
                        raise AssertionError(f"unknown operation: {op_name}")
                    self._assert_drag_state_consistency(panel, app)
                    self._assert_activation_invariants(win, other)

                self._dispatch_flush_motion(app)
                self._assert_drag_state_consistency(panel, app)
                self._assert_activation_invariants(win, other)


if __name__ == "__main__":
    unittest.main()
