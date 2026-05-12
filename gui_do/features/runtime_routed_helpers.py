from __future__ import annotations


def bind_feature_logic_aliases(feature, logic_bindings) -> None:
    """Bind routed-feature logic aliases idempotently from declarative bindings."""
    for binding in logic_bindings:
        if feature.bound_logic_name(alias=binding.alias) is None:
            feature.bind_logic(binding.provider_name, alias=binding.alias)


def setup_routed_feature_runtime(
    feature,
    host,
    *,
    ensure_scene_scheduler_fn,
    scene_name: str = "main",
    scheduler_attr_name: str = "scheduler",
    scheduler_dispatch_limit: int | None = None,
    logic_bindings=(),
):
    """Initialize standard routed-feature runtime dependencies and optional logic bindings."""
    scheduler = ensure_scene_scheduler_fn(
        feature,
        host,
        scene_name=scene_name,
        attr_name=scheduler_attr_name,
    )
    if scheduler_dispatch_limit is not None:
        scheduler.set_message_dispatch_limit(int(scheduler_dispatch_limit))
    if logic_bindings:
        bind_feature_logic_aliases(feature, logic_bindings)
    return scheduler
