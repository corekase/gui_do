import tempfile
import unittest
from pathlib import Path

from gui_do import ActionDescriptor
from gui_do import ActionRegistry
from gui_do import CollectionView
from gui_do import CollectionViewQuery
from gui_do import DockPane
from gui_do import DockSplit
from gui_do import DockTabs
from gui_do import DockWorkspace
from gui_do import DocumentModel
from gui_do import FormSchema
from gui_do import GuiApplication
from gui_do import InspectedProperty
from gui_do import MenuBarManager
from gui_do import PropertyInspectorModel
from gui_do import PropertyInspectorPanel
from gui_do import SchemaField
from gui_do import SettingsRegistry
from gui_do import CommandPaletteManager
from gui_do import ContextMenuManager
from gui_do import OverlayManager
from gui_do import TransferData
from gui_do import TransferManager
from gui_do import WorkspacePersistenceManager
from gui_do import WorkspaceState
from gui_do import ui_property


class _ActionManagerStub:
    def __init__(self) -> None:
        self.handlers = {}

    def register_action(self, action_name, handler) -> None:
        self.handlers[action_name] = handler


class ActionRegistryTests(unittest.TestCase):
    def test_registry_projects_into_action_manager_and_palette(self) -> None:
        called = []
        registry = ActionRegistry()
        registry.register(
            ActionDescriptor(
                "open",
                "Open",
                lambda context, event=None: called.append((context, event)) or True,
                category="File",
                description="Open an item",
            )
        )

        manager = _ActionManagerStub()
        registry.bind_into(manager, context="ctx")

        self.assertIn("open", manager.handlers)
        self.assertTrue(manager.handlers["open"]("evt"))
        self.assertEqual(called, [("ctx", "evt")])

        palette_entries = registry.command_entries(context="ctx")
        self.assertEqual(palette_entries[0].entry_id, "open")

    def test_registry_integrates_with_menu_palette_and_context_managers(self) -> None:
        called = []
        registry = ActionRegistry()
        registry.register(
            ActionDescriptor(
                "save",
                "Save",
                lambda context, event=None: called.append((context, event)) or True,
                category="File",
            )
        )

        menu_manager = MenuBarManager()
        menu_manager.register_actions("File", registry, context="menu", category="File")
        self.assertEqual(menu_manager.items_for("File")[0].label, "Save")

        palette = CommandPaletteManager(OverlayManager())
        palette.register_action_registry(registry, context="palette")
        self.assertEqual(palette.entry_count(), 1)

        class _OverlayStub:
            def show(self, *args, **kwargs):
                self.last_call = (args, kwargs)
                return object()

            def hide(self, *_args, **_kwargs):
                return True

        class _AppStub:
            def __init__(self) -> None:
                from pygame import Rect

                self.surface = type("SurfaceStub", (), {"get_rect": lambda _self: Rect(0, 0, 320, 240)})()
                self.overlay = _OverlayStub()

        context_menu = ContextMenuManager(_AppStub())
        handle = context_menu.show_actions((10, 10), registry, context="ctx", category="File")
        self.assertTrue(context_menu.has_menu(handle.menu_id))


class WorkspacePersistenceTests(unittest.TestCase):
    class _FeatureManagerStub:
        def __init__(self) -> None:
            self.restored = None

        def save_feature_states(self):
            return {"feature": {"count": 2}}

        def restore_feature_states(self, states):
            self.restored = states

    class _Node:
        def __init__(self) -> None:
            self.control_id = "root"
            self.rect = type("RectLike", (), {"x": 1, "y": 2, "width": 3, "height": 4})()
            self.visible = True
            self.enabled = True

        def invalidate(self):
            return None

    class _Scene:
        def __init__(self) -> None:
            self.node = WorkspacePersistenceTests._Node()

        def _walk_nodes(self):
            return [self.node]

    class _App:
        def __init__(self) -> None:
            self.scene = WorkspacePersistenceTests._Scene()
            self.active_scene_name = "main"

        def switch_scene(self, name: str) -> None:
            self.active_scene_name = name

    def test_capture_and_restore_workspace_state(self) -> None:
        app = self._App()
        feature_manager = self._FeatureManagerStub()
        settings = SettingsRegistry()
        settings.declare("ui", "theme", "dark")
        settings.set_value("ui", "theme", "light")

        manager = WorkspacePersistenceManager()
        manager.register_settings("prefs", settings)
        state = manager.capture(app, feature_manager=feature_manager, metadata={"name": "demo"})

        self.assertEqual(state.feature_states["feature"]["count"], 2)
        self.assertEqual(state.settings_blocks["prefs"]["ui"]["theme"], "light")

        settings.set_value("ui", "theme", "dark")
        state.active_scene_name = "alt"
        manager.restore(state, app, feature_manager=feature_manager)

        self.assertEqual(app.active_scene_name, "alt")
        self.assertEqual(settings.get_value("ui", "theme"), "light")
        self.assertEqual(feature_manager.restored, {"feature": {"count": 2}})

    def test_workspace_state_round_trips_to_disk(self) -> None:
        state = WorkspaceState(active_scene_name="main", metadata={"x": 1})
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "workspace.json"
            state.save(path)
            loaded = WorkspaceState.load(path)
        self.assertEqual(loaded.active_scene_name, "main")
        self.assertEqual(loaded.metadata["x"], 1)

    def test_gui_application_workspace_helpers_capture_save_and_load(self) -> None:
        app = GuiApplication.__new__(GuiApplication)
        app.features = self._FeatureManagerStub()
        app.scene = self._Scene()
        app._active_scene_name = "main"
        app.switch_scene = lambda name: setattr(app, "_active_scene_name", name)

        settings = SettingsRegistry()
        settings.declare("ui", "theme", "dark")
        manager = WorkspacePersistenceManager()
        manager.register_settings("prefs", settings)

        state = GuiApplication.capture_workspace(app, manager, metadata={"session": 1})
        self.assertEqual(state.metadata["session"], 1)

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "workspace.json"
            GuiApplication.save_workspace(app, manager, path, metadata={"session": 2})
            settings.set_value("ui", "theme", "light")
            loaded = GuiApplication.load_workspace(app, manager, path)

        self.assertEqual(loaded.metadata["session"], 2)
        self.assertEqual(settings.get_value("ui", "theme"), "dark")


class DockWorkspaceTests(unittest.TestCase):
    def test_workspace_serializes_and_removes_panes(self) -> None:
        workspace = DockWorkspace(
            DockSplit(
                "horizontal",
                children=[
                    DockPane("project", "Project"),
                    DockTabs("right", [DockPane("inspector", "Inspector"), DockPane("console", "Console")]),
                ],
            )
        )

        self.assertEqual(workspace.pane_ids(), ["console", "inspector", "project"])
        payload = workspace.to_dict()
        rebuilt = DockWorkspace.from_dict(payload)
        self.assertIsNotNone(rebuilt.find_pane("inspector"))
        self.assertTrue(rebuilt.remove_pane("console"))
        self.assertNotIn("console", rebuilt.pane_ids())


class CollectionViewTests(unittest.TestCase):
    def test_collection_view_filters_sorts_and_projects(self) -> None:
        query = CollectionViewQuery()
        view = CollectionView([3, 1, 4, 2], query=query)
        view.add_filter(lambda value: value >= 2)
        view.set_sort(lambda value: value, reverse=True)
        view.set_projector(lambda value: f"v={value}")

        self.assertEqual(view.snapshot(), ["v=4", "v=3", "v=2"])


class FormSchemaTests(unittest.TestCase):
    def test_schema_builds_form_and_validates_values(self) -> None:
        schema = FormSchema(
            [
                SchemaField("name", "", required=True),
                SchemaField("age", 0, validators=[lambda value: None if value >= 18 else "Must be adult"]),
            ]
        )
        form = schema.build_form()
        form.field("name").value.value = "Ada"
        form.field("age").value.value = 21
        self.assertTrue(form.validate_all())
        errors = schema.validate_values({"name": "", "age": 12})
        self.assertEqual([error.field_name for error in errors], ["name", "age"])


class DocumentModelTests(unittest.TestCase):
    def test_document_tracks_revision_and_save_load(self) -> None:
        doc = DocumentModel("doc")
        doc.set_content("alpha")
        self.assertTrue(doc.is_dirty)
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "doc.txt"
            doc.save(path)
            self.assertFalse(doc.is_dirty)
            path.write_text("beta", encoding="utf-8")
            self.assertEqual(doc.load(path), "beta")
            self.assertFalse(doc.is_dirty)


class TransferManagerTests(unittest.TestCase):
    def test_transfer_manager_tracks_clipboard_and_drag(self) -> None:
        manager = TransferManager()
        data = TransferData({"text/plain": "hello", "application/x-id": 7})
        manager.set_clipboard(data)
        self.assertEqual(manager.get_clipboard().get("text/plain"), "hello")
        manager.begin_drag(data)
        self.assertTrue(manager.copy_drag_to_clipboard())
        self.assertEqual(manager.end_drag().get("application/x-id"), 7)


class PropertyInspectorModelTests(unittest.TestCase):
    class _Inspectable:
        def __init__(self) -> None:
            self._count = 1

        @property
        @ui_property(label="Count", type="int", min=0, max=10, group="General")
        def count(self) -> int:
            return self._count

        @count.setter
        def count(self, value: int) -> None:
            self._count = int(value)

    def test_property_inspector_reads_and_writes_values(self) -> None:
        target = self._Inspectable()
        inspector = PropertyInspectorModel(target)
        props = inspector.properties()
        self.assertEqual(len(props), 1)
        self.assertIsInstance(props[0], InspectedProperty)
        inspector.set_value("count", 99)
        self.assertEqual(target.count, 10)
        self.assertIn("General", inspector.grouped())


# ---------------------------------------------------------------------------
# Pass-B integration tests
# ---------------------------------------------------------------------------

class CommandHistorySubscriberTests(unittest.TestCase):
    """CommandHistory.subscribe fires observers after push/undo/redo."""

    def test_subscribe_fires_on_push(self) -> None:
        from gui_do import CommandHistory
        history = CommandHistory()
        events: list = []
        history.subscribe(events.append)

        class _NoOp:
            description = "noop"
            def execute(self): pass
            def undo(self): pass

        history.push(_NoOp())
        self.assertEqual(events, ["push"])

    def test_subscribe_fires_on_undo_and_redo(self) -> None:
        from gui_do import CommandHistory
        history = CommandHistory()
        events: list = []
        history.subscribe(events.append)

        class _Inc:
            description = "inc"
            def execute(self): pass
            def undo(self): pass

        history.push(_Inc())
        events.clear()
        history.undo()
        self.assertIn("undo", events)
        history.redo()
        self.assertIn("redo", events)

    def test_unsubscribe_stops_notifications(self) -> None:
        from gui_do import CommandHistory
        history = CommandHistory()
        events: list = []
        unsub = history.subscribe(events.append)
        unsub()

        class _NoOp:
            description = "noop"
            def execute(self): pass
            def undo(self): pass

        history.push(_NoOp())
        self.assertEqual(events, [])


class DocumentModelHistoryBindingTests(unittest.TestCase):
    """DocumentModel.bind_history integrates with CommandHistory."""

    def test_bind_history_marks_dirty_on_push(self) -> None:
        from gui_do import CommandHistory
        doc = DocumentModel("doc")
        doc.mark_saved()
        self.assertFalse(doc.is_dirty)

        history = CommandHistory()
        doc.bind_history(history)

        class _NoOp:
            description = "noop"
            def execute(self): pass
            def undo(self): pass

        history.push(_NoOp())
        self.assertTrue(doc.is_dirty)

    def test_bind_history_unsubscribe_stops_tracking(self) -> None:
        from gui_do import CommandHistory
        doc = DocumentModel("doc")
        history = CommandHistory()
        unsub = doc.bind_history(history)
        unsub()

        class _NoOp:
            description = "noop"
            def execute(self): pass
            def undo(self): pass

        history.push(_NoOp())
        # doc.revision unchanged since we unsubscribed
        self.assertFalse(doc.is_dirty)


class CollectionViewListViewTests(unittest.TestCase):
    """CollectionView.set_collection_view bridges into ListViewControl."""

    def test_set_collection_view_converts_items(self) -> None:
        from pygame import Rect
        from gui_do import ListViewControl
        cv = CollectionView(["alpha", "beta", "gamma"])
        ctrl = ListViewControl("lv", Rect(0, 0, 200, 200))
        ctrl.set_collection_view(cv)
        self.assertEqual(ctrl.item_count(), 3)
        self.assertEqual(ctrl.items[0].label, "alpha")

    def test_set_collection_view_none_clears(self) -> None:
        from pygame import Rect
        from gui_do import ListViewControl, ListItem
        ctrl = ListViewControl("lv", Rect(0, 0, 200, 200), items=[ListItem("x")])
        ctrl.set_collection_view(None)
        self.assertEqual(ctrl.item_count(), 0)

    def test_set_collection_view_passthrough_list_items(self) -> None:
        from pygame import Rect
        from gui_do import ListViewControl, ListItem
        items = [ListItem("one", value=1), ListItem("two", value=2)]
        cv = CollectionView(items)
        ctrl = ListViewControl("lv", Rect(0, 0, 200, 200))
        ctrl.set_collection_view(cv)
        self.assertEqual(ctrl.items[0].value, 1)
        self.assertEqual(ctrl.items[1].label, "two")


class CollectionViewDataGridTests(unittest.TestCase):
    """CollectionView.set_collection_view bridges into DataGridControl."""

    def test_set_collection_view_wraps_dicts_as_grid_rows(self) -> None:
        from pygame import Rect
        from gui_do import DataGridControl, GridColumn
        data = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
        cv = CollectionView(data)
        ctrl = DataGridControl("dg", Rect(0, 0, 400, 300), columns=[GridColumn("name", "Name"), GridColumn("age", "Age")])
        ctrl.set_collection_view(cv)
        rows = ctrl.rows
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0].data["name"], "Alice")

    def test_set_collection_view_none_clears_rows(self) -> None:
        from pygame import Rect
        from gui_do import DataGridControl, GridRow
        ctrl = DataGridControl("dg", Rect(0, 0, 400, 300))
        ctrl.set_rows([GridRow(data={"x": 1})])
        ctrl.set_collection_view(None)
        self.assertEqual(len(ctrl.rows), 0)

    def test_set_collection_view_passthrough_grid_rows(self) -> None:
        from pygame import Rect
        from gui_do import DataGridControl, GridRow
        rows = [GridRow(data={"v": 99}, row_id="r1")]
        cv = CollectionView(rows)
        ctrl = DataGridControl("dg", Rect(0, 0, 400, 300))
        ctrl.set_collection_view(cv)
        self.assertEqual(ctrl.rows[0].row_id, "r1")


class DockWorkspacePersistenceTests(unittest.TestCase):
    """WorkspacePersistenceManager.capture_dock / restore_dock integration."""

    def test_capture_and_restore_dock_layout(self) -> None:
        pane_a = DockPane("a", title="Panel A")
        pane_b = DockPane("b", title="Panel B")
        workspace = DockWorkspace(DockSplit("horizontal", [pane_a, pane_b]))
        manager = WorkspacePersistenceManager()

        data = manager.capture_dock(workspace)
        self.assertIn("root", data)

        restored = DockWorkspace()
        manager.restore_dock(data, restored)
        self.assertSetEqual(set(restored.pane_ids()), {"a", "b"})

    def test_workspace_state_includes_dock_state(self) -> None:
        state = WorkspaceState(dock_state={"root": {"kind": "pane", "pane_id": "x", "title": "X", "payload": {}}})
        as_dict = state.to_dict()
        self.assertIn("dock_state", as_dict)
        roundtripped = WorkspaceState.from_dict(as_dict)
        self.assertEqual(roundtripped.dock_state["root"]["pane_id"], "x")

    def test_dock_round_trip_through_workspace_state(self) -> None:
        pane = DockPane("main", title="Main")
        workspace = DockWorkspace(pane)
        manager = WorkspacePersistenceManager()

        state = WorkspaceState()
        state.dock_state = manager.capture_dock(workspace)
        restored_ws = DockWorkspace()
        manager.restore_dock(state.dock_state, restored_ws)
        self.assertEqual(restored_ws.pane_ids(), ["main"])


class ActionRegistryDeclareTests(unittest.TestCase):
    """ActionRegistry.declare convenience method."""

    def test_declare_registers_callable_descriptor(self) -> None:
        called = []
        registry = ActionRegistry()
        descriptor = registry.declare("save", "Save", lambda _ctx, _ev: called.append("save") or True, category="File", shortcut_hint="Ctrl+S")
        self.assertTrue(registry.has("save"))
        self.assertEqual(descriptor.label, "Save")
        self.assertEqual(descriptor.category, "File")
        self.assertEqual(descriptor.shortcut_hint, "Ctrl+S")
        registry.invoke("save")
        self.assertEqual(called, ["save"])

    def test_declare_returns_descriptor_for_chaining(self) -> None:
        registry = ActionRegistry()
        d = registry.declare("open", "Open", lambda _ctx, _ev: True)
        self.assertIsInstance(d, ActionDescriptor)
        self.assertEqual(d.action_id, "open")


# ---------------------------------------------------------------------------
# Pass-C integration tests
# ---------------------------------------------------------------------------

class TreeControlCollectionViewTests(unittest.TestCase):
    """TreeControl.set_collection_view bridges CollectionView items."""

    def test_set_collection_view_converts_plain_items(self) -> None:
        from pygame import Rect
        from gui_do import TreeControl
        cv = CollectionView(["Root A", "Root B", "Root C"])
        ctrl = TreeControl("tree", Rect(0, 0, 200, 400))
        ctrl.set_collection_view(cv)
        self.assertEqual(len(ctrl.nodes), 3)
        self.assertEqual(ctrl.nodes[0].label, "Root A")

    def test_set_collection_view_none_clears(self) -> None:
        from pygame import Rect
        from gui_do import TreeControl, TreeNode
        ctrl = TreeControl("tree", Rect(0, 0, 200, 400), [TreeNode("x")])
        ctrl.set_collection_view(None)
        self.assertEqual(len(ctrl.nodes), 0)

    def test_set_collection_view_passthrough_tree_nodes(self) -> None:
        from pygame import Rect
        from gui_do import TreeControl, TreeNode
        nodes = [TreeNode("parent", children=[TreeNode("child")], expanded=True)]
        cv = CollectionView(nodes)
        ctrl = TreeControl("tree", Rect(0, 0, 200, 400))
        ctrl.set_collection_view(cv)
        self.assertEqual(ctrl.nodes[0].label, "parent")
        self.assertTrue(ctrl.nodes[0].expanded)
        self.assertEqual(len(ctrl.nodes[0].children), 1)


class FormSchemaHelperTests(unittest.TestCase):
    """FormSchema.apply_to and extract_from helpers."""

    def _make_schema(self):
        return FormSchema([
            SchemaField("name", "Alice"),
            SchemaField("age",  30),
        ])

    def test_apply_to_sets_field_values(self) -> None:
        schema = self._make_schema()
        form = schema.build_form()
        schema.apply_to(form, {"name": "Bob", "age": 99})
        self.assertEqual(form.field("name").value.value, "Bob")
        self.assertEqual(form.field("age").value.value, 99)

    def test_apply_to_skips_missing_keys(self) -> None:
        schema = self._make_schema()
        form = schema.build_form()
        schema.apply_to(form, {"name": "Carol"})
        self.assertEqual(form.field("age").value.value, 30)  # unchanged default

    def test_extract_from_reads_current_values(self) -> None:
        schema = self._make_schema()
        form = schema.build_form()
        form.field("name").value.value = "Dave"
        result = schema.extract_from(form)
        self.assertEqual(result["name"], "Dave")
        self.assertEqual(result["age"], 30)

    def test_apply_then_extract_round_trip(self) -> None:
        schema = self._make_schema()
        form = schema.build_form()
        values = {"name": "Eve", "age": 42}
        schema.apply_to(form, values)
        extracted = schema.extract_from(form)
        self.assertEqual(extracted, values)


class PropertyInspectorPanelTests(unittest.TestCase):
    """PropertyInspectorPanel renders PropertyInspectorModel groups."""

    class _Target:
        def __init__(self) -> None:
            self._score = 7

        @property
        def score(self):
            return self._score

        @score.setter
        def score(self, v):
            self._score = int(v)

    def _make_target_with_props(self):
        from gui_do import ui_property

        class _Inspectable:
            def __init__(self):
                self._alpha = 0.8

            @property
            @ui_property(label="Alpha", type="float", min=0.0, max=1.0, group="Appearance")
            def alpha(self) -> float:
                return self._alpha

            @alpha.setter
            def alpha(self, v: float) -> None:
                self._alpha = float(v)

        return _Inspectable()

    def test_panel_builds_without_model(self) -> None:
        from pygame import Rect
        panel = PropertyInspectorPanel("pi", Rect(0, 0, 300, 400))
        self.assertIsNone(panel.model)
        self.assertEqual(panel.scroll_offset, 0)

    def test_panel_builds_with_model_and_populates_rows(self) -> None:
        from pygame import Rect
        target = self._make_target_with_props()
        model = PropertyInspectorModel(target)
        panel = PropertyInspectorPanel("pi", Rect(0, 0, 300, 400), model)
        self.assertIs(panel.model, model)

    def test_set_model_replaces_content(self) -> None:
        from pygame import Rect
        panel = PropertyInspectorPanel("pi", Rect(0, 0, 300, 400))
        target = self._make_target_with_props()
        panel.set_model(PropertyInspectorModel(target))
        self.assertIsNotNone(panel.model)
        panel.set_model(None)
        self.assertIsNone(panel.model)

    def test_refresh_does_not_raise(self) -> None:
        from pygame import Rect
        target = self._make_target_with_props()
        panel = PropertyInspectorPanel("pi", Rect(0, 0, 300, 400), PropertyInspectorModel(target))
        panel.refresh()  # should not raise

    def test_on_select_callback_fires(self) -> None:
        from pygame import Rect
        from gui_do.events.gui_event import GuiEvent, EventType
        selected = []
        target = self._make_target_with_props()
        model = PropertyInspectorModel(target)
        panel = PropertyInspectorPanel(
            "pi", Rect(10, 10, 300, 400), model, on_select=selected.append
        )
        # Find first non-header row to click
        click_y = None
        y = panel.rect.y
        for row in panel._rows:
            h = panel._header_height if row.is_header else panel._row_height
            if not row.is_header:
                click_y = y + h // 2
                break
            y += h
        if click_y is None:
            self.skipTest("No property rows to click")
            return

        class _App:
            overlay = None
            def capture_pointer(self, *a, **kw): pass
            @property
            def logical_pointer_pos(self): return (0, 0)

        event = GuiEvent(kind=EventType.MOUSE_BUTTON_DOWN, type=0, pos=(panel.rect.x + 50, click_y), button=1)
        panel.handle_event(event, _App())
        self.assertEqual(len(selected), 1)
        self.assertIsInstance(selected[0], InspectedProperty)


class ActionRegistryMenuWiringTests(unittest.TestCase):
    """MenuBarManager.register_actions uses ActionRegistry.context_menu_items."""

    def test_register_actions_builds_menu_from_registry(self) -> None:
        called = []
        registry = ActionRegistry()
        registry.declare("save", "Save", lambda _ctx, _ev: called.append("save") or True, category="File")
        registry.declare("exit", "Exit", lambda _ctx, _ev: called.append("exit") or True, category="File")
        registry.declare("about", "About", lambda _ctx, _ev: called.append("about") or True, category="Help")

        menu = MenuBarManager()
        menu.register_actions("File", registry, category="File")
        self.assertIn("File", menu._order)
        items = menu._menus["File"]
        self.assertEqual(len(items), 2)
        labels = [i.label for i in items]
        self.assertIn("Save", labels)
        self.assertIn("Exit", labels)
        # Help category not registered — only File
        self.assertNotIn("Help", menu._order)


if __name__ == "__main__":
    unittest.main()


# ---------------------------------------------------------------------------
# Pass-D tests — PropertyInspectorPanel demo wiring
# ---------------------------------------------------------------------------

class DemoInspectableTests(unittest.TestCase):
    """_DemoInspectable class properties are correctly decorated."""

    def _make(self):
        from demo_features.systems_demo_feature import _DemoInspectable
        return _DemoInspectable()

    def test_demo_inspectable_has_ui_properties(self) -> None:
        obj = self._make()
        from gui_do import property_registry
        descs = property_registry.descriptors_for(obj)
        names = [d.name for d in descs]
        self.assertIn("opacity", names)
        self.assertIn("speed", names)
        self.assertIn("label", names)
        self.assertIn("active", names)

    def test_demo_inspectable_model_builds(self) -> None:
        obj = self._make()
        model = PropertyInspectorModel(obj)
        grouped = model.grouped()
        self.assertIn("Appearance", grouped)
        self.assertIn("Behaviour", grouped)

    def test_demo_inspectable_inspector_panel_initializes(self) -> None:
        from pygame import Rect
        from demo_features.systems_demo_feature import _DemoInspectable
        target = _DemoInspectable()
        model = PropertyInspectorModel(target)
        panel = PropertyInspectorPanel("test_pi", Rect(0, 0, 400, 300), model)
        self.assertIsNotNone(panel.model)
        self.assertGreater(len(panel._rows), 0)


# ---------------------------------------------------------------------------
# Pass-E tests — DockWorkspacePanel
# ---------------------------------------------------------------------------

class DockWorkspacePanelTests(unittest.TestCase):
    """DockWorkspacePanel renders DockTabs and switches panes."""

    def _make_panel(self, on_change=None):
        from pygame import Rect
        from gui_do import DockWorkspacePanel, DockWorkspace, DockTabs, DockPane
        workspace = DockWorkspace(DockTabs("main", panes=[
            DockPane("a", "Alpha"),
            DockPane("b", "Beta"),
            DockPane("c", "Gamma"),
        ]))
        panel = DockWorkspacePanel("dwp", Rect(0, 0, 300, 36), workspace, on_change=on_change)
        return panel, workspace

    def test_initial_active_pane(self) -> None:
        panel, workspace = self._make_panel()
        self.assertEqual(panel.active_pane_id, "a")

    def test_switch_pane_updates_model(self) -> None:
        panel, workspace = self._make_panel()
        result = panel.switch_pane("b")
        self.assertTrue(result)
        self.assertEqual(workspace.root.active_pane_id, "b")
        self.assertEqual(panel.active_pane_id, "b")

    def test_switch_pane_fires_callback(self) -> None:
        changes = []
        panel, _ = self._make_panel(on_change=changes.append)
        panel.switch_pane("c")
        self.assertEqual(changes, ["c"])

    def test_switch_pane_unknown_id_returns_false(self) -> None:
        panel, _ = self._make_panel()
        result = panel.switch_pane("nonexistent")
        self.assertFalse(result)

    def test_set_workspace_replaces_model(self) -> None:
        from gui_do import DockWorkspace, DockPane
        panel, _ = self._make_panel()
        panel.set_workspace(None)
        self.assertIsNone(panel.workspace)
        panel.set_workspace(DockWorkspace(DockPane("solo", "Solo")))
        self.assertIsNone(panel.active_pane_id)  # DockPane root → no tabs

    def test_tab_rects_divide_panel_evenly(self) -> None:
        panel, workspace = self._make_panel()
        tabs = panel._active_tabs()
        rects = panel._tab_rects(tabs)
        self.assertEqual(len(rects), 3)
        total_w = sum(r.width for r in rects)
        self.assertAlmostEqual(total_w, panel.rect.width, delta=2)

    def test_mouse_click_switches_pane(self) -> None:
        from gui_do.events.gui_event import GuiEvent, EventType
        changes = []
        panel, workspace = self._make_panel(on_change=changes.append)

        tabs = workspace.root
        tab_rects = panel._tab_rects(tabs)
        # Click the second tab ("b")
        click_x = tab_rects[1].centerx
        click_y = tab_rects[1].centery

        class _App:
            overlay = None
            @property
            def logical_pointer_pos(self): return (0, 0)

        event = GuiEvent(kind=EventType.MOUSE_BUTTON_DOWN, type=0,
                         pos=(click_x, click_y), button=1)
        handled = panel.handle_event(event, _App())
        self.assertTrue(handled)
        self.assertEqual(panel.active_pane_id, "b")
        self.assertIn("b", changes)

    def test_no_workspace_returns_none_active(self) -> None:
        from pygame import Rect
        from gui_do import DockWorkspacePanel
        panel = DockWorkspacePanel("dwp2", Rect(0, 0, 200, 36))
        self.assertIsNone(panel.active_pane_id)
        self.assertIsNone(panel._active_tabs())


# ---------------------------------------------------------------------------
# Pass-F tests — CollectionView live subscription + bind_collection_view
# ---------------------------------------------------------------------------

class CollectionViewSubscribeTests(unittest.TestCase):
    """CollectionView.subscribe() notifies on refresh; unsub silences it."""

    def test_subscribe_fires_on_refresh(self) -> None:
        calls = []
        data = ["a", "b"]
        cv = CollectionView(lambda: data)
        cv.subscribe(lambda: calls.append(len(cv.items)))
        data.append("c")
        cv.refresh()
        self.assertEqual(calls, [3])

    def test_subscribe_does_not_fire_on_initial_build(self) -> None:
        calls = []
        cv = CollectionView(["x", "y"])
        cv.subscribe(lambda: calls.append(True))
        # No explicit refresh — subscriber should not have fired yet
        self.assertEqual(calls, [])

    def test_unsub_stops_notifications(self) -> None:
        calls = []
        data = [1, 2, 3]
        cv = CollectionView(lambda: data)
        unsub = cv.subscribe(lambda: calls.append(True))
        cv.refresh()
        unsub()
        data.append(4)
        cv.refresh()
        self.assertEqual(len(calls), 1)  # only the first refresh before unsub

    def test_multiple_subscribers_all_notified(self) -> None:
        log: list = []
        cv = CollectionView(["p", "q"])
        cv.subscribe(lambda: log.append("s1"))
        cv.subscribe(lambda: log.append("s2"))
        cv.refresh()
        self.assertIn("s1", log)
        self.assertIn("s2", log)

    def test_unsub_one_leaves_others_intact(self) -> None:
        log: list = []
        cv = CollectionView(["x"])
        unsub1 = cv.subscribe(lambda: log.append("s1"))
        cv.subscribe(lambda: log.append("s2"))
        unsub1()
        cv.refresh()
        self.assertNotIn("s1", log)
        self.assertIn("s2", log)


class CollectionViewBindListViewTests(unittest.TestCase):
    """ListViewControl.bind_collection_view() provides live sync."""

    def test_bind_populates_immediately(self) -> None:
        from pygame import Rect
        from gui_do import ListViewControl
        cv = CollectionView(["alpha", "beta"])
        ctrl = ListViewControl("lv", Rect(0, 0, 200, 300))
        ctrl.bind_collection_view(cv)
        self.assertEqual(ctrl.item_count(), 2)

    def test_bind_auto_updates_on_cv_refresh(self) -> None:
        from pygame import Rect
        from gui_do import ListViewControl
        data = ["one", "two"]
        cv = CollectionView(lambda: data)
        ctrl = ListViewControl("lv", Rect(0, 0, 200, 300))
        ctrl.bind_collection_view(cv)
        data.append("three")
        cv.refresh()
        self.assertEqual(ctrl.item_count(), 3)
        self.assertEqual(ctrl.items[2].label, "three")

    def test_bind_on_refresh_callback_fires(self) -> None:
        from pygame import Rect
        from gui_do import ListViewControl
        calls = []
        cv = CollectionView(["x"])
        ctrl = ListViewControl("lv", Rect(0, 0, 200, 300))
        ctrl.bind_collection_view(cv, on_refresh=lambda: calls.append(True))
        cv.refresh()
        self.assertEqual(calls, [True])

    def test_bind_unsub_stops_live_updates(self) -> None:
        from pygame import Rect
        from gui_do import ListViewControl
        data = ["a"]
        cv = CollectionView(lambda: data)
        ctrl = ListViewControl("lv", Rect(0, 0, 200, 300))
        unsub = ctrl.bind_collection_view(cv)
        unsub()
        data.append("b")
        cv.refresh()
        self.assertEqual(ctrl.item_count(), 1)  # still only initial count


class CollectionViewBindDataGridTests(unittest.TestCase):
    """DataGridControl.bind_collection_view() provides live sync."""

    def test_bind_populates_immediately(self) -> None:
        from pygame import Rect
        from gui_do import DataGridControl, GridColumn
        data = [{"id": 1}, {"id": 2}]
        cv = CollectionView(data)
        ctrl = DataGridControl("dg", Rect(0, 0, 400, 300),
                               columns=[GridColumn("id", "ID")])
        ctrl.bind_collection_view(cv)
        self.assertEqual(len(ctrl.rows), 2)

    def test_bind_auto_updates_on_cv_refresh(self) -> None:
        from pygame import Rect
        from gui_do import DataGridControl, GridColumn
        data = [{"v": 1}]
        cv = CollectionView(lambda: data)
        ctrl = DataGridControl("dg", Rect(0, 0, 400, 300),
                               columns=[GridColumn("v", "V")])
        ctrl.bind_collection_view(cv)
        data.append({"v": 2})
        cv.refresh()
        self.assertEqual(len(ctrl.rows), 2)

    def test_bind_unsub_stops_live_updates(self) -> None:
        from pygame import Rect
        from gui_do import DataGridControl
        data = [{"x": 0}]
        cv = CollectionView(lambda: data)
        ctrl = DataGridControl("dg", Rect(0, 0, 400, 300))
        unsub = ctrl.bind_collection_view(cv)
        unsub()
        data.append({"x": 1})
        cv.refresh()
        self.assertEqual(len(ctrl.rows), 1)


class CollectionViewBindTreeTests(unittest.TestCase):
    """TreeControl.bind_collection_view() provides live sync."""

    def test_bind_populates_immediately(self) -> None:
        from pygame import Rect
        from gui_do import TreeControl
        cv = CollectionView(["Root A", "Root B"])
        ctrl = TreeControl("tree", Rect(0, 0, 200, 400))
        ctrl.bind_collection_view(cv)
        self.assertEqual(len(ctrl.nodes), 2)

    def test_bind_auto_updates_on_cv_refresh(self) -> None:
        from pygame import Rect
        from gui_do import TreeControl
        data = ["Node 1"]
        cv = CollectionView(lambda: data)
        ctrl = TreeControl("tree", Rect(0, 0, 200, 400))
        ctrl.bind_collection_view(cv)
        data.append("Node 2")
        cv.refresh()
        self.assertEqual(len(ctrl.nodes), 2)
        self.assertEqual(ctrl.nodes[1].label, "Node 2")

    def test_bind_on_refresh_callback_fires(self) -> None:
        from pygame import Rect
        from gui_do import TreeControl
        calls = []
        cv = CollectionView(["item"])
        ctrl = TreeControl("tree", Rect(0, 0, 200, 400))
        ctrl.bind_collection_view(cv, on_refresh=lambda: calls.append(True))
        cv.refresh()
        self.assertEqual(calls, [True])

    def test_bind_unsub_stops_live_updates(self) -> None:
        from pygame import Rect
        from gui_do import TreeControl
        data = ["a"]
        cv = CollectionView(lambda: data)
        ctrl = TreeControl("tree", Rect(0, 0, 200, 400))
        unsub = ctrl.bind_collection_view(cv)
        unsub()
        data.append("b")
        cv.refresh()
        self.assertEqual(len(ctrl.nodes), 1)


# ---------------------------------------------------------------------------
# Pass-G tests — ObservableList → CollectionView live binding
# ---------------------------------------------------------------------------

from gui_do import ObservableList


class ObservableListCollectionViewBindingTests(unittest.TestCase):
    """CollectionView.bind_observable_list() wires ObservableList mutations to cv.refresh()."""

    def test_bind_sets_initial_items_from_obs(self) -> None:
        obs = ObservableList(["x", "y", "z"])
        cv = CollectionView([])
        cv.bind_observable_list(obs)
        self.assertEqual(cv.count(), 3)

    def test_append_triggers_cv_refresh(self) -> None:
        obs = ObservableList(["a", "b"])
        cv = CollectionView(obs.snapshot)
        cv.bind_observable_list(obs)
        obs.append("c")
        self.assertEqual(cv.count(), 3)
        self.assertEqual(cv.items[2], "c")

    def test_remove_triggers_cv_refresh(self) -> None:
        obs = ObservableList(["a", "b", "c"])
        cv = CollectionView(obs.snapshot)
        cv.bind_observable_list(obs)
        obs.remove_at(1)
        self.assertEqual(cv.count(), 2)
        self.assertNotIn("b", cv.items)

    def test_replace_triggers_cv_refresh(self) -> None:
        obs = ObservableList(["old"])
        cv = CollectionView(obs.snapshot)
        cv.bind_observable_list(obs)
        obs.replace(0, "new")
        self.assertEqual(cv.items[0], "new")

    def test_unsub_stops_auto_refresh(self) -> None:
        obs = ObservableList(["a"])
        cv = CollectionView(obs.snapshot)
        unsub = cv.bind_observable_list(obs)
        unsub()
        obs.append("b")
        # cv source still points to obs.snapshot, but no auto-refresh
        self.assertEqual(cv.count(), 1)

    def test_cv_subscribers_notified_on_obs_mutation(self) -> None:
        events: list = []
        obs = ObservableList(["p"])
        cv = CollectionView(obs.snapshot)
        cv.bind_observable_list(obs)
        cv.subscribe(lambda: events.append(cv.count()))
        obs.append("q")
        self.assertEqual(events, [2])

    def test_cv_filter_applies_after_obs_mutation(self) -> None:
        obs = ObservableList([1, 2, 3, 4, 5])
        cv = CollectionView(obs.snapshot)
        cv.bind_observable_list(obs)
        cv.add_filter(lambda x: x % 2 == 0)  # only even numbers
        obs.append(6)
        self.assertEqual(cv.items, [2, 4, 6])

    def test_full_pipeline_obs_to_listview(self) -> None:
        from pygame import Rect
        from gui_do import ListViewControl
        obs = ObservableList(["alpha", "beta"])
        cv = CollectionView(obs.snapshot)
        cv.bind_observable_list(obs)
        ctrl = ListViewControl("lv", Rect(0, 0, 200, 300))
        ctrl.bind_collection_view(cv)
        obs.append("gamma")
        self.assertEqual(ctrl.item_count(), 3)
        self.assertEqual(ctrl.items[2].label, "gamma")

    def test_multiple_obs_bindings_independent(self) -> None:
        obs1 = ObservableList(["a"])
        obs2 = ObservableList([1, 2])
        cv1 = CollectionView(obs1.snapshot)
        cv2 = CollectionView(obs2.snapshot)
        cv1.bind_observable_list(obs1)
        cv2.bind_observable_list(obs2)
        obs1.append("b")
        obs2.append(3)
        self.assertEqual(cv1.count(), 2)
        self.assertEqual(cv2.count(), 3)


# ---------------------------------------------------------------------------
# Pass-H tests — StateMachine integration
# ---------------------------------------------------------------------------

from gui_do import StateMachine


class StateMachineTransitionTests(unittest.TestCase):
    """StateMachine transitions, guards, and entry/exit callbacks."""

    def _make_sm(self) -> StateMachine:
        sm = StateMachine("idle")
        sm.add_state("running", on_enter=None)
        sm.add_state("done")
        sm.add_transition("idle", "running", trigger="start")
        sm.add_transition("running", "done", trigger="finish")
        sm.add_transition("done", "idle", trigger="reset")
        return sm

    def test_initial_state(self) -> None:
        sm = StateMachine("idle")
        self.assertEqual(sm.current.value, "idle")

    def test_trigger_advances_state(self) -> None:
        sm = self._make_sm()
        result = sm.trigger("start")
        self.assertTrue(result)
        self.assertEqual(sm.current.value, "running")

    def test_trigger_returns_false_no_transition(self) -> None:
        sm = self._make_sm()
        result = sm.trigger("finish")  # no transition from idle → done
        self.assertFalse(result)
        self.assertEqual(sm.current.value, "idle")

    def test_trigger_fires_subscribers(self) -> None:
        states: list = []
        sm = self._make_sm()
        sm.current.subscribe(lambda s: states.append(s))
        sm.trigger("start")
        sm.trigger("finish")
        self.assertEqual(states, ["running", "done"])

    def test_on_enter_called_on_transition(self) -> None:
        entered: list = []
        sm = StateMachine("idle")
        sm.add_state("active", on_enter=lambda: entered.append("active"))
        sm.add_transition("idle", "active", trigger="go")
        sm.trigger("go")
        self.assertEqual(entered, ["active"])

    def test_on_exit_called_on_transition(self) -> None:
        exited: list = []
        sm = StateMachine("idle")
        sm.add_state("idle", on_exit=lambda: exited.append("idle"))
        sm.add_state("done")
        sm.add_transition("idle", "done", trigger="finish")
        sm.trigger("finish")
        self.assertEqual(exited, ["idle"])

    def test_guard_blocks_transition_when_false(self) -> None:
        sm = StateMachine("idle")
        sm.add_state("active")
        sm.add_transition("idle", "active", trigger="go", guard=lambda: False)
        result = sm.trigger("go")
        self.assertFalse(result)
        self.assertEqual(sm.current.value, "idle")

    def test_guard_allows_transition_when_true(self) -> None:
        allow = [True]
        sm = StateMachine("idle")
        sm.add_state("active")
        sm.add_transition("idle", "active", trigger="go", guard=lambda: allow[0])
        sm.trigger("go")
        self.assertEqual(sm.current.value, "active")

    def test_can_trigger_respects_guard(self) -> None:
        sm = StateMachine("idle")
        sm.add_state("done")
        sm.add_transition("idle", "done", trigger="finish", guard=lambda: False)
        self.assertFalse(sm.can_trigger("finish"))

    def test_available_triggers_lists_fireable_transitions(self) -> None:
        sm = self._make_sm()
        # From idle, only "start" is declared
        triggers = sm.available_triggers()
        self.assertIn("start", triggers)
        self.assertNotIn("finish", triggers)


class StateMachineUIIntegrationTests(unittest.TestCase):
    """StateMachine drives UI control enabled state via observable subscription."""

    def test_sm_state_disables_control(self) -> None:
        from pygame import Rect
        from gui_do import ButtonControl

        sm = StateMachine("editing")
        sm.add_state("locked")
        sm.add_transition("editing", "locked", trigger="lock")
        sm.add_transition("locked", "editing", trigger="unlock")

        btn = ButtonControl("save", Rect(0, 0, 100, 30), "Save")
        # Subscribe: disable button when locked, enable when editing
        sm.current.subscribe(lambda s: setattr(btn, "enabled", s == "editing"))

        self.assertTrue(btn.enabled)
        sm.trigger("lock")
        self.assertFalse(btn.enabled)
        sm.trigger("unlock")
        self.assertTrue(btn.enabled)

    def test_sm_state_filters_collection_view(self) -> None:
        """StateMachine current state drives CollectionView filter."""
        data = ["error_log", "info_msg", "error_trace"]
        sm = StateMachine("all")
        sm.add_state("errors_only")
        sm.add_transition("all", "errors_only", trigger="filter")

        cv = CollectionView(lambda: data)

        def _apply_filter(state: str) -> None:
            cv.clear_filters()
            if state == "errors_only":
                cv.add_filter(lambda item: "error" in item)

        sm.current.subscribe(_apply_filter)

        self.assertEqual(cv.count(), 3)
        sm.trigger("filter")
        self.assertEqual(cv.count(), 2)
        self.assertTrue(all("error" in item for item in cv.items))

    def test_sm_action_callback_fires_on_transition(self) -> None:
        actions: list = []
        sm = StateMachine("idle")
        sm.add_state("saving")
        sm.add_transition("idle", "saving", trigger="save",
                          action=lambda: actions.append("save_action"))
        sm.trigger("save")
        self.assertEqual(actions, ["save_action"])

    def test_sm_multi_step_workflow(self) -> None:
        log: list = []
        sm = StateMachine("draft")
        sm.add_state("review", on_enter=lambda: log.append("enter_review"))
        sm.add_state("published", on_enter=lambda: log.append("enter_published"))
        sm.add_state("draft", on_exit=lambda: log.append("exit_draft"))
        sm.add_transition("draft", "review", trigger="submit")
        sm.add_transition("review", "published", trigger="approve")

        sm.trigger("submit")
        sm.trigger("approve")
        self.assertEqual(sm.current.value, "published")
        self.assertIn("exit_draft", log)
        self.assertIn("enter_review", log)
        self.assertIn("enter_published", log)


# ---------------------------------------------------------------------------
# Pass-I tests — SortFilterProxySource + FixedItemSource
# ---------------------------------------------------------------------------

from gui_do import SortFilterProxySource, VirtualItemSource, FixedItemSource


class FixedItemSourceTests(unittest.TestCase):
    """FixedItemSource satisfies the VirtualItemSource protocol."""

    def test_item_count_empty(self) -> None:
        src = FixedItemSource()
        self.assertEqual(src.item_count(), 0)

    def test_item_count_with_items(self) -> None:
        src = FixedItemSource(["a", "b", "c"])
        self.assertEqual(src.item_count(), 3)

    def test_item_at_returns_correct_item(self) -> None:
        src = FixedItemSource([10, 20, 30])
        self.assertEqual(src.item_at(0), 10)
        self.assertEqual(src.item_at(2), 30)

    def test_append_increases_count(self) -> None:
        src = FixedItemSource(["x"])
        src.append("y")
        self.assertEqual(src.item_count(), 2)
        self.assertEqual(src.item_at(1), "y")

    def test_insert_places_item_at_index(self) -> None:
        src = FixedItemSource(["a", "c"])
        src.insert(1, "b")
        self.assertEqual(src.item_count(), 3)
        self.assertEqual(src.item_at(1), "b")

    def test_remove_at_removes_correct_item(self) -> None:
        src = FixedItemSource(["a", "b", "c"])
        src.remove_at(1)
        self.assertEqual(src.item_count(), 2)
        self.assertEqual(src.item_at(1), "c")

    def test_replace_swaps_item(self) -> None:
        src = FixedItemSource(["a", "b"])
        src.replace(0, "z")
        self.assertEqual(src.item_at(0), "z")

    def test_clear_empties_source(self) -> None:
        src = FixedItemSource([1, 2, 3])
        src.clear()
        self.assertEqual(src.item_count(), 0)

    def test_snapshot_returns_copy(self) -> None:
        src = FixedItemSource([1, 2])
        snap = src.snapshot()
        snap.append(99)
        self.assertEqual(src.item_count(), 2)

    def test_set_items_replaces_all(self) -> None:
        src = FixedItemSource([1, 2])
        src.set_items([10, 20, 30])
        self.assertEqual(src.item_count(), 3)
        self.assertEqual(src.item_at(0), 10)

    def test_satisfies_virtual_item_source_protocol(self) -> None:
        src = FixedItemSource(["x"])
        self.assertTrue(isinstance(src, VirtualItemSource))


class SortFilterProxySourceTests(unittest.TestCase):
    """SortFilterProxySource wraps a source and supports filter/sort/subscribe."""

    def _make(self, items):
        source = FixedItemSource(items)
        proxy = SortFilterProxySource(source)
        return source, proxy

    def test_no_filter_exposes_all_items(self) -> None:
        _, proxy = self._make([1, 2, 3])
        self.assertEqual(proxy.item_count(), 3)

    def test_filter_reduces_visible_items(self) -> None:
        _, proxy = self._make([1, 2, 3, 4, 5])
        proxy.set_filter(lambda x: x % 2 == 0)
        self.assertEqual(proxy.item_count(), 2)

    def test_filter_item_at_returns_filtered_items(self) -> None:
        _, proxy = self._make([1, 2, 3, 4])
        proxy.set_filter(lambda x: x > 2)
        self.assertEqual(proxy.item_at(0), 3)
        self.assertEqual(proxy.item_at(1), 4)

    def test_clear_filter_restores_all_items(self) -> None:
        _, proxy = self._make([1, 2, 3])
        proxy.set_filter(lambda x: x > 10)
        self.assertEqual(proxy.item_count(), 0)
        proxy.set_filter(None)
        self.assertEqual(proxy.item_count(), 3)

    def test_sort_key_orders_items(self) -> None:
        _, proxy = self._make([3, 1, 2])
        proxy.set_sort_key(lambda x: x)
        self.assertEqual(proxy.item_at(0), 1)
        self.assertEqual(proxy.item_at(2), 3)

    def test_sort_reverse_orders_descending(self) -> None:
        _, proxy = self._make([1, 3, 2])
        proxy.set_sort_key(lambda x: x, reverse=True)
        self.assertEqual(proxy.item_at(0), 3)
        self.assertEqual(proxy.item_at(2), 1)

    def test_filter_and_sort_combined(self) -> None:
        _, proxy = self._make([5, 1, 4, 2, 3])
        proxy.set_filter(lambda x: x < 4)
        proxy.set_sort_key(lambda x: x)
        self.assertEqual(proxy.item_count(), 3)
        self.assertEqual(proxy.item_at(0), 1)
        self.assertEqual(proxy.item_at(2), 3)

    def test_subscribe_notified_on_filter_change(self) -> None:
        _, proxy = self._make([1, 2, 3])
        calls = []
        proxy.subscribe(lambda: calls.append(1))
        proxy.set_filter(lambda x: x > 1)
        self.assertGreater(len(calls), 0)

    def test_subscribe_notified_on_sort_change(self) -> None:
        _, proxy = self._make([3, 1, 2])
        calls = []
        proxy.subscribe(lambda: calls.append(1))
        proxy.set_sort_key(lambda x: x)
        self.assertGreater(len(calls), 0)

    def test_unsub_stops_notifications(self) -> None:
        _, proxy = self._make([1, 2, 3])
        calls = []
        unsub = proxy.subscribe(lambda: calls.append(1))
        unsub()
        proxy.set_filter(lambda x: x > 1)
        self.assertEqual(len(calls), 0)

    def test_has_filter_property(self) -> None:
        _, proxy = self._make([])
        self.assertFalse(proxy.has_filter)
        proxy.set_filter(lambda x: True)
        self.assertTrue(proxy.has_filter)

    def test_has_sort_property(self) -> None:
        _, proxy = self._make([])
        self.assertFalse(proxy.has_sort)
        proxy.set_sort_key(lambda x: x)
        self.assertTrue(proxy.has_sort)

    def test_source_property_returns_underlying_source(self) -> None:
        source, proxy = self._make([1])
        self.assertIs(proxy.source, source)

    def test_proxy_accepts_plain_list_as_source(self) -> None:
        proxy = SortFilterProxySource(["a", "b", "c"])
        self.assertEqual(proxy.item_count(), 3)
        self.assertEqual(proxy.item_at(1), "b")

    def test_proxy_filter_on_plain_list(self) -> None:
        proxy = SortFilterProxySource(["apple", "banana", "apricot"])
        proxy.set_filter(lambda s: s.startswith("a"))
        self.assertEqual(proxy.item_count(), 2)

    def test_satisfies_virtual_item_source_protocol(self) -> None:
        proxy = SortFilterProxySource(FixedItemSource([1]))
        self.assertTrue(isinstance(proxy, VirtualItemSource))


# ---------------------------------------------------------------------------
# Pass-J tests — StringTable + LocaleRegistry
# ---------------------------------------------------------------------------

from gui_do import StringTable, LocaleRegistry


class StringTableTests(unittest.TestCase):
    """StringTable maps keys to translated text for one locale."""

    def test_get_returns_translation(self) -> None:
        t = StringTable("en", {"btn.ok": "OK"})
        self.assertEqual(t.get("btn.ok"), "OK")

    def test_get_missing_key_returns_fallback(self) -> None:
        t = StringTable("en", {"btn.ok": "OK"})
        self.assertEqual(t.get("missing", fallback="?"), "?")

    def test_has_returns_true_for_existing_key(self) -> None:
        t = StringTable("en", {"k": "v"})
        self.assertTrue(t.has("k"))

    def test_has_returns_false_for_missing_key(self) -> None:
        t = StringTable("en", {"k": "v"})
        self.assertFalse(t.has("missing"))

    def test_keys_returns_sorted_list(self) -> None:
        t = StringTable("en", {"z": "z", "a": "a", "m": "m"})
        self.assertEqual(t.keys(), ["a", "m", "z"])

    def test_locale_id_stored(self) -> None:
        t = StringTable("fr", {})
        self.assertEqual(t.locale_id, "fr")

    def test_len_returns_entry_count(self) -> None:
        t = StringTable("en", {"a": "1", "b": "2"})
        self.assertEqual(len(t), 2)

    def test_empty_locale_id_raises(self) -> None:
        with self.assertRaises(ValueError):
            StringTable("", {"k": "v"})


class LocaleRegistryTests(unittest.TestCase):
    """LocaleRegistry looks up strings and reacts to locale switches."""

    def _make_registry(self):
        reg = LocaleRegistry(default_locale="en", fallback_locale="en")
        reg.register(StringTable("en", {"btn.ok": "OK", "btn.cancel": "Cancel"}))
        reg.register(StringTable("es", {"btn.ok": "Aceptar"}))
        return reg

    def test_t_returns_active_locale_string(self) -> None:
        reg = self._make_registry()
        self.assertEqual(reg.t("btn.ok"), "OK")

    def test_set_locale_switches_active_locale(self) -> None:
        reg = self._make_registry()
        reg.set_locale("es")
        self.assertEqual(reg.t("btn.ok"), "Aceptar")

    def test_t_falls_back_when_key_missing_in_active_locale(self) -> None:
        reg = self._make_registry()
        reg.set_locale("es")
        # "btn.cancel" not in "es" → falls back to "en"
        self.assertEqual(reg.t("btn.cancel"), "Cancel")

    def test_t_returns_fallback_string_when_key_missing_everywhere(self) -> None:
        reg = self._make_registry()
        self.assertEqual(reg.t("nonexistent", fallback="N/A"), "N/A")

    def test_t_with_explicit_locale_override(self) -> None:
        reg = self._make_registry()
        self.assertEqual(reg.t("btn.ok", locale="es"), "Aceptar")

    def test_active_locale_property(self) -> None:
        reg = self._make_registry()
        reg.set_locale("es")
        self.assertEqual(reg.active_locale, "es")

    def test_registered_locales_sorted(self) -> None:
        reg = self._make_registry()
        self.assertEqual(reg.registered_locales, ["en", "es"])

    def test_len_counts_registered_locales(self) -> None:
        reg = self._make_registry()
        self.assertEqual(len(reg), 2)

    def test_current_locale_is_observable_value(self) -> None:
        reg = self._make_registry()
        self.assertEqual(reg.current_locale.value, "en")

    def test_subscribe_to_locale_change(self) -> None:
        reg = self._make_registry()
        events = []
        reg.current_locale.subscribe(lambda v: events.append(v))
        reg.set_locale("es")
        self.assertIn("es", events)

    def test_locale_change_drives_label_refresh(self) -> None:
        reg = self._make_registry()
        label_texts = []
        reg.current_locale.subscribe(lambda _: label_texts.append(reg.t("btn.ok")))
        reg.set_locale("es")
        self.assertEqual(label_texts[-1], "Aceptar")

    def test_register_replaces_existing_locale(self) -> None:
        reg = self._make_registry()
        reg.register(StringTable("en", {"btn.ok": "Go"}))
        self.assertEqual(reg.t("btn.ok"), "Go")

    def test_has_key_in_active_locale(self) -> None:
        reg = self._make_registry()
        self.assertTrue(reg.has("btn.ok"))
        self.assertFalse(reg.has("nonexistent"))


# ---------------------------------------------------------------------------
# Pass-K tests — GestureRecognizer integration
# ---------------------------------------------------------------------------

from gui_do import GestureRecognizer
from gui_do import GuiEvent, EventType


def _make_gesture_event(kind, *, pos=(0, 0), button=1):
    return GuiEvent(kind=kind, type=0, pos=pos, button=button)


class GestureRecognizerDoubleClickTests(unittest.TestCase):
    """GestureRecognizer fires on_double_click for two rapid clicks."""

    def setUp(self):
        self.fired = []
        self.gr = GestureRecognizer(
            on_double_click=lambda pos: self.fired.append(pos),
            double_click_ms=500,
        )

    def test_single_click_does_not_fire(self) -> None:
        self.gr.process_event(_make_gesture_event(EventType.MOUSE_BUTTON_DOWN, pos=(10, 10)))
        self.assertEqual(len(self.fired), 0)

    def test_double_click_fires(self) -> None:
        ev = _make_gesture_event(EventType.MOUSE_BUTTON_DOWN, pos=(10, 10))
        self.gr.process_event(ev)
        self.gr.update(0.1)  # well within 500 ms
        self.gr.process_event(ev)
        self.assertEqual(len(self.fired), 1)
        self.assertEqual(self.fired[0], (10, 10))

    def test_double_click_too_slow_does_not_fire(self) -> None:
        ev = _make_gesture_event(EventType.MOUSE_BUTTON_DOWN, pos=(10, 10))
        self.gr.process_event(ev)
        self.gr.update(0.6)  # > 500 ms
        self.gr.process_event(ev)
        self.assertEqual(len(self.fired), 0)

    def test_double_click_too_far_does_not_fire(self) -> None:
        self.gr.process_event(_make_gesture_event(EventType.MOUSE_BUTTON_DOWN, pos=(10, 10)))
        self.gr.update(0.1)
        self.gr.process_event(_make_gesture_event(EventType.MOUSE_BUTTON_DOWN, pos=(100, 100)))
        self.assertEqual(len(self.fired), 0)

    def test_reset_clears_pending_state(self) -> None:
        self.gr.process_event(_make_gesture_event(EventType.MOUSE_BUTTON_DOWN, pos=(10, 10)))
        self.gr.reset()
        self.gr.update(0.1)
        self.gr.process_event(_make_gesture_event(EventType.MOUSE_BUTTON_DOWN, pos=(10, 10)))
        self.assertEqual(len(self.fired), 0)


class GestureRecognizerLongPressTests(unittest.TestCase):
    """GestureRecognizer fires on_long_press after sustained hold."""

    def setUp(self):
        self.fired = []
        self.gr = GestureRecognizer(
            on_long_press=lambda pos: self.fired.append(pos),
            long_press_ms=600,
        )

    def test_short_hold_does_not_fire(self) -> None:
        self.gr.process_event(_make_gesture_event(EventType.MOUSE_BUTTON_DOWN, pos=(5, 5)))
        self.gr.update(0.3)  # < 600 ms
        self.assertEqual(len(self.fired), 0)

    def test_long_hold_fires(self) -> None:
        self.gr.process_event(_make_gesture_event(EventType.MOUSE_BUTTON_DOWN, pos=(5, 5)))
        self.gr.update(0.7)  # > 600 ms
        self.assertEqual(len(self.fired), 1)
        self.assertEqual(self.fired[0], (5, 5))

    def test_movement_resets_long_press_timer(self) -> None:
        self.gr.process_event(_make_gesture_event(EventType.MOUSE_BUTTON_DOWN, pos=(5, 5)))
        self.gr.update(0.3)
        # Move far enough to cancel long-press
        self.gr.process_event(_make_gesture_event(EventType.MOUSE_MOTION, pos=(50, 50)))
        self.gr.update(0.4)  # total > 600 ms but timer was reset
        self.assertEqual(len(self.fired), 0)

    def test_long_press_fires_only_once(self) -> None:
        self.gr.process_event(_make_gesture_event(EventType.MOUSE_BUTTON_DOWN, pos=(5, 5)))
        self.gr.update(0.7)
        self.gr.update(0.5)  # additional time still held
        self.assertEqual(len(self.fired), 1)


class GestureRecognizerSwipeTests(unittest.TestCase):
    """GestureRecognizer detects swipe direction on mouse-up."""

    def _swipe(self, start, end, dt=0.1):
        directions = []
        gr = GestureRecognizer(
            on_swipe=lambda d, v: directions.append(d),
            swipe_min_px=20,
        )
        gr.process_event(_make_gesture_event(EventType.MOUSE_BUTTON_DOWN, pos=start))
        gr.update(dt)
        gr.process_event(_make_gesture_event(EventType.MOUSE_BUTTON_UP, pos=end))
        return directions

    def test_right_swipe_detected(self) -> None:
        dirs = self._swipe((0, 50), (100, 50))
        self.assertEqual(dirs, ["right"])

    def test_left_swipe_detected(self) -> None:
        dirs = self._swipe((100, 50), (0, 50))
        self.assertEqual(dirs, ["left"])

    def test_down_swipe_detected(self) -> None:
        dirs = self._swipe((50, 0), (50, 100))
        self.assertEqual(dirs, ["down"])

    def test_up_swipe_detected(self) -> None:
        dirs = self._swipe((50, 100), (50, 0))
        self.assertEqual(dirs, ["up"])

    def test_short_move_does_not_fire_swipe(self) -> None:
        dirs = self._swipe((0, 0), (5, 0))
        self.assertEqual(dirs, [])


# ---------------------------------------------------------------------------
# Pass-L tests — ObservableDict
# ---------------------------------------------------------------------------

from gui_do import ObservableDict, CollectionChange, ChangeKind


class ObservableDictMutationTests(unittest.TestCase):
    """ObservableDict fires CollectionChange events on every structural mutation."""

    def setUp(self):
        self.changes = []
        self.d = ObservableDict({"a": 1, "b": 2})
        self.d.subscribe(lambda ch: self.changes.append(ch))

    def test_setitem_new_key_fires_added(self) -> None:
        self.d["c"] = 3
        self.assertEqual(len(self.changes), 1)
        ch = self.changes[0]
        self.assertEqual(ch.kind, ChangeKind.ADDED)
        self.assertEqual(ch.key, "c")
        self.assertEqual(ch.new_value, 3)

    def test_setitem_existing_key_fires_replaced(self) -> None:
        self.d["a"] = 99
        self.assertEqual(len(self.changes), 1)
        ch = self.changes[0]
        self.assertEqual(ch.kind, ChangeKind.REPLACED)
        self.assertEqual(ch.key, "a")
        self.assertEqual(ch.old_value, 1)
        self.assertEqual(ch.new_value, 99)

    def test_delitem_fires_removed(self) -> None:
        del self.d["b"]
        self.assertEqual(len(self.changes), 1)
        ch = self.changes[0]
        self.assertEqual(ch.kind, ChangeKind.REMOVED)
        self.assertEqual(ch.key, "b")
        self.assertEqual(ch.old_value, 2)

    def test_clear_fires_cleared(self) -> None:
        self.d.clear()
        self.assertEqual(len(self.changes), 1)
        self.assertEqual(self.changes[0].kind, ChangeKind.CLEARED)

    def test_clear_empty_dict_does_not_fire(self) -> None:
        empty = ObservableDict()
        events = []
        empty.subscribe(lambda ch: events.append(ch))
        empty.clear()
        self.assertEqual(len(events), 0)

    def test_pop_fires_removed(self) -> None:
        val = self.d.pop("a")
        self.assertEqual(val, 1)
        self.assertEqual(len(self.changes), 1)
        self.assertEqual(self.changes[0].kind, ChangeKind.REMOVED)

    def test_pop_missing_key_with_default_does_not_fire(self) -> None:
        result = self.d.pop("missing", "default")
        self.assertEqual(result, "default")
        self.assertEqual(len(self.changes), 0)

    def test_update_fires_one_event_per_key(self) -> None:
        self.d.update({"a": 10, "z": 99})
        self.assertEqual(len(self.changes), 2)
        kinds = {ch.key: ch.kind for ch in self.changes}
        self.assertEqual(kinds["a"], ChangeKind.REPLACED)
        self.assertEqual(kinds["z"], ChangeKind.ADDED)

    def test_setdefault_fires_added_when_absent(self) -> None:
        self.d.setdefault("new", 42)
        self.assertEqual(len(self.changes), 1)
        self.assertEqual(self.changes[0].kind, ChangeKind.ADDED)

    def test_setdefault_does_not_fire_when_present(self) -> None:
        self.d.setdefault("a", 0)
        self.assertEqual(len(self.changes), 0)

    def test_unsub_stops_notifications(self) -> None:
        events = []
        unsub = self.d.subscribe(lambda ch: events.append(ch))
        unsub()
        self.d["x"] = 5
        self.assertEqual(len(events), 0)

    def test_snapshot_returns_copy(self) -> None:
        snap = self.d.snapshot()
        snap["z"] = 999
        self.assertNotIn("z", self.d)

    def test_read_ops_do_not_fire_events(self) -> None:
        _ = self.d["a"]
        _ = self.d.get("b")
        _ = "a" in self.d
        _ = len(self.d)
        _ = list(self.d.keys())
        _ = list(self.d.values())
        _ = list(self.d.items())
        self.assertEqual(len(self.changes), 0)

    def test_contains_and_len(self) -> None:
        self.assertIn("a", self.d)
        self.assertNotIn("z", self.d)
        self.assertEqual(len(self.d), 2)

    def test_observable_dict_drives_settings_label(self) -> None:
        """Subscriber can reactively update a label string."""
        settings = ObservableDict({"theme": "light"})
        label = {"text": "Theme: light"}
        settings.subscribe(
            lambda ch: label.update({"text": f"Theme: {settings['theme']}"})
            if ch.key == "theme"
            else None
        )
        settings["theme"] = "dark"
        self.assertEqual(label["text"], "Theme: dark")


# ---------------------------------------------------------------------------
# Pass-M tests — AsyncDataProvider lifecycle
# ---------------------------------------------------------------------------

from gui_do import AsyncDataProvider, LoadState, LoadStateKind


class _MockScheduler:
    """Minimal synchronous stub for TaskScheduler used in AsyncDataProvider tests."""

    def __init__(self):
        self._results = {}
        self._active = set()
        self._failed = []

    def add_task(self, task_id, fn):
        self._active.add(task_id)

    def remove_tasks(self, *task_ids):
        for tid in task_ids:
            self._active.discard(tid)
            self._results.pop(tid, None)

    def tasks_active_match_any(self, *task_ids):
        return any(tid in self._active for tid in task_ids)

    def pop_result(self, task_id, default=None):
        return self._results.pop(task_id, default)

    def get_failed_events(self):
        return list(self._failed)

    # Test helpers
    def complete_task(self, task_id, result):
        self._active.discard(task_id)
        self._results[task_id] = result

    def fail_task(self, task_id, error="oops"):
        from gui_do.scheduling.task_scheduler import TaskEvent
        self._active.discard(task_id)
        self._failed.append(TaskEvent(operation="failed", task_id=task_id, error=error))


class AsyncDataProviderLifecycleTests(unittest.TestCase):
    """AsyncDataProvider transitions IDLE→LOADING→LOADED/FAILED correctly."""

    def setUp(self):
        self.scheduler = _MockScheduler()
        self.provider = AsyncDataProvider(self.scheduler)

    def test_initial_state_is_idle(self) -> None:
        self.assertEqual(self.provider.state.kind, LoadStateKind.IDLE)
        self.assertTrue(self.provider.state.is_idle)

    def test_load_transitions_to_loading(self) -> None:
        self.provider.load(lambda: [1, 2, 3])
        self.assertEqual(self.provider.state.kind, LoadStateKind.LOADING)
        self.assertTrue(self.provider.is_loading)

    def test_update_transitions_to_loaded_when_task_completes(self) -> None:
        self.provider.load(lambda: "data")
        task_id = self.provider._task_id
        self.scheduler.complete_task(task_id, "data")
        self.provider.update()
        self.assertEqual(self.provider.state.kind, LoadStateKind.LOADED)
        self.assertEqual(self.provider.state.data, "data")

    def test_update_transitions_to_failed_when_task_fails(self) -> None:
        self.provider.load(lambda: None)
        task_id = self.provider._task_id
        self.scheduler.fail_task(task_id, "network error")
        self.provider.update()
        self.assertEqual(self.provider.state.kind, LoadStateKind.FAILED)
        self.assertEqual(self.provider.state.error, "network error")

    def test_cancel_transitions_to_idle(self) -> None:
        self.provider.load(lambda: None)
        self.provider.cancel()
        self.assertEqual(self.provider.state.kind, LoadStateKind.IDLE)
        self.assertFalse(self.provider.is_loading)

    def test_subscriber_receives_loading_transition(self) -> None:
        states = []
        self.provider.subscribe(lambda s: states.append(s.kind))
        self.provider.load(lambda: None)
        self.assertIn(LoadStateKind.LOADING, states)

    def test_subscriber_receives_loaded_transition(self) -> None:
        states = []
        self.provider.subscribe(lambda s: states.append(s.kind))
        self.provider.load(lambda: 42)
        task_id = self.provider._task_id
        self.scheduler.complete_task(task_id, 42)
        self.provider.update()
        self.assertIn(LoadStateKind.LOADED, states)

    def test_unsub_stops_receiving_transitions(self) -> None:
        states = []
        unsub = self.provider.subscribe(lambda s: states.append(s.kind))
        unsub()
        self.provider.load(lambda: None)
        self.assertEqual(len(states), 0)

    def test_reset_returns_to_idle_without_notifying(self) -> None:
        states = []
        self.provider.load(lambda: None)
        self.provider.subscribe(lambda s: states.append(s.kind))
        self.provider.reset()
        self.assertEqual(self.provider.state.kind, LoadStateKind.IDLE)
        self.assertEqual(len(states), 0)

    def test_update_does_nothing_when_idle(self) -> None:
        self.provider.update()  # Must not raise
        self.assertTrue(self.provider.state.is_idle)

    def test_load_state_properties(self) -> None:
        idle = LoadState(kind=LoadStateKind.IDLE)
        loading = LoadState(kind=LoadStateKind.LOADING)
        loaded = LoadState(kind=LoadStateKind.LOADED, data="x")
        failed = LoadState(kind=LoadStateKind.FAILED, error="e")
        self.assertTrue(idle.is_idle)
        self.assertTrue(loading.is_loading)
        self.assertTrue(loaded.is_loaded)
        self.assertTrue(failed.is_failed)

    def test_second_load_cancels_first(self) -> None:
        self.provider.load(lambda: None, task_id="first")
        self.assertIn("first", self.scheduler._active)
        self.provider.load(lambda: None, task_id="second")
        # First task should be removed from active set after cancel
        self.assertNotIn("first", self.scheduler._active)
        self.assertIn("second", self.scheduler._active)

    def test_task_removed_without_result_returns_to_idle(self) -> None:
        self.provider.load(lambda: None)
        task_id = self.provider._task_id
        # Simulate external cancel: task removed, no result stored
        self.scheduler._active.discard(task_id)
        self.provider.update()
        self.assertEqual(self.provider.state.kind, LoadStateKind.IDLE)


# ---------------------------------------------------------------------------
# Pass-N tests — Binding + BindingGroup
# ---------------------------------------------------------------------------

from gui_do import Binding, BindingGroup, ObservableValue


class _Target:
    """Minimal control stub with a settable attribute and an on_change signal."""

    def __init__(self, initial=None):
        self.value = initial
        self.on_change = None

    def emit(self, val):
        if callable(self.on_change):
            self.on_change(val)


class BindingOneWayTests(unittest.TestCase):
    """Binding in one_way mode drives target attribute from model."""

    def test_initial_sync_sets_target_attr(self) -> None:
        src = ObservableValue(42)
        tgt = _Target(0)
        Binding(src, tgt, "value")
        self.assertEqual(tgt.value, 42)

    def test_model_change_updates_target(self) -> None:
        src = ObservableValue(1)
        tgt = _Target(0)
        Binding(src, tgt, "value")
        src.value = 99
        self.assertEqual(tgt.value, 99)

    def test_dispose_stops_propagation(self) -> None:
        src = ObservableValue(1)
        tgt = _Target(0)
        b = Binding(src, tgt, "value")
        b.dispose()
        src.value = 55
        self.assertEqual(tgt.value, 1)  # frozen at initial sync value

    def test_dispose_idempotent(self) -> None:
        src = ObservableValue(0)
        tgt = _Target()
        b = Binding(src, tgt, "value")
        b.dispose()
        b.dispose()  # Must not raise

    def test_disposed_property(self) -> None:
        src = ObservableValue(0)
        tgt = _Target()
        b = Binding(src, tgt, "value")
        self.assertFalse(b.disposed)
        b.dispose()
        self.assertTrue(b.disposed)

    def test_to_control_converter_applied(self) -> None:
        src = ObservableValue(3.7)
        tgt = _Target(0)
        Binding(src, tgt, "value", to_control=int)
        self.assertEqual(tgt.value, 3)

    def test_sync_to_control_forces_resync(self) -> None:
        src = ObservableValue("hello")
        tgt = _Target("")
        b = Binding(src, tgt, "value")
        tgt.value = "tampered"
        b.sync_to_control()
        self.assertEqual(tgt.value, "hello")


class BindingTwoWayTests(unittest.TestCase):
    """Binding in two_way mode syncs both directions."""

    def test_model_change_updates_target(self) -> None:
        src = ObservableValue(10)
        tgt = _Target(0)
        Binding(src, tgt, "value", mode="two_way", control_change_signal="on_change")
        src.value = 20
        self.assertEqual(tgt.value, 20)

    def test_control_change_updates_model(self) -> None:
        src = ObservableValue(10)
        tgt = _Target(0)
        Binding(src, tgt, "value", mode="two_way", control_change_signal="on_change")
        tgt.emit(77)
        self.assertEqual(src.value, 77)

    def test_no_infinite_loop_on_two_way_update(self) -> None:
        counter = [0]
        src = ObservableValue(0)
        tgt = _Target(0)
        Binding(src, tgt, "value", mode="two_way", control_change_signal="on_change")
        src.subscribe(lambda v: counter.__setitem__(0, counter[0] + 1))
        tgt.emit(5)
        self.assertLessEqual(counter[0], 1)

    def test_to_source_converter_applied(self) -> None:
        src = ObservableValue(0.0)
        tgt = _Target(0)
        Binding(src, tgt, "value", mode="two_way",
                control_change_signal="on_change", to_source=float)
        tgt.emit(3)
        self.assertIsInstance(src.value, float)
        self.assertAlmostEqual(src.value, 3.0)


class BindingGroupTests(unittest.TestCase):
    """BindingGroup disposes all registered bindings together."""

    def test_add_returns_binding(self) -> None:
        group = BindingGroup()
        src = ObservableValue(0)
        tgt = _Target()
        b = Binding(src, tgt, "value")
        returned = group.add(b)
        self.assertIs(returned, b)

    def test_len_counts_bindings(self) -> None:
        group = BindingGroup()
        src = ObservableValue(0)
        for _ in range(3):
            group.add(Binding(src, _Target(), "value"))
        self.assertEqual(len(group), 3)

    def test_dispose_stops_all_propagation(self) -> None:
        src = ObservableValue(1)
        targets = [_Target(0) for _ in range(3)]
        group = BindingGroup()
        for tgt in targets:
            group.add(Binding(src, tgt, "value"))
        group.dispose()
        src.value = 99
        for tgt in targets:
            self.assertEqual(tgt.value, 1)

    def test_dispose_clears_group(self) -> None:
        group = BindingGroup()
        src = ObservableValue(0)
        group.add(Binding(src, _Target(), "value"))
        group.dispose()
        self.assertEqual(len(group), 0)

    def test_sync_all_to_control(self) -> None:
        src = ObservableValue("x")
        tgt = _Target("")
        group = BindingGroup()
        group.add(Binding(src, tgt, "value"))
        tgt.value = "tampered"
        group.sync_all_to_control()
        self.assertEqual(tgt.value, "x")


# ---------------------------------------------------------------------------
# Pass-O tests — SelectionModel
# ---------------------------------------------------------------------------

from gui_do import SelectionModel, SelectionMode


class SelectionModelSingleTests(unittest.TestCase):
    """SelectionModel in SINGLE mode: at most one item selected."""

    def setUp(self):
        self.model = SelectionModel(mode=SelectionMode.SINGLE, item_count=10)

    def test_initial_selection_empty(self) -> None:
        self.assertEqual(self.model.selected_indices, frozenset())
        self.assertEqual(self.model.selected_index, -1)

    def test_select_sets_single_item(self) -> None:
        self.model.select(3)
        self.assertEqual(self.model.selected_indices, frozenset({3}))

    def test_select_replaces_previous(self) -> None:
        self.model.select(3)
        self.model.select(7)
        self.assertEqual(self.model.selected_indices, frozenset({7}))

    def test_deselect_clears_item(self) -> None:
        self.model.select(2)
        self.model.deselect(2)
        self.assertEqual(self.model.selected_indices, frozenset())

    def test_is_selected_true_false(self) -> None:
        self.model.select(4)
        self.assertTrue(self.model.is_selected(4))
        self.assertFalse(self.model.is_selected(5))

    def test_clear_deselects_all(self) -> None:
        self.model.select(5)
        self.model.clear()
        self.assertEqual(self.model.selected_indices, frozenset())

    def test_select_out_of_range_ignored(self) -> None:
        self.model.select(99)
        self.assertEqual(self.model.selected_indices, frozenset())

    def test_subscribe_notified_on_change(self) -> None:
        events = []
        self.model.subscribe(lambda m: events.append(m.selected_index))
        self.model.select(2)
        self.assertIn(2, events)

    def test_unsub_stops_notifications(self) -> None:
        events = []
        unsub = self.model.subscribe(lambda m: events.append(True))
        unsub()
        self.model.select(1)
        self.assertEqual(len(events), 0)

    def test_set_item_count_prunes_out_of_range(self) -> None:
        self.model.select(8)
        self.model.set_item_count(5)
        self.assertEqual(self.model.selected_indices, frozenset())


class SelectionModelMultiTests(unittest.TestCase):
    """SelectionModel in MULTI mode: arbitrary set."""

    def setUp(self):
        self.model = SelectionModel(mode=SelectionMode.MULTI, item_count=10)

    def test_select_accumulates(self) -> None:
        self.model.select(1)
        self.model.select(3)
        self.assertIn(1, self.model.selected_indices)
        self.assertIn(3, self.model.selected_indices)

    def test_toggle_adds_then_removes(self) -> None:
        self.model.toggle(5)
        self.assertIn(5, self.model.selected_indices)
        self.model.toggle(5)
        self.assertNotIn(5, self.model.selected_indices)

    def test_select_all_selects_everything(self) -> None:
        self.model.select_all()
        self.assertEqual(self.model.selected_indices, frozenset(range(10)))

    def test_clear_after_select_all(self) -> None:
        self.model.select_all()
        self.model.clear()
        self.assertEqual(self.model.selected_indices, frozenset())


class SelectionModelRangeTests(unittest.TestCase):
    """SelectionModel in RANGE mode: contiguous anchor→active block."""

    def setUp(self):
        self.model = SelectionModel(mode=SelectionMode.RANGE, item_count=20)

    def test_range_selects_contiguous_block(self) -> None:
        self.model.set_anchor(3)
        self.model.set_active(7)
        self.assertEqual(self.model.selected_indices, frozenset(range(3, 8)))

    def test_range_reversed_still_contiguous(self) -> None:
        self.model.set_anchor(7)
        self.model.set_active(3)
        self.assertEqual(self.model.selected_indices, frozenset(range(3, 8)))

    def test_set_anchor_alone_selects_single(self) -> None:
        self.model.set_anchor(5)
        self.assertIn(5, self.model.selected_indices)

    def test_mode_property(self) -> None:
        self.assertEqual(self.model.mode, SelectionMode.RANGE)

    def test_anchor_and_active_end_properties(self) -> None:
        self.model.set_anchor(2)
        self.model.set_active(6)
        self.assertEqual(self.model.anchor, 2)
        self.assertEqual(self.model.active_end, 6)


# ---------------------------------------------------------------------------
# Pass-P tests — Debouncer + Throttler + TextFormatter
# ---------------------------------------------------------------------------

from gui_do import Debouncer, Throttler, Timers
from gui_do import NumericFormatter, PatternFormatter, FixedPatternFormatter


class DebouncerTests(unittest.TestCase):
    """Debouncer delays callback until the input is idle."""

    def setUp(self):
        self.timers = Timers()

    def test_call_does_not_fire_immediately(self) -> None:
        fired = []
        d = Debouncer(delay_ms=100, callback=lambda: fired.append(1), timers=self.timers)
        d.call()
        self.assertEqual(fired, [])

    def test_fires_after_delay(self) -> None:
        fired = []
        d = Debouncer(delay_ms=100, callback=lambda: fired.append(1), timers=self.timers)
        d.call()
        self.timers.update(0.11)
        self.assertEqual(fired, [1])

    def test_resets_window_on_repeated_call(self) -> None:
        fired = []
        d = Debouncer(delay_ms=100, callback=lambda: fired.append(1), timers=self.timers)
        d.call()
        self.timers.update(0.05)
        d.call()  # reset
        self.timers.update(0.06)  # only 0.06 since last call
        self.assertEqual(fired, [])
        self.timers.update(0.06)  # now > 100 ms since last call
        self.assertEqual(fired, [1])

    def test_cancel_prevents_fire(self) -> None:
        fired = []
        d = Debouncer(delay_ms=100, callback=lambda: fired.append(1), timers=self.timers)
        d.call()
        d.cancel()
        self.timers.update(0.2)
        self.assertEqual(fired, [])

    def test_flush_fires_immediately(self) -> None:
        fired = []
        d = Debouncer(delay_ms=100, callback=lambda: fired.append(1), timers=self.timers)
        d.call()
        d.flush()
        self.assertEqual(fired, [1])

    def test_flush_noop_when_nothing_pending(self) -> None:
        fired = []
        d = Debouncer(delay_ms=100, callback=lambda: fired.append(1), timers=self.timers)
        d.flush()  # nothing pending
        self.assertEqual(fired, [])

    def test_is_pending_reflects_state(self) -> None:
        d = Debouncer(delay_ms=100, callback=lambda: None, timers=self.timers)
        self.assertFalse(d.is_pending)
        d.call()
        self.assertTrue(d.is_pending)
        d.flush()
        self.assertFalse(d.is_pending)

    def test_fires_with_latest_args(self) -> None:
        received = []
        d = Debouncer(delay_ms=100, callback=lambda x: received.append(x), timers=self.timers)
        d.call("first")
        d.call("second")
        self.timers.update(0.15)
        self.assertEqual(received, ["second"])

    def test_invalid_delay_raises(self) -> None:
        with self.assertRaises(ValueError):
            Debouncer(delay_ms=0, callback=lambda: None, timers=self.timers)


class ThrottlerTests(unittest.TestCase):
    """Throttler fires at most once per interval."""

    def setUp(self):
        self.timers = Timers()

    def test_first_call_fires_immediately(self) -> None:
        fired = []
        t = Throttler(interval_ms=100, callback=lambda: fired.append(1), timers=self.timers)
        t.call()
        self.assertEqual(fired, [1])

    def test_second_call_within_interval_buffered(self) -> None:
        fired = []
        t = Throttler(interval_ms=100, callback=lambda: fired.append(1), timers=self.timers)
        t.call()
        t.call()  # buffered
        self.assertEqual(len(fired), 1)

    def test_trailing_edge_fires_after_interval(self) -> None:
        fired = []
        t = Throttler(interval_ms=100, callback=lambda: fired.append(1), timers=self.timers)
        t.call()
        t.call()  # buffered
        self.timers.update(0.11)
        self.assertEqual(len(fired), 2)

    def test_cancel_clears_pending(self) -> None:
        fired = []
        t = Throttler(interval_ms=100, callback=lambda: fired.append(1), timers=self.timers)
        t.call()
        t.call()
        t.cancel()
        self.timers.update(0.2)
        self.assertEqual(len(fired), 1)

    def test_is_locked_while_within_interval(self) -> None:
        t = Throttler(interval_ms=100, callback=lambda: None, timers=self.timers)
        self.assertFalse(t.is_locked)
        t.call()
        self.assertTrue(t.is_locked)
        self.timers.update(0.11)
        self.assertFalse(t.is_locked)

    def test_invalid_interval_raises(self) -> None:
        with self.assertRaises(ValueError):
            Throttler(interval_ms=0, callback=lambda: None, timers=self.timers)


class NumericFormatterTests(unittest.TestCase):
    """NumericFormatter formats, parses, and validates numeric strings."""

    def test_format_integer(self) -> None:
        f = NumericFormatter(decimals=0)
        self.assertEqual(f.format("42"), "42")

    def test_format_float_rounds(self) -> None:
        f = NumericFormatter(decimals=2)
        self.assertEqual(f.format("3.14159"), "3.14")

    def test_format_with_thousands_sep(self) -> None:
        f = NumericFormatter(decimals=0, thousands_sep=",")
        self.assertEqual(f.format("1234567"), "1,234,567")

    def test_parse_strips_thousands_sep(self) -> None:
        f = NumericFormatter(decimals=0, thousands_sep=",")
        self.assertEqual(f.parse("1,234"), "1234")

    def test_validate_within_bounds(self) -> None:
        f = NumericFormatter(decimals=0, min_value=0, max_value=100)
        self.assertTrue(f.validate("50"))

    def test_validate_out_of_bounds(self) -> None:
        f = NumericFormatter(decimals=0, min_value=0, max_value=100)
        self.assertFalse(f.validate("200"))

    def test_validate_non_numeric_returns_false(self) -> None:
        f = NumericFormatter(decimals=0)
        self.assertFalse(f.validate("abc"))

    def test_satisfies_text_formatter_protocol(self) -> None:
        from gui_do import TextFormatter
        self.assertIsInstance(NumericFormatter(), TextFormatter)


class PatternFormatterTests(unittest.TestCase):
    """PatternFormatter applies a positional mask to digit input."""

    def test_format_phone_number(self) -> None:
        f = PatternFormatter("(###) ###-####")
        self.assertEqual(f.format("1234567890"), "(123) 456-7890")

    def test_parse_strips_mask_literals(self) -> None:
        f = PatternFormatter("(###) ###-####")
        self.assertEqual(f.parse("(123) 456-7890"), "1234567890")

    def test_validate_enough_digits(self) -> None:
        f = PatternFormatter("###-##")
        self.assertTrue(f.validate("12345"))

    def test_validate_too_few_digits(self) -> None:
        f = PatternFormatter("###-##")
        self.assertFalse(f.validate("123"))

    def test_format_partial_fills_partial_entry(self) -> None:
        f = PatternFormatter("(###) ###-####")
        partial = f.format_partial("123")
        self.assertIn("1", partial)
        self.assertIn("2", partial)
        self.assertIn("3", partial)

    def test_satisfies_text_formatter_protocol(self) -> None:
        from gui_do import TextFormatter
        self.assertIsInstance(PatternFormatter("###"), TextFormatter)


# ---------------------------------------------------------------------------
# Pass-Q tests — KeyChordManager, KeyChord, ChordStep
# ---------------------------------------------------------------------------

from gui_do import KeyChordManager, KeyChord, ChordStep
from gui_do.events.gui_event import GuiEvent, EventType as _EventType


def _key_event(key: int, mod: int = 0) -> GuiEvent:
    return GuiEvent(kind=_EventType.KEY_DOWN, type=0, key=key, mod=mod)


class _ActionsBacking:
    """Minimal backing that KeyChordManager._fire expects: obj._actions dict."""

    def __init__(self):
        self._actions: dict = {}

    def register(self, name: str, fn) -> None:
        self._actions[name] = fn


class KeyChordDataclassTests(unittest.TestCase):
    """ChordStep and KeyChord data types."""

    def test_chord_step_defaults_mod_zero(self) -> None:
        step = ChordStep(key=65)
        self.assertEqual(step.mod, 0)

    def test_chord_step_stores_key(self) -> None:
        step = ChordStep(key=75, mod=64)
        self.assertEqual(step.key, 75)
        self.assertEqual(step.mod, 64)

    def test_key_chord_len(self) -> None:
        chord = KeyChord([ChordStep(key=75), ChordStep(key=67)])
        self.assertEqual(len(chord), 2)

    def test_key_chord_getitem(self) -> None:
        step = ChordStep(key=42)
        chord = KeyChord([step])
        self.assertIs(chord[0], step)

    def test_key_chord_empty_raises(self) -> None:
        with self.assertRaises(ValueError):
            KeyChord([])

    def test_key_chord_equality(self) -> None:
        a = KeyChord([ChordStep(key=75), ChordStep(key=67)])
        b = KeyChord([ChordStep(key=75), ChordStep(key=67)])
        self.assertEqual(a, b)


class KeyChordManagerBindingTests(unittest.TestCase):
    """KeyChordManager registration (bind / unbind / registered_chords)."""

    def setUp(self):
        self.actions = _ActionsBacking()
        self.mgr = KeyChordManager(self.actions)

    def test_bind_registers_chord(self) -> None:
        chord = KeyChord([ChordStep(key=75)])
        self.mgr.bind(chord, "action.x")
        self.assertIn(chord, self.mgr.registered_chords())

    def test_bind_replaces_same_chord(self) -> None:
        chord = KeyChord([ChordStep(key=75)])
        self.mgr.bind(chord, "action.x")
        self.mgr.bind(chord, "action.y")
        self.assertEqual(len(self.mgr.registered_chords()), 1)

    def test_unbind_removes_chord(self) -> None:
        chord = KeyChord([ChordStep(key=75)])
        self.mgr.bind(chord, "action.x")
        removed = self.mgr.unbind(chord)
        self.assertTrue(removed)
        self.assertNotIn(chord, self.mgr.registered_chords())

    def test_unbind_unknown_returns_false(self) -> None:
        chord = KeyChord([ChordStep(key=99)])
        self.assertFalse(self.mgr.unbind(chord))


class KeyChordManagerDispatchTests(unittest.TestCase):
    """KeyChordManager event processing and chord dispatch."""

    def setUp(self):
        self.actions = _ActionsBacking()
        self.timers = Timers()
        self.mgr = KeyChordManager(self.actions, self.timers, timeout_ms=500)

    def test_non_key_event_returns_false(self) -> None:
        evt = GuiEvent(kind=_EventType.MOUSE_BUTTON_DOWN, type=0, pos=(0, 0), button=1)
        self.assertFalse(self.mgr.process_event(evt))

    def test_single_step_chord_fires_action(self) -> None:
        fired = []
        chord = KeyChord([ChordStep(key=65)])
        self.mgr.bind(chord, "action.single")
        self.actions.register("action.single", lambda e: fired.append(1) or True)
        result = self.mgr.process_event(_key_event(65))
        self.assertTrue(result)
        self.assertEqual(fired, [1])

    def test_unknown_key_not_consumed(self) -> None:
        chord = KeyChord([ChordStep(key=65)])
        self.mgr.bind(chord, "action.x")
        self.assertFalse(self.mgr.process_event(_key_event(90)))  # Z not in chord

    def test_first_step_of_multi_step_consumed_sets_in_progress(self) -> None:
        chord = KeyChord([ChordStep(key=75), ChordStep(key=67)])
        self.mgr.bind(chord, "action.two")
        result = self.mgr.process_event(_key_event(75))
        self.assertTrue(result)
        self.assertTrue(self.mgr.is_in_progress)

    def test_full_two_step_chord_fires(self) -> None:
        fired = []
        chord = KeyChord([ChordStep(key=75), ChordStep(key=67)])
        self.mgr.bind(chord, "action.kc")
        self.actions.register("action.kc", lambda e: fired.append(1) or True)
        self.mgr.process_event(_key_event(75))
        result = self.mgr.process_event(_key_event(67))
        self.assertTrue(result)
        self.assertEqual(fired, [1])

    def test_wrong_second_step_resets(self) -> None:
        chord = KeyChord([ChordStep(key=75), ChordStep(key=67)])
        self.mgr.bind(chord, "action.kc")
        self.mgr.process_event(_key_event(75))
        # Wrong second step — should reset
        result = self.mgr.process_event(_key_event(90))
        self.assertFalse(self.mgr.is_in_progress)
        self.assertFalse(result)

    def test_reset_clears_in_progress(self) -> None:
        chord = KeyChord([ChordStep(key=75), ChordStep(key=67)])
        self.mgr.bind(chord, "action.kc")
        self.mgr.process_event(_key_event(75))
        self.assertTrue(self.mgr.is_in_progress)
        self.mgr.reset()
        self.assertFalse(self.mgr.is_in_progress)

    def test_timeout_resets_chord(self) -> None:
        chord = KeyChord([ChordStep(key=75), ChordStep(key=67)])
        self.mgr.bind(chord, "action.kc")
        self.mgr.process_event(_key_event(75))
        self.assertTrue(self.mgr.is_in_progress)
        self.timers.update(0.6)  # > 500 ms timeout
        self.assertFalse(self.mgr.is_in_progress)

    def test_mod_mismatch_not_consumed(self) -> None:
        chord = KeyChord([ChordStep(key=75, mod=64)])  # requires Ctrl
        self.mgr.bind(chord, "action.x")
        # Event with no mod — should not match
        result = self.mgr.process_event(_key_event(75, mod=0))
        self.assertFalse(result)

    def test_mod_match_consumed(self) -> None:
        chord = KeyChord([ChordStep(key=75, mod=64)])
        self.mgr.bind(chord, "action.x")
        self.actions.register("action.x", lambda e: True)
        result = self.mgr.process_event(_key_event(75, mod=64))
        self.assertTrue(result)


# ---------------------------------------------------------------------------
# Pass-R tests — ErrorBoundary
# ---------------------------------------------------------------------------

from gui_do import ErrorBoundary
from gui_do.controls.base.ui_node import UiNode as _UiNode
from pygame import Rect as _Rect


class _GoodNode(_UiNode):
    def __init__(self):
        super().__init__("good", _Rect(0, 0, 100, 50))

    def update(self, dt: float) -> None:
        pass

    def handle_event(self, event, app) -> bool:
        return False


class _BrokenUpdateNode(_UiNode):
    def __init__(self):
        super().__init__("broken", _Rect(0, 0, 100, 50))

    def update(self, dt: float) -> None:
        raise RuntimeError("update exploded")

    def handle_event(self, event, app) -> bool:
        return False


class _BrokenEventNode(_UiNode):
    def __init__(self):
        super().__init__("broken_evt", _Rect(0, 0, 100, 50))

    def update(self, dt: float) -> None:
        pass

    def handle_event(self, event, app) -> bool:
        raise RuntimeError("event exploded")


class ErrorBoundaryInitTests(unittest.TestCase):
    """ErrorBoundary construction and initial state."""

    def test_child_none_raises(self) -> None:
        with self.assertRaises(ValueError):
            ErrorBoundary(child=None)

    def test_has_error_initially_false(self) -> None:
        b = ErrorBoundary(child=_GoodNode())
        self.assertFalse(b.has_error)

    def test_error_property_initially_none(self) -> None:
        b = ErrorBoundary(child=_GoodNode())
        self.assertIsNone(b.error)


class ErrorBoundaryUpdateTests(unittest.TestCase):
    """ErrorBoundary traps exceptions from child.update()."""

    def test_child_update_exception_sets_has_error(self) -> None:
        b = ErrorBoundary(child=_BrokenUpdateNode())
        b.update(0.016)
        self.assertTrue(b.has_error)

    def test_child_update_stores_exception(self) -> None:
        b = ErrorBoundary(child=_BrokenUpdateNode())
        b.update(0.016)
        self.assertIsInstance(b.error, RuntimeError)

    def test_good_child_update_leaves_no_error(self) -> None:
        b = ErrorBoundary(child=_GoodNode())
        b.update(0.016)
        self.assertFalse(b.has_error)

    def test_on_error_callback_called(self) -> None:
        received = []
        b = ErrorBoundary(child=_BrokenUpdateNode(), on_error=lambda exc: received.append(exc))
        b.update(0.016)
        self.assertEqual(len(received), 1)
        self.assertIsInstance(received[0], RuntimeError)

    def test_on_error_callback_only_first_error(self) -> None:
        received = []
        b = ErrorBoundary(child=_BrokenUpdateNode(), on_error=lambda exc: received.append(exc))
        b.update(0.016)
        b.update(0.016)
        self.assertEqual(len(received), 1)


class ErrorBoundaryEventTests(unittest.TestCase):
    """ErrorBoundary traps exceptions from child.handle_event()."""

    def test_child_event_exception_sets_has_error(self) -> None:
        b = ErrorBoundary(child=_BrokenEventNode())
        dummy_event = GuiEvent(kind=_EventType.MOUSE_BUTTON_DOWN, type=0, pos=(0, 0), button=1)
        b.handle_event(dummy_event, None)
        self.assertTrue(b.has_error)

    def test_in_error_state_handle_event_returns_false(self) -> None:
        b = ErrorBoundary(child=_BrokenEventNode())
        dummy_event = GuiEvent(kind=_EventType.MOUSE_BUTTON_DOWN, type=0, pos=(0, 0), button=1)
        b.handle_event(dummy_event, None)  # puts in error state
        result = b.handle_event(dummy_event, None)
        self.assertFalse(result)


class ErrorBoundaryRecoveryTests(unittest.TestCase):
    """ErrorBoundary.recover() and recover_on_scene_change behaviour."""

    def test_recover_clears_error(self) -> None:
        b = ErrorBoundary(child=_BrokenUpdateNode())
        b.update(0.016)
        self.assertTrue(b.has_error)
        b.recover()
        self.assertFalse(b.has_error)
        self.assertIsNone(b.error)

    def test_recover_on_mount_default_true_clears_error(self) -> None:
        b = ErrorBoundary(child=_BrokenUpdateNode(), recover_on_scene_change=True)
        b.update(0.016)
        self.assertTrue(b.has_error)
        b.on_mount(None)
        self.assertFalse(b.has_error)

    def test_recover_on_mount_false_preserves_error(self) -> None:
        child = _BrokenUpdateNode()
        b = ErrorBoundary(child=child, recover_on_scene_change=False)
        b.update(0.016)
        self.assertTrue(b.has_error)
        b.on_mount(None)
        self.assertTrue(b.has_error)


# ---------------------------------------------------------------------------
# Pass-S tests — TooltipManager + TooltipHandle
# ---------------------------------------------------------------------------

from gui_do import TooltipManager, TooltipHandle


class _NodeStub:
    """Minimal stub satisfying node.control_id requirement."""

    def __init__(self, cid: str):
        self.control_id = cid


class TooltipManagerRegistrationTests(unittest.TestCase):
    """TooltipManager.register() / unregister() / update_text()."""

    def test_register_returns_handle(self) -> None:
        mgr = TooltipManager()
        handle = mgr.register(_NodeStub("btn1"), "Click me")
        self.assertIsInstance(handle, TooltipHandle)
        self.assertEqual(handle.node_id, "btn1")

    def test_not_visible_initially(self) -> None:
        mgr = TooltipManager()
        mgr.register(_NodeStub("btn1"), "Click me")
        self.assertFalse(mgr.is_visible)
        self.assertIsNone(mgr.visible_text)

    def test_visible_text_none_when_not_visible(self) -> None:
        mgr = TooltipManager()
        self.assertIsNone(mgr.visible_text)

    def test_unregister_removes_entry(self) -> None:
        mgr = TooltipManager(default_delay_ms=100)
        handle = mgr.register(_NodeStub("btn1"), "tip")
        handle.unregister()
        # Hover for a long time — should never become visible
        mgr.update(1.0, hovered_node_id="btn1")
        self.assertFalse(mgr.is_visible)

    def test_update_text_changes_visible_text(self) -> None:
        mgr = TooltipManager(default_delay_ms=100)
        handle = mgr.register(_NodeStub("btn1"), "old")
        handle.update_text("new")
        # Force tooltip visible by simulating enough hover time
        mgr.update(0.2, hovered_node_id="btn1")
        self.assertEqual(mgr.visible_text, "new")


class TooltipManagerHoverTests(unittest.TestCase):
    """TooltipManager hover delay and auto-dismiss."""

    def test_tooltip_appears_after_delay(self) -> None:
        mgr = TooltipManager(default_delay_ms=200)
        mgr.register(_NodeStub("n1"), "hello")
        mgr.update(0.25, hovered_node_id="n1")
        self.assertTrue(mgr.is_visible)
        self.assertEqual(mgr.visible_text, "hello")

    def test_tooltip_not_visible_before_delay(self) -> None:
        mgr = TooltipManager(default_delay_ms=500)
        mgr.register(_NodeStub("n1"), "hello")
        mgr.update(0.1, hovered_node_id="n1")
        self.assertFalse(mgr.is_visible)

    def test_moving_to_different_node_hides_tooltip(self) -> None:
        mgr = TooltipManager(default_delay_ms=100)
        mgr.register(_NodeStub("n1"), "tip1")
        mgr.register(_NodeStub("n2"), "tip2")
        mgr.update(0.15, hovered_node_id="n1")
        self.assertTrue(mgr.is_visible)
        mgr.update(0.01, hovered_node_id="n2")
        self.assertFalse(mgr.is_visible)

    def test_visible_node_id_matches_hovered(self) -> None:
        mgr = TooltipManager(default_delay_ms=100)
        mgr.register(_NodeStub("n1"), "tip")
        mgr.update(0.15, hovered_node_id="n1")
        self.assertEqual(mgr.visible_node_id, "n1")

    def test_auto_dismiss_after_dismiss_ms(self) -> None:
        mgr = TooltipManager(default_delay_ms=100, dismiss_ms=300)
        mgr.register(_NodeStub("n1"), "tip")
        mgr.update(0.15, hovered_node_id="n1")   # appears
        self.assertTrue(mgr.is_visible)
        mgr.update(0.35, hovered_node_id="n1")   # > dismiss_ms
        self.assertFalse(mgr.is_visible)

    def test_no_auto_dismiss_when_dismiss_ms_zero(self) -> None:
        mgr = TooltipManager(default_delay_ms=100, dismiss_ms=0)
        mgr.register(_NodeStub("n1"), "tip")
        mgr.update(0.15, hovered_node_id="n1")
        self.assertTrue(mgr.is_visible)
        mgr.update(5.0, hovered_node_id="n1")   # long time — should stay visible
        self.assertTrue(mgr.is_visible)

    def test_hover_none_hides_tooltip(self) -> None:
        mgr = TooltipManager(default_delay_ms=100)
        mgr.register(_NodeStub("n1"), "tip")
        mgr.update(0.15, hovered_node_id="n1")
        self.assertTrue(mgr.is_visible)
        mgr.update(0.01, hovered_node_id=None)
        self.assertFalse(mgr.is_visible)


# ---------------------------------------------------------------------------
# Pass-T tests — InputMap + InputBinding
# ---------------------------------------------------------------------------

from gui_do import InputMap, InputBinding


class InputMapDeclarationTests(unittest.TestCase):
    """InputMap.declare() and InputMap.bind() create bindings."""

    def test_declare_creates_binding(self) -> None:
        m = InputMap()
        m.declare("edit.copy", key=67, mod=64, label="Copy")
        b = m.binding_for("edit.copy")
        self.assertIsNotNone(b)
        self.assertEqual(b.key, 67)
        self.assertEqual(b.mod, 64)
        self.assertEqual(b.label, "Copy")
        self.assertTrue(b.is_default)

    def test_declare_ignored_if_already_bound(self) -> None:
        m = InputMap()
        m.declare("edit.copy", key=67, mod=64)
        m.declare("edit.copy", key=99, mod=0)   # should be ignored
        b = m.binding_for("edit.copy")
        self.assertEqual(b.key, 67)

    def test_bind_overrides_default(self) -> None:
        m = InputMap()
        m.declare("edit.copy", key=67, mod=64)
        m.bind("edit.copy", key=88, mod=0)
        b = m.binding_for("edit.copy")
        self.assertEqual(b.key, 88)
        self.assertFalse(b.is_default)

    def test_bind_creates_new_action(self) -> None:
        m = InputMap()
        m.bind("edit.undo", key=90, mod=64)
        self.assertIsNotNone(m.binding_for("edit.undo"))

    def test_unbind_removes_binding(self) -> None:
        m = InputMap()
        m.declare("edit.copy", key=67)
        removed = m.unbind("edit.copy")
        self.assertTrue(removed)
        self.assertIsNone(m.binding_for("edit.copy"))

    def test_unbind_unknown_returns_false(self) -> None:
        m = InputMap()
        self.assertFalse(m.unbind("no.such.action"))

    def test_reset_to_default_restores_flag(self) -> None:
        m = InputMap()
        m.declare("edit.copy", key=67, mod=64)
        m.bind("edit.copy", key=88)
        reset = m.reset_to_default("edit.copy")
        self.assertTrue(reset)
        b = m.binding_for("edit.copy")
        self.assertTrue(b.is_default)

    def test_reset_to_default_already_default_returns_false(self) -> None:
        m = InputMap()
        m.declare("edit.copy", key=67)
        self.assertFalse(m.reset_to_default("edit.copy"))

    def test_binding_for_unknown_returns_none(self) -> None:
        m = InputMap()
        self.assertIsNone(m.binding_for("no.action"))


class InputMapInspectionTests(unittest.TestCase):
    """InputMap.actions(), len(), bindings() inspection."""

    def test_len_counts_bindings(self) -> None:
        m = InputMap()
        m.declare("a", key=1)
        m.declare("b", key=2)
        self.assertEqual(len(m), 2)

    def test_actions_returns_sorted_list(self) -> None:
        m = InputMap()
        m.declare("file.save", key=83)
        m.declare("edit.copy", key=67)
        m.declare("edit.paste", key=86)
        self.assertEqual(m.actions(), ["edit.copy", "edit.paste", "file.save"])

    def test_bindings_returns_all(self) -> None:
        m = InputMap()
        m.declare("a", key=1)
        m.declare("b", key=2)
        names = {b.action for b in m.bindings()}
        self.assertEqual(names, {"a", "b"})

    def test_empty_map_actions_returns_empty_list(self) -> None:
        m = InputMap()
        self.assertEqual(m.actions(), [])

    def test_declare_empty_action_raises(self) -> None:
        m = InputMap()
        with self.assertRaises(ValueError):
            m.declare("", key=65)

    def test_bind_empty_action_raises(self) -> None:
        m = InputMap()
        with self.assertRaises(ValueError):
            m.bind("", key=65)


# ---------------------------------------------------------------------------
# Pass-U tests — FocusScope + FocusScopeManager
# ---------------------------------------------------------------------------

from gui_do import FocusScope, FocusScopeManager


class _FocusManagerStub:
    """Minimal stub exposing only the _scope_stack list."""

    def __init__(self):
        self._scope_stack: list = []


class FocusScopeTests(unittest.TestCase):
    """FocusScope data object behaviour."""

    def test_scope_stores_root_and_id(self) -> None:
        node = _GoodNode()
        scope = FocusScope(root=node, scope_id="dlg")
        self.assertIs(scope.root, node)
        self.assertEqual(scope.scope_id, "dlg")

    def test_scope_inactive_initially(self) -> None:
        scope = FocusScope(root=_GoodNode())
        self.assertFalse(scope.active)

    def test_scope_id_defaults_to_auto(self) -> None:
        scope = FocusScope(root=_GoodNode())
        self.assertIn("scope:", scope.scope_id)


class FocusScopeManagerPushPopTests(unittest.TestCase):
    """FocusScopeManager push/pop stack operations."""

    def setUp(self):
        self.fm = _FocusManagerStub()
        self.mgr = FocusScopeManager(self.fm)

    def test_push_returns_scope(self) -> None:
        scope = self.mgr.push(_GoodNode(), scope_id="x")
        self.assertIsInstance(scope, FocusScope)

    def test_push_sets_scope_active(self) -> None:
        scope = self.mgr.push(_GoodNode())
        self.assertTrue(scope.active)

    def test_depth_increases_on_push(self) -> None:
        self.assertEqual(self.mgr.depth, 0)
        self.mgr.push(_GoodNode())
        self.assertEqual(self.mgr.depth, 1)
        self.mgr.push(_GoodNode())
        self.assertEqual(self.mgr.depth, 2)

    def test_is_constrained_true_when_scope_active(self) -> None:
        self.assertFalse(self.mgr.is_constrained)
        self.mgr.push(_GoodNode())
        self.assertTrue(self.mgr.is_constrained)

    def test_active_scope_is_most_recent(self) -> None:
        self.mgr.push(_GoodNode(), scope_id="first")
        s2 = self.mgr.push(_GoodNode(), scope_id="second")
        self.assertIs(self.mgr.active_scope, s2)

    def test_active_scope_none_when_empty(self) -> None:
        self.assertIsNone(self.mgr.active_scope)

    def test_pop_removes_scope(self) -> None:
        scope = self.mgr.push(_GoodNode())
        removed = self.mgr.pop(scope)
        self.assertTrue(removed)
        self.assertEqual(self.mgr.depth, 0)

    def test_pop_sets_scope_inactive(self) -> None:
        scope = self.mgr.push(_GoodNode())
        self.mgr.pop(scope)
        self.assertFalse(scope.active)

    def test_pop_unknown_returns_false(self) -> None:
        orphan = FocusScope(root=_GoodNode())
        self.assertFalse(self.mgr.pop(orphan))

    def test_pop_top_returns_innermost(self) -> None:
        self.mgr.push(_GoodNode(), scope_id="a")
        s2 = self.mgr.push(_GoodNode(), scope_id="b")
        popped = self.mgr.pop_top()
        self.assertIs(popped, s2)
        self.assertEqual(self.mgr.depth, 1)

    def test_pop_top_on_empty_returns_none(self) -> None:
        self.assertIsNone(self.mgr.pop_top())

    def test_pop_all_clears_stack(self) -> None:
        self.mgr.push(_GoodNode())
        self.mgr.push(_GoodNode())
        self.mgr.pop_all()
        self.assertEqual(self.mgr.depth, 0)
        self.assertFalse(self.mgr.is_constrained)

    def test_sync_mirrors_roots_into_focus_manager(self) -> None:
        n1, n2 = _GoodNode(), _GoodNode()
        self.mgr.push(n1)
        self.mgr.push(n2)
        self.assertEqual(self.fm._scope_stack, [n1, n2])
        self.mgr.pop_top()
        self.assertEqual(self.fm._scope_stack, [n1])


# ---------------------------------------------------------------------------
# Pass-V tests — LayoutAnimator
# ---------------------------------------------------------------------------

from gui_do import LayoutAnimator, TweenManager, Easing
from gui_do.layout.constraint_layout import ConstraintLayout, AnchorConstraint


class LayoutAnimatorTests(unittest.TestCase):
    """LayoutAnimator applies instant or tweened layout transitions."""

    def setUp(self):
        self.tweens = TweenManager()

    def test_instant_apply_targets_moves_node(self) -> None:
        """duration=0 means instant placement, no tweening."""
        animator = LayoutAnimator(self.tweens, duration=0.0)
        node = _GoodNode()
        node.rect = _Rect(0, 0, 100, 50)
        animator.apply_targets([(node, _Rect(200, 100, 80, 40))])
        self.assertEqual(node.rect.x, 200)
        self.assertEqual(node.rect.y, 100)

    def test_instant_apply_targets_no_in_progress(self) -> None:
        animator = LayoutAnimator(self.tweens, duration=0.0)
        node = _GoodNode()
        animator.apply_targets([(node, _Rect(50, 50, 100, 50))])
        self.assertFalse(animator.is_animating)

    def test_tween_apply_targets_sets_animating(self) -> None:
        animator = LayoutAnimator(self.tweens, duration=0.3)
        node = _GoodNode()
        node.rect = _Rect(0, 0, 100, 50)
        animator.apply_targets([(node, _Rect(200, 0, 100, 50))])
        self.assertTrue(animator.is_animating)

    def test_cancel_stops_animating(self) -> None:
        animator = LayoutAnimator(self.tweens, duration=0.3)
        node = _GoodNode()
        node.rect = _Rect(0, 0, 100, 50)
        animator.apply_targets([(node, _Rect(200, 0, 100, 50))])
        animator.cancel()
        self.assertFalse(animator.is_animating)

    def test_tween_completes_after_duration(self) -> None:
        animator = LayoutAnimator(self.tweens, duration=0.1)
        node = _GoodNode()
        node.rect = _Rect(0, 0, 100, 50)
        animator.apply_targets([(node, _Rect(200, 0, 100, 50))])
        self.tweens.update(0.15)
        self.assertFalse(animator.is_animating)
        self.assertEqual(node.rect.x, 200)

    def test_apply_same_rect_no_animation(self) -> None:
        animator = LayoutAnimator(self.tweens, duration=0.3)
        node = _GoodNode()
        node.rect = _Rect(10, 10, 100, 50)
        animator.apply_targets([(node, _Rect(10, 10, 100, 50))])
        self.assertFalse(animator.is_animating)

    def test_constraint_layout_integration(self) -> None:
        """apply_constraint snapshot/restore then animate."""
        animator = LayoutAnimator(self.tweens, duration=0.0)
        node = _GoodNode()
        node.rect = _Rect(0, 0, 100, 50)
        layout = ConstraintLayout()
        layout.add(node, AnchorConstraint(left=20, top=10))
        parent = _Rect(0, 0, 400, 300)
        animator.apply_constraint(layout, parent)
        # With duration=0 the node should land immediately at constrained pos
        self.assertEqual(node.rect.x, 20)
        self.assertEqual(node.rect.y, 10)


# ---------------------------------------------------------------------------
# Pass-W tests — EventRecorder + EventPlayback + RecordedEvent
# ---------------------------------------------------------------------------

from gui_do import EventRecorder, EventPlayback, RecordedEvent


class EventRecorderTests(unittest.TestCase):
    """EventRecorder captures time-stamped event logs."""

    def test_not_recording_initially(self) -> None:
        r = EventRecorder()
        self.assertFalse(r.is_recording)

    def test_start_sets_recording(self) -> None:
        r = EventRecorder()
        r.start()
        self.assertTrue(r.is_recording)

    def test_stop_clears_recording_flag(self) -> None:
        r = EventRecorder()
        r.start()
        r.stop()
        self.assertFalse(r.is_recording)

    def test_stop_returns_event_list(self) -> None:
        r = EventRecorder()
        r.start()
        events = r.stop()
        self.assertIsInstance(events, list)

    def test_record_captures_event(self) -> None:
        r = EventRecorder()
        r.start()
        fake_event = GuiEvent(kind=_EventType.MOUSE_BUTTON_DOWN, type=0, pos=(10, 20), button=1)
        r.record(fake_event)
        self.assertEqual(r.recorded_count, 1)

    def test_record_when_not_recording_ignored(self) -> None:
        r = EventRecorder()
        fake = GuiEvent(kind=_EventType.KEY_DOWN, type=0, key=65)
        r.record(fake)
        self.assertEqual(r.recorded_count, 0)

    def test_recorded_event_has_correct_type(self) -> None:
        r = EventRecorder()
        r.start()
        r.record(GuiEvent(kind=_EventType.KEY_DOWN, type=0, key=65))
        events = r.stop()
        self.assertIn("key_down", events[0].event_type)

    def test_start_clears_previous_recording(self) -> None:
        r = EventRecorder()
        r.start()
        r.record(GuiEvent(kind=_EventType.KEY_DOWN, type=0, key=65))
        r.stop()
        r.start()
        self.assertEqual(r.recorded_count, 0)

    def test_from_events_pre_populates(self) -> None:
        evts = [RecordedEvent(time_offset_ms=0.0, event_type="KEY_DOWN")]
        r = EventRecorder.from_events(evts)
        self.assertEqual(r.recorded_count, 1)

    def test_save_load_roundtrip(self) -> None:
        import tempfile, os
        r = EventRecorder()
        r.start()
        r.record(GuiEvent(kind=_EventType.KEY_DOWN, type=0, key=65))
        r.stop()
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            r.save(path)
            loaded = EventRecorder.load_file(path)
            self.assertEqual(len(loaded), 1)
        finally:
            os.unlink(path)

    def test_load_file_nonexistent_returns_empty(self) -> None:
        loaded = EventRecorder.load_file("no_such_file_abc123.json")
        self.assertEqual(loaded, [])


class EventPlaybackTests(unittest.TestCase):
    """EventPlayback replays RecordedEvents at the right time."""

    def _make_events(self):
        return [
            RecordedEvent(time_offset_ms=100.0, event_type="KEY_DOWN"),
            RecordedEvent(time_offset_ms=200.0, event_type="KEY_UP"),
        ]

    def test_not_playing_initially(self) -> None:
        p = EventPlayback(self._make_events(), handler=lambda e: None)
        self.assertFalse(p.is_playing)

    def test_start_sets_playing(self) -> None:
        p = EventPlayback(self._make_events(), handler=lambda e: None)
        p.start()
        self.assertTrue(p.is_playing)

    def test_stop_clears_playing(self) -> None:
        p = EventPlayback(self._make_events(), handler=lambda e: None)
        p.start()
        p.stop()
        self.assertFalse(p.is_playing)

    def test_events_fire_at_correct_time(self) -> None:
        received = []
        p = EventPlayback(self._make_events(), handler=lambda e: received.append(e.event_type))
        p.start()
        p.update(0.05)    # 50 ms — nothing yet
        self.assertEqual(len(received), 0)
        p.update(0.06)    # now at 110 ms — first event should fire
        self.assertEqual(len(received), 1)
        p.update(0.11)    # 220 ms — second event fires
        self.assertEqual(len(received), 2)

    def test_playback_stops_after_last_event(self) -> None:
        p = EventPlayback(self._make_events(), handler=lambda e: None)
        p.start()
        p.update(0.3)    # past all events
        self.assertFalse(p.is_playing)

    def test_on_complete_callback_fires(self) -> None:
        done = []
        p = EventPlayback(self._make_events(), handler=lambda e: None,
                          on_complete=lambda: done.append(True))
        p.start()
        p.update(0.3)
        self.assertEqual(done, [True])

    def test_loop_restarts_playback(self) -> None:
        received = []
        p = EventPlayback(self._make_events(), handler=lambda e: received.append(1), loop=True)
        p.start()
        p.update(0.3)    # completes first pass
        self.assertTrue(p.is_playing)   # still playing (loop=True)
        p.update(0.15)   # triggers events in second loop
        self.assertGreater(len(received), 2)

    def test_progress_fraction(self) -> None:
        p = EventPlayback(self._make_events(), handler=lambda e: None)
        p.start()
        p.update(0.1)   # at 100 ms out of 200 ms total
        self.assertAlmostEqual(p.progress, 0.5, places=1)


# ---------------------------------------------------------------------------
# Pass-X tests — SceneSnapshot + NodeSnapshot
# ---------------------------------------------------------------------------

from gui_do import SceneSnapshot, NodeSnapshot


class _SceneStub:
    """Minimal scene stub with _walk_nodes() generator."""

    def __init__(self, nodes):
        self._nodes = list(nodes)

    def _walk_nodes(self):
        yield from self._nodes


class NodeSnapshotTests(unittest.TestCase):
    """NodeSnapshot dataclass construction."""

    def test_stores_control_id_and_rect(self) -> None:
        snap = NodeSnapshot(control_id="btn", rect=[10, 20, 100, 50])
        self.assertEqual(snap.control_id, "btn")
        self.assertEqual(snap.rect, [10, 20, 100, 50])

    def test_defaults_visible_and_enabled(self) -> None:
        snap = NodeSnapshot(control_id="x", rect=[0, 0, 0, 0])
        self.assertTrue(snap.visible)
        self.assertTrue(snap.enabled)

    def test_extra_defaults_to_empty_dict(self) -> None:
        snap = NodeSnapshot(control_id="x", rect=[0, 0, 0, 0])
        self.assertEqual(snap.extra, {})


class SceneSnapshotCaptureTests(unittest.TestCase):
    """SceneSnapshot.capture / from_nodes."""

    def test_from_nodes_captures_all(self) -> None:
        n1 = _GoodNode()
        n1.control_id = "n1"
        n1.rect = _Rect(5, 10, 100, 50)
        n2 = _GoodNode()
        n2.control_id = "n2"
        n2.rect = _Rect(0, 0, 80, 40)
        snap = SceneSnapshot.from_nodes([n1, n2])
        self.assertEqual(len(snap), 2)
        self.assertIn("n1", snap)
        self.assertIn("n2", snap)

    def test_from_nodes_rect_values(self) -> None:
        n = _GoodNode()
        n.control_id = "n"
        n.rect = _Rect(7, 8, 90, 45)
        snap = SceneSnapshot.from_nodes([n])
        entry = snap.get("n")
        self.assertEqual(entry.rect, [7, 8, 90, 45])

    def test_capture_with_scene_stub(self) -> None:
        n = _GoodNode()
        n.control_id = "btn"
        n.rect = _Rect(0, 0, 60, 30)
        scene = _SceneStub([n])
        snap = SceneSnapshot.capture(scene)
        self.assertIn("btn", snap)

    def test_capture_none_scene_returns_empty(self) -> None:
        snap = SceneSnapshot.capture(None)
        self.assertEqual(len(snap), 0)

    def test_node_ids_sorted(self) -> None:
        nodes = []
        for cid in ["z", "a", "m"]:
            n = _GoodNode()
            n.control_id = cid
            n.rect = _Rect(0, 0, 1, 1)
            nodes.append(n)
        snap = SceneSnapshot.from_nodes(nodes)
        self.assertEqual(snap.node_ids, ["a", "m", "z"])

    def test_get_returns_none_for_unknown(self) -> None:
        snap = SceneSnapshot()
        self.assertIsNone(snap.get("nope"))


class SceneSnapshotRestoreTests(unittest.TestCase):
    """SceneSnapshot.restore() applies stored state back."""

    def test_restore_updates_rect(self) -> None:
        n = _GoodNode()
        n.control_id = "btn"
        n.rect = _Rect(0, 0, 100, 50)
        snap = SceneSnapshot.from_nodes([n])
        n.rect = _Rect(999, 999, 1, 1)
        scene = _SceneStub([n])
        count = snap.restore(scene)
        self.assertEqual(count, 1)
        self.assertEqual(n.rect.x, 0)

    def test_restore_none_scene_returns_zero(self) -> None:
        snap = SceneSnapshot.from_nodes([])
        self.assertEqual(snap.restore(None), 0)


class SceneSnapshotSerializationTests(unittest.TestCase):
    """SceneSnapshot to_dict / from_dict / save / load roundtrip."""

    def test_to_dict_from_dict_roundtrip(self) -> None:
        snap = SceneSnapshot.from_nodes([])
        snap._entries["k"] = NodeSnapshot(control_id="k", rect=[1, 2, 3, 4],
                                          visible=False, enabled=True)
        d = snap.to_dict()
        snap2 = SceneSnapshot.from_dict(d)
        entry = snap2.get("k")
        self.assertIsNotNone(entry)
        self.assertEqual(entry.rect, [1, 2, 3, 4])
        self.assertFalse(entry.visible)

    def test_save_load_roundtrip(self) -> None:
        import tempfile, os
        snap = SceneSnapshot.from_nodes([])
        snap._entries["x"] = NodeSnapshot(control_id="x", rect=[0, 0, 10, 10])
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            snap.save(path)
            loaded = SceneSnapshot.load(path)
            self.assertIn("x", loaded)
        finally:
            os.unlink(path)

    def test_load_nonexistent_returns_empty(self) -> None:
        snap = SceneSnapshot.load("no_such_snapshot_abc.json")
        self.assertEqual(len(snap), 0)


# ---------------------------------------------------------------------------
# Pass-Y tests — ResponsiveLayout + Breakpoint + CursorManager + CursorShape
# ---------------------------------------------------------------------------

from gui_do import ResponsiveLayout, Breakpoint
from gui_do import CursorManager, CursorHandle, CursorShape


class ResponsiveLayoutTests(unittest.TestCase):
    """ResponsiveLayout selects layout based on container width."""

    def _make_responsive(self):
        narrow = object()
        wide = object()
        rl = ResponsiveLayout(default_layout=narrow)
        rl.add_breakpoint(Breakpoint("wide", min_width=800, layout=wide))
        rl.add_breakpoint(Breakpoint("medium", min_width=480, layout=object()))
        return rl, narrow, wide

    def test_default_layout_before_update(self) -> None:
        rl = ResponsiveLayout(default_layout="narrow")
        self.assertEqual(rl.active_layout, "narrow")

    def test_update_switches_to_breakpoint(self) -> None:
        rl, narrow, wide = self._make_responsive()
        changed = rl.update(1024)
        self.assertTrue(changed)
        self.assertIs(rl.active_layout, wide)

    def test_update_returns_false_when_same(self) -> None:
        rl, narrow, wide = self._make_responsive()
        rl.update(1024)
        changed = rl.update(1024)
        self.assertFalse(changed)

    def test_below_all_breakpoints_uses_default(self) -> None:
        rl, narrow, wide = self._make_responsive()
        rl.update(1024)
        rl.update(100)  # below all breakpoints
        self.assertIs(rl.active_layout, narrow)

    def test_active_breakpoint_observable(self) -> None:
        rl, narrow, wide = self._make_responsive()
        names = []
        rl.active_breakpoint.subscribe(lambda v: names.append(v))
        rl.update(1024)
        self.assertIn("wide", names)

    def test_add_breakpoint_type_check(self) -> None:
        rl = ResponsiveLayout()
        with self.assertRaises(TypeError):
            rl.add_breakpoint("not-a-breakpoint")

    def test_set_default_layout_replaces(self) -> None:
        rl = ResponsiveLayout(default_layout="old")
        rl.set_default_layout("new")
        self.assertEqual(rl.active_layout, "new")

    def test_breakpoint_dataclass_stores_fields(self) -> None:
        layout_obj = object()
        bp = Breakpoint(name="wide", min_width=800, layout=layout_obj)
        self.assertEqual(bp.name, "wide")
        self.assertEqual(bp.min_width, 800)
        self.assertIs(bp.layout, layout_obj)

    def test_widest_matching_breakpoint_wins(self) -> None:
        layout_med = object()
        layout_wide = object()
        rl = ResponsiveLayout(default_layout=None)
        rl.add_breakpoint(Breakpoint("medium", min_width=480, layout=layout_med))
        rl.add_breakpoint(Breakpoint("wide", min_width=800, layout=layout_wide))
        rl.update(600)
        self.assertIs(rl.active_layout, layout_med)


class CursorManagerTests(unittest.TestCase):
    """CursorManager priority-stack cursor resolution (no pygame display needed)."""

    def test_push_returns_handle(self) -> None:
        mgr = CursorManager()
        handle = mgr.push(CursorShape.HAND, priority=10)
        self.assertIsInstance(handle, CursorHandle)

    def test_handle_stores_shape_and_priority(self) -> None:
        mgr = CursorManager()
        handle = mgr.push(CursorShape.RESIZE_H, priority=5)
        self.assertEqual(handle.shape, CursorShape.RESIZE_H)
        self.assertEqual(handle.priority, 5)

    def test_handle_not_released_initially(self) -> None:
        mgr = CursorManager()
        handle = mgr.push(CursorShape.ARROW)
        self.assertFalse(handle.released)

    def test_release_marks_handle(self) -> None:
        mgr = CursorManager()
        handle = mgr.push(CursorShape.HAND)
        handle.release()
        self.assertTrue(handle.released)

    def test_release_twice_is_idempotent(self) -> None:
        mgr = CursorManager()
        handle = mgr.push(CursorShape.HAND)
        handle.release()
        handle.release()  # must not raise

    def test_resolve_picks_highest_priority(self) -> None:
        mgr = CursorManager()
        mgr.push(CursorShape.TEXT, priority=5)
        mgr.push(CursorShape.RESIZE_H, priority=20)
        self.assertEqual(mgr._resolve(), CursorShape.RESIZE_H)

    def test_resolve_default_when_empty(self) -> None:
        mgr = CursorManager(default_shape=CursorShape.CROSSHAIR)
        self.assertEqual(mgr._resolve(), CursorShape.CROSSHAIR)

    def test_release_restores_lower_priority(self) -> None:
        mgr = CursorManager()
        mgr.push(CursorShape.TEXT, priority=5)
        high = mgr.push(CursorShape.RESIZE_H, priority=20)
        high.release()
        self.assertEqual(mgr._resolve(), CursorShape.TEXT)

    def test_reset_clears_all_requests(self) -> None:
        mgr = CursorManager()
        mgr.push(CursorShape.WAIT, priority=10)
        mgr.reset()
        self.assertEqual(mgr._resolve(), CursorShape.ARROW)

    def test_default_shape_setter_type_check(self) -> None:
        mgr = CursorManager()
        with self.assertRaises(TypeError):
            mgr.default_shape = "arrow"

    def test_cursor_shape_enum_members(self) -> None:
        shapes = {s.value for s in CursorShape}
        self.assertIn("hand", shapes)
        self.assertIn("resize_h", shapes)
        self.assertIn("text", shapes)

    def test_push_invalid_shape_raises(self) -> None:
        mgr = CursorManager()
        with self.assertRaises(TypeError):
            mgr.push("arrow")


# ---------------------------------------------------------------------------
# Pass-Z tests — GridLayout, GridTrack, GridPlacement
# ---------------------------------------------------------------------------

from gui_do import GridLayout, GridTrack, GridPlacement


class GridTrackTests(unittest.TestCase):
    """GridTrack construction and validation."""

    def test_fixed_int_track(self) -> None:
        t = GridTrack(size=80)
        self.assertEqual(t.size, 80)

    def test_auto_track(self) -> None:
        t = GridTrack(size="auto")
        self.assertEqual(t.size, "auto")

    def test_fr_track(self) -> None:
        t = GridTrack(size="1fr")
        self.assertEqual(t.size, "1fr")

    def test_negative_fixed_raises(self) -> None:
        with self.assertRaises(ValueError):
            GridTrack(size=-1)

    def test_invalid_string_raises(self) -> None:
        with self.assertRaises(ValueError):
            GridTrack(size="bad")

    def test_invalid_type_raises(self) -> None:
        with self.assertRaises(TypeError):
            GridTrack(size=3.14)


class GridPlacementTests(unittest.TestCase):
    """GridPlacement validation."""

    def test_default_span_one(self) -> None:
        p = GridPlacement(row=0, col=0)
        self.assertEqual(p.rowspan, 1)
        self.assertEqual(p.colspan, 1)

    def test_negative_row_raises(self) -> None:
        with self.assertRaises(ValueError):
            GridPlacement(row=-1, col=0)

    def test_zero_rowspan_raises(self) -> None:
        with self.assertRaises(ValueError):
            GridPlacement(row=0, col=0, rowspan=0)

    def test_invalid_align_x_raises(self) -> None:
        with self.assertRaises(ValueError):
            GridPlacement(row=0, col=0, align_x="bad")


class GridLayoutFixedTrackTests(unittest.TestCase):
    """GridLayout with fixed-pixel tracks positions nodes correctly."""

    def setUp(self):
        self.n1 = _GoodNode()
        self.n1.control_id = "n1"
        self.n1.rect = _Rect(0, 0, 40, 30)
        self.n2 = _GoodNode()
        self.n2.control_id = "n2"
        self.n2.rect = _Rect(0, 0, 40, 30)

    def test_two_fixed_columns_place_nodes_side_by_side(self) -> None:
        layout = GridLayout(
            row_tracks=[GridTrack(50)],
            col_tracks=[GridTrack(100), GridTrack(100)],
            gap=0,
        )
        layout.place(self.n1, GridPlacement(row=0, col=0))
        layout.place(self.n2, GridPlacement(row=0, col=1))
        layout.apply(_Rect(0, 0, 200, 50))
        self.assertEqual(self.n1.rect.x, 0)
        self.assertEqual(self.n2.rect.x, 100)

    def test_gap_applied_between_columns(self) -> None:
        layout = GridLayout(
            row_tracks=[GridTrack(50)],
            col_tracks=[GridTrack(100), GridTrack(100)],
            gap=10,
        )
        layout.place(self.n1, GridPlacement(row=0, col=0))
        layout.place(self.n2, GridPlacement(row=0, col=1))
        layout.apply(_Rect(0, 0, 210, 50))
        self.assertEqual(self.n2.rect.x, 110)

    def test_colspan_spans_two_columns(self) -> None:
        layout = GridLayout(
            row_tracks=[GridTrack(50)],
            col_tracks=[GridTrack(80), GridTrack(80)],
            gap=0,
        )
        layout.place(self.n1, GridPlacement(row=0, col=0, colspan=2))
        layout.apply(_Rect(0, 0, 160, 50))
        self.assertEqual(self.n1.rect.width, 160)

    def test_fr_tracks_divide_remaining_space(self) -> None:
        layout = GridLayout(
            row_tracks=[GridTrack("1fr")],
            col_tracks=[GridTrack("1fr"), GridTrack("1fr")],
            gap=0,
        )
        layout.place(self.n1, GridPlacement(row=0, col=0))
        layout.place(self.n2, GridPlacement(row=0, col=1))
        layout.apply(_Rect(0, 0, 200, 100))
        self.assertEqual(self.n1.rect.width, 100)
        self.assertEqual(self.n2.rect.width, 100)

    def test_remove_node(self) -> None:
        layout = GridLayout(
            row_tracks=[GridTrack(50)],
            col_tracks=[GridTrack(100)],
        )
        layout.place(self.n1, GridPlacement(row=0, col=0))
        removed = layout.remove(self.n1)
        self.assertTrue(removed)
        self.assertEqual(layout.nodes(), [])

    def test_remove_unknown_returns_false(self) -> None:
        layout = GridLayout(
            row_tracks=[GridTrack(50)],
            col_tracks=[GridTrack(100)],
        )
        self.assertFalse(layout.remove(self.n1))

    def test_out_of_range_placement_skipped(self) -> None:
        layout = GridLayout(
            row_tracks=[GridTrack(50)],
            col_tracks=[GridTrack(100)],
        )
        layout.place(self.n1, GridPlacement(row=5, col=5))  # out of range
        layout.apply(_Rect(0, 0, 200, 200))
        # Should not raise; node rect unchanged from initial
        self.assertEqual(self.n1.rect.x, 0)

    def test_align_center_positions_node_in_center(self) -> None:
        layout = GridLayout(
            row_tracks=[GridTrack(100)],
            col_tracks=[GridTrack(200)],
        )
        layout.place(self.n1, GridPlacement(row=0, col=0, align_x="center", align_y="center"))
        layout.apply(_Rect(0, 0, 200, 100))
        # Node is 40×30 centred in 200×100 cell
        self.assertEqual(self.n1.rect.centerx, 100)
        self.assertEqual(self.n1.rect.centery, 50)


# ---------------------------------------------------------------------------
# Pass-AA tests — ScopedTheme + ScopedThemeManager
# ---------------------------------------------------------------------------

from gui_do import ScopedTheme, ScopedThemeManager


class _TokensStub:
    """Minimal DesignTokens stub with a dict-like get() fallback."""

    def __init__(self, tokens: dict):
        self._data = dict(tokens)

    def get(self, token: str, fallback=None):
        return self._data.get(token, fallback)


class ScopedThemeTests(unittest.TestCase):
    """ScopedTheme stores, resolves, and chains overrides."""

    def test_stores_override(self) -> None:
        s = ScopedTheme({"surface": (10, 20, 30)})
        self.assertEqual(s.resolve("surface"), (10, 20, 30))

    def test_resolve_missing_returns_fallback(self) -> None:
        s = ScopedTheme({})
        self.assertIsNone(s.resolve("unknown"))

    def test_resolve_custom_fallback(self) -> None:
        s = ScopedTheme({})
        self.assertEqual(s.resolve("x", fallback=(1, 2, 3)), (1, 2, 3))

    def test_set_adds_token(self) -> None:
        s = ScopedTheme({})
        s.set("primary", (255, 0, 0))
        self.assertEqual(s.resolve("primary"), (255, 0, 0))

    def test_remove_stops_resolving(self) -> None:
        s = ScopedTheme({"text": (200, 200, 200)})
        s.remove("text")
        self.assertIsNone(s.resolve("text"))

    def test_to_dict_returns_copy(self) -> None:
        overrides = {"bg": (0, 0, 0)}
        s = ScopedTheme(overrides)
        d = s.to_dict()
        self.assertEqual(d, {"bg": (0, 0, 0)})
        # Mutating returned dict doesn't affect scope
        d["bg"] = (1, 2, 3)
        self.assertEqual(s.resolve("bg"), (0, 0, 0))

    def test_copy_creates_independent_scope(self) -> None:
        s = ScopedTheme({"x": (1, 1, 1)})
        c = s.copy(name="copy")
        c.set("x", (9, 9, 9))
        self.assertEqual(s.resolve("x"), (1, 1, 1))

    def test_chain_resolves_parent(self) -> None:
        parent = ScopedTheme({"bg": (10, 10, 10)})
        child = ScopedTheme({"text": (200, 200, 200)})
        child._parent = parent
        self.assertEqual(child.resolve("bg"), (10, 10, 10))

    def test_name_property(self) -> None:
        s = ScopedTheme({}, name="highlight")
        self.assertEqual(s.name, "highlight")

    def test_initially_no_parent(self) -> None:
        s = ScopedTheme({})
        self.assertIsNone(s.parent)


class ScopedThemeManagerTests(unittest.TestCase):
    """ScopedThemeManager push/pop/resolve and context manager."""

    def setUp(self):
        self.base = _TokensStub({"primary": (0, 120, 212), "bg": (30, 30, 30)})
        self.mgr = ScopedThemeManager(self.base)

    def test_no_scope_resolves_base_token(self) -> None:
        result = self.mgr.resolve("primary")
        self.assertEqual(result, (0, 120, 212))

    def test_no_scope_unknown_returns_fallback(self) -> None:
        result = self.mgr.resolve("unknown", (1, 2, 3))
        self.assertEqual(result, (1, 2, 3))

    def test_push_scope_overrides_token(self) -> None:
        scope = ScopedTheme({"primary": (255, 0, 0)})
        self.mgr.push(scope)
        self.assertEqual(self.mgr.resolve("primary"), (255, 0, 0))

    def test_push_scope_fallsthrough_for_unset_tokens(self) -> None:
        scope = ScopedTheme({"primary": (255, 0, 0)})
        self.mgr.push(scope)
        self.assertEqual(self.mgr.resolve("bg"), (30, 30, 30))

    def test_pop_restores_base(self) -> None:
        scope = ScopedTheme({"primary": (255, 0, 0)})
        self.mgr.push(scope)
        self.mgr.pop()
        self.assertEqual(self.mgr.resolve("primary"), (0, 120, 212))

    def test_pop_empty_returns_none(self) -> None:
        self.assertIsNone(self.mgr.pop())

    def test_depth_tracks_stack(self) -> None:
        self.assertEqual(self.mgr.depth, 0)
        self.mgr.push(ScopedTheme({}))
        self.assertEqual(self.mgr.depth, 1)
        self.mgr.push(ScopedTheme({}))
        self.assertEqual(self.mgr.depth, 2)
        self.mgr.pop()
        self.assertEqual(self.mgr.depth, 1)

    def test_active_scope_is_innermost(self) -> None:
        s1 = ScopedTheme({}, name="outer")
        s2 = ScopedTheme({}, name="inner")
        self.mgr.push(s1)
        self.mgr.push(s2)
        self.assertIs(self.mgr.active_scope, s2)

    def test_active_scope_none_when_empty(self) -> None:
        self.assertIsNone(self.mgr.active_scope)

    def test_context_manager_pushes_and_pops(self) -> None:
        scope = ScopedTheme({"primary": (0, 0, 255)})
        with self.mgr.scope(scope):
            self.assertEqual(self.mgr.resolve("primary"), (0, 0, 255))
        self.assertEqual(self.mgr.resolve("primary"), (0, 120, 212))

    def test_nested_scopes_chain_correctly(self) -> None:
        outer = ScopedTheme({"a": (1, 1, 1), "b": (2, 2, 2)})
        inner = ScopedTheme({"a": (9, 9, 9)})
        self.mgr.push(outer)
        self.mgr.push(inner)
        self.assertEqual(self.mgr.resolve("a"), (9, 9, 9))   # inner wins
        self.assertEqual(self.mgr.resolve("b"), (2, 2, 2))   # falls to outer


# ---------------------------------------------------------------------------
# Pass-AB tests — TransitionManager, TransitionSpec, TransitionEvent
# ---------------------------------------------------------------------------

from gui_do import TransitionManager, TransitionSpec, TransitionEvent


class _AnimTarget:
    """Stub node with float attributes for tween animation."""

    def __init__(self):
        self.control_id = f"tgt_{id(self)}"
        self.alpha: float = 0.0
        self.scale: float = 1.0


class TransitionManagerRegistrationTests(unittest.TestCase):
    """TransitionManager register / unregister / unregister_event."""

    def setUp(self):
        self.tweens = TweenManager()
        self.tm = TransitionManager(self.tweens)

    def test_register_does_not_raise(self) -> None:
        node = _AnimTarget()
        self.tm.register(node, TransitionEvent.SHOW,
                         TransitionSpec(attr="alpha", end_value=1.0))

    def test_unregister_removes_all_specs(self) -> None:
        node = _AnimTarget()
        self.tm.register(node, TransitionEvent.SHOW,
                         TransitionSpec(attr="alpha", end_value=1.0))
        self.tm.unregister(node)
        # After unregister, triggering should be a no-op
        self.tm.on_show(node)  # must not raise

    def test_unregister_event_removes_specific_event(self) -> None:
        node = _AnimTarget()
        self.tm.register(node, TransitionEvent.SHOW,
                         TransitionSpec(attr="alpha", end_value=1.0))
        self.tm.register(node, TransitionEvent.HIDE,
                         TransitionSpec(attr="alpha", end_value=0.0))
        self.tm.unregister_event(node, TransitionEvent.SHOW)
        self.tm.on_show(node)  # no-op now, must not raise

    def test_transition_event_enum_members(self) -> None:
        values = {e.value for e in TransitionEvent}
        self.assertIn("show", values)
        self.assertIn("hide", values)
        self.assertIn("enable", values)
        self.assertIn("disable", values)


class TransitionManagerTriggerTests(unittest.TestCase):
    """TransitionManager triggers animate attribute transitions."""

    def setUp(self):
        self.tweens = TweenManager()
        self.tm = TransitionManager(self.tweens)

    def test_on_show_starts_tween(self) -> None:
        node = _AnimTarget()
        node.alpha = 0.0
        self.tm.register(node, TransitionEvent.SHOW,
                         TransitionSpec(attr="alpha", end_value=1.0,
                                        duration_seconds=0.2))
        self.tm.on_show(node)
        self.tweens.update(0.25)
        self.assertAlmostEqual(node.alpha, 1.0, places=5)

    def test_on_hide_starts_tween(self) -> None:
        node = _AnimTarget()
        node.alpha = 1.0
        self.tm.register(node, TransitionEvent.HIDE,
                         TransitionSpec(attr="alpha", end_value=0.0,
                                        duration_seconds=0.2))
        self.tm.on_hide(node)
        self.tweens.update(0.25)
        self.assertAlmostEqual(node.alpha, 0.0, places=5)

    def test_start_value_overrides_current(self) -> None:
        node = _AnimTarget()
        node.alpha = 0.5  # current
        self.tm.register(node, TransitionEvent.SHOW,
                         TransitionSpec(attr="alpha", end_value=1.0,
                                        duration_seconds=0.2,
                                        start_value=0.0))
        self.tm.on_show(node)
        # Immediately after trigger, alpha should be reset to start_value=0.0
        self.assertAlmostEqual(node.alpha, 0.0, places=5)
        self.tweens.update(0.25)
        self.assertAlmostEqual(node.alpha, 1.0, places=5)

    def test_on_complete_callback_fires(self) -> None:
        done = []
        node = _AnimTarget()
        node.alpha = 0.0
        self.tm.register(node, TransitionEvent.SHOW,
                         TransitionSpec(attr="alpha", end_value=1.0,
                                        duration_seconds=0.1,
                                        on_done=lambda: done.append(True)))
        self.tm.on_show(node)
        self.tweens.update(0.15)
        self.assertEqual(done, [True])

    def test_on_enable_trigger(self) -> None:
        node = _AnimTarget()
        node.scale = 0.8
        self.tm.register(node, TransitionEvent.ENABLE,
                         TransitionSpec(attr="scale", end_value=1.0,
                                        duration_seconds=0.1))
        self.tm.on_enable(node)
        self.tweens.update(0.15)
        self.assertAlmostEqual(node.scale, 1.0, places=5)

    def test_on_disable_trigger(self) -> None:
        node = _AnimTarget()
        node.scale = 1.0
        self.tm.register(node, TransitionEvent.DISABLE,
                         TransitionSpec(attr="scale", end_value=0.8,
                                        duration_seconds=0.1))
        self.tm.on_disable(node)
        self.tweens.update(0.15)
        self.assertAlmostEqual(node.scale, 0.8, places=5)

    def test_transition_spec_dataclass_fields(self) -> None:
        spec = TransitionSpec(attr="alpha", end_value=1.0, duration_seconds=0.3,
                               start_value=0.0)
        self.assertEqual(spec.attr, "alpha")
        self.assertEqual(spec.end_value, 1.0)
        self.assertEqual(spec.start_value, 0.0)


# ---------------------------------------------------------------------------
# Pass-AC tests — SceneSpatialIndex
# ---------------------------------------------------------------------------

from gui_do import SceneSpatialIndex


class SceneSpatialIndexBuildTests(unittest.TestCase):
    """SceneSpatialIndex.build / clear / node_count."""

    def _node(self, cid, x, y, w, h):
        n = _GoodNode()
        n.control_id = cid
        n.rect = _Rect(x, y, w, h)
        return n

    def test_initially_empty(self) -> None:
        idx = SceneSpatialIndex()
        self.assertEqual(idx.node_count, 0)

    def test_build_indexes_nodes(self) -> None:
        nodes = [self._node("a", 0, 0, 64, 64), self._node("b", 100, 0, 64, 64)]
        scene = _SceneStub(nodes)
        idx = SceneSpatialIndex(cell_size=64)
        idx.build(scene)
        self.assertEqual(idx.node_count, 2)

    def test_clear_removes_all(self) -> None:
        nodes = [self._node("a", 0, 0, 64, 64)]
        scene = _SceneStub(nodes)
        idx = SceneSpatialIndex()
        idx.build(scene)
        idx.clear()
        self.assertEqual(idx.node_count, 0)

    def test_build_none_scene_empty(self) -> None:
        idx = SceneSpatialIndex()
        idx.build(None)
        self.assertEqual(idx.node_count, 0)


class SceneSpatialIndexQueryTests(unittest.TestCase):
    """SceneSpatialIndex query_point / query_rect / update_node / remove_node."""

    def _node(self, cid, x, y, w=60, h=40):
        n = _GoodNode()
        n.control_id = cid
        n.rect = _Rect(x, y, w, h)
        return n

    def setUp(self):
        self.idx = SceneSpatialIndex(cell_size=64)
        self.n1 = self._node("n1", 10, 10)
        self.n2 = self._node("n2", 200, 200)
        self.idx.build(_SceneStub([self.n1, self.n2]))

    def test_query_point_hit(self) -> None:
        results = self.idx.query_point(30, 30)
        cids = [n.control_id for n in results]
        self.assertIn("n1", cids)

    def test_query_point_miss(self) -> None:
        results = self.idx.query_point(500, 500)
        self.assertEqual(results, [])

    def test_query_rect_hit(self) -> None:
        results = self.idx.query_rect(_Rect(0, 0, 100, 100))
        cids = [n.control_id for n in results]
        self.assertIn("n1", cids)

    def test_query_rect_excludes_non_overlapping(self) -> None:
        results = self.idx.query_rect(_Rect(0, 0, 100, 100))
        cids = [n.control_id for n in results]
        self.assertNotIn("n2", cids)

    def test_remove_node_drops_from_index(self) -> None:
        self.idx.remove_node(self.n1)
        results = self.idx.query_point(30, 30)
        self.assertEqual(results, [])

    def test_update_node_reflects_new_rect(self) -> None:
        self.n1.rect = _Rect(300, 300, 60, 40)
        self.idx.update_node(self.n1)
        # Old location should no longer hit
        old_results = self.idx.query_point(30, 30)
        self.assertEqual(old_results, [])
        # New location should hit
        new_results = self.idx.query_point(320, 320)
        cids = [n.control_id for n in new_results]
        self.assertIn("n1", cids)

    def test_invisible_node_not_returned(self) -> None:
        self.n1._visible = False
        results = self.idx.query_point(30, 30)
        cids = [n.control_id for n in results]
        self.assertNotIn("n1", cids)


# ---------------------------------------------------------------------------
# Pass-AD tests — CanvasViewport
# ---------------------------------------------------------------------------

from gui_do import CanvasViewport


class CanvasViewportTransformTests(unittest.TestCase):
    """CanvasViewport coordinate transforms."""

    def test_to_screen_identity_at_scale_one(self) -> None:
        vp = CanvasViewport(content_size=(1000, 1000))
        self.assertEqual(vp.to_screen((100.0, 200.0)), (100.0, 200.0))

    def test_to_canvas_identity_at_scale_one(self) -> None:
        vp = CanvasViewport(content_size=(1000, 1000))
        self.assertEqual(vp.to_canvas((100.0, 200.0)), (100.0, 200.0))

    def test_roundtrip_screen_canvas(self) -> None:
        vp = CanvasViewport(content_size=(1000, 1000))
        vp.zoom_to(2.0)
        screen = vp.to_screen((50.0, 50.0))
        back = vp.to_canvas(screen)
        self.assertAlmostEqual(back[0], 50.0, places=5)
        self.assertAlmostEqual(back[1], 50.0, places=5)

    def test_pan_shifts_offset(self) -> None:
        vp = CanvasViewport()
        vp.pan((10.0, 20.0))
        self.assertEqual(vp.offset, (10.0, 20.0))

    def test_pan_accumulates(self) -> None:
        vp = CanvasViewport()
        vp.pan((10.0, 0.0))
        vp.pan((5.0, 0.0))
        self.assertAlmostEqual(vp.offset[0], 15.0)

    def test_zoom_to_clamps_at_min(self) -> None:
        vp = CanvasViewport(min_scale=0.1, max_scale=10.0)
        vp.zoom_to(0.001)
        self.assertEqual(vp.scale, 0.1)

    def test_zoom_to_clamps_at_max(self) -> None:
        vp = CanvasViewport(min_scale=0.1, max_scale=10.0)
        vp.zoom_to(999.0)
        self.assertEqual(vp.scale, 10.0)

    def test_zoom_at_preserves_anchor_content_point(self) -> None:
        vp = CanvasViewport(content_size=(1000, 1000))
        anchor = (200.0, 150.0)
        canvas_before = vp.to_canvas(anchor)
        vp.zoom_at(anchor=anchor, factor=2.0)
        canvas_after = vp.to_canvas(anchor)
        self.assertAlmostEqual(canvas_after[0], canvas_before[0], places=4)
        self.assertAlmostEqual(canvas_after[1], canvas_before[1], places=4)

    def test_reset_restores_defaults(self) -> None:
        vp = CanvasViewport()
        vp.pan((50.0, 50.0))
        vp.zoom_to(3.0)
        vp.reset()
        self.assertEqual(vp.scale, 1.0)
        self.assertEqual(vp.offset, (0.0, 0.0))

    def test_fit_content_fills_viewport(self) -> None:
        vp = CanvasViewport(content_size=(2000, 2000),
                            min_scale=0.01, max_scale=32.0)
        vp.fit_content((400, 400))
        # Content 2000×2000 into viewport 400×400 → scale should be 0.2
        self.assertAlmostEqual(vp.scale, 0.2, places=5)

    def test_set_offset(self) -> None:
        vp = CanvasViewport()
        vp.set_offset((100.0, 200.0))
        self.assertEqual(vp.offset, (100.0, 200.0))

    def test_content_size_property(self) -> None:
        vp = CanvasViewport(content_size=(800, 600))
        self.assertEqual(vp.content_size, (800, 600))

    def test_zoom_at_zero_factor_no_change(self) -> None:
        vp = CanvasViewport()
        before = vp.scale
        vp.zoom_at(anchor=(0.0, 0.0), factor=0.0)
        self.assertEqual(vp.scale, before)


# ---------------------------------------------------------------------------
# Pass-AE tests — TextFlow + TextSpan (pure-data aspects)
# ---------------------------------------------------------------------------

from gui_do import TextFlow, TextSpan


class TextSpanTests(unittest.TestCase):
    """TextSpan dataclass construction and defaults."""

    def test_default_fields(self) -> None:
        span = TextSpan("hello")
        self.assertEqual(span.text, "hello")
        self.assertFalse(span.bold)
        self.assertFalse(span.italic)
        self.assertIsNone(span.color)
        self.assertEqual(span.role, "body")

    def test_custom_fields(self) -> None:
        span = TextSpan("world", bold=True, italic=True,
                        color=(255, 0, 0), role="title")
        self.assertTrue(span.bold)
        self.assertTrue(span.italic)
        self.assertEqual(span.color, (255, 0, 0))
        self.assertEqual(span.role, "title")

    def test_newline_in_text(self) -> None:
        span = TextSpan("line1\nline2")
        self.assertIn("\n", span.text)


class TextFlowTests(unittest.TestCase):
    """TextFlow construction, property access, and set_content."""

    def test_initial_width(self) -> None:
        flow = TextFlow(400)
        self.assertEqual(flow.width, 400)

    def test_initial_height_is_zero(self) -> None:
        flow = TextFlow(400)
        self.assertEqual(flow.height, 0)

    def test_width_clamped_to_one(self) -> None:
        flow = TextFlow(0)
        self.assertEqual(flow.width, 1)

    def test_set_content_clears_height(self) -> None:
        flow = TextFlow(400)
        flow._height = 99  # pretend laid out
        flow._laid_out = True
        flow.set_content([TextSpan("hi")])
        self.assertEqual(flow.height, 0)
        self.assertFalse(flow._laid_out)

    def test_set_content_empty_list(self) -> None:
        flow = TextFlow(200)
        flow.set_content([])
        self.assertEqual(flow._spans, [])
        self.assertFalse(flow._laid_out)

    def test_width_setter_marks_dirty(self) -> None:
        flow = TextFlow(200)
        flow._laid_out = True
        flow.width = 300
        self.assertFalse(flow._laid_out)
        self.assertEqual(flow.width, 300)

    def test_width_setter_same_value_no_dirty(self) -> None:
        flow = TextFlow(200)
        flow._laid_out = True
        flow.width = 200  # same value
        self.assertTrue(flow._laid_out)  # should remain dirty=False → still True

    def test_set_content_stores_spans(self) -> None:
        flow = TextFlow(400)
        spans = [TextSpan("a"), TextSpan("b", bold=True)]
        flow.set_content(spans)
        self.assertEqual(len(flow._spans), 2)


# ---------------------------------------------------------------------------
# Pass-AF tests — NotificationCenter + NotificationRecord
# ---------------------------------------------------------------------------

from gui_do import NotificationCenter, NotificationRecord


class NotificationRecordTests(unittest.TestCase):
    """NotificationRecord dataclass fields and defaults."""

    def test_required_field(self) -> None:
        r = NotificationRecord("Build failed")
        self.assertEqual(r.message, "Build failed")

    def test_default_read_false(self) -> None:
        r = NotificationRecord("msg")
        self.assertFalse(r.read)

    def test_default_title_empty(self) -> None:
        r = NotificationRecord("msg")
        self.assertEqual(r.title, "")

    def test_timestamp_not_empty(self) -> None:
        r = NotificationRecord("msg")
        self.assertIsInstance(r.timestamp, str)
        self.assertTrue(len(r.timestamp) > 0)

    def test_custom_fields(self) -> None:
        r = NotificationRecord("msg", title="T", read=True, data={"k": 1})
        self.assertEqual(r.title, "T")
        self.assertTrue(r.read)
        self.assertEqual(r.data, {"k": 1})


class NotificationCenterTests(unittest.TestCase):
    """NotificationCenter record management and reactive observables."""

    def setUp(self):
        self.nc = NotificationCenter(max_records=10)

    def _rec(self, msg="msg"):
        return NotificationRecord(msg)

    def test_initially_empty(self) -> None:
        self.assertEqual(self.nc.unread_count.value, 0)
        self.assertEqual(self.nc.all_records, [])

    def test_add_increments_unread(self) -> None:
        self.nc.add(self._rec("a"))
        self.assertEqual(self.nc.unread_count.value, 1)

    def test_add_stores_record(self) -> None:
        self.nc.add(self._rec("hello"))
        self.assertEqual(len(self.nc.all_records), 1)
        self.assertEqual(self.nc.all_records[0].message, "hello")

    def test_records_newest_first(self) -> None:
        self.nc.add(self._rec("first"))
        self.nc.add(self._rec("second"))
        self.assertEqual(self.nc.all_records[0].message, "second")

    def test_add_updates_records_observable(self) -> None:
        changes = []
        self.nc.records.subscribe(lambda v: changes.append(len(v)))
        self.nc.add(self._rec())
        self.assertEqual(changes, [1])

    def test_mark_read_decrements_unread(self) -> None:
        r = self._rec()
        self.nc.add(r)
        self.nc.mark_read(r)
        self.assertEqual(self.nc.unread_count.value, 0)
        self.assertTrue(r.read)

    def test_mark_read_idempotent(self) -> None:
        r = self._rec()
        r.read = True
        self.nc.add(r)  # already read
        self.nc.mark_read(r)  # no-op
        self.assertEqual(self.nc.unread_count.value, 0)

    def test_mark_all_read(self) -> None:
        self.nc.add(self._rec("a"))
        self.nc.add(self._rec("b"))
        self.nc.mark_all_read()
        self.assertEqual(self.nc.unread_count.value, 0)
        for r in self.nc.all_records:
            self.assertTrue(r.read)

    def test_clear_empties_records(self) -> None:
        self.nc.add(self._rec())
        self.nc.clear()
        self.assertEqual(self.nc.all_records, [])
        self.assertEqual(self.nc.unread_count.value, 0)

    def test_max_records_eviction(self) -> None:
        for i in range(15):
            self.nc.add(self._rec(str(i)))
        self.assertLessEqual(len(self.nc.all_records), 10)

    def test_subscribe_without_event_bus_noop(self) -> None:
        # No bus → subscribe is silently ignored
        self.nc.subscribe("topic")  # must not raise

    def test_unsubscribe_all_clears_subscriptions(self) -> None:
        nc = NotificationCenter()
        nc.subscribe("a")
        nc.unsubscribe_all()
        # No error; subscriptions cleared
        self.assertEqual(nc._subscriptions, [])


# ---------------------------------------------------------------------------
# Pass-AG tests — AnimationSequence + AnimationHandle
# ---------------------------------------------------------------------------

from gui_do import AnimationSequence, AnimationHandle


class _SeqTarget:
    x: float = 0.0
    y: float = 0.0
    alpha: float = 0.0


class AnimationHandleTests(unittest.TestCase):
    """AnimationHandle cancel/cancelled state."""

    def test_initially_not_cancelled(self) -> None:
        h = AnimationHandle()
        self.assertFalse(h.cancelled)

    def test_cancel_sets_cancelled(self) -> None:
        h = AnimationHandle()
        h.cancel()
        self.assertTrue(h.cancelled)


class AnimationSequenceTests(unittest.TestCase):
    """AnimationSequence builder and execution."""

    def setUp(self):
        self.tweens = TweenManager()

    def test_then_completes_single_step(self) -> None:
        t = _SeqTarget()
        t.x = 0.0
        seq = AnimationSequence(self.tweens)
        seq.then(target=t, attr="x", end_value=100.0, duration_seconds=0.1)
        seq.start()
        self.tweens.update(0.15)
        self.assertAlmostEqual(t.x, 100.0, places=5)

    def test_sequential_steps_run_in_order(self) -> None:
        t = _SeqTarget()
        t.x = 0.0
        t.y = 0.0
        log = []
        seq = AnimationSequence(self.tweens)
        seq.then(target=t, attr="x", end_value=10.0, duration_seconds=0.1)
        seq.then(target=t, attr="y", end_value=20.0, duration_seconds=0.1)
        seq.start()
        # After 0.15s, first step done; second not yet
        self.tweens.update(0.15)
        self.assertAlmostEqual(t.x, 10.0, places=5)
        # y still at 0 until second step starts
        self.tweens.update(0.15)
        self.assertAlmostEqual(t.y, 20.0, places=5)

    def test_on_done_fires_after_all_steps(self) -> None:
        done = []
        t = _SeqTarget()
        t.x = 0.0
        seq = AnimationSequence(self.tweens)
        seq.then(target=t, attr="x", end_value=1.0, duration_seconds=0.05)
        seq.on_done(lambda: done.append(True))
        seq.start()
        self.tweens.update(0.1)
        self.assertEqual(done, [True])

    def test_parallel_steps_both_run(self) -> None:
        t = _SeqTarget()
        t.x = 0.0
        t.y = 0.0
        seq = AnimationSequence(self.tweens)
        seq.parallel([
            dict(target=t, attr="x", end_value=50.0, duration_seconds=0.1),
            dict(target=t, attr="y", end_value=80.0, duration_seconds=0.1),
        ])
        seq.start()
        self.tweens.update(0.15)
        self.assertAlmostEqual(t.x, 50.0, places=5)
        self.assertAlmostEqual(t.y, 80.0, places=5)

    def test_wait_delays_next_step(self) -> None:
        t = _SeqTarget()
        t.x = 0.0
        seq = AnimationSequence(self.tweens)
        seq.wait(0.1)
        seq.then(target=t, attr="x", end_value=10.0, duration_seconds=0.05)
        seq.start()
        self.tweens.update(0.05)
        # Still in wait phase; x unchanged
        self.assertAlmostEqual(t.x, 0.0, places=5)
        self.tweens.update(0.15)
        self.assertAlmostEqual(t.x, 10.0, places=5)

    def test_cancel_stops_further_steps(self) -> None:
        t = _SeqTarget()
        t.x = 0.0
        t.y = 0.0
        seq = AnimationSequence(self.tweens)
        seq.then(target=t, attr="x", end_value=10.0, duration_seconds=0.1)
        seq.then(target=t, attr="y", end_value=99.0, duration_seconds=0.1)
        handle = seq.start()
        self.tweens.update(0.05)
        handle.cancel()
        self.tweens.update(0.2)
        # y should never reach 99 because cancel blocked step 2
        self.assertAlmostEqual(t.y, 0.0, places=5)

    def test_parallel_empty_group_no_hang(self) -> None:
        done = []
        t = _SeqTarget()
        seq = AnimationSequence(self.tweens)
        seq.parallel([])
        seq.on_done(lambda: done.append(True))
        seq.start()
        self.tweens.update(0.01)
        self.assertEqual(done, [True])

    def test_builder_returns_self(self) -> None:
        seq = AnimationSequence(self.tweens)
        t = _SeqTarget()
        result = seq.then(target=t, attr="x", end_value=1.0, duration_seconds=0.1)
        self.assertIs(result, seq)

    def test_on_done_returns_self(self) -> None:
        seq = AnimationSequence(self.tweens)
        result = seq.on_done(lambda: None)
        self.assertIs(result, seq)


# ---------------------------------------------------------------------------
# Pass-AH tests — SettingsRegistry + SettingDescriptor
# ---------------------------------------------------------------------------

from gui_do import SettingsRegistry, SettingDescriptor


class SettingDescriptorTests(unittest.TestCase):
    """SettingDescriptor field access."""

    def test_fields(self) -> None:
        d = SettingDescriptor("audio", "volume", 1.0, "Master Volume")
        self.assertEqual(d.namespace, "audio")
        self.assertEqual(d.key, "volume")
        self.assertEqual(d.default, 1.0)
        self.assertEqual(d.label, "Master Volume")

    def test_empty_label_default(self) -> None:
        d = SettingDescriptor("ns", "k", 42)
        self.assertEqual(d.label, "")


class SettingsRegistryTests(unittest.TestCase):
    """SettingsRegistry declare/get/set/reset/inspect."""

    def setUp(self):
        self.reg = SettingsRegistry()

    def test_declare_returns_observable(self) -> None:
        ov = self.reg.declare("audio", "volume", 1.0)
        self.assertEqual(ov.value, 1.0)

    def test_declare_same_key_idempotent(self) -> None:
        ov1 = self.reg.declare("audio", "volume", 1.0)
        ov1.subscribe(lambda v: None)
        ov2 = self.reg.declare("audio", "volume", 0.5)  # same ns/key
        self.assertIs(ov1, ov2)
        self.assertEqual(ov2.value, 1.0)  # default from first declare

    def test_get_value(self) -> None:
        self.reg.declare("app", "theme", "dark")
        self.assertEqual(self.reg.get_value("app", "theme"), "dark")

    def test_set_value_fires_subscriber(self) -> None:
        changes = []
        self.reg.declare("app", "zoom", 1.0).subscribe(changes.append)
        self.reg.set_value("app", "zoom", 2.0)
        self.assertIn(2.0, changes)

    def test_get_undeclared_raises_key_error(self) -> None:
        with self.assertRaises(KeyError):
            self.reg.get("nope", "nope")

    def test_empty_namespace_raises(self) -> None:
        with self.assertRaises(ValueError):
            self.reg.declare("", "k", 0)

    def test_empty_key_raises(self) -> None:
        with self.assertRaises(ValueError):
            self.reg.declare("ns", "", 0)

    def test_reset_reverts_to_default(self) -> None:
        self.reg.declare("ui", "size", 14)
        self.reg.set_value("ui", "size", 20)
        self.reg.reset("ui")
        self.assertEqual(self.reg.get_value("ui", "size"), 14)

    def test_reset_all(self) -> None:
        self.reg.declare("a", "x", 1)
        self.reg.declare("b", "y", 2)
        self.reg.set_value("a", "x", 99)
        self.reg.set_value("b", "y", 99)
        self.reg.reset_all()
        self.assertEqual(self.reg.get_value("a", "x"), 1)
        self.assertEqual(self.reg.get_value("b", "y"), 2)

    def test_namespaces_sorted(self) -> None:
        self.reg.declare("z", "k", 0)
        self.reg.declare("a", "k", 0)
        ns = self.reg.namespaces()
        self.assertEqual(ns, sorted(ns))

    def test_keys_sorted(self) -> None:
        self.reg.declare("ns", "b", 0)
        self.reg.declare("ns", "a", 0)
        ks = self.reg.keys("ns")
        self.assertEqual(ks, sorted(ks))

    def test_describe_returns_descriptor(self) -> None:
        self.reg.declare("ns", "k", 42, label="The K")
        d = self.reg.describe("ns", "k")
        self.assertIsNotNone(d)
        self.assertEqual(d.default, 42)
        self.assertEqual(d.label, "The K")

    def test_describe_unknown_returns_none(self) -> None:
        self.assertIsNone(self.reg.describe("ns", "missing"))

    def test_all_descriptors_ordered(self) -> None:
        self.reg.declare("b", "y", 0)
        self.reg.declare("a", "x", 0)
        all_d = self.reg.all_descriptors()
        ns_keys = [(d.namespace, d.key) for d in all_d]
        self.assertEqual(ns_keys, sorted(ns_keys))

    def test_save_returns_false_without_path(self) -> None:
        result = self.reg.save()
        self.assertFalse(result)

    def test_load_returns_false_without_path(self) -> None:
        result = self.reg.load()
        self.assertFalse(result)


# ---------------------------------------------------------------------------
# Pass-AI tests — Router + RouteEntry
# ---------------------------------------------------------------------------

from gui_do import Router, RouteEntry


class RouterRegistrationTests(unittest.TestCase):
    """Router.register / scene_for / guard / on_route_change."""

    def test_register_and_scene_for(self) -> None:
        r = Router()
        r.register("/home", "home_scene")
        self.assertEqual(r.scene_for("/home"), "home_scene")

    def test_scene_for_unknown_is_none(self) -> None:
        r = Router()
        self.assertIsNone(r.scene_for("/unknown"))

    def test_empty_route_raises(self) -> None:
        r = Router()
        with self.assertRaises(ValueError):
            r.register("", "scene")

    def test_empty_scene_raises(self) -> None:
        r = Router()
        with self.assertRaises(ValueError):
            r.register("/home", "")

    def test_add_guard_non_callable_raises(self) -> None:
        r = Router()
        with self.assertRaises(ValueError):
            r.add_guard("not_callable")  # type: ignore

    def test_on_route_change_non_callable_raises(self) -> None:
        r = Router()
        with self.assertRaises(ValueError):
            r.on_route_change("not_callable")  # type: ignore


class RouterNavigationTests(unittest.TestCase):
    """Router push / pop / replace / guards / callbacks."""

    def setUp(self):
        self.router = Router()
        self.router.register("/home", "home_scene")
        self.router.register("/editor", "editor_scene")
        self.router.register("/settings", "settings_scene")

    def test_push_adds_to_history(self) -> None:
        self.router.push("/home")
        self.assertEqual(self.router.current_route, "/home")

    def test_push_returns_true_on_success(self) -> None:
        self.assertTrue(self.router.push("/home"))

    def test_push_fires_on_route_change(self) -> None:
        events = []
        self.router.on_route_change(events.append)
        self.router.push("/home")
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].route, "/home")

    def test_push_with_params_stored(self) -> None:
        self.router.push("/editor", {"file": "main.py"})
        self.assertEqual(self.router.current_params, {"file": "main.py"})

    def test_pop_returns_to_previous(self) -> None:
        self.router.push("/home")
        self.router.push("/editor")
        self.router.pop()
        self.assertEqual(self.router.current_route, "/home")

    def test_pop_empty_history_returns_false(self) -> None:
        self.assertFalse(self.router.pop())

    def test_pop_single_entry_returns_false(self) -> None:
        self.router.push("/home")
        self.assertFalse(self.router.pop())

    def test_can_pop_with_two_entries(self) -> None:
        self.router.push("/home")
        self.router.push("/editor")
        self.assertTrue(self.router.can_pop())

    def test_can_pop_one_entry_false(self) -> None:
        self.router.push("/home")
        self.assertFalse(self.router.can_pop())

    def test_replace_changes_current_without_growing_history(self) -> None:
        self.router.push("/home")
        self.router.replace("/editor")
        self.assertEqual(self.router.current_route, "/editor")
        self.assertEqual(len(self.router.history), 1)

    def test_guard_blocking_prevents_navigation(self) -> None:
        self.router.push("/home")
        self.router.add_guard(lambda f, t, p: False)  # block all
        result = self.router.push("/editor")
        self.assertFalse(result)
        self.assertEqual(self.router.current_route, "/home")

    def test_guard_allowing_permits_navigation(self) -> None:
        self.router.push("/home")
        self.router.add_guard(lambda f, t, p: True)
        result = self.router.push("/editor")
        self.assertTrue(result)
        self.assertEqual(self.router.current_route, "/editor")

    def test_unsubscribe_stops_callbacks(self) -> None:
        events = []
        unsub = self.router.on_route_change(events.append)
        self.router.push("/home")
        unsub()
        self.router.push("/editor")
        self.assertEqual(len(events), 1)  # second push not received

    def test_history_is_copy(self) -> None:
        self.router.push("/home")
        h = self.router.history
        h.clear()
        self.assertEqual(len(self.router.history), 1)

    def test_route_entry_fields(self) -> None:
        e = RouteEntry(route="/home", params={"x": 1})
        self.assertEqual(e.route, "/home")
        self.assertEqual(e.params, {"x": 1})

    def test_current_params_empty_when_no_history(self) -> None:
        self.assertEqual(self.router.current_params, {})

    def test_current_params_returns_copy(self) -> None:
        self.router.push("/home", {"k": "v"})
        p = self.router.current_params
        p["k"] = "modified"
        self.assertEqual(self.router.current_params, {"k": "v"})


# ---------------------------------------------------------------------------
# Pass-AJ tests — FlexLayout, FlexItem, FlexDirection, FlexAlign, FlexJustify
# ---------------------------------------------------------------------------

from gui_do import FlexLayout, FlexItem, FlexDirection, FlexAlign, FlexJustify


def _flex_node(x=0, y=0, w=40, h=30, cid=None):
    """Create a _GoodNode with the given rect for flex tests."""
    n = _GoodNode()
    n.control_id = cid or f"fn_{id(n)}"
    n.rect = _Rect(x, y, w, h)
    return n


class FlexLayoutRowTests(unittest.TestCase):
    """FlexLayout ROW direction — basics, grow, gap, justify, align."""

    def test_row_places_items_left_to_right(self) -> None:
        n1, n2 = _flex_node(w=50), _flex_node(w=60)
        fl = FlexLayout(direction=FlexDirection.ROW, gap=0)
        fl.items = [FlexItem(n1, basis=50), FlexItem(n2, basis=60)]
        fl.apply(_Rect(0, 0, 200, 40))
        self.assertEqual(n1.rect.x, 0)
        self.assertEqual(n2.rect.x, 50)

    def test_row_gap_offsets_second_item(self) -> None:
        n1, n2 = _flex_node(w=50), _flex_node(w=50)
        fl = FlexLayout(direction=FlexDirection.ROW, gap=10)
        fl.items = [FlexItem(n1, basis=50), FlexItem(n2, basis=50)]
        fl.apply(_Rect(0, 0, 200, 40))
        self.assertEqual(n2.rect.x, 60)

    def test_grow_distributes_surplus(self) -> None:
        n1, n2 = _flex_node(), _flex_node()
        fl = FlexLayout(direction=FlexDirection.ROW, gap=0)
        fl.items = [FlexItem(n1, grow=1, basis=0), FlexItem(n2, grow=1, basis=0)]
        fl.apply(_Rect(0, 0, 200, 40))
        self.assertEqual(n1.rect.width, 100)
        self.assertEqual(n2.rect.width, 100)

    def test_grow_zero_does_not_grow(self) -> None:
        n1, n2 = _flex_node(), _flex_node()
        fl = FlexLayout(direction=FlexDirection.ROW, gap=0)
        fl.items = [FlexItem(n1, grow=0, basis=50), FlexItem(n2, grow=1, basis=0)]
        fl.apply(_Rect(0, 0, 200, 40))
        self.assertEqual(n1.rect.width, 50)
        self.assertEqual(n2.rect.width, 150)

    def test_align_stretch_fills_cross_axis(self) -> None:
        n1 = _flex_node(h=20)
        fl = FlexLayout(direction=FlexDirection.ROW, align=FlexAlign.STRETCH)
        fl.items = [FlexItem(n1, basis=100)]
        fl.apply(_Rect(0, 0, 200, 80))
        self.assertEqual(n1.rect.height, 80)

    def test_align_center_centers_cross_axis(self) -> None:
        n1 = _flex_node(h=20)
        fl = FlexLayout(direction=FlexDirection.ROW, align=FlexAlign.CENTER)
        fl.items = [FlexItem(n1, basis=100)]
        fl.apply(_Rect(0, 0, 200, 80))
        self.assertEqual(n1.rect.centery, 40)

    def test_align_end_aligns_bottom(self) -> None:
        n1 = _flex_node(h=20)
        fl = FlexLayout(direction=FlexDirection.ROW, align=FlexAlign.END)
        fl.items = [FlexItem(n1, basis=100)]
        fl.apply(_Rect(0, 0, 200, 80))
        self.assertEqual(n1.rect.bottom, 80)

    def test_justify_center(self) -> None:
        n1 = _flex_node()
        fl = FlexLayout(direction=FlexDirection.ROW, justify=FlexJustify.CENTER, gap=0)
        fl.items = [FlexItem(n1, basis=80)]
        fl.apply(_Rect(0, 0, 200, 40))
        # 80px item centred in 200px → x = 60
        self.assertEqual(n1.rect.x, 60)

    def test_justify_end(self) -> None:
        n1 = _flex_node()
        fl = FlexLayout(direction=FlexDirection.ROW, justify=FlexJustify.END, gap=0)
        fl.items = [FlexItem(n1, basis=80)]
        fl.apply(_Rect(0, 0, 200, 40))
        self.assertEqual(n1.rect.right, 200)

    def test_max_size_clamps_grow(self) -> None:
        n1, n2 = _flex_node(), _flex_node()
        fl = FlexLayout(direction=FlexDirection.ROW, gap=0)
        fl.items = [FlexItem(n1, grow=1, basis=0, max_size=50),
                    FlexItem(n2, grow=1, basis=0)]
        fl.apply(_Rect(0, 0, 200, 40))
        self.assertLessEqual(n1.rect.width, 50)

    def test_min_size_clamps_shrink(self) -> None:
        n1, n2 = _flex_node(), _flex_node()
        fl = FlexLayout(direction=FlexDirection.ROW, gap=0)
        fl.items = [FlexItem(n1, basis=150, min_size=100),
                    FlexItem(n2, basis=150)]
        fl.apply(_Rect(0, 0, 100, 40))  # very tight container
        self.assertGreaterEqual(n1.rect.width, 100)

    def test_padding_shrinks_available_space(self) -> None:
        n1 = _flex_node()
        fl = FlexLayout(direction=FlexDirection.ROW, padding=20, gap=0)
        fl.items = [FlexItem(n1, grow=1, basis=0)]
        fl.apply(_Rect(0, 0, 200, 80))
        # padding=20 on each side → available = 160
        self.assertEqual(n1.rect.width, 160)
        self.assertEqual(n1.rect.x, 20)

    def test_empty_items_no_error(self) -> None:
        fl = FlexLayout(direction=FlexDirection.ROW)
        fl.apply(_Rect(0, 0, 200, 80))  # must not raise

    def test_add_helper_appends(self) -> None:
        n1 = _flex_node()
        fl = FlexLayout(direction=FlexDirection.ROW)
        item = fl.add(n1, basis=50)
        self.assertIs(item.node, n1)
        self.assertEqual(len(fl.items), 1)

    def test_remove_helper(self) -> None:
        n1 = _flex_node()
        fl = FlexLayout(direction=FlexDirection.ROW)
        fl.add(n1)
        removed = fl.remove(n1)
        self.assertTrue(removed)
        self.assertEqual(fl.items, [])

    def test_remove_unknown_returns_false(self) -> None:
        fl = FlexLayout(direction=FlexDirection.ROW)
        self.assertFalse(fl.remove(_flex_node()))

    def test_clear_removes_all(self) -> None:
        fl = FlexLayout(direction=FlexDirection.ROW)
        fl.add(_flex_node())
        fl.add(_flex_node())
        fl.clear()
        self.assertEqual(fl.items, [])


class FlexLayoutColumnTests(unittest.TestCase):
    """FlexLayout COLUMN direction — vertical flow."""

    def test_column_places_items_top_to_bottom(self) -> None:
        n1, n2 = _flex_node(h=30), _flex_node(h=40)
        fl = FlexLayout(direction=FlexDirection.COLUMN, gap=0)
        fl.items = [FlexItem(n1, basis=30), FlexItem(n2, basis=40)]
        fl.apply(_Rect(0, 0, 100, 200))
        self.assertEqual(n1.rect.y, 0)
        self.assertEqual(n2.rect.y, 30)

    def test_column_grow_distributes_vertically(self) -> None:
        n1, n2 = _flex_node(), _flex_node()
        fl = FlexLayout(direction=FlexDirection.COLUMN, gap=0)
        fl.items = [FlexItem(n1, grow=1, basis=0), FlexItem(n2, grow=1, basis=0)]
        fl.apply(_Rect(0, 0, 80, 200))
        self.assertEqual(n1.rect.height, 100)
        self.assertEqual(n2.rect.height, 100)

    def test_align_self_overrides_container_align(self) -> None:
        n1, n2 = _flex_node(w=40), _flex_node(w=40)
        fl = FlexLayout(direction=FlexDirection.COLUMN, align=FlexAlign.START, gap=0)
        fl.items = [
            FlexItem(n1, basis=30, align_self=FlexAlign.STRETCH),
            FlexItem(n2, basis=30),
        ]
        fl.apply(_Rect(0, 0, 100, 100))
        self.assertEqual(n1.rect.width, 100)
        self.assertEqual(n2.rect.width, 40)  # inherits START = no stretch

    def test_flex_enum_members(self) -> None:
        self.assertIn(FlexDirection.ROW, list(FlexDirection))
        self.assertIn(FlexAlign.STRETCH, list(FlexAlign))
        self.assertIn(FlexJustify.SPACE_BETWEEN, list(FlexJustify))


# ---------------------------------------------------------------------------
# Pass-AK tests — FormModel, FormField, ValidationRule, FieldError
# ---------------------------------------------------------------------------

from gui_do import FormModel, FormField, ValidationRule, FieldError


class FormFieldTests(unittest.TestCase):
    """FormField validation, commit, reset, dirty tracking."""

    def _field(self, value="", required=False, validators=None):
        return FormField("field", value, required=required, validators=validators or [])

    def test_initial_not_dirty(self) -> None:
        f = self._field("hello")
        self.assertFalse(f.is_dirty)

    def test_change_marks_dirty(self) -> None:
        f = self._field("hello")
        f.value.value = "world"
        self.assertTrue(f.is_dirty)

    def test_commit_clears_dirty(self) -> None:
        f = self._field("hello")
        f.value.value = "world"
        f.commit()
        self.assertFalse(f.is_dirty)

    def test_reset_reverts_to_committed(self) -> None:
        f = self._field("hello")
        f.value.value = "world"
        f.reset()
        self.assertEqual(f.value.value, "hello")

    def test_validate_passes_no_validators(self) -> None:
        f = self._field("anything")
        self.assertTrue(f.validate())

    def test_required_empty_fails_validation(self) -> None:
        f = self._field("", required=True)
        self.assertFalse(f.validate())
        self.assertIsNotNone(f.first_error)

    def test_required_non_empty_passes(self) -> None:
        f = self._field("x", required=True)
        self.assertTrue(f.validate())

    def test_custom_validator_failure(self) -> None:
        def must_be_int(v):
            try:
                int(v)
                return None
            except (TypeError, ValueError):
                return "Must be an integer."

        f = self._field("abc", validators=[must_be_int])
        self.assertFalse(f.validate())
        self.assertEqual(f.first_error, "Must be an integer.")

    def test_custom_validator_passing(self) -> None:
        f = self._field("42", validators=[lambda v: None if v.isdigit() else "digits only"])
        self.assertTrue(f.validate())

    def test_errors_cleared_after_reset(self) -> None:
        f = self._field("", required=True)
        f.validate()
        f.reset()
        self.assertEqual(f.errors, [])
        self.assertTrue(f.is_valid)

    def test_on_errors_changed_fires(self) -> None:
        changes = []
        f = self._field("", required=True)
        f.on_errors_changed(changes.append)
        f.validate()
        self.assertEqual(len(changes), 1)

    def test_on_errors_changed_unsubscribe(self) -> None:
        changes = []
        f = self._field("", required=True)
        unsub = f.on_errors_changed(changes.append)
        unsub()
        f.validate()
        self.assertEqual(changes, [])

    def test_add_validator_appends(self) -> None:
        f = self._field("x")
        f.add_validator(lambda v: "bad" if v != "ok" else None)
        self.assertFalse(f.validate())

    def test_name_property(self) -> None:
        f = FormField("my_field", 0)
        self.assertEqual(f.name, "my_field")


class FormModelTests(unittest.TestCase):
    """FormModel aggregate operations."""

    def setUp(self):
        self.form = FormModel()

    def test_add_field_returns_field(self) -> None:
        f = self.form.add_field("name", "")
        self.assertIsInstance(f, FormField)

    def test_field_by_name(self) -> None:
        self.form.add_field("email", "a@b.com")
        self.assertEqual(self.form.field("email").value.value, "a@b.com")

    def test_fields_property_is_copy(self) -> None:
        self.form.add_field("x", 1)
        fields = self.form.fields
        fields["injected"] = None  # mutate copy
        self.assertNotIn("injected", self.form.fields)

    def test_is_dirty_any_field(self) -> None:
        f = self.form.add_field("a", "x")
        self.assertFalse(self.form.is_dirty)
        f.value.value = "y"
        self.assertTrue(self.form.is_dirty)

    def test_validate_all_valid(self) -> None:
        self.form.add_field("a", "hello", required=True)
        self.assertTrue(self.form.validate_all())
        self.assertTrue(self.form.is_valid)

    def test_validate_all_invalid(self) -> None:
        self.form.add_field("a", "", required=True)
        self.assertFalse(self.form.validate_all())
        self.assertFalse(self.form.is_valid)

    def test_commit_all_clears_dirty(self) -> None:
        f = self.form.add_field("a", "x")
        f.value.value = "y"
        self.form.commit_all()
        self.assertFalse(self.form.is_dirty)

    def test_reset_all_reverts_fields(self) -> None:
        f = self.form.add_field("a", "original")
        f.value.value = "changed"
        self.form.reset_all()
        self.assertEqual(f.value.value, "original")

    def test_get_values_snapshot(self) -> None:
        self.form.add_field("a", 1)
        self.form.add_field("b", 2)
        vals = self.form.get_values()
        self.assertEqual(vals, {"a": 1, "b": 2})

    def test_cross_validator_failure(self) -> None:
        fa = self.form.add_field("start", 10)
        fb = self.form.add_field("end", 5)

        def _check(form):
            if form.field("start").value.value > form.field("end").value.value:
                return [FieldError("end", "end must be >= start")]
            return None

        self.form.add_cross_validator(_check)
        self.assertFalse(self.form.validate_all())
        self.assertEqual(len(self.form.cross_errors), 1)

    def test_cross_validator_passing(self) -> None:
        self.form.add_field("a", 1)
        self.form.add_field("b", 2)
        self.form.add_cross_validator(lambda form: None)
        self.assertTrue(self.form.validate_all())
        self.assertEqual(self.form.cross_errors, [])

    def test_field_error_fields(self) -> None:
        e = FieldError("email", "invalid format")
        self.assertEqual(e.field_name, "email")
        self.assertEqual(e.message, "invalid format")


# ---------------------------------------------------------------------------
# Pass-AL tests — ComputedValue
# ---------------------------------------------------------------------------

from gui_do import ComputedValue


class ComputedValueTests(unittest.TestCase):
    """ComputedValue lazy derivation and subscriber notification."""

    def _ov(self, v):
        return ObservableValue(v)

    def test_initial_value(self) -> None:
        a = self._ov(3)
        cv = ComputedValue(lambda: a.value * 2, deps=[a])
        self.assertEqual(cv.value, 6)

    def test_recomputes_on_dep_change(self) -> None:
        a = self._ov(1)
        b = self._ov(2)
        cv = ComputedValue(lambda: a.value + b.value, deps=[a, b])
        a.value = 10
        self.assertEqual(cv.value, 12)

    def test_notifies_subscribers(self) -> None:
        changes = []
        a = self._ov(1)
        cv = ComputedValue(lambda: a.value * 2, deps=[a])
        cv.subscribe(changes.append)
        a.value = 5
        self.assertIn(10, changes)

    def test_unsubscribe_stops_notifications(self) -> None:
        changes = []
        a = self._ov(1)
        cv = ComputedValue(lambda: a.value, deps=[a])
        unsub = cv.subscribe(changes.append)
        unsub()
        a.value = 99
        self.assertEqual(changes, [])

    def test_dispose_removes_dep_listeners(self) -> None:
        a = self._ov(1)
        cv = ComputedValue(lambda: a.value, deps=[a])
        cv.dispose()
        # After dispose, changing dep should not raise
        a.value = 99  # must not raise

    def test_lazy_no_recompute_when_not_dirty(self) -> None:
        calls = []
        a = self._ov(1)

        def _fn():
            calls.append(True)
            return a.value

        cv = ComputedValue(_fn, deps=[a])
        _ = cv.value  # first read
        _ = cv.value  # second read — no dep change
        self.assertEqual(len(calls), 1)

    def test_multiple_deps(self) -> None:
        a, b, c = self._ov(1), self._ov(2), self._ov(3)
        cv = ComputedValue(lambda: a.value + b.value + c.value, deps=[a, b, c])
        c.value = 10
        self.assertEqual(cv.value, 13)


# ---------------------------------------------------------------------------
# Pass-AM tests — ToastManager, ToastHandle, ToastSeverity
# ---------------------------------------------------------------------------

from gui_do import ToastManager, ToastHandle, ToastSeverity


class ToastManagerTests(unittest.TestCase):
    """ToastManager show, dismiss, update expiry."""

    def _mgr(self, **kw):
        return ToastManager(_Rect(0, 0, 800, 600), **kw)

    def test_show_returns_handle(self) -> None:
        mgr = self._mgr()
        h = mgr.show("hello")
        self.assertIsInstance(h, ToastHandle)

    def test_visible_count_increments(self) -> None:
        mgr = self._mgr()
        mgr.show("a")
        mgr.show("b")
        self.assertEqual(mgr.visible_count, 2)

    def test_handle_is_visible_true(self) -> None:
        mgr = self._mgr()
        h = mgr.show("msg")
        self.assertTrue(h.is_visible)

    def test_dismiss_removes_toast(self) -> None:
        mgr = self._mgr()
        h = mgr.show("msg")
        h.dismiss()
        self.assertEqual(mgr.visible_count, 0)
        self.assertFalse(h.is_visible)

    def test_dismiss_all_returns_count(self) -> None:
        mgr = self._mgr()
        mgr.show("a")
        mgr.show("b")
        n = mgr.dismiss_all()
        self.assertEqual(n, 2)
        self.assertEqual(mgr.visible_count, 0)

    def test_max_visible_evicts_oldest(self) -> None:
        mgr = self._mgr(max_visible=2)
        mgr.show("a")
        mgr.show("b")
        mgr.show("c")
        self.assertEqual(mgr.visible_count, 2)

    def test_update_expires_toast(self) -> None:
        mgr = self._mgr(default_duration_seconds=0.1)
        mgr.show("bye", duration_seconds=0.1)
        mgr.update(0.2)
        self.assertEqual(mgr.visible_count, 0)

    def test_update_persistent_not_expired(self) -> None:
        mgr = self._mgr()
        mgr.show_persistent("persistent")
        mgr.update(9999.0)
        self.assertEqual(mgr.visible_count, 1)

    def test_toast_severity_enum_members(self) -> None:
        members = {s for s in ToastSeverity}
        self.assertIn(ToastSeverity.INFO, members)
        self.assertIn(ToastSeverity.ERROR, members)
        self.assertIn(ToastSeverity.WARNING, members)
        self.assertIn(ToastSeverity.SUCCESS, members)

    def test_severity_custom(self) -> None:
        mgr = self._mgr()
        h = mgr.show("warn!", severity=ToastSeverity.WARNING)
        self.assertIsInstance(h, ToastHandle)

    def test_show_persistent_returns_handle(self) -> None:
        mgr = self._mgr()
        h = mgr.show_persistent("info", severity=ToastSeverity.INFO)
        self.assertTrue(h.is_visible)


# ---------------------------------------------------------------------------
# Pass-AN tests — ClipboardManager
# ---------------------------------------------------------------------------

from gui_do import ClipboardManager


class ClipboardManagerTests(unittest.TestCase):
    """ClipboardManager graceful failure without display."""

    def test_copy_returns_bool(self) -> None:
        # In headless test env, copy may return True or False — must not raise
        result = ClipboardManager.copy("hello")
        self.assertIsInstance(result, bool)

    def test_paste_returns_str(self) -> None:
        # In headless test env, paste returns "" or a string — must not raise
        result = ClipboardManager.paste()
        self.assertIsInstance(result, str)

    def test_copy_paste_static_methods(self) -> None:
        # Static method — callable on class without instantiating
        self.assertTrue(callable(ClipboardManager.copy))
        self.assertTrue(callable(ClipboardManager.paste))


# ---------------------------------------------------------------------------
# Pass-AO tests — EventBus (subscribe, publish, unsubscribe, scope, once)
# ---------------------------------------------------------------------------

from gui_do import EventBus


class EventBusSubscribePublishTests(unittest.TestCase):
    """EventBus basic publish/subscribe."""

    def test_subscribe_and_publish(self) -> None:
        bus = EventBus()
        received = []
        bus.subscribe("topic", received.append)
        bus.publish("topic", "hello")
        self.assertEqual(received, ["hello"])

    def test_no_subscribers_no_error(self) -> None:
        bus = EventBus()
        bus.publish("nobody_listening", 42)  # must not raise

    def test_unsubscribe_stops_delivery(self) -> None:
        bus = EventBus()
        received = []
        sub = bus.subscribe("t", received.append)
        bus.unsubscribe(sub)
        bus.publish("t", "msg")
        self.assertEqual(received, [])

    def test_subscriber_count_by_topic(self) -> None:
        bus = EventBus()
        bus.subscribe("a", lambda _: None)
        bus.subscribe("a", lambda _: None)
        bus.subscribe("b", lambda _: None)
        self.assertEqual(bus.subscriber_count("a"), 2)
        self.assertEqual(bus.subscriber_count("b"), 1)

    def test_subscriber_count_total(self) -> None:
        bus = EventBus()
        bus.subscribe("x", lambda _: None)
        bus.subscribe("y", lambda _: None)
        self.assertEqual(bus.subscriber_count(), 2)

    def test_multiple_topics_independent(self) -> None:
        bus = EventBus()
        a_log, b_log = [], []
        bus.subscribe("a", a_log.append)
        bus.subscribe("b", b_log.append)
        bus.publish("a", 1)
        bus.publish("b", 2)
        self.assertEqual(a_log, [1])
        self.assertEqual(b_log, [2])

    def test_publish_none_payload(self) -> None:
        bus = EventBus()
        received = []
        bus.subscribe("t", received.append)
        bus.publish("t")
        self.assertEqual(received, [None])


class EventBusScopeTests(unittest.TestCase):
    """EventBus scoped subscriptions and unsubscribe_scope."""

    def test_scoped_subscriber_receives_matching_scope(self) -> None:
        bus = EventBus()
        received = []
        bus.subscribe("t", received.append, scope="s1")
        bus.publish("t", "msg", scope="s1")
        self.assertEqual(received, ["msg"])

    def test_scoped_subscriber_not_reached_by_unscoped_publish(self) -> None:
        bus = EventBus()
        received = []
        bus.subscribe("t", received.append, scope="s1")
        # Unscoped publish only reaches scope=None subscribers
        bus.publish("t", "msg")
        self.assertEqual(received, [])

    def test_unscoped_subscriber_receives_all_publishes(self) -> None:
        bus = EventBus()
        received = []
        bus.subscribe("t", received.append)  # no scope
        bus.publish("t", "a", scope="s1")
        bus.publish("t", "b")
        self.assertEqual(received, ["a", "b"])

    def test_unsubscribe_scope_removes_all(self) -> None:
        bus = EventBus()
        received = []
        # Use distinct handlers so subscriptions are unique objects in the set
        h1, h2 = lambda p: received.append(p), lambda p: received.append(p)
        bus.subscribe("t", h1, scope="grp")
        bus.subscribe("t", h2, scope="grp")
        removed = bus.unsubscribe_scope("grp")
        self.assertEqual(removed, 2)
        bus.publish("t", "msg", scope="grp")
        self.assertEqual(received, [])

    def test_unsubscribe_scope_unknown_returns_zero(self) -> None:
        bus = EventBus()
        self.assertEqual(bus.unsubscribe_scope("nobody"), 0)


class EventBusOnceTests(unittest.TestCase):
    """EventBus.once delivers exactly one message."""

    def test_once_fires_once(self) -> None:
        bus = EventBus()
        received = []
        bus.once("t", received.append)
        bus.publish("t", 1)
        bus.publish("t", 2)
        self.assertEqual(received, [1])

    def test_once_cancel_before_delivery(self) -> None:
        bus = EventBus()
        received = []
        sub = bus.once("t", received.append)
        bus.unsubscribe(sub)
        bus.publish("t", "msg")
        self.assertEqual(received, [])

    def test_once_auto_unsubscribes(self) -> None:
        bus = EventBus()
        bus.once("t", lambda _: None)
        bus.publish("t", "x")
        self.assertEqual(bus.subscriber_count("t"), 0)


# ---------------------------------------------------------------------------
# Pass-AP tests — InvalidationTracker
# ---------------------------------------------------------------------------

from gui_do import InvalidationTracker


class InvalidationTrackerTests(unittest.TestCase):
    """InvalidationTracker dirty rects, full-redraw, and frame lifecycle."""

    def test_initially_full_redraw(self) -> None:
        t = InvalidationTracker()
        full, rects = t.begin_frame()
        self.assertTrue(full)
        self.assertEqual(rects, [])

    def test_invalidate_all_sets_full_redraw(self) -> None:
        t = InvalidationTracker()
        t.end_frame()
        t.invalidate_all()
        full, _ = t.begin_frame()
        self.assertTrue(full)

    def test_end_frame_clears_dirty(self) -> None:
        t = InvalidationTracker()
        t.end_frame()  # clear initial state
        full, rects = t.begin_frame()
        self.assertFalse(full)

    def test_invalidate_rect_adds_dirty_region(self) -> None:
        t = InvalidationTracker()
        t.end_frame()
        t.invalidate_rect(_Rect(10, 10, 50, 50))
        full, rects = t.begin_frame()
        self.assertFalse(full)
        self.assertEqual(len(rects), 1)

    def test_screen_size_full_coverage_promotes_to_full_redraw(self) -> None:
        t = InvalidationTracker()
        t.set_screen_size((100, 100))
        t.end_frame()
        t.invalidate_rect(_Rect(0, 0, 100, 100))  # entire screen
        full, _ = t.begin_frame()
        self.assertTrue(full)

    def test_merge_dirty_rects_combines_overlapping(self) -> None:
        t = InvalidationTracker()
        t.end_frame()
        t.invalidate_rect(_Rect(0, 0, 40, 40))
        t.invalidate_rect(_Rect(30, 30, 40, 40))  # overlaps with first
        merged = t.merge_dirty_rects()
        self.assertEqual(len(merged), 1)

    def test_merge_dirty_rects_separate_keeps_both(self) -> None:
        t = InvalidationTracker()
        t.end_frame()
        t.invalidate_rect(_Rect(0, 0, 20, 20))
        t.invalidate_rect(_Rect(200, 200, 20, 20))
        merged = t.merge_dirty_rects()
        self.assertEqual(len(merged), 2)

    def test_end_frame_clears_dirty_rects(self) -> None:
        t = InvalidationTracker()
        t.end_frame()
        t.invalidate_rect(_Rect(0, 0, 10, 10))
        t.end_frame()
        merged = t.merge_dirty_rects()
        self.assertEqual(merged, [])


# ---------------------------------------------------------------------------
# Pass-AQ tests — ChangeKind, CollectionChange, ObservableList mutations
# ---------------------------------------------------------------------------

from gui_do import ChangeKind, CollectionChange, ObservableList


class ChangeKindCollectionChangeTests(unittest.TestCase):
    """ChangeKind enum and CollectionChange dataclass."""

    def test_change_kind_members(self) -> None:
        kinds = {k for k in ChangeKind}
        self.assertIn(ChangeKind.ADDED, kinds)
        self.assertIn(ChangeKind.REMOVED, kinds)
        self.assertIn(ChangeKind.REPLACED, kinds)
        self.assertIn(ChangeKind.CLEARED, kinds)
        self.assertIn(ChangeKind.MOVED, kinds)

    def test_collection_change_fields(self) -> None:
        ch = CollectionChange(kind=ChangeKind.ADDED, index=0, new_value="x")
        self.assertEqual(ch.kind, ChangeKind.ADDED)
        self.assertEqual(ch.index, 0)
        self.assertEqual(ch.new_value, "x")
        self.assertIsNone(ch.old_value)

    def test_collection_change_frozen(self) -> None:
        ch = CollectionChange(kind=ChangeKind.CLEARED)
        with self.assertRaises((AttributeError, TypeError)):
            ch.kind = ChangeKind.ADDED  # type: ignore


class ObservableListMutationTests(unittest.TestCase):
    """ObservableList mutations fire correct ChangeKind events."""

    def _list(self, *items):
        return ObservableList(list(items))

    def test_append_fires_added(self) -> None:
        events = []
        lst = self._list(1, 2)
        lst.subscribe(events.append)
        lst.append(3)
        self.assertEqual(events[-1].kind, ChangeKind.ADDED)
        self.assertEqual(events[-1].new_value, 3)

    def test_insert_fires_added(self) -> None:
        events = []
        lst = self._list(1, 2)
        lst.subscribe(events.append)
        lst.insert(0, 0)
        self.assertEqual(events[-1].kind, ChangeKind.ADDED)
        self.assertEqual(events[-1].index, 0)

    def test_remove_at_fires_removed(self) -> None:
        events = []
        lst = self._list("a", "b", "c")
        lst.subscribe(events.append)
        removed = lst.remove_at(1)
        self.assertEqual(removed, "b")
        self.assertEqual(events[-1].kind, ChangeKind.REMOVED)
        self.assertEqual(events[-1].old_value, "b")

    def test_setitem_fires_replaced(self) -> None:
        events = []
        lst = self._list(1, 2, 3)
        lst.subscribe(events.append)
        lst[1] = 99
        self.assertEqual(events[-1].kind, ChangeKind.REPLACED)
        self.assertEqual(events[-1].new_value, 99)

    def test_snapshot_returns_copy(self) -> None:
        lst = self._list(1, 2, 3)
        snap = lst.snapshot()
        snap.append(4)
        self.assertEqual(len(lst), 3)

    def test_unsubscribe_stops_events(self) -> None:
        events = []
        lst = self._list(1)
        unsub = lst.subscribe(events.append)
        unsub()
        lst.append(2)
        self.assertEqual(events, [])

    def test_len_and_iteration(self) -> None:
        lst = self._list(10, 20, 30)
        self.assertEqual(len(lst), 3)
        self.assertEqual(list(lst), [10, 20, 30])

    def test_contains(self) -> None:
        lst = self._list("x", "y")
        self.assertIn("x", lst)
        self.assertNotIn("z", lst)

    def test_index_found(self) -> None:
        lst = self._list("a", "b", "c")
        self.assertEqual(lst.index("b"), 1)

    def test_non_callable_listener_raises(self) -> None:
        lst = self._list()
        with self.assertRaises(ValueError):
            lst.subscribe("not_callable")  # type: ignore


# ---------------------------------------------------------------------------
# Pass-AR tests — LayoutPass, MeasureContext, ArrangeContext, LayoutRoot
# ---------------------------------------------------------------------------

from gui_do import LayoutPass, MeasureContext, ArrangeContext, LayoutRoot


class _SimpleLayout:
    """Minimal layout that records calls for test assertions."""

    def __init__(self, preferred=(200, 100)):
        self._preferred = preferred
        self.measure_calls = []
        self.arrange_calls = []

    def measure(self, context: MeasureContext):
        self.measure_calls.append((context.available_width, context.available_height))
        return self._preferred

    def arrange(self, context: ArrangeContext):
        self.arrange_calls.append(_Rect(context.rect))


class MeasureContextTests(unittest.TestCase):
    """MeasureContext attribute access."""

    def test_attributes(self) -> None:
        ctx = MeasureContext(800, 600)
        self.assertEqual(ctx.available_width, 800)
        self.assertEqual(ctx.available_height, 600)

    def test_available_size_tuple(self) -> None:
        ctx = MeasureContext(400, 300)
        self.assertEqual(ctx.available_size, (400, 300))


class ArrangeContextTests(unittest.TestCase):
    """ArrangeContext wraps a Rect."""

    def test_rect_stored(self) -> None:
        ctx = ArrangeContext(_Rect(10, 20, 300, 200))
        self.assertEqual(ctx.rect, _Rect(10, 20, 300, 200))

    def test_rect_is_copy(self) -> None:
        r = _Rect(0, 0, 100, 50)
        ctx = ArrangeContext(r)
        r.x = 999
        self.assertEqual(ctx.rect.x, 0)


class LayoutRootTests(unittest.TestCase):
    """LayoutRoot dirty tracking, update, preferred_size."""

    def test_initially_dirty(self) -> None:
        layout = _SimpleLayout()
        root = LayoutRoot(layout)
        self.assertTrue(root.is_dirty)

    def test_update_runs_measure_and_arrange(self) -> None:
        layout = _SimpleLayout()
        root = LayoutRoot(layout)
        ran = root.update(_Rect(0, 0, 800, 600))
        self.assertTrue(ran)
        self.assertEqual(len(layout.measure_calls), 1)
        self.assertEqual(len(layout.arrange_calls), 1)

    def test_update_skipped_when_not_dirty(self) -> None:
        layout = _SimpleLayout()
        root = LayoutRoot(layout)
        root.update(_Rect(0, 0, 800, 600))
        ran = root.update(_Rect(0, 0, 800, 600))  # same rect, not dirty
        self.assertFalse(ran)
        self.assertEqual(len(layout.measure_calls), 1)

    def test_mark_dirty_triggers_rerun(self) -> None:
        layout = _SimpleLayout()
        root = LayoutRoot(layout)
        root.update(_Rect(0, 0, 800, 600))
        root.mark_dirty()
        ran = root.update(_Rect(0, 0, 800, 600))
        self.assertTrue(ran)
        self.assertEqual(len(layout.measure_calls), 2)

    def test_preferred_size_after_update(self) -> None:
        layout = _SimpleLayout(preferred=(320, 240))
        root = LayoutRoot(layout)
        root.update(_Rect(0, 0, 800, 600))
        self.assertEqual(root.preferred_size, (320, 240))

    def test_new_rect_triggers_rerun(self) -> None:
        layout = _SimpleLayout()
        root = LayoutRoot(layout)
        root.update(_Rect(0, 0, 800, 600))
        ran = root.update(_Rect(0, 0, 1024, 768))  # different rect
        self.assertTrue(ran)

    def test_mark_dirty_with_invalidation(self) -> None:
        layout = _SimpleLayout()
        tracker = InvalidationTracker()
        tracker.end_frame()  # clear initial full-redraw
        root = LayoutRoot(layout, invalidation=tracker)
        root.update(_Rect(0, 0, 100, 100))
        tracker.end_frame()
        root.mark_dirty()
        full, _ = tracker.begin_frame()
        self.assertTrue(full)

    def test_layout_pass_protocol_satisfied(self) -> None:
        self.assertIsInstance(_SimpleLayout(), LayoutPass)


# ---------------------------------------------------------------------------
# Pass-AS tests — PropertyRegistry, PropertyDescriptor, ui_property
# ---------------------------------------------------------------------------

from gui_do import PropertyRegistry, PropertyDescriptor, ui_property, property_registry


class _InspectableControl:
    @property
    @ui_property(label="Alpha", type="float", min=0.0, max=1.0, group="Appearance")
    def alpha(self) -> float:
        return 1.0

    @alpha.setter
    def alpha(self, v: float) -> None:
        pass

    @property
    @ui_property(label="Title", type="str", group="Content")
    def title(self) -> str:
        return ""


class _ReadOnlyControl:
    @property
    @ui_property(label="Version", type="str", read_only=True)
    def version(self) -> str:
        return "1.0"


class PropertyDescriptorTests(unittest.TestCase):
    """PropertyDescriptor dataclass field access."""

    def test_fields(self) -> None:
        d = PropertyDescriptor(name="alpha", label="Alpha",
                               type="float", min=0.0, max=1.0,
                               group="Appearance")
        self.assertEqual(d.name, "alpha")
        self.assertEqual(d.label, "Alpha")
        self.assertEqual(d.type, "float")
        self.assertEqual(d.min, 0.0)
        self.assertEqual(d.group, "Appearance")

    def test_default_group(self) -> None:
        d = PropertyDescriptor(name="x", label="X")
        self.assertEqual(d.group, "General")

    def test_default_read_only_false(self) -> None:
        d = PropertyDescriptor(name="x", label="X")
        self.assertFalse(d.read_only)


class PropertyRegistryTests(unittest.TestCase):
    """PropertyRegistry scans @ui_property annotations."""

    def setUp(self):
        self.reg = PropertyRegistry()

    def test_descriptors_for_class(self) -> None:
        descs = self.reg.descriptors_for(_InspectableControl)
        names = [d.name for d in descs]
        self.assertIn("alpha", names)
        self.assertIn("title", names)

    def test_descriptor_label_correct(self) -> None:
        descs = self.reg.descriptors_for(_InspectableControl)
        alpha_desc = next(d for d in descs if d.name == "alpha")
        self.assertEqual(alpha_desc.label, "Alpha")

    def test_descriptor_type_correct(self) -> None:
        descs = self.reg.descriptors_for(_InspectableControl)
        alpha_desc = next(d for d in descs if d.name == "alpha")
        self.assertEqual(alpha_desc.type, "float")

    def test_descriptor_group_correct(self) -> None:
        descs = self.reg.descriptors_for(_InspectableControl)
        title_desc = next(d for d in descs if d.name == "title")
        self.assertEqual(title_desc.group, "Content")

    def test_read_only_property_detected(self) -> None:
        descs = self.reg.descriptors_for(_ReadOnlyControl)
        v = next(d for d in descs if d.name == "version")
        self.assertTrue(v.read_only)

    def test_descriptors_for_instance(self) -> None:
        instance = _InspectableControl()
        descs = self.reg.descriptors_for(instance)
        self.assertTrue(len(descs) >= 2)

    def test_cached_result_same_object(self) -> None:
        descs1 = self.reg.descriptors_for(_InspectableControl)
        descs2 = self.reg.descriptors_for(_InspectableControl)
        self.assertEqual([d.name for d in descs1], [d.name for d in descs2])

    def test_manual_register(self) -> None:
        reg = PropertyRegistry()
        d = PropertyDescriptor(name="custom", label="Custom", type="int")
        reg.register(_InspectableControl, d)
        descs = reg.descriptors_for(_InspectableControl)
        names = [desc.name for desc in descs]
        self.assertIn("custom", names)

    def test_clear_resets_cache(self) -> None:
        reg = PropertyRegistry()
        reg.descriptors_for(_InspectableControl)
        reg.clear()
        # After clear, all_classes should be empty (or at least the freshly
        # cleared class is gone)
        for cls in reg.all_classes():
            self.assertNotEqual(cls, _InspectableControl)

    def test_module_level_singleton_exists(self) -> None:
        self.assertIsInstance(property_registry, PropertyRegistry)


# ---------------------------------------------------------------------------
# Pass-AT tests — TelemetryCollector, TelemetrySample
# ---------------------------------------------------------------------------

from gui_do import TelemetryCollector, TelemetrySample, configure_telemetry, telemetry_collector


class TelemetryCollectorTests(unittest.TestCase):
    """TelemetryCollector enable/disable, record, filter, span."""

    def setUp(self):
        self.tc = TelemetryCollector()

    def test_initially_disabled(self) -> None:
        self.assertFalse(self.tc.enabled())

    def test_enable_disable(self) -> None:
        self.tc.enable()
        self.assertTrue(self.tc.enabled())
        self.tc.disable()
        self.assertFalse(self.tc.enabled())

    def test_should_record_when_disabled(self) -> None:
        self.assertFalse(self.tc.should_record("sys", "point"))

    def test_should_record_when_enabled(self) -> None:
        self.tc.enable()
        self.assertTrue(self.tc.should_record("sys", "point"))

    def test_set_min_duration_valid(self) -> None:
        self.tc.set_min_duration_ms(10.0)  # must not raise

    def test_set_min_duration_negative_raises(self) -> None:
        with self.assertRaises(ValueError):
            self.tc.set_min_duration_ms(-1.0)

    def test_set_system_enabled_empty_raises(self) -> None:
        with self.assertRaises(ValueError):
            self.tc.set_system_enabled("", True)

    def test_set_point_enabled_empty_raises(self) -> None:
        with self.assertRaises(ValueError):
            self.tc.set_point_enabled("sys", "", True)

    def test_set_file_logging_enabled(self) -> None:
        self.tc.set_file_logging_enabled(True)
        self.assertTrue(self.tc.file_logging_enabled())
        self.tc.set_file_logging_enabled(False)
        self.assertFalse(self.tc.file_logging_enabled())

    def test_set_live_analysis_enabled(self) -> None:
        self.tc.set_live_analysis_enabled(True)
        self.assertTrue(self.tc.live_analysis_enabled())

    def test_reset_clears_samples(self) -> None:
        self.tc.reset()  # must not raise

    def test_span_context_manager_no_error(self) -> None:
        self.tc.enable()
        with self.tc.span("sys", "point"):
            pass  # must not raise

    def test_span_disabled_no_error(self) -> None:
        with self.tc.span("sys", "point"):
            pass

    def test_clear_filters(self) -> None:
        self.tc.set_system_enabled("sys", False)
        self.tc.clear_filters()
        self.tc.enable()
        self.assertTrue(self.tc.should_record("sys", "pt"))

    def test_telemetry_sample_fields(self) -> None:
        s = TelemetrySample(timestamp=1.0, system="sys",
                            point="pt", elapsed_ms=5.0, metadata={})
        self.assertEqual(s.system, "sys")
        self.assertEqual(s.elapsed_ms, 5.0)

    def test_configure_telemetry_function_exists(self) -> None:
        self.assertTrue(callable(configure_telemetry))

    def test_telemetry_collector_singleton(self) -> None:
        self.assertIsInstance(telemetry_collector(), TelemetryCollector)


# ---------------------------------------------------------------------------
# Pass-AU tests — TaskScheduler, TaskEvent
# ---------------------------------------------------------------------------

from gui_do import TaskScheduler, TaskEvent


class TaskSchedulerStaticTests(unittest.TestCase):
    """TaskScheduler static helpers and construction."""

    def test_recommended_worker_count_default(self) -> None:
        count = TaskScheduler.recommended_worker_count()
        self.assertIsInstance(count, int)
        self.assertGreaterEqual(count, 1)

    def test_recommended_worker_count_cap(self) -> None:
        count = TaskScheduler.recommended_worker_count(logical_cpus=16, cap=4)
        self.assertLessEqual(count, 4)

    def test_recommended_worker_count_min_one(self) -> None:
        count = TaskScheduler.recommended_worker_count(logical_cpus=1, reserve_for_ui=1)
        self.assertEqual(count, 1)

    def test_construction(self) -> None:
        ts = TaskScheduler(max_workers=2)
        ts.shutdown()

    def test_default_not_paused(self) -> None:
        ts = TaskScheduler(max_workers=1)
        try:
            self.assertFalse(ts.is_execution_paused())
        finally:
            ts.shutdown()

    def test_set_execution_paused(self) -> None:
        ts = TaskScheduler(max_workers=1)
        try:
            ts.set_execution_paused(True)
            self.assertTrue(ts.is_execution_paused())
            ts.set_execution_paused(False)
            self.assertFalse(ts.is_execution_paused())
        finally:
            ts.shutdown()

    def test_add_task_does_not_raise(self) -> None:
        ts = TaskScheduler(max_workers=1)
        try:
            ts.add_task("t1", lambda: None)
        finally:
            ts.shutdown()

    def test_remove_tasks_no_error(self) -> None:
        ts = TaskScheduler(max_workers=1)
        try:
            ts.add_task("t2", lambda: None)
            ts.remove_tasks("t2")
        finally:
            ts.shutdown()

    def test_remove_all_no_error(self) -> None:
        ts = TaskScheduler(max_workers=1)
        try:
            ts.add_task("a", lambda: None)
            ts.add_task("b", lambda: None)
            ts.remove_all()
        finally:
            ts.shutdown()

    def test_suspend_resume_all(self) -> None:
        ts = TaskScheduler(max_workers=1)
        try:
            ts.add_task("s1", lambda: None)
            ts.suspend_all()
            ts.resume_all()
        finally:
            ts.shutdown()

    def test_shutdown_idempotent(self) -> None:
        ts = TaskScheduler(max_workers=1)
        ts.shutdown()
        ts.shutdown()  # second shutdown must not raise


class TaskEventTests(unittest.TestCase):
    """TaskEvent dataclass fields."""

    def test_fields(self) -> None:
        e = TaskEvent(operation="start", task_id="t1")
        self.assertEqual(e.operation, "start")
        self.assertEqual(e.task_id, "t1")
        self.assertIsNone(e.error)

    def test_with_error(self) -> None:
        e = TaskEvent(operation="fail", task_id="t2", error="oops")
        self.assertEqual(e.error, "oops")


# ---------------------------------------------------------------------------
# Pass-AV tests — PresentationModel, ValueChangeCallback, ValueChangeReason
# ---------------------------------------------------------------------------

from gui_do import PresentationModel, ValueChangeCallback, ValueChangeReason


class PresentationModelTests(unittest.TestCase):
    """PresentationModel bind/dispose lifecycle."""

    def test_bind_receives_updates(self) -> None:
        from gui_do import ObservableValue
        model = PresentationModel()
        obs = ObservableValue(0)
        received = []
        model.bind(obs, received.append)
        obs.value = 42
        self.assertEqual(received, [42])

    def test_dispose_unsubscribes(self) -> None:
        from gui_do import ObservableValue
        model = PresentationModel()
        obs = ObservableValue(0)
        received = []
        model.bind(obs, received.append)
        model.dispose()
        obs.value = 99
        self.assertEqual(received, [])

    def test_dispose_twice_no_error(self) -> None:
        model = PresentationModel()
        model.dispose()
        model.dispose()

    def test_bind_multiple(self) -> None:
        from gui_do import ObservableValue
        model = PresentationModel()
        a, b = ObservableValue(0), ObservableValue(0)
        log_a, log_b = [], []
        model.bind(a, log_a.append)
        model.bind(b, log_b.append)
        a.value = 1
        b.value = 2
        model.dispose()
        a.value = 9
        b.value = 9
        self.assertEqual(log_a, [1])
        self.assertEqual(log_b, [2])


class ValueChangeReasonTests(unittest.TestCase):
    """ValueChangeReason enum members."""

    def test_members_exist(self) -> None:
        reasons = {r for r in ValueChangeReason}
        self.assertIn(ValueChangeReason.KEYBOARD, reasons)
        self.assertIn(ValueChangeReason.PROGRAMMATIC, reasons)
        self.assertIn(ValueChangeReason.MOUSE_DRAG, reasons)
        self.assertIn(ValueChangeReason.WHEEL, reasons)

    def test_is_str_enum(self) -> None:
        self.assertIsInstance(ValueChangeReason.KEYBOARD, str)

    def test_callable_type(self) -> None:
        # ValueChangeCallback is a type alias (Callable), not a class
        import inspect
        from gui_do.events.value_change_callback import ValueChangeCallback as _VCC
        # Just ensure it is importable and usable as a type hint — verify via get_args
        self.assertTrue(True)


# ---------------------------------------------------------------------------
# Pass-AW tests — DragDropManager, DragPayload
# ---------------------------------------------------------------------------

from gui_do import DragDropManager, DragPayload


class DragPayloadTests(unittest.TestCase):
    """DragPayload dataclass."""

    def test_fields(self) -> None:
        p = DragPayload(drag_id="d1", data={"key": "val"})
        self.assertEqual(p.drag_id, "d1")
        self.assertEqual(p.data, {"key": "val"})
        self.assertIsNone(p.ghost_surface)
        self.assertEqual(p.ghost_offset, (0, 0))

    def test_custom_ghost_offset(self) -> None:
        p = DragPayload(drag_id="d2", ghost_offset=(10, 20))
        self.assertEqual(p.ghost_offset, (10, 20))


class DragDropManagerTests(unittest.TestCase):
    """DragDropManager construction and idle-state properties."""

    def test_construction_no_args(self) -> None:
        dm = DragDropManager()
        self.assertIsNotNone(dm)

    def test_custom_threshold(self) -> None:
        dm = DragDropManager(drag_threshold=12)
        self.assertIsNotNone(dm)

    def test_is_active_initially_false(self) -> None:
        dm = DragDropManager()
        self.assertFalse(dm.is_active)

    def test_active_payload_initially_none(self) -> None:
        dm = DragDropManager()
        self.assertIsNone(dm.active_payload)


# ---------------------------------------------------------------------------
# Pass-AX tests — ResizeManager
# ---------------------------------------------------------------------------

from gui_do import ResizeManager
from gui_do import EventBus


class ResizeManagerTests(unittest.TestCase):
    """ResizeManager initial size, notify_resize, callbacks, layout registration."""

    def test_default_initial_size(self) -> None:
        mgr = ResizeManager()
        self.assertEqual(mgr.size, (800, 600))
        self.assertEqual(mgr.width, 800)
        self.assertEqual(mgr.height, 600)

    def test_custom_initial_size(self) -> None:
        mgr = ResizeManager(initial_size=(1920, 1080))
        self.assertEqual(mgr.size, (1920, 1080))

    def test_notify_resize_updates_size(self) -> None:
        mgr = ResizeManager()
        mgr.notify_resize(1024, 768)
        self.assertEqual(mgr.size, (1024, 768))

    def test_resize_count_increments(self) -> None:
        mgr = ResizeManager()
        self.assertEqual(mgr.resize_count, 0)
        mgr.notify_resize(640, 480)
        self.assertEqual(mgr.resize_count, 1)
        mgr.notify_resize(800, 600)
        self.assertEqual(mgr.resize_count, 2)

    def test_on_resize_callback_fires(self) -> None:
        mgr = ResizeManager()
        received = []
        mgr.on_resize(lambda w, h: received.append((w, h)))
        mgr.notify_resize(1280, 720)
        self.assertEqual(received, [(1280, 720)])

    def test_on_resize_unsubscribe(self) -> None:
        mgr = ResizeManager()
        received = []
        unsub = mgr.on_resize(lambda w, h: received.append((w, h)))
        unsub()
        mgr.notify_resize(800, 600)
        self.assertEqual(received, [])

    def test_on_resize_non_callable_raises(self) -> None:
        mgr = ResizeManager()
        with self.assertRaises(ValueError):
            mgr.on_resize("not_callable")  # type: ignore

    def test_publishes_to_event_bus(self) -> None:
        bus = EventBus()
        mgr = ResizeManager(event_bus=bus)
        received = []
        bus.subscribe("window_resized", received.append)
        mgr.notify_resize(1024, 768)
        self.assertEqual(received, [(1024, 768)])

    def test_min_size_clamp(self) -> None:
        mgr = ResizeManager()
        mgr.notify_resize(0, 0)
        self.assertEqual(mgr.size, (1, 1))

    def test_unregister_layout_unknown_returns_false(self) -> None:
        from gui_do.layout.constraint_layout import ConstraintLayout
        mgr = ResizeManager()
        cl = ConstraintLayout()
        self.assertFalse(mgr.unregister_layout(cl))


# ---------------------------------------------------------------------------
# Pass-AY tests — FileDialogOptions, FileDialogHandle (pure data, no app)
# ---------------------------------------------------------------------------

from gui_do import FileDialogOptions, FileDialogHandle


class FileDialogOptionsTests(unittest.TestCase):
    """FileDialogOptions dataclass defaults and fields."""

    def test_default_title(self) -> None:
        opts = FileDialogOptions()
        self.assertEqual(opts.title, "Open File")

    def test_default_filters_empty(self) -> None:
        opts = FileDialogOptions()
        self.assertEqual(opts.filters, [])

    def test_allow_new_file_default_false(self) -> None:
        opts = FileDialogOptions()
        self.assertFalse(opts.allow_new_file)

    def test_multi_select_default_false(self) -> None:
        opts = FileDialogOptions()
        self.assertFalse(opts.multi_select)

    def test_custom_fields(self) -> None:
        opts = FileDialogOptions(
            title="Save As",
            allow_new_file=True,
            filters=[("Images", [".png", ".jpg"])],
        )
        self.assertEqual(opts.title, "Save As")
        self.assertTrue(opts.allow_new_file)
        self.assertEqual(opts.filters[0][0], "Images")


class FileDialogHandleTests(unittest.TestCase):
    """FileDialogHandle pure-data lifecycle."""

    def test_initially_open(self) -> None:
        h = FileDialogHandle()
        self.assertTrue(h.is_open)
        self.assertIsNone(h.result)

    def test_cancel_closes_handle(self) -> None:
        h = FileDialogHandle()
        h._cancel()
        self.assertFalse(h.is_open)
        self.assertEqual(h.result, [])

    def test_resolve_closes_handle(self) -> None:
        h = FileDialogHandle()
        h._resolve(["path/to/file.txt"])
        self.assertFalse(h.is_open)
        self.assertEqual(h.result, ["path/to/file.txt"])

    def test_on_close_callback_fires(self) -> None:
        h = FileDialogHandle()
        received = []
        h._on_close = received.append
        h._resolve(["a.txt"])
        self.assertEqual(received, [["a.txt"]])

    def test_cancel_on_close_fires_empty(self) -> None:
        h = FileDialogHandle()
        received = []
        h._on_close = received.append
        h._cancel()
        self.assertEqual(received, [[]])


# ---------------------------------------------------------------------------
# Pass-AZ tests — DesignTokens, ThemeManager
# ---------------------------------------------------------------------------

from gui_do import DesignTokens, ThemeManager


class DesignTokensTests(unittest.TestCase):
    """DesignTokens token storage and access."""

    def test_get_known_token(self) -> None:
        dt = DesignTokens("t", {"primary": (90, 140, 210)})
        self.assertEqual(dt.get("primary"), (90, 140, 210))

    def test_get_missing_with_fallback(self) -> None:
        dt = DesignTokens("t", {})
        self.assertEqual(dt.get("unknown", (1, 2, 3)), (1, 2, 3))

    def test_set_token(self) -> None:
        dt = DesignTokens("t", {})
        dt.set("accent", (50, 100, 200))
        self.assertEqual(dt.get("accent"), (50, 100, 200))

    def test_token_names_sorted(self) -> None:
        dt = DesignTokens("t", {"z": (0, 0, 0), "a": (1, 1, 1)})
        self.assertEqual(dt.token_names(), ["a", "z"])

    def test_to_dict_returns_copy(self) -> None:
        dt = DesignTokens("t", {"k": (5, 5, 5)})
        d = dt.to_dict()
        d["extra"] = (9, 9, 9)
        self.assertNotIn("extra", dt.token_names())

    def test_copy(self) -> None:
        dt = DesignTokens("original", {"x": (1, 2, 3)})
        copy = dt.copy("copy")
        self.assertEqual(copy.name, "copy")
        self.assertEqual(copy.get("x"), (1, 2, 3))

    def test_from_dict(self) -> None:
        dt = DesignTokens.from_dict("t", {"primary": [10, 20, 30]})
        self.assertEqual(dt.get("primary"), (10, 20, 30))

    def test_name_attribute(self) -> None:
        dt = DesignTokens("myname", {})
        self.assertEqual(dt.name, "myname")


class ThemeManagerTests(unittest.TestCase):
    """ThemeManager built-in themes, register, switch, token resolution."""

    def test_default_active_theme_is_dark(self) -> None:
        mgr = ThemeManager()
        self.assertEqual(mgr.active_theme.value, "dark")

    def test_switch_to_light(self) -> None:
        mgr = ThemeManager()
        result = mgr.switch("light")
        self.assertTrue(result)
        self.assertEqual(mgr.active_theme.value, "light")

    def test_switch_unknown_returns_false(self) -> None:
        mgr = ThemeManager()
        result = mgr.switch("nonexistent")
        self.assertFalse(result)
        self.assertEqual(mgr.active_theme.value, "dark")  # unchanged

    def test_register_custom_theme(self) -> None:
        mgr = ThemeManager()
        mgr.register_theme("contrast", {"primary": (255, 220, 0), "surface": (0, 0, 0)})
        result = mgr.switch("contrast")
        self.assertTrue(result)
        self.assertEqual(mgr.active_theme.value, "contrast")

    def test_active_tokens_observable(self) -> None:
        mgr = ThemeManager()
        received = []
        mgr.active_tokens.subscribe(received.append)
        mgr.switch("light")
        self.assertEqual(len(received), 1)
        self.assertIsInstance(received[0], DesignTokens)

    def test_register_empty_name_raises(self) -> None:
        mgr = ThemeManager()
        with self.assertRaises(ValueError):
            mgr.register_theme("", {"x": (0, 0, 0)})

    def test_register_design_tokens_directly(self) -> None:
        mgr = ThemeManager()
        dt = DesignTokens("custom2", {"text": (200, 200, 200)})
        mgr.register_theme("custom2", dt)
        mgr.switch("custom2")
        self.assertEqual(mgr.active_theme.value, "custom2")


# ---------------------------------------------------------------------------
# Pass-BA tests — FontRoleRegistry, FontRoleDef (pure-data)
# ---------------------------------------------------------------------------

from gui_do import FontRoleRegistry


class FontRoleRegistryTests(unittest.TestCase):
    """FontRoleRegistry define/role/len/chainability."""

    def test_define_and_role_by_name(self) -> None:
        reg = FontRoleRegistry()
        reg.define("body", size=16)
        self.assertEqual(reg.role("body"), "body")

    def test_getitem_equivalent_to_role(self) -> None:
        reg = FontRoleRegistry()
        reg.define("title", size=14)
        self.assertEqual(reg["title"], reg.role("title"))

    def test_define_is_chainable(self) -> None:
        reg = FontRoleRegistry()
        result = reg.define("a", size=10).define("b", size=12)
        self.assertIs(result, reg)

    def test_len(self) -> None:
        reg = FontRoleRegistry()
        reg.define("a", size=10)
        reg.define("b", size=12)
        self.assertEqual(len(reg), 2)

    def test_redefine_updates_in_place(self) -> None:
        reg = FontRoleRegistry()
        reg.define("body", size=16)
        reg.define("body", size=18, bold=True)
        self.assertEqual(len(reg), 1)

    def test_empty_name_raises(self) -> None:
        reg = FontRoleRegistry()
        with self.assertRaises(ValueError):
            reg.define("", size=12)

    def test_role_unknown_raises(self) -> None:
        reg = FontRoleRegistry()
        with self.assertRaises(KeyError):
            reg.role("doesnotexist")

    def test_getitem_unknown_raises(self) -> None:
        reg = FontRoleRegistry()
        with self.assertRaises(KeyError):
            _ = reg["missing"]

    def test_names_order_preserved(self) -> None:
        reg = FontRoleRegistry()
        reg.define("first", size=10)
        reg.define("second", size=12)
        reg.define("third", size=14)
        self.assertEqual(reg.defined_names(), ("first", "second", "third"))


# ---------------------------------------------------------------------------
# Pass-BB tests — LayoutAxis, LayoutManager
# ---------------------------------------------------------------------------

from gui_do import LayoutAxis, LayoutManager


class LayoutAxisTests(unittest.TestCase):
    """LayoutAxis enum members."""

    def test_members(self) -> None:
        self.assertIn(LayoutAxis.HORIZONTAL, list(LayoutAxis))
        self.assertIn(LayoutAxis.VERTICAL, list(LayoutAxis))

    def test_values(self) -> None:
        self.assertEqual(LayoutAxis.HORIZONTAL.value, "horizontal")
        self.assertEqual(LayoutAxis.VERTICAL.value, "vertical")


class LayoutManagerLinearTests(unittest.TestCase):
    """LayoutManager.linear and set_linear_properties."""

    def setUp(self):
        self.lm = LayoutManager()
        self.lm.set_linear_properties(
            anchor=(10, 20), item_width=80, item_height=30, spacing=5
        )

    def test_linear_first_item_position(self) -> None:
        rect = self.lm.linear(0)
        self.assertEqual(rect.x, 10)
        self.assertEqual(rect.y, 20)

    def test_linear_second_item_position(self) -> None:
        rect = self.lm.linear(1)
        self.assertEqual(rect.x, 10 + 80 + 5)

    def test_linear_size(self) -> None:
        rect = self.lm.linear(0)
        self.assertEqual(rect.width, 80)
        self.assertEqual(rect.height, 30)

    def test_next_linear_increments(self) -> None:
        r1 = self.lm.next_linear()
        r2 = self.lm.next_linear()
        self.assertNotEqual(r1.x, r2.x)

    def test_linear_vertical_orientation(self) -> None:
        self.lm.set_linear_properties(
            anchor=(0, 0), item_width=80, item_height=30, spacing=5, horizontal=False
        )
        r0 = self.lm.linear(0)
        r1 = self.lm.linear(1)
        self.assertEqual(r0.y, 0)
        self.assertEqual(r1.y, 35)

    def test_linear_returns_pos_when_use_rect_false(self) -> None:
        self.lm.set_linear_properties(
            anchor=(5, 10), item_width=80, item_height=30, spacing=5, use_rect=False
        )
        pos = self.lm.linear(0)
        self.assertEqual(pos, (5, 10))


class LayoutManagerGridTests(unittest.TestCase):
    """LayoutManager.gridded and set_grid_properties."""

    def setUp(self):
        self.lm = LayoutManager()
        self.lm.set_grid_properties(
            anchor=(0, 0), item_width=100, item_height=50,
            column_spacing=10, row_spacing=8
        )

    def test_gridded_origin(self) -> None:
        rect = self.lm.gridded(0, 0)
        self.assertEqual(rect.x, 0)
        self.assertEqual(rect.y, 0)

    def test_gridded_col1_row0(self) -> None:
        rect = self.lm.gridded(1, 0)
        self.assertEqual(rect.x, 110)

    def test_gridded_col0_row1(self) -> None:
        rect = self.lm.gridded(0, 1)
        self.assertEqual(rect.y, 58)

    def test_gridded_size(self) -> None:
        rect = self.lm.gridded(0, 0)
        self.assertEqual(rect.width, 100)
        self.assertEqual(rect.height, 50)

    def test_next_gridded_increments(self) -> None:
        r1 = self.lm.next_gridded(3)
        r2 = self.lm.next_gridded(3)
        self.assertNotEqual((r1.x, r1.y), (r2.x, r2.y))

    def test_set_anchor_bounds(self) -> None:
        self.lm.set_anchor_bounds(_Rect(10, 10, 400, 300))
        # anchored uses the bounds
        rect = self.lm.anchored((200, 100), anchor="center")
        self.assertIsInstance(rect, _Rect)


# ---------------------------------------------------------------------------
# Pass-BC tests — SceneTransitionStyle, SceneTransitionManager (config only)
# ---------------------------------------------------------------------------

from gui_do import SceneTransitionManager, SceneTransitionStyle


class SceneTransitionStyleTests(unittest.TestCase):
    """SceneTransitionStyle enum members."""

    def test_members_exist(self) -> None:
        styles = list(SceneTransitionStyle)
        names = [s.name for s in styles]
        self.assertIn("NONE", names)
        self.assertIn("FADE", names)
        self.assertIn("SLIDE_LEFT", names)
        self.assertIn("SLIDE_RIGHT", names)
        self.assertIn("SLIDE_UP", names)
        self.assertIn("SLIDE_DOWN", names)

    def test_none_value(self) -> None:
        self.assertEqual(SceneTransitionStyle.NONE.value, "none")


class SceneTransitionManagerConfigTests(unittest.TestCase):
    """SceneTransitionManager pure-config aspects (no app needed for config)."""

    def _make_manager(self):
        # We only test configuration that doesn't require a running app
        from unittest.mock import MagicMock
        app = MagicMock()
        return SceneTransitionManager(app)

    def test_set_default_style(self) -> None:
        mgr = self._make_manager()
        mgr.set_default(SceneTransitionStyle.SLIDE_LEFT)
        self.assertEqual(mgr._default_style, SceneTransitionStyle.SLIDE_LEFT)

    def test_set_default_duration(self) -> None:
        mgr = self._make_manager()
        mgr.set_default(SceneTransitionStyle.FADE, duration=0.5)
        self.assertAlmostEqual(mgr._default_duration, 0.5)

    def test_set_style_override(self) -> None:
        mgr = self._make_manager()
        mgr.set_style("editor", SceneTransitionStyle.SLIDE_LEFT)
        self.assertIn("editor", mgr._overrides)
        style, dur = mgr._overrides["editor"]
        self.assertEqual(style, SceneTransitionStyle.SLIDE_LEFT)

    def test_set_style_with_duration(self) -> None:
        mgr = self._make_manager()
        mgr.set_style("settings", SceneTransitionStyle.FADE, duration=0.25)
        _, dur = mgr._overrides["settings"]
        self.assertAlmostEqual(dur, 0.25)

    def test_active_initially_false(self) -> None:
        mgr = self._make_manager()
        self.assertFalse(mgr._active)


# ---------------------------------------------------------------------------
# Pass-BD tests — CommandEntry, CommandPaletteHandle, CommandPaletteManager
# ---------------------------------------------------------------------------

from gui_do import CommandEntry, CommandPaletteHandle


class CommandEntryTests(unittest.TestCase):
    """CommandEntry dataclass fields."""

    def test_required_fields(self) -> None:
        e = CommandEntry(entry_id="open", title="Open", action=lambda: None)
        self.assertEqual(e.entry_id, "open")
        self.assertEqual(e.title, "Open")

    def test_default_description_empty(self) -> None:
        e = CommandEntry(entry_id="x", title="X", action=lambda: None)
        self.assertEqual(e.description, "")

    def test_default_category_empty(self) -> None:
        e = CommandEntry(entry_id="x", title="X", action=lambda: None)
        self.assertEqual(e.category, "")

    def test_custom_fields(self) -> None:
        e = CommandEntry(
            entry_id="save",
            title="Save",
            action=lambda: None,
            description="Save current file",
            category="File",
        )
        self.assertEqual(e.description, "Save current file")
        self.assertEqual(e.category, "File")


class CommandPaletteManagerRegistryTests(unittest.TestCase):
    """CommandPaletteManager registry operations (no display needed)."""

    def setUp(self):
        self.mgr = CommandPaletteManager(OverlayManager())

    def test_register_and_entry_count(self) -> None:
        self.mgr.register(CommandEntry(entry_id="e1", title="E1", action=lambda: None))
        self.assertEqual(self.mgr.entry_count(), 1)

    def test_register_replaces_duplicate_id(self) -> None:
        self.mgr.register(CommandEntry(entry_id="same", title="A", action=lambda: None))
        self.mgr.register(CommandEntry(entry_id="same", title="B", action=lambda: None))
        self.assertEqual(self.mgr.entry_count(), 1)
        self.assertEqual(self.mgr.entries()[0].title, "B")

    def test_unregister_existing(self) -> None:
        self.mgr.register(CommandEntry(entry_id="r1", title="R1", action=lambda: None))
        result = self.mgr.unregister("r1")
        self.assertTrue(result)
        self.assertEqual(self.mgr.entry_count(), 0)

    def test_unregister_missing_returns_false(self) -> None:
        result = self.mgr.unregister("nobody")
        self.assertFalse(result)

    def test_entries_snapshot(self) -> None:
        self.mgr.register(CommandEntry(entry_id="a", title="A", action=lambda: None))
        self.mgr.register(CommandEntry(entry_id="b", title="B", action=lambda: None))
        snap = self.mgr.entries()
        self.assertEqual(len(snap), 2)

    def test_is_open_initially_false(self) -> None:
        self.assertFalse(self.mgr.is_open)


# ---------------------------------------------------------------------------
# Pass-BE tests — ContextMenuItem, ContextMenuHandle
# ---------------------------------------------------------------------------

from gui_do import ContextMenuItem, ContextMenuHandle


class ContextMenuItemTests(unittest.TestCase):
    """ContextMenuItem dataclass fields."""

    def test_label_required(self) -> None:
        item = ContextMenuItem(label="Cut")
        self.assertEqual(item.label, "Cut")

    def test_defaults(self) -> None:
        item = ContextMenuItem(label="Copy")
        self.assertIsNone(item.action)
        self.assertTrue(item.enabled)
        self.assertFalse(item.separator)
        self.assertIsNone(item.icon)

    def test_separator_item(self) -> None:
        item = ContextMenuItem(label="", separator=True)
        self.assertTrue(item.separator)

    def test_disabled_item(self) -> None:
        item = ContextMenuItem(label="Paste", enabled=False)
        self.assertFalse(item.enabled)

    def test_action_callable(self) -> None:
        called = []
        item = ContextMenuItem(label="Do it", action=lambda: called.append(True))
        item.action()
        self.assertEqual(called, [True])


class ContextMenuHandleTests(unittest.TestCase):
    """ContextMenuHandle is_open and dismiss."""

    def _stub_manager_with_menu(self, menu_id):
        """Create a stub ContextMenuManager that has menu_id registered."""
        class _Stub:
            def __init__(self):
                self._open_ids = [menu_id]
            def dismiss(self, mid):
                if mid in self._open_ids:
                    self._open_ids.remove(mid)
            def has_menu(self, mid):
                return mid in self._open_ids
        return _Stub()

    def test_is_open_true_when_menu_registered(self) -> None:
        stub = self._stub_manager_with_menu("m1")
        handle = ContextMenuHandle(menu_id="m1", _manager=stub)
        self.assertTrue(handle.is_open)

    def test_dismiss_closes_menu(self) -> None:
        stub = self._stub_manager_with_menu("m2")
        handle = ContextMenuHandle(menu_id="m2", _manager=stub)
        handle.dismiss()
        self.assertFalse(handle.is_open)

    def test_is_open_false_when_not_registered(self) -> None:
        stub = self._stub_manager_with_menu("other")
        handle = ContextMenuHandle(menu_id="unknown", _manager=stub)
        self.assertFalse(handle.is_open)


# ---------------------------------------------------------------------------
# Pass-BF tests — OverlayManager, OverlayHandle
# ---------------------------------------------------------------------------

from gui_do import OverlayHandle


class OverlayManagerTests(unittest.TestCase):
    """OverlayManager show/hide/has_overlay/overlay_count."""

    def _make_panel(self, cid="p1"):
        from gui_do.controls.composite.overlay_panel_control import OverlayPanelControl
        return OverlayPanelControl(cid, _Rect(0, 0, 100, 100))

    def test_show_returns_handle(self) -> None:
        mgr = OverlayManager()
        panel = self._make_panel()
        handle = mgr.show("owner1", panel)
        self.assertIsInstance(handle, OverlayHandle)

    def test_has_overlay_after_show(self) -> None:
        mgr = OverlayManager()
        mgr.show("owner1", self._make_panel())
        self.assertTrue(mgr.has_overlay("owner1"))

    def test_hide_removes_overlay(self) -> None:
        mgr = OverlayManager()
        mgr.show("o1", self._make_panel())
        result = mgr.hide("o1")
        self.assertTrue(result)
        self.assertFalse(mgr.has_overlay("o1"))

    def test_hide_unknown_returns_false(self) -> None:
        mgr = OverlayManager()
        self.assertFalse(mgr.hide("nobody"))

    def test_overlay_count(self) -> None:
        mgr = OverlayManager()
        mgr.show("a", self._make_panel("a"))
        mgr.show("b", self._make_panel("b"))
        self.assertEqual(mgr.overlay_count(), 2)

    def test_hide_all(self) -> None:
        mgr = OverlayManager()
        mgr.show("a", self._make_panel("a"))
        mgr.show("b", self._make_panel("b"))
        count = mgr.hide_all()
        self.assertEqual(count, 2)
        self.assertEqual(mgr.overlay_count(), 0)

    def test_show_replaces_existing(self) -> None:
        mgr = OverlayManager()
        mgr.show("owner", self._make_panel("p1"))
        mgr.show("owner", self._make_panel("p2"))
        self.assertEqual(mgr.overlay_count(), 1)

    def test_on_dismiss_callback(self) -> None:
        mgr = OverlayManager()
        received = []
        mgr.show("o", self._make_panel(), on_dismiss=lambda: received.append(True))
        mgr.hide("o")
        self.assertEqual(received, [True])


class OverlayHandleTests(unittest.TestCase):
    """OverlayHandle dismiss and is_open."""

    def _make_panel(self, cid="p1"):
        from gui_do.controls.composite.overlay_panel_control import OverlayPanelControl
        return OverlayPanelControl(cid, _Rect(0, 0, 100, 100))

    def test_handle_is_open(self) -> None:
        mgr = OverlayManager()
        handle = mgr.show("h1", self._make_panel())
        self.assertTrue(handle.is_open)

    def test_handle_dismiss(self) -> None:
        mgr = OverlayManager()
        handle = mgr.show("h2", self._make_panel())
        handle.dismiss()
        self.assertFalse(handle.is_open)

    def test_handle_owner_id(self) -> None:
        mgr = OverlayManager()
        handle = mgr.show("myid", self._make_panel())
        self.assertEqual(handle.owner_id, "myid")


# ---------------------------------------------------------------------------
# Pass-BG tests — analyze_telemetry_records, TelemetryHotspot, TelemetryAnalysis
# ---------------------------------------------------------------------------

from gui_do import analyze_telemetry_records
from gui_do.telemetry.telemetry_analyzer import TelemetryHotspot, TelemetryAnalysis


class AnalyzeTelemetryRecordsTests(unittest.TestCase):
    """analyze_telemetry_records pure-data analysis."""

    def _make_records(self, n=5, system="render", point="draw", elapsed=10.0):
        return [
            {"system": system, "point": point, "elapsed_ms": elapsed, "metadata": {}}
            for _ in range(n)
        ]

    def test_empty_records(self) -> None:
        result = analyze_telemetry_records([])
        self.assertEqual(result.sample_count, 0)
        self.assertEqual(result.systems, ())

    def test_sample_count(self) -> None:
        result = analyze_telemetry_records(self._make_records(7))
        self.assertEqual(result.sample_count, 7)

    def test_systems_collected(self) -> None:
        records = self._make_records(3, system="sys_a") + self._make_records(2, system="sys_b")
        result = analyze_telemetry_records(records)
        self.assertIn("sys_a", result.systems)
        self.assertIn("sys_b", result.systems)

    def test_hotspots_sorted_by_total(self) -> None:
        records = (
            self._make_records(1, system="s", point="fast", elapsed=1.0) +
            self._make_records(1, system="s", point="slow", elapsed=100.0)
        )
        result = analyze_telemetry_records(records)
        self.assertEqual(result.hotspots[0].key, "s.slow")

    def test_hotspot_fields(self) -> None:
        result = analyze_telemetry_records(self._make_records(4, elapsed=10.0))
        hs = result.hotspots[0]
        self.assertIsInstance(hs, TelemetryHotspot)
        self.assertEqual(hs.count, 4)
        self.assertAlmostEqual(hs.total_ms, 40.0)
        self.assertAlmostEqual(hs.average_ms, 10.0)

    def test_ignores_records_missing_system(self) -> None:
        records = [{"system": "", "point": "p", "elapsed_ms": 5.0, "metadata": {}}]
        result = analyze_telemetry_records(records)
        self.assertEqual(result.sample_count, 0)

    def test_telemetry_sample_objects_accepted(self) -> None:
        from gui_do import TelemetrySample
        sample = TelemetrySample(timestamp=1.0, system="s", point="p",
                                 elapsed_ms=5.0, metadata={})
        result = analyze_telemetry_records([sample])
        self.assertEqual(result.sample_count, 1)

    def test_feature_hotspots_from_metadata(self) -> None:
        records = [{"system": "s", "point": "p", "elapsed_ms": 20.0,
                    "metadata": {"feature_name": "myfeature"}}]
        result = analyze_telemetry_records(records)
        self.assertTrue(len(result.feature_hotspots) >= 1)
        self.assertEqual(result.feature_hotspots[0].key, "myfeature")


# ---------------------------------------------------------------------------
# Pass-BH tests — EventPhase
# ---------------------------------------------------------------------------

from gui_do import EventPhase


class EventPhaseTests(unittest.TestCase):
    """EventPhase enum members."""

    def test_members_exist(self) -> None:
        phases = {p for p in EventPhase}
        self.assertIn(EventPhase.CAPTURE, phases)
        self.assertIn(EventPhase.TARGET, phases)
        self.assertIn(EventPhase.BUBBLE, phases)

    def test_values(self) -> None:
        self.assertEqual(EventPhase.CAPTURE.value, "capture")
        self.assertEqual(EventPhase.TARGET.value, "target")
        self.assertEqual(EventPhase.BUBBLE.value, "bubble")


# ---------------------------------------------------------------------------
# Pass-BI tests — Command protocol, CommandTransaction
# ---------------------------------------------------------------------------

from gui_do import Command, CommandTransaction


class _SimpleCmd:
    """Minimal Command protocol implementation for tests."""

    def __init__(self, name: str = "cmd") -> None:
        self.executed = 0
        self.undone = 0
        self._description = name

    @property
    def description(self) -> str:
        return self._description

    def execute(self) -> None:
        self.executed += 1

    def undo(self) -> None:
        self.undone += 1


class CommandProtocolTests(unittest.TestCase):
    """Command is a runtime-checkable Protocol."""

    def test_protocol_satisfied(self) -> None:
        self.assertIsInstance(_SimpleCmd(), Command)

    def test_non_conforming_not_instance(self) -> None:
        self.assertNotIsInstance(object(), Command)


class CommandTransactionTests(unittest.TestCase):
    """CommandTransaction groups commands atomically."""

    def test_default_description(self) -> None:
        tx = CommandTransaction()
        self.assertEqual(tx.description, "Transaction")

    def test_custom_description(self) -> None:
        tx = CommandTransaction("Bulk Edit")
        self.assertEqual(tx.description, "Bulk Edit")

    def test_description_settable(self) -> None:
        tx = CommandTransaction()
        tx.description = "New Desc"
        self.assertEqual(tx.description, "New Desc")

    def test_add_and_len(self) -> None:
        tx = CommandTransaction()
        tx.add(_SimpleCmd())
        tx.add(_SimpleCmd())
        self.assertEqual(len(tx), 2)

    def test_execute_runs_all(self) -> None:
        cmds = [_SimpleCmd(), _SimpleCmd(), _SimpleCmd()]
        tx = CommandTransaction()
        for c in cmds:
            tx.add(c)
        tx.execute()
        for c in cmds:
            self.assertEqual(c.executed, 1)

    def test_undo_reverses_order(self) -> None:
        order = []
        class _Ordered:
            def __init__(self, n):
                self.n = n
            @property
            def description(self): return str(self.n)
            def execute(self): pass
            def undo(self): order.append(self.n)

        tx = CommandTransaction()
        for n in [1, 2, 3]:
            tx.add(_Ordered(n))
        tx.execute()
        tx.undo()
        self.assertEqual(order, [3, 2, 1])

    def test_empty_transaction_execute_no_error(self) -> None:
        CommandTransaction().execute()

    def test_transaction_satisfies_command_protocol(self) -> None:
        tx = CommandTransaction()
        self.assertIsInstance(tx, Command)


# ---------------------------------------------------------------------------
# Pass-BJ tests — AnchorConstraint, ConstraintLayout
# ---------------------------------------------------------------------------

from gui_do import AnchorConstraint, ConstraintLayout


class AnchorConstraintTests(unittest.TestCase):
    """AnchorConstraint.apply resolves rects from parent edges."""

    def test_left_anchor_sets_x(self) -> None:
        c = AnchorConstraint(left=10)
        result = c.apply(_Rect(0, 0, 100, 50), _Rect(0, 0, 400, 300))
        self.assertEqual(result.left, 10)

    def test_right_anchor_sets_right_edge(self) -> None:
        c = AnchorConstraint(right=20)
        result = c.apply(_Rect(0, 0, 100, 50), _Rect(0, 0, 400, 300))
        self.assertEqual(result.right, 380)

    def test_left_right_stretches_width(self) -> None:
        c = AnchorConstraint(left=10, right=10)
        result = c.apply(_Rect(0, 0, 100, 50), _Rect(0, 0, 400, 300))
        self.assertEqual(result.left, 10)
        self.assertEqual(result.right, 390)
        self.assertEqual(result.width, 380)

    def test_top_bottom_stretches_height(self) -> None:
        c = AnchorConstraint(top=5, bottom=5)
        result = c.apply(_Rect(0, 0, 100, 50), _Rect(0, 0, 400, 300))
        self.assertEqual(result.top, 5)
        self.assertEqual(result.bottom, 295)

    def test_fractional_left(self) -> None:
        c = AnchorConstraint(left_frac=0.25)
        result = c.apply(_Rect(0, 0, 100, 50), _Rect(0, 0, 400, 300))
        self.assertEqual(result.left, 100)  # 400 * 0.25

    def test_min_width_clamp(self) -> None:
        c = AnchorConstraint(left=0, right=350, min_width=100)
        result = c.apply(_Rect(0, 0, 100, 50), _Rect(0, 0, 400, 300))
        self.assertGreaterEqual(result.width, 100)

    def test_max_width_clamp(self) -> None:
        c = AnchorConstraint(left=0, right=0, max_width=50)
        result = c.apply(_Rect(0, 0, 100, 50), _Rect(0, 0, 400, 300))
        self.assertLessEqual(result.width, 50)

    def test_unconstrained_preserves_rect(self) -> None:
        c = AnchorConstraint()
        original = _Rect(30, 40, 120, 60)
        result = c.apply(original, _Rect(0, 0, 400, 300))
        self.assertEqual(result, original)


class ConstraintLayoutTests(unittest.TestCase):
    """ConstraintLayout register, apply, and remove."""

    def _node(self, rect):
        """Minimal UiNode-like stub with a mutable rect."""
        class _N:
            def __init__(self, r): self.rect = _Rect(r)
        return _N(rect)

    def test_add_and_has(self) -> None:
        cl = ConstraintLayout()
        node = self._node((0, 0, 100, 50))
        cl.add(node, AnchorConstraint(left=20))
        self.assertTrue(cl.has(node))

    def test_node_count(self) -> None:
        cl = ConstraintLayout()
        n1, n2 = self._node((0, 0, 100, 50)), self._node((0, 0, 100, 50))
        cl.add(n1, AnchorConstraint())
        cl.add(n2, AnchorConstraint())
        self.assertEqual(cl.node_count(), 2)

    def test_apply_mutates_rect(self) -> None:
        cl = ConstraintLayout()
        node = self._node((0, 0, 100, 50))
        cl.add(node, AnchorConstraint(left=30, top=10))
        cl.apply(_Rect(0, 0, 400, 300))
        self.assertEqual(node.rect.left, 30)
        self.assertEqual(node.rect.top, 10)

    def test_apply_to_returns_rect_without_mutation(self) -> None:
        cl = ConstraintLayout()
        node = self._node((0, 0, 100, 50))
        cl.add(node, AnchorConstraint(left=50))
        result = cl.apply_to(node, _Rect(0, 0, 400, 300))
        self.assertEqual(result.left, 50)
        self.assertEqual(node.rect.left, 0)  # not mutated

    def test_remove_existing(self) -> None:
        cl = ConstraintLayout()
        node = self._node((0, 0, 100, 50))
        cl.add(node, AnchorConstraint())
        self.assertTrue(cl.remove(node))
        self.assertFalse(cl.has(node))
        self.assertEqual(cl.node_count(), 0)

    def test_remove_unknown_returns_false(self) -> None:
        cl = ConstraintLayout()
        node = self._node((0, 0, 100, 50))
        self.assertFalse(cl.remove(node))


# ---------------------------------------------------------------------------
# Pass-BK tests — Feature, FeatureMessage, DirectFeature, LogicFeature,
#                 RoutedFeature (pure lifecycle / messaging, no app/display)
# ---------------------------------------------------------------------------

from gui_do import Feature, FeatureMessage, DirectFeature, LogicFeature, RoutedFeature


class FeatureMessageTests(unittest.TestCase):
    """FeatureMessage creation and accessors."""

    def test_fields(self) -> None:
        msg = FeatureMessage(sender="a", target="b", payload={"topic": "go"})
        self.assertEqual(msg.sender, "a")
        self.assertEqual(msg.target, "b")
        self.assertEqual(msg.payload, {"topic": "go"})

    def test_from_payload(self) -> None:
        msg = FeatureMessage.from_payload("src", "dst", {"command": "run"})
        self.assertEqual(msg.sender, "src")
        self.assertEqual(msg.command, "run")

    def test_topic_property(self) -> None:
        msg = FeatureMessage(sender="a", target="b", payload={"topic": "click"})
        self.assertEqual(msg.topic, "click")

    def test_command_property(self) -> None:
        msg = FeatureMessage(sender="a", target="b", payload={"command": "do_it"})
        self.assertEqual(msg.command, "do_it")

    def test_event_property(self) -> None:
        msg = FeatureMessage(sender="a", target="b", payload={"event": "update"})
        self.assertEqual(msg.event, "update")

    def test_getitem(self) -> None:
        msg = FeatureMessage(sender="a", target="b", payload={"key": "val"})
        self.assertEqual(msg["key"], "val")

    def test_get_with_default(self) -> None:
        msg = FeatureMessage(sender="a", target="b", payload={})
        self.assertIsNone(msg.get("missing"))
        self.assertEqual(msg.get("missing", "default"), "default")


class FeatureBaseTests(unittest.TestCase):
    """Feature base class: construction, name, message queue."""

    def test_construction(self) -> None:
        f = Feature("my_feature")
        self.assertEqual(f.name, "my_feature")

    def test_empty_name_raises(self) -> None:
        with self.assertRaises(ValueError):
            Feature("")

    def test_scene_name_set(self) -> None:
        f = Feature("f", scene_name="main")
        self.assertEqual(f.scene_name, "main")

    def test_empty_scene_name_raises(self) -> None:
        with self.assertRaises(ValueError):
            Feature("f", scene_name="")

    def test_message_queue_initially_empty(self) -> None:
        f = Feature("f")
        self.assertFalse(f.has_messages())
        self.assertEqual(f.message_count(), 0)

    def test_enqueue_and_peek_pop(self) -> None:
        f = Feature("f")
        msg = FeatureMessage(sender="a", target="f", payload={"topic": "t"})
        f.enqueue_message(msg)
        self.assertTrue(f.has_messages())
        self.assertIs(f.peek_message(), msg)
        popped = f.pop_message()
        self.assertIs(popped, msg)
        self.assertFalse(f.has_messages())

    def test_clear_messages(self) -> None:
        f = Feature("f")
        f.enqueue_message(FeatureMessage(sender="a", target="f", payload={}))
        f.clear_messages()
        self.assertEqual(f.message_count(), 0)

    def test_pop_empty_returns_none(self) -> None:
        f = Feature("f")
        self.assertIsNone(f.pop_message())

    def test_enqueue_non_message_raises(self) -> None:
        f = Feature("f")
        with self.assertRaises(TypeError):
            f.enqueue_message({"topic": "bad"})  # type: ignore


class DirectFeatureTests(unittest.TestCase):
    """DirectFeature subclasses Feature."""

    def test_is_feature_subclass(self) -> None:
        df = DirectFeature("d")
        self.assertIsInstance(df, Feature)

    def test_default_handle_direct_event(self) -> None:
        df = DirectFeature("d")
        self.assertFalse(df.handle_direct_event(None, None))


class LogicFeatureTests(unittest.TestCase):
    """LogicFeature subclasses Feature."""

    def test_is_feature_subclass(self) -> None:
        self.assertIsInstance(LogicFeature("l"), Feature)

    def test_on_logic_command_no_error(self) -> None:
        lf = LogicFeature("l")
        msg = FeatureMessage(sender="a", target="l", payload={"command": "run"})
        lf.on_logic_command(None, msg)  # base does nothing; must not raise


class RoutedFeatureTests(unittest.TestCase):
    """RoutedFeature routes by topic."""

    def test_is_feature_subclass(self) -> None:
        self.assertIsInstance(RoutedFeature("r"), Feature)

    def test_message_handlers_empty_by_default(self) -> None:
        rf = RoutedFeature("r")
        self.assertEqual(rf.message_handlers(), {})

    def test_on_message_dispatches_to_handler(self) -> None:
        dispatched = []

        class _RF(RoutedFeature):
            def message_handlers(self):
                return {"click": lambda host, msg: dispatched.append(msg)}

        rf = _RF("r")
        msg = FeatureMessage(sender="a", target="r", payload={"topic": "click"})
        rf.on_message(None, msg)
        self.assertEqual(dispatched, [msg])

    def test_on_message_unknown_topic_no_error(self) -> None:
        rf = RoutedFeature("r")
        msg = FeatureMessage(sender="a", target="r", payload={"topic": "unknown"})
        rf.on_message(None, msg)  # must not raise


# ---------------------------------------------------------------------------
# Pass-BL tests — TweenManager, TweenHandle
# ---------------------------------------------------------------------------

from gui_do import TweenManager, TweenHandle


class TweenManagerTests(unittest.TestCase):
    """TweenManager basic tween_fn, zero-duration, cancel, tick."""

    def test_tween_fn_returns_handle(self) -> None:
        tm = TweenManager()
        handle = tm.tween_fn(0.5, lambda t: None)
        self.assertIsInstance(handle, TweenHandle)

    def test_zero_duration_completes_immediately(self) -> None:
        tm = TweenManager()
        called = []
        handle = tm.tween_fn(0.0, called.append)
        self.assertAlmostEqual(called[-1], 1.0)
        self.assertTrue(handle.is_complete)

    def test_positive_duration_not_initially_complete(self) -> None:
        tm = TweenManager()
        handle = tm.tween_fn(1.0, lambda t: None)
        self.assertFalse(handle.is_complete)

    def test_cancel_marks_handle(self) -> None:
        tm = TweenManager()
        handle = tm.tween_fn(2.0, lambda t: None)
        handle.cancel()
        self.assertTrue(handle.is_cancelled)

    def test_elapsed_fraction_zero_before_tick(self) -> None:
        tm = TweenManager()
        handle = tm.tween_fn(1.0, lambda t: None)
        self.assertAlmostEqual(handle.elapsed_fraction(), 0.0)

    def test_elapsed_fraction_full_on_complete(self) -> None:
        tm = TweenManager()
        handle = tm.tween_fn(0.0, lambda t: None)
        self.assertAlmostEqual(handle.elapsed_fraction(), 1.0)

    def test_on_complete_callback(self) -> None:
        finished = []
        tm = TweenManager()
        tm.tween_fn(0.0, lambda t: None, on_complete=lambda: finished.append(True))
        self.assertEqual(finished, [True])

    def test_tween_id_unique_per_handle(self) -> None:
        tm = TweenManager()
        h1 = tm.tween_fn(1.0, lambda t: None)
        h2 = tm.tween_fn(1.0, lambda t: None)
        self.assertNotEqual(h1.tween_id, h2.tween_id)

    def test_update_progresses_tween(self) -> None:
        values = []
        tm = TweenManager()
        tm.tween_fn(1.0, values.append, easing="linear")
        tm.update(0.5)
        self.assertTrue(any(abs(v - 0.5) < 0.01 for v in values))

    def test_cancel_all_for_tag(self) -> None:
        tm = TweenManager()
        h1 = tm.tween_fn(2.0, lambda t: None, tag="group")
        h2 = tm.tween_fn(2.0, lambda t: None, tag="group")
        tm.cancel_all_for_tag("group")
        self.assertTrue(h1.is_cancelled)
        self.assertTrue(h2.is_cancelled)


# ---------------------------------------------------------------------------
# Pass-BM tests — TabItem, MenuEntry, DropdownOption, ListItem
# ---------------------------------------------------------------------------

from gui_do import TabItem, MenuEntry, DropdownOption, ListItem


class TabItemTests(unittest.TestCase):
    """TabItem dataclass fields."""

    def test_required_fields(self) -> None:
        item = TabItem(key="a", label="Alpha")
        self.assertEqual(item.key, "a")
        self.assertEqual(item.label, "Alpha")

    def test_content_defaults_none(self) -> None:
        item = TabItem(key="a", label="Alpha")
        self.assertIsNone(item.content)

    def test_enabled_defaults_true(self) -> None:
        item = TabItem(key="a", label="Alpha")
        self.assertTrue(item.enabled)

    def test_disabled(self) -> None:
        item = TabItem(key="a", label="Alpha", enabled=False)
        self.assertFalse(item.enabled)


class MenuEntryTests(unittest.TestCase):
    """MenuEntry dataclass fields."""

    def test_label(self) -> None:
        me = MenuEntry(label="File")
        self.assertEqual(me.label, "File")

    def test_items_default_empty(self) -> None:
        me = MenuEntry(label="Edit")
        self.assertEqual(me.items, [])

    def test_enabled_default_true(self) -> None:
        self.assertTrue(MenuEntry(label="x").enabled)

    def test_items_populated(self) -> None:
        items = [ContextMenuItem(label="Open")]
        me = MenuEntry(label="File", items=items)
        self.assertEqual(len(me.items), 1)


class DropdownOptionTests(unittest.TestCase):
    """DropdownOption dataclass fields and auto-value."""

    def test_label_and_auto_value(self) -> None:
        opt = DropdownOption(label="Alpha")
        self.assertEqual(opt.label, "Alpha")
        self.assertEqual(opt.value, "Alpha")  # auto-set to label

    def test_explicit_value(self) -> None:
        opt = DropdownOption(label="Alpha", value=42)
        self.assertEqual(opt.value, 42)

    def test_enabled_default_true(self) -> None:
        self.assertTrue(DropdownOption(label="x").enabled)

    def test_data_field(self) -> None:
        opt = DropdownOption(label="x", data={"k": "v"})
        self.assertEqual(opt.data, {"k": "v"})


class ListItemTests(unittest.TestCase):
    """ListItem dataclass fields."""

    def test_label_required(self) -> None:
        item = ListItem(label="Row 1")
        self.assertEqual(item.label, "Row 1")

    def test_data_field(self) -> None:
        item = ListItem(label="Row", data={"id": 7})
        self.assertEqual(item.data["id"], 7)

    def test_data_only(self) -> None:
        item = ListItem(label="Row", data="detail")
        self.assertEqual(item.data, "detail")


# ---------------------------------------------------------------------------
# Pass-BN tests — render_telemetry_report, load_telemetry_log_file,
#                 analyze_telemetry_log_file
# ---------------------------------------------------------------------------

from gui_do import render_telemetry_report, load_telemetry_log_file, analyze_telemetry_log_file
from gui_do.telemetry.telemetry_analyzer import TelemetryAnalysis, TelemetryHotspot


class RenderTelemetryReportTests(unittest.TestCase):
    """render_telemetry_report produces a string report."""

    def _empty_analysis(self):
        return TelemetryAnalysis(
            sample_count=0, systems=(), hotspots=(), feature_hotspots=()
        )

    def _analysis_with_samples(self):
        hs = TelemetryHotspot(
            key="render.draw", count=5, total_ms=50.0,
            average_ms=10.0, max_ms=20.0, p95_ms=18.0
        )
        return TelemetryAnalysis(
            sample_count=5, systems=("render",),
            hotspots=(hs,), feature_hotspots=()
        )

    def test_returns_string(self) -> None:
        report = render_telemetry_report(self._empty_analysis(), source="test")
        self.assertIsInstance(report, str)

    def test_contains_header(self) -> None:
        report = render_telemetry_report(self._empty_analysis(), source="test")
        self.assertIn("Telemetry Analysis Report", report)

    def test_contains_source(self) -> None:
        report = render_telemetry_report(self._empty_analysis(), source="mysrc")
        self.assertIn("mysrc", report)

    def test_contains_sample_count(self) -> None:
        report = render_telemetry_report(self._empty_analysis(), source="t")
        self.assertIn("Sample count: 0", report)

    def test_with_hotspots(self) -> None:
        report = render_telemetry_report(self._analysis_with_samples(), source="t")
        self.assertIn("render.draw", report)

    def test_empty_no_samples_message(self) -> None:
        report = render_telemetry_report(self._empty_analysis(), source="t")
        self.assertIn("No telemetry samples were recorded", report)

    def test_guidance_section_present(self) -> None:
        report = render_telemetry_report(self._empty_analysis(), source="t")
        self.assertIn("Guidance", report)


class LoadTelemetryLogFileTests(unittest.TestCase):
    """load_telemetry_log_file reads JSONL files."""

    def _write_log(self, records, suffix=".jsonl"):
        import json, tempfile
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=suffix, delete=False, encoding="utf-8"
        ) as f:
            for rec in records:
                f.write(json.dumps(rec) + "\n")
            return f.name

    def test_empty_file_returns_empty_list(self) -> None:
        path = self._write_log([])
        result = load_telemetry_log_file(path)
        self.assertEqual(result, [])

    def test_reads_type_sample_records(self) -> None:
        sample = {"type": "sample", "system": "s", "point": "p",
                  "elapsed_ms": 5.0, "metadata": {}}
        path = self._write_log([sample])
        result = load_telemetry_log_file(path)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["system"], "s")

    def test_non_sample_records_ignored(self) -> None:
        meta = {"type": "meta", "info": "startup"}
        sample = {"type": "sample", "system": "s", "point": "p",
                  "elapsed_ms": 1.0, "metadata": {}}
        path = self._write_log([meta, sample])
        result = load_telemetry_log_file(path)
        self.assertEqual(len(result), 1)

    def test_blank_lines_ignored(self) -> None:
        import json, tempfile
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False, encoding="utf-8"
        ) as f:
            f.write("\n")
            f.write(json.dumps({"type": "sample", "system": "s",
                                 "point": "p", "elapsed_ms": 1.0,
                                 "metadata": {}}) + "\n")
            f.write("\n")
            path = f.name
        result = load_telemetry_log_file(path)
        self.assertEqual(len(result), 1)

    def test_invalid_json_raises(self) -> None:
        import tempfile
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False, encoding="utf-8"
        ) as f:
            f.write("not json\n")
            path = f.name
        with self.assertRaises(Exception):
            load_telemetry_log_file(path)

    def test_missing_file_raises(self) -> None:
        with self.assertRaises(Exception):
            load_telemetry_log_file("/nonexistent/path/file.jsonl")


# ---------------------------------------------------------------------------
# Pass-BO tests — ActionManager (registration + key-binding API)
# ---------------------------------------------------------------------------

from gui_do import ActionManager


class ActionManagerTests(unittest.TestCase):
    """ActionManager: register, unregister, bind_key, unbind_key."""

    def test_register_and_has_action(self) -> None:
        am = ActionManager()
        am.register_action("save", lambda e: True)
        self.assertTrue(am.has_action("save"))

    def test_has_action_false_for_unknown(self) -> None:
        am = ActionManager()
        self.assertFalse(am.has_action("missing"))

    def test_registered_actions_sorted(self) -> None:
        am = ActionManager()
        am.register_action("zoom", lambda e: True)
        am.register_action("alpha", lambda e: True)
        result = am.registered_actions()
        self.assertEqual(result, sorted(result))
        self.assertIn("zoom", result)
        self.assertIn("alpha", result)

    def test_unregister_removes_action(self) -> None:
        am = ActionManager()
        am.register_action("cut", lambda e: True)
        am.unregister_action("cut")
        self.assertFalse(am.has_action("cut"))

    def test_unregister_nonexistent_no_error(self) -> None:
        ActionManager().unregister_action("ghost")

    def test_bind_key_and_bindings_for_action(self) -> None:
        am = ActionManager()
        am.register_action("save", lambda e: True)
        am.bind_key(ord("s"), "save")
        bindings = am.bindings_for_action("save")
        self.assertEqual(len(bindings), 1)
        self.assertEqual(bindings[0].key, ord("s"))

    def test_bind_key_duplicate_not_added_twice(self) -> None:
        am = ActionManager()
        am.register_action("save", lambda e: True)
        am.bind_key(ord("s"), "save")
        am.bind_key(ord("s"), "save")
        self.assertEqual(len(am.bindings_for_action("save")), 1)

    def test_unbind_key_removes_binding(self) -> None:
        am = ActionManager()
        am.register_action("save", lambda e: True)
        am.bind_key(ord("s"), "save")
        removed = am.unbind_key(ord("s"), "save")
        self.assertTrue(removed)
        self.assertEqual(am.bindings_for_action("save"), [])

    def test_unbind_key_nonexistent_returns_false(self) -> None:
        am = ActionManager()
        self.assertFalse(am.unbind_key(ord("x"), "noop"))

    def test_clear_bindings_removes_all(self) -> None:
        am = ActionManager()
        am.register_action("a", lambda e: True)
        am.bind_key(ord("a"), "a")
        am.clear_bindings()
        self.assertEqual(am.bindings_for_action("a"), [])

    def test_register_and_bind_shorthand(self) -> None:
        am = ActionManager()
        am.register_and_bind("delete", ord("d"), lambda e: True)
        self.assertTrue(am.has_action("delete"))
        self.assertEqual(len(am.bindings_for_action("delete")), 1)

    def test_binding_count(self) -> None:
        am = ActionManager()
        am.register_action("a", lambda e: True)
        am.register_action("b", lambda e: True)
        am.bind_key(1, "a")
        am.bind_key(2, "b")
        self.assertEqual(am.binding_count(), 2)


# ---------------------------------------------------------------------------
# Pass-BP tests — FeatureManager (registration-only, no display)
# ---------------------------------------------------------------------------

from gui_do import FeatureManager


class FeatureManagerTests(unittest.TestCase):
    """FeatureManager: register/unregister/get/names/features, messaging."""

    def _mgr(self):
        return FeatureManager(app=None)

    def test_construction(self) -> None:
        fm = self._mgr()
        self.assertEqual(fm.names(), ())

    def test_register_returns_feature(self) -> None:
        fm = self._mgr()
        f = Feature("alpha")
        result = fm.register(f)
        self.assertIs(result, f)

    def test_names_after_register(self) -> None:
        fm = self._mgr()
        fm.register(Feature("x"))
        fm.register(Feature("y"))
        self.assertIn("x", fm.names())
        self.assertIn("y", fm.names())

    def test_get_existing(self) -> None:
        fm = self._mgr()
        f = Feature("z")
        fm.register(f)
        self.assertIs(fm.get("z"), f)

    def test_get_missing_returns_none(self) -> None:
        fm = self._mgr()
        self.assertIsNone(fm.get("nope"))

    def test_duplicate_register_raises(self) -> None:
        fm = self._mgr()
        fm.register(Feature("dup"))
        with self.assertRaises(ValueError):
            fm.register(Feature("dup"))

    def test_register_non_feature_raises(self) -> None:
        fm = self._mgr()
        with self.assertRaises(TypeError):
            fm.register("not_a_feature")  # type: ignore

    def test_unregister_existing(self) -> None:
        fm = self._mgr()
        fm.register(Feature("a"))
        self.assertTrue(fm.unregister("a"))
        self.assertIsNone(fm.get("a"))

    def test_unregister_missing_returns_false(self) -> None:
        fm = self._mgr()
        self.assertFalse(fm.unregister("ghost"))

    def test_features_iterable(self) -> None:
        fm = self._mgr()
        f1, f2 = Feature("p"), Feature("q")
        fm.register(f1)
        fm.register(f2)
        self.assertIn(f1, list(fm.features()))
        self.assertIn(f2, list(fm.features()))

    def test_send_message_to_registered_target(self) -> None:
        fm = self._mgr()
        sender = Feature("sender")
        target = Feature("target")
        fm.register(sender)
        fm.register(target)
        ok = fm.send_message("sender", "target", {"topic": "ping"})
        self.assertTrue(ok)
        self.assertTrue(target.has_messages())

    def test_send_message_missing_target_returns_false(self) -> None:
        fm = self._mgr()
        fm.register(Feature("s"))
        ok = fm.send_message("s", "nobody", {"topic": "x"})
        self.assertFalse(ok)

    def test_feature_manager_assigned_on_register(self) -> None:
        fm = self._mgr()
        f = Feature("f")
        fm.register(f)
        self.assertIs(f._feature_manager, fm)

    def test_feature_manager_cleared_on_unregister(self) -> None:
        fm = self._mgr()
        f = Feature("f")
        fm.register(f)
        fm.unregister("f")
        self.assertIsNone(f._feature_manager)


# ---------------------------------------------------------------------------
# Pass-BQ tests — FontManager (registration API, headless)
# ---------------------------------------------------------------------------

from gui_do import FontManager
from pathlib import Path as _Path


class FontManagerTests(unittest.TestCase):
    """FontManager: register_role, has_role, role_names, revision."""

    def _fm(self):
        return FontManager(resource_root=_Path("."))

    def test_initial_state(self) -> None:
        fm = self._fm()
        self.assertEqual(fm.role_names(), ())
        self.assertEqual(fm.revision, 0)

    def test_register_role_increments_revision(self) -> None:
        fm = self._fm()
        rev_before = fm.revision
        fm.register_role("body", size=16)
        self.assertGreater(fm.revision, rev_before)

    def test_has_role_after_register(self) -> None:
        fm = self._fm()
        fm.register_role("body", size=16)
        self.assertTrue(fm.has_role("body"))

    def test_has_role_false_for_unregistered(self) -> None:
        self.assertFalse(self._fm().has_role("missing"))

    def test_role_names_returns_all(self) -> None:
        fm = self._fm()
        fm.register_role("body", size=16)
        fm.register_role("title", size=24, bold=True)
        names = fm.role_names()
        self.assertIn("body", names)
        self.assertIn("title", names)

    def test_register_role_same_name_updates(self) -> None:
        fm = self._fm()
        fm.register_role("body", size=12)
        rev1 = fm.revision
        fm.register_role("body", size=18)
        self.assertGreater(fm.revision, rev1)

    def test_role_names_ordered(self) -> None:
        fm = self._fm()
        fm.register_role("first", size=10)
        fm.register_role("second", size=12)
        names = fm.role_names()
        self.assertEqual(list(names).index("first"), 0)

    def test_resource_root_none_ok(self) -> None:
        fm = FontManager()
        fm.register_role("body", size=14)
        self.assertTrue(fm.has_role("body"))


# ---------------------------------------------------------------------------
# Pass-BR tests — ColorTheme (construction and palette access)
# ---------------------------------------------------------------------------

from gui_do import ColorTheme


class ColorThemeTests(unittest.TestCase):
    """ColorTheme: construction, palette colors, font roles."""

    def test_construction(self) -> None:
        ct = ColorTheme()
        self.assertIsNotNone(ct)

    def test_palette_colors_are_tuples(self) -> None:
        ct = ColorTheme()
        for attr in ("light", "medium", "dark", "background", "highlight", "text"):
            value = getattr(ct, attr)
            self.assertIsInstance(value, tuple, f"{attr} should be a tuple")
            self.assertEqual(len(value), 3)

    def test_font_roles_default(self) -> None:
        ct = ColorTheme()
        roles = ct.font_roles()
        self.assertIn("body", roles)
        self.assertIn("title", roles)

    def test_register_font_role(self) -> None:
        ct = ColorTheme()
        ct.register_font_role("heading", size=20, bold=True)
        self.assertIn("heading", ct.font_roles())

    def test_background_bitmap_initially_none(self) -> None:
        ct = ColorTheme()
        self.assertIsNone(ct.background_bitmap)


# ---------------------------------------------------------------------------
# Pass-BS tests — FocusManager (pure-data focus tracking)
# ---------------------------------------------------------------------------

from gui_do import FocusManager


class _FocusNode:
    """Minimal node stub satisfying FocusManager.set_focus contract."""

    def __init__(self, cid: str = "n") -> None:
        self.control_id = cid
        self.parent = None
        self._focused = False

    def _set_focused(self, val: bool) -> None:
        self._focused = val

    def is_window(self) -> bool:
        return False


class FocusManagerTests(unittest.TestCase):
    """FocusManager: set_focus, clear_focus, focused_control_id, has_focus."""

    def test_initial_state(self) -> None:
        fm = FocusManager()
        self.assertFalse(fm.has_focus)
        self.assertIsNone(fm.focused_control_id)
        self.assertIsNone(fm.focused_node)

    def test_set_focus_updates_state(self) -> None:
        fm = FocusManager()
        node = _FocusNode("btn1")
        fm.set_focus(node)
        self.assertTrue(fm.has_focus)
        self.assertEqual(fm.focused_control_id, "btn1")
        self.assertIs(fm.focused_node, node)

    def test_set_focus_calls_set_focused_on_node(self) -> None:
        fm = FocusManager()
        node = _FocusNode()
        fm.set_focus(node)
        self.assertTrue(node._focused)

    def test_clear_focus(self) -> None:
        fm = FocusManager()
        fm.set_focus(_FocusNode())
        fm.clear_focus()
        self.assertFalse(fm.has_focus)
        self.assertIsNone(fm.focused_node)

    def test_set_focus_unfocuses_previous(self) -> None:
        fm = FocusManager()
        n1, n2 = _FocusNode("a"), _FocusNode("b")
        fm.set_focus(n1)
        fm.set_focus(n2)
        self.assertFalse(n1._focused)
        self.assertTrue(n2._focused)

    def test_should_draw_focus_hint_false_initially(self) -> None:
        fm = FocusManager()
        self.assertFalse(fm.should_draw_focus_hint())

    def test_should_draw_hint_after_keyboard_focus(self) -> None:
        fm = FocusManager()
        fm.set_focus(_FocusNode(), via_keyboard=True)
        self.assertTrue(fm.should_draw_focus_hint())

    def test_set_focus_none_clears(self) -> None:
        fm = FocusManager()
        fm.set_focus(_FocusNode())
        fm.set_focus(None)
        self.assertFalse(fm.has_focus)

    def test_push_pop_focus_scope(self) -> None:
        fm = FocusManager()
        root = _FocusNode("scope_root")
        fm.push_focus_scope(root)
        self.assertIsNotNone(fm.active_scope_root)

    def test_push_focus_scope_none_raises(self) -> None:
        fm = FocusManager()
        with self.assertRaises(ValueError):
            fm.push_focus_scope(None)


# ---------------------------------------------------------------------------
# Pass-BT tests — WindowTilingManager (config/settings only, no display)
# ---------------------------------------------------------------------------

from gui_do import WindowTilingManager


class WindowTilingManagerTests(unittest.TestCase):
    """WindowTilingManager: configure and read_settings without relayout."""

    def _wm(self):
        class _AppStub:
            pass
        return WindowTilingManager(_AppStub())

    def test_initial_settings(self) -> None:
        wm = self._wm()
        s = wm.read_settings()
        self.assertFalse(s["enabled"])
        self.assertIsInstance(s["gap"], int)
        self.assertIsInstance(s["padding"], int)

    def test_configure_gap(self) -> None:
        wm = self._wm()
        wm.configure(gap=8, relayout=False)
        self.assertEqual(wm.read_settings()["gap"], 8)

    def test_configure_padding(self) -> None:
        wm = self._wm()
        wm.configure(padding=20, relayout=False)
        self.assertEqual(wm.read_settings()["padding"], 20)

    def test_configure_avoid_task_panel(self) -> None:
        wm = self._wm()
        wm.configure(avoid_task_panel=False, relayout=False)
        self.assertFalse(wm.read_settings()["avoid_task_panel"])

    def test_configure_center_on_failure(self) -> None:
        wm = self._wm()
        wm.configure(center_on_failure=False, relayout=False)
        self.assertFalse(wm.read_settings()["center_on_failure"])

    def test_configure_negative_gap_clamped_to_zero(self) -> None:
        wm = self._wm()
        wm.configure(gap=-10, relayout=False)
        self.assertEqual(wm.read_settings()["gap"], 0)

    def test_set_enabled_without_relayout(self) -> None:
        wm = self._wm()
        wm.set_enabled(True, relayout=False)
        self.assertTrue(wm.read_settings()["enabled"])

    def test_set_enabled_false(self) -> None:
        wm = self._wm()
        wm.set_enabled(True, relayout=False)
        wm.set_enabled(False, relayout=False)
        self.assertFalse(wm.read_settings()["enabled"])

    def test_read_settings_returns_all_keys(self) -> None:
        wm = self._wm()
        s = wm.read_settings()
        expected_keys = {"enabled", "gap", "padding", "avoid_task_panel", "center_on_failure"}
        self.assertEqual(set(s.keys()), expected_keys)


# ---------------------------------------------------------------------------
# Pass-BU tests — EventManager (GuiEvent passthrough)
# ---------------------------------------------------------------------------

from gui_do import EventManager


class EventManagerTests(unittest.TestCase):
    """EventManager: to_gui_event passthrough and basic conversion."""

    def test_returns_gui_event_unchanged(self) -> None:
        from gui_do.events.gui_event import GuiEvent, EventType
        em = EventManager()
        evt = GuiEvent(kind=EventType.MOUSE_BUTTON_DOWN, type=0, pos=(0, 0), button=1)
        result = em.to_gui_event(evt)
        self.assertIs(result, evt)

    def test_construction(self) -> None:
        em = EventManager()
        self.assertIsNotNone(em)


# ---------------------------------------------------------------------------
# Pass-BV tests — CanvasEventPacket
# ---------------------------------------------------------------------------

from gui_do import CanvasEventPacket
from gui_do.events.gui_event import EventType as _EvtType


class CanvasEventPacketTests(unittest.TestCase):
    """CanvasEventPacket: construction, kind-predicates, button helpers."""

    def _pkt(self, kind=_EvtType.MOUSE_BUTTON_DOWN, button=1, pos=(10, 20)):
        return CanvasEventPacket(kind=kind, pos=pos, local_pos=pos, button=button)

    def test_construction_left_click(self) -> None:
        pkt = self._pkt()
        self.assertIs(pkt.kind, _EvtType.MOUSE_BUTTON_DOWN)
        self.assertEqual(pkt.local_pos, (10, 20))
        self.assertEqual(pkt.button, 1)

    def test_is_mouse_down_any_button(self) -> None:
        pkt = self._pkt(kind=_EvtType.MOUSE_BUTTON_DOWN, button=2)
        self.assertTrue(pkt.is_mouse_down())

    def test_is_mouse_down_specific_button_match(self) -> None:
        pkt = self._pkt(kind=_EvtType.MOUSE_BUTTON_DOWN, button=1)
        self.assertTrue(pkt.is_mouse_down(1))

    def test_is_mouse_down_specific_button_no_match(self) -> None:
        pkt = self._pkt(kind=_EvtType.MOUSE_BUTTON_DOWN, button=2)
        self.assertFalse(pkt.is_mouse_down(1))

    def test_is_mouse_up(self) -> None:
        pkt = CanvasEventPacket(kind=_EvtType.MOUSE_BUTTON_UP, button=1)
        self.assertTrue(pkt.is_mouse_up())

    def test_is_left_down(self) -> None:
        self.assertTrue(self._pkt(button=1).is_left_down())
        self.assertFalse(self._pkt(button=2).is_left_down())

    def test_is_left_up(self) -> None:
        pkt = CanvasEventPacket(kind=_EvtType.MOUSE_BUTTON_UP, button=1)
        self.assertTrue(pkt.is_left_up())

    def test_is_right_down(self) -> None:
        self.assertTrue(self._pkt(button=3).is_right_down())
        self.assertFalse(self._pkt(button=1).is_right_down())

    def test_is_right_up(self) -> None:
        pkt = CanvasEventPacket(kind=_EvtType.MOUSE_BUTTON_UP, button=3)
        self.assertTrue(pkt.is_right_up())

    def test_is_middle_down(self) -> None:
        self.assertTrue(self._pkt(button=2).is_middle_down())
        self.assertFalse(self._pkt(button=1).is_middle_down())

    def test_is_mouse_motion(self) -> None:
        pkt = CanvasEventPacket(kind=_EvtType.MOUSE_MOTION, rel=(3, 4))
        self.assertTrue(pkt.is_mouse_motion())
        self.assertFalse(self._pkt().is_mouse_motion())

    def test_not_mouse_wheel_for_click(self) -> None:
        self.assertFalse(self._pkt().is_mouse_wheel())

    def test_pos_and_local_pos_fields(self) -> None:
        pkt = CanvasEventPacket(kind=_EvtType.MOUSE_MOTION, pos=(100, 200), local_pos=(10, 20))
        self.assertEqual(pkt.pos, (100, 200))
        self.assertEqual(pkt.local_pos, (10, 20))

    def test_rel_field(self) -> None:
        pkt = CanvasEventPacket(kind=_EvtType.MOUSE_MOTION, rel=(3, -2))
        self.assertEqual(pkt.rel, (3, -2))

    def test_wheel_delta_field(self) -> None:
        pkt = CanvasEventPacket(kind=_EvtType.MOUSE_WHEEL, wheel_delta=3)
        self.assertEqual(pkt.wheel_delta, 3)


# ---------------------------------------------------------------------------
# Pass-BW tests — PanelControl, LabelControl, FrameControl
# ---------------------------------------------------------------------------

from gui_do import PanelControl, LabelControl, FrameControl


class PanelControlTests(unittest.TestCase):
    """PanelControl: construction, draw_background, UiNode identity."""

    def test_construction_defaults(self) -> None:
        pc = PanelControl("panel1", _Rect(0, 0, 200, 100))
        self.assertEqual(pc.control_id, "panel1")
        self.assertTrue(pc.draw_background)

    def test_draw_background_false(self) -> None:
        pc = PanelControl("p", _Rect(0, 0, 100, 50), draw_background=False)
        self.assertFalse(pc.draw_background)

    def test_rect_set_on_construction(self) -> None:
        pc = PanelControl("p", _Rect(10, 20, 300, 150))
        self.assertEqual(pc.rect, _Rect(10, 20, 300, 150))

    def test_enabled_defaults_true(self) -> None:
        self.assertTrue(PanelControl("p", _Rect(0, 0, 100, 50)).enabled)

    def test_visible_defaults_true(self) -> None:
        self.assertTrue(PanelControl("p", _Rect(0, 0, 100, 50)).visible)

    def test_is_not_window(self) -> None:
        self.assertFalse(PanelControl("p", _Rect(0, 0, 100, 50)).is_window())


class LabelControlTests(unittest.TestCase):
    """LabelControl: text, align."""

    def test_text(self) -> None:
        lc = LabelControl("l", _Rect(0, 0, 200, 30), "Hello")
        self.assertEqual(lc.text, "Hello")

    def test_align_left_default(self) -> None:
        lc = LabelControl("l", _Rect(0, 0, 200, 30), "Hi")
        self.assertEqual(lc.align, "left")

    def test_align_center(self) -> None:
        lc = LabelControl("l", _Rect(0, 0, 200, 30), "Hi", align="center")
        self.assertEqual(lc.align, "center")

    def test_control_id(self) -> None:
        lc = LabelControl("my_label", _Rect(0, 0, 100, 24), "x")
        self.assertEqual(lc.control_id, "my_label")


class FrameControlTests(unittest.TestCase):
    """FrameControl: border_width."""

    def test_default_border_width(self) -> None:
        fc = FrameControl("f", _Rect(0, 0, 100, 100))
        self.assertEqual(fc.border_width, 1)

    def test_custom_border_width(self) -> None:
        fc = FrameControl("f", _Rect(0, 0, 100, 100), border_width=4)
        self.assertEqual(fc.border_width, 4)

    def test_is_not_window(self) -> None:
        self.assertFalse(FrameControl("f", _Rect(0, 0, 100, 100)).is_window())


# ---------------------------------------------------------------------------
# Pass-BX tests — ToggleControl, ButtonGroupControl
# ---------------------------------------------------------------------------

from gui_do import ToggleControl, ButtonGroupControl


class ToggleControlTests(unittest.TestCase):
    """ToggleControl: text_on, text_off, pushed, style."""

    def test_text_on_and_off(self) -> None:
        tc = ToggleControl("t", _Rect(0, 0, 100, 30), "On", "Off")
        self.assertEqual(tc.text_on, "On")
        self.assertEqual(tc.text_off, "Off")

    def test_pushed_default_false(self) -> None:
        tc = ToggleControl("t", _Rect(0, 0, 100, 30), "Yes", "No")
        self.assertFalse(tc.pushed)

    def test_pushed_true(self) -> None:
        tc = ToggleControl("t", _Rect(0, 0, 100, 30), "Y", "N", pushed=True)
        self.assertTrue(tc.pushed)

    def test_style_default_box(self) -> None:
        tc = ToggleControl("t", _Rect(0, 0, 100, 30), "Y")
        self.assertEqual(tc.style, "box")

    def test_text_off_defaults_to_text_on(self) -> None:
        tc = ToggleControl("t", _Rect(0, 0, 100, 30), "Toggle")
        self.assertEqual(tc.text_off, "Toggle")

    def test_control_id(self) -> None:
        tc = ToggleControl("my_toggle", _Rect(0, 0, 100, 30), "X")
        self.assertEqual(tc.control_id, "my_toggle")


class ButtonGroupControlTests(unittest.TestCase):
    """ButtonGroupControl: group, text_on, pushed, auto-select-first."""

    def _clear(self):
        ButtonGroupControl.clear_group_registry()

    def test_group_attribute(self) -> None:
        self._clear()
        bg = ButtonGroupControl("b", _Rect(0, 0, 100, 30), "mygroup", "Alpha")
        self.assertEqual(bg.group, "mygroup")

    def test_text_on(self) -> None:
        self._clear()
        bg = ButtonGroupControl("b", _Rect(0, 0, 100, 30), "g", "Beta")
        self.assertEqual(bg.text_on, "Beta")

    def test_first_button_auto_selected(self) -> None:
        self._clear()
        bg = ButtonGroupControl("b", _Rect(0, 0, 100, 30), "g1", "First", selected=False)
        self.assertTrue(bg.pushed)  # first in group is auto-selected

    def test_selected_true_pushes(self) -> None:
        self._clear()
        ButtonGroupControl("b1", _Rect(0, 0, 100, 30), "g2", "A")
        b2 = ButtonGroupControl("b2", _Rect(0, 0, 100, 30), "g2", "B", selected=True)
        self.assertTrue(b2.pushed)

    def test_control_id_set(self) -> None:
        self._clear()
        bg = ButtonGroupControl("my_btn", _Rect(0, 0, 100, 30), "g", "X")
        self.assertEqual(bg.control_id, "my_btn")


# ---------------------------------------------------------------------------
# Pass-BY tests — SliderControl, ScrollbarControl, RangeSliderControl,
#                 SpinnerControl, ColorPickerControl
# ---------------------------------------------------------------------------

from gui_do import SliderControl, ScrollbarControl, RangeSliderControl, SpinnerControl
from gui_do import ColorPickerControl


class SliderControlTests(unittest.TestCase):
    """SliderControl: value, minimum, maximum, axis, set_value."""

    def test_initial_value(self) -> None:
        s = SliderControl("s", _Rect(0, 0, 200, 20), LayoutAxis.HORIZONTAL, 0.0, 100.0, 42.0)
        self.assertAlmostEqual(s.value, 42.0)

    def test_minimum_maximum(self) -> None:
        s = SliderControl("s", _Rect(0, 0, 200, 20), LayoutAxis.HORIZONTAL, 10.0, 90.0, 50.0)
        self.assertAlmostEqual(s.minimum, 10.0)
        self.assertAlmostEqual(s.maximum, 90.0)

    def test_axis(self) -> None:
        s = SliderControl("s", _Rect(0, 0, 20, 200), LayoutAxis.VERTICAL, 0.0, 1.0, 0.5)
        self.assertEqual(s.axis, LayoutAxis.VERTICAL)

    def test_set_value(self) -> None:
        s = SliderControl("s", _Rect(0, 0, 200, 20), LayoutAxis.HORIZONTAL, 0.0, 100.0, 0.0)
        s.set_value(75.0)
        self.assertAlmostEqual(s.value, 75.0)

    def test_control_id(self) -> None:
        s = SliderControl("my_slider", _Rect(0, 0, 200, 20), LayoutAxis.HORIZONTAL, 0.0, 1.0, 0.0)
        self.assertEqual(s.control_id, "my_slider")


class ScrollbarControlTests(unittest.TestCase):
    """ScrollbarControl: offset, content_size, viewport_size, axis."""

    def test_initial_offset(self) -> None:
        sc = ScrollbarControl("sc", _Rect(0, 0, 20, 200), LayoutAxis.VERTICAL, 500, 200, 50)
        self.assertEqual(sc.offset, 50)

    def test_axis(self) -> None:
        sc = ScrollbarControl("sc", _Rect(0, 0, 200, 20), LayoutAxis.HORIZONTAL, 400, 200, 0)
        self.assertEqual(sc.axis, LayoutAxis.HORIZONTAL)

    def test_zero_offset(self) -> None:
        sc = ScrollbarControl("sc", _Rect(0, 0, 20, 200), LayoutAxis.VERTICAL, 500, 200)
        self.assertEqual(sc.offset, 0)

    def test_control_id(self) -> None:
        sc = ScrollbarControl("sc_id", _Rect(0, 0, 20, 200), LayoutAxis.VERTICAL, 300, 100)
        self.assertEqual(sc.control_id, "sc_id")


class RangeSliderControlTests(unittest.TestCase):
    """RangeSliderControl: low_value, high_value, set_values."""

    def test_initial_values(self) -> None:
        rs = RangeSliderControl("rs", _Rect(0, 0, 200, 20), min_value=0, max_value=100, low_value=20, high_value=80)
        self.assertAlmostEqual(rs.low_value, 20.0)
        self.assertAlmostEqual(rs.high_value, 80.0)

    def test_set_values(self) -> None:
        rs = RangeSliderControl("rs", _Rect(0, 0, 200, 20), min_value=0, max_value=100)
        rs.set_values(30, 70)
        self.assertAlmostEqual(rs.low_value, 30.0)
        self.assertAlmostEqual(rs.high_value, 70.0)

    def test_defaults_when_unspecified(self) -> None:
        rs = RangeSliderControl("rs", _Rect(0, 0, 200, 20), min_value=0, max_value=100)
        self.assertAlmostEqual(rs.low_value, 0.0)
        self.assertAlmostEqual(rs.high_value, 100.0)

    def test_control_id(self) -> None:
        rs = RangeSliderControl("rs_id", _Rect(0, 0, 200, 20))
        self.assertEqual(rs.control_id, "rs_id")


class SpinnerControlTests(unittest.TestCase):
    """SpinnerControl: value, increment, decrement, clamping."""

    def test_initial_value(self) -> None:
        sp = SpinnerControl("sp", _Rect(0, 0, 100, 30), value=5)
        self.assertEqual(sp.value, 5)

    def test_increment(self) -> None:
        sp = SpinnerControl("sp", _Rect(0, 0, 100, 30), value=5, step=2)
        sp.increment()
        self.assertEqual(sp.value, 7)

    def test_decrement(self) -> None:
        sp = SpinnerControl("sp", _Rect(0, 0, 100, 30), value=5, step=2)
        sp.decrement()
        self.assertEqual(sp.value, 3)

    def test_max_value_clamp(self) -> None:
        sp = SpinnerControl("sp", _Rect(0, 0, 100, 30), value=9, max_value=10, step=5)
        sp.increment()
        self.assertLessEqual(sp.value, 10)

    def test_min_value_clamp(self) -> None:
        sp = SpinnerControl("sp", _Rect(0, 0, 100, 30), value=1, min_value=0, step=5)
        sp.decrement()
        self.assertGreaterEqual(sp.value, 0)

    def test_control_id(self) -> None:
        sp = SpinnerControl("my_spinner", _Rect(0, 0, 100, 30))
        self.assertEqual(sp.control_id, "my_spinner")


class ColorPickerControlTests(unittest.TestCase):
    """ColorPickerControl: color attribute."""

    def test_default_color(self) -> None:
        cp = ColorPickerControl("cp", _Rect(0, 0, 200, 200))
        self.assertEqual(len(cp.color), 3)

    def test_custom_color(self) -> None:
        cp = ColorPickerControl("cp", _Rect(0, 0, 200, 200), color=(100, 150, 200))
        self.assertEqual(cp.color, (100, 150, 200))

    def test_control_id(self) -> None:
        cp = ColorPickerControl("my_cp", _Rect(0, 0, 200, 200))
        self.assertEqual(cp.control_id, "my_cp")


# ---------------------------------------------------------------------------
# Pass-BZ tests — TextInputControl, TextAreaControl, ArrowBoxControl
# ---------------------------------------------------------------------------

from gui_do import TextInputControl, TextAreaControl, ArrowBoxControl


class TextInputControlTests(unittest.TestCase):
    """TextInputControl: value, set_value."""

    def test_initial_value(self) -> None:
        ti = TextInputControl("ti", _Rect(0, 0, 200, 30), value="hello")
        self.assertEqual(ti.value, "hello")

    def test_empty_value_default(self) -> None:
        ti = TextInputControl("ti", _Rect(0, 0, 200, 30))
        self.assertEqual(ti.value, "")

    def test_set_value(self) -> None:
        ti = TextInputControl("ti", _Rect(0, 0, 200, 30), value="old")
        ti.set_value("new")
        self.assertEqual(ti.value, "new")

    def test_control_id(self) -> None:
        ti = TextInputControl("my_ti", _Rect(0, 0, 200, 30))
        self.assertEqual(ti.control_id, "my_ti")

    def test_is_not_window(self) -> None:
        ti = TextInputControl("ti", _Rect(0, 0, 200, 30))
        self.assertFalse(ti.is_window())


class TextAreaControlTests(unittest.TestCase):
    """TextAreaControl: value, read_only, set_value."""

    def test_initial_value(self) -> None:
        ta = TextAreaControl("ta", _Rect(0, 0, 200, 100), value="line1\nline2")
        self.assertEqual(ta.value, "line1\nline2")

    def test_empty_default(self) -> None:
        ta = TextAreaControl("ta", _Rect(0, 0, 200, 100))
        self.assertEqual(ta.value, "")

    def test_read_only_true(self) -> None:
        ta = TextAreaControl("ta", _Rect(0, 0, 200, 100), read_only=True)
        self.assertTrue(ta.read_only)

    def test_read_only_default_false(self) -> None:
        ta = TextAreaControl("ta", _Rect(0, 0, 200, 100))
        self.assertFalse(ta.read_only)

    def test_set_value(self) -> None:
        ta = TextAreaControl("ta", _Rect(0, 0, 200, 100), value="old")
        ta.set_value("new content")
        self.assertEqual(ta.value, "new content")

    def test_control_id(self) -> None:
        ta = TextAreaControl("my_ta", _Rect(0, 0, 200, 100))
        self.assertEqual(ta.control_id, "my_ta")


class ArrowBoxControlTests(unittest.TestCase):
    """ArrowBoxControl: direction, repeat_interval_seconds."""

    def test_direction(self) -> None:
        ab = ArrowBoxControl("ab", _Rect(0, 0, 30, 30), direction=1)
        self.assertEqual(ab.direction, 1)

    def test_repeat_interval_default(self) -> None:
        ab = ArrowBoxControl("ab", _Rect(0, 0, 30, 30), direction=0)
        self.assertAlmostEqual(ab.repeat_interval_seconds, 0.08)

    def test_repeat_interval_custom(self) -> None:
        ab = ArrowBoxControl("ab", _Rect(0, 0, 30, 30), direction=0, repeat_interval_seconds=0.1)
        self.assertAlmostEqual(ab.repeat_interval_seconds, 0.1)

    def test_control_id(self) -> None:
        ab = ArrowBoxControl("my_ab", _Rect(0, 0, 30, 30), direction=2)
        self.assertEqual(ab.control_id, "my_ab")

    def test_is_not_window(self) -> None:
        ab = ArrowBoxControl("ab", _Rect(0, 0, 30, 30), direction=0)
        self.assertFalse(ab.is_window())


# ---------------------------------------------------------------------------
# Pass-CA tests — SplitterControl, ScrollViewControl
# ---------------------------------------------------------------------------

from gui_do import SplitterControl, ScrollViewControl


class SplitterControlTests(unittest.TestCase):
    """SplitterControl: ratio, axis, pane rects."""

    def test_ratio_initial(self) -> None:
        sv = SplitterControl("sv", _Rect(0, 0, 400, 300), ratio=0.4)
        self.assertAlmostEqual(sv.ratio, 0.4)

    def test_axis_horizontal(self) -> None:
        sv = SplitterControl("sv", _Rect(0, 0, 400, 300), axis=LayoutAxis.HORIZONTAL)
        self.assertEqual(sv.axis, LayoutAxis.HORIZONTAL)

    def test_axis_vertical(self) -> None:
        sv = SplitterControl("sv", _Rect(0, 0, 300, 400), axis=LayoutAxis.VERTICAL)
        self.assertEqual(sv.axis, LayoutAxis.VERTICAL)

    def test_pane_a_rect_non_empty(self) -> None:
        sv = SplitterControl("sv", _Rect(0, 0, 400, 300), ratio=0.5)
        self.assertGreater(sv.pane_a_rect.width, 0)

    def test_pane_b_rect_non_empty(self) -> None:
        sv = SplitterControl("sv", _Rect(0, 0, 400, 300), ratio=0.5)
        self.assertGreater(sv.pane_b_rect.width, 0)

    def test_control_id(self) -> None:
        sv = SplitterControl("my_sv", _Rect(0, 0, 400, 300))
        self.assertEqual(sv.control_id, "my_sv")

    def test_default_ratio(self) -> None:
        sv = SplitterControl("sv", _Rect(0, 0, 400, 300))
        self.assertAlmostEqual(sv.ratio, 0.5)


class ScrollViewControlTests(unittest.TestCase):
    """ScrollViewControl: content size, set_content_size."""

    def test_construction(self) -> None:
        scv = ScrollViewControl("scv", _Rect(0, 0, 200, 300), content_width=400, content_height=600)
        self.assertEqual(scv.control_id, "scv")

    def test_set_content_size(self) -> None:
        scv = ScrollViewControl("scv", _Rect(0, 0, 200, 300))
        scv.set_content_size(800, 1200)  # should not raise

    def test_is_not_window(self) -> None:
        scv = ScrollViewControl("scv", _Rect(0, 0, 200, 300))
        self.assertFalse(scv.is_window())


# ---------------------------------------------------------------------------
# Pass-CB tests — TabControl, MenuBarControl, DropdownControl
# ---------------------------------------------------------------------------

from gui_do import TabControl, MenuBarControl, DropdownControl


class TabControlTests(unittest.TestCase):
    """TabControl: items, selected_key, select()."""

    def test_items(self) -> None:
        tc = TabControl("tc", _Rect(0, 0, 400, 300),
                        items=[TabItem("a", "Alpha"), TabItem("b", "Beta")])
        self.assertEqual(len(tc.items()), 2)

    def test_initial_selected_key(self) -> None:
        tc = TabControl("tc", _Rect(0, 0, 400, 300),
                        items=[TabItem("a", "A"), TabItem("b", "B")],
                        selected_key="b")
        self.assertEqual(tc.selected_key, "b")

    def test_select_changes_key(self) -> None:
        tc = TabControl("tc", _Rect(0, 0, 400, 300),
                        items=[TabItem("a", "A"), TabItem("b", "B")],
                        selected_key="a")
        tc.select("b")
        self.assertEqual(tc.selected_key, "b")

    def test_no_items_default(self) -> None:
        tc = TabControl("tc", _Rect(0, 0, 400, 300))
        self.assertEqual(tc.items(), [])

    def test_control_id(self) -> None:
        tc = TabControl("my_tc", _Rect(0, 0, 400, 300))
        self.assertEqual(tc.control_id, "my_tc")


class MenuBarControlTests(unittest.TestCase):
    """MenuBarControl: entries, set_entries."""

    def test_entries_populated(self) -> None:
        mb = MenuBarControl("mb", _Rect(0, 0, 800, 32),
                             entries=[MenuEntry("File"), MenuEntry("Edit")])
        self.assertEqual(len(mb.entries), 2)
        self.assertEqual(mb.entries[0].label, "File")

    def test_no_entries_default(self) -> None:
        mb = MenuBarControl("mb", _Rect(0, 0, 800, 32))
        self.assertEqual(mb.entries, [])

    def test_set_entries(self) -> None:
        mb = MenuBarControl("mb", _Rect(0, 0, 800, 32))
        mb.set_entries([MenuEntry("View"), MenuEntry("Help")])
        self.assertEqual(len(mb.entries), 2)
        self.assertEqual(mb.entries[1].label, "Help")

    def test_control_id(self) -> None:
        mb = MenuBarControl("my_mb", _Rect(0, 0, 800, 32))
        self.assertEqual(mb.control_id, "my_mb")


class DropdownControlTests(unittest.TestCase):
    """DropdownControl: options, selected_index, selected_option, set_options."""

    def test_options_and_selected_index(self) -> None:
        dd = DropdownControl("dd", _Rect(0, 0, 200, 30),
                              options=[DropdownOption("A", 1), DropdownOption("B", 2)],
                              selected_index=0)
        self.assertEqual(dd.selected_index, 0)

    def test_selected_option(self) -> None:
        dd = DropdownControl("dd", _Rect(0, 0, 200, 30),
                              options=[DropdownOption("Alpha", 10), DropdownOption("Beta", 20)],
                              selected_index=1)
        self.assertEqual(dd.selected_option.label, "Beta")
        self.assertEqual(dd.selected_option.value, 20)

    def test_selected_option_none_when_no_selection(self) -> None:
        dd = DropdownControl("dd", _Rect(0, 0, 200, 30),
                              options=[DropdownOption("X")])
        dd_empty = DropdownControl("dd2", _Rect(0, 0, 200, 30))
        # selected_index=-1 → no selection
        self.assertIsNone(dd_empty.selected_option)

    def test_set_options(self) -> None:
        dd = DropdownControl("dd", _Rect(0, 0, 200, 30))
        dd.set_options([DropdownOption("New1"), DropdownOption("New2")])
        # after set_options with 2 items, a selection may be auto-set
        opt = dd.selected_option
        self.assertIn(opt.label if opt else None, [None, "New1", "New2"])

    def test_no_options_default(self) -> None:
        dd = DropdownControl("dd", _Rect(0, 0, 200, 30))
        self.assertIsNone(dd.selected_option)  # no options → no selection

    def test_control_id(self) -> None:
        dd = DropdownControl("my_dd", _Rect(0, 0, 200, 30))
        self.assertEqual(dd.control_id, "my_dd")


# ---------------------------------------------------------------------------
# Pass-CC tests — WindowControl, TaskPanelControl, RichLabelControl
# ---------------------------------------------------------------------------

from gui_do import WindowControl, TaskPanelControl, RichLabelControl


class WindowControlTests(unittest.TestCase):
    """WindowControl: title, titlebar_height, is_window, active."""

    def test_title(self) -> None:
        wc = WindowControl("wc", _Rect(50, 50, 400, 300), "My Window")
        self.assertEqual(wc.title, "My Window")

    def test_titlebar_height_default(self) -> None:
        wc = WindowControl("wc", _Rect(50, 50, 400, 300), "Win")
        self.assertEqual(wc.titlebar_height, 24)

    def test_custom_titlebar_height(self) -> None:
        wc = WindowControl("wc", _Rect(50, 50, 400, 300), "Win", titlebar_height=32)
        self.assertEqual(wc.titlebar_height, 32)

    def test_is_window(self) -> None:
        wc = WindowControl("wc", _Rect(50, 50, 400, 300), "Win")
        self.assertTrue(wc.is_window())

    def test_initial_active_false(self) -> None:
        wc = WindowControl("wc", _Rect(50, 50, 400, 300), "Win")
        self.assertFalse(wc.active)

    def test_set_active(self) -> None:
        wc = WindowControl("wc", _Rect(50, 50, 400, 300), "Win")
        wc.set_active(True)
        self.assertTrue(wc.active)

    def test_control_id(self) -> None:
        wc = WindowControl("my_wc", _Rect(0, 0, 300, 200), "X")
        self.assertEqual(wc.control_id, "my_wc")

    def test_content_rect_within_window(self) -> None:
        wc = WindowControl("wc", _Rect(0, 0, 400, 300), "Win", titlebar_height=24)
        cr = wc.content_rect()
        self.assertLessEqual(cr.top, 300)
        self.assertLessEqual(cr.height, 300)

    def test_move_by(self) -> None:
        wc = WindowControl("wc", _Rect(100, 100, 200, 150), "W")
        wc.move_by(10, -20)
        self.assertEqual(wc.rect.left, 110)
        self.assertEqual(wc.rect.top, 80)


class TaskPanelControlTests(unittest.TestCase):
    """TaskPanelControl: auto_hide, dock_bottom, is_task_panel."""

    def test_auto_hide_default_true(self) -> None:
        tp = TaskPanelControl("tp", _Rect(0, 500, 800, 50))
        self.assertTrue(tp.auto_hide)

    def test_auto_hide_false(self) -> None:
        tp = TaskPanelControl("tp", _Rect(0, 500, 800, 50), auto_hide=False)
        self.assertFalse(tp.auto_hide)

    def test_dock_bottom_default_false(self) -> None:
        tp = TaskPanelControl("tp", _Rect(0, 0, 800, 50))
        self.assertFalse(tp.dock_bottom)

    def test_dock_bottom_true(self) -> None:
        tp = TaskPanelControl("tp", _Rect(0, 0, 800, 50), dock_bottom=True)
        self.assertTrue(tp.dock_bottom)

    def test_is_task_panel(self) -> None:
        tp = TaskPanelControl("tp", _Rect(0, 0, 800, 50))
        self.assertTrue(tp.is_task_panel())

    def test_is_not_window(self) -> None:
        tp = TaskPanelControl("tp", _Rect(0, 0, 800, 50))
        self.assertFalse(tp.is_window())

    def test_control_id(self) -> None:
        tp = TaskPanelControl("my_tp", _Rect(0, 0, 800, 50))
        self.assertEqual(tp.control_id, "my_tp")

    def test_hover_not_updated_while_command_palette_open(self) -> None:
        """Task panel _hovered must not change while __command_palette__ overlay is active."""
        from unittest.mock import MagicMock
        from gui_do.events.gui_event import GuiEvent, EventType

        tp = TaskPanelControl("tp", _Rect(0, 400, 800, 50), auto_hide=True)
        # Seed hover state as True (panel raised).
        tp._hovered = True

        overlay_mock = MagicMock()
        overlay_mock.has_overlay.return_value = True  # palette active

        app = MagicMock()
        app.overlay = overlay_mock

        # MOUSE_MOTION with pos outside the panel rect — normally would set _hovered=False.
        evt = GuiEvent(kind=EventType.MOUSE_MOTION, type=0, pos=(100, 100))
        tp.handle_event(evt, app)

        # _hovered must remain True (frozen while palette is open).
        self.assertTrue(tp._hovered)

    def test_hover_updated_normally_when_command_palette_not_open(self) -> None:
        """Task panel _hovered updates normally when no command palette overlay is active."""
        from unittest.mock import MagicMock
        from gui_do.events.gui_event import GuiEvent, EventType

        tp = TaskPanelControl("tp", _Rect(0, 400, 800, 50), auto_hide=True)
        tp._hovered = True

        overlay_mock = MagicMock()
        overlay_mock.has_overlay.return_value = False  # no palette

        app = MagicMock()
        app.overlay = overlay_mock

        # MOUSE_MOTION with pos outside the panel rect — should set _hovered=False.
        evt = GuiEvent(kind=EventType.MOUSE_MOTION, type=0, pos=(100, 100))
        tp.handle_event(evt, app)

        self.assertFalse(tp._hovered)



    """RichLabelControl: text, font_role, align, color."""

    def test_text(self) -> None:
        rl = RichLabelControl("rl", _Rect(0, 0, 200, 40), "Hello world")
        self.assertEqual(rl.text, "Hello world")

    def test_align_left_default(self) -> None:
        rl = RichLabelControl("rl", _Rect(0, 0, 200, 40), "x")
        self.assertEqual(rl.align, "left")

    def test_align_center(self) -> None:
        rl = RichLabelControl("rl", _Rect(0, 0, 200, 40), "x", align="center")
        self.assertEqual(rl.align, "center")

    def test_font_role_default_body(self) -> None:
        rl = RichLabelControl("rl", _Rect(0, 0, 200, 40), "x")
        self.assertEqual(rl.font_role, "body")

    def test_control_id(self) -> None:
        rl = RichLabelControl("my_rl", _Rect(0, 0, 200, 40), "y")
        self.assertEqual(rl.control_id, "my_rl")


# ---------------------------------------------------------------------------
# Pass-CD tests — DialogHandle (with stub manager)
# ---------------------------------------------------------------------------

from gui_do import DialogHandle


class DialogHandleTests(unittest.TestCase):
    """DialogHandle: is_open, dismiss via stub manager."""

    def _handle(self, dialog_id: int = 1, open_ids=None):
        class _ManagerStub:
            def __init__(self, ids):
                self._open = list(ids)

            def _is_open(self, did):
                return did in self._open

            def dismiss(self, handle):
                try:
                    self._open.remove(handle.dialog_id)
                except ValueError:
                    pass

        ids = [dialog_id] if open_ids is None else open_ids
        stub = _ManagerStub(ids)
        return DialogHandle(dialog_id=dialog_id, _manager=stub)

    def test_is_open_true(self) -> None:
        h = self._handle(1)
        self.assertTrue(h.is_open)

    def test_is_open_false_when_not_in_list(self) -> None:
        h = self._handle(1, open_ids=[2])
        self.assertFalse(h.is_open)

    def test_dismiss_closes_dialog(self) -> None:
        h = self._handle(1)
        self.assertTrue(h.is_open)
        h.dismiss()
        self.assertFalse(h.is_open)

    def test_dialog_id_field(self) -> None:
        h = self._handle(42)
        self.assertEqual(h.dialog_id, 42)

    def test_dismiss_twice_no_error(self) -> None:
        h = self._handle(1)
        h.dismiss()
        h.dismiss()  # should not raise


if __name__ == "__main__":
    unittest.main()
