import unittest

import pygame
from pygame import Rect

from gui_do.controls.chrome.menu_bar_control import _FlyoutPanel
from gui_do.controls.chrome.menu_bar_control import MenuEntry, MenuStripControl, SceneMenuOptions, WindowMenuOptions
from gui_do.controls.base.ui_node import UiNode
from gui_do.events.gui_event import EventType, GuiEvent
from gui_do.focus.focus_manager import FocusManager
from gui_do.features.feature_lifecycle import add_window_menu_strip
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
        self.locking_object = None
        self.mouse_point_locked = False
        self.lock_point_pos = None

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


class _StubWindowPresentationMenuSource:
    def __init__(self, windows):
        self._windows = tuple(windows)

    def menu_windows(self, *, scene_name=None):
        _ = scene_name
        pairs = []
        for index, window in enumerate(self._windows, start=1):
            binding = type("_Binding", (), {"key": f"k{index}", "task_panel_slot_index": index})()
            pairs.append((binding, window))
        return tuple(pairs)


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


class TestMenuStripControl(unittest.TestCase):
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

        menu = MenuStripControl(
            "menu",
            app=app,
            scene_menu=SceneMenuOptions(shown=True),
            scene_items_provider=_scene_items,
        )

        scenes_entry = next((entry for entry in menu.entries if entry.label == "Scene"), None)
        self.assertIsNotNone(scenes_entry)
        self.assertIsNotNone(scenes_entry.flyout_min_width)
        self.assertGreater(scenes_entry.flyout_min_width, 140)

    def test_scene_menu_accepts_focus_for_tab_traversal(self):
        app = _StubApp(scene=_StubScene([]))
        menu = MenuStripControl(
            "menu",
            app=app,
            scene_items_provider=lambda: [ContextMenuItem("Main")],
            scene_menu=SceneMenuOptions(shown=True),
        )

        self.assertTrue(menu.accepts_focus())

    def test_scene_menu_keyboard_left_right_cycles_open_submenus(self):
        app = _StubApp(scene=_StubScene([]))

        menu = MenuStripControl(
            "menu",
            app=app,
            scene_items_provider=lambda: [ContextMenuItem("Main")],
            window_items_provider=lambda: [ContextMenuItem("Systems")],
            scene_menu=SceneMenuOptions(shown=True),
            window_menu=WindowMenuOptions(shown=True),
        )

        app.theme

        consumed = menu.handle_event(
            GuiEvent(kind=EventType.KEY_DOWN, type=pygame.KEYDOWN, key=pygame.K_DOWN),
            app=app,
            theme=app.theme,
        )
        self.assertTrue(consumed)
        self.assertEqual(0, menu._open_index)

    def test_scene_menu_active_marker_updates_on_keyboard_open(self):
        app = _StubApp(scene=_StubScene([]))
        menu = MenuStripControl(
            "menu",
            app=app,
            scene_menu=SceneMenuOptions(shown=True),
        )

        app.active_scene_name = "control_showcase"
        consumed = menu.handle_event(
            GuiEvent(kind=EventType.KEY_DOWN, type=pygame.KEYDOWN, key=pygame.K_DOWN),
            app=app,
            theme=app.theme,
        )

        self.assertTrue(consumed)
        scenes_entry = next((entry for entry in menu.entries if entry.label == "Scene"), None)
        self.assertIsNotNone(scenes_entry)
        labels = [item.label for item in scenes_entry.items]
        self.assertNotIn("Control Showcase", labels)
        self.assertIn("Main", labels)

    def test_windows_menu_state_updates_on_keyboard_open(self):
        window = _StubWindowNode("systems_window", "Systems Demo", visible=False)
        app = _StubApp(scene=_StubScene([window]))
        menu = MenuStripControl(
            "menu",
            app=app,
            scene_name="main",
            window_menu=WindowMenuOptions(shown=True),
        )

        window.visible = True
        consumed = menu.handle_event(
            GuiEvent(kind=EventType.KEY_DOWN, type=pygame.KEYDOWN, key=pygame.K_DOWN),
            app=app,
            theme=app.theme,
        )

        self.assertTrue(consumed)
        windows_entry = next((entry for entry in menu.entries if entry.label == "Window"), None)
        self.assertIsNotNone(windows_entry)
        labels = [item.label for item in windows_entry.items]
        self.assertIn("Systems Demo", labels)

    def test_windows_menu_uses_shared_presentation_source_order(self):
        scene_nodes = [
            _StubWindowNode("non_menu_window", "Non-Menu", visible=True),
            _StubWindowNode("systems_window", "Systems", visible=True),
            _StubWindowNode("life_window", "Conway's Game of Life", visible=True),
            _StubWindowNode("mandel_window", "Mandelbrot", visible=True),
        ]
        app = _StubApp(scene=_StubScene(scene_nodes))
        presentation = _StubWindowPresentationMenuSource(
            (
                scene_nodes[1],
                scene_nodes[2],
                scene_nodes[3],
            )
        )

        menu = MenuStripControl(
            "menu",
            app=app,
            scene_name="main",
            window_menu=WindowMenuOptions(shown=True),
            window_presentation=presentation,
        )

        windows_entry = next((entry for entry in menu.entries if entry.label == "Window"), None)
        self.assertIsNotNone(windows_entry)
        labels = [item.label for item in windows_entry.items]
        self.assertEqual(["Systems", "Conway's Game of Life", "Mandelbrot"], labels)

    def test_open_windows_flyout_auto_refreshes_when_visibility_changes(self):
        window = _StubWindowNode("systems_window", "Systems Demo", visible=False)
        app = _StubApp(scene=_StubScene([window]))
        menu = MenuStripControl(
            "menu",
            app=app,
            scene_name="main",
            window_menu=WindowMenuOptions(shown=True),
        )

        consumed = menu.handle_event(
            GuiEvent(kind=EventType.KEY_DOWN, type=pygame.KEYDOWN, key=pygame.K_DOWN),
            app=app,
            theme=app.theme,
        )
        self.assertTrue(consumed)
        self.assertEqual(1, len(app.overlay.shown))

        window.visible = True
        menu.update(0.016)

        windows_entry = next((entry for entry in menu.entries if entry.label == "Window"), None)
        self.assertIsNotNone(windows_entry)
        labels = [item.label for item in windows_entry.items]
        self.assertIn("Systems Demo", labels)
        self.assertGreaterEqual(len(app.overlay.hidden), 1)
        self.assertGreaterEqual(len(app.overlay.shown), 2)

    def test_open_scenes_flyout_auto_refreshes_current_scene_filtering(self):
        app = _StubApp(scene=_StubScene([]))
        menu = MenuStripControl(
            "menu",
            app=app,
            scene_menu=SceneMenuOptions(shown=True),
        )

        consumed = menu.handle_event(
            GuiEvent(kind=EventType.KEY_DOWN, type=pygame.KEYDOWN, key=pygame.K_DOWN),
            app=app,
            theme=app.theme,
        )
        self.assertTrue(consumed)
        self.assertEqual(1, len(app.overlay.shown))

        app.active_scene_name = "control_showcase"
        menu.update(0.016)

        scenes_entry = next((entry for entry in menu.entries if entry.label == "Scene"), None)
        self.assertIsNotNone(scenes_entry)
        labels = [item.label for item in scenes_entry.items]
        self.assertNotIn("Control Showcase", labels)
        self.assertIn("Main", labels)
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
        menu = MenuStripControl(
            "menu",
            app=app,
            scene_items_provider=lambda: [ContextMenuItem("Main")],
            scene_menu=SceneMenuOptions(shown=True),
        )
        app.scene = _FocusScene([menu])

        focus = FocusManager()
        focus.set_focus(menu)

        consumed = focus.route_key_event(
            GuiEvent(kind=EventType.KEY_DOWN, type=pygame.KEYDOWN, key=pygame.K_DOWN),
            app=app,
        )

        self.assertTrue(consumed)
        self.assertEqual(0, menu._open_index)

    def test_space_activates_highlighted_flyout_item(self):
        app = _StubApp(scene=_StubScene([]))
        calls = []
        menu = MenuStripControl(
            "menu",
            app=app,
            scene_items_provider=lambda: [ContextMenuItem("Main", action=lambda: calls.append("main"))],
            scene_menu=SceneMenuOptions(shown=True),
        )

        # Open first menu.
        consumed = menu.handle_event(
            GuiEvent(kind=EventType.KEY_DOWN, type=pygame.KEYDOWN, key=pygame.K_DOWN),
            app=app,
            theme=app.theme,
        )
        self.assertTrue(consumed)
        owner, panel, _ = app.overlay.shown[-1]
        self.assertIn("_menubar_menu_0", owner)

        # Highlight first selectable row and activate with Space.
        panel.handle_event(
            GuiEvent(kind=EventType.KEY_DOWN, type=pygame.KEYDOWN, key=pygame.K_DOWN),
            app=app,
            theme=app.theme,
        )
        consumed = panel.handle_event(
            GuiEvent(kind=EventType.KEY_DOWN, type=pygame.KEYDOWN, key=pygame.K_SPACE),
            app=app,
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
        menu = MenuStripControl(
            "menu",
            app=app,
            scene_items_provider=lambda: [ContextMenuItem("Main")],
            scene_menu=SceneMenuOptions(shown=True),
        )
        other = _DummyFocusable("other")
        app.scene = _FocusScene([menu, other])

        focus = FocusManager()
        focus.set_focus(menu)

        consumed = focus.route_key_event(
            GuiEvent(kind=EventType.KEY_DOWN, type=pygame.KEYDOWN, key=pygame.K_DOWN),
            app=app,
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

        menu = MenuStripControl(
            "menu",
            app=app,
            scene_menu=SceneMenuOptions(shown=True),
            scene_items_provider=_scene_items,
        )

        first_entry = next((entry for entry in menu.entries if entry.label == "Scene"), None)
        self.assertIsNotNone(first_entry)
        first_width = int(first_entry.flyout_min_width)

        state["long"] = False
        menu.refresh_entries()
        second_entry = next((entry for entry in menu.entries if entry.label == "Scene"), None)
        self.assertIsNotNone(second_entry)
        second_width = int(second_entry.flyout_min_width)

        self.assertGreater(first_width, second_width)

    def test_regular_menu_width_is_automatic_from_items(self):
        items = [ContextMenuItem("Extremely long regular menu option label for auto sizing")]
        width, height = _FlyoutPanel.measure(items)

        self.assertGreater(width, 140)
        self.assertGreater(height, 0)

    def test_flyout_width_is_at_least_top_level_entry_graphical_width(self):
        app = _StubApp(scene=_StubScene([]))
        menu = MenuStripControl(
            "menu",
            entries=[
                MenuEntry(
                    "A very very long top level menu label",
                    [ContextMenuItem("x")],
                )
            ],
            app=app,
        )

        consumed = menu.handle_event(
            GuiEvent(kind=EventType.KEY_DOWN, type=pygame.KEYDOWN, key=pygame.K_DOWN),
            app=app,
            theme=app.theme,
        )
        self.assertTrue(consumed)
        self.assertTrue(app.overlay.shown)

        _owner, panel, _kwargs = app.overlay.shown[-1]
        top_level_entry_width = menu._entry_rects(app.theme)[0].width
        self.assertGreaterEqual(panel.rect.width, top_level_entry_width)

    def test_scene_menu_compact_width_is_not_clamped_to_legacy_floor(self):
        item = ContextMenuItem("Main")
        setattr(item, "_menu_scene_compact", True)
        width, _height = _FlyoutPanel.measure([item], min_width=24)

        self.assertLess(width, 140)

    def test_windows_menu_discovers_mandelbrot_window_without_built_in_setter(self):
        mandel_window = _StubWindowNode("mandelbrot_window", "Mandelbrot Demo", visible=False)
        scene = _StubScene([_StubPlainNode(), mandel_window])
        app = _StubApp(scene=scene)

        menu = MenuStripControl(
            "menu",
            app=app,
            scene_name="main",
            window_menu=WindowMenuOptions(shown=True),
        )

        windows_entry = next((entry for entry in menu.entries if entry.label == "Window"), None)
        self.assertIsNotNone(windows_entry)
        labels = [item.label for item in windows_entry.items]
        self.assertIn("Mandelbrot Demo", labels)

    def test_windows_menu_action_calls_on_window_toggled_callback(self):
        systems_window = _StubWindowNode("systems_window", "Systems Demo", visible=False)
        scene = _StubScene([systems_window])
        app = _StubApp(scene=scene)
        callback_events = []

        menu = MenuStripControl(
            "menu",
            app=app,
            scene_name="main",
            window_menu=WindowMenuOptions(shown=True),
            on_window_toggled=lambda window, next_visible: callback_events.append((window.control_id, bool(next_visible))),
        )

        windows_entry = next((entry for entry in menu.entries if entry.label == "Window"), None)
        self.assertIsNotNone(windows_entry)
        self.assertTrue(windows_entry.items)

        windows_entry.items[0].action()

        self.assertTrue(systems_window.visible)
        self.assertEqual([("systems_window", True)], callback_events)

    def test_scene_menu_excludes_current_active_scene(self):
        app = _StubApp(scene=_StubScene([]))
        selected = []
        menu = MenuStripControl(
            "menu",
            app=app,
            scene_menu=SceneMenuOptions(shown=True),
            on_scene_selected=lambda scene_name: selected.append(str(scene_name)),
        )

        scenes_entry = next((entry for entry in menu.entries if entry.label == "Scene"), None)
        self.assertIsNotNone(scenes_entry)
        self.assertEqual(1, len(scenes_entry.items))

        scenes_entry.items[0].action()
        self.assertEqual(["control_showcase"], selected)

    def test_empty_autogenerated_scene_menu_highlights_without_opening_overlay(self):
        app = _StubApp(scene=_StubScene([]))
        app.active_scene_name = "main"
        app.scene_names = lambda: ["main"]
        menu = MenuStripControl(
            "menu",
            app=app,
            scene_menu=SceneMenuOptions(shown=True),
            window_menu=WindowMenuOptions(shown=False),
        )
        menu.rect.width = 500

        scene_index = next(i for i, entry in enumerate(menu.entries) if entry.label == "Scene")
        scene_rect = menu._entry_rects(app.theme)[scene_index]

        consumed = menu.handle_event(
            GuiEvent(
                kind=EventType.MOUSE_MOTION,
                type=pygame.MOUSEMOTION,
                pos=(scene_rect.centerx, scene_rect.centery),
            ),
            app=app,
            theme=app.theme,
        )

        self.assertTrue(consumed)
        self.assertEqual(scene_index, menu._hovered_index)
        self.assertEqual(-1, menu._open_index)
        self.assertEqual([], app.overlay.shown)

    def test_empty_autogenerated_window_menu_highlights_without_opening_overlay(self):
        app = _StubApp(scene=_StubScene([_StubPlainNode()]))
        menu = MenuStripControl(
            "menu",
            app=app,
            scene_menu=SceneMenuOptions(shown=False),
            window_menu=WindowMenuOptions(shown=True),
        )
        menu.rect.width = 500

        window_index = next(i for i, entry in enumerate(menu.entries) if entry.label == "Window")
        window_rect = menu._entry_rects(app.theme)[window_index]

        consumed = menu.handle_event(
            GuiEvent(
                kind=EventType.MOUSE_MOTION,
                type=pygame.MOUSEMOTION,
                pos=(window_rect.centerx, window_rect.centery),
            ),
            app=app,
            theme=app.theme,
        )

        self.assertTrue(consumed)
        self.assertEqual(window_index, menu._hovered_index)
        self.assertEqual(-1, menu._open_index)
        self.assertEqual([], app.overlay.shown)

    def test_add_window_menu_strip_accepts_optional_scene_and_window_providers(self):
        app = _StubApp(scene=_StubScene([]))
        host = _StubHost(app)
        window = _StubWindowContainer()

        added = add_window_menu_strip(
            window,
            host,
            control_id="menu",
            scene_name="main",
            on_minimize=lambda: None,
            scenes_shown=True,
            windows_shown=True,
            scene_items_provider=lambda: [ContextMenuItem("Custom Scene")],
            window_items_provider=lambda: [ContextMenuItem("Custom Window")],
        )

        self.assertIs(added, window.added[0])
        entries_by_label = {entry.label: entry for entry in added.entries}
        self.assertEqual(["Custom Scene"], [item.label for item in entries_by_label["Scene"].items])
        self.assertEqual(["Custom Window"], [item.label for item in entries_by_label["Window"].items])

    def test_adding_second_menu_bar_to_same_parent_raises(self):
        parent = UiNode("panel", Rect(0, 0, 800, 600))
        parent.add_child(MenuStripControl("menu_a"))
        with self.assertRaises(ValueError) as ctx:
            parent.add_child(MenuStripControl("menu_b"))
        self.assertIn("can only have one menu bar in this scope", str(ctx.exception))

    def test_adding_menu_bar_without_parent_does_not_raise(self):
        MenuStripControl("menu_standalone")  # on_mount(None) — should be fine


class TestSceneMenuStripMouseClickRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not pygame.get_init():
            pygame.init()
        if not pygame.font.get_init():
            pygame.font.init()

    def test_mouse_click_on_scene_flyout_item_fires_when_focus_stealer_present(self):
        from gui_do.app.gui_application import GuiApplication
        from gui_do.controls.input.button_control import ButtonControl
        surface = pygame.Surface((800, 200))
        app = GuiApplication(surface)
        app.create_scene("main")
        app.create_scene("control_showcase")
        app.switch_scene("control_showcase")
        fired = []
        menu = MenuStripControl(
            "menu",
            app=app,
            scene_name="control_showcase",
            scene_menu=SceneMenuOptions(shown=True),
            scene_items_provider=lambda: [
                ContextMenuItem("Main", action=lambda: fired.append("main"))
            ],
        )
        menu.set_tab_index(1)
        app.add(menu, scene_name="control_showcase")
        focus_stealer = ButtonControl("stealer", Rect(0, 28, 800, 172), "Steal")
        focus_stealer.set_tab_index(2)
        app.add(focus_stealer, scene_name="control_showcase")
        app.focus.set_focus(menu)
        app.theme.register_font_role("default", size=14)
        menu.handle_event(
            GuiEvent(kind=EventType.KEY_DOWN, type=pygame.KEYDOWN, key=pygame.K_DOWN),
            app=app,
            theme=app.theme,
        )
        self.assertGreaterEqual(menu._open_index, 0)
        self.assertGreater(app.overlay.overlay_count(), 0)
        flyout_panel = app.overlay._records[0].control
        flyout_rect = flyout_panel.rect
        click_x = flyout_rect.x + flyout_rect.width // 2
        click_y = flyout_rect.y + 4 + 13
        click = GuiEvent(
            kind=EventType.MOUSE_BUTTON_DOWN,
            type=pygame.MOUSEBUTTONDOWN,
            pos=(click_x, click_y),
            button=1,
        )
        app.process_event(click)
        self.assertEqual(["main"], fired)


if __name__ == "__main__":
    unittest.main()
