import unittest

import pygame
from pygame import Rect, Surface

from gui.app.gui_application import GuiApplication
from gui.controls.panel_control import PanelControl
from gui.core.event_bus import EventBus
from gui.core.gui_event import EventPhase, EventType, GuiEvent
from gui.core.presentation_model import ObservableValue, PresentationModel
from gui.core.scene import Scene
from gui.core.ui_node import UiNode


class _ProbeNode(UiNode):
    def __init__(self, control_id: str, rect: Rect) -> None:
        super().__init__(control_id, rect)
        self.capture_count = 0
        self.target_count = 0
        self.bubble_count = 0
        self.received_phases = []

    def on_event_capture(self, event, _app) -> bool:
        self.capture_count += 1
        self.received_phases.append(event.phase)
        return False

    def handle_event(self, event, _app) -> bool:
        self.target_count += 1
        self.received_phases.append(event.phase)
        return False

    def on_event_bubble(self, event, _app) -> bool:
        self.bubble_count += 1
        self.received_phases.append(event.phase)
        return False


class _FocusableNode(UiNode):
    def __init__(self, control_id: str, rect: Rect) -> None:
        super().__init__(control_id, rect)
        self.set_tab_index(0)
        self.key_events = 0

    def handle_event(self, event, _app) -> bool:
        if event.kind is EventType.KEY_DOWN:
            self.key_events += 1
            return True
        return False


class _DisposableNode(UiNode):
    def __init__(self, control_id: str, rect: Rect) -> None:
        super().__init__(control_id, rect)
        self.mounted = 0
        self.unmounted = 0

    def on_mount(self, _parent) -> None:
        self.mounted += 1

    def on_unmount(self, _parent) -> None:
        self.unmounted += 1


class _MiniPresentationModel(PresentationModel):
    def __init__(self) -> None:
        super().__init__()
        self.title = ObservableValue("before")
        self.history = []


class CoreFoundationProgressionTests(unittest.TestCase):
    def test_scene_routed_event_phases_are_applied(self) -> None:
        pygame.init()
        try:
            app = GuiApplication(Surface((160, 100)))
            scene = Scene()
            probe = scene.add(_ProbeNode("probe", Rect(0, 0, 160, 100)))
            event = GuiEvent(kind=EventType.MOUSE_BUTTON_DOWN, type=pygame.MOUSEBUTTONDOWN, pos=(2, 3), button=1)

            consumed = scene.dispatch(event, app)

            self.assertFalse(consumed)
            self.assertEqual(probe.capture_count, 1)
            self.assertEqual(probe.target_count, 1)
            self.assertEqual(probe.bubble_count, 1)
            self.assertEqual(probe.received_phases, [EventPhase.CAPTURE, EventPhase.TARGET, EventPhase.BUBBLE])
        finally:
            pygame.quit()

    def test_focus_manager_routes_keys_to_focused_control(self) -> None:
        pygame.init()
        try:
            app = GuiApplication(Surface((220, 120)))
            root = app.add(PanelControl("root", Rect(0, 0, 220, 120)))
            focusable = root.add(_FocusableNode("focusable", Rect(10, 10, 80, 20)))

            app.process_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": (12, 12), "button": 1}))
            consumed = app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_a}))

            self.assertTrue(consumed)
            self.assertTrue(focusable.focused)
            self.assertEqual(focusable.key_events, 1)
        finally:
            pygame.quit()

    def test_action_manager_bindings_fire_for_active_scene(self) -> None:
        pygame.init()
        try:
            app = GuiApplication(Surface((180, 100)))
            app.create_scene("alt")
            app.switch_scene("alt")
            seen = {"count": 0}

            def _on_action(_event) -> bool:
                seen["count"] += 1
                return True

            app.actions.register_action("save", _on_action)
            app.actions.bind_key(pygame.K_s, "save", scene="alt")

            consumed = app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_s}))

            self.assertTrue(consumed)
            self.assertEqual(seen["count"], 1)
        finally:
            pygame.quit()

    def test_panel_remove_can_dispose_child(self) -> None:
        panel = PanelControl("panel", Rect(0, 0, 120, 80))
        child = panel.add(_DisposableNode("child", Rect(0, 0, 10, 10)))

        removed = panel.remove(child, dispose=True)

        self.assertTrue(removed)
        self.assertEqual(child.mounted, 1)
        self.assertEqual(child.unmounted, 1)
        self.assertTrue(child.disposed)

    def test_scene_remove_can_dispose_root_node(self) -> None:
        scene = Scene()
        node = scene.add(_DisposableNode("node", Rect(0, 0, 10, 10)))

        removed = scene.remove(node, dispose=True)

        self.assertTrue(removed)
        self.assertEqual(node.mounted, 1)
        self.assertEqual(node.unmounted, 1)
        self.assertTrue(node.disposed)

    def test_presentation_model_observable_updates_and_disposes(self) -> None:
        model = _MiniPresentationModel()
        model.bind(model.title, lambda value: model.history.append(value))

        model.title.value = "after"
        model.dispose()
        model.title.value = "ignored"

        self.assertEqual(model.history, ["after"])

    def test_event_bus_scope_filters_subscribers(self) -> None:
        bus = EventBus()
        seen = []

        bus.subscribe("changed", lambda payload: seen.append(("all", payload)))
        bus.subscribe("changed", lambda payload: seen.append(("life", payload)), scope="life")

        bus.publish("changed", {"v": 1}, scope="life")
        bus.publish("changed", {"v": 2}, scope="other")

        self.assertEqual(seen, [("all", {"v": 1}), ("life", {"v": 1}), ("all", {"v": 2})])

    def test_accessibility_metadata_setters_are_available(self) -> None:
        node = UiNode("node", Rect(0, 0, 10, 10))

        node.set_accessibility(role="button", label="Save")
        node.set_tab_index(2)

        self.assertEqual(node.accessibility_role, "button")
        self.assertEqual(node.accessibility_label, "Save")
        self.assertEqual(node.tab_index, 2)


if __name__ == "__main__":
    unittest.main()
