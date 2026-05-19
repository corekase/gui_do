from __future__ import annotations

from pygame import Rect


def instantiate_features_from_specs(host, feature_specs) -> None:
    """Instantiate feature objects from specs and attach them to host attributes."""
    for spec in feature_specs:
        setattr(host, spec.attr_name, spec.factory())


def register_features_from_specs(app, host, feature_specs) -> None:
    """Register instantiated host feature attributes to the application."""
    for spec in feature_specs:
        feature = getattr(host, spec.attr_name)
        app.register_feature(feature, host=host)


def register_window_presentation_specs(window_presentation, window_specs) -> None:
    """Register feature-window presentation bindings from declarative window specs."""
    for spec in window_specs:
        kwargs = {
            "feature_attribute_name": spec.feature_attribute_name,
            "toggle_attribute_name": spec.toggle_attribute_name,
            "action_name": spec.action_name,
            "action_label": spec.action_label,
            "task_panel_toggle_button_id": spec.task_panel_toggle_button_id,
            "task_panel_label": spec.task_panel_label,
            "task_panel_style": spec.task_panel_style,
            "task_panel_slot_index": spec.task_panel_slot_index,
            "accessibility_label": spec.accessibility_label,
        }
        if hasattr(spec, "window_effects"):
            kwargs["window_effects"] = dict(spec.window_effects or {})
        if hasattr(spec, "window_menu_opt_in"):
            kwargs["window_menu_opt_in"] = bool(spec.window_menu_opt_in)
        window_presentation.register_feature_window(spec.key, **kwargs)


def register_window_tab_builders(tab_manager, feature, host, rect, tab_specs) -> None:
    """Register tab content builders from declarative (tab_key, builder_attr) specs."""
    for tab_key, builder_attr in tab_specs:
        builder = getattr(feature, str(builder_attr), None)
        if not callable(builder):
            raise AttributeError(f"Missing tab builder '{builder_attr}' for tab '{tab_key}'")
        tab_manager.register(str(tab_key), builder(host, Rect(rect)))
