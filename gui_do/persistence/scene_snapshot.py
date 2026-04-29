"""SceneSnapshot — serialise and restore UiNode state in a scene graph.

Captures the rect, visibility, and enabled-state of nodes identified by
``control_id`` and restores them later.  Integrates with
:class:`~gui_do.CommandHistory` for structural undo/redo, and with
:class:`~gui_do.SettingsRegistry` for workspace persistence.

Only *data* state is serialised — behaviour (callbacks, closures, subscriptions)
is not touched.  This makes snapshots safe to round-trip across serialisation
boundaries.

Usage::

    from gui_do import SceneSnapshot

    # Capture current state of all nodes in the scene:
    snap = SceneSnapshot.capture(app.scene)

    # … user moves/resizes controls …

    # Restore:
    restored_count = snap.restore(app.scene)

    # Persist to disk:
    snap.save("workspace.json")

    # Load and restore on next launch:
    snap2 = SceneSnapshot.load("workspace.json")
    snap2.restore(app.scene)

    # Integrate with CommandHistory:
    class RestoreSnapshotCommand:
        description = "Restore layout"
        def __init__(self, before, after, scene):
            self._before = before
            self._after  = after
            self._scene  = scene
        def execute(self): self._after.restore(self._scene)
        def undo(self):    self._before.restore(self._scene)
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set


# ---------------------------------------------------------------------------
# NodeSnapshot
# ---------------------------------------------------------------------------


@dataclass
class NodeSnapshot:
    """Serialisable state for one :class:`~gui_do.UiNode`.

    Attributes
    ----------
    control_id:
        Matches :attr:`~gui_do.UiNode.control_id`.
    rect:
        ``(x, y, w, h)`` tuple.
    visible:
        Visibility state.
    enabled:
        Enabled state.
    extra:
        Optional application-specific key/value pairs (strings only for
        JSON safety).
    """

    control_id: str
    rect: List[int]          # [x, y, w, h]
    visible: bool = True
    enabled: bool = True
    extra: Dict[str, str] = None   # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.extra is None:
            self.extra = {}


# ---------------------------------------------------------------------------
# SceneSnapshot
# ---------------------------------------------------------------------------


class SceneSnapshot:
    """A point-in-time snapshot of selected nodes' rect/visibility/enabled state.

    Parameters
    ----------
    entries:
        Mapping of ``control_id`` → :class:`NodeSnapshot`.
    """

    def __init__(self, entries: Optional[Dict[str, NodeSnapshot]] = None) -> None:
        self._entries: Dict[str, NodeSnapshot] = entries or {}

    # ------------------------------------------------------------------
    # Capture
    # ------------------------------------------------------------------

    @staticmethod
    def capture(
        scene: object,
        *,
        include_ids: Optional[Set[str]] = None,
    ) -> "SceneSnapshot":
        """Capture current state from all (or selected) nodes in *scene*.

        Parameters
        ----------
        scene:
            A :class:`~gui_do.Scene` instance (or any object with a
            ``_walk_nodes()`` generator).
        include_ids:
            When supplied, only nodes whose ``control_id`` is in this set are
            captured.  Pass ``None`` to capture all nodes.
        """
        entries: Dict[str, NodeSnapshot] = {}
        if scene is None:
            return SceneSnapshot(entries)
        for node in scene._walk_nodes():   # noqa: SLF001
            cid = getattr(node, "control_id", None)
            if cid is None:
                continue
            if include_ids is not None and cid not in include_ids:
                continue
            rect = getattr(node, "rect", None)
            if rect is not None:
                r = [int(rect.x), int(rect.y), int(rect.width), int(rect.height)]
            else:
                r = [0, 0, 0, 0]
            entries[cid] = NodeSnapshot(
                control_id=cid,
                rect=r,
                visible=bool(getattr(node, "visible", True)),
                enabled=bool(getattr(node, "enabled", True)),
            )
        return SceneSnapshot(entries)

    @staticmethod
    def from_nodes(nodes: Iterable) -> "SceneSnapshot":
        """Capture state from an explicit iterable of nodes."""
        entries: Dict[str, NodeSnapshot] = {}
        for node in nodes:
            cid = getattr(node, "control_id", None)
            if cid is None:
                continue
            rect = getattr(node, "rect", None)
            r = [int(rect.x), int(rect.y), int(rect.width), int(rect.height)] if rect else [0, 0, 0, 0]
            entries[cid] = NodeSnapshot(
                control_id=cid,
                rect=r,
                visible=bool(getattr(node, "visible", True)),
                enabled=bool(getattr(node, "enabled", True)),
            )
        return SceneSnapshot(entries)

    # ------------------------------------------------------------------
    # Restore
    # ------------------------------------------------------------------

    def restore(self, scene: object) -> int:
        """Apply stored state back to matching nodes in *scene*.

        Returns the number of nodes whose state was updated.
        """
        if scene is None or not self._entries:
            return 0
        updated = 0
        for node in scene._walk_nodes():   # noqa: SLF001
            cid = getattr(node, "control_id", None)
            if cid is None:
                continue
            snap = self._entries.get(cid)
            if snap is None:
                continue
            rect = getattr(node, "rect", None)
            if rect is not None:
                rect.x, rect.y = snap.rect[0], snap.rect[1]
                rect.width, rect.height = snap.rect[2], snap.rect[3]
            node.visible = snap.visible
            node.enabled = snap.enabled
            try:
                node.invalidate()
            except Exception:
                pass
            updated += 1
        return updated

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        """Return a JSON-serialisable dict representation."""
        return {cid: asdict(snap) for cid, snap in self._entries.items()}

    @staticmethod
    def from_dict(data: dict) -> "SceneSnapshot":
        """Reconstruct a :class:`SceneSnapshot` from a :meth:`to_dict` result."""
        entries = {cid: NodeSnapshot(**v) for cid, v in data.items()}
        return SceneSnapshot(entries)

    def save(self, path: "str | Path") -> None:
        """Write this snapshot to a JSON file."""
        Path(path).write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

    @staticmethod
    def load(path: "str | Path") -> "SceneSnapshot":
        """Load a snapshot from a JSON file written by :meth:`save`.

        Returns an empty snapshot if the file does not exist.
        """
        p = Path(path)
        if not p.exists():
            return SceneSnapshot()
        data = json.loads(p.read_text(encoding="utf-8"))
        return SceneSnapshot.from_dict(data)

    # ------------------------------------------------------------------
    # Inspection
    # ------------------------------------------------------------------

    @property
    def node_ids(self) -> List[str]:
        """Sorted list of captured ``control_id`` values."""
        return sorted(self._entries.keys())

    def get(self, control_id: str) -> Optional[NodeSnapshot]:
        """Return the :class:`NodeSnapshot` for *control_id*, or ``None``."""
        return self._entries.get(control_id)

    def __len__(self) -> int:
        return len(self._entries)

    def __contains__(self, control_id: str) -> bool:
        return control_id in self._entries
