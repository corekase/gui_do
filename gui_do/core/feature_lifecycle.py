"""Shared Feature abstractions for managed lifecycle composition."""

from __future__ import annotations

from collections import OrderedDict, deque
from dataclasses import dataclass
import inspect
from time import perf_counter
from typing import Any, Callable, Deque, Dict, Iterable, Mapping, Optional
from .error_handling import logical_error, report_nonfatal_error
from .telemetry import telemetry_collector

@dataclass(slots=True)
class FeatureMessage:
    """Structured message envelope used for inter-feature transport."""

    sender: str
    target: str
    payload: Dict[str, Any]

    @classmethod
    def from_payload(cls, sender: str, target: str, payload: Mapping[str, Any]) -> "FeatureMessage":
        return cls(sender=str(sender), target=str(target), payload=dict(payload))

    def __getitem__(self, key: str) -> Any:
        return self.payload[key]

    def get(self, key: str, default: Any = None) -> Any:
        return self.payload.get(key, default)

    @property
    def topic(self) -> Optional[str]:
        value = self.payload.get("topic")
        return value if isinstance(value, str) else None

    @property
    def command(self) -> Optional[str]:
        value = self.payload.get("command")
        return value if isinstance(value, str) else None

    @property
    def event(self) -> Optional[str]:
        value = self.payload.get("event")
        return value if isinstance(value, str) else None


class Feature:
    """Base unit for managed GUI lifecycle composition."""

    HOST_REQUIREMENTS: Dict[str, tuple[str, ...]] = {}

    def __init__(self, name: str, *, scene_name: Optional[str] = None) -> None:
        normalized = str(name).strip()
        if not normalized:
            raise logical_error(
                "feature name must be a non-empty string",
                subsystem="feature_lifecycle",
                operation="Feature.__init__",
                exc_type=ValueError,
                details={"name": name},
                source_skip_frames=1,
            )
        self.name = normalized
        if scene_name is None:
            self.scene_name = None
        else:
            normalized_scene_name = str(scene_name).strip()
            if not normalized_scene_name:
                raise logical_error(
                    "scene_name must be a non-empty string when provided",
                    subsystem="feature_lifecycle",
                    operation="Feature.__init__",
                    exc_type=ValueError,
                    details={"scene_name": scene_name},
                    source_skip_frames=1,
                )
            self.scene_name = normalized_scene_name
        self._feature_manager = None
        self._message_queue: Deque[FeatureMessage] = deque()
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

    def save_state(self) -> dict:
        """Return a JSON-serializable dict of persistent feature state.

        Override to capture state that should survive across sessions.
        The default implementation returns an empty dict.
        """
        return {}

    def restore_state(self, state: dict) -> None:
        """Apply previously saved state produced by :meth:`save_state`.

        Called by :meth:`FeatureManager.restore_feature_states` after
        :meth:`build` completes.  Override to apply persisted values.
        """

    def send_message(self, target_feature_name: str, message: Mapping[str, Any]) -> bool:
        if self._feature_manager is None:
            raise logical_error(
                "feature must be registered before sending messages",
                subsystem="feature_lifecycle",
                operation="Feature.send_message",
                exc_type=RuntimeError,
                details={"feature_name": self.name, "target_feature_name": target_feature_name},
                source_skip_frames=1,
            )
        return self._feature_manager.send_message(self.name, target_feature_name, message)

    def bind_logic(self, logic_feature_name: str, *, alias: str = "default") -> None:
        if self._feature_manager is None:
            raise logical_error(
                "feature must be registered before binding logic features",
                subsystem="feature_lifecycle",
                operation="Feature.bind_logic",
                exc_type=RuntimeError,
                details={"feature_name": self.name, "logic_feature_name": logic_feature_name, "alias": alias},
                source_skip_frames=1,
            )
        self._feature_manager.bind_logic(self.name, logic_feature_name, alias=alias)

    def unbind_logic(self, *, alias: str = "default") -> bool:
        if self._feature_manager is None:
            raise logical_error(
                "feature must be registered before unbinding logic features",
                subsystem="feature_lifecycle",
                operation="Feature.unbind_logic",
                exc_type=RuntimeError,
                details={"feature_name": self.name, "alias": alias},
                source_skip_frames=1,
            )
        return self._feature_manager.unbind_logic(self.name, alias=alias)

    def bound_logic_name(self, *, alias: str = "default") -> Optional[str]:
        if self._feature_manager is None:
            raise logical_error(
                "feature must be registered before querying logic feature names",
                subsystem="feature_lifecycle",
                operation="Feature.bound_logic_name",
                exc_type=RuntimeError,
                details={"feature_name": self.name, "alias": alias},
                source_skip_frames=1,
            )
        return self._feature_manager.bound_logic_name(self.name, alias=alias)

    def send_logic_message(self, message: Mapping[str, Any], *, alias: str = "default") -> bool:
        if self._feature_manager is None:
            raise logical_error(
                "feature must be registered before sending logic messages",
                subsystem="feature_lifecycle",
                operation="Feature.send_logic_message",
                exc_type=RuntimeError,
                details={"feature_name": self.name, "alias": alias},
                source_skip_frames=1,
            )
        return self._feature_manager.send_logic_message(self.name, message, alias=alias)

    def enqueue_message(self, message: FeatureMessage) -> None:
        if not isinstance(message, FeatureMessage):
            raise logical_error(
                "feature messages must be FeatureMessage instances",
                subsystem="feature_lifecycle",
                operation="Feature.enqueue_message",
                exc_type=TypeError,
                details={"feature_name": self.name, "message_type": type(message).__name__},
                source_skip_frames=1,
            )
        self._message_queue.append(message)

    def has_messages(self) -> bool:
        return bool(self._message_queue)

    def message_count(self) -> int:
        return len(self._message_queue)

    def peek_message(self) -> Optional[FeatureMessage]:
        if not self._message_queue:
            return None
        return self._message_queue[0]

    def pop_message(self) -> Optional[FeatureMessage]:
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
                raise logical_error(
                    "font role definitions must be dictionaries",
                    subsystem="feature_lifecycle",
                    operation="Feature.register_font_roles",
                    exc_type=TypeError,
                    details={"feature_name": self.name, "role_name": role_name, "spec_type": type(spec).__name__},
                    source_skip_frames=1,
                )
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
            raise logical_error(
                f"unknown feature font role: {self.name}.{local_name}",
                subsystem="feature_lifecycle",
                operation="Feature.font_role",
                exc_type=KeyError,
                details={"feature_name": self.name, "role_name": local_name},
                source_skip_frames=1,
            )
        return qualified_name

    @staticmethod
    def _normalize_font_role_name(role_name: str) -> str:
        normalized = str(role_name).strip()
        if not normalized:
            raise logical_error(
                "font role name must be a non-empty string",
                subsystem="feature_lifecycle",
                operation="Feature._normalize_font_role_name",
                exc_type=ValueError,
                details={"role_name": role_name},
                source_skip_frames=1,
            )
        return normalized

    @staticmethod
    def _resolve_app(host):
        app = getattr(host, "app", host)
        if not hasattr(app, "register_font_role"):
            raise logical_error(
                "host does not expose an application with register_font_role()",
                subsystem="feature_lifecycle",
                operation="Feature._resolve_app",
                exc_type=AttributeError,
                details={"host_type": type(host).__name__},
                source_skip_frames=1,
            )
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
        raise logical_error(
            f"{self.__class__.__name__}.{hook_name} requires host fields: {missing_csv}",
            subsystem="feature_lifecycle",
            operation="Feature.validate_host_for",
            exc_type=AttributeError,
            details={"feature_class": self.__class__.__name__, "hook_name": hook_name, "missing_fields": tuple(missing)},
            source_skip_frames=1,
        )


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

    def on_logic_command(self, host, message: FeatureMessage) -> None:
        return None

    def on_update(self, host) -> None:
        while self.has_messages():
            message = self.pop_message()
            if message is None:
                continue
            if message.command is None:
                continue
            self.on_logic_command(host, message)


class RoutedFeature(Feature):
    """Feature subtype that routes queued messages by a canonical topic key."""

    MESSAGE_TOPIC_KEY = "topic"

    def message_handlers(self) -> Dict[str, Callable[[Any, FeatureMessage], None]]:
        """Return mapping of topic names to message handlers."""
        return {}

    def on_message(self, host, message: FeatureMessage) -> None:
        """Handle one routed message; unresolved topics are ignored by default."""
        handlers = self.message_handlers()
        topic = message.topic
        if topic is None:
            return
        handler = handlers.get(topic)
        if handler is None:
            return
        handler(host, message)

    def on_update(self, host) -> None:
        while self.has_messages():
            message = self.pop_message()
            if message is None:
                continue
            topic = message.topic
            if topic is None:
                continue
            self.on_message(host, message)


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
            raise logical_error(
                "register expects a Feature instance",
                subsystem="feature_lifecycle",
                operation="FeatureManager.register",
                exc_type=TypeError,
                details={"feature_type": type(feature).__name__},
                source_skip_frames=1,
            )
        if feature.name in self._features:
            raise logical_error(
                f"feature already registered: {feature.name}",
                subsystem="feature_lifecycle",
                operation="FeatureManager.register",
                exc_type=ValueError,
                details={"feature_name": feature.name},
                source_skip_frames=1,
            )
        self._validate_host_contract(feature)
        feature._feature_manager = self
        host_obj = self.app if host is None else host
        # Call on_register before inserting into _features so that any companion
        # features registered inside on_register appear before this feature in
        # iteration order (e.g. for correct message-passing in update_features).
        feature.on_register(host_obj)
        self._features[feature.name] = feature
        self._feature_hosts[feature.name] = host_obj
        self._runtime_bound.discard(feature.name)
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

    def send_message(self, sender_name: str, target_feature_name: str, message: Mapping[str, Any]) -> bool:
        collector = telemetry_collector()
        if not isinstance(message, Mapping):
            raise logical_error(
                "feature messages must be mappings",
                subsystem="feature_lifecycle",
                operation="FeatureManager.send_message",
                exc_type=TypeError,
                details={"sender_name": sender_name, "target_feature_name": target_feature_name, "message_type": type(message).__name__},
                source_skip_frames=1,
            )
        envelope = FeatureMessage.from_payload(str(sender_name), str(target_feature_name), message)
        topic = envelope.topic or ""
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
            envelope.target = target.name
            target.enqueue_message(envelope)
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
            raise logical_error(
                "runnable must be callable",
                subsystem="feature_lifecycle",
                operation="FeatureManager.register_runnable",
                exc_type=TypeError,
                details={"feature_name": feature_name, "runnable_name": runnable_name, "runnable_type": type(runnable).__name__},
                source_skip_frames=1,
            )
        name = str(runnable_name).strip()
        if not name:
            raise logical_error(
                "runnable_name must be a non-empty string",
                subsystem="feature_lifecycle",
                operation="FeatureManager.register_runnable",
                exc_type=ValueError,
                details={"feature_name": feature_name, "runnable_name": runnable_name},
                source_skip_frames=1,
            )
        bucket = self._runnables.setdefault(str(feature_name), {})
        bucket[name] = runnable

    def bind_logic(self, consumer_feature_name: str, logic_feature_name: str, *, alias: str = "default") -> None:
        consumer = self._require_feature(consumer_feature_name)
        provider = self._require_feature(logic_feature_name)
        if not isinstance(provider, LogicFeature):
            raise logical_error(
                f"feature is not a LogicFeature: {provider.name}",
                subsystem="feature_lifecycle",
                operation="FeatureManager.bind_logic",
                exc_type=TypeError,
                details={"consumer": consumer.name, "provider": provider.name, "alias": alias},
                source_skip_frames=1,
            )
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

    def send_logic_message(self, consumer_feature_name: str, message: Mapping[str, Any], *, alias: str = "default") -> bool:
        provider_name = self.bound_logic_name(consumer_feature_name, alias=alias)
        if provider_name is None:
            return False
        return self.send_message(str(consumer_feature_name), provider_name, message)

    def run(self, feature_name: str, runnable_name: str, *args, **kwargs) -> Any:
        feature_bucket = self._runnables.get(str(feature_name), {})
        runnable = feature_bucket.get(str(runnable_name))
        if runnable is None:
            raise logical_error(
                f"unknown runnable: {feature_name}.{runnable_name}",
                subsystem="feature_lifecycle",
                operation="FeatureManager.run",
                exc_type=KeyError,
                details={"feature_name": feature_name, "runnable_name": runnable_name},
                source_skip_frames=1,
            )
        return runnable(*args, **kwargs)

    def handle_event(self, event, host=None) -> bool:
        collector = telemetry_collector()
        for feature in self._features.values():
            if not self._is_feature_active_for_scene(feature):
                continue
            host_obj = self._resolve_host(feature.name, host)
            with collector.span("feature_lifecycle", "feature_handle_event", metadata={"feature_name": feature.name}):
                if feature.handle_event(host_obj, event):
                    return True
        return False

    def update_features(self, host=None) -> None:
        collector = telemetry_collector()
        for feature in self._features.values():
            if not self._is_feature_active_for_scene(feature):
                continue
            host_obj = self._resolve_host(feature.name, host)
            with collector.span("feature_lifecycle", "feature_update", metadata={"feature_name": feature.name}):
                feature.on_update(host_obj)

    def draw(self, surface, theme, host=None) -> None:
        collector = telemetry_collector()
        for feature in self._features.values():
            if not self._is_feature_active_for_scene(feature):
                continue
            host_obj = self._resolve_host(feature.name, host)
            with collector.span("feature_lifecycle", "feature_draw", metadata={"feature_name": feature.name}):
                feature.draw(host_obj, surface, theme)

    def handle_direct_event(self, event, host=None) -> bool:
        collector = telemetry_collector()
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
        collector = telemetry_collector()
        for feature in self._features.values():
            if not isinstance(feature, DirectFeature):
                continue
            if not self._is_feature_active_for_scene(feature):
                continue
            host_obj = self._resolve_host(feature.name, host)
            with collector.span("feature_lifecycle", "direct_feature_update", metadata={"feature_name": feature.name}):
                feature.on_direct_update(host_obj, dt_seconds)

    def draw_direct_features(self, surface, theme, host=None) -> None:
        collector = telemetry_collector()
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
            from gui_do.core.first_frame_profiler import first_frame_profiler

            first_frame_profiler().record_once(
                "feature.prewarm",
                f"{scene_name}:{feature_name}",
                elapsed_ms,
                detail="feature prewarm hook",
            )
        except Exception as exc:
            report_nonfatal_error(
                "failed to record feature prewarm telemetry sample",
                kind="logical",
                subsystem="feature_lifecycle",
                operation="FeatureManager._record_prewarm_sample",
                cause=exc,
                details={"scene_name": scene_name, "feature_name": feature_name, "elapsed_ms": float(elapsed_ms)},
                source_skip_frames=1,
            )
            return

    def build_features(self, host) -> None:
        collector = telemetry_collector()
        for feature in self._features.values():
            feature.validate_host_for(host, "build")
            with collector.span("feature_lifecycle", "feature_build", metadata={"feature_name": feature.name}):
                feature.build(host)

    def bind_runtime(self, host) -> None:
        collector = telemetry_collector()
        for feature in self._features.values():
            feature.validate_host_for(host, "bind_runtime")
            with collector.span("feature_lifecycle", "feature_bind_runtime", metadata={"feature_name": feature.name}):
                feature.bind_runtime(host)
            self._runtime_bound.add(feature.name)

    def shutdown_runtime(self, host=None) -> None:
        """Call shutdown_runtime(host) for features with active runtime bindings."""
        collector = telemetry_collector()
        for feature in reversed(tuple(self._features.values())):
            if feature.name not in self._runtime_bound:
                continue
            host_obj = self._resolve_host(feature.name, host)
            with collector.span("feature_lifecycle", "feature_shutdown_runtime", metadata={"feature_name": feature.name}):
                feature.shutdown_runtime(host_obj)
            self._runtime_bound.discard(feature.name)

    def configure_accessibility(self, host, tab_index_start: int) -> int:
        collector = telemetry_collector()
        next_index = int(tab_index_start)
        for feature in self._features.values():
            feature.validate_host_for(host, "configure_accessibility")
            with collector.span("feature_lifecycle", "feature_configure_accessibility", metadata={"feature_name": feature.name}):
                next_index = int(feature.configure_accessibility(host, next_index))
        return next_index

    def _require_feature(self, feature_name: str) -> Feature:
        feature = self.get(feature_name)
        if feature is None:
            raise logical_error(
                f"unknown feature: {feature_name}",
                subsystem="feature_lifecycle",
                operation="FeatureManager._require_feature",
                exc_type=KeyError,
                details={"feature_name": feature_name},
                source_skip_frames=1,
            )
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
            raise logical_error(
                f"{feature.__class__.__name__}.{hook_name} first positional parameter must be 'host' or '_host', got {host_parameter_name!r}",
                subsystem="feature_lifecycle",
                operation="FeatureManager._validate_host_contract",
                exc_type=ValueError,
                details={"feature_class": feature.__class__.__name__, "hook_name": hook_name, "parameter_name": host_parameter_name},
                source_skip_frames=1,
            )

    @staticmethod
    def _normalize_alias(alias: str) -> str:
        alias_name = str(alias).strip()
        if not alias_name:
            raise logical_error(
                "logic binding alias must be a non-empty string",
                subsystem="feature_lifecycle",
                operation="FeatureManager._normalize_alias",
                exc_type=ValueError,
                details={"alias": alias},
                source_skip_frames=1,
            )
        return alias_name

    def save_feature_states(self) -> Dict[str, dict]:
        """Collect persistent state from every registered feature.

        Returns a ``{feature_name: state_dict}`` mapping suitable for
        JSON serialisation and later passing to :meth:`restore_feature_states`.
        Features that raise during :meth:`Feature.save_state` are skipped with
        an empty dict recorded under their name.
        """
        states: Dict[str, dict] = {}
        for feature in self._features.values():
            try:
                state = feature.save_state()
            except Exception:
                state = {}
            states[feature.name] = state if isinstance(state, dict) else {}
        return states

    def restore_feature_states(self, states: Dict[str, dict]) -> None:
        """Distribute saved states to registered features.

        *states* should be a ``{feature_name: state_dict}`` mapping as produced
        by :meth:`save_feature_states`.  Features with no entry in *states* are
        silently skipped.  Errors during :meth:`Feature.restore_state` are
        swallowed so that a corrupt state block cannot prevent other features
        from restoring.
        """
        if not isinstance(states, dict):
            return
        for name, state in states.items():
            feature = self._features.get(str(name))
            if feature is None or not isinstance(state, dict):
                continue
            try:
                feature.restore_state(state)
            except Exception:
                pass
