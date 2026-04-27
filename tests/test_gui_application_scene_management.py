"""Tests for GuiApplication scene management APIs: scene_names, has_scene, remove_scene."""
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pygame

from gui_do.app.gui_application import GuiApplication
from gui_do.controls.window_control import WindowControl
from gui_do.controls.label_control import LabelControl
from gui_do.controls.button_control import ButtonControl
from gui_do.controls.canvas_control import CanvasControl
from gui_do.controls.slider_control import SliderControl
from gui_do.controls.toggle_control import ToggleControl
from gui_do.layout.layout_axis import LayoutAxis
from gui_do import FeatureMessage, LogicFeature, Feature, RoutedFeature


def _make_app() -> GuiApplication:
    surface = MagicMock(spec=pygame.Surface)
    surface.get_rect.return_value = pygame.Rect(0, 0, 800, 600)
    surface.get_size.return_value = (800, 600)
    with patch("pygame.mouse.get_pos", return_value=(0, 0)), \
         patch("pygame.mouse.set_pos"):
        return GuiApplication.__new__(GuiApplication)


class GuiApplicationSceneManagementSetup(unittest.TestCase):
    """Base providing a minimal GuiApplication instance for scene tests."""

    def setUp(self) -> None:
        pygame.init()
        self.surface = pygame.display.set_mode((200, 150))
        with patch("pygame.mouse.get_pos", return_value=(0, 0)):
            self.app = GuiApplication(self.surface)

    def tearDown(self) -> None:
        self.app.shutdown()
        pygame.quit()


class SceneNamesTests(GuiApplicationSceneManagementSetup):

    def test_scene_names_contains_default_on_init(self) -> None:
        self.assertIn("default", self.app.scene_names())

    def test_scene_names_returns_list(self) -> None:
        self.assertIsInstance(self.app.scene_names(), list)

    def test_scene_names_grows_after_create_scene(self) -> None:
        self.app.create_scene("extra")
        self.assertIn("extra", self.app.scene_names())

    def test_scene_names_contains_active_scene(self) -> None:
        self.assertIn(self.app.active_scene_name, self.app.scene_names())

    def test_scene_names_snapshot_is_independent(self) -> None:
        names = self.app.scene_names()
        self.app.create_scene("new_scene")
        # Original snapshot unchanged
        self.assertNotIn("new_scene", names)


class HasSceneTests(GuiApplicationSceneManagementSetup):

    def test_has_scene_true_for_default(self) -> None:
        self.assertTrue(self.app.has_scene("default"))

    def test_has_scene_false_for_unknown(self) -> None:
        self.assertFalse(self.app.has_scene("nonexistent"))

    def test_has_scene_true_after_create_scene(self) -> None:
        self.app.create_scene("fresh")
        self.assertTrue(self.app.has_scene("fresh"))

    def test_has_scene_false_after_remove_scene(self) -> None:
        self.app.create_scene("temp")
        self.app.remove_scene("temp")
        self.assertFalse(self.app.has_scene("temp"))


class RemoveSceneTests(GuiApplicationSceneManagementSetup):

    def test_remove_scene_returns_false_for_unknown(self) -> None:
        self.assertFalse(self.app.remove_scene("does_not_exist"))

    def test_remove_scene_returns_false_for_active_scene(self) -> None:
        # "default" is the active scene — must not be removable
        self.assertFalse(self.app.remove_scene(self.app.active_scene_name))

    def test_remove_scene_returns_true_for_inactive(self) -> None:
        self.app.create_scene("side")
        self.assertTrue(self.app.remove_scene("side"))

    def test_remove_scene_removes_from_scene_names(self) -> None:
        self.app.create_scene("gone")
        self.app.remove_scene("gone")
        self.assertNotIn("gone", self.app.scene_names())

    def test_remove_scene_active_remains_after_inactive_removed(self) -> None:
        self.app.create_scene("side")
        self.app.remove_scene("side")
        self.assertIn(self.app.active_scene_name, self.app.scene_names())

    def test_remove_scene_idempotent(self) -> None:
        self.app.create_scene("once")
        self.assertTrue(self.app.remove_scene("once"))
        self.assertFalse(self.app.remove_scene("once"))

    def test_remove_scene_does_not_affect_other_scenes(self) -> None:
        self.app.create_scene("keep")
        self.app.create_scene("drop")
        self.app.remove_scene("drop")
        self.assertTrue(self.app.has_scene("keep"))

    def test_removed_scene_cannot_be_switched_to(self) -> None:
        self.app.create_scene("away")
        self.app.remove_scene("away")
        with self.assertRaises(ValueError):
            self.app.switch_scene("away")


class _StubFeature(Feature):
    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.host_seen = None
        self.bind_calls = 0
        self.shutdown_calls = 0
        self.unregister_calls = 0
        self.update_calls = 0

    def on_register(self, host) -> None:
        self.host_seen = host

    def bind_runtime(self, host) -> None:
        del host
        self.bind_calls += 1

    def shutdown_runtime(self, host) -> None:
        del host
        self.shutdown_calls += 1

    def on_unregister(self, host) -> None:
        del host
        self.unregister_calls += 1

    def on_update(self, host) -> None:
        del host
        self.update_calls += 1


class _StubLogicFeature(LogicFeature):
    def __init__(self, name: str = "logic") -> None:
        super().__init__(name)


class _EchoLogicFeature(LogicFeature):
    def __init__(self, name: str = "logic") -> None:
        super().__init__(name)
        self._counter = 0

    def on_logic_command(self, _host, message: FeatureMessage) -> None:
        if message.command != "echo":
            return
        self._counter += 1
        self.send_message(
            message.sender,
            {
                "topic": "logic.echo",
                "count": self._counter,
                "value": message.get("value"),
            },
        )


class _LogicConsumerFeature(Feature):
    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.received_payloads = []

    def on_update(self, _host) -> None:
        while self.has_messages():
            payload = self.pop_message()
            if payload is not None:
                self.received_payloads.append(payload)


class _RoutedCaptureFeature(RoutedFeature):
    def __init__(self, name: str = "routed") -> None:
        super().__init__(name)
        self.seen = []

    def message_handlers(self):
        return {
            "alpha": self._on_alpha,
        }

    def _on_alpha(self, _host, message: FeatureMessage) -> None:
        self.seen.append((message.sender, message.get("value")))


class PartApiTests(GuiApplicationSceneManagementSetup):

    def test_register_and_get_feature(self) -> None:
        feature = _StubFeature("alpha")
        self.app.register_feature(feature, host=self.app)
        self.assertIs(self.app.get_feature("alpha"), feature)
        self.assertIn("alpha", self.app.feature_names())

    def test_unregister_feature(self) -> None:
        self.app.register_feature(_StubFeature("alpha"), host=self.app)
        self.assertTrue(self.app.unregister_feature("alpha"))
        self.assertIsNone(self.app.get_feature("alpha"))

    def test_unregister_part_shuts_down_bound_runtime(self) -> None:
        feature = _StubFeature("alpha")
        self.app.register_feature(feature, host=self.app)
        self.app.bind_features_runtime(self.app)

        self.assertTrue(self.app.unregister_feature("alpha"))

        self.assertEqual(1, feature.bind_calls)
        self.assertEqual(1, feature.shutdown_calls)
        self.assertEqual(1, feature.unregister_calls)

    def test_send_feature_message(self) -> None:
        sender = _StubFeature("sender")
        target = _StubFeature("target")
        self.app.register_feature(sender, host=self.app)
        self.app.register_feature(target, host=self.app)
        sent = self.app.send_feature_message("sender", "target", {"kind": "ping"})
        self.assertTrue(sent)
        self.assertTrue(target.has_messages())
        msg = target.pop_message()
        self.assertIsNotNone(msg)
        self.assertEqual("ping", msg["kind"])
        self.assertEqual("sender", msg.sender)
        self.assertEqual("target", msg.target)

    def test_register_and_run_feature_runnable(self) -> None:
        self.app.register_feature(_StubFeature("worker"), host=self.app)
        self.app.register_feature_runnable("worker", "sum", lambda x, y: x + y)
        self.assertEqual(7, self.app.run_feature_runnable("worker", "sum", 3, 4))

    def test_bind_logic_and_send_logic_message(self) -> None:
        consumer = _StubFeature("consumer")
        logic = _StubLogicFeature("logic")
        self.app.register_feature(consumer, host=self.app)
        self.app.register_feature(logic, host=self.app)

        self.app.bind_feature_logic("consumer", "logic")
        sent = self.app.send_feature_logic_message("consumer", {"command": "snapshot"})

        self.assertTrue(sent)
        self.assertEqual("logic", self.app.get_feature_logic("consumer"))
        self.assertTrue(logic.has_messages())
        payload = logic.pop_message()
        self.assertIsNotNone(payload)
        self.assertEqual("consumer", payload.sender)
        self.assertEqual("logic", payload.target)

    def test_unbind_logic_returns_true_when_alias_present(self) -> None:
        consumer = _StubFeature("consumer")
        logic = _StubLogicFeature("logic")
        self.app.register_feature(consumer, host=self.app)
        self.app.register_feature(logic, host=self.app)
        self.app.bind_feature_logic("consumer", "logic", alias="life")

        removed = self.app.unbind_feature_logic("consumer", alias="life")

        self.assertTrue(removed)
        self.assertIsNone(self.app.get_feature_logic("consumer", alias="life"))

    def test_non_owner_consumer_can_use_logic_part_and_receive_reply(self) -> None:
        consumer = _LogicConsumerFeature("consumer")
        logic = _EchoLogicFeature("logic")
        self.app.register_feature(consumer, host=self.app)
        self.app.register_feature(logic, host=self.app)
        self.app.bind_feature_logic("consumer", "logic", alias="shared")

        sent = self.app.send_feature_logic_message("consumer", {"command": "echo", "value": "one"}, alias="shared")
        self.app.features.update_features()
        self.app.features.update_features()

        self.assertTrue(sent)
        self.assertEqual(1, len(consumer.received_payloads))
        payload = consumer.received_payloads[0]
        self.assertEqual("logic.echo", payload["topic"])
        self.assertEqual("one", payload["value"])
        self.assertEqual(1, payload["count"])
        self.assertEqual("logic", payload.sender)
        self.assertEqual("consumer", payload.target)

    def test_multiple_non_owner_consumers_can_share_one_logic_part(self) -> None:
        logic = _EchoLogicFeature("logic")
        consumer_a = _LogicConsumerFeature("consumer_a")
        consumer_b = _LogicConsumerFeature("consumer_b")
        self.app.register_feature(logic, host=self.app)
        self.app.register_feature(consumer_a, host=self.app)
        self.app.register_feature(consumer_b, host=self.app)
        self.app.bind_feature_logic("consumer_a", "logic", alias="shared")
        self.app.bind_feature_logic("consumer_b", "logic", alias="shared")

        self.assertTrue(self.app.send_feature_logic_message("consumer_a", {"command": "echo", "value": "a"}, alias="shared"))
        self.assertTrue(self.app.send_feature_logic_message("consumer_b", {"command": "echo", "value": "b"}, alias="shared"))
        self.app.features.update_features()
        self.app.features.update_features()

        self.assertEqual(1, len(consumer_a.received_payloads))
        self.assertEqual(1, len(consumer_b.received_payloads))
        self.assertEqual("a", consumer_a.received_payloads[0]["value"])
        self.assertEqual("b", consumer_b.received_payloads[0]["value"])
        self.assertEqual("logic", consumer_a.received_payloads[0].sender)
        self.assertEqual("logic", consumer_b.received_payloads[0].sender)

    def test_app_shutdown_shuts_down_bound_parts_once(self) -> None:
        feature = _StubFeature("alpha")
        self.app.register_feature(feature, host=self.app)
        self.app.bind_features_runtime(self.app)

        self.app.shutdown()
        self.app.shutdown()

        self.assertEqual(1, feature.bind_calls)
        self.assertEqual(1, feature.shutdown_calls)

    def test_part_font_role_helper_registers_namespaced_role(self) -> None:
        feature = _StubFeature("alpha")

        role_name = feature.register_font_role(self.app, "window_title", size=18)

        self.assertEqual("feature.alpha.window_title", role_name)
        self.assertEqual("feature.alpha.window_title", feature.font_role("window_title"))
        self.assertTrue(self.app.theme.fonts.has_role("feature.alpha.window_title"))

    def test_app_run_delegates_to_ui_engine(self) -> None:
        with patch("gui_do.loop.ui_engine.UiEngine.run", return_value=12) as run_mock:
            frames = self.app.run(target_fps=75, max_frames=3)

        self.assertEqual(12, frames)
        run_mock.assert_called_once_with(max_frames=3)

    def test_routed_message_part_dispatches_registered_topics(self) -> None:
        routed = _RoutedCaptureFeature("routed")
        sender = _StubFeature("sender")
        self.app.register_feature(routed, host=self.app)
        self.app.register_feature(sender, host=self.app)

        self.assertTrue(self.app.send_feature_message("sender", "routed", {"topic": "alpha", "value": 7}))
        self.app.features.update_features()

        self.assertEqual(routed.seen, [("sender", 7)])

    def test_routed_message_part_ignores_unknown_topics(self) -> None:
        routed = _RoutedCaptureFeature("routed")
        sender = _StubFeature("sender")
        self.app.register_feature(routed, host=self.app)
        self.app.register_feature(sender, host=self.app)

        self.assertTrue(self.app.send_feature_message("sender", "routed", {"topic": "beta", "value": 3}))
        self.app.features.update_features()

        self.assertEqual(routed.seen, [])


class FeatureUiTypesTests(GuiApplicationSceneManagementSetup):

    def test_read_feature_ui_types_returns_same_instance(self) -> None:
        ui_types_a = self.app.read_feature_ui_types()
        ui_types_b = self.app.read_feature_ui_types()
        self.assertIs(ui_types_a, ui_types_b)

    def test_read_feature_ui_types_contains_expected_bindings(self) -> None:
        ui_types = self.app.read_feature_ui_types()
        self.assertIs(ui_types.window_control_cls, WindowControl)
        self.assertIs(ui_types.label_control_cls, LabelControl)
        self.assertIs(ui_types.button_control_cls, ButtonControl)
        self.assertIs(ui_types.canvas_control_cls, CanvasControl)
        self.assertIs(ui_types.slider_control_cls, SliderControl)
        self.assertIs(ui_types.toggle_control_cls, ToggleControl)
        self.assertIs(ui_types.layout_axis_cls, LayoutAxis)


class PristineDefaultsTests(GuiApplicationSceneManagementSetup):

    def test_default_scene_has_black_pristine_surface(self) -> None:
        target = pygame.Surface(self.surface.get_size())

        restored = self.app.restore_pristine(surface=target)

        self.assertTrue(restored)
        self.assertEqual(target.get_at((0, 0))[:3], (0, 0, 0))

    def test_new_scene_has_black_pristine_surface(self) -> None:
        self.app.create_scene("alt")
        self.app.switch_scene("alt")
        target = pygame.Surface(self.surface.get_size())

        restored = self.app.restore_pristine(surface=target)

        self.assertTrue(restored)
        self.assertEqual(target.get_at((0, 0))[:3], (0, 0, 0))

    def test_set_pristine_overwrites_default_surface(self) -> None:
        source = pygame.Surface((4, 4)).convert()
        source.fill((12, 34, 56))
        self.app.set_pristine(source)
        target = pygame.Surface(self.surface.get_size())

        restored = self.app.restore_pristine(surface=target)

        self.assertTrue(restored)
        self.assertEqual(target.get_at((0, 0))[:3], (12, 34, 56))


class ScreenLifecycleChainingTests(GuiApplicationSceneManagementSetup):

    def test_chain_screen_lifecycle_calls_base_then_layers(self) -> None:
        order = []
        self.app.set_screen_lifecycle(
            preamble=lambda: order.append("base_pre"),
            postamble=lambda: order.append("base_post"),
        )
        self.app.chain_screen_lifecycle(
            preamble=lambda: order.append("layer1_pre"),
            postamble=lambda: order.append("layer1_post"),
        )
        self.app.chain_screen_lifecycle(
            preamble=lambda: order.append("layer2_pre"),
            postamble=lambda: order.append("layer2_post"),
        )

        self.app._screen_preamble()
        self.app._screen_postamble()

        self.assertEqual(
            order,
            ["base_pre", "layer1_pre", "layer2_pre", "base_post", "layer1_post", "layer2_post"],
        )

    def test_chain_screen_lifecycle_event_handler_short_circuits_on_consumed(self) -> None:
        calls = []
        self.app.set_screen_lifecycle(event_handler=lambda _event: (calls.append("base") or False))
        self.app.chain_screen_lifecycle(event_handler=lambda _event: (calls.append("layer1") or True))
        self.app.chain_screen_lifecycle(event_handler=lambda _event: (calls.append("layer2") or False))

        consumed = self.app._screen_event_handler(SimpleNamespace())

        self.assertTrue(consumed)
        self.assertEqual(calls, ["base", "layer1"])

    def test_chain_screen_lifecycle_dispose_removes_only_target_layer(self) -> None:
        order = []
        self.app.set_screen_lifecycle(preamble=lambda: order.append("base"))
        dispose_layer_1 = self.app.chain_screen_lifecycle(preamble=lambda: order.append("layer1"))
        self.app.chain_screen_lifecycle(preamble=lambda: order.append("layer2"))

        removed = dispose_layer_1()
        self.app._screen_preamble()

        self.assertTrue(removed)
        self.assertEqual(order, ["base", "layer2"])

    def test_scene_scoped_screen_lifecycle_runs_only_for_active_scene(self) -> None:
        order = []
        self.app.create_scene("alt")
        self.app.chain_screen_lifecycle(preamble=lambda: order.append("default"), scene_name="default")
        self.app.chain_screen_lifecycle(preamble=lambda: order.append("alt"), scene_name="alt")

        self.app._screen_preamble()
        self.app.switch_scene("alt")
        self.app._screen_preamble()

        self.assertEqual(order, ["default", "alt"])


class SceneSuspensionTests(GuiApplicationSceneManagementSetup):

    def test_scene_scoped_part_updates_suspend_when_scene_inactive(self) -> None:
        self.app.create_scene("alt")
        default_part = _StubFeature("default_part")
        default_part.scene_name = "default"
        alt_part = _StubFeature("alt_part")
        alt_part.scene_name = "alt"
        self.app.register_feature(default_part, host=self.app)
        self.app.register_feature(alt_part, host=self.app)

        self.app.features.update_features()
        self.app.switch_scene("alt")
        self.app.features.update_features()

        self.assertEqual(default_part.update_calls, 1)
        self.assertEqual(alt_part.update_calls, 1)

    def test_scene_timers_are_suspended_until_scene_is_active(self) -> None:
        self.app.create_scene("alt")
        default_ticks = []
        alt_ticks = []

        self.app.timers.add_timer("default_tick", 0.1, lambda: default_ticks.append(True))
        self.app.switch_scene("alt")
        self.app.timers.add_timer("alt_tick", 0.1, lambda: alt_ticks.append(True))

        self.app.switch_scene("default")
        self.app.update(0.11)
        self.assertEqual(len(default_ticks), 1)
        self.assertEqual(len(alt_ticks), 0)

        self.app.switch_scene("alt")
        self.app.update(0.11)
        self.assertEqual(len(default_ticks), 1)
        self.assertEqual(len(alt_ticks), 1)


class ScenePrewarmTests(GuiApplicationSceneManagementSetup):

    def test_prewarm_scene_delegates_to_feature_manager(self) -> None:
        self.app.create_scene("control_showcase")
        with patch.object(self.app.features, "prewarm_features", return_value=3) as prewarm_mock:
            warmed = self.app.prewarm_scene("control_showcase")

        self.assertEqual(3, warmed)
        prewarm_mock.assert_called_once()
        args, kwargs = prewarm_mock.call_args
        self.assertIsNone(args[0])
        self.assertIs(args[2], self.app._scene_runtime("control_showcase").theme)
        self.assertEqual(kwargs["scene_name"], "control_showcase")
        self.assertFalse(kwargs["force"])


if __name__ == "__main__":
    unittest.main()
