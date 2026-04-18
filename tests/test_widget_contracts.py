import unittest
from collections import deque
from types import SimpleNamespace

import pygame
from pygame import Rect

from gui.utility.events import CanvasEvent, GuiError, Orientation
from gui.widgets.buttongroup import ButtonGroup
from gui.widgets.canvas import Canvas, CanvasEventPacket
from gui.widgets.label import Label
from gui.widgets.scrollbar import Scrollbar


class GraphicsFactorySpy:
    def __init__(self) -> None:
        self.calls = []

    def get_current_font_name(self):
        return "main"

    def set_font(self, name):
        self.calls.append(("set_font", name))

    def set_last_font(self):
        self.calls.append(("set_last_font", None))

    def render_text(self, text, colour=None, shadow=False):
        self.calls.append(("render_text", text, colour, shadow))
        return pygame.Surface((20, 10))


class CanvasContractTests(unittest.TestCase):
    def _build_canvas(self) -> Canvas:
        canvas = Canvas.__new__(Canvas)
        canvas._disabled = False
        canvas._events = deque([], maxlen=4)
        canvas.queued_event = False
        canvas.CEvent = None
        canvas.canvas = pygame.Surface((8, 8))
        canvas.pristine = pygame.Surface((8, 8))
        canvas.coalesce_motion_events = True
        canvas.on_overflow = None
        return canvas

    def test_read_event_updates_queue_state_tracking(self) -> None:
        canvas = self._build_canvas()
        first = CanvasEventPacket()
        first.type = CanvasEvent.MouseMotion
        second = CanvasEventPacket()
        second.type = CanvasEvent.MouseButtonDown
        canvas._events.extend([first, second])
        canvas.queued_event = True
        canvas.CEvent = first

        observed_first = Canvas.read_event(canvas)
        self.assertIs(observed_first, first)
        self.assertTrue(canvas.queued_event)
        self.assertIs(canvas.CEvent, second)

        observed_second = Canvas.read_event(canvas)
        self.assertIs(observed_second, second)
        self.assertFalse(canvas.queued_event)
        self.assertIsNone(canvas.CEvent)

        self.assertIsNone(Canvas.read_event(canvas))

    def test_set_event_queue_limit_rejects_invalid_values(self) -> None:
        canvas = self._build_canvas()

        with self.assertRaises(GuiError):
            Canvas.set_event_queue_limit(canvas, 0)
        with self.assertRaises(GuiError):
            Canvas.set_event_queue_limit(canvas, "3")  # type: ignore[arg-type]

    def test_set_event_queue_limit_updates_maxlen_and_head_state(self) -> None:
        canvas = self._build_canvas()
        packet = CanvasEventPacket()
        packet.type = CanvasEvent.MouseWheel
        canvas._events.append(packet)

        Canvas.set_event_queue_limit(canvas, 2)

        self.assertEqual(Canvas.get_event_queue_limit(canvas), 2)
        self.assertTrue(canvas.queued_event)
        self.assertIs(canvas.CEvent, packet)

    def test_motion_coalescing_and_overflow_handler_validation(self) -> None:
        canvas = self._build_canvas()

        with self.assertRaises(GuiError):
            Canvas.set_motion_coalescing(canvas, "yes")  # type: ignore[arg-type]
        with self.assertRaises(GuiError):
            Canvas.set_overflow_handler(canvas, "not-callable")  # type: ignore[arg-type]

        Canvas.set_motion_coalescing(canvas, False)
        self.assertFalse(canvas.coalesce_motion_events)

        callback = lambda dropped, total: None
        Canvas.set_overflow_handler(canvas, callback)
        self.assertIs(canvas.on_overflow, callback)
        Canvas.set_overflow_handler(canvas, None)
        self.assertIsNone(canvas.on_overflow)

    def test_restore_pristine_requires_initialized_snapshot(self) -> None:
        canvas = self._build_canvas()
        canvas.pristine = None

        with self.assertRaises(GuiError):
            Canvas.restore_pristine(canvas)

    def test_get_canvas_surface_returns_canvas_reference(self) -> None:
        canvas = self._build_canvas()

        self.assertIs(Canvas.get_canvas_surface(canvas), canvas.canvas)


class LabelContractTests(unittest.TestCase):
    def test_render_uses_shadow_colour_when_enabled(self) -> None:
        label = Label.__new__(Label)
        label.gui = SimpleNamespace(graphics_factory=GraphicsFactorySpy())
        label.shadow = True

        Label._render(label, "hello")

        self.assertEqual(label.gui.graphics_factory.calls[-1][0], "render_text")
        self.assertEqual(label.gui.graphics_factory.calls[-1][1], "hello")
        self.assertEqual(label.gui.graphics_factory.calls[-1][3], True)

    def test_set_label_restores_previous_font_when_font_captured(self) -> None:
        label = Label.__new__(Label)
        label.gui = SimpleNamespace(graphics_factory=GraphicsFactorySpy())
        label.shadow = False
        label._font = "main"

        Label.set_label(label, "updated")

        calls = label.gui.graphics_factory.calls
        self.assertEqual(calls[0], ("set_font", "main"))
        self.assertEqual(calls[1][0], "render_text")
        self.assertEqual(calls[2], ("set_last_font", None))


class ButtonGroupContractTests(unittest.TestCase):
    def test_button_id_falls_back_to_self_for_invalid_selection(self) -> None:
        button = ButtonGroup.__new__(ButtonGroup)
        button.group = "grp"
        button.id = "self"

        mediator = SimpleNamespace(get_selection=lambda _group: None)
        button.gui = SimpleNamespace(button_group_mediator=mediator)
        self.assertEqual(ButtonGroup.button_id.fget(button), "self")

        other_group = SimpleNamespace(group="other", id="other-id")
        button.gui = SimpleNamespace(button_group_mediator=SimpleNamespace(get_selection=lambda _group: other_group))
        self.assertEqual(ButtonGroup.button_id.fget(button), "self")

        bad_id = SimpleNamespace(group="grp", id="")
        button.gui = SimpleNamespace(button_group_mediator=SimpleNamespace(get_selection=lambda _group: bad_id))
        self.assertEqual(ButtonGroup.button_id.fget(button), "self")

    def test_button_group_and_build_event_use_mediator_selection(self) -> None:
        button = ButtonGroup.__new__(ButtonGroup)
        button.group = "grp"
        button.id = "self"
        selected = SimpleNamespace(group="grp", id="selected")

        mediator = SimpleNamespace(get_selection=lambda _group: selected)
        event_factory = lambda event_type, **kwargs: SimpleNamespace(type=event_type, **kwargs)
        button.gui = SimpleNamespace(button_group_mediator=mediator, event=event_factory)

        self.assertEqual(ButtonGroup.button_group.fget(button), "grp")
        event = ButtonGroup.build_gui_event(button)
        self.assertEqual(event.group, "grp")
        self.assertEqual(event.widget_id, "selected")


class ScrollbarConversionHelperTests(unittest.TestCase):
    def test_graphical_range_respects_orientation(self) -> None:
        scrollbar = Scrollbar.__new__(Scrollbar)
        scrollbar._disabled = False
        scrollbar._graphic_rect = Rect(0, 0, 40, 10)

        scrollbar._horizontal = Orientation.Horizontal
        self.assertEqual(Scrollbar._graphical_range(scrollbar), 40)

        scrollbar._horizontal = Orientation.Vertical
        self.assertEqual(Scrollbar._graphical_range(scrollbar), 10)

    def test_graphical_to_total_handles_zero_graphical_range(self) -> None:
        scrollbar = Scrollbar.__new__(Scrollbar)
        scrollbar._disabled = False
        scrollbar._graphic_rect = Rect(0, 0, 0, 10)
        scrollbar._horizontal = Orientation.Horizontal
        scrollbar._total_range = 100

        self.assertEqual(Scrollbar._graphical_to_total(scrollbar, 5), 0)

    def test_total_to_graphical_handles_non_positive_total_range(self) -> None:
        scrollbar = Scrollbar.__new__(Scrollbar)
        scrollbar._disabled = False
        scrollbar._graphic_rect = Rect(0, 0, 20, 6)
        scrollbar._horizontal = Orientation.Horizontal
        scrollbar._total_range = 0

        self.assertEqual(Scrollbar._total_to_graphical(scrollbar, 5), 0)


if __name__ == "__main__":
    unittest.main()
