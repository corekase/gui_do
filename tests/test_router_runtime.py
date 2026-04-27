import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from gui_do import Router, RouteEntry


class RouterRuntimeTests(unittest.TestCase):

    def setUp(self) -> None:
        pygame.init()
        self.router = Router()
        self.router.register("/home", "home_scene")
        self.router.register("/editor", "editor_scene")
        self.router.register("/settings", "settings_scene")

    def tearDown(self) -> None:
        pygame.quit()

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def test_register_empty_route_raises(self) -> None:
        with self.assertRaises(ValueError):
            self.router.register("", "scene")

    def test_register_empty_scene_raises(self) -> None:
        with self.assertRaises(ValueError):
            self.router.register("/home", "")

    def test_scene_for_returns_registered(self) -> None:
        self.assertEqual(self.router.scene_for("/home"), "home_scene")

    def test_scene_for_unknown_returns_none(self) -> None:
        self.assertIsNone(self.router.scene_for("/unknown"))

    # ------------------------------------------------------------------
    # push
    # ------------------------------------------------------------------

    def test_push_sets_current_route(self) -> None:
        self.router.push("/home")
        self.assertEqual(self.router.current_route, "/home")

    def test_push_returns_true(self) -> None:
        result = self.router.push("/home")
        self.assertTrue(result)

    def test_push_adds_to_history(self) -> None:
        self.router.push("/home")
        self.router.push("/editor")
        hist = self.router.history
        self.assertEqual([e.route for e in hist], ["/home", "/editor"])

    def test_push_passes_params(self) -> None:
        self.router.push("/editor", {"file": "test.py"})
        self.assertEqual(self.router.current_params, {"file": "test.py"})

    def test_push_blocked_by_guard(self) -> None:
        self.router.add_guard(lambda frm, to, p: False)
        result = self.router.push("/home")
        self.assertFalse(result)
        self.assertIsNone(self.router.current_route)

    def test_push_allowed_by_guard(self) -> None:
        self.router.add_guard(lambda frm, to, p: True)
        result = self.router.push("/home")
        self.assertTrue(result)

    # ------------------------------------------------------------------
    # pop
    # ------------------------------------------------------------------

    def test_pop_returns_false_when_empty(self) -> None:
        result = self.router.pop()
        self.assertFalse(result)

    def test_pop_returns_false_with_one_entry(self) -> None:
        self.router.push("/home")
        result = self.router.pop()
        self.assertFalse(result)

    def test_pop_goes_back(self) -> None:
        self.router.push("/home")
        self.router.push("/editor")
        result = self.router.pop()
        self.assertTrue(result)
        self.assertEqual(self.router.current_route, "/home")

    def test_pop_removes_history_entry(self) -> None:
        self.router.push("/home")
        self.router.push("/editor")
        self.router.pop()
        self.assertEqual(len(self.router.history), 1)

    def test_can_pop_false_when_empty(self) -> None:
        self.assertFalse(self.router.can_pop())

    def test_can_pop_true_after_two_pushes(self) -> None:
        self.router.push("/home")
        self.router.push("/editor")
        self.assertTrue(self.router.can_pop())

    # ------------------------------------------------------------------
    # replace
    # ------------------------------------------------------------------

    def test_replace_changes_current_without_growing_history(self) -> None:
        self.router.push("/home")
        self.router.replace("/editor")
        self.assertEqual(self.router.current_route, "/editor")
        self.assertEqual(len(self.router.history), 1)

    def test_replace_returns_true(self) -> None:
        self.router.push("/home")
        result = self.router.replace("/editor")
        self.assertTrue(result)

    def test_replace_blocked_by_guard(self) -> None:
        self.router.push("/home")
        self.router.add_guard(lambda frm, to, p: False)
        result = self.router.replace("/editor")
        self.assertFalse(result)
        self.assertEqual(self.router.current_route, "/home")

    def test_replace_on_empty_history_adds_entry(self) -> None:
        self.router.replace("/home")
        self.assertEqual(self.router.current_route, "/home")
        self.assertEqual(len(self.router.history), 1)

    # ------------------------------------------------------------------
    # on_route_change
    # ------------------------------------------------------------------

    def test_on_route_change_fires_on_push(self) -> None:
        events = []
        self.router.on_route_change(lambda e: events.append(e.route))
        self.router.push("/home")
        self.assertEqual(events, ["/home"])

    def test_on_route_change_fires_on_pop(self) -> None:
        self.router.push("/home")
        self.router.push("/editor")
        events = []
        self.router.on_route_change(lambda e: events.append(e.route))
        self.router.pop()
        self.assertEqual(events, ["/home"])

    def test_unsubscribe_stops_callbacks(self) -> None:
        events = []
        unsub = self.router.on_route_change(lambda e: events.append(e.route))
        self.router.push("/home")
        unsub()
        self.router.push("/editor")
        self.assertEqual(events, ["/home"])

    def test_add_guard_non_callable_raises(self) -> None:
        with self.assertRaises(ValueError):
            self.router.add_guard("not_callable")  # type: ignore

    # ------------------------------------------------------------------
    # RouteEntry
    # ------------------------------------------------------------------

    def test_route_entry_defaults(self) -> None:
        entry = RouteEntry(route="/test")
        self.assertEqual(entry.route, "/test")
        self.assertEqual(entry.params, {})

    def test_current_params_returns_copy(self) -> None:
        self.router.push("/home", {"x": 1})
        params = self.router.current_params
        params["x"] = 999
        self.assertEqual(self.router.current_params["x"], 1)

    def test_history_returns_copy(self) -> None:
        self.router.push("/home")
        h = self.router.history
        h.clear()
        self.assertEqual(len(self.router.history), 1)


if __name__ == "__main__":
    unittest.main()
