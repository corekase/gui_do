import unittest

from gui_do.overlays.command_palette_manager import CommandEntry, CommandPaletteManager


class _OverlayStub:
    def has_overlay(self, _owner_id):
        return False

    def hide(self, _owner_id):
        return None


class _OverlayLifecycleStub:
    def __init__(self):
        self._open = set()
        self._dismiss_callbacks = {}
        self.show_calls = []
        self.hide_calls = []

    def has_overlay(self, owner_id):
        return str(owner_id) in self._open

    def hide(self, owner_id):
        owner = str(owner_id)
        self.hide_calls.append(owner)
        self._open.discard(owner)
        callback = self._dismiss_callbacks.pop(owner, None)
        if callable(callback):
            callback()
        return None

    def show(self, owner_id, control, **kwargs):
        owner = str(owner_id)
        self.show_calls.append((owner, control, dict(kwargs)))
        self._open.add(owner)
        self._dismiss_callbacks[owner] = kwargs.get("on_dismiss")
        return object()


class _WindowStub:
    def __init__(self, control_id: str, title: str, scene_name: str, visible: bool = False):
        self.control_id = str(control_id)
        self.title = str(title)
        self.scene_name = str(scene_name)
        self.visible = bool(visible)


class _BindingStub:
    def __init__(self, key: str, slot_index: int):
        self.key = str(key)
        self.task_panel_slot_index = int(slot_index)


class _WindowPresentationStub:
    def __init__(self):
        self._bindings = (
            _BindingStub("systems", 1),
            _BindingStub("life", 2),
            _BindingStub("mandel", 3),
        )
        self._windows = {
            "systems": _WindowStub("systems_window", "System", "main", visible=True),
            "life": _WindowStub("life_window", "Life", "main", visible=False),
            "mandel": _WindowStub("mandel_window", "Mandelbrot", "main", visible=False),
        }

    def bindings(self):
        return self._bindings

    def get_window(self, key: str):
        return self._windows.get(str(key))


class _FeatureRegistryStub:
    def __init__(self):
        self._features = {}


class _AppStub:
    def __init__(self):
        self.active_scene_name = "main"
        self.features = _FeatureRegistryStub()

    def scene_names(self):
        return ("main", "control_showcase")

    def scene_pretty_name(self, scene_name: str):
        return {
            "main": "Main",
            "control_showcase": "Control Showcase",
        }.get(str(scene_name), str(scene_name))


class _PaletteAppStub(_AppStub):
    def __init__(self, overlay):
        super().__init__()
        self.overlay = overlay
        self.focus = _FocusStub()

    def switch_scene(self, scene_name: str):
        self.active_scene_name = str(scene_name)
        self.overlay.hide("__command_palette__")


class _FocusStub:
    def __init__(self):
        self.focused_node = None
        self.calls = []

    def set_focus(self, node, *, via_keyboard=False):
        _ = via_keyboard
        self.focused_node = node
        self.calls.append(node)


class TestCommandPaletteGroupedEntries(unittest.TestCase):
    def test_show_is_idempotent_while_already_open(self):
        overlay = _OverlayLifecycleStub()
        app = _PaletteAppStub(overlay)
        manager = CommandPaletteManager(overlay)
        manager.register(CommandEntry(entry_id="custom:one", title="One", action=lambda: None, category="Custom"))

        first = manager.show(app)
        second = manager.show(app)

        self.assertTrue(first.is_open)
        self.assertTrue(second.is_open)
        self.assertEqual(1, len(overlay.show_calls))
        self.assertEqual(0, len(overlay.hide_calls))

    def test_show_enables_focus_lost_dismiss_for_non_palette_control_activation(self):
        overlay = _OverlayLifecycleStub()
        app = _PaletteAppStub(overlay)
        manager = CommandPaletteManager(overlay)
        manager.register(CommandEntry(entry_id="custom:one", title="One", action=lambda: None, category="Custom"))

        manager.show(app)

        self.assertEqual(1, len(overlay.show_calls))
        _, _control, kwargs = overlay.show_calls[0]
        self.assertTrue(bool(kwargs.get("dismiss_on_focus_lost")))
        self.assertEqual("__command_palette___list", str(kwargs.get("focus_owner_id", "")))

    def test_show_moves_focus_to_palette_list_and_hide_restores_previous_focus(self):
        overlay = _OverlayLifecycleStub()
        app = _PaletteAppStub(overlay)
        manager = CommandPaletteManager(overlay)
        manager.register(CommandEntry(entry_id="custom:one", title="One", action=lambda: None, category="Custom"))
        previous_focus = object()
        app.focus.focused_node = previous_focus

        manager.show(app)

        self.assertIsNotNone(manager._open_listview)
        self.assertIs(app.focus.focused_node, manager._open_listview)

        manager.hide()

        self.assertIs(app.focus.focused_node, previous_focus)

    def test_group_order_allows_custom_between_scene_and_window_groups(self):
        manager = CommandPaletteManager(_OverlayStub())
        app = _AppStub()
        window_presentation = _WindowPresentationStub()

        manager.configure_builtin_entry_groups(
            app,
            window_presentation=window_presentation,
            include_scene_entries=True,
            include_window_entries=True,
            group_order=("scenes", "custom", "windows"),
            custom_entries_provider=lambda _app: (
                CommandEntry(
                    entry_id="custom:refresh",
                    title="Refresh",
                    action=lambda: None,
                    category="Custom",
                ),
            ),
        )

        manager._before_show_callback()
        entry_ids = [entry.entry_id for entry in manager.entries()]

        self.assertEqual(
            [
                "scene:control_showcase",
                "custom:refresh",
                "window:main:systems_window",
                "window:main:life_window",
                "window:main:mandel_window",
            ],
            entry_ids,
        )

    def test_disable_scene_and_window_groups_emits_no_builtin_entries(self):
        manager = CommandPaletteManager(_OverlayStub())
        app = _AppStub()

        manager.configure_builtin_entry_groups(
            app,
            include_scene_entries=False,
            include_window_entries=False,
            group_order=("scenes", "windows", "custom"),
            custom_entries_provider=None,
        )

        manager._before_show_callback()
        self.assertEqual([], manager.entries())

    def test_custom_provider_can_be_no_arg_callable(self):
        manager = CommandPaletteManager(_OverlayStub())
        app = _AppStub()

        manager.configure_builtin_entry_groups(
            app,
            include_scene_entries=False,
            include_window_entries=False,
            group_order=("custom",),
            custom_entries_provider=lambda: (
                CommandEntry(
                    entry_id="custom:retile",
                    title="Retile",
                    action=lambda: None,
                    category="Custom",
                ),
            ),
        )

        manager._before_show_callback()
        entry_ids = [entry.entry_id for entry in manager.entries()]
        self.assertEqual(["custom:retile"], entry_ids)

    def test_scene_scoped_entries_are_filtered_to_active_scene(self):
        manager = CommandPaletteManager(_OverlayStub())
        app = _AppStub()

        manager.configure_builtin_entry_groups(
            app,
            include_scene_entries=False,
            include_window_entries=False,
            group_order=("custom",),
            custom_entries_provider=lambda _app: (
                CommandEntry(
                    entry_id="custom:main_only",
                    title="Main Only",
                    action=lambda: None,
                    category="Custom",
                    scene_name="main",
                ),
                CommandEntry(
                    entry_id="custom:showcase_only",
                    title="Showcase Only",
                    action=lambda: None,
                    category="Custom",
                    scene_name="control_showcase",
                ),
            ),
        )

        manager._before_show_callback()
        self.assertEqual(["custom:main_only"], [entry.entry_id for entry in manager.entries()])

        app.active_scene_name = "control_showcase"
        manager._invalidate_entry_projection()
        self.assertEqual(["custom:showcase_only"], [entry.entry_id for entry in manager.entries()])

    def test_selecting_window_toggle_entry_dismisses_palette(self):
        overlay = _OverlayLifecycleStub()
        app = _PaletteAppStub(overlay)
        manager = CommandPaletteManager(overlay)
        calls = []
        manager.register(
            CommandEntry(
                entry_id="window:main:logs",
                title="Logs",
                action=lambda: calls.append("toggle"),
                category="Windows",
                render_kind="window_toggle",
                window_visible=False,
            )
        )

        manager.show(app)
        listview = manager._open_listview
        self.assertIsNotNone(listview)
        item = listview._items[0]

        listview._on_select(0, item)

        self.assertFalse(manager.is_open)
        self.assertEqual(["toggle"], calls)
        self.assertTrue(bool(item.data.window_visible))
        self.assertEqual(1, len(overlay.show_calls))
        self.assertEqual(1, len(overlay.hide_calls))

    def test_mouse_activation_then_select_callback_does_not_double_toggle(self):
        overlay = _OverlayLifecycleStub()
        app = _PaletteAppStub(overlay)
        manager = CommandPaletteManager(overlay)
        calls = []
        manager.register(
            CommandEntry(
                entry_id="window:main:inspector",
                title="Inspector",
                action=lambda: calls.append("toggle"),
                category="Windows",
                render_kind="window_toggle",
                window_visible=False,
            )
        )

        manager.show(app)
        listview = manager._open_listview
        self.assertIsNotNone(listview)
        item = listview._items[0]
        pos = (listview.rect.x + 1, listview.rect.y + 1)

        handled = manager.try_activate_action_at(pos)
        self.assertTrue(handled)
        self.assertEqual(["toggle"], calls)
        self.assertTrue(bool(item.data.window_visible))

        # Simulate the list-view select callback on the same click path.
        listview._on_select(0, item)

        self.assertTrue(manager.is_open)
        self.assertEqual(["toggle"], calls)
        self.assertTrue(bool(item.data.window_visible))
        self.assertEqual(0, len(overlay.hide_calls))

    def test_mouse_activation_reopens_palette_when_action_path_dismisses_it(self):
        overlay = _OverlayLifecycleStub()
        app = _PaletteAppStub(overlay)
        manager = CommandPaletteManager(overlay)
        calls = []

        def _toggle_and_dismiss():
            calls.append("toggle")
            overlay.hide("__command_palette__")

        manager.register(
            CommandEntry(
                entry_id="window:main:inspector",
                title="Inspector",
                action=_toggle_and_dismiss,
                category="Windows",
                render_kind="window_toggle",
                window_visible=False,
            )
        )

        manager.show(app)
        listview = manager._open_listview
        self.assertIsNotNone(listview)
        item = listview._items[0]
        pos = (listview.rect.x + 1, listview.rect.y + 1)

        handled = manager.try_activate_action_at(pos)

        self.assertTrue(handled)
        self.assertTrue(manager.is_open)
        self.assertEqual(["toggle"], calls)
        self.assertTrue(bool(item.data.window_visible))
        self.assertEqual(2, len(overlay.show_calls))
        self.assertEqual(["__command_palette__"], overlay.hide_calls)

    def test_selecting_command_toggle_entry_dismisses_palette(self):
        overlay = _OverlayLifecycleStub()
        app = _PaletteAppStub(overlay)
        manager = CommandPaletteManager(overlay)
        state = {"enabled": False}
        calls = []

        def _toggle():
            state["enabled"] = not state["enabled"]
            calls.append("toggle")

        manager.register(
            CommandEntry(
                entry_id="command:main:automatic_layout",
                title="Automatic Layout Off",
                action=_toggle,
                category="Commands",
                scene_name="main",
                render_kind="command_toggle",
                toggle_state=False,
            )
        )

        manager.show(app)
        listview = manager._open_listview
        self.assertIsNotNone(listview)
        item = listview._items[0]

        listview._on_select(0, item)

        self.assertFalse(manager.is_open)
        self.assertEqual(["toggle"], calls)
        self.assertTrue(state["enabled"])
        self.assertEqual(1, len(overlay.hide_calls))

    def test_mouse_activation_command_toggle_stays_open_and_refreshes_state(self):
        overlay = _OverlayLifecycleStub()
        app = _PaletteAppStub(overlay)
        manager = CommandPaletteManager(overlay)
        state = {"enabled": False}
        calls = []

        def _toggle():
            state["enabled"] = not state["enabled"]
            calls.append("toggle")

        def _refresh(entry: CommandEntry) -> None:
            entry.toggle_state = state["enabled"]
            entry.title = "Automatic Layout On" if state["enabled"] else "Automatic Layout Off"

        manager.register(
            CommandEntry(
                entry_id="command:main:automatic_layout",
                title="Automatic Layout Off",
                action=_toggle,
                category="Commands",
                scene_name="main",
                render_kind="command_toggle",
                toggle_state=False,
                refresh_after_action=_refresh,
            )
        )

        manager.show(app)
        listview = manager._open_listview
        self.assertIsNotNone(listview)
        item = listview._items[0]
        pos = (listview.rect.x + 1, listview.rect.y + 1)

        handled = manager.try_activate_action_at(pos)
        self.assertTrue(handled)
        self.assertTrue(manager.is_open)
        self.assertEqual(["toggle"], calls)
        self.assertTrue(state["enabled"])
        self.assertTrue(bool(item.data.toggle_state))
        self.assertEqual("Automatic Layout On", item.data.title)

        listview._on_select(0, item)

        self.assertTrue(manager.is_open)
        self.assertEqual(["toggle"], calls)
        self.assertEqual(0, len(overlay.hide_calls))

    def test_mouse_activation_command_button_stays_open(self):
        overlay = _OverlayLifecycleStub()
        app = _PaletteAppStub(overlay)
        manager = CommandPaletteManager(overlay)
        calls = []

        manager.register(
            CommandEntry(
                entry_id="command:main:layout_now",
                title="Layout Windows Now",
                action=lambda: calls.append("layout"),
                category="Commands",
                scene_name="main",
                render_kind="command_button",
            )
        )

        manager.show(app)
        listview = manager._open_listview
        self.assertIsNotNone(listview)
        item = listview._items[0]
        pos = (listview.rect.x + 1, listview.rect.y + 1)

        handled = manager.try_activate_action_at(pos)

        self.assertTrue(handled)
        self.assertTrue(manager.is_open)
        self.assertEqual(["layout"], calls)

        listview._on_select(0, item)

        self.assertTrue(manager.is_open)
        self.assertEqual(["layout"], calls)
        self.assertEqual(0, len(overlay.hide_calls))

    def test_action_bind_activation_does_not_require_multiple_left_clicks_for_command_button(self):
        overlay = _OverlayLifecycleStub()
        app = _PaletteAppStub(overlay)
        manager = CommandPaletteManager(overlay)
        calls = []

        manager.register(
            CommandEntry(
                entry_id="command:main:layout_now",
                title="Layout Windows Now",
                action=lambda: calls.append("layout"),
                category="Commands",
                scene_name="main",
                render_kind="command_button",
            )
        )

        manager.show(app)
        listview = manager._open_listview
        self.assertIsNotNone(listview)
        item = listview._items[0]
        pos = (listview.rect.x + 1, listview.rect.y + 1)

        # Action-bind path should not suppress a later distinct left-click select.
        handled = manager.try_activate_action_at(pos, suppress_followup_select=False)
        self.assertTrue(handled)
        self.assertTrue(manager.is_open)
        self.assertEqual(["layout"], calls)

        listview._on_select(0, item)

        self.assertFalse(manager.is_open)
        self.assertEqual(["layout", "layout"], calls)
        self.assertEqual(1, len(overlay.hide_calls))

    def test_mouse_activation_default_entry_stays_open(self):
        overlay = _OverlayLifecycleStub()
        app = _PaletteAppStub(overlay)
        manager = CommandPaletteManager(overlay)
        calls = []

        manager.register(
            CommandEntry(
                entry_id="scene:control_showcase",
                title="Control Showcase",
                action=lambda: calls.append("scene"),
                category="Scenes",
            )
        )

        manager.show(app)
        listview = manager._open_listview
        self.assertIsNotNone(listview)
        item = listview._items[0]
        pos = (listview.rect.x + 1, listview.rect.y + 1)

        handled = manager.try_activate_action_at(pos)

        self.assertTrue(handled)
        self.assertTrue(manager.is_open)
        self.assertEqual(["scene"], calls)

        listview._on_select(0, item)

        self.assertTrue(manager.is_open)
        self.assertEqual(["scene"], calls)
        self.assertEqual(0, len(overlay.hide_calls))

    def test_mouse_activation_scene_change_does_not_reopen_or_leave_stale_suppression(self):
        overlay = _OverlayLifecycleStub()
        app = _PaletteAppStub(overlay)
        manager = CommandPaletteManager(overlay)
        calls = []

        manager.register(
            CommandEntry(
                entry_id="scene:control_showcase",
                title="Control Showcase",
                action=lambda: (calls.append("scene"), app.switch_scene("control_showcase")),
                category="Scenes",
            )
        )

        manager.show(app)
        listview = manager._open_listview
        self.assertIsNotNone(listview)
        item = listview._items[0]
        pos = (listview.rect.x + 1, listview.rect.y + 1)

        handled = manager.try_activate_action_at(pos)

        self.assertTrue(handled)
        self.assertFalse(manager.is_open)
        self.assertEqual(["scene"], calls)
        self.assertEqual("control_showcase", app.active_scene_name)

        manager.show(app)
        reopened_listview = manager._open_listview
        self.assertIsNotNone(reopened_listview)
        reopened_item = reopened_listview._items[0]
        reopened_listview._on_select(0, reopened_item)

        self.assertEqual(["scene", "scene"], calls)
        self.assertFalse(manager.is_open)

    def test_selecting_non_window_entry_still_closes_palette(self):
        overlay = _OverlayLifecycleStub()
        app = _PaletteAppStub(overlay)
        manager = CommandPaletteManager(overlay)
        calls = []
        manager.register(
            CommandEntry(
                entry_id="custom:refresh",
                title="Refresh",
                action=lambda: calls.append("run"),
                category="Custom",
            )
        )

        manager.show(app)
        listview = manager._open_listview
        self.assertIsNotNone(listview)
        item = listview._items[0]

        listview._on_select(0, item)

        self.assertFalse(manager.is_open)
        self.assertEqual(["run"], calls)
        self.assertEqual(1, len(overlay.hide_calls))


if __name__ == "__main__":
    unittest.main()
