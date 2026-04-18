import unittest
from types import SimpleNamespace
from unittest.mock import patch

from pygame import Rect

from event_mouse_fixtures import build_mouse_gui_stub
from gui.utility.events import ArrowPosition, ButtonStyle, GuiError, Orientation
from gui.utility.object_registry import GuiObjectRegistry
from gui.utility.gui_utils.task_panel import _ManagedTaskPanel
from gui.utility.ui_factory import GuiUiFactory
from gui.utility.intermediates.widget import Widget
from gui.utility.gui_utils.workspace_state import WorkspaceState
import gui.utility.gui_manager as gm


class _Convertible:
    def convert(self):
        return self


class _PanelSurface:
    def __init__(self, size):
        self._rect = Rect(0, 0, size[0], size[1])

    def convert(self):
        return self

    def get_rect(self):
        return Rect(self._rect)


class GuiManagerRoiBatch4Tests(unittest.TestCase):
    def test_managed_task_panel_constructor_validates_inputs(self) -> None:
        gui = SimpleNamespace(surface=SimpleNamespace(get_rect=lambda: Rect(0, 0, 100, 80)))

        with self.assertRaises(GuiError):
            _ManagedTaskPanel(gui, 0, 0, 1, True, 1.0, 1, None, None, None, None)
        with self.assertRaises(GuiError):
            _ManagedTaskPanel(gui, 20, "x", 1, True, 1.0, 1, None, None, None, None)  # type: ignore[arg-type]
        with self.assertRaises(GuiError):
            _ManagedTaskPanel(gui, 20, 0, 0, True, 1.0, 1, None, None, None, None)
        with self.assertRaises(GuiError):
            _ManagedTaskPanel(gui, 20, 0, 1, "yes", 1.0, 1, None, None, None, None)  # type: ignore[arg-type]
        with self.assertRaises(GuiError):
            _ManagedTaskPanel(gui, 20, 0, 1, True, 1.0, 0, None, None, None, None)
        with self.assertRaises(GuiError):
            _ManagedTaskPanel(gui, 20, 0, 1, True, 0.0, 1, None, None, None, None)
        with self.assertRaises(GuiError):
            _ManagedTaskPanel(gui, 20, 100, 1, True, 1.0, 1, None, None, None, None)
        with self.assertRaises(GuiError):
            _ManagedTaskPanel(gui, 20, 0, 20, True, 1.0, 1, None, None, None, None)

    def test_managed_task_panel_constructor_without_backdrop_builds_pristine(self) -> None:
        timer_calls = []
        pre_calls = []
        evt_calls = []
        post_calls = []

        gui = build_mouse_gui_stub(
            mouse_pos=(0, 0),
            extras={
                "surface": SimpleNamespace(get_rect=lambda: Rect(0, 0, 120, 80)),
                "timers": SimpleNamespace(add_timer=lambda tid, interval, cb: timer_calls.append((tid, interval, cb))),
                "copy_graphic_area": lambda *_args, **_kwargs: _Convertible(),
                "set_pristine": lambda *_args, **_kwargs: None,
            },
        )

        class FakeFrame:
            def __init__(self, *_args, **_kwargs):
                self.state = None
                self.surface = None

            def draw(self):
                return None

        with patch("gui.utility.gui_utils.task_panel.pygame.surface.Surface", side_effect=lambda size: _PanelSurface(size)), patch(
            "gui.utility.gui_utils.task_panel.Frame", FakeFrame
        ):
            panel = _ManagedTaskPanel(
                gui,
                height=20,
                x=10,
                reveal_pixels=4,
                auto_hide=True,
                timer_interval=3.0,
                movement_step=2,
                backdrop=None,
                preamble=lambda: pre_calls.append(True),
                event_handler=lambda event: evt_calls.append(event),
                postamble=lambda: post_calls.append(True),
            )

        self.assertEqual(panel.width, 110)
        self.assertEqual(panel.y, 76)
        self.assertIsNotNone(panel.pristine)
        self.assertEqual(len(timer_calls), 1)

        panel.run_preamble()
        panel.handle_event("evt")
        panel.run_postamble()
        self.assertEqual(pre_calls, [True])
        self.assertEqual(evt_calls, ["evt"])
        self.assertEqual(post_calls, [True])

    def test_managed_task_panel_constructor_with_backdrop_uses_set_pristine(self) -> None:
        set_pristine_calls = []
        gui = build_mouse_gui_stub(
            mouse_pos=(0, 0),
            extras={
                "surface": SimpleNamespace(get_rect=lambda: Rect(0, 0, 100, 60)),
                "timers": SimpleNamespace(add_timer=lambda *_args, **_kwargs: None),
                "copy_graphic_area": lambda *_args, **_kwargs: _Convertible(),
                "set_pristine": lambda backdrop, panel: set_pristine_calls.append((backdrop, panel)),
            },
        )

        with patch("gui.utility.gui_utils.task_panel.pygame.surface.Surface", side_effect=lambda size: _PanelSurface(size)):
            panel = _ManagedTaskPanel(gui, 20, 0, 4, True, 1.0, 1, "panel.png", None, None, None)

        self.assertEqual(len(set_pristine_calls), 1)
        self.assertEqual(set_pristine_calls[0][0], "panel.png")
        self.assertIs(set_pristine_calls[0][1], panel)

    def test_manager_init_validation_guards(self) -> None:
        surface = SimpleNamespace(get_rect=lambda: Rect(0, 0, 100, 60))

        with self.assertRaises(GuiError):
            gm.GuiManager(None, [("main", "a.ttf", 12)])  # type: ignore[arg-type]
        with self.assertRaises(GuiError):
            gm.GuiManager(surface, [])
        with self.assertRaises(GuiError):
            gm.GuiManager(surface, [("bad",)])  # type: ignore[list-item]
        with self.assertRaises(GuiError):
            gm.GuiManager(surface, [("", "a.ttf", 12)])
        with self.assertRaises(GuiError):
            gm.GuiManager(surface, [("main", "", 12)])
        with self.assertRaises(GuiError):
            gm.GuiManager(surface, [("main", "a.ttf", 0)])

    def test_manager_init_success_with_injected_providers(self) -> None:
        visible_calls = []
        loaded_fonts = []

        graphics_factory = SimpleNamespace(load_font=lambda *args: loaded_fonts.append(args))
        surface = SimpleNamespace(get_rect=lambda: Rect(0, 0, 100, 80))

        with patch("gui.utility.gui_manager.EventDispatcher", side_effect=lambda gui: SimpleNamespace(gui=gui)), patch(
            "gui.utility.gui_manager.LayoutManager", return_value=SimpleNamespace()
        ), patch("gui.utility.gui_manager.Renderer", side_effect=lambda gui: SimpleNamespace(gui=gui)), patch(
            "gui.utility.gui_manager.Scheduler", side_effect=lambda gui: SimpleNamespace(gui=gui)
        ), patch("gui.utility.gui_manager.Timers", return_value=SimpleNamespace()), patch(
            "gui.utility.gui_manager.ButtonGroupMediator", return_value=SimpleNamespace()
        ):
            gui = gm.GuiManager(
                surface,
                [("main", "a.ttf", 12), ("title", "b.ttf", 14)],
                graphics_factory=graphics_factory,
                task_panel_enabled=False,
                event_getter=lambda: [],
                mouse_get_pos=lambda: (1, 2),
                mouse_set_pos=lambda _pos: None,
                mouse_set_visible=lambda visible: visible_calls.append(visible),
            )

        self.assertEqual(visible_calls, [False])
        self.assertEqual(loaded_fonts, [("main", "a.ttf", 12), ("title", "b.ttf", 14)])
        self.assertEqual(gui.mouse_pos, (1, 2))

    def test_manager_init_rejects_non_callable_injected_providers(self) -> None:
        surface = SimpleNamespace(get_rect=lambda: Rect(0, 0, 100, 60))
        graphics_factory = SimpleNamespace(load_font=lambda *_args: None)

        with self.assertRaises(GuiError):
            gm.GuiManager(surface, [("main", "a.ttf", 12)], graphics_factory=graphics_factory, task_panel_enabled=False, event_getter=1)  # type: ignore[arg-type]
        with self.assertRaises(GuiError):
            gm.GuiManager(surface, [("main", "a.ttf", 12)], graphics_factory=graphics_factory, task_panel_enabled=False, mouse_get_pos=1)  # type: ignore[arg-type]
        with self.assertRaises(GuiError):
            gm.GuiManager(surface, [("main", "a.ttf", 12)], graphics_factory=graphics_factory, task_panel_enabled=False, mouse_set_pos=1)  # type: ignore[arg-type]
        with self.assertRaises(GuiError):
            gm.GuiManager(surface, [("main", "a.ttf", 12)], graphics_factory=graphics_factory, task_panel_enabled=False, mouse_set_visible=1)  # type: ignore[arg-type]

    def test_configure_fonts_builds_and_loads_in_one_call(self) -> None:
        loaded_fonts = []
        gui = gm.GuiManager.__new__(gm.GuiManager)
        gui._graphics_factory = SimpleNamespace(load_font=lambda *args: loaded_fonts.append(args))

        registry = gm.GuiManager.configure_fonts(
            gui,
            titlebar=("Ubuntu-B.ttf", 14),
            normal=("Gimbot.ttf", 16),
        )

        self.assertEqual(
            registry,
            [("titlebar", "Ubuntu-B.ttf", 14), ("normal", "Gimbot.ttf", 16)],
        )
        self.assertEqual(
            loaded_fonts,
            [("titlebar", "Ubuntu-B.ttf", 14), ("normal", "Gimbot.ttf", 16)],
        )

    def test_configure_fonts_validates_entries(self) -> None:
        gui = gm.GuiManager.__new__(gm.GuiManager)
        gui._graphics_factory = SimpleNamespace(load_font=lambda *_args: None)

        with self.assertRaises(GuiError):
            gm.GuiManager.configure_fonts(gui)
        with self.assertRaises(GuiError):
            gm.GuiManager.configure_fonts(gui, main=("a.ttf",))  # type: ignore[arg-type]
        with self.assertRaises(GuiError):
            gm.GuiManager.configure_fonts(gui, main=("", 12))
        with self.assertRaises(GuiError):
            gm.GuiManager.configure_fonts(gui, main=("a.ttf", 0))

    def test_manager_init_without_fonts_is_supported(self) -> None:
        visible_calls = []
        loaded_fonts = []

        graphics_factory = SimpleNamespace(load_font=lambda *args: loaded_fonts.append(args))
        surface = SimpleNamespace(get_rect=lambda: Rect(0, 0, 100, 80))

        with patch("gui.utility.gui_manager.EventDispatcher", side_effect=lambda gui: SimpleNamespace(gui=gui)), patch(
            "gui.utility.gui_manager.LayoutManager", return_value=SimpleNamespace()
        ), patch("gui.utility.gui_manager.Renderer", side_effect=lambda gui: SimpleNamespace(gui=gui)), patch(
            "gui.utility.gui_manager.Scheduler", side_effect=lambda gui: SimpleNamespace(gui=gui)
        ), patch("gui.utility.gui_manager.Timers", return_value=SimpleNamespace()), patch(
            "gui.utility.gui_manager.ButtonGroupMediator", return_value=SimpleNamespace()
        ):
            gm.GuiManager(
                surface,
                graphics_factory=graphics_factory,
                task_panel_enabled=False,
                event_getter=lambda: [],
                mouse_get_pos=lambda: (1, 2),
                mouse_set_pos=lambda _pos: None,
                mouse_set_visible=lambda visible: visible_calls.append(visible),
            )

        self.assertEqual(visible_calls, [False])
        self.assertEqual(loaded_fonts, [])

    def test_manager_init_accepts_fonts_iterable(self) -> None:
        visible_calls = []
        loaded_fonts = []

        graphics_factory = SimpleNamespace(load_font=lambda *args: loaded_fonts.append(args))
        surface = SimpleNamespace(get_rect=lambda: Rect(0, 0, 100, 80))
        fonts_iterable = ((name, filename, size) for name, filename, size in [
            ("main", "a.ttf", 12),
            ("title", "b.ttf", 14),
        ])

        with patch("gui.utility.gui_manager.EventDispatcher", side_effect=lambda gui: SimpleNamespace(gui=gui)), patch(
            "gui.utility.gui_manager.LayoutManager", return_value=SimpleNamespace()
        ), patch("gui.utility.gui_manager.Renderer", side_effect=lambda gui: SimpleNamespace(gui=gui)), patch(
            "gui.utility.gui_manager.Scheduler", side_effect=lambda gui: SimpleNamespace(gui=gui)
        ), patch("gui.utility.gui_manager.Timers", return_value=SimpleNamespace()), patch(
            "gui.utility.gui_manager.ButtonGroupMediator", return_value=SimpleNamespace()
        ):
            gm.GuiManager(
                surface,
                fonts_iterable,
                graphics_factory=graphics_factory,
                task_panel_enabled=False,
                event_getter=lambda: [],
                mouse_get_pos=lambda: (1, 2),
                mouse_set_pos=lambda _pos: None,
                mouse_set_visible=lambda visible: visible_calls.append(visible),
            )

        self.assertEqual(visible_calls, [False])
        self.assertEqual(loaded_fonts, [("main", "a.ttf", 12), ("title", "b.ttf", 14)])

    def test_widget_factory_helpers_delegate_to_add(self) -> None:
        gui = gm.GuiManager.__new__(gm.GuiManager)
        created = []
        gui.add = lambda obj: created.append(obj) or obj
        gui.ui_factory = GuiUiFactory(gui)

        with patch("gui.utility.ui_factory.ArrowBox", side_effect=lambda *args: SimpleNamespace(kind="arrow", args=args)), patch(
            "gui.utility.ui_factory.Button", side_effect=lambda *args: SimpleNamespace(kind="button", args=args)
        ), patch("gui.utility.ui_factory.ButtonGroup", side_effect=lambda *args: SimpleNamespace(kind="group", args=args)), patch(
            "gui.utility.ui_factory.Canvas", side_effect=lambda *args: SimpleNamespace(kind="canvas", args=args)
        ), patch("gui.utility.ui_factory.Frame", side_effect=lambda *args: SimpleNamespace(kind="frame", args=args)), patch(
            "gui.utility.ui_factory.Image", side_effect=lambda *args: SimpleNamespace(kind="image", args=args)
        ), patch("gui.utility.ui_factory.Label", side_effect=lambda *args: SimpleNamespace(kind="label", args=args)), patch(
            "gui.utility.ui_factory.Scrollbar", side_effect=lambda *args: SimpleNamespace(kind="scrollbar", args=args)
        ), patch("gui.utility.ui_factory.Toggle", side_effect=lambda *args: SimpleNamespace(kind="toggle", args=args)), patch(
            "gui.utility.ui_factory.Window", side_effect=lambda *args: SimpleNamespace(kind="window", args=args)
        ):
            gm.GuiManager.arrow_box(gui, "a", Rect(0, 0, 1, 1), 90)
            gm.GuiManager.button(gui, "b", Rect(0, 0, 1, 1), ButtonStyle.Box, None)
            gm.GuiManager.button_group(gui, "grp", "bg", Rect(0, 0, 1, 1), ButtonStyle.Box, "x")
            gm.GuiManager.canvas(gui, "c", Rect(0, 0, 1, 1))
            gm.GuiManager.frame(gui, "f", Rect(0, 0, 1, 1))
            gm.GuiManager.image(gui, "i", Rect(0, 0, 1, 1), "img.png")
            gm.GuiManager.label(gui, (1, 2), "lbl")
            gm.GuiManager.scrollbar(gui, "s", Rect(0, 0, 20, 6), Orientation.Horizontal, ArrowPosition.Skip, (10, 0, 5, 1))
            gm.GuiManager.toggle(gui, "t", Rect(0, 0, 1, 1), ButtonStyle.Box, False, "p")
            gm.GuiManager.window(gui, "w", (0, 0), (10, 10))

        self.assertEqual(len(created), 10)
        # Button wrapper should normalize None text to empty string.
        self.assertEqual(created[1].args[4], "")
        # Label wrapper should auto-generate id when omitted.
        self.assertEqual(created[6].args[1], "label_1")

    def test_helper_describe_and_registration_paths(self) -> None:
        gui = gm.GuiManager.__new__(gm.GuiManager)
        gui.widgets = []
        gui.windows = []
        gui.task_panel = None
        gui.workspace_state = WorkspaceState()
        gui.object_registry = GuiObjectRegistry(gui)

        # Incoming container description switches across task panel, screen, and window.
        self.assertEqual(gui.object_registry.describe_incoming_widget_container(), "screen")
        active = SimpleNamespace(x=3, y=4, width=7, height=8)
        gui.workspace_state.active_object = active
        gui.windows = [active]
        self.assertIn("window pos=(3,4)", gui.object_registry.describe_incoming_widget_container())
        gui.workspace_state.task_panel_capture = True
        gui.task_panel = SimpleNamespace(widgets=[])
        self.assertEqual(gui.object_registry.describe_incoming_widget_container(), "task_panel")

        # _describe_widget_container identifies screen, task panel, and window.
        widget = Widget.__new__(Widget)
        widget.window = None
        self.assertEqual(gui.object_registry.describe_widget_container(widget), "screen")
        gui.task_panel.widgets = [widget]
        self.assertEqual(gui.object_registry.describe_widget_container(widget), "task_panel")
        gui.task_panel.widgets = []
        win = gm.Window.__new__(gm.Window)
        win.x = 1
        win.y = 2
        win.width = 3
        win.height = 4
        widget.window = win
        self.assertEqual(gui.object_registry.describe_widget_container(widget), "window pos=(1,2) size=(3,4)")
        widget.window = object()
        self.assertEqual(gui.object_registry.describe_widget_container(widget), "screen")


if __name__ == "__main__":
    unittest.main()
