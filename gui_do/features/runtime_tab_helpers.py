from __future__ import annotations

from typing import Callable, Sequence

from pygame import Rect

from ..controls.chrome.window_control import WindowControl
from ..controls.data.tab_control import TabControl, TabItem
from .feature_lifecycle import create_anchored_feature_window
from .runtime_registration_helpers import register_window_tab_builders


def create_tab_control_from_specs(
    control_id: str,
    rect,
    tab_specs,
    *,
    selected_key: str,
    on_change,
) -> TabControl:
    """Create a TabControl from declarative tab specs."""
    return TabControl(
        str(control_id),
        Rect(rect),
        items=[TabItem(spec.key, spec.label) for spec in tab_specs],
        selected_key=str(selected_key),
        on_change=on_change,
    )


def compute_tabbed_window_layout(
    content_rect: Rect,
    *,
    tab_height: int,
    tab_rows: int = 2,
    padding: int = 0,
    min_content_height: int = 60,
) -> tuple[Rect, Rect]:
    """Return (tab_rect, tab_content_rect) for a tabbed window content surface."""
    pad = int(padding)
    body_top = content_rect.top + pad
    body_bottom = content_rect.bottom - pad
    body_h = body_bottom - body_top
    body_content_top = body_top + (int(tab_height) * int(tab_rows))
    body_content_h = max(int(min_content_height), body_bottom - body_content_top)
    body_rect = Rect(content_rect.left + pad, body_top, content_rect.width - pad * 2, body_h)
    body_content_rect = Rect(
        content_rect.left + pad,
        body_content_top,
        content_rect.width - pad * 2,
        body_content_h,
    )
    return body_rect, body_content_rect


def register_window_tab_builder_specs(tab_manager, feature, host, rect, tab_specs) -> None:
    """Register tab content builders from TabBuilderSpec definitions."""
    register_window_tab_builders(
        tab_manager,
        feature,
        host,
        rect,
        [(spec.key, spec.builder_attr) for spec in tab_specs],
    )


def setup_feature_presenter_tabs(
    presenter,
    *,
    control_id: str,
    tab_rect,
    tab_specs,
    selected_key: str,
    on_change,
    tab_manager,
    feature,
    host,
    tab_content_rect,
):
    """Create, attach, and register feature tab controls/builders in one call."""
    tab_control = create_tab_control_from_specs(
        control_id,
        tab_rect,
        tab_specs,
        selected_key=selected_key,
        on_change=on_change,
    )
    presenter.add_control(tab_control)
    register_window_tab_builder_specs(
        tab_manager,
        feature,
        host,
        tab_content_rect,
        tab_specs,
    )
    # Activate the initial selected tab to show its content
    tab_manager.activate(selected_key)
    return tab_control


def setup_feature_presenter_tabs_from_window_content(
    presenter,
    *,
    window,
    spec,
    tab_specs,
    on_change,
    tab_manager,
    feature,
    host,
    on_activate_callbacks: Sequence[tuple[str, Callable[[], object]]] = (),
    compute_tabbed_window_layout_fn=None,
    setup_feature_presenter_tabs_fn=None,
):
    """Compute tab layout from window content and wire presenter tabs."""
    if compute_tabbed_window_layout_fn is None:
        compute_tabbed_window_layout_fn = compute_tabbed_window_layout
    if setup_feature_presenter_tabs_fn is None:
        setup_feature_presenter_tabs_fn = setup_feature_presenter_tabs

    tab_rect, tab_content_rect = compute_tabbed_window_layout_fn(
        window.content_rect(),
        tab_height=int(spec.tab_height),
        tab_rows=int(spec.tab_rows),
        padding=int(spec.padding),
        min_content_height=int(spec.min_content_height),
    )
    tab_control = setup_feature_presenter_tabs_fn(
        presenter,
        control_id=str(spec.control_id),
        tab_rect=tab_rect,
        tab_specs=tab_specs,
        selected_key=str(spec.selected_key),
        on_change=on_change,
        tab_manager=tab_manager,
        feature=feature,
        host=host,
        tab_content_rect=tab_content_rect,
    )
    for tab_key, callback in on_activate_callbacks:
        tab_manager.on_activate(str(tab_key), callback)
    return tab_control


def register_tab_update_handlers(router, handlers) -> None:
    """Register multiple active-tab update handlers on a router."""
    for tab_key, handler in handlers:
        router.register(tab_key, handler)


def create_presented_anchored_window(
    host,
    *,
    control_id: str,
    title: str,
    size: tuple[int, int],
    anchor: str,
    margin: tuple[int, int],
    presenter,
    window_control_cls=WindowControl,
    use_frame_backdrop: bool = True,
    create_anchored_feature_window_fn=None,
):
    """Create an anchored window and attach a presenter in one call."""
    if create_anchored_feature_window_fn is None:
        create_anchored_feature_window_fn = create_anchored_feature_window

    window = create_anchored_feature_window_fn(
        host,
        window_control_cls=window_control_cls,
        control_id=control_id,
        title=title,
        size=size,
        anchor=anchor,
        margin=margin,
        use_frame_backdrop=bool(use_frame_backdrop),
    )
    window.set_presenter(presenter)
    return window


def create_presented_window_from_spec(
    host,
    *,
    presenter,
    spec,
    window_control_cls=WindowControl,
    create_presented_anchored_window_fn=None,
):
    """Create and attach a presenter-backed anchored window from a typed spec."""
    if create_presented_anchored_window_fn is None:
        create_presented_anchored_window_fn = create_presented_anchored_window

    return create_presented_anchored_window_fn(
        host,
        control_id=spec.control_id,
        title=spec.title,
        size=spec.size,
        anchor=spec.anchor,
        margin=spec.margin,
        presenter=presenter,
        window_control_cls=window_control_cls,
        use_frame_backdrop=spec.use_frame_backdrop,
    )


def create_feature_presented_window(
    host,
    *,
    feature,
    presenter_cls,
    spec,
    window_control_cls=WindowControl,
    create_presented_window_from_spec_fn=None,
):
    """Instantiate presenter from (feature, host) and create an anchored window from spec."""
    presenter = presenter_cls(feature, host)
    if create_presented_window_from_spec_fn is None:
        create_presented_window_from_spec_fn = create_presented_window_from_spec

    return create_presented_window_from_spec_fn(
        host,
        presenter=presenter,
        spec=spec,
        window_control_cls=window_control_cls,
    )
