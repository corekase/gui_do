import unittest
from types import SimpleNamespace

from pygame import Rect

from gui_do.controls.chrome.scene_menu_strip_control import SceneMenuStripControl


class _WindowStub:
    def __init__(self, control_id: str, title: str, visible: bool = False) -> None:
        self.control_id = control_id
        self.title = title
        self.visible = visible

    @staticmethod
    def is_window() -> bool:
        return True


class _SceneStub:
    def __init__(self, windows) -> None:
        self._windows = list(windows)

    def _walk_nodes(self):
        return list(self._windows)


class _AppStub:
    def __init__(self, scene) -> None:
        self.scene = scene
        self.active_scene_name = "main"
        self.features = SimpleNamespace(_features={}, _feature_hosts={})
        self._pretty_names = {"main": "Desktop Demo"}

    @staticmethod
    def scene_names():
        return ["main"]

    def scene_pretty_name(self, name: str) -> str:
        return self._pretty_names.get(name, name)


class SceneMenuStripControlWindowOrderRuntimeTests(unittest.TestCase):
    @staticmethod
    def _window_item_labels(control: SceneMenuStripControl):
        for entry in control.entries:
            if entry.label == "Windows":
                return [item.label for item in entry.items]
        return []

    def test_window_menu_order_is_stable_when_scene_walk_order_changes(self) -> None:
        life = _WindowStub("life_window", "Life")
        mandel = _WindowStub("mandel_window", "Mandelbrot")
        system = _WindowStub("system_window", "System")
        scene = _SceneStub([life, mandel, system])
        app = _AppStub(scene)

        control = SceneMenuStripControl(
            "menu",
            Rect(0, 0, 400, 28),
            app,
            scenes_shown=False,
            windows_shown=True,
            on_window_toggled=lambda _window, _visible: None,
        )

        initial = self._window_item_labels(control)
        self.assertEqual(initial, ["[ ] Life", "[ ] Mandelbrot", "[ ] System"])

        control._toggle_window(mandel)
        # Simulate runtime z-order or node-list changes after toggle.
        scene._windows = [life, system, mandel]
        control.refresh_entries()

        after = self._window_item_labels(control)
        self.assertEqual(after, ["[ ] Life", "[x] Mandelbrot", "[ ] System"])

    def test_scene_items_use_pretty_name_label(self) -> None:
        scene = _SceneStub([])
        app = _AppStub(scene)

        control = SceneMenuStripControl(
            "menu",
            Rect(0, 0, 400, 28),
            app,
            scenes_shown=True,
            windows_shown=False,
        )

        labels = []
        for entry in control.entries:
            if entry.label == "Scenes":
                labels = [item.label for item in entry.items]
                break
        self.assertEqual(labels, ["* Desktop Demo"])


if __name__ == "__main__":
    unittest.main()
