"""
Declarative presenter control builders for specs-driven UI.
User code only provides minimal specs; all registration and instantiation is automatic.
"""
from typing import Any, Dict, Callable

class ControlFactory:
    def __init__(self, registry: Dict[str, Callable]):
        self.registry = registry

    def create(self, spec: Dict[str, Any]):
        ctrl_type = spec["type"]
        builder = self.registry[ctrl_type]

        # Accept either {"type": ..., "params": {...}} or compact specs where
        # all fields besides `type` are treated as constructor parameters.
        params = spec.get("params")
        if params is None:
            params = {key: value for key, value in spec.items() if key != "type"}
        return builder(**params)

class PanelPresenterMixin:
    def on_create(self, content_rect, controls):
        for ctrl in controls:
            ctrl.place(content_rect)


def register_control_from_spec(registry: Dict[str, Callable], spec: Dict[str, Any]):
    ctrl_type = spec["type"]
    registry[ctrl_type] = lambda **params: spec["factory"](**params)
