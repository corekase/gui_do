"""Shared Part abstractions for managed lifecycle composition."""

from __future__ import annotations

from collections import OrderedDict, deque
from copy import deepcopy
from typing import Any, Callable, Deque, Dict, Iterable, Optional


class Part:
    """Base unit for managed GUI lifecycle composition."""

    HOST_REQUIREMENTS: Dict[str, tuple[str, ...]] = {}

    def __init__(self, name: str, *, scene_name: Optional[str] = None) -> None:
        normalized = str(name).strip()
        if not normalized:
            raise ValueError("part name must be a non-empty string")
        self.name = normalized
        if scene_name is None:
            self.scene_name = None
        else:
            normalized_scene_name = str(scene_name).strip()
            if not normalized_scene_name:
                raise ValueError("scene_name must be a non-empty string when provided")
            self.scene_name = normalized_scene_name
        self._part_manager = None
        self._message_queue: Deque[Dict[str, Any]] = deque()
        self._font_roles: Dict[str, str] = {}

    def on_register(self, host) -> None:
        return None

    def on_unregister(self, host) -> None:
        return None

    def build(self, host) -> None:
        return None

    def bind_runtime(self, host) -> None:
        return None

    def configure_accessibility(self, host, tab_index_start: int) -> int:
        return int(tab_index_start)

    def shutdown_runtime(self, host) -> None:
        return None

    def handle_event(self, host, event) -> bool:
        return False

    def on_update(self, host) -> None:
        return None

    def draw(self, host, surface, theme) -> None:
        return None

    def send_message(self, target_part_name: str, message: Dict[str, Any]) -> bool:
        if self._part_manager is None:
            return False
        return self._part_manager.send_message(self.name, target_part_name, message)

    def enqueue_message(self, message: Dict[str, Any]) -> None:
        if not isinstance(message, dict):
            raise TypeError("part messages must be dictionaries")
        self._message_queue.append(deepcopy(message))

    def has_messages(self) -> bool:
        return bool(self._message_queue)

    def message_queue_empty(self) -> bool:
        return not self._message_queue

    def message_count(self) -> int:
        return len(self._message_queue)

    def peek_message(self) -> Optional[Dict[str, Any]]:
        if not self._message_queue:
            return None
        return deepcopy(self._message_queue[0])

    def pop_message(self) -> Optional[Dict[str, Any]]:
        if not self._message_queue:
            return None
        return self._message_queue.popleft()

    def clear_messages(self) -> None:
        self._message_queue.clear()

    def register_font_role(
        self,
        host,
        role_name: str,
        *,
        size: int,
        file_path: Optional[str] = None,
        system_name: Optional[str] = None,
        bold: bool = False,
        italic: bool = False,
        scene_name: Optional[str] = None,
    ) -> str:
        """Register one namespaced font role owned by this part."""
        local_name = self._normalize_font_role_name(role_name)
        app = self._resolve_app(host)
        qualified_name = f"part.{self.name}.{local_name}"
        app.register_font_role(
            qualified_name,
            size=size,
            file_path=file_path,
            system_name=system_name,
            bold=bold,
            italic=italic,
            scene_name=scene_name,
        )
        self._font_roles[local_name] = qualified_name
        return qualified_name

    def register_font_roles(self, host, roles: Dict[str, Dict[str, Any]], *, scene_name: Optional[str] = None) -> Dict[str, str]:
        """Register multiple namespaced font roles owned by this part."""
        registered: Dict[str, str] = {}
        for role_name, spec in dict(roles).items():
            if not isinstance(spec, dict):
                raise TypeError("font role definitions must be dictionaries")
            registered[role_name] = self.register_font_role(
                host,
                role_name,
                size=spec["size"],
                file_path=spec.get("file_path"),
                system_name=spec.get("system_name"),
                bold=bool(spec.get("bold", False)),
                italic=bool(spec.get("italic", False)),
                scene_name=scene_name,
            )
        return registered

    def font_role(self, role_name: str) -> str:
        """Resolve a local part font role name to its registered global role."""
        local_name = self._normalize_font_role_name(role_name)
        qualified_name = self._font_roles.get(local_name)
        if qualified_name is None:
            raise KeyError(f"unknown part font role: {self.name}.{local_name}")
        return qualified_name

    @staticmethod
    def _normalize_font_role_name(role_name: str) -> str:
        normalized = str(role_name).strip()
        if not normalized:
            raise ValueError("font role name must be a non-empty string")
        return normalized

    @staticmethod
    def _resolve_app(host):
        app = getattr(host, "app", host)
        if not hasattr(app, "register_font_role"):
            raise AttributeError("host does not expose an application with register_font_role()")
        return app

    def host_requirements_for(self, hook_name: str) -> tuple[str, ...]:
        """Return required host field names for a lifecycle hook."""
        requirements = dict(getattr(self, "HOST_REQUIREMENTS", {}))
        required = requirements.get(str(hook_name), ())
        return tuple(str(name) for name in required)

    def validate_host_for(self, host, hook_name: str) -> None:
        """Validate required host fields for one lifecycle hook."""
        required_fields = self.host_requirements_for(hook_name)
        if not required_fields:
            return
        missing = [name for name in required_fields if not hasattr(host, name)]
        if not missing:
            return
        missing_csv = ", ".join(missing)
        raise AttributeError(f"{self.__class__.__name__}.{hook_name} requires host fields: {missing_csv}")


class PartManager:
    """Coordinates lifecycle, messaging, and utility registrations for parts."""

    def __init__(self, app) -> None:
        self.app = app
        self._parts: "OrderedDict[str, Part]" = OrderedDict()
        self._part_hosts: Dict[str, object] = {}
        self._runnables: Dict[str, Dict[str, Callable[..., Any]]] = {}
        self._runtime_bound_parts: set[str] = set()

    def register(self, part: Part, host=None) -> Part:
        if not isinstance(part, Part):
            raise TypeError("register expects a Part instance")
        if part.name in self._parts:
            raise ValueError(f"part already registered: {part.name}")
        part._part_manager = self
        self._parts[part.name] = part
        host_obj = self.app if host is None else host
        self._part_hosts[part.name] = host_obj
        self._runtime_bound_parts.discard(part.name)
        part.on_register(host_obj)
        return part

    def unregister(self, name: str, host=None) -> bool:
        key = str(name)
        part = self._parts.get(key)
        if part is None:
            return False
        host_obj = self._part_hosts.get(part.name)
        if host_obj is None:
            host_obj = self.app if host is None else host
        if part.name in self._runtime_bound_parts:
            part.shutdown_runtime(host_obj)
        part.on_unregister(host_obj)
        self._parts.pop(key, None)
        self._part_hosts.pop(part.name, None)
        self._runtime_bound_parts.discard(part.name)
        part._part_manager = None
        self._runnables.pop(part.name, None)
        return True

    def get(self, name: str) -> Optional[Part]:
        return self._parts.get(str(name))

    def names(self) -> tuple[str, ...]:
        return tuple(self._parts.keys())

    def parts(self) -> Iterable[Part]:
        return tuple(self._parts.values())

    def send_message(self, sender_name: str, target_part_name: str, message: Dict[str, Any]) -> bool:
        target = self._parts.get(str(target_part_name))
        if target is None:
            return False
        payload = dict(message)
        payload.setdefault("_from", str(sender_name))
        payload.setdefault("_to", target.name)
        target.enqueue_message(payload)
        return True

    def register_runnable(self, part_name: str, runnable_name: str, runnable: Callable[..., Any]) -> None:
        self._require_part(part_name)
        if not callable(runnable):
            raise TypeError("runnable must be callable")
        name = str(runnable_name).strip()
        if not name:
            raise ValueError("runnable_name must be a non-empty string")
        bucket = self._runnables.setdefault(str(part_name), {})
        bucket[name] = runnable

    def run(self, part_name: str, runnable_name: str, *args, **kwargs) -> Any:
        part_bucket = self._runnables.get(str(part_name), {})
        runnable = part_bucket.get(str(runnable_name))
        if runnable is None:
            raise KeyError(f"unknown runnable: {part_name}.{runnable_name}")
        return runnable(*args, **kwargs)

    def handle_event(self, event, host=None) -> bool:
        for part in self._parts.values():
            if not self._is_part_active_for_scene(part):
                continue
            host_obj = self._resolve_host(part.name, host)
            if part.handle_event(host_obj, event):
                return True
        return False

    def update_parts(self, host=None) -> None:
        for part in self._parts.values():
            if not self._is_part_active_for_scene(part):
                continue
            host_obj = self._resolve_host(part.name, host)
            part.on_update(host_obj)

    def draw(self, surface, theme, host=None) -> None:
        for part in self._parts.values():
            if not self._is_part_active_for_scene(part):
                continue
            host_obj = self._resolve_host(part.name, host)
            part.draw(host_obj, surface, theme)

    def build_parts(self, host) -> None:
        for part in self._parts.values():
            part.validate_host_for(host, "build")
            part.build(host)

    def bind_runtime(self, host) -> None:
        for part in self._parts.values():
            part.validate_host_for(host, "bind_runtime")
            part.bind_runtime(host)
            self._runtime_bound_parts.add(part.name)

    def shutdown_runtime(self, host=None) -> None:
        """Call shutdown_runtime(host) for parts with active runtime bindings."""
        for part in reversed(tuple(self._parts.values())):
            if part.name not in self._runtime_bound_parts:
                continue
            host_obj = self._resolve_host(part.name, host)
            part.shutdown_runtime(host_obj)
            self._runtime_bound_parts.discard(part.name)

    def configure_accessibility(self, host, tab_index_start: int) -> int:
        next_index = int(tab_index_start)
        for part in self._parts.values():
            part.validate_host_for(host, "configure_accessibility")
            next_index = int(part.configure_accessibility(host, next_index))
        return next_index

    def _require_part(self, part_name: str) -> Part:
        part = self.get(part_name)
        if part is None:
            raise KeyError(f"unknown part: {part_name}")
        return part

    def _resolve_host(self, part_name: str, override_host=None):
        if override_host is not None:
            return override_host
        return self._part_hosts.get(part_name, self.app)

    def _is_part_active_for_scene(self, part: Part) -> bool:
        scene_name = getattr(part, "scene_name", None)
        if scene_name is None:
            return True
        return str(scene_name) == str(self.app.active_scene_name)
