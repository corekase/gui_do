"""Tests for Router and RouteEntry from state.router."""
import unittest

from gui_do.state.router import Router, RouteEntry


# ===========================================================================
# RouteEntry dataclass
# ===========================================================================


class TestRouteEntry(unittest.TestCase):
    def test_route_stored(self):
        entry = RouteEntry(route="/home")
        self.assertEqual("/home", entry.route)

    def test_params_default_empty(self):
        entry = RouteEntry(route="/home")
        self.assertEqual({}, entry.params)

    def test_params_stored(self):
        entry = RouteEntry(route="/editor", params={"id": 42})
        self.assertEqual({"id": 42}, entry.params)


# ===========================================================================
# Router — initial state
# ===========================================================================


class TestRouterInitial(unittest.TestCase):
    def test_current_route_none(self):
        r = Router()
        self.assertIsNone(r.current_route)

    def test_current_params_empty(self):
        r = Router()
        self.assertEqual({}, r.current_params)

    def test_history_empty(self):
        r = Router()
        self.assertEqual(0, len(r.history))


# ===========================================================================
# Router.register
# ===========================================================================


class TestRouterRegister(unittest.TestCase):
    def test_register_valid(self):
        r = Router()
        r.register("/home", "home_scene")  # should not raise

    def test_register_empty_route_raises(self):
        r = Router()
        with self.assertRaises(ValueError):
            r.register("", "home_scene")

    def test_register_empty_scene_raises(self):
        r = Router()
        with self.assertRaises(ValueError):
            r.register("/home", "")


# ===========================================================================
# Router.push
# ===========================================================================


class TestRouterPush(unittest.TestCase):
    def test_push_returns_true(self):
        r = Router()
        r.register("/home", "home_scene")
        self.assertTrue(r.push("/home"))

    def test_push_updates_current_route(self):
        r = Router()
        r.register("/home", "home_scene")
        r.push("/home")
        self.assertEqual("/home", r.current_route)

    def test_push_stores_params(self):
        r = Router()
        r.register("/editor", "editor_scene")
        r.push("/editor", params={"id": 7})
        self.assertEqual({"id": 7}, r.current_params)

    def test_push_adds_to_history(self):
        r = Router()
        r.register("/home", "home_scene")
        r.register("/editor", "editor_scene")
        r.push("/home")
        r.push("/editor")
        self.assertEqual(2, len(r.history))

    def test_push_fires_on_route_change(self):
        r = Router()
        r.register("/home", "home_scene")
        changes = []
        r.on_route_change(lambda e: changes.append(e.route))
        r.push("/home")
        self.assertEqual(["/home"], changes)

    def test_push_blocked_by_guard(self):
        r = Router()
        r.register("/home", "home_scene")
        r.add_guard(lambda f, t, p: False)
        result = r.push("/home")
        self.assertFalse(result)
        self.assertIsNone(r.current_route)


# ===========================================================================
# Router.pop
# ===========================================================================


class TestRouterPop(unittest.TestCase):
    def test_pop_single_entry_returns_false(self):
        r = Router()
        r.register("/home", "home_scene")
        r.push("/home")
        self.assertFalse(r.pop())

    def test_pop_two_entries_returns_true(self):
        r = Router()
        r.register("/home", "home_scene")
        r.register("/editor", "editor_scene")
        r.push("/home")
        r.push("/editor")
        self.assertTrue(r.pop())

    def test_pop_restores_previous_route(self):
        r = Router()
        r.register("/home", "home_scene")
        r.register("/editor", "editor_scene")
        r.push("/home")
        r.push("/editor")
        r.pop()
        self.assertEqual("/home", r.current_route)

    def test_pop_decrements_history(self):
        r = Router()
        r.register("/home", "home_scene")
        r.register("/editor", "editor_scene")
        r.push("/home")
        r.push("/editor")
        r.pop()
        self.assertEqual(1, len(r.history))


# ===========================================================================
# Router.replace
# ===========================================================================


class TestRouterReplace(unittest.TestCase):
    def test_replace_returns_true(self):
        r = Router()
        r.register("/home", "home_scene")
        r.register("/editor", "editor_scene")
        r.push("/home")
        self.assertTrue(r.replace("/editor"))

    def test_replace_changes_current_route(self):
        r = Router()
        r.register("/home", "home_scene")
        r.register("/editor", "editor_scene")
        r.push("/home")
        r.replace("/editor")
        self.assertEqual("/editor", r.current_route)

    def test_replace_does_not_grow_history(self):
        r = Router()
        r.register("/home", "home_scene")
        r.register("/editor", "editor_scene")
        r.push("/home")
        r.replace("/editor")
        self.assertEqual(1, len(r.history))


# ===========================================================================
# Router.on_route_change
# ===========================================================================


class TestRouterOnRouteChange(unittest.TestCase):
    def test_callback_receives_route_entry(self):
        r = Router()
        r.register("/home", "home_scene")
        entries = []
        r.on_route_change(lambda e: entries.append(e))
        r.push("/home")
        self.assertEqual(1, len(entries))
        self.assertIsInstance(entries[0], RouteEntry)

    def test_unsub_removes_callback(self):
        r = Router()
        r.register("/home", "home_scene")
        changes = []
        unsub = r.on_route_change(lambda e: changes.append(e.route))
        unsub()
        r.push("/home")
        self.assertEqual([], changes)


# ===========================================================================
# Router guards
# ===========================================================================


class TestRouterGuards(unittest.TestCase):
    def test_guard_allows_navigation(self):
        r = Router()
        r.register("/home", "home_scene")
        r.add_guard(lambda f, t, p: True)
        self.assertTrue(r.push("/home"))

    def test_multiple_guards_all_must_pass(self):
        r = Router()
        r.register("/home", "home_scene")
        r.add_guard(lambda f, t, p: True)
        r.add_guard(lambda f, t, p: False)
        self.assertFalse(r.push("/home"))

    def test_guard_receives_from_to(self):
        r = Router()
        r.register("/home", "home_scene")
        r.register("/editor", "editor_scene")
        received = []
        r.add_guard(lambda f, t, p: received.append((f, t)) or True)
        r.push("/home")
        r.push("/editor")
        self.assertEqual([("", "/home"), ("/home", "/editor")], received)

    def test_non_callable_guard_raises(self):
        r = Router()
        with self.assertRaises(ValueError):
            r.add_guard("not callable")  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
