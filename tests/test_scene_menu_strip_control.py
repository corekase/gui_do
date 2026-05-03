import unittest

import pygame
from pygame import Rect

from gui_do.controls.chrome.menu_bar_control import _FlyoutPanel
from gui_do.controls.chrome.scene_menu_strip_control import SceneMenuStripControl
from gui_do.controls.base.ui_node import UiNode
from gui_do.events.gui_event import EventType, GuiEvent
from gui_do.focus.focus_manager import FocusManager
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


class _StubOverlay:
    def __init__(self):
        self.shown = []
        self.hidden = []

    def show(self, owner, panel, **kwargs):
        self.shown.append((owner, panel, kwargs))

    def hide(self, owner):
        self.hidden.append(owner)


class _StubApp:
    def __init__(self, scene=None):
        self.scene = scene
        self.active_scene_name = "main"
        self.features = _StubFeatures()
        self.overlay = _StubOverlay()
        self.surface = pygame.Surface((800, 600))

        class _Fonts:
            def scaled_size(self, scale):
                return int(16 * float(scale))

            def font_instance(self, _role, size=16):
                return pygame.font.SysFont(None, int(size))

        class _Theme:
            def __init__(self):
                self.fonts = _Fonts()
                self.text = (255, 255, 255)
                self.highlight = (90, 90, 90)
                self.panel = (30, 30, 30)
                self.border = (60, 60, 60)

        self.theme = _Theme()

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


class _DummyFocusable(UiNode):
    def __init__(self, control_id: str):
        super().__init__(control_id, Rect(0, 0, 10, 10))
        self.set_tab_index(1)


class _DummyTaskPanel(UiNode):
    def __init__(self, control_id: str = "task_panel"):
        super().__init__(control_id, Rect(0, 0, 100, 30))

    def is_task_panel(self) -> bool:
        return True


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

    def test_scene_menu_accepts_focus_for_tab_traversal(self):
        app = _StubApp(scene=_StubScene([]))
        menu = SceneMenuStripControl(
            "menu",
            Rect(0, 0, 500, 28),
            app,
            scene_items_provider=lambda: [ContextMenuItem("Main")],
            scenes_shown=True,
        )

        self.assertTrue(menu.accepts_focus())

    def test_scene_menu_keyboard_left_right_cycles_open_submenus(self):
        app = _StubApp(scene=_StubScene([]))

        menu = SceneMenuStripControl(
            "menu",
            Rect(0, 0, 500, 28),
            app,
            scene_items_provider=lambda: [ContextMenuItem("Main")],
            window_items_provider=lambda: [ContextMenuItem("Systems")],
            scenes_shown=True,
            windows_shown=True,
        )

        theme = app.theme

        consumed = menu.handle_event(
            GuiEvent(kind=EventType.KEY_DOWN, type=pygame.KEYDOWN, key=pygame.K_DOWN),
            app,
            theme=app.theme,
        )
        self.assertTrue(consumed)
        self.assertEqual(0, menu._open_index)

    def test_scene_menu_active_marker_updates_on_keyboard_open(self):
        app = _StubApp(scene=_StubScene([]))
        menu = SceneMenuStripControl(
            "menu",
            Rect(0, 0, 500, 28),
            app,
            scenes_shown=True,
        )

        app.active_scene_name = "control_showcase"
        consumed = menu.handle_event(
            GuiEvent(kind=EventType.KEY_DOWN, type=pygame.KEYDOWN, key=pygame.K_DOWN),
            app,
            theme=app.theme,
        )

        self.assertTrue(consumed)
        scenes_entry = next((entry for entry in menu.entries if entry.label == "Scenes"), None)
        self.assertIsNotNone(scenes_entry)
        labels = [item.label for item in scenes_entry.items]
        self.assertIn("* Control Showcase", labels)

    def test_windows_menu_state_updates_on_keyboard_open(self):
        window = _StubWindowNode("systems_window", "Systems Demo", visible=False)
        app = _StubApp(scene=_StubScene([window]))
        menu = SceneMenuStripControl(
            "menu",
            Rect(0, 0, 500, 28),
            app,
            scene_name="main",
            windows_shown=True,
        )

        window.visible = True
        consumed = menu.handle_event(
            GuiEvent(kind=EventType.KEY_DOWN, type=pygame.KEYDOWN, key=pygame.K_DOWN),
            app,
            theme=app.theme,
        )

        self.assertTrue(consumed)
        windows_entry = next((entry for entry in menu.entries if entry.label == "Windows"), None)
        self.assertIsNotNone(windows_entry)
        labels = [item.label for item in windows_entry.items]
        self.assertIn("[x] Systems Demo", labels)

    def test_open_windows_flyout_auto_refreshes_when_visibility_changes(self):
        window = _StubWindowNode("systems_window", "Systems Demo", visible=False)
        app = _StubApp(scene=_StubScene([window]))
        menu = SceneMenuStripControl(
            "menu",
            Rect(0, 0, 500, 28),
            app,
            scene_name="main",
            windows_shown=True,
        )

        consumed = menu.handle_event(
            GuiEvent(kind=EventType.KEY_DOWN, type=pygame.KEYDOWN, key=pygame.K_DOWN),
            app,
            theme=app.theme,
        )
        self.assertTrue(consumed)
        self.assertEqual(1, len(app.overlay.shown))

        window.visible = True
        menu.update(0.016)

        windows_entry = next((entry for entry in menu.entries if entry.label == "Windows"), None)
        self.assertIsNotNone(windows_entry)
        labels = [item.label for item in windows_entry.items]
        self.assertIn("[x] Systems Demo", labels)
        self.assertGreaterEqual(len(app.overlay.hidden), 1)
        self.assertGreaterEqual(len(app.overlay.shown), 2)

    def test_open_scenes_flyout_auto_refreshes_active_marker(self):
        app = _StubApp(scene=_StubScene([]))
        menu = SceneMenuStripControl(
            "menu",
            Rect(0, 0, 500, 28),
            app,
            scenes_shown=True,
        )

        consumed = menu.handle_event(
            GuiEvent(kind=EventType.KEY_DOWN, type=pygame.KEYDOWN, key=pygame.K_DOWN),
            app,
            theme=app.theme,
        )
        self.assertTrue(consumed)
        self.assertEqual(1, len(app.overlay.shown))

        app.active_scene_name = "control_showcase"
        menu.update(0.016)

        scenes_entry = next((entry for entry in menu.entries if entry.label == "Scenes"), None)
        self.assertIsNotNone(scenes_entry)
        labels = [item.label for item in scenes_entry.items]
        self.assertIn("* Control Showcase", labels)
        self.assertGreaterEqual(len(app.overlay.hidden), 1)
        self.assertGreaterEqual(len(app.overlay.shown), 2)

    def test_focus_manager_routes_menu_key_event_with_app_theme(self):
        class _FocusScene:
            def __init__(self, nodes):
                self.nodes = list(nodes)

            def _walk_nodes(self):
                queue = list(self.nodes)
                i = 0
                while i < len(queue):
                    node = queue[i]
                    i += 1
                    yield node
                    queue.extend(getattr(node, "children", ()))

        app = _StubApp()
        menu = SceneMenuStripControl(
            "menu",
            Rect(0, 0, 500, 28),
            app,
            scene_items_provider=lambda: [ContextMenuItem("Main")],
            scenes_shown=True,
        )
        app.scene = _FocusScene([menu])

        focus = FocusManager()
        focus.set_focus(menu)

        consumed = focus.route_key_event(
            GuiEvent(kind=EventType.KEY_DOWN, type=pygame.KEYDOWN, key=pygame.K_DOWN),
            app,
        )

        self.assertTrue(consumed)
        self.assertEqual(0, menu._open_index)

    def test_space_activates_highlighted_flyout_item(self):
        app = _StubApp(scene=_StubScene([]))
        calls = []
        menu = SceneMenuStripControl(
            "menu",
            Rect(0, 0, 500, 28),
            app,
            scene_items_provider=lambda: [ContextMenuItem("Main", action=lambda: calls.append("main"))],
            scenes_shown=True,
        )

        # Open first menu.
        consumed = menu.handle_event(
            GuiEvent(kind=EventType.KEY_DOWN, type=pygame.KEYDOWN, key=pygame.K_DOWN),
            app,
            theme=app.theme,
        )
        self.assertTrue(consumed)
        owner, panel, _ = app.overlay.shown[-1]
        self.assertIn("_menubar_menu_0", owner)

        # Highlight first selectable row and activate with Space.
        panel.handle_event(
            GuiEvent(kind=EventType.KEY_DOWN, type=pygame.KEYDOWN, key=pygame.K_DOWN),
            app,
            theme=app.theme,
        )
        consumed = panel.handle_event(
            GuiEvent(kind=EventType.KEY_DOWN, type=pygame.KEYDOWN, key=pygame.K_SPACE),
            app,
            theme=app.theme,
        )
        self.assertTrue(consumed)
        self.assertEqual(["main"], calls)

    def test_menu_flyout_closes_when_focus_moves_away(self):
        class _FocusScene:
            def __init__(self, nodes):
                self.nodes = list(nodes)

            def _walk_nodes(self):
                queue = list(self.nodes)
                i = 0
                while i < len(queue):
                    node = queue[i]
                    i += 1
                    yield node
                    queue.extend(getattr(node, "children", ()))

        app = _StubApp()
        menu = SceneMenuStripControl(
            "menu",
            Rect(0, 0, 500, 28),
            app,
            scene_items_provider=lambda: [ContextMenuItem("Main")],
            scenes_shown=True,
        )
        other = _DummyFocusable("other")
        app.scene = _FocusScene([menu, other])

        focus = FocusManager()
        focus.set_focus(menu)

        consumed = focus.route_key_event(
            GuiEvent(kind=EventType.KEY_DOWN, type=pygame.KEYDOWN, key=pygame.K_DOWN),
            app,
        )
        self.assertTrue(consumed)
        self.assertGreaterEqual(menu._open_index, 0)

        focus.set_focus(other)

        self.assertEqual(-1, menu._open_index)
        self.assertTrue(app.overlay.hidden)

    def test_normal_tab_candidates_exclude_task_panel_descendants(self):
        class _FocusScene:
            def __init__(self, nodes):
                self.nodes = list(nodes)

            def _walk_nodes(self):
                queue = list(self.nodes)
                i = 0
                while i < len(queue):
                    node = queue[i]
                    i += 1
                    yield node
                    queue.extend(getattr(node, "children", ()))

        focus = FocusManager()
        menu = _DummyFocusable("screen_menu")
        menu.set_tab_index(0)
        panel = _DummyTaskPanel()
        task_button = _DummyFocusable("task_button")
        task_button.parent = panel
        panel.children.append(task_button)
        scene = _FocusScene([menu, panel])

        self.assertEqual(1, focus.focusable_count(scene))

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
