import unittest

from pygame import Rect

from demo_features.life.life_feature import LifeFeature


class _StubPacket:
    def __init__(self, *, is_down: bool = True, local_pos=None, pos=None):
        self._is_down = bool(is_down)
        self.local_pos = local_pos
        self.pos = pos

    def is_mouse_down(self, button: int) -> bool:
        return int(button) == 1 and self._is_down


class _StubCanvasSurface:
    def __init__(self):
        self.fill_calls = []

    def fill(self, color, rect=None):
        self.fill_calls.append((color, rect))


class _StubCanvas:
    def __init__(self, packets):
        self._packets = list(packets)
        self.rect = Rect(0, 0, 200, 160)
        self.canvas = _StubCanvasSurface()

    def read_event(self):
        if not self._packets:
            return None
        return self._packets.pop(0)


class _StubTheme:
    def __init__(self):
        self.medium = (10, 20, 30)


class _StubApp:
    def __init__(self):
        self.theme = _StubTheme()


class _StubDemo:
    def __init__(self):
        self.app = _StubApp()


class _StubToggle:
    def __init__(self, pushed: bool):
        self.pushed = bool(pushed)


class TestLifeDemoFeatureAbstractions(unittest.TestCase):
    def test_update_life_frame_core_toggles_cell_from_local_point(self):
        feature = LifeFeature()
        feature.life_cells = set()
        feature.life_origin = [0.0, 0.0]
        feature.life_cell_size = 10
        sent = []
        feature._send_life_logic_command = lambda command, **extra: sent.append((command, extra))

        canvas = _StubCanvas([_StubPacket(local_pos=(20, 10))])
        feature._update_life_frame_core(_StubDemo(), canvas, _StubToggle(False))

        self.assertIn((2, 1), feature.life_cells)
        self.assertIn(("toggle_cell", {"cell": (2, 1)}), sent)

    def test_update_life_frame_core_steps_when_toggle_pushed(self):
        feature = LifeFeature()
        feature.life_cells = {(0, 0), (1, 0), (-1, 0), (0, -1), (1, -2)}
        feature.life_origin = [0.0, 0.0]
        feature.life_cell_size = 12
        sent = []
        feature._send_life_logic_command = lambda command, **extra: sent.append((command, extra))

        canvas = _StubCanvas([])
        feature._update_life_frame_core(_StubDemo(), canvas, _StubToggle(True))

        self.assertTrue(any(command == "next" for command, _ in sent))
        self.assertGreaterEqual(len(canvas.canvas.fill_calls), 1)


if __name__ == "__main__":
    unittest.main()
