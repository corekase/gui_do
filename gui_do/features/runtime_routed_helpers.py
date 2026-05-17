from __future__ import annotations

from typing import Any, Callable


def _apply_logic_bindings(feature, logic_bindings) -> None:
    for binding in logic_bindings:
        if feature.bound_logic_name(alias=binding.alias) is None:
            feature.bind_logic(binding.provider_name, alias=binding.alias)


def configure_routed_feature_runtime(
    feature,
    host,
    *,
    ensure_scene_scheduler_fn,
    scene_name: str = "main",
    scheduler_attr_name: str = "scheduler",
    scheduler_dispatch_limit: int | None = None,
    logic_bindings=(),
    companion_providers=(),
):
    """Single routed-runtime entrypoint for scheduler, logic bindings, and companions."""
    if companion_providers:
        lifecycle = RoutedFeatureLifecycleBuilder().extend(companion_providers)
        lifecycle.register_on(feature, host=host)

    scheduler = ensure_scene_scheduler_fn(
        feature,
        host,
        scene_name=scene_name,
        attr_name=scheduler_attr_name,
    )
    if scheduler_dispatch_limit is not None:
        scheduler.set_message_dispatch_limit(int(scheduler_dispatch_limit))
    if logic_bindings:
        _apply_logic_bindings(feature, logic_bindings)
    return scheduler


class RoutedFeatureLifecycleBuilder:
    """Small fluent helper for companion provider registration."""

    def __init__(self) -> None:
        self._companions: list[Callable[[], Any]] = []

    def add_companion(self, companion_provider: Callable[[], Any]) -> "RoutedFeatureLifecycleBuilder":
        self._companions.append(companion_provider)
        return self

    def extend(self, companion_providers) -> "RoutedFeatureLifecycleBuilder":
        for companion_provider in companion_providers:
            self.add_companion(companion_provider)
        return self

    def build(self) -> tuple[Callable[[], Any], ...]:
        return tuple(self._companions)

    def register_on(self, feature, *, host=None) -> None:
        providers = self.build()
        if not providers:
            return
        manager = getattr(feature, "_feature_manager", None)
        if manager is None:
            return
        host_obj = manager.app if host is None else host
        for provider in providers:
            companion = provider() if callable(provider) else provider
            if companion is not None:
                manager.register(companion, host_obj)


class EventSubscriptionSpecBuilder:
    """Collect event subscription descriptors in a compact, chainable style."""

    def __init__(self) -> None:
        self._subscriptions: list[dict[str, Any]] = []

    def subscribe(
        self,
        *,
        attr_name: str,
        topic: str,
        handler,
        scope: str | None = None,
    ) -> "EventSubscriptionSpecBuilder":
        self._subscriptions.append(
            {
                "attr_name": attr_name,
                "topic": topic,
                "handler": handler,
                "scope": scope,
            }
        )
        return self

    def build(self) -> tuple[dict[str, Any], ...]:
        return tuple(self._subscriptions)


__all__ = [
    "configure_routed_feature_runtime",
    "RoutedFeatureLifecycleBuilder",
    "EventSubscriptionSpecBuilder",
]
