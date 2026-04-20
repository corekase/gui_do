import unittest

from pygame import Rect

from gui.utility.geometry import (
    clamp_point_to_rect,
    point_in_rect,
    to_screen,
    to_window,
    validate_point,
)


class _WindowStub:
    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y


class _PanelStub:
    def __init__(self, left: int, top: int) -> None:
        self.left = left
        self.top = top


class GeometryContractTests(unittest.TestCase):
    def test_validate_point_accepts_int_tuple(self) -> None:
        self.assertEqual(validate_point((2, 3)), (2, 3))

    def test_validate_point_rejects_non_int_values(self) -> None:
        with self.assertRaises(ValueError):
            validate_point((1.0, 2))  # type: ignore[arg-type]

    def test_clamp_point_to_rect_uses_inclusive_right_bottom(self) -> None:
        rect = Rect(10, 20, 5, 4)
        self.assertEqual(clamp_point_to_rect((99, 99), rect), (14, 23))
        self.assertEqual(clamp_point_to_rect((9, 19), rect), (10, 20))

    def test_point_in_rect_matches_pygame_bounds(self) -> None:
        rect = Rect(10, 20, 5, 4)
        self.assertTrue(point_in_rect((10, 20), rect))
        self.assertTrue(point_in_rect((14, 23), rect))
        self.assertFalse(point_in_rect((15, 23), rect))
        self.assertFalse(point_in_rect((14, 24), rect))

    def test_to_window_and_to_screen_round_trip(self) -> None:
        window = _WindowStub(100, 50)
        local = (7, 9)
        screen = to_screen(local, window)
        self.assertEqual(screen, (107, 59))
        self.assertEqual(to_window(screen, window), local)

    def test_to_window_and_to_screen_support_left_top(self) -> None:
        panel = _PanelStub(30, 40)
        local = (1, 2)
        screen = to_screen(local, panel)
        self.assertEqual(screen, (31, 42))
        self.assertEqual(to_window(screen, panel), local)


if __name__ == "__main__":
    unittest.main()
