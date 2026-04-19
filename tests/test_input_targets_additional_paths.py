import unittest

import pygame
from pygame import Rect
from pygame.locals import KEYDOWN, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION

from gui.utility.events import Event
from gui.utility.input.input_actions import InputAction
from gui.utility.input.input_targets import InputTargetResolver


class _GuiEventStub:
    def __init__(self, event_type: Event, **kwargs: object) -> None:
        self.type = event_type
        for key, value in kwargs.items():
            setattr(self, key, value)


class _WidgetStub:
    def __init__(
        self,
        widget_id: str,
        *,
        visible: bool = True,
        collides: bool = False,
        outside_collision: bool = False,
    ) -> None:
        self.id = widget_id
        self.visible = visible
        self._collides = collides
        self._outside_collision = outside_collision
        self.hit_rect = None
        self.draw_rect = Rect(10, 10, 20, 20)

    def get_collide(self, _window) -> bool:
        return self._collides

    def should_handle_outside_collision(self) -> bool:
        return self._outside_collision

    def build_gui_event(self, window=None):
        return _GuiEventStub(Event.Widget, widget_id=self.id, window=window)


class _ContainerStub:
    def __init__(self, widgets) -> None:
        self.widgets = widgets


class _WindowStub(_ContainerStub):
    def __init__(self, widgets, *, visible: bool = True, rect: Rect = Rect(0, 0, 200, 200)) -> None:
        super().__init__(widgets)
        self.visible = visible
        self._rect = rect

    def get_window_rect(self):
        return self._rect


class _TaskPanelStub(_ContainerStub):
    def __init__(self, widgets, *, visible: bool = True, rect: Rect = Rect(0, 0, 200, 200)) -> None:
        super().__init__(widgets)
        self.visible = visible
        self._rect = rect

    def get_rect(self):
        return self._rect


class _SnapshotWidgetBag:
    """Makes tuple(snapshot) differ from live containment checks to hit mutation guards."""

    def __init__(self, snapshot, live_items) -> None:
        self._snapshot = tuple(snapshot)
        self._live_items = list(live_items)

    def __iter__(self):
        return iter(self._snapshot)

    def __contains__(self, item) -> bool:
        return item in self._live_items


class _RegistryStub:
    def __init__(self, *, registered=True, raise_error=False, expose_method=True) -> None:
        self._registered = registered
        self._raise_error = raise_error
        self._expose_method = expose_method

    def is_registered_object(self, _widget):
        if not self._expose_method:
            raise AttributeError("method hidden")
        if self._raise_error:
            raise RuntimeError("boom")
        return self._registered


class _GuiStub:
    def __init__(self) -> None:
        self.widgets = []
        self.windows = []
        self.task_panel = None
        self.active_window = None
        self._mouse_pos = (5, 5)
        self.handled_ids = []
        self.focus_updates = []
        self.raised_windows = []
        self.updated_active_window = 0
        self.handle_return_by_id = {}
        self.object_registry = None

    def update_active_window(self) -> None:
        self.updated_active_window += 1

    def get_mouse_pos(self):
        return self._mouse_pos

    def convert_to_window(self, point, _window):
        return point

    def handle_widget(self, widget, _event, _window=None):
        self.handled_ids.append(widget.id)
        return self.handle_return_by_id.get(widget.id, False)

    def update_focus(self, widget) -> None:
        self.focus_updates.append(widget)

    def raise_window(self, window) -> None:
        self.raised_windows.append(window)

    def event(self, event_type: Event, **kwargs: object):
        return _GuiEventStub(event_type, **kwargs)


class InputTargetResolverAdditionalPathTests(unittest.TestCase):
    def setUp(self) -> None:
        self.gui = _GuiStub()
        self.resolver = InputTargetResolver(self.gui)

    def test_update_active_window_delegates(self) -> None:
        self.resolver.update_active_window()
        self.assertEqual(self.gui.updated_active_window, 1)

    def test_dispatch_widget_layer_skips_removed_and_invisible(self) -> None:
        removed = _WidgetStub("removed", visible=True, collides=True)
        hidden = _WidgetStub("hidden", visible=False, collides=True)
        bag = _SnapshotWidgetBag([removed, hidden], live_items=[hidden])
        container = _ContainerStub(bag)

        hit_any, focus_target = self.resolver._dispatch_widget_layer(
            pygame.event.Event(MOUSEBUTTONDOWN, {"button": 1}),
            container,
        )

        self.assertFalse(hit_any)
        self.assertIsNone(focus_target)
        self.assertEqual(self.gui.handled_ids, [])

    def test_dispatch_widget_layer_outside_collision_task_panel_emits(self) -> None:
        widget = _WidgetStub("panel-w", collides=False, outside_collision=True)
        container = _ContainerStub([widget])
        self.gui.handle_return_by_id["panel-w"] = True
        self.gui.object_registry = _RegistryStub(registered=True)

        action = self.resolver._dispatch_widget_layer(
            pygame.event.Event(MOUSEBUTTONDOWN, {"button": 1}),
            container,
            emit_task_panel=True,
        )

        self.assertIsInstance(action, InputAction)
        self.assertEqual(action.event_type, Event.Widget)
        self.assertEqual(action.kwargs["widget_id"], "panel-w")
        self.assertTrue(action.kwargs["task_panel"])
        self.assertEqual(self.gui.focus_updates, [])

    def test_dispatch_widget_layer_hit_without_handle_returns_tuple(self) -> None:
        widget = _WidgetStub("w", collides=True)
        hit_any, focus_target = self.resolver._dispatch_widget_layer(
            pygame.event.Event(MOUSEBUTTONDOWN, {"button": 1}),
            _ContainerStub([widget]),
        )

        self.assertTrue(hit_any)
        self.assertIs(focus_target, widget)

    def test_registry_resolution_handles_missing_and_exceptions(self) -> None:
        widget = _WidgetStub("w")

        self.gui.object_registry = None
        self.assertIsNone(self.resolver._is_registered_via_registry(widget))

        class _NoMethodRegistry:
            pass

        self.gui.object_registry = _NoMethodRegistry()
        self.assertIsNone(self.resolver._is_registered_via_registry(widget))

        self.gui.object_registry = _RegistryStub(raise_error=True)
        self.assertIsNone(self.resolver._is_registered_via_registry(widget))

    def test_process_screen_widgets_hit_but_not_handled_focuses_and_passes(self) -> None:
        widget = _WidgetStub("screen", collides=True)
        self.gui.widgets = [widget]
        self.gui._mouse_pos = (15, 15)
        self.gui.object_registry = _RegistryStub(registered=True)

        action = self.resolver.process_screen_widgets(
            pygame.event.Event(MOUSEBUTTONDOWN, {"button": 1})
        )

        self.assertEqual(action.event_type, Event.Pass)
        self.assertEqual(self.gui.focus_updates, [widget])

    def test_process_screen_widgets_no_hit_maps_base_mouse_event(self) -> None:
        widget = _WidgetStub("screen", collides=False)
        self.gui.widgets = [widget]

        down_action = self.resolver.process_screen_widgets(
            pygame.event.Event(MOUSEBUTTONDOWN, {"button": 2})
        )
        up_action = self.resolver.process_screen_widgets(
            pygame.event.Event(MOUSEBUTTONUP, {"button": 3})
        )
        motion_action = self.resolver.process_screen_widgets(
            pygame.event.Event(MOUSEMOTION, {"rel": (1, 2)})
        )
        fallback_action = self.resolver.process_screen_widgets(
            pygame.event.Event(KEYDOWN, {"key": 1})
        )

        self.assertEqual(down_action.event_type, Event.MouseButtonDown)
        self.assertEqual(down_action.kwargs["button"], 2)
        self.assertEqual(up_action.event_type, Event.MouseButtonUp)
        self.assertEqual(up_action.kwargs["button"], 3)
        self.assertEqual(motion_action.event_type, Event.MouseMotion)
        self.assertEqual(motion_action.kwargs["rel"], (1, 2))
        self.assertEqual(fallback_action.event_type, Event.Pass)
        self.assertEqual(self.gui.focus_updates, [None, None, None, None])

    def test_process_window_widgets_paths(self) -> None:
        event = pygame.event.Event(MOUSEBUTTONDOWN, {"button": 1})

        # No window under mouse falls through to base mapping.
        self.gui.windows = []
        no_window_action = self.resolver.process_window_widgets(event)
        self.assertEqual(no_window_action.event_type, Event.MouseButtonDown)

        # Layer returns InputAction directly.
        win_action_widget = _WidgetStub("win-action", collides=True)
        self.gui.windows = [_WindowStub([win_action_widget], rect=Rect(0, 0, 100, 100))]
        self.gui.active_window = self.gui.windows[0]
        self.gui.object_registry = _RegistryStub(registered=True)
        self.gui.handle_return_by_id["win-action"] = True

        direct_action = self.resolver.process_window_widgets(event)
        self.assertIsNotNone(direct_action.builder)
        built_event = direct_action.builder()
        self.assertEqual(built_event.type, Event.Widget)
        self.assertEqual(built_event.widget_id, "win-action")
        self.assertEqual(self.gui.raised_windows, [self.gui.active_window])

        # Hit but not handled keeps focus and returns pass.
        win_pass_widget = _WidgetStub("win-pass", collides=True)
        self.gui.windows = [_WindowStub([win_pass_widget], rect=Rect(0, 0, 100, 100))]
        self.gui.handle_return_by_id["win-pass"] = False
        pass_action = self.resolver.process_window_widgets(event)
        self.assertEqual(pass_action.event_type, Event.Pass)
        self.assertIs(self.gui.focus_updates[-1], win_pass_widget)

    def test_process_task_panel_widget_paths(self) -> None:
        event = pygame.event.Event(MOUSEBUTTONDOWN, {"button": 1})

        # No panel or hidden panel returns None.
        self.gui.task_panel = None
        self.assertIsNone(self.resolver.process_task_panel_widgets(event))

        self.gui.task_panel = _TaskPanelStub([], visible=False)
        self.assertIsNone(self.resolver.process_task_panel_widgets(event))

        # Panel miss returns None.
        self.gui.task_panel = _TaskPanelStub([], visible=True, rect=Rect(100, 100, 10, 10))
        self.assertIsNone(self.resolver.process_task_panel_widgets(event))

        # Panel handled path returns widget action with task_panel marker.
        panel_widget = _WidgetStub("panel-hit", collides=True)
        self.gui.task_panel = _TaskPanelStub([panel_widget], visible=True, rect=Rect(0, 0, 100, 100))
        self.gui.handle_return_by_id["panel-hit"] = True
        self.gui.object_registry = _RegistryStub(registered=True)
        handled_action = self.resolver.process_task_panel_widgets(event)
        self.assertEqual(handled_action.event_type, Event.Widget)
        self.assertEqual(handled_action.kwargs["widget_id"], "panel-hit")
        self.assertTrue(handled_action.kwargs["task_panel"])

        # Panel hit but not handled returns pass and updates focus.
        panel_widget2 = _WidgetStub("panel-pass", collides=True)
        self.gui.task_panel = _TaskPanelStub([panel_widget2], visible=True, rect=Rect(0, 0, 100, 100))
        self.gui.handle_return_by_id["panel-pass"] = False
        pass_action = self.resolver.process_task_panel_widgets(event)
        self.assertEqual(pass_action.event_type, Event.Pass)
        self.assertIs(self.gui.focus_updates[-1], panel_widget2)

    def test_is_registered_widget_fallback_paths(self) -> None:
        widget = _WidgetStub("registered")
        other = _WidgetStub("other")

        self.assertFalse(self.resolver.is_registered_widget(None))

        self.gui.object_registry = _RegistryStub(registered=True)
        self.assertTrue(self.resolver.is_registered_widget(widget))

        self.gui.object_registry = _RegistryStub(raise_error=True)
        self.gui.widgets = [widget]
        self.assertTrue(self.resolver.is_registered_widget(widget))

        self.gui.widgets = []
        self.gui.task_panel = _TaskPanelStub([widget])
        self.assertTrue(self.resolver.is_registered_widget(widget))

        self.gui.task_panel = _TaskPanelStub([])
        self.gui.windows = [_WindowStub([widget])]
        self.assertTrue(self.resolver.is_registered_widget(widget))
        self.assertFalse(self.resolver.is_registered_widget(other))


if __name__ == "__main__":
    unittest.main()
