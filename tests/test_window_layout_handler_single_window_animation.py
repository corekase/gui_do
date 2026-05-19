import unittest
from unittest.mock import patch

from pygame import Rect

from gui_do.layout.window_layout_handler import WindowLayoutHandler


class _Surface:
    def __init__(self, rect: Rect):
        self._rect = Rect(rect)

    def get_rect(self) -> Rect:
        return Rect(self._rect)


class _Scene:
    def __init__(self, nodes):
        self.nodes = list(nodes)


class _WindowNode:
    def __init__(self, x: int, y: int, w: int, h: int, *, visible: bool = True):
        self.rect = Rect(x, y, w, h)
        self.visible = bool(visible)
        self.children = []
        self.parent = None

    def is_window(self) -> bool:
        return True

    def is_task_panel(self) -> bool:
        return False

    def move_by(self, dx: int, dy: int) -> None:
        self.rect = self.rect.move(int(dx), int(dy))


class _App:
    def __init__(self, surface_rect: Rect, scene):
        self.surface = _Surface(surface_rect)
        self.scene = scene


class TestWindowLayoutHandlerSingleWindowAnimation(unittest.TestCase):
    def test_single_window_standard_relayout_uses_animation(self):
        window = _WindowNode(0, 0, 120, 90, visible=True)
        scene = _Scene([window])
        app = _App(Rect(0, 0, 400, 300), scene)
        handler = WindowLayoutHandler(app, scene=scene)
        handler.enabled = True

        with patch.object(handler, "_animate_window_to") as animate_mock:
            handler.arrange_windows()

        animate_mock.assert_called_once()

    def test_single_window_immediate_relayout_moves_without_animation(self):
        window = _WindowNode(0, 0, 120, 90, visible=True)
        scene = _Scene([window])
        app = _App(Rect(0, 0, 400, 300), scene)
        handler = WindowLayoutHandler(app, scene=scene)
        handler.enabled = True

        with patch.object(handler, "_animate_window_to") as animate_mock:
            handler.arrange_windows(include_hidden=True, immediate=True)

        animate_mock.assert_not_called()
        self.assertNotEqual((window.rect.x, window.rect.y), (0, 0))


if __name__ == "__main__":
    unittest.main()
