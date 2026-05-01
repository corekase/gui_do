import unittest
from unittest.mock import patch

from demo_features.feature_abstractions import (
    apply_accessibility_sequence,
    build_tools_menu_entries,
    create_presented_anchored_window,
    ensure_scene_scheduler,
    register_companion_logic_features,
)


class _StubActionRegistry:
    def context_menu_items(self, *, category: str):
        if category != "Tools":
            return []

        class _Item:
            def __init__(self, label: str):
                self.label = label

        return [_Item("One"), _Item("Open Command Palette (F5)"), _Item("Two")]


class _StubHost:
    def __init__(self, action_registry=None):
        self.action_registry = action_registry


class _StubControl:
    def __init__(self):
        self.tab_indices = []
        self.accessibility = []

    def set_tab_index(self, idx: int):
        self.tab_indices.append(int(idx))

    def set_accessibility(self, *, role: str, label: str):
        self.accessibility.append((str(role), str(label)))


class _StubFeatureManager:
    def __init__(self):
        self.register_calls = []

    def register(self, provider, host):
        self.register_calls.append((provider, host))


class _StubWindow:
    def __init__(self):
        self.presenter = None

    def set_presenter(self, presenter):
        self.presenter = presenter


class _StubSchedulerHostApp:
    def __init__(self, scheduler):
        self._scheduler = scheduler
        self.requests = []

    def get_scene_scheduler(self, scene_name: str):
        self.requests.append(str(scene_name))
        return self._scheduler


class _StubSchedulerHost:
    def __init__(self, scheduler):
        self.app = _StubSchedulerHostApp(scheduler)


class _StubFeatureWithScheduler:
    def __init__(self):
        self.scheduler = None


class TestDemoFeatureAbstractions(unittest.TestCase):
    def test_build_tools_menu_entries_handles_missing_registry(self):
        entries = build_tools_menu_entries(_StubHost(None))
        self.assertEqual([], entries)

    def test_build_tools_menu_entries_applies_exclusions(self):
        entries = build_tools_menu_entries(
            _StubHost(_StubActionRegistry()),
            exclude_labels=("Open Command Palette (F5)",),
        )
        self.assertEqual(1, len(entries))
        self.assertEqual("Tools", entries[0].label)
        labels = [item.label for item in entries[0].items]
        self.assertEqual(["One", "Two"], labels)

    def test_apply_accessibility_sequence_sets_tab_order_and_labels(self):
        first = _StubControl()
        second = _StubControl()

        next_index = apply_accessibility_sequence(
            [
                (first, "button", "First"),
                (None, "button", "Skipped"),
                (second, "toggle", "Second"),
            ],
            5,
        )

        self.assertEqual(7, next_index)
        self.assertEqual([5], first.tab_indices)
        self.assertEqual([("button", "First")], first.accessibility)
        self.assertEqual([6], second.tab_indices)
        self.assertEqual([("toggle", "Second")], second.accessibility)

    def test_register_companion_logic_features_registers_all_providers(self):
        manager = _StubFeatureManager()
        host = object()
        providers = [object(), object(), object()]

        register_companion_logic_features(manager, host, providers)

        self.assertEqual(3, len(manager.register_calls))
        self.assertEqual(
            [(providers[0], host), (providers[1], host), (providers[2], host)],
            manager.register_calls,
        )

    def test_create_presented_anchored_window_attaches_presenter(self):
        host = object()
        presenter = object()
        window = _StubWindow()

        with patch("demo_features.feature_abstractions.create_anchored_feature_window", return_value=window) as create_window:
            result = create_presented_anchored_window(
                host,
                control_id="x",
                title="Demo",
                size=(320, 240),
                anchor="top_left",
                margin=(10, 10),
                presenter=presenter,
            )

        self.assertIs(window, result)
        self.assertIs(presenter, window.presenter)
        self.assertEqual(1, create_window.call_count)

    def test_ensure_scene_scheduler_caches_scheduler_on_feature(self):
        scheduler = object()
        host = _StubSchedulerHost(scheduler)
        feature = _StubFeatureWithScheduler()

        first = ensure_scene_scheduler(feature, host, scene_name="main")
        second = ensure_scene_scheduler(feature, host, scene_name="main")

        self.assertIs(scheduler, first)
        self.assertIs(scheduler, second)
        self.assertIs(scheduler, feature.scheduler)
        self.assertEqual(["main"], host.app.requests)


if __name__ == "__main__":
    unittest.main()
