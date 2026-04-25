"""Shared Feature abstractions for managed lifecycle composition."""

from __future__ import annotations

from collections import OrderedDict, deque
from contextlib import nullcontext
from copy import deepcopy
import inspect
from time import perf_counter
from typing import Any, Callable, Deque, Dict, Iterable, Optional


class _NoopTelemetryCollector:
    def span(self, _system: str, _point: str, _metadata: Optional[Dict[str, Any]] = None):
        return nullcontext()

    def record_duration(self, _system: str, _point: str, _elapsed_ms: float, *, _metadata: Optional[Dict[str, Any]] = None) -> None:
        return None


def _telemetry_collector():
    try:
        from gui.core.telemetry import telemetry_collector

        return telemetry_collector()
    except ImportError:
        return _NoopTelemetryCollector()


class Feature:
    """Base unit for managed GUI lifecycle composition."""

    HOST_REQUIREMENTS: Dict[str, tuple[str, ...]] = {}

    def __init__(self, name: str, *, scene_name: Optional[str] = None) -> None:
        normalized = str(name).strip()
        if not normalized:
            raise ValueError("feature name must be a non-empty string")
        self.name = normalized
        if scene_name is None:
            self.scene_name = None
        else:
            normalized_scene_name = str(scene_name).strip()
            if not normalized_scene_name:
                raise ValueError("scene_name must be a non-empty string when provided")
            self.scene_name = normalized_scene_name
        self._feature_manager = None
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

    def send_message(self, target_feature_name: str, message: Dict[str, Any]) -> bool:
        if self._feature_manager is None:
            raise RuntimeError("feature must be registered before sending messages")
        return self._feature_manager.send_message(self.name, target_feature_name, message)

    def bind_logic(self, logic_feature_name: str, *, alias: str = "default") -> None:
        if self._feature_manager is None:
            raise RuntimeError("feature must be registered before binding logic features")
        self._feature_manager.bind_logic(self.name, logic_feature_name, alias=alias)

    def unbind_logic(self, *, alias: str = "default") -> bool:
        if self._feature_manager is None:
            raise RuntimeError("feature must be registered before unbinding logic features")
        return self._feature_manager.unbind_logic(self.name, alias=alias)

    def bound_logic_name(self, *, alias: str = "default") -> Optional[str]:
        if self._feature_manager is None:
            raise RuntimeError("feature must be registered before querying logic feature names")
        return self._feature_manager.bound_logic_name(self.name, alias=alias)

    def send_logic_message(self, message: Dict[str, Any], *, alias: str = "default") -> bool:
        if self._feature_manager is None:
            raise RuntimeError("feature must be registered before sending logic messages")
        return self._feature_manager.send_logic_message(self.name, message, alias=alias)

    def enqueue_message(self, message: Dict[str, Any]) -> None:
        if not isinstance(message, dict):
            raise TypeError("feature messages must be dictionaries")
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
        """Register one namespaced font role owned by this feature."""
        local_name = self._normalize_font_role_name(role_name)
        app = self._resolve_app(host)
        qualified_name = f"feature.{self.name}.{local_name}"
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
        """Register multiple namespaced font roles owned by this feature."""
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
        """Resolve a local feature font role name to its registered global role."""
        local_name = self._normalize_font_role_name(role_name)
        qualified_name = self._font_roles.get(local_name)
        if qualified_name is None:
            raise KeyError(f"unknown feature font role: {self.name}.{local_name}")
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


class DirectFeature(Feature):
    """Feature subtype for direct screen event/update/draw integration.

    Bypasses the widget pipeline entirely, receiving raw per-frame dt_seconds
    and drawing directly to the restored pristine surface — analogous to how
    DirectX bypasses the Windows GDI for direct hardware access.
    """

    def handle_direct_event(self, host, event) -> bool:
        return False

    def on_direct_update(self, host, dt_seconds: float) -> None:
        return None

    def draw_direct(self, host, surface, theme) -> None:
        return None


class LogicFeature(Feature):
    """Feature subtype for domain logic routed through message commands."""

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


class RoutedFeature(Feature):
    """Feature subtype that routes queued messages by a canonical topic key."""

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


class FeatureManager:
    """Coordinates lifecycle, messaging, and utility registrations for features."""

    _LIFECYCLE_HOOKS = (
        "on_register",
        "on_unregister",
        "build",
        "bind_runtime",
        "configure_accessibility",
        "shutdown_runtime",
        "handle_event",
        "on_update",
        "draw",
        "handle_direct_event",
        "on_direct_update",
        "draw_direct",
        "on_logic_command",
        "on_message",
        "prewarm",
    )

    def __init__(self, app) -> None:
        self.app = app
        self._features: "OrderedDict[str, Feature]" = OrderedDict()
        self._feature_hosts: Dict[str, object] = {}
        self._runnables: Dict[str, Dict[str, Callable[..., Any]]] = {}
        self._runtime_bound: set[str] = set()
        self._logic_bindings: Dict[str, Dict[str, str]] = {}
        self._prewarmed: set[tuple[str, str]] = set()

    def register(self, feature: Feature, host=None) -> Feature:
        if not isinstance(feature, Feature):
            raise TypeError("register expects a Feature instance")
        if feature.name in self._features:
            raise ValueError(f"feature already registered: {feature.name}")
        self._validate_host_contract(feature)
        feature._feature_manager = self
        self._features[feature.name] = feature
        host_obj = self.app if host is None else host
        self._feature_hosts[feature.name] = host_obj
        self._runtime_bound.discard(feature.name)
        feature.on_register(host_obj)
        return feature

    def unregister(self, name: str, host=None) -> bool:
        key = str(name)
        feature = self._features.get(key)
        if feature is None:
            return False
        host_obj = self._feature_hosts.get(feature.name)
        if host_obj is None:
            host_obj = self.app if host is None else host
        if feature.name in self._runtime_bound:
            feature.shutdown_runtime(host_obj)
        feature.on_unregister(host_obj)
        self._features.pop(key, None)
        self._feature_hosts.pop(feature.name, None)
        self._runtime_bound.discard(feature.name)
        self._logic_bindings.pop(feature.name, None)
        for consumer_name, alias_map in tuple(self._logic_bindings.items()):
            aliases_to_remove = [alias for alias, provider_name in alias_map.items() if provider_name == feature.name]
            for alias in aliases_to_remove:
                alias_map.pop(alias, None)
            if not alias_map:
                self._logic_bindings.pop(consumer_name, None)
        feature._feature_manager = None
        self._runnables.pop(feature.name, None)
        return True

    def get(self, name: str) -> Optional[Feature]:
        return self._features.get(str(name))

    def names(self) -> tuple[str, ...]:
        return tuple(self._features.keys())

    def features(self) -> Iterable[Feature]:
        return tuple(self._features.values())

    def send_message(self, sender_name: str, target_feature_name: str, message: Dict[str, Any]) -> bool:
        collector = _telemetry_collector()
        topic = ""
        if isinstance(message, dict):
            raw_topic = message.get("topic")
            if isinstance(raw_topic, str):
                topic = raw_topic
        target = self._features.get(str(target_feature_name))
        if target is None:
            collector.record_duration(
                "feature_lifecycle",
                "send_message_missing_target",
                0.0,
                metadata={"sender": str(sender_name), "target": str(target_feature_name), "topic": topic},
            )
            return False
        with collector.span(
            "feature_lifecycle",
            "send_message",
            metadata={"sender": str(sender_name), "target": target.name, "topic": topic},
        ):
            payload = dict(message)
            payload.setdefault("_from", str(sender_name))
            payload.setdefault("_to", target.name)
            target.enqueue_message(payload)
            collector.record_duration(
                "feature_lifecycle",
                "target_queue_depth",
                0.0,
                metadata={"target": target.name, "queue_depth": target.message_count()},
            )
            return True

    def register_runnable(self, feature_name: str, runnable_name: str, runnable: Callable[..., Any]) -> None:
        self._require_feature(feature_name)
        if not callable(runnable):
            raise TypeError("runnable must be callable")
        name = str(runnable_name).strip()
        if not name:
            raise ValueError("runnable_name must be a non-empty string")
        bucket = self._runnables.setdefault(str(feature_name), {})
        bucket[name] = runnable

    def bind_logic(self, consumer_feature_name: str, logic_feature_name: str, *, alias: str = "default") -> None:
        consumer = self._require_feature(consumer_feature_name)
        provider = self._require_feature(logic_feature_name)
        if not isinstance(provider, LogicFeature):
            raise TypeError(f"feature is not a LogicFeature: {provider.name}")
        alias_name = self._normalize_alias(alias)
        bucket = self._logic_bindings.setdefault(consumer.name, {})
        bucket[alias_name] = provider.name

    def unbind_logic(self, consumer_feature_name: str, *, alias: str = "default") -> bool:
        alias_name = self._normalize_alias(alias)
        bucket = self._logic_bindings.get(str(consumer_feature_name))
        if not bucket or alias_name not in bucket:
            return False
        bucket.pop(alias_name, None)
        if not bucket:
            self._logic_bindings.pop(str(consumer_feature_name), None)
        return True

    def bound_logic_name(self, consumer_feature_name: str, *, alias: str = "default") -> Optional[str]:
        alias_name = self._normalize_alias(alias)
        bucket = self._logic_bindings.get(str(consumer_feature_name), {})
        return bucket.get(alias_name)

    def send_logic_message(self, consumer_feature_name: str, message: Dict[str, Any], *, alias: str = "default") -> bool:
        provider_name = self.bound_logic_name(consumer_feature_name, alias=alias)
        if provider_name is None:
            return False
        return self.send_message(str(consumer_feature_name), provider_name, message)

    def run(self, feature_name: str, runnable_name: str, *args, **kwargs) -> Any:
        feature_bucket = self._runnables.get(str(feature_name), {})
        runnable = feature_bucket.get(str(runnable_name))
        if runnable is None:
            raise KeyError(f"unknown runnable: {feature_name}.{runnable_name}")
        return runnable(*args, **kwargs)

    def handle_event(self, event, host=None) -> bool:
        collector = _telemetry_collector()
        for feature in self._features.values():
            if not self._is_feature_active_for_scene(feature):
                continue
            host_obj = self._resolve_host(feature.name, host)
            with collector.span("feature_lifecycle", "feature_handle_event", metadata={"feature_name": feature.name}):
                if feature.handle_event(host_obj, event):
                    return True
        return False

    def update_features(self, host=None) -> None:
        collector = _telemetry_collector()
        for feature in self._features.values():
            if not self._is_feature_active_for_scene(feature):
                continue
            host_obj = self._resolve_host(feature.name, host)
            with collector.span("feature_lifecycle", "feature_update", metadata={"feature_name": feature.name}):
                feature.on_update(host_obj)

    def draw(self, surface, theme, host=None) -> None:
        collector = _telemetry_collector()
        for feature in self._features.values():
            if not self._is_feature_active_for_scene(feature):
                continue
            host_obj = self._resolve_host(feature.name, host)
            with collector.span("feature_lifecycle", "feature_draw", metadata={"feature_name": feature.name}):
                feature.draw(host_obj, surface, theme)

    def handle_direct_event(self, event, host=None) -> bool:
        collector = _telemetry_collector()
        for feature in self._features.values():
            if not isinstance(feature, DirectFeature):
                continue
            if not self._is_feature_active_for_scene(feature):
                continue
            host_obj = self._resolve_host(feature.name, host)
            with collector.span("feature_lifecycle", "direct_feature_handle_event", metadata={"feature_name": feature.name}):
                if feature.handle_direct_event(host_obj, event):
                    return True
        return False

    def update_direct_features(self, dt_seconds: float, host=None) -> None:
        collector = _telemetry_collector()
        for feature in self._features.values():
            if not isinstance(feature, DirectFeature):
                continue
            if not self._is_feature_active_for_scene(feature):
                continue
            host_obj = self._resolve_host(feature.name, host)
            with collector.span("feature_lifecycle", "direct_feature_update", metadata={"feature_name": feature.name}):
                feature.on_direct_update(host_obj, dt_seconds)

    def draw_direct_features(self, surface, theme, host=None) -> None:
        collector = _telemetry_collector()
        for feature in self._features.values():
            if not isinstance(feature, DirectFeature):
                continue
            if not self._is_feature_active_for_scene(feature):
                continue
            host_obj = self._resolve_host(feature.name, host)
            with collector.span("feature_lifecycle", "direct_feature_draw", metadata={"feature_name": feature.name}):
                feature.draw_direct(host_obj, surface, theme)

    def prewarm_features(self, host, surface, theme, *, scene_name: Optional[str] = None, force: bool = False) -> int:
        target_scene_name = str(self.app.active_scene_name if scene_name is None else scene_name)
        warmed = 0
        for feature in self._features.values():
            if not self._is_feature_active_for_scene(feature, scene_name=target_scene_name):
                continue
            cache_key = (feature.name, target_scene_name)
            if cache_key in self._prewarmed and not force:
                continue
            host_obj = self._resolve_host(feature.name, host)
            feature.validate_host_for(host_obj, "prewarm")
            start = perf_counter()
            feature.prewarm(host_obj, surface, theme)
            elapsed_ms = (perf_counter() - start) * 1000.0
            self._record_prewarm_sample(target_scene_name, feature.name, elapsed_ms)
            self._prewarmed.add(cache_key)
            warmed += 1
        return warmed

    @staticmethod
    def _record_prewarm_sample(scene_name: str, feature_name: str, elapsed_ms: float) -> None:
        try:
            from gui.core.first_frame_profiler import first_frame_profiler

            first_frame_profiler().record_once(
                "feature.prewarm",
                f"{scene_name}:{feature_name}",
                elapsed_ms,
                detail="feature prewarm hook",
            )
        except Exception:
            return

    def build_features(self, host) -> None:
        collector = _telemetry_collector()
        for feature in self._features.values():
            feature.validate_host_for(host, "build")
            with collector.span("feature_lifecycle", "feature_build", metadata={"feature_name": feature.name}):
                feature.build(host)

    def bind_runtime(self, host) -> None:
        collector = _telemetry_collector()
        for feature in self._features.values():
            feature.validate_host_for(host, "bind_runtime")
            with collector.span("feature_lifecycle", "feature_bind_runtime", metadata={"feature_name": feature.name}):
                feature.bind_runtime(host)
            self._runtime_bound.add(feature.name)

    def shutdown_runtime(self, host=None) -> None:
        """Call shutdown_runtime(host) for features with active runtime bindings."""
        collector = _telemetry_collector()
        for feature in reversed(tuple(self._features.values())):
            if feature.name not in self._runtime_bound:
                continue
            host_obj = self._resolve_host(feature.name, host)
            with collector.span("feature_lifecycle", "feature_shutdown_runtime", metadata={"feature_name": feature.name}):
                feature.shutdown_runtime(host_obj)
            self._runtime_bound.discard(feature.name)

    def configure_accessibility(self, host, tab_index_start: int) -> int:
        collector = _telemetry_collector()
        next_index = int(tab_index_start)
        for feature in self._features.values():
            feature.validate_host_for(host, "configure_accessibility")
            with collector.span("feature_lifecycle", "feature_configure_accessibility", metadata={"feature_name": feature.name}):
                next_index = int(feature.configure_accessibility(host, next_index))
        return next_index

    def _require_feature(self, feature_name: str) -> Feature:
        feature = self.get(feature_name)
        if feature is None:
            raise KeyError(f"unknown feature: {feature_name}")
        return feature

    def _resolve_host(self, feature_name: str, override_host=None):
        if override_host is not None:
            return override_host
        return self._feature_hosts.get(feature_name, self.app)

    def _is_feature_active_for_scene(self, feature: Feature, *, scene_name: Optional[str] = None) -> bool:
        target_scene_name = self.app.active_scene_name if scene_name is None else scene_name
        feature_scene = feature.scene_name
        if feature_scene is None:
            return True
        return str(feature_scene) == str(target_scene_name)

    @classmethod
    def _validate_host_contract(cls, feature: Feature) -> None:
        for hook_name in cls._LIFECYCLE_HOOKS:
            method = getattr(feature, hook_name, None)
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
                f"{feature.__class__.__name__}.{hook_name} first positional parameter must be 'host' or '_host', got {host_parameter_name!r}"
            )

    @staticmethod
    def _normalize_alias(alias: str) -> str:
        alias_name = str(alias).strip()
        if not alias_name:
            raise ValueError("logic binding alias must be a non-empty string")
        return alias_name
