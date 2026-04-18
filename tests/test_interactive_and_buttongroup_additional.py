import unittest
from types import SimpleNamespace

import pygame
from pygame import Rect
from pygame.locals import KEYDOWN, MOUSEBUTTONDOWN, MOUSEMOTION

from event_mouse_fixtures import build_mouse_gui_stub
from gui.utility.events import ButtonStyle, Event, InteractiveState, GuiError
from gui.utility.interactive import BaseInteractive
from gui.widgets.buttongroup import ButtonGroup


class _SurfaceSpy:
    def __init__(self):
        self.blit_calls = []

    def blit(self, bitmap, pos):
        self.blit_calls.append((bitmap, pos))


class _MediatorStub:
    def __init__(self):
        self._selection = {}
        self.register_calls = []
        self.select_calls = []

    def register(self, group, button):
        self.register_calls.append((group, button))

    def get_selection(self, group):
        return self._selection.get(group)

    def select(self, group, button):
        self.select_calls.append((group, button))
        self._selection[group] = button


class InteractiveAndButtonGroupAdditionalTests(unittest.TestCase):
    def _build_gui_stub(self):
        return build_mouse_gui_stub(
            mouse_pos=(5, 5),
            extras={
                "restore_pristine": lambda *_args, **_kwargs: None,
                "event": lambda event_type, **kwargs: SimpleNamespace(type=event_type, **kwargs),
                "graphics_factory": SimpleNamespace(
                    build_interactive_visuals=lambda _style, _text, rect: SimpleNamespace(
                        idle=object(), hover=object(), armed=object(), hit_rect=Rect(rect)
                    )
                ),
                "button_group_mediator": _MediatorStub(),
            },
        )

    def test_baseinteractive_leave_only_resets_non_armed(self) -> None:
        widget = BaseInteractive.__new__(BaseInteractive)
        widget.state = InteractiveState.Hover
        BaseInteractive.leave(widget)
        self.assertEqual(widget.state, InteractiveState.Idle)

        widget.state = InteractiveState.Armed
        BaseInteractive.leave(widget)
        self.assertEqual(widget.state, InteractiveState.Armed)

    def test_baseinteractive_handle_event_collision_flow(self) -> None:
        widget = BaseInteractive.__new__(BaseInteractive)
        widget.state = InteractiveState.Idle
        widget.get_collide = lambda _window: False

        self.assertFalse(BaseInteractive.handle_event(widget, pygame.event.Event(KEYDOWN, {}), None))
        self.assertEqual(widget.state, InteractiveState.Idle)

        widget.state = InteractiveState.Armed
        self.assertFalse(BaseInteractive.handle_event(widget, pygame.event.Event(KEYDOWN, {}), None))
        self.assertEqual(widget.state, InteractiveState.Armed)

        widget.state = InteractiveState.Idle
        widget.get_collide = lambda _window: True
        self.assertTrue(BaseInteractive.handle_event(widget, pygame.event.Event(KEYDOWN, {}), None))
        self.assertEqual(widget.state, InteractiveState.Hover)

    def test_baseinteractive_draw_uses_state_specific_bitmap(self) -> None:
        widget = BaseInteractive.__new__(BaseInteractive)
        widget.id = "w"
        widget.surface = _SurfaceSpy()
        widget.draw_rect = Rect(10, 20, 5, 5)
        widget.auto_restore_pristine = False
        widget.idle = object()
        widget.hover = object()
        widget.armed = object()

        widget.state = InteractiveState.Idle
        BaseInteractive.draw(widget)
        widget.state = InteractiveState.Hover
        BaseInteractive.draw(widget)
        widget.state = InteractiveState.Armed
        BaseInteractive.draw(widget)

        self.assertEqual(
            widget.surface.blit_calls,
            [
                (widget.idle, (10, 20)),
                (widget.hover, (10, 20)),
                (widget.armed, (10, 20)),
            ],
        )

    def test_buttongroup_init_validates_group(self) -> None:
        gui = self._build_gui_stub()

        with self.assertRaises(GuiError):
            ButtonGroup(gui, "", "id", Rect(0, 0, 10, 10), ButtonStyle.Box, "x")

    def test_buttongroup_init_registers_and_selects_when_first_selected(self) -> None:
        gui = self._build_gui_stub()
        mediator = gui.button_group_mediator

        def register(group, button):
            mediator._selection[group] = button
            mediator.register_calls.append((group, button))

        mediator.register = register

        button = ButtonGroup(gui, "grp", "id", Rect(0, 0, 10, 10), ButtonStyle.Box, "x")

        self.assertEqual(len(mediator.register_calls), 1)
        self.assertIs(mediator.get_selection("grp"), button)
        self.assertEqual(button.state, InteractiveState.Armed)

    def test_buttongroup_handle_event_non_mouse_is_ignored(self) -> None:
        gui = self._build_gui_stub()
        button = ButtonGroup(gui, "grp", "id", Rect(0, 0, 10, 10), ButtonStyle.Box, "x")

        self.assertFalse(button.handle_event(pygame.event.Event(KEYDOWN, {}), None))

    def test_buttongroup_handle_event_hover_and_click_select(self) -> None:
        gui = self._build_gui_stub()
        mediator = gui.button_group_mediator
        button = ButtonGroup(gui, "grp", "id", Rect(0, 0, 10, 10), ButtonStyle.Box, "x")
        button.state = InteractiveState.Idle
        button.get_collide = lambda _window: True

        self.assertFalse(button.handle_event(pygame.event.Event(MOUSEMOTION, {}), None))
        self.assertEqual(button.state, InteractiveState.Hover)

        clicked = button.handle_event(pygame.event.Event(MOUSEBUTTONDOWN, {"button": 1}), None)
        self.assertTrue(clicked)
        self.assertEqual(button.state, InteractiveState.Armed)
        self.assertEqual(len(mediator.select_calls), 1)

    def test_buttongroup_handle_event_non_left_click_does_not_select(self) -> None:
        gui = self._build_gui_stub()
        mediator = gui.button_group_mediator
        button = ButtonGroup(gui, "grp", "id", Rect(0, 0, 10, 10), ButtonStyle.Box, "x")
        button.state = InteractiveState.Hover
        button.get_collide = lambda _window: True

        clicked = button.handle_event(pygame.event.Event(MOUSEBUTTONDOWN, {"button": 3}), None)
        self.assertFalse(clicked)
        self.assertEqual(len(mediator.select_calls), 0)

    def test_buttongroup_should_handle_outside_collision_when_armed(self) -> None:
        gui = self._build_gui_stub()
        button = ButtonGroup(gui, "grp", "id", Rect(0, 0, 10, 10), ButtonStyle.Box, "x")

        button.state = InteractiveState.Hover
        self.assertFalse(button.should_handle_outside_collision())

        button.state = InteractiveState.Armed
        self.assertTrue(button.should_handle_outside_collision())

    def test_buttongroup_build_gui_event_includes_group_widget_and_window(self) -> None:
        gui = self._build_gui_stub()
        button = ButtonGroup(gui, "grp", "id", Rect(0, 0, 10, 10), ButtonStyle.Box, "x")
        window = object()

        event = button.build_gui_event(window=window)

        self.assertEqual(event.type, Event.Group)
        self.assertEqual(event.group, "grp")
        self.assertEqual(event.widget_id, "id")
        self.assertIs(event.window, window)


if __name__ == "__main__":
    unittest.main()
