from types import SimpleNamespace
import unittest

from gui_do.features.data_driven_runtime import (
    PaletteInputBindSpec,
    SceneCommandPaletteSpec,
    bind_palette_window_action_bind,
    setup_scene_command_palette_bindings,
)


class _StubActions:
    def __init__(self):
        self.handlers = {}
        self.global_key_binds = []
        self.global_pointer_binds = []

    def has_action(self, action_name: str) -> bool:
        return str(action_name) in self.handlers

    def register_action(self, action_name: str, handler) -> None:
        self.handlers[str(action_name)] = handler

    def bind_global_key(self, key: int, action_name: str, *, scene: str | None = None) -> None:
        self.global_key_binds.append((int(key), str(action_name), scene))

    def bind_global_pointer_button(self, button: int, action_name: str, *, scene: str | None = None) -> None:
        self.global_pointer_binds.append((int(button), str(action_name), scene))


class _StubPaletteManager:
    def __init__(self, *, is_open: bool = False):
        self.is_open = bool(is_open)
        self.show_calls = []
        self.activations = []

    def show(self, app) -> None:
        self.show_calls.append(app)
        self.is_open = True

    def try_activate_action_at(self, pos: tuple[int, int], *, suppress_followup_select: bool = True) -> bool:
        self.activations.append(((int(pos[0]), int(pos[1])), bool(suppress_followup_select)))
        return True


class _StubApp:
    def __init__(self, *, logical_pointer_pos=(0, 0)):
        self.actions = _StubActions()
        self.logical_pointer_pos = logical_pointer_pos


class _StubHost:
    def __init__(self, app, palette_manager):
        self.app = app
        self._palette_manager = palette_manager


class SceneCommandPaletteBindingTests(unittest.TestCase):
    def test_setup_scene_command_palette_bindings_uses_logical_pointer_fallback(self):
        app = _StubApp(logical_pointer_pos=(137, 241))
        palette_manager = _StubPaletteManager(is_open=True)
        spec = SceneCommandPaletteSpec(
            scene_name="main",
            toggle=PaletteInputBindSpec(action_name="command_palette_toggle", key=116),
            action=PaletteInputBindSpec(action_name="command_palette_action", pointer_button=2),
        )

        setup_scene_command_palette_bindings(app, palette_manager, spec)

        handled = app.actions.handlers["command_palette_action"](SimpleNamespace(pos=None))

        self.assertTrue(handled)
        self.assertEqual([(2, "command_palette_action", "main")], app.actions.global_pointer_binds)
        self.assertEqual([((137, 241), False)], palette_manager.activations)

    def test_bind_palette_window_action_bind_uses_logical_pointer_fallback(self):
        app = _StubApp(logical_pointer_pos=(410, 96))
        palette_manager = _StubPaletteManager(is_open=True)
        host = _StubHost(app, palette_manager)

        bind_palette_window_action_bind(host, app.actions)

        handled = app.actions.handlers["command_palette_action"](SimpleNamespace(pos=None))

        self.assertTrue(handled)
        self.assertEqual([((410, 96), False)], palette_manager.activations)


if __name__ == "__main__":
    unittest.main()
