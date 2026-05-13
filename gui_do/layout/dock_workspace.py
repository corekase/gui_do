"""Dock workspace — portable pane/tab/split layout model."""
from __future__ import annotations

from dataclasses import dataclass, field
from .layout_registry import LayoutRegistry
from typing import Any, Dict, List, Optional, Union


@dataclass(slots=True)
class DockPane:
    pane_id: str
    title: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kind": "pane",
            "pane_id": self.pane_id,
            "title": self.title,
            "payload": dict(self.payload),
        }


@dataclass(slots=True)
class DockTabs:
    tabs_id: str
    panes: List[DockPane] = field(default_factory=list)
    active_pane_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.active_pane_id is None and self.panes:
            self.active_pane_id = self.panes[0].pane_id

    def add_pane(self, pane: DockPane) -> None:
        self.panes.append(pane)
        if self.active_pane_id is None:
            self.active_pane_id = pane.pane_id

    def remove_pane(self, pane_id: str) -> bool:
        target = str(pane_id)
        before = len(self.panes)
        self.panes = [pane for pane in self.panes if pane.pane_id != target]
        if len(self.panes) == before:
            return False
        if self.active_pane_id == target:
            self.active_pane_id = self.panes[0].pane_id if self.panes else None
        return True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kind": "tabs",
            "tabs_id": self.tabs_id,
            "panes": [pane.to_dict() for pane in self.panes],
            "active_pane_id": self.active_pane_id,
        }


DockNode = Union[DockPane, DockTabs, "DockSplit"]


@dataclass(slots=True)
class DockSplit:
    axis: str
    children: List[DockNode] = field(default_factory=list)
    ratios: List[float] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.axis not in {"horizontal", "vertical"}:
            raise ValueError("axis must be 'horizontal' or 'vertical'")
        if not self.ratios and self.children:
            portion = 1.0 / len(self.children)
            self.ratios = [portion for _ in self.children]
        if self.children and len(self.children) != len(self.ratios):
            raise ValueError("children and ratios must have matching lengths")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kind": "split",
            "axis": self.axis,
            "children": [DockWorkspace.node_to_dict(child) for child in self.children],
            "ratios": list(self.ratios),
        }



class DockWorkspace:
    """Serializable docking layout model for panes, tabs, and splits, with standardized padding, inset, and margin."""

    def __init__(self, root: DockNode | None = None, *, padding: int = 0, inset: int | tuple = 0, margin: int | tuple = 0) -> None:
        self.root = root
        self._padding: int = int(padding)
        self._inset = self._parse_box_param(inset)
        self._margin = self._parse_box_param(margin)

    @staticmethod
    def _parse_box_param(val):
        if isinstance(val, int):
            return (val, val, val, val)
        if isinstance(val, (tuple, list)) and len(val) == 4:
            return tuple(int(x) for x in val)
        return (0, 0, 0, 0)

    def adjust_container(self, container_rect):
        pad = self._padding
        inset_l, inset_t, inset_r, inset_b = self._inset
        margin_l, margin_t, margin_r, margin_b = self._margin
        return (
            container_rect.x + pad + inset_l + margin_l,
            container_rect.y + pad + inset_t + margin_t,
            container_rect.width - 2 * pad - inset_l - inset_r - margin_l - margin_r,
            container_rect.height - 2 * pad - inset_t - inset_b - margin_t - margin_b,
        )

    def pane_ids(self) -> List[str]:
        return sorted(self._collect_panes(self.root).keys())

    def find_pane(self, pane_id: str) -> Optional[DockPane]:
        return self._collect_panes(self.root).get(str(pane_id))

    def to_dict(self) -> Dict[str, Any]:
        return {"root": None if self.root is None else self.node_to_dict(self.root)}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DockWorkspace":
        root = data.get("root")
        if root is None:
            return cls()
        return cls(root=cls.node_from_dict(root))

    @classmethod
    def node_to_dict(cls, node: DockNode) -> Dict[str, Any]:
        return node.to_dict()

    @classmethod
    def node_from_dict(cls, data: Dict[str, Any]) -> DockNode:
        kind = str(data.get("kind", "")).strip()
        if kind == "pane":
            return DockPane(
                pane_id=str(data.get("pane_id", "")),
                title=str(data.get("title", "")),
                payload=dict(data.get("payload", {})),
            )
        if kind == "tabs":
            return DockTabs(
                tabs_id=str(data.get("tabs_id", "")),
                panes=[cls.node_from_dict(item) for item in list(data.get("panes", []))],
                active_pane_id=data.get("active_pane_id"),
            )
        if kind == "split":
            return DockSplit(
                axis=str(data.get("axis", "horizontal")),
                children=[cls.node_from_dict(item) for item in list(data.get("children", []))],
                ratios=[float(value) for value in list(data.get("ratios", []))],
            )
        raise ValueError(f"Unknown dock node kind: {kind!r}")

    def remove_pane(self, pane_id: str) -> bool:
        target = str(pane_id)
        new_root, removed = self._remove_pane(self.root, target)
        self.root = new_root
        return removed

    def _remove_pane(self, node: DockNode | None, pane_id: str) -> tuple[DockNode | None, bool]:
        if node is None:
            return None, False
        if isinstance(node, DockPane):
            return (None, True) if node.pane_id == pane_id else (node, False)
        if isinstance(node, DockTabs):
            removed = node.remove_pane(pane_id)
            if not node.panes:
                return None, removed
            if len(node.panes) == 1:
                return node.panes[0], removed
            return node, removed
        new_children: List[DockNode] = []
        removed_any = False
        new_ratios: List[float] = []
        for child, ratio in zip(node.children, node.ratios):
            new_child, removed = self._remove_pane(child, pane_id)
            removed_any = removed_any or removed
            if new_child is not None:
                new_children.append(new_child)
                new_ratios.append(ratio)
        node.children = new_children
        if not new_children:
            return None, removed_any
        if len(new_children) == 1:
            return new_children[0], removed_any
        total = sum(new_ratios) or 1.0
        node.ratios = [ratio / total for ratio in new_ratios]
        return node, removed_any

    @staticmethod
    def _collect_panes(node: DockNode | None) -> Dict[str, DockPane]:
        result: Dict[str, DockPane] = {}
        if node is None:
            return result
        if isinstance(node, DockPane):
            result[node.pane_id] = node
            return result
        if isinstance(node, DockTabs):
            for pane in node.panes:
                result[pane.pane_id] = pane
            return result
        for child in node.children:
            result.update(DockWorkspace._collect_panes(child))
        return result

    def __init__(self, root: DockNode | None = None, *, padding: int = 0, inset: int | tuple = 0, margin: int | tuple = 0) -> None:
        self.root = root
        self._padding: int = int(padding)
        self._inset = self._parse_box_param(inset)
        self._margin = self._parse_box_param(margin)

    @staticmethod
    def _parse_box_param(val):
        if isinstance(val, int):
            return (val, val, val, val)
        if isinstance(val, (tuple, list)) and len(val) == 4:
            return tuple(int(x) for x in val)
        return (0, 0, 0, 0)


    def adjust_container(self, container_rect):
        pad = self._padding
        inset_l, inset_t, inset_r, inset_b = self._inset
        margin_l, margin_t, margin_r, margin_b = self._margin
        return (
            container_rect.x + pad + inset_l + margin_l,
            container_rect.y + pad + inset_t + margin_t,
            container_rect.width - 2 * pad - inset_l - inset_r - margin_l - margin_r,
            container_rect.height - 2 * pad - inset_t - inset_b - margin_t - margin_b,
        )

    def pane_ids(self) -> List[str]:
        return sorted(self._collect_panes(self.root).keys())

    def find_pane(self, pane_id: str) -> Optional[DockPane]:
        return self._collect_panes(self.root).get(str(pane_id))

    def to_dict(self) -> Dict[str, Any]:
        return {"root": None if self.root is None else self.node_to_dict(self.root)}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DockWorkspace":
        root = data.get("root")
        if root is None:
            return cls()
        return cls(root=cls.node_from_dict(root))

    @classmethod
    def node_to_dict(cls, node: DockNode) -> Dict[str, Any]:
        return node.to_dict()


    @classmethod
    def node_from_dict(cls, data: Dict[str, Any]) -> DockNode:
        kind = str(data.get("kind", "")).strip()
        if kind == "pane":
            return DockPane(
                pane_id=str(data.get("pane_id", "")),
                title=str(data.get("title", "")),
                payload=dict(data.get("payload", {})),
            )
        if kind == "tabs":
            return DockTabs(
                tabs_id=str(data.get("tabs_id", "")),
                panes=[cls.node_from_dict(item) for item in list(data.get("panes", []))],
                active_pane_id=data.get("active_pane_id"),
            )
        if kind == "split":
            return DockSplit(
                axis=str(data.get("axis", "horizontal")),
                children=[cls.node_from_dict(item) for item in list(data.get("children", []))],
                ratios=[float(value) for value in list(data.get("ratios", []))],
            )
        raise ValueError(f"Unknown dock node kind: {kind!r}")



# Register in LayoutRegistry
LayoutRegistry.register('dock', DockWorkspace)
