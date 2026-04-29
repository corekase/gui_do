"""Action registry — shared action descriptors for menus, palettes, and key routing."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Mapping, Optional


ActionCallback = Callable[[Any, object | None], bool | None]
ActionPredicate = Callable[[Any], bool]


@dataclass(slots=True)
class ActionDescriptor:
    """One canonical action definition shared across UI surfaces.

    A descriptor centralises the user-facing label, optional category/shortcut
    hint, and enablement/checked-state logic so command palette, menu, toolbar,
    and keyboard routing can all read from the same source.
    """

    action_id: str
    label: str
    callback: ActionCallback
    category: str = ""
    shortcut_hint: str = ""
    description: str = ""
    enabled: bool | ActionPredicate = True
    checked: bool | ActionPredicate = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_enabled(self, context: Any = None) -> bool:
        value = self.enabled
        if callable(value):
            return bool(value(context))
        return bool(value)

    def is_checked(self, context: Any = None) -> bool:
        value = self.checked
        if callable(value):
            return bool(value(context))
        return bool(value)

    def invoke(self, context: Any = None, event: object | None = None) -> bool:
        if not self.is_enabled(context):
            return False
        return bool(self.callback(context, event))


class ActionRegistry:
    """Registry of canonical actions that can project into multiple UI systems."""

    def __init__(self) -> None:
        self._actions: Dict[str, ActionDescriptor] = {}

    def register(self, descriptor: ActionDescriptor) -> None:
        action_id = str(descriptor.action_id).strip()
        if not action_id:
            raise ValueError("action_id must be a non-empty string")
        if not callable(descriptor.callback):
            raise ValueError("ActionDescriptor.callback must be callable")
        self._actions[action_id] = descriptor

    def declare(
        self,
        action_id: str,
        label: str,
        callback: ActionCallback,
        *,
        category: str = "",
        shortcut_hint: str = "",
        description: str = "",
        enabled: "bool | ActionPredicate" = True,
        checked: "bool | ActionPredicate" = False,
        metadata: "Dict[str, Any] | None" = None,
    ) -> ActionDescriptor:
        """Convenience wrapper: create an :class:`ActionDescriptor` and register it.

        Returns the created descriptor for further customisation.
        """
        descriptor = ActionDescriptor(
            action_id=str(action_id).strip(),
            label=str(label),
            callback=callback,
            category=str(category),
            shortcut_hint=str(shortcut_hint),
            description=str(description),
            enabled=enabled,
            checked=checked,
            metadata=dict(metadata) if metadata else {},
        )
        self.register(descriptor)
        return descriptor

    def register_many(self, descriptors: List[ActionDescriptor]) -> None:
        for descriptor in descriptors:
            self.register(descriptor)

    def unregister(self, action_id: str) -> bool:
        return bool(self._actions.pop(str(action_id), None))

    def clear(self) -> None:
        self._actions.clear()

    def has(self, action_id: str) -> bool:
        return str(action_id) in self._actions

    def get(self, action_id: str) -> ActionDescriptor:
        try:
            return self._actions[str(action_id)]
        except KeyError:
            raise KeyError(f"Action not registered: {action_id!r}") from None

    def descriptors(self) -> List[ActionDescriptor]:
        return list(self._actions.values())

    def action_ids(self) -> List[str]:
        return sorted(self._actions.keys())

    def invoke(self, action_id: str, context: Any = None, event: object | None = None) -> bool:
        return self.get(action_id).invoke(context, event)

    def bind_into(self, action_manager, *, context: Any = None) -> None:
        """Register all actions in an :class:`ActionManager`.

        Keyboard bindings remain owned by ``ActionManager`` / ``InputMap``.
        This method only contributes the canonical action handlers.
        """
        for descriptor in self._actions.values():
            action_manager.register_action(
                descriptor.action_id,
                lambda event, _descriptor=descriptor, _context=context: _descriptor.invoke(_context, event),
            )

    def command_entries(self, *, context: Any = None) -> List[object]:
        from ..overlays.command_palette_manager import CommandEntry

        entries: List[CommandEntry] = []
        for descriptor in self._actions.values():
            entries.append(
                CommandEntry(
                    entry_id=descriptor.action_id,
                    title=descriptor.label,
                    action=lambda _descriptor=descriptor, _context=context: _descriptor.invoke(_context),
                    description=descriptor.description,
                    category=descriptor.category,
                )
            )
        return entries

    def context_menu_items(self, *, context: Any = None, category: str | None = None) -> List[object]:
        from ..overlays.context_menu_manager import ContextMenuItem

        items: List[ContextMenuItem] = []
        for descriptor in self._actions.values():
            if category is not None and str(descriptor.category) != str(category):
                continue
            items.append(
                ContextMenuItem(
                    descriptor.label,
                    action=lambda _descriptor=descriptor, _context=context: _descriptor.invoke(_context),
                    enabled=descriptor.is_enabled(context),
                )
            )
        return items

    def to_dict(self) -> Dict[str, Mapping[str, Any]]:
        return {
            action_id: {
                "action_id": descriptor.action_id,
                "label": descriptor.label,
                "category": descriptor.category,
                "shortcut_hint": descriptor.shortcut_hint,
                "description": descriptor.description,
                "enabled": descriptor.is_enabled(None),
                "checked": descriptor.is_checked(None),
                "metadata": dict(descriptor.metadata),
            }
            for action_id, descriptor in self._actions.items()
        }
