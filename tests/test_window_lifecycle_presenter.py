import unittest

from pygame import Rect

from gui_do.controls.base.ui_node import UiNode
from gui_do.controls.chrome.window_control import WindowControl
from gui_do.controls.chrome.window_presenter import WindowPresenter
from gui_do.events.gui_event import EventType, GuiEvent


class _StubApp:
    def __init__(self):
        self.locking_object = None
        self.mouse_point_locked = False
        self.lock_point_pos = None


class _StubFontInstance:
    def __init__(self, line_height: int):
        self.line_height = int(line_height)


class _StubFonts:
    def __init__(self, line_height: int):
        self._line_height = int(line_height)

    def font_instance(self, role_name: str):
        _ = role_name
        return _StubFontInstance(self._line_height)


class _StubTheme:
    def __init__(self, line_height: int):
        self.fonts = _StubFonts(line_height)


class _TrackingNode(UiNode):
    def __init__(self, control_id: str, rect: Rect):
        super().__init__(control_id, rect)
        self.update_calls = 0
        self.event_calls = 0

    def update(self, dt_seconds: float) -> None:
        _ = dt_seconds
        self.update_calls += 1

    def handle_event(self, event, app, theme=None) -> bool:
        _ = app
        _ = theme
        if event.kind is EventType.MOUSE_BUTTON_DOWN:
            self.event_calls += 1
            return True
        return False


class _TrackingPresenter(WindowPresenter):
    def __init__(self):
        super().__init__(None)
        self.attached = False
        self.created = False
        self.resized_to = None
        self.before_calls = 0
        self.update_calls = 0
        self.after_calls = 0
        self.handled_events = 0

    def on_attach(self, window):
        _ = window
        self.attached = True

    def on_create(self):
        super().on_create()
        self.created = True

    def on_resize(self, new_rect):
        self.resized_to = Rect(new_rect)

    def before_update(self, dt_seconds: float):
        _ = dt_seconds
        self.before_calls += 1

    def update(self, dt_seconds: float):
        _ = dt_seconds
        self.update_calls += 1

    def after_update(self, dt_seconds: float):
        _ = dt_seconds
        self.after_calls += 1

    def handle_event(self, event):
        if event.kind is EventType.MOUSE_WHEEL:
            self.handled_events += 1
            return True
        return False


class _StubShearController:
    def __init__(self):
        self.dispose_calls = 0

    def dispose(self):
        self.dispose_calls += 1


class TestWindowLifecyclePresenter(unittest.TestCase):
    def test_add_remove_clear_manage_content_layer_children(self):
        window = WindowControl("w", (220, 160), "Window")
        node_a = _TrackingNode("a", Rect(30, 60, 50, 20))
        node_b = _TrackingNode("b", Rect(85, 60, 50, 20))

        window.add(node_a)
        window.add(node_b)

        self.assertEqual(1, len(window.children))
        self.assertIs(window, node_a.parent.parent)
        self.assertEqual(2, len(window.children[0].children))

        removed = window.remove(node_a)
        self.assertTrue(removed)
        self.assertEqual(1, len(window.children[0].children))

        cleared = window.clear_children()
        self.assertEqual(1, cleared)
        self.assertEqual(0, len(window.children[0].children))
        self.assertEqual(1, len(window.children))

    def test_move_by_translates_entire_content_subtree(self):
        window = WindowControl("w", (200, 120), "Window")
        parent = _TrackingNode("parent", Rect(30, 50, 60, 30))
        child = _TrackingNode("child", Rect(35, 55, 20, 10))
        parent.add_child(child)
        window.add(parent)

        window.move_by(12, -7)

        self.assertEqual((12, -7), window.rect.topleft)
        self.assertEqual((42, 43), parent.rect.topleft)
        self.assertEqual((47, 48), child.rect.topleft)

    def test_content_scope_blocks_titlebar_child_interaction(self):
        window = WindowControl("w", (280, 200), "Window")
        target = _TrackingNode("target", Rect(120, 170, 80, 30))
        window.add(target)
        app = _StubApp()

        titlebar_event = GuiEvent(kind=EventType.MOUSE_BUTTON_DOWN, type=0, pos=(130, 12), button=1)
        consumed = window.handle_event(titlebar_event, app)

        # The window is opaque to position-based mouse input: it consumes the
        # event to prevent fall-through to windows underneath, even though the
        # click landed in the titlebar/chrome area where children are not reached.
        self.assertTrue(consumed)
        self.assertEqual(0, target.event_calls)

        content_event = GuiEvent(kind=EventType.MOUSE_BUTTON_DOWN, type=0, pos=(130, 175), button=1)
        consumed = window.handle_event(content_event, app)

        self.assertTrue(consumed)
        self.assertEqual(1, target.event_calls)

    def test_presenter_lifecycle_hooks_are_wired(self):
        window = WindowControl("w", (200, 140), "Window")
        presenter = _TrackingPresenter()
        app = _StubApp()

        window.set_presenter(presenter)
        self.assertTrue(presenter.attached)
        self.assertTrue(presenter.created)

        window.resize(260, 170)
        self.assertEqual((260, 170), presenter.resized_to.size)

        window.update(0.016)
        self.assertEqual(1, presenter.before_calls)
        self.assertEqual(1, presenter.update_calls)
        self.assertEqual(1, presenter.after_calls)

        event = GuiEvent(kind=EventType.MOUSE_WHEEL, type=0, pos=(10, 40), wheel_y=1)
        consumed = window.handle_event(event, app)

        self.assertTrue(consumed)
        self.assertEqual(1, presenter.handled_events)

    def test_titlebar_height_fits_to_title_font_height_plus_padding(self):
        window = WindowControl("w", (220, 160), "Window", titlebar_height=24)
        theme = _StubTheme(line_height=30)

        window._fit_titlebar_height_to_font(theme)

        self.assertEqual(38, window.titlebar_height)

    def test_titlebar_height_respects_minimum_floor_when_font_is_small(self):
        window = WindowControl("w", (220, 160), "Window", titlebar_height=24)
        theme = _StubTheme(line_height=6)

        window._fit_titlebar_height_to_font(theme)

        self.assertEqual(14, window.titlebar_height)

    def test_dispose_releases_shear_controller(self):
        window = WindowControl("w", (220, 160), "Window")
        shear = _StubShearController()
        window.shear_controller = shear
        window.shear_active = True

        window.dispose()

        self.assertEqual(1, shear.dispose_calls)
        self.assertIsNone(window.shear_controller)
        self.assertFalse(window.shear_active)


if __name__ == "__main__":
    unittest.main()
