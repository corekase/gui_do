import unittest

import pygame
from pygame.locals import KEYDOWN, MOUSEMOTION, QUIT

from gui.utility.events import Event
from gui.utility.gui_manager import GuiManager
from gui.utility.scheduler import TaskKind


class GraphicsFactoryStub:
    def load_font(self, _name: str, _filename: str, _size: int) -> None:
        return None


class IntegrationGuiManagerPipelineTests(unittest.TestCase):
    def _build_gui(self, event_batches=None):
        batches = [] if event_batches is None else list(event_batches)
        mouse_pos = {"value": (10, 10)}
        visible_calls = []
        mouse_set_calls = []

        def event_getter():
            if batches:
                return batches.pop(0)
            return []

        def mouse_get_pos():
            return mouse_pos["value"]

        def mouse_set_pos(pos):
            mouse_pos["value"] = pos
            mouse_set_calls.append(pos)

        def mouse_set_visible(visible: bool):
            visible_calls.append(visible)

        gui = GuiManager(
            surface=pygame.Surface((80, 60)),
            fonts=[("normal", "unused.ttf", 12)],
            graphics_factory=GraphicsFactoryStub(),
            task_panel_enabled=False,
            event_getter=event_getter,
            mouse_get_pos=mouse_get_pos,
            mouse_set_pos=mouse_set_pos,
            mouse_set_visible=mouse_set_visible,
        )

        return gui, visible_calls, mouse_set_calls, mouse_pos

    def test_event_stream_routes_to_screen_handler_and_updates_mouse(self) -> None:
        events = [
            [
                pygame.event.Event(KEYDOWN, {"key": 42}),
                pygame.event.Event(MOUSEMOTION, {"pos": (33, 44), "rel": (1, 2)}),
                pygame.event.Event(QUIT, {}),
            ]
        ]
        gui, visible_calls, _mouse_set_calls, _mouse_pos = self._build_gui(events)

        received = []
        gui.set_screen_lifecycle(event_handler=lambda event: received.append(event))

        for event in gui.events():
            gui.dispatch_event(event)

        self.assertEqual(visible_calls, [False])
        self.assertEqual([event.type for event in received], [Event.KeyDown, Event.MouseMotion, Event.Quit])
        self.assertEqual(received[0].key, 42)
        self.assertEqual(received[1].rel, (1, 2))
        self.assertEqual(received[1].pos, (33, 44))

    def test_task_owner_dispatch_takes_precedence_over_screen_handler(self) -> None:
        gui, _visible_calls, _mouse_set_calls, _mouse_pos = self._build_gui()

        screen_received = []
        owner_received = []

        owner = type("Owner", (), {"visible": True, "handle_event": lambda self, event: owner_received.append(event)})()
        gui.windows.append(owner)
        gui.set_screen_lifecycle(event_handler=lambda event: screen_received.append(event))

        gui.set_task_owner("task-1", owner)
        task_event = gui.scheduler.event(TaskKind.Finished, "task-1")

        gui.dispatch_event(task_event)

        self.assertEqual(len(owner_received), 1)
        self.assertEqual(len(screen_received), 0)
        self.assertEqual(getattr(owner_received[0], "id", None), "task-1")

    def test_buffered_draw_and_undraw_with_cursor_updates_cursor_rect(self) -> None:
        gui, _visible_calls, _mouse_set_calls, _mouse_pos = self._build_gui()
        gui.buffered = True
        gui.cursor_image = pygame.Surface((3, 3))
        gui.cursor_hotspot = (1, 1)
        gui.mouse_pos = (20, 30)

        gui.draw_gui()

        self.assertIsNotNone(gui.cursor_rect)
        self.assertEqual(gui.cursor_rect.topleft, (19, 29))

        gui.undraw_gui()


if __name__ == "__main__":
    unittest.main()
