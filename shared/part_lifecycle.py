"""Shared Part abstractions for managed lifecycle composition."""

from __future__ import annotations

from collections import OrderedDict, deque
from copy import deepcopy
from typing import Any, Callable, Deque, Dict, Iterable, Optional


class Part:
    """Base unit for managed GUI lifecycle composition."""

    def __init__(self, name: str) -> None:
        normalized = str(name).strip()
        if not normalized:
            raise ValueError("part name must be a non-empty string")
        self.name = normalized
        self._part_manager = None
        self._message_queue: Deque[Dict[str, Any]] = deque()

    def on_register(self, host) -> None:
        return None

    def on_unregister(self, host) -> None:
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


class PartManager:
    """Coordinates lifecycle, messaging, and utility registrations for parts."""

    def __init__(self, app) -> None:
        self.app = app
        self._parts: "OrderedDict[str, Part]" = OrderedDict()
        self._part_hosts: Dict[str, object] = {}
        self._runnables: Dict[str, Dict[str, Callable[..., Any]]] = {}

    def register(self, part: Part, host=None) -> Part:
        if not isinstance(part, Part):
            raise TypeError("register expects a Part instance")
        if part.name in self._parts:
            raise ValueError(f"part already registered: {part.name}")
        part._part_manager = self
        self._parts[part.name] = part
        host_obj = self.app if host is None else host
        self._part_hosts[part.name] = host_obj
        part.on_register(host_obj)
        return part

    def unregister(self, name: str, host=None) -> bool:
        part = self._parts.pop(str(name), None)
        if part is None:
            return False
        host_obj = self._part_hosts.pop(part.name, None)
        if host_obj is None:
            host_obj = self.app if host is None else host
        part.on_unregister(host_obj)
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

    def register_scene_node(self, part_name: str, node, scene_name: Optional[str] = None):
        self._require_part(part_name)
        return self.app.add(node, scene_name=scene_name)

    def register_window(self, part_name: str, window, scene_name: Optional[str] = None):
        self._require_part(part_name)
        return self.app.add(window, scene_name=scene_name)

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
            host_obj = self._resolve_host(part.name, host)
            if part.handle_event(host_obj, event):
                return True
        return False

    def update_parts(self, host=None) -> None:
        for part in self._parts.values():
            host_obj = self._resolve_host(part.name, host)
            part.on_update(host_obj)

    def draw(self, surface, theme, host=None) -> None:
        for part in self._parts.values():
            host_obj = self._resolve_host(part.name, host)
            part.draw(host_obj, surface, theme)

    def build_parts(self, host) -> None:
        for part in self._parts.values():
            build = getattr(part, "build", None)
            if callable(build):
                build(host)

    def bind_runtime(self, host) -> None:
        for part in self._parts.values():
            bind = getattr(part, "bind_runtime", None)
            if callable(bind):
                bind(host)

    def configure_accessibility(self, host, tab_index_start: int) -> int:
        next_index = int(tab_index_start)
        for part in self._parts.values():
            configure = getattr(part, "configure_accessibility", None)
            if callable(configure):
                next_index = int(configure(host, next_index))
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
