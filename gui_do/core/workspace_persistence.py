"""Workspace persistence — coordinated save/restore of scene, feature, and settings state."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .scene_snapshot import SceneSnapshot
from ..layout.dock_workspace import DockWorkspace


@dataclass(slots=True)
class WorkspaceState:
    """Serializable workspace/session payload."""

    version: int = 1
    active_scene_name: str = "default"
    scene_snapshot: Dict[str, Any] = field(default_factory=dict)
    feature_states: Dict[str, dict] = field(default_factory=dict)
    settings_blocks: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    dock_state: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": int(self.version),
            "active_scene_name": str(self.active_scene_name),
            "scene_snapshot": dict(self.scene_snapshot),
            "feature_states": {k: dict(v) for k, v in self.feature_states.items()},
            "settings_blocks": {k: dict(v) for k, v in self.settings_blocks.items()},
            "metadata": dict(self.metadata),
            "dock_state": dict(self.dock_state),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkspaceState":
        return cls(
            version=int(data.get("version", 1)),
            active_scene_name=str(data.get("active_scene_name", "default")),
            scene_snapshot=dict(data.get("scene_snapshot", {})),
            feature_states={str(k): dict(v) for k, v in dict(data.get("feature_states", {})).items() if isinstance(v, dict)},
            settings_blocks={str(k): dict(v) for k, v in dict(data.get("settings_blocks", {})).items() if isinstance(v, dict)},
            metadata=dict(data.get("metadata", {})),
            dock_state=dict(data.get("dock_state", {})),
        )

    def save(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "WorkspaceState":
        location = Path(path)
        if not location.exists():
            return cls()
        return cls.from_dict(json.loads(location.read_text(encoding="utf-8")))


class WorkspacePersistenceManager:
    """Coordinates save/restore across scene snapshots, features, and settings."""

    def __init__(self) -> None:
        self._settings_registries: Dict[str, object] = {}

    def register_settings(self, block_name: str, registry) -> None:
        name = str(block_name).strip()
        if not name:
            raise ValueError("block_name must be a non-empty string")
        self._settings_registries[name] = registry

    def unregister_settings(self, block_name: str) -> bool:
        return bool(self._settings_registries.pop(str(block_name), None))

    def registered_blocks(self) -> List[str]:
        return sorted(self._settings_registries.keys())

    def capture(self, app, *, feature_manager=None, metadata: Optional[Dict[str, Any]] = None) -> WorkspaceState:
        scene_snapshot = SceneSnapshot.capture(app.scene).to_dict()
        feature_states = {} if feature_manager is None else feature_manager.save_feature_states()
        settings_blocks: Dict[str, Dict[str, Any]] = {}
        for block_name, registry in self._settings_registries.items():
            settings_blocks[block_name] = self._registry_values(registry)
        return WorkspaceState(
            active_scene_name=str(app.active_scene_name),
            scene_snapshot=scene_snapshot,
            feature_states=feature_states,
            settings_blocks=settings_blocks,
            metadata=dict(metadata or {}),
        )

    def restore(self, state: WorkspaceState, app, *, feature_manager=None) -> None:
        if str(app.active_scene_name) != str(state.active_scene_name):
            app.switch_scene(state.active_scene_name)
        if feature_manager is not None:
            feature_manager.restore_feature_states(state.feature_states)
        snapshot = SceneSnapshot.from_dict(state.scene_snapshot)
        snapshot.restore(app.scene)
        for block_name, values in state.settings_blocks.items():
            registry = self._settings_registries.get(block_name)
            if registry is None:
                continue
            for namespace, namespace_values in values.items():
                if not isinstance(namespace_values, dict):
                    continue
                for key, value in namespace_values.items():
                    try:
                        registry.set_value(namespace, key, value)
                    except KeyError:
                        continue

    @staticmethod
    def _registry_values(registry) -> Dict[str, Dict[str, Any]]:
        result: Dict[str, Dict[str, Any]] = {}
        for namespace in registry.namespaces():
            result[namespace] = {}
            for key in registry.keys(namespace):
                result[namespace][key] = registry.get_value(namespace, key)
        return result

    # ------------------------------------------------------------------
    # DockWorkspace integration
    # ------------------------------------------------------------------

    @staticmethod
    def capture_dock(workspace: DockWorkspace) -> Dict[str, Any]:
        """Serialize a :class:`DockWorkspace` layout to a plain dict.

        The returned dict can be stored in :attr:`WorkspaceState.dock_state`
        and later passed to :meth:`restore_dock` to reconstruct the layout.
        """
        return workspace.to_dict()

    @staticmethod
    def restore_dock(data: Dict[str, Any], workspace: DockWorkspace) -> None:
        """Apply a previously captured dock layout to an existing *workspace*.

        The workspace root is replaced with the deserialized layout.
        """
        restored = DockWorkspace.from_dict(data)
        workspace.root = restored.root
