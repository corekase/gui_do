"""Shared Part abstractions for managed lifecycle composition."""

from __future__ import annotations

from collections import OrderedDict, deque
from contextlib import nullcontext
from copy import deepcopy
import inspect
from time import perf_counter
from typing import Any, Callable, Deque, Dict, Iterable, Optional


class _NoopTelemetryCollector:
    def span(self, _system: str, _point: str, metadata: Optional[Dict[str, Any]] = None):
        del metadata
        return nullcontext()

    def record_duration(self, _system: str, _point: str, _elapsed_ms: float, *, metadata: Optional[Dict[str, Any]] = None) -> None:
        del metadata
        return None


def _telemetry_collector():
    try:
        from gui.core.telemetry import telemetry_collector

        return telemetry_collector()
    except Exception:
        return _NoopTelemetryCollector()


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

    def prewarm(self, host, surface, theme) -> None:
        return None

    def send_message(self, target_part_name: str, message: Dict[str, Any]) -> bool:
        if self._part_manager is None:
            return False
        return self._part_manager.send_message(self.name, target_part_name, message)

    def bind_logic_part(self, logic_part_name: str, *, alias: str = "default") -> None:
        if self._part_manager is None:
            raise RuntimeError("part must be registered before binding logic parts")
        self._part_manager.bind_logic_part(self.name, logic_part_name, alias=alias)

    def unbind_logic_part(self, *, alias: str = "default") -> bool:
        if self._part_manager is None:
            return False
        return self._part_manager.unbind_logic_part(self.name, alias=alias)

    def logic_part_name(self, *, alias: str = "default") -> Optional[str]:
        if self._part_manager is None:
            return None
        return self._part_manager.logic_part_name(self.name, alias=alias)

    def send_logic_message(self, message: Dict[str, Any], *, alias: str = "default") -> bool:
        if self._part_manager is None:
            return False
        return self._part_manager.send_logic_message(self.name, message, alias=alias)

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
        requirements = dict(self.HOST_REQUIREMENTS)
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


class ScreenPart(Part):
    """Part subtype for direct screen event/update/draw integration."""

    def handle_screen_event(self, host, event) -> bool:
        return False

    def on_screen_update(self, host, dt_seconds: float) -> None:
        return None

    def draw_screen(self, host, surface, theme) -> None:
        return None


class LogicPart(Part):
    """Part subtype for domain logic routed through message commands."""

    def on_logic_command(self, host, sender_name: str, command: str, payload: Dict[str, Any]) -> None:
        return None

    def on_update(self, host) -> None:
        while self.has_messages():
            message = self.pop_message()
            if not isinstance(message, dict):
                continue
            command = message.get("command")
            if not isinstance(command, str):
                continue
            self.on_logic_command(host, str(message.get("_from", "")), command, message)


class RoutedMessagePart(Part):
    """Part subtype that routes queued messages by a canonical topic key."""

    MESSAGE_TOPIC_KEY = "topic"

    def message_handlers(self) -> Dict[str, Callable[[Any, str, Dict[str, Any]], None]]:
        """Return mapping of topic names to message handlers."""
        return {}

    def on_message(self, host, sender_name: str, topic: str, payload: Dict[str, Any]) -> None:
        """Handle one routed message; unresolved topics are ignored by default."""
        handlers = self.message_handlers()
        handler = handlers.get(str(topic))
        if handler is None:
            return
        handler(host, str(sender_name), payload)

    def on_update(self, host) -> None:
        topic_key = str(self.MESSAGE_TOPIC_KEY)
        while self.has_messages():
            message = self.pop_message()
            if not isinstance(message, dict):
                continue
            topic = message.get(topic_key)
            if not isinstance(topic, str):
                continue
            self.on_message(host, str(message.get("_from", "")), topic, message)


class PartManager:
    """Coordinates lifecycle, messaging, and utility registrations for parts."""

    _HOST_PARAMETER_HOOKS = (
        "on_register",
        "on_unregister",
        "build",
        "bind_runtime",
        "configure_accessibility",
        "shutdown_runtime",
        "handle_event",
        "on_update",
        "draw",
        "handle_screen_event",
        "on_screen_update",
        "draw_screen",
        "on_logic_command",
        "on_message",
        "prewarm",
    )

    def __init__(self, app) -> None:
        self.app = app
        self._parts: "OrderedDict[str, Part]" = OrderedDict()
        self._part_hosts: Dict[str, object] = {}
        self._runnables: Dict[str, Dict[str, Callable[..., Any]]] = {}
        self._runtime_bound_parts: set[str] = set()
        self._logic_bindings: Dict[str, Dict[str, str]] = {}
        self._prewarmed_parts: set[tuple[str, str]] = set()

    def register(self, part: Part, host=None) -> Part:
        if not isinstance(part, Part):
            raise TypeError("register expects a Part instance")
        if part.name in self._parts:
            raise ValueError(f"part already registered: {part.name}")
        self._validate_host_parameter_contract(part)
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
        self._logic_bindings.pop(part.name, None)
        for consumer_name, alias_map in tuple(self._logic_bindings.items()):
            aliases_to_remove = [alias for alias, provider_name in alias_map.items() if provider_name == part.name]
            for alias in aliases_to_remove:
                alias_map.pop(alias, None)
            if not alias_map:
                self._logic_bindings.pop(consumer_name, None)
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
        collector = _telemetry_collector()
        topic = ""
        if isinstance(message, dict):
            raw_topic = message.get("topic")
            if isinstance(raw_topic, str):
                topic = raw_topic
        target = self._parts.get(str(target_part_name))
        if target is None:
            collector.record_duration(
                "part_lifecycle",
                "send_message_missing_target",
                0.0,
                metadata={"sender": str(sender_name), "target": str(target_part_name), "topic": topic},
            )
            return False
        with collector.span(
            "part_lifecycle",
            "send_message",
            metadata={"sender": str(sender_name), "target": target.name, "topic": topic},
        ):
            payload = dict(message)
            payload.setdefault("_from", str(sender_name))
            payload.setdefault("_to", target.name)
            target.enqueue_message(payload)
            collector.record_duration(
                "part_lifecycle",
                "target_queue_depth",
                0.0,
                metadata={"target": target.name, "queue_depth": target.message_count()},
            )
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

    def bind_logic_part(self, consumer_part_name: str, logic_part_name: str, *, alias: str = "default") -> None:
        consumer = self._require_part(consumer_part_name)
        provider = self._require_part(logic_part_name)
        if not isinstance(provider, LogicPart):
            raise TypeError(f"part is not a LogicPart: {provider.name}")
        alias_name = self._normalize_alias(alias)
        bucket = self._logic_bindings.setdefault(consumer.name, {})
        bucket[alias_name] = provider.name

    def unbind_logic_part(self, consumer_part_name: str, *, alias: str = "default") -> bool:
        alias_name = self._normalize_alias(alias)
        bucket = self._logic_bindings.get(str(consumer_part_name))
        if not bucket or alias_name not in bucket:
            return False
        bucket.pop(alias_name, None)
        if not bucket:
            self._logic_bindings.pop(str(consumer_part_name), None)
        return True

    def logic_part_name(self, consumer_part_name: str, *, alias: str = "default") -> Optional[str]:
        alias_name = self._normalize_alias(alias)
        bucket = self._logic_bindings.get(str(consumer_part_name), {})
        return bucket.get(alias_name)

    def send_logic_message(self, consumer_part_name: str, message: Dict[str, Any], *, alias: str = "default") -> bool:
        provider_name = self.logic_part_name(consumer_part_name, alias=alias)
        if provider_name is None:
            return False
        return self.send_message(str(consumer_part_name), provider_name, message)

    def run(self, part_name: str, runnable_name: str, *args, **kwargs) -> Any:
        part_bucket = self._runnables.get(str(part_name), {})
        runnable = part_bucket.get(str(runnable_name))
        if runnable is None:
            raise KeyError(f"unknown runnable: {part_name}.{runnable_name}")
        return runnable(*args, **kwargs)

    def handle_event(self, event, host=None) -> bool:
        collector = _telemetry_collector()
        for part in self._parts.values():
            if not self._is_part_active_for_scene(part):
                continue
            host_obj = self._resolve_host(part.name, host)
            with collector.span("part_lifecycle", "part_handle_event", metadata={"part_name": part.name}):
                if part.handle_event(host_obj, event):
                    return True
        return False

    def update_parts(self, host=None) -> None:
        collector = _telemetry_collector()
        for part in self._parts.values():
            if not self._is_part_active_for_scene(part):
                continue
            host_obj = self._resolve_host(part.name, host)
            with collector.span("part_lifecycle", "part_update", metadata={"part_name": part.name}):
                part.on_update(host_obj)

    def draw(self, surface, theme, host=None) -> None:
        collector = _telemetry_collector()
        for part in self._parts.values():
            if not self._is_part_active_for_scene(part):
                continue
            host_obj = self._resolve_host(part.name, host)
            with collector.span("part_lifecycle", "part_draw", metadata={"part_name": part.name}):
                part.draw(host_obj, surface, theme)

    def handle_screen_event(self, event, host=None) -> bool:
        collector = _telemetry_collector()
        for part in self._parts.values():
            if not isinstance(part, ScreenPart):
                continue
            if not self._is_part_active_for_scene(part):
                continue
            host_obj = self._resolve_host(part.name, host)
            with collector.span("part_lifecycle", "screen_part_handle_event", metadata={"part_name": part.name}):
                if part.handle_screen_event(host_obj, event):
                    return True
        return False

    def update_screen_parts(self, dt_seconds: float, host=None) -> None:
        collector = _telemetry_collector()
        for part in self._parts.values():
            if not isinstance(part, ScreenPart):
                continue
            if not self._is_part_active_for_scene(part):
                continue
            host_obj = self._resolve_host(part.name, host)
            with collector.span("part_lifecycle", "screen_part_update", metadata={"part_name": part.name}):
                part.on_screen_update(host_obj, dt_seconds)

    def draw_screen_parts(self, surface, theme, host=None) -> None:
        collector = _telemetry_collector()
        for part in self._parts.values():
            if not isinstance(part, ScreenPart):
                continue
            if not self._is_part_active_for_scene(part):
                continue
            host_obj = self._resolve_host(part.name, host)
            with collector.span("part_lifecycle", "screen_part_draw", metadata={"part_name": part.name}):
                part.draw_screen(host_obj, surface, theme)

    def prewarm_parts(self, host, surface, theme, *, scene_name: Optional[str] = None, force: bool = False) -> int:
        target_scene_name = str(self.app.active_scene_name if scene_name is None else scene_name)
        warmed = 0
        for part in self._parts.values():
            if not self._is_part_active_for_scene(part, scene_name=target_scene_name):
                continue
            cache_key = (part.name, target_scene_name)
            if cache_key in self._prewarmed_parts and not force:
                continue
            host_obj = self._resolve_host(part.name, host)
            part.validate_host_for(host_obj, "prewarm")
            start = perf_counter()
            part.prewarm(host_obj, surface, theme)
            elapsed_ms = (perf_counter() - start) * 1000.0
            self._record_prewarm_sample(target_scene_name, part.name, elapsed_ms)
            self._prewarmed_parts.add(cache_key)
            warmed += 1
        return warmed

    @staticmethod
    def _record_prewarm_sample(scene_name: str, part_name: str, elapsed_ms: float) -> None:
        try:
            from gui.core.first_frame_profiler import first_frame_profiler

            first_frame_profiler().record_once(
                "part.prewarm",
                f"{scene_name}:{part_name}",
                elapsed_ms,
                detail="part prewarm hook",
            )
        except Exception:
            return

    def build_parts(self, host) -> None:
        collector = _telemetry_collector()
        for part in self._parts.values():
            part.validate_host_for(host, "build")
            with collector.span("part_lifecycle", "part_build", metadata={"part_name": part.name}):
                part.build(host)

    def bind_runtime(self, host) -> None:
        collector = _telemetry_collector()
        for part in self._parts.values():
            part.validate_host_for(host, "bind_runtime")
            with collector.span("part_lifecycle", "part_bind_runtime", metadata={"part_name": part.name}):
                part.bind_runtime(host)
            self._runtime_bound_parts.add(part.name)

    def shutdown_runtime(self, host=None) -> None:
        """Call shutdown_runtime(host) for parts with active runtime bindings."""
        collector = _telemetry_collector()
        for part in reversed(tuple(self._parts.values())):
            if part.name not in self._runtime_bound_parts:
                continue
            host_obj = self._resolve_host(part.name, host)
            with collector.span("part_lifecycle", "part_shutdown_runtime", metadata={"part_name": part.name}):
                part.shutdown_runtime(host_obj)
            self._runtime_bound_parts.discard(part.name)

    def configure_accessibility(self, host, tab_index_start: int) -> int:
        collector = _telemetry_collector()
        next_index = int(tab_index_start)
        for part in self._parts.values():
            part.validate_host_for(host, "configure_accessibility")
            with collector.span("part_lifecycle", "part_configure_accessibility", metadata={"part_name": part.name}):
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

    def _is_part_active_for_scene(self, part: Part, *, scene_name: Optional[str] = None) -> bool:
        target_scene_name = self.app.active_scene_name if scene_name is None else scene_name
        scene_name = part.scene_name
        if scene_name is None:
            return True
        return str(scene_name) == str(target_scene_name)

    @classmethod
    def _validate_host_parameter_contract(cls, part: Part) -> None:
        for hook_name in cls._HOST_PARAMETER_HOOKS:
            method = getattr(part, hook_name, None)
            if method is None or not callable(method):
                continue
            try:
                signature = inspect.signature(method)
            except (TypeError, ValueError):
                continue
            positional = [
                parameter
                for parameter in signature.parameters.values()
                if parameter.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
            ]
            if not positional:
                continue
            host_parameter_name = positional[0].name
            if host_parameter_name in ("host", "_host"):
                continue
            raise ValueError(
                f"{part.__class__.__name__}.{hook_name} first positional parameter must be 'host' or '_host', got {host_parameter_name!r}"
            )

    @staticmethod
    def _normalize_alias(alias: str) -> str:
        alias_name = str(alias).strip()
        if not alias_name:
            raise ValueError("logic binding alias must be a non-empty string")
        return alias_name
