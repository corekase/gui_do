import unittest

from pygame import Rect

from gui_do.controls.arrow_box_control import ArrowBoxControl
from gui_do.controls.button_control import ButtonControl
from gui_do.controls.scrollbar_control import ScrollbarControl
from gui_do.controls.slider_control import SliderControl
from gui_do.controls.toggle_control import ToggleControl
from gui_do.core.gui_event import EventType, GuiEvent
from gui_do.layout.layout_axis import LayoutAxis


class _StubTimers:
    def __init__(self) -> None:
        self.added = []
        self.removed = []

    def add_timer(self, timer_id, interval, callback) -> None:
        self.added.append((timer_id, interval, callback))

    def remove_timer(self, timer_id) -> None:
        self.removed.append(timer_id)


class _StubPointerCapture:
    def __init__(self) -> None:
        self.owner_id = None
        self.lock_rect = None

    def begin(self, owner_id, lock_rect) -> None:
        self.owner_id = owner_id
        self.lock_rect = lock_rect

    def end(self, owner_id) -> None:
        if self.owner_id == owner_id:
            self.owner_id = None
            self.lock_rect = None

    def is_owned_by(self, owner_id) -> bool:
        return self.owner_id == owner_id

    def clamp(self, pos):
        return pos


class _StubInputState:
    def __init__(self) -> None:
        self.pointer_pos = (0, 0)


class _StubApp:
    def __init__(self) -> None:
        self.timers = _StubTimers()
        self.pointer_capture = _StubPointerCapture()
        self.input_state = _StubInputState()


def _mouse_down(pos):
    return GuiEvent(kind=EventType.MOUSE_BUTTON_DOWN, type=0, pos=pos, button=1)


def _mouse_up(pos):
    return GuiEvent(kind=EventType.MOUSE_BUTTON_UP, type=0, pos=pos, button=1)


def _mouse_motion(pos):
    return GuiEvent(kind=EventType.MOUSE_MOTION, type=0, pos=pos, rel=(0, 0))


def _mouse_wheel(pos, delta):
    return GuiEvent(kind=EventType.MOUSE_WHEEL, type=0, pos=pos, wheel_y=delta)


class ControlInteractionGuardsTests(unittest.TestCase):
    def test_button_and_toggle_ignore_events_when_disabled(self) -> None:
        app = _StubApp()
        clicked = []
        toggled = []
        button = ButtonControl("btn", Rect(0, 0, 40, 20), "B", on_click=lambda: clicked.append(True))
        toggle = ToggleControl("tog", Rect(0, 0, 40, 20), "On", on_toggle=lambda state: toggled.append(state))
        button.enabled = False
        toggle.enabled = False

        self.assertFalse(button.handle_event(_mouse_down((10, 10)), app))
        self.assertFalse(button.handle_event(_mouse_up((10, 10)), app))
        self.assertFalse(toggle.handle_event(_mouse_down((10, 10)), app))

        self.assertEqual(clicked, [])
        self.assertEqual(toggled, [])
        self.assertFalse(button.pressed)

    def test_arrow_box_ignores_events_when_hidden_or_disabled(self) -> None:
        app = _StubApp()
        fired = []
        control = ArrowBoxControl("arr", Rect(0, 0, 30, 30), 0, on_activate=lambda: fired.append(True), repeat_interval_seconds=0.05)

        control.enabled = False
        self.assertFalse(control.handle_event(_mouse_down((5, 5)), app))
        self.assertEqual(fired, [])
        self.assertEqual(app.timers.added, [])

        control.enabled = True
        control.visible = False
        self.assertFalse(control.handle_event(_mouse_down((5, 5)), app))
        self.assertEqual(fired, [])
        self.assertEqual(app.timers.added, [])

    def test_slider_does_not_start_drag_or_wheel_when_disabled(self) -> None:
        app = _StubApp()
        slider = SliderControl("s", Rect(0, 0, 120, 24), LayoutAxis.HORIZONTAL, 0.0, 100.0, 50.0)
        app.input_state.pointer_pos = (20, 12)
        slider.enabled = False
        baseline = slider.value

        self.assertFalse(slider.handle_event(_mouse_down(slider.handle_rect().center), app))
        self.assertFalse(slider.handle_event(_mouse_wheel((20, 12), 1), app))

        self.assertFalse(slider.dragging)
        self.assertIsNone(app.pointer_capture.owner_id)
        self.assertEqual(slider.value, baseline)

    def test_scrollbar_does_not_start_drag_or_wheel_when_hidden(self) -> None:
        app = _StubApp()
        bar = ScrollbarControl("sb", Rect(0, 0, 120, 24), LayoutAxis.HORIZONTAL, content_size=1000, viewport_size=200, offset=100, step=10)
        app.input_state.pointer_pos = (20, 12)
        bar.visible = False
        baseline = bar.offset

        self.assertFalse(bar.handle_event(_mouse_down(bar.handle_rect().center), app))
        self.assertFalse(bar.handle_event(_mouse_wheel((20, 12), 1), app))

        self.assertFalse(bar.dragging)
        self.assertIsNone(app.pointer_capture.owner_id)
        self.assertEqual(bar.offset, baseline)

    def test_disabling_dragging_slider_or_scrollbar_releases_capture(self) -> None:
        app = _StubApp()
        slider = SliderControl("s", Rect(0, 0, 120, 24), LayoutAxis.HORIZONTAL, 0.0, 100.0, 50.0)
        bar = ScrollbarControl("sb", Rect(0, 0, 120, 24), LayoutAxis.HORIZONTAL, content_size=1000, viewport_size=200, offset=100, step=10)

        slider.dragging = True
        app.pointer_capture.owner_id = "s"
        slider.enabled = False
        self.assertFalse(slider.handle_event(_mouse_motion((10, 10)), app))
        self.assertFalse(slider.dragging)
        self.assertIsNone(app.pointer_capture.owner_id)

        bar.dragging = True
        app.pointer_capture.owner_id = "sb"
        bar.visible = False
        self.assertFalse(bar.handle_event(_mouse_motion((10, 10)), app))
        self.assertFalse(bar.dragging)
        self.assertIsNone(app.pointer_capture.owner_id)


if __name__ == "__main__":
    unittest.main()
