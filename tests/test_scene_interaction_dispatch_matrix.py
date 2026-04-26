import itertools
import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
from pygame import Rect

from gui_do import GuiApplication, LabelControl, PanelControl, TaskPanelControl, WindowControl


class SceneInteractionDispatchMatrixTests(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()
        self.surface = pygame.display.set_mode((500, 360))

    def tearDown(self) -> None:
        pygame.quit()

    def _new_runtime(self):
        app = GuiApplication(self.surface)
        root = app.add(PanelControl("root", Rect(0, 0, 500, 360)))
        win_a = root.add(WindowControl("a", Rect(40, 40, 180, 140), "A"))
        win_b = root.add(WindowControl("b", Rect(180, 60, 180, 140), "B"))
        task_panel = app.add(TaskPanelControl("task_panel", Rect(0, 320, 500, 40), auto_hide=False, dock_bottom=True))
        task_panel.add(LabelControl("task_label", Rect(10, 330, 120, 20), "Task"))
        win_b.active = True
        return app, root, win_a, win_b

    @staticmethod
    def _active_id(*windows: WindowControl):
        active = [window.control_id for window in windows if window.active]
        if not active:
            return None
        if len(active) > 1:
            raise AssertionError("more than one active window")
        return active[0]

    @staticmethod
    def _assert_activation_invariants(*windows: WindowControl) -> None:
        active_windows = [window for window in windows if window.active]
        if len(active_windows) > 1:
            raise AssertionError("more than one active window")
        if active_windows:
            active = active_windows[0]
            if not (active.visible and active.enabled):
                raise AssertionError("active window must remain visible and enabled")

    def _click(self, app: GuiApplication, pos: tuple[int, int]) -> None:
        app.process_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": pos, "button": 1}))
        app.process_event(pygame.event.Event(pygame.MOUSEBUTTONUP, {"pos": pos, "button": 1}))

    def _drag_cycle(self, app: GuiApplication, win: WindowControl) -> None:
        start = win.title_bar_rect().center
        app.process_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": start, "button": 1}))
        app.process_event(
            pygame.event.Event(
                pygame.MOUSEMOTION,
                {"pos": (start[0] + 12, start[1] + 8), "rel": (12, 8), "buttons": (1, 0, 0)},
            )
        )
        app.process_event(pygame.event.Event(pygame.MOUSEBUTTONUP, {"pos": (start[0] + 12, start[1] + 8), "button": 1}))

    @staticmethod
    def _drag_start(app: GuiApplication, win: WindowControl) -> None:
        app.process_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": win.title_bar_rect().center, "button": 1}))

    @staticmethod
    def _flush_motion(app: GuiApplication) -> None:
        app.process_event(pygame.event.Event(pygame.MOUSEMOTION, {"pos": (5, 5), "rel": (0, 0), "buttons": (0, 0, 0)}))

    def test_multi_root_click_drag_permutations_preserve_invariants(self) -> None:
        operation_names = ["click_a", "click_bg", "click_task", "drag_a"]

        for sequence in itertools.permutations(operation_names, 3):
            with self.subTest(sequence=sequence):
                app, _root, win_a, win_b = self._new_runtime()
                for op_name in sequence:
                    before_active = self._active_id(win_a, win_b)
                    if op_name == "click_a":
                        self._click(app, win_a.title_bar_rect().center)
                        self.assertEqual(self._active_id(win_a, win_b), "a")
                    elif op_name == "click_bg":
                        self._click(app, (5, 5))
                        self.assertIsNone(self._active_id(win_a, win_b))
                    elif op_name == "click_task":
                        self._click(app, (20, 335))
                        self.assertEqual(self._active_id(win_a, win_b), before_active)
                    elif op_name == "drag_a":
                        self._drag_cycle(app, win_a)
                        self.assertEqual(self._active_id(win_a, win_b), "a")
                    else:
                        raise AssertionError(f"unknown operation: {op_name}")
                    self._assert_activation_invariants(win_a, win_b)
                    self.assertIsNone(app.pointer_capture.owner_id)

    def test_background_click_remains_authoritative_after_task_and_drag(self) -> None:
        app, _root, win_a, win_b = self._new_runtime()

        self._click(app, (20, 335))
        self.assertEqual(self._active_id(win_a, win_b), "b")

        self._drag_cycle(app, win_a)
        self.assertEqual(self._active_id(win_a, win_b), "a")

        self._click(app, (5, 5))
        self.assertIsNone(self._active_id(win_a, win_b))
        self.assertIsNone(app.pointer_capture.owner_id)

    def test_drag_start_capture_and_transition_sequences_cleanup(self) -> None:
        operation_names = ["hide_a", "disable_a", "remove_a", "click_task"]

        for sequence in itertools.permutations(operation_names, 2):
            with self.subTest(sequence=sequence):
                app, root, win_a, win_b = self._new_runtime()
                self._drag_start(app, win_a)
                self.assertEqual(app.pointer_capture.owner_id, "a")
                self.assertEqual(self._active_id(win_a, win_b), "a")

                for op_name in sequence:
                    if op_name == "hide_a":
                        win_a.visible = False
                        self.assertIsNone(root._drag_window)
                        self.assertIsNone(root._drag_last_pos)
                    elif op_name == "disable_a":
                        win_a.enabled = False
                        self.assertIsNone(root._drag_window)
                        self.assertIsNone(root._drag_last_pos)
                    elif op_name == "remove_a":
                        removed = root.remove(win_a)
                        self.assertTrue(removed)
                        self.assertIsNone(root._drag_window)
                        self.assertIsNone(root._drag_last_pos)
                    elif op_name == "click_task":
                        self._click(app, (20, 335))
                    else:
                        raise AssertionError(f"unknown operation: {op_name}")
                    self._assert_activation_invariants(win_a, win_b)

                self._flush_motion(app)
                self.assertIsNone(app.pointer_capture.owner_id)
                self._assert_activation_invariants(win_a, win_b)


if __name__ == "__main__":
    unittest.main()
