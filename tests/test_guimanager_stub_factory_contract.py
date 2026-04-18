import unittest
from types import SimpleNamespace

from gui_manager_test_factory import build_gui_manager_stub, build_locking_stub, build_routing_stub, build_state_manager_stub


class GuiManagerStubFactoryContractTests(unittest.TestCase):
    def test_builds_stub_with_required_collaborators(self) -> None:
        gui = build_gui_manager_stub()

        required_attrs = [
            "object_registry",
            "dispatch_bridge",
            "event_delivery",
            "event_input",
            "graphics",
            "layout",
            "lifecycle",
            "lock_flow",
            "pointer",
            "render_flow",
            "task_panel_config",
            "widget_state",
            "workspace",
        ]
        for attr in required_attrs:
            self.assertTrue(hasattr(gui, attr), f"missing collaborator: {attr}")

    def test_build_can_optionally_include_ui_factory(self) -> None:
        gui = build_gui_manager_stub(include_ui_factory=True)
        self.assertTrue(hasattr(gui, "ui_factory"))

    def test_routing_preset_sets_screen_capture_helpers(self) -> None:
        gui = build_gui_manager_stub(preset="routing")

        self.assertEqual(gui._screen_events, [])
        gui.screen_lifecycle.handle_event("evt")
        self.assertEqual(gui._screen_events, ["evt"])
        self.assertEqual(gui.lock_area((1, 2)), (1, 2))

    def test_locking_preset_sets_lock_state_defaults(self) -> None:
        gui = build_gui_manager_stub(preset="locking")

        self.assertIsNotNone(gui.locking_object)
        self.assertTrue(gui.mouse_locked)
        self.assertFalse(gui.mouse_point_locked)
        self.assertIsNotNone(gui.lock_area_rect)

    def test_state_manager_preset_sets_mouse_shims(self) -> None:
        gui = build_gui_manager_stub(preset="state_manager")

        self.assertEqual(gui.get_mouse_pos(), (0, 0))
        gui.set_mouse_pos((8, 9), True)
        self.assertEqual(gui.get_mouse_pos(), (8, 9))

    def test_unknown_preset_raises(self) -> None:
        with self.assertRaises(ValueError):
            build_gui_manager_stub(preset="unknown")  # type: ignore[arg-type]

    def test_convenience_helpers_map_to_expected_presets(self) -> None:
        routing = build_routing_stub()
        locking = build_locking_stub()
        state_manager = build_state_manager_stub()

        self.assertEqual(routing.lock_area((3, 4)), (3, 4))
        self.assertTrue(locking.mouse_locked)
        self.assertEqual(state_manager.get_mouse_pos(), (0, 0))

    def test_convenience_helpers_forward_common_options(self) -> None:
        surface = SimpleNamespace(tag="surface")

        routing = build_routing_stub(surface=surface, include_ui_factory=True)
        locking = build_locking_stub(surface=surface, include_ui_factory=True)
        state_manager = build_state_manager_stub(surface=surface, include_ui_factory=True)

        self.assertIs(routing.surface, surface)
        self.assertIs(locking.surface, surface)
        self.assertIs(state_manager.surface, surface)
        self.assertTrue(hasattr(routing, "ui_factory"))
        self.assertTrue(hasattr(locking, "ui_factory"))
        self.assertTrue(hasattr(state_manager, "ui_factory"))

    def test_state_manager_helper_supports_scheduler_and_tracking_hooks(self) -> None:
        scheduler = object()
        gui = build_state_manager_stub(mouse_pos=(4, 5), scheduler=scheduler, track_set_calls=True)

        self.assertIs(gui._scheduler, scheduler)
        self.assertEqual(gui.get_mouse_pos(), (4, 5))
        gui.set_mouse_pos((7, 8), False)
        self.assertEqual(gui.set_calls[-1], ((7, 8), False))

    def test_state_manager_helper_supports_scheduler_factory(self) -> None:
        marker = object()
        gui = build_state_manager_stub(scheduler_factory=lambda _gui: marker)

        self.assertIs(gui._scheduler, marker)

    def test_state_manager_helper_rejects_conflicting_scheduler_options(self) -> None:
        with self.assertRaises(ValueError):
            build_state_manager_stub(scheduler=object(), scheduler_factory=lambda _gui: object())


if __name__ == "__main__":
    unittest.main()
