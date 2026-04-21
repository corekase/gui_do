from typing import List

from .ui_node import UiNode


class Scene:
    """Top-level scene graph container."""

    def __init__(self) -> None:
        self.nodes: List[UiNode] = []

    def add(self, node: UiNode) -> UiNode:
        self.nodes.append(node)
        return node

    def update(self, dt_seconds: float) -> None:
        for node in self.nodes:
            if node.visible:
                node.update(dt_seconds)

    def dispatch(self, event, app) -> bool:
        for node in reversed(self.nodes):
            if node.visible and node.enabled and node.handle_event(event, app):
                return True
        return False

    def draw(self, surface, theme) -> None:
        for node in self.nodes:
            if node.visible:
                node.draw(surface, theme)
