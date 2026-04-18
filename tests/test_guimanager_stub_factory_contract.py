import unittest

from gui_manager_test_factory import build_gui_manager_stub


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
        gui._screen_event_handler("evt")
        self.assertEqual(gui._screen_events, ["evt"])
        self.assertEqual(gui.lock_area((1, 2)), (1, 2))

    def test_locking_preset_sets_lock_state_defaults(self) -> None:
        gui = build_gui_manager_stub(preset="locking")

        self.assertIsNotNone(gui.locking_object)
        self.assertTrue(gui.mouse_locked)
        self.assertFalse(gui.mouse_point_locked)
        self.assertIsNotNone(gui.lock_area_rect)

    def test_unknown_preset_raises(self) -> None:
        with self.assertRaises(ValueError):
            build_gui_manager_stub(preset="unknown")  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
