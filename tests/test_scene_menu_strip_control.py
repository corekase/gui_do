import unittest

import pygame
from pygame import Rect

from gui_do.controls.chrome.menu_bar_control import _FlyoutPanel
from gui_do.controls.chrome.scene_menu_strip_control import SceneMenuStripControl
from gui_do.features.feature_lifecycle import add_window_scene_menu_strip
from gui_do.overlays.context_menu_manager import ContextMenuItem


class _StubWindowNode:
    def __init__(self, control_id: str, title: str, visible: bool = False):
        self.control_id = str(control_id)
        self.title = str(title)
        self.visible = bool(visible)

    def is_window(self) -> bool:
        return True


class _StubPlainNode:
    def is_window(self) -> bool:
        return False


class _StubScene:
    def __init__(self, nodes):
        self._nodes = list(nodes)
        self.name = "main"

    def _walk_nodes(self):
        return list(self._nodes)


class _StubFeatures:
    def __init__(self):
        self._features = {}


class _StubApp:
    def __init__(self, scene=None):
        self.scene = scene
        self.active_scene_name = "main"
        self.features = _StubFeatures()

    def scene_names(self):
        return ["main", "control_showcase"]

    def scene_pretty_name(self, name: str) -> str:
        names = {
            "main": "Main",
            "control_showcase": "Control Showcase",
        }
        return names.get(name, str(name))


class _StubHost:
    def __init__(self, app):
        self.app = app


class _StubWindowContainer:
    def __init__(self):
        self.added = []

    def add(self, child):
        self.added.append(child)
        return child


class TestSceneMenuStripControl(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not pygame.get_init():
            pygame.init()
        if not pygame.font.get_init():
            pygame.font.init()

    def test_scene_menu_tracks_longest_label_for_flyout_width(self):
        app = _StubApp(scene=_StubScene([]))

        def _scene_items():
            return [
                ContextMenuItem("A"),
                ContextMenuItem("A very long scene display label that must fit"),
            ]

        menu = SceneMenuStripControl(
            "menu",
            Rect(0, 0, 500, 28),
            app,
            scenes_shown=True,
            scene_items_provider=_scene_items,
        )

        scenes_entry = next((entry for entry in menu.entries if entry.label == "Scenes"), None)
        self.assertIsNotNone(scenes_entry)
        self.assertIsNotNone(scenes_entry.flyout_min_width)
        self.assertGreater(scenes_entry.flyout_min_width, 140)

    def test_scene_menu_width_recomputes_when_discovery_changes(self):
        app = _StubApp(scene=_StubScene([]))
        state = {"long": True}

        def _scene_items():
            if state["long"]:
                return [ContextMenuItem("A very long scene display label that must fit")]
            return [ContextMenuItem("Short")]

        menu = SceneMenuStripControl(
            "menu",
            Rect(0, 0, 500, 28),
            app,
            scenes_shown=True,
            scene_items_provider=_scene_items,
        )

        first_entry = next((entry for entry in menu.entries if entry.label == "Scenes"), None)
        self.assertIsNotNone(first_entry)
        first_width = int(first_entry.flyout_min_width)

        state["long"] = False
        menu.refresh_entries()
        second_entry = next((entry for entry in menu.entries if entry.label == "Scenes"), None)
        self.assertIsNotNone(second_entry)
        second_width = int(second_entry.flyout_min_width)

        self.assertGreater(first_width, second_width)

    def test_regular_menu_width_is_automatic_from_items(self):
        items = [ContextMenuItem("Extremely long regular menu option label for auto sizing")]
        width, height = _FlyoutPanel.measure(items)

        self.assertGreater(width, 140)
        self.assertGreater(height, 0)

    def test_windows_menu_discovers_mandelbrot_window_without_built_in_setter(self):
        mandel_window = _StubWindowNode("mandelbrot_window", "Mandelbrot Demo", visible=False)
        scene = _StubScene([_StubPlainNode(), mandel_window])
        app = _StubApp(scene=scene)

        menu = SceneMenuStripControl(
            "menu",
            Rect(0, 0, 500, 28),
            app,
            scene_name="main",
            windows_shown=True,
        )

        windows_entry = next((entry for entry in menu.entries if entry.label == "Windows"), None)
        self.assertIsNotNone(windows_entry)
        labels = [item.label for item in windows_entry.items]
        self.assertIn("[ ] Mandelbrot Demo", labels)

    def test_windows_menu_action_calls_on_window_toggled_callback(self):
        systems_window = _StubWindowNode("systems_window", "Systems Demo", visible=False)
        scene = _StubScene([systems_window])
        app = _StubApp(scene=scene)
        callback_events = []

        menu = SceneMenuStripControl(
            "menu",
            Rect(0, 0, 500, 28),
            app,
            scene_name="main",
            windows_shown=True,
            on_window_toggled=lambda window, next_visible: callback_events.append((window.control_id, bool(next_visible))),
        )

        windows_entry = next((entry for entry in menu.entries if entry.label == "Windows"), None)
        self.assertIsNotNone(windows_entry)
        self.assertTrue(windows_entry.items)

        windows_entry.items[0].action()

        self.assertTrue(systems_window.visible)
        self.assertEqual([("systems_window", True)], callback_events)

    def test_add_window_scene_menu_strip_accepts_optional_scene_and_window_providers(self):
        app = _StubApp(scene=_StubScene([]))
        host = _StubHost(app)
        window = _StubWindowContainer()

        added = add_window_scene_menu_strip(
            window,
            host,
            control_id="menu",
            rect=Rect(0, 0, 600, 28),
            scene_name="main",
            on_minimize=lambda: None,
            scenes_shown=True,
            windows_shown=True,
            scene_items_provider=lambda: [ContextMenuItem("Custom Scene")],
            window_items_provider=lambda: [ContextMenuItem("Custom Window")],
        )

        self.assertIs(added, window.added[0])
        entries_by_label = {entry.label: entry for entry in added.entries}
        self.assertEqual(["Custom Scene"], [item.label for item in entries_by_label["Scenes"].items])
        self.assertEqual(["Custom Window"], [item.label for item in entries_by_label["Windows"].items])


if __name__ == "__main__":
    unittest.main()
