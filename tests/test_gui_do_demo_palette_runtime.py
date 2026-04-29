import unittest
from types import SimpleNamespace

from gui_do import CommandPaletteManager, OverlayManager


class _WindowStub:
    def __init__(self, control_id: str, title: str, visible: bool = False) -> None:
        self.control_id = control_id
        self.title = title
        self.visible = visible

    @staticmethod
    def is_window() -> bool:
        return True


class _SceneStub:
    def __init__(self, nodes) -> None:
        self._nodes = list(nodes)

    def _walk_nodes(self):
        return list(self._nodes)


class GuiDoDemoPaletteRuntimeTests(unittest.TestCase):
    def test_allowed_builtin_scene_names_excludes_active_and_scene_less_features(self) -> None:
        app = SimpleNamespace(
            scene_names=lambda: ["default", "main", "control_showcase"],
            active_scene_name="main",
            features=SimpleNamespace(
                _features={
                    "backdrop": SimpleNamespace(scene_name=None),
                    "main": SimpleNamespace(scene_name="main"),
                    "controls": SimpleNamespace(scene_name="control_showcase"),
                }
            ),
        )

        allowed = CommandPaletteManager._allowed_builtin_scene_names(app)

        self.assertEqual(allowed, ["control_showcase"])

    def test_builtin_window_entries_use_deterministic_order_even_if_initial_walk_order_is_scrambled(self) -> None:
        palette = CommandPaletteManager(OverlayManager())

        w1 = _WindowStub("life_window", "Life")
        w2 = _WindowStub("mandel_window", "Mandelbrot")
        w3 = _WindowStub("system_window", "System")
        scene = _SceneStub([w2, w3, w1])

        app = SimpleNamespace(
            scene_names=lambda: ["main"],
            scene_pretty_name=lambda name: "Desktop Demo" if name == "main" else name,
            active_scene_name="main",
            features=SimpleNamespace(_features={"main": SimpleNamespace(scene_name="main")}),
            scene=scene,
            tile_windows=lambda: None,
        )

        palette._register_builtin_scene_and_window_entries(app)
        initial_titles = [entry.title for entry in palette.entries() if entry.category == "Windows"]
        self.assertEqual(initial_titles, ["Life", "Mandelbrot", "System"])

        scene._nodes = [w3, w1, w2]
        palette._register_builtin_scene_and_window_entries(app)
        second_titles = [entry.title for entry in palette.entries() if entry.category == "Windows"]
        self.assertEqual(second_titles, ["Life", "Mandelbrot", "System"])

    def test_builtin_palette_selection_is_remembered_per_scene(self) -> None:
        palette = CommandPaletteManager(OverlayManager())
        app = SimpleNamespace(active_scene_name="main")

        palette._remember_selection_for_scene(app, SimpleNamespace(entry_id="window:main:life_window"))

        self.assertEqual(palette._selected_entry_id_for_scene(app), "window:main:life_window")


if __name__ == "__main__":
    unittest.main()
