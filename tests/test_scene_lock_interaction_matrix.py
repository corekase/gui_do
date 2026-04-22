import itertools
import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
from pygame import Rect

from gui import GuiApplication, PanelControl, WindowControl


class SceneLockInteractionMatrixTests(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()
        self.surface = pygame.display.set_mode((500, 360))

    def tearDown(self) -> None:
        pygame.quit()

    def _new_runtime(self):
        app = GuiApplication(self.surface)
        root = app.add(PanelControl("root", Rect(0, 0, 500, 360)))
        win_a = root.add(WindowControl("a", Rect(40, 40, 180, 140), "A"))
        win_b = root.add(WindowControl("b", Rect(220, 60, 180, 140), "B"))
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

    @staticmethod
    def _assert_lock_state_sane(app: GuiApplication) -> None:
        if app.mouse_point_locked:
            if app.lock_point_pos is None:
                raise AssertionError("mouse_point_locked requires lock_point_pos")
            if app.locking_object is None:
                raise AssertionError("mouse_point_locked requires locking_object")

    @staticmethod
    def _assert_drag_state_consistency(panel: PanelControl, app: GuiApplication) -> None:
        if panel._drag_window is None and panel._drag_last_pos is not None:
            raise AssertionError("drag last position must be cleared when no drag window exists")
        if panel._drag_window is not None and not app.pointer_capture.is_owned_by(panel._drag_window.control_id):
            raise AssertionError("active drag window must own pointer capture")

    @staticmethod
    def _click(app: GuiApplication, pos: tuple[int, int]) -> None:
        app.process_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": pos, "button": 1}))
        app.process_event(pygame.event.Event(pygame.MOUSEBUTTONUP, {"pos": pos, "button": 1}))

    def test_click_and_lock_transition_permutations_preserve_invariants(self) -> None:
        operation_names = ["lock_point_a", "unlock_point", "click_a", "click_bg", "lock_area", "unlock_area"]

        for sequence in itertools.permutations(operation_names, 3):
            with self.subTest(sequence=sequence):
                app, _root, win_a, win_b = self._new_runtime()
                title_anchor = win_a.title_bar_rect().center
                for op_name in sequence:
                    if op_name == "lock_point_a":
                        app.set_lock_point(win_a, title_anchor)
                    elif op_name == "unlock_point":
                        app.set_lock_point(None)
                    elif op_name == "lock_area":
                        app.set_lock_area(Rect(0, 0, 140, 120))
                    elif op_name == "unlock_area":
                        app.set_lock_area(None)
                    elif op_name == "click_a":
                        self._click(app, title_anchor)
                        self.assertEqual(self._active_id(win_a, win_b), "a")
                    elif op_name == "click_bg":
                        self._click(app, (5, 5))
                        expected = "a" if app.mouse_point_locked else None
                        self.assertEqual(self._active_id(win_a, win_b), expected)
                    else:
                        raise AssertionError(f"unknown operation: {op_name}")

                    self._assert_lock_state_sane(app)
                    self._assert_activation_invariants(win_a, win_b)

    def test_drag_lifecycle_under_lock_point_and_lock_area(self) -> None:
        app, root, win_a, win_b = self._new_runtime()
        title_anchor = win_a.title_bar_rect().center

        app.set_lock_area(Rect(0, 0, 150, 110))
        app.set_lock_point(win_a, title_anchor)

        app.process_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": (490, 350), "button": 1}))
        self.assertEqual(app.pointer_capture.owner_id, "a")
        self.assertEqual(self._active_id(win_a, win_b), "a")

        app.process_event(
            pygame.event.Event(
                pygame.MOUSEMOTION,
                {"pos": (490, 350), "rel": (20, 12), "buttons": (1, 0, 0)},
            )
        )
        self.assertEqual(app.input_state.pointer_pos, title_anchor)

        app.set_lock_point(None)
        app.process_event(
            pygame.event.Event(
                pygame.MOUSEMOTION,
                {"pos": (490, 350), "rel": (10, 6), "buttons": (1, 0, 0)},
            )
        )
        self.assertEqual(app.input_state.pointer_pos, (149, 109))

        app.process_event(pygame.event.Event(pygame.MOUSEBUTTONUP, {"pos": (490, 350), "button": 1}))
        self.assertIsNone(app.pointer_capture.owner_id)
        self.assertIsNone(root._drag_window)
        self.assertIsNone(root._drag_last_pos)
        self._assert_activation_invariants(win_a, win_b)

    def test_lock_and_drag_transition_permutations_cleanup_capture(self) -> None:
        operation_names = ["hide_a", "disable_a", "remove_a", "unlock_point", "unlock_area"]

        for sequence in itertools.permutations(operation_names, 2):
            with self.subTest(sequence=sequence):
                app, root, win_a, win_b = self._new_runtime()
                title_anchor = win_a.title_bar_rect().center
                app.set_lock_area(Rect(0, 0, 150, 110))
                app.set_lock_point(win_a, title_anchor)

                app.process_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": (490, 350), "button": 1}))
                self.assertEqual(app.pointer_capture.owner_id, "a")
                self.assertEqual(self._active_id(win_a, win_b), "a")

                for op_name in sequence:
                    if op_name == "hide_a":
                        win_a.visible = False
                    elif op_name == "disable_a":
                        win_a.enabled = False
                    elif op_name == "remove_a":
                        self.assertTrue(root.remove(win_a))
                    elif op_name == "unlock_point":
                        app.set_lock_point(None)
                    elif op_name == "unlock_area":
                        app.set_lock_area(None)
                    else:
                        raise AssertionError(f"unknown operation: {op_name}")

                    self._assert_lock_state_sane(app)
                    self._assert_activation_invariants(win_a, win_b)
                    self._assert_drag_state_consistency(root, app)

                app.process_event(
                    pygame.event.Event(
                        pygame.MOUSEMOTION,
                        {"pos": (5, 5), "rel": (0, 0), "buttons": (0, 0, 0)},
                    )
                )
                app.process_event(pygame.event.Event(pygame.MOUSEBUTTONUP, {"pos": (5, 5), "button": 1}))

                self.assertIsNone(app.pointer_capture.owner_id)
                self._assert_lock_state_sane(app)
                self._assert_activation_invariants(win_a, win_b)
                self._assert_drag_state_consistency(root, app)

    def test_scene_switch_during_locked_drag_preserves_and_then_releases_capture(self) -> None:
        app, root_life, win_a_life, win_b_life = self._new_runtime()
        app.create_scene("mandel")
        root_mandel = app.add(PanelControl("root_mandel", Rect(0, 0, 500, 360)), scene_name="mandel")
        win_mandel = root_mandel.add(WindowControl("m", Rect(80, 80, 160, 120), "M"))
        win_mandel.active = True

        title_anchor = win_a_life.title_bar_rect().center
        app.set_lock_area(Rect(0, 0, 150, 110))
        app.set_lock_point(win_a_life, title_anchor)
        app.process_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": (490, 350), "button": 1}))

        self.assertEqual(app.pointer_capture.owner_id, "a")
        self.assertEqual(self._active_id(win_a_life, win_b_life), "a")
        self._assert_drag_state_consistency(root_life, app)

        app.switch_scene("mandel")
        self.assertEqual(app.active_scene_name, "mandel")
        self.assertEqual(app.pointer_capture.owner_id, "a")

        self._click(app, (5, 5))
        self.assertIsNone(self._active_id(win_mandel))
        self.assertEqual(app.pointer_capture.owner_id, "a")

        app.switch_scene("default")
        app.set_lock_point(None)
        app.set_lock_area(None)
        app.process_event(pygame.event.Event(pygame.MOUSEBUTTONUP, {"pos": title_anchor, "button": 1}))

        self.assertIsNone(app.pointer_capture.owner_id)
        self.assertIsNone(root_life._drag_window)
        self.assertIsNone(root_life._drag_last_pos)
        self._assert_activation_invariants(win_a_life, win_b_life)

    def test_scene_switch_with_hidden_dragged_window_releases_after_return_flush(self) -> None:
        app, root_life, win_a_life, win_b_life = self._new_runtime()
        app.create_scene("mandel")
        app.add(PanelControl("root_mandel", Rect(0, 0, 500, 360)), scene_name="mandel")

        title_anchor = win_a_life.title_bar_rect().center
        app.set_lock_point(win_a_life, title_anchor)
        app.process_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": (490, 350), "button": 1}))
        self.assertEqual(app.pointer_capture.owner_id, "a")

        app.switch_scene("mandel")
        win_a_life.visible = False
        self.assertIsNone(root_life._drag_window)
        self.assertIsNone(root_life._drag_last_pos)
        self.assertEqual(app.pointer_capture.owner_id, "a")

        app.switch_scene("default")
        app.process_event(pygame.event.Event(pygame.MOUSEMOTION, {"pos": (5, 5), "rel": (0, 0), "buttons": (0, 0, 0)}))
        app.set_lock_point(None)

        self.assertIsNone(app.pointer_capture.owner_id)
        self.assertIsNone(root_life._drag_window)
        self.assertIsNone(root_life._drag_last_pos)
        self._assert_activation_invariants(win_a_life, win_b_life)


if __name__ == "__main__":
    unittest.main()
