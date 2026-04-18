import unittest
from types import SimpleNamespace

from pygame import Rect

from gui.utility.events import Event, GuiError
from gui.utility.intermediates.widget import Widget


class DummyWidget(Widget):
    def leave(self) -> None:
        self.left = True


class WidgetBaseContractTests(unittest.TestCase):
    def _build_gui(self):
        gui = SimpleNamespace()
        gui.convert_to_window = lambda point, _window: point
        gui.get_mouse_pos = lambda: (5, 5)
        gui.event = lambda event_type, **kwargs: SimpleNamespace(type=event_type, **kwargs)
        gui.restore_calls = []
        gui.restore_pristine = lambda draw_rect, _window: gui.restore_calls.append((draw_rect.x, draw_rect.y))
        return gui

    def test_widget_default_leave_is_noop(self) -> None:
        widget = Widget(self._build_gui(), "w", Rect(0, 0, 10, 10))

        self.assertIsNone(widget.leave())

    def test_visible_position_and_collision_contracts(self) -> None:
        widget = DummyWidget(self._build_gui(), "w", Rect(1, 2, 10, 10))
        widget.hit_rect = Rect(3, 4, 6, 6)

        widget.visible = False
        self.assertFalse(widget.visible)
        with self.assertRaises(GuiError):
            widget.visible = "yes"  # type: ignore[assignment]

        widget.position = (10, 20)
        self.assertEqual(widget.position, (10, 20))
        self.assertEqual(widget.hit_rect.x, 12)
        self.assertEqual(widget.hit_rect.y, 22)

        with self.assertRaises(GuiError):
            widget.position = (10,)  # type: ignore[assignment]

        widget.gui.get_mouse_pos = lambda: (13, 23)
        self.assertTrue(widget.get_collide())
        widget.gui.get_mouse_pos = lambda: (100, 100)
        self.assertFalse(widget.get_collide())

    def test_build_event_and_draw_guard(self) -> None:
        widget = DummyWidget(self._build_gui(), "w", Rect(0, 0, 4, 4))
        event = widget.build_gui_event()

        self.assertEqual(event.type, Event.Widget)
        self.assertEqual(event.widget_id, "w")

        with self.assertRaises(GuiError):
            widget.draw()

    def test_widget_defaults_outside_collision_false_and_draw_restores_when_enabled(self) -> None:
        widget = DummyWidget(self._build_gui(), "w", Rect(0, 0, 4, 4))
        widget.surface = object()
        widget.auto_restore_pristine = True

        self.assertFalse(widget.should_handle_outside_collision())
        widget.draw()
        self.assertEqual(widget.gui.restore_calls, [(0, 0)])

    def test_collision_uses_draw_rect_when_hit_rect_missing(self) -> None:
        widget = DummyWidget(self._build_gui(), "w", Rect(0, 0, 4, 4))
        widget.hit_rect = None

        self.assertFalse(widget.get_collide())
        widget.gui.get_mouse_pos = lambda: (1, 1)
        self.assertTrue(widget.get_collide())


if __name__ == "__main__":
    unittest.main()
