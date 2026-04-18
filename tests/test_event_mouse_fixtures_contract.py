import unittest

from event_mouse_fixtures import build_mouse_gui_stub


class EventMouseFixturesContractTests(unittest.TestCase):
    def test_default_mouse_and_identity_converters(self) -> None:
        gui = build_mouse_gui_stub()

        self.assertEqual(gui.get_mouse_pos(), (0, 0))
        self.assertEqual(gui.convert_to_window((3, 4), None), (3, 4))
        self.assertEqual(gui.convert_to_screen((3, 4), None), (3, 4))

    def test_mouse_position_is_mutable_via_setter(self) -> None:
        gui = build_mouse_gui_stub(mouse_pos=(1, 2))

        self.assertEqual(gui.get_mouse_pos(), (1, 2))
        gui.set_mouse_pos((9, 8))
        self.assertEqual(gui.get_mouse_pos(), (9, 8))

    def test_optional_lock_area_and_extras_are_attached(self) -> None:
        calls = []
        gui = build_mouse_gui_stub(
            set_lock_area=lambda widget, area=None: calls.append((widget, area)),
            extras={"marker": 123},
        )

        self.assertEqual(gui.marker, 123)
        gui.set_lock_area("w", "a")
        self.assertEqual(calls, [("w", "a")])


if __name__ == "__main__":
    unittest.main()
