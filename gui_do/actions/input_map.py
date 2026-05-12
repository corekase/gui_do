"""InputMap — persistence-aware action→input binding table.

Bridges physical key inputs to logical action names.  Features declare their
default bindings via :meth:`InputMap.declare`; users or application code can
remap them with :meth:`InputMap.bind`.  Call :meth:`InputMap.apply` to push
all bindings into an :class:`~gui_do.ActionManager` and
:meth:`InputMap.save` / :meth:`InputMap.load` to persist overrides through
a :class:`~gui_do.SettingsRegistry`.

Usage::

    from gui_do import InputMap, ActionManager, SettingsRegistry

    imap = InputMap()

    # Declare defaults (typically called during feature setup):
    imap.declare("edit.copy",   key=67, mod=64,  label="Copy")       # Ctrl+C
    imap.declare("edit.paste",  key=86, mod=64,  label="Paste")      # Ctrl+V
    imap.declare("file.save",   key=83, mod=64,  label="Save")       # Ctrl+S

    # Apply to ActionManager (registers key bindings):
    actions = ActionManager()
    actions.register_action("edit.copy",  lambda _e: do_copy())
    imap.apply(actions)

    # Remap at runtime:
    imap.bind("edit.copy", key=67, mod=72)  # Ctrl+Shift+C

    # Persist overrides:
    registry = SettingsRegistry("settings.json")
    imap.save(registry)
    imap.load(registry)   # on next launch
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .action_manager import ActionManager
    from ..persistence.settings_registry import SettingsRegistry


# ---------------------------------------------------------------------------
# InputBinding
# ---------------------------------------------------------------------------


@dataclass
class InputBinding:
    """A logical action bound to a physical key.

    Attributes
    ----------
    action:
        The logical action name (must be registered in :class:`~gui_do.ActionManager`).
    key:
        Pygame key constant (e.g. ``pygame.K_c``).
    mod:
        Modifier mask (e.g. ``pygame.KMOD_CTRL``).  ``0`` means no modifier.
    label:
        Human-readable description shown in settings UI or keybinding lists.
    is_default:
        ``True`` when this is the original declared default (not user-remapped).
    """

    action: str
    key: int
    mod: int = 0
    label: str = ""
    is_default: bool = True


# ---------------------------------------------------------------------------
# InputMap
# ---------------------------------------------------------------------------


class InputMap:
    """Persistence-aware action→key binding table.

    Workflow:

    1. Features call :meth:`declare` with default key assignments.
    2. Application (or user settings) calls :meth:`bind` to override.
    3. :meth:`apply` pushes all current bindings into an
       :class:`~gui_do.ActionManager`.
    4. :meth:`save` / :meth:`load` persist user overrides through a
       :class:`~gui_do.SettingsRegistry` namespace ``"input_map"``.
    """

    _SETTINGS_NAMESPACE = "input_map"

    def __init__(self) -> None:
        # action -> InputBinding
        self._bindings: Dict[str, InputBinding] = {}

    # ------------------------------------------------------------------
    # Declaration API
    # ------------------------------------------------------------------

    def declare(
        self,
        action: str,
        *,
        key: int,
        mod: int = 0,
        label: str = "",
    ) -> None:
        """Declare the default binding for *action*.

        If a binding already exists (e.g. loaded from settings) this call is
        silently ignored so that persisted user preferences are preserved.
        """
        action = str(action).strip()
        if not action:
            raise ValueError("action must be a non-empty string")
        if action in self._bindings:
            return
        self._bindings[action] = InputBinding(
            action=action,
            key=int(key),
            mod=int(mod),
            label=str(label),
            is_default=True,
        )

    # ------------------------------------------------------------------
    # Remapping API
    # ------------------------------------------------------------------

    def bind(self, action: str, *, key: int, mod: int = 0) -> None:
        """Override the key binding for *action*.

        Creates the binding if *action* has not been declared yet.
        """
        action = str(action).strip()
        if not action:
            raise ValueError("action must be a non-empty string")
        existing = self._bindings.get(action)
        label = existing.label if existing is not None else ""
        self._bindings[action] = InputBinding(
            action=action,
            key=int(key),
            mod=int(mod),
            label=label,
            is_default=False,
        )

    def unbind(self, action: str) -> bool:
        """Remove the binding for *action*.  Returns ``True`` if a binding existed."""
        return self._bindings.pop(str(action).strip(), None) is not None

    def reset_to_default(self, action: str) -> bool:
        """Restore the declared default for *action* if it was overridden.

        Returns ``True`` when a reset occurred.
        """
        binding = self._bindings.get(str(action))
        if binding is None or binding.is_default:
            return False
        self._bindings[action] = InputBinding(
            action=binding.action,
            key=binding.key,
            mod=binding.mod,
            label=binding.label,
            is_default=True,
        )
        return True

    # ------------------------------------------------------------------
    # Apply to ActionManager
    # ------------------------------------------------------------------

    def apply(self, actions: "ActionManager", *, scene: Optional[str] = None) -> int:
        """Register all current bindings in *actions*.

        Clears any existing key bindings for registered actions before
        re-applying so stale overrides do not accumulate.

        Returns the number of bindings applied.
        """
        from .action_manager import KeyBinding

        count = 0
        for binding in self._bindings.values():
            if actions.has_action(binding.action):
                count += actions.replace_bindings_for_action(
                    binding.action,
                    (KeyBinding(binding.key, scene=scene, window_only=False),),
                )
        return count

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self, registry: "SettingsRegistry") -> None:
        """Persist all non-default (user-overridden) bindings to *registry*."""
        for binding in self._bindings.values():
            if not binding.is_default:
                ns_key = f"{binding.action}.key"
                mod_key = f"{binding.action}.mod"
                registry.declare(self._SETTINGS_NAMESPACE, ns_key, binding.key)
                registry.declare(self._SETTINGS_NAMESPACE, mod_key, binding.mod)
                registry.set_value(self._SETTINGS_NAMESPACE, ns_key, binding.key)
                registry.set_value(self._SETTINGS_NAMESPACE, mod_key, binding.mod)
        registry.save()

    def load(self, registry: "SettingsRegistry") -> int:
        """Restore overrides from *registry*.  Returns the number of bindings restored."""
        restored = 0
        for action, binding in list(self._bindings.items()):
            ns_key = f"{action}.key"
            mod_key = f"{action}.mod"
            try:
                obs_key = registry.get(self._SETTINGS_NAMESPACE, ns_key)
                obs_mod = registry.get(self._SETTINGS_NAMESPACE, mod_key)
            except KeyError:
                continue
            new_key = int(obs_key.value)
            new_mod = int(obs_mod.value)
            if new_key != binding.key or new_mod != binding.mod:
                self._bindings[action] = InputBinding(
                    action=action,
                    key=new_key,
                    mod=new_mod,
                    label=binding.label,
                    is_default=False,
                )
                restored += 1
        return restored

    # ------------------------------------------------------------------
    # Inspection
    # ------------------------------------------------------------------

    def bindings(self) -> List[InputBinding]:
        """Return all registered bindings in declaration order."""
        return list(self._bindings.values())

    def binding_for(self, action: str) -> Optional[InputBinding]:
        """Return the binding for *action*, or ``None`` if not declared."""
        return self._bindings.get(str(action))

    def actions(self) -> List[str]:
        """Return a sorted list of all declared action names."""
        return sorted(self._bindings.keys())

    def __len__(self) -> int:
        return len(self._bindings)
