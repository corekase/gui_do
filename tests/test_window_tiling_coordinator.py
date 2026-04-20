import unittest
from types import SimpleNamespace

from pygame import Rect

from gui.utility.coordinators.window_tiling_coordinator import WindowTilingCoordinator
from gui.utility.events import GuiError


class WindowStub:
    def __init__(self, x: int, y: int, width: int, height: int, titlebar_size: int = 20, visible: bool = True) -> None:
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.titlebar_size = titlebar_size
        self.visible = visible

    @property
    def position(self):
        return (self.x, self.y)

    @position.setter
    def position(self, pos):
        self.x, self.y = pos


class WindowTilingCoordinatorTests(unittest.TestCase):
    def _build_gui_stub(self, width: int = 800, height: int = 600):
        return SimpleNamespace(
            surface=SimpleNamespace(get_rect=lambda: Rect(0, 0, width, height)),
            task_panel=None,
            windows=[],
        )

    def test_arrange_windows_tiles_non_overlapping_when_capacity_allows(self) -> None:
        gui = self._build_gui_stub()
        w1 = WindowStub(100, 100, 260, 220)
        w2 = WindowStub(150, 140, 260, 220)
        gui.windows = [w1, w2]
        tiler = WindowTilingCoordinator(gui)

        tiler.set_enabled(True)
        r1 = Rect(w1.x, w1.y - w1.titlebar_size, w1.width, w1.height + w1.titlebar_size)
        r2 = Rect(w2.x, w2.y - w2.titlebar_size, w2.width, w2.height + w2.titlebar_size)

        self.assertFalse(r1.colliderect(r2))

    def test_arrange_windows_centers_single_visible_window(self) -> None:
        gui = self._build_gui_stub()
        w1 = WindowStub(40, 80, 260, 220)
        gui.windows = [w1]
        tiler = WindowTilingCoordinator(gui)

        tiler.set_enabled(True)

        centered = Rect(0, 0, w1.width, w1.height + w1.titlebar_size)
        centered.center = gui.surface.get_rect().center
        self.assertEqual(w1.position, (centered.x, centered.y + w1.titlebar_size))

    def test_arrange_windows_keeps_existing_window_close_when_new_window_appears(self) -> None:
        gui = self._build_gui_stub()
        w1 = WindowStub(30, 200, 220, 180)
        w2 = WindowStub(400, 200, 220, 180)
        gui.windows = [w1, w2]
        tiler = WindowTilingCoordinator(gui)

        tiler.set_enabled(True)
        before_dx = w2.x - w1.x
        before_dy = w2.y - w1.y

        w3 = WindowStub(500, 200, 220, 180)
        gui.windows.append(w3)
        tiler.on_window_registered(w3)

        after_dx = w2.x - w1.x
        after_dy = w2.y - w1.y
        self.assertEqual(after_dx, before_dx)
        self.assertEqual(after_dy, before_dy)

        occupied = [
            Rect(window.x, window.y - window.titlebar_size, window.width, window.height + window.titlebar_size)
            for window in (w1, w2, w3)
        ]
        occupied_bounds = occupied[0].unionall(occupied[1:])
        self.assertEqual(occupied_bounds.center, gui.surface.get_rect().center)

    def test_arrange_windows_centers_new_window_when_non_overlapping_layout_cannot_fit(self) -> None:
        gui = self._build_gui_stub(width=220, height=160)
        w1 = WindowStub(10, 30, 140, 120)
        w2 = WindowStub(20, 35, 140, 120)
        gui.windows = [w1, w2]
        tiler = WindowTilingCoordinator(gui)
        tiler.padding = 16
        tiler.gap = 16

        tiler.set_enabled(True, relayout=False)
        before_w1 = w1.position
        tiler.on_window_visibility_changed(w2, True)

        self.assertEqual(w1.position, before_w1)
        centered_rect = Rect(0, 0, w2.width, w2.height + w2.titlebar_size)
        centered_rect.center = gui.surface.get_rect().center
        self.assertEqual(w2.position, (centered_rect.x, centered_rect.y + w2.titlebar_size))

    def test_visibility_change_relayouts_and_centers_remaining_window(self) -> None:
        gui = self._build_gui_stub()
        w1 = WindowStub(30, 120, 220, 180)
        w2 = WindowStub(410, 120, 220, 180)
        gui.windows = [w1, w2]
        tiler = WindowTilingCoordinator(gui)

        tiler.set_enabled(True)
        w2.visible = False
        tiler.on_window_visibility_changed(w2, False)

        centered = Rect(0, 0, w1.width, w1.height + w1.titlebar_size)
        centered.center = gui.surface.get_rect().center
        self.assertEqual(w1.position, (centered.x, centered.y + w1.titlebar_size))

    def test_configure_validates_runtime_values(self) -> None:
        gui = self._build_gui_stub()
        tiler = WindowTilingCoordinator(gui)

        with self.assertRaises(GuiError):
            tiler.configure(gap=-1)
        with self.assertRaises(GuiError):
            tiler.configure(padding=-1)
        with self.assertRaises(GuiError):
            tiler.configure(avoid_task_panel=1)  # type: ignore[arg-type]
        with self.assertRaises(GuiError):
            tiler.configure(center_on_failure=1)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
