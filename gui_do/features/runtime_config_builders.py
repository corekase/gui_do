from __future__ import annotations


def build_scene_setup_specs(
    entries,
    *,
    scene_setup_binding_spec_cls,
    scene_setup_spec_cls,
    default_transition_style=None,
    default_transition_duration=None,
    initial_scene_name: str | None = None,
):
    specs = []
    for entry in entries:
        if isinstance(entry, scene_setup_spec_cls):
            make_initial = bool(entry.make_initial or (initial_scene_name is not None and str(entry.name) == str(initial_scene_name)))
            specs.append(
                scene_setup_spec_cls(
                    name=str(entry.name),
                    pretty_name=entry.pretty_name,
                    transition_style=entry.transition_style,
                    transition_duration=entry.transition_duration,
                    tiling_enabled=bool(entry.tiling_enabled),
                    tiling_gap=entry.tiling_gap,
                    tiling_padding=entry.tiling_padding,
                    tiling_avoid_task_panel=entry.tiling_avoid_task_panel,
                    tiling_center_on_failure=entry.tiling_center_on_failure,
                    tiling_relayout=bool(entry.tiling_relayout),
                    make_initial=make_initial,
                )
            )
            continue

        if isinstance(entry, scene_setup_binding_spec_cls):
            transition_style = entry.transition_style if entry.transition_style is not None else default_transition_style
            transition_duration = entry.transition_duration if entry.transition_duration is not None else default_transition_duration
            make_initial = bool(entry.make_initial or (initial_scene_name is not None and str(entry.name) == str(initial_scene_name)))
            specs.append(
                scene_setup_spec_cls(
                    name=str(entry.name),
                    pretty_name=entry.pretty_name,
                    transition_style=transition_style,
                    transition_duration=transition_duration,
                    tiling_enabled=bool(entry.tiling_enabled),
                    tiling_gap=entry.tiling_gap,
                    tiling_padding=entry.tiling_padding,
                    tiling_avoid_task_panel=entry.tiling_avoid_task_panel,
                    tiling_center_on_failure=entry.tiling_center_on_failure,
                    tiling_relayout=bool(entry.tiling_relayout),
                    make_initial=make_initial,
                )
            )
            continue

        if len(entry) == 2:
            name, pretty_name = entry
            transition_style = default_transition_style
            transition_duration = default_transition_duration
        elif len(entry) == 3:
            name, pretty_name, transition_style = entry
            transition_duration = default_transition_duration
        elif len(entry) == 4:
            name, pretty_name, transition_style, transition_duration = entry
        else:
            raise ValueError("Scene setup tuple entries must contain 2-4 values")

        specs.append(
            scene_setup_spec_cls(
                name=str(name),
                pretty_name=None if pretty_name is None else str(pretty_name),
                transition_style=transition_style,
                transition_duration=transition_duration,
                make_initial=bool(initial_scene_name is not None and str(name) == str(initial_scene_name)),
            )
        )
    return tuple(specs)


def build_runtime_scene_specs(
    entries,
    *,
    runtime_scene_binding_spec_cls,
    runtime_scene_spec_cls,
    pristine_asset: str | None = None,
    bind_escape_to_exit: bool = False,
    prewarm: bool = False,
):
    specs = []
    for entry in entries:
        if isinstance(entry, runtime_scene_spec_cls):
            specs.append(entry)
            continue
        if isinstance(entry, runtime_scene_binding_spec_cls):
            specs.append(
                runtime_scene_spec_cls(
                    scene_name=str(entry.scene_name),
                    pristine_asset=entry.pristine_asset,
                    bind_escape_to_exit=bool(entry.bind_escape_to_exit),
                    prewarm=bool(entry.prewarm),
                )
            )
            continue
        if isinstance(entry, str):
            specs.append(
                runtime_scene_spec_cls(
                    scene_name=str(entry),
                    pristine_asset=pristine_asset,
                    bind_escape_to_exit=bool(bind_escape_to_exit),
                    prewarm=bool(prewarm),
                )
            )
            continue

        if len(entry) == 2:
            scene_name, scene_asset = entry
            scene_bind_escape = bind_escape_to_exit
            scene_prewarm = prewarm
        elif len(entry) == 3:
            scene_name, scene_asset, scene_bind_escape = entry
            scene_prewarm = prewarm
        elif len(entry) == 4:
            scene_name, scene_asset, scene_bind_escape, scene_prewarm = entry
        else:
            raise ValueError("Runtime scene tuple entries must contain 2-4 values")

        specs.append(
            runtime_scene_spec_cls(
                scene_name=str(scene_name),
                pristine_asset=None if scene_asset is None else str(scene_asset),
                bind_escape_to_exit=bool(scene_bind_escape),
                prewarm=bool(scene_prewarm),
            )
        )
    return tuple(specs)


def build_scene_root_specs(entries, *, scene_root_binding_spec_cls, scene_root_spec_cls):
    specs = []
    for entry in entries:
        if isinstance(entry, scene_root_spec_cls):
            specs.append(entry)
            continue
        if isinstance(entry, scene_root_binding_spec_cls):
            specs.append(
                scene_root_spec_cls(
                    scene_name=str(entry.scene_name),
                    control_id=str(entry.control_id),
                    draw_background=bool(entry.draw_background),
                )
            )
            continue
        if len(entry) == 2:
            scene_name, control_id = entry
            draw_background = False
        elif len(entry) == 3:
            scene_name, control_id, draw_background = entry
        else:
            raise ValueError("Scene root tuple entries must contain 2-3 values")
        specs.append(
            scene_root_spec_cls(
                scene_name=str(scene_name),
                control_id=str(control_id),
                draw_background=bool(draw_background),
            )
        )
    return tuple(specs)


def build_cursor_specs(entries, *, cursor_binding_spec_cls, cursor_spec_cls, default_hotspot=(0, 0)):
    specs = []
    for entry in entries:
        if isinstance(entry, cursor_spec_cls):
            specs.append(entry)
            continue
        if isinstance(entry, cursor_binding_spec_cls):
            specs.append(
                cursor_spec_cls(
                    name=str(entry.name),
                    path=str(entry.path),
                    hotspot=(int(entry.hotspot[0]), int(entry.hotspot[1])),
                )
            )
            continue
        if len(entry) == 2:
            name, path = entry
            hotspot = default_hotspot
        elif len(entry) == 3:
            name, path, hotspot = entry
        else:
            raise ValueError("Cursor tuple entries must contain 2-3 values")
        specs.append(
            cursor_spec_cls(
                name=str(name),
                path=str(path),
                hotspot=(int(hotspot[0]), int(hotspot[1])),
            )
        )
    return tuple(specs)


def build_font_role_specs(entries, *, font_role_binding_spec_cls, mapping_cls):
    role_map = {}
    passthrough_blocks = []

    for entry in entries:
        if isinstance(entry, mapping_cls):
            passthrough_blocks.append({str(k): dict(v) for k, v in entry.items()})
            continue
        if isinstance(entry, font_role_binding_spec_cls):
            role = str(entry.role)
            role_map[role] = {
                "size": int(entry.size),
                "font": str(entry.font),
                "bold": bool(entry.bold),
                "italic": bool(entry.italic),
            }
            continue
        if len(entry) == 3:
            role, size, font = entry
            bold = False
            italic = False
        elif len(entry) == 5:
            role, size, font, bold, italic = entry
        else:
            raise ValueError("Font role tuple entries must contain 3 or 5 values")
        role_map[str(role)] = {
            "size": int(size),
            "font": str(font),
            "bold": bool(bold),
            "italic": bool(italic),
        }

    blocks = []
    if role_map:
        blocks.append(role_map)
    blocks.extend(passthrough_blocks)
    return tuple(blocks)


def build_scene_bundle_specs(
    entries,
    *,
    scene_setup_spec_cls,
    runtime_scene_spec_cls,
    scene_root_spec_cls,
    action_spec_cls,
    default_transition_style=None,
    default_transition_duration=None,
    default_nav_category: str = "Scenes",
    initial_scene_name: str | None = None,
):
    scene_specs = []
    runtime_specs = []
    root_specs = []
    action_specs = []

    for entry in entries:
        if isinstance(entry, scene_setup_spec_cls):
            scene_specs.append(entry)
            continue
        if isinstance(entry, runtime_scene_spec_cls):
            runtime_specs.append(entry)
            continue
        if isinstance(entry, scene_root_spec_cls):
            root_specs.append(entry)
            continue
        if isinstance(entry, action_spec_cls):
            action_specs.append(entry)
            continue

        scene_name = str(entry.scene_name)
        if entry.emit_scene_setup_spec:
            scene_specs.append(
                scene_setup_spec_cls(
                    name=scene_name,
                    pretty_name=entry.pretty_name,
                    transition_style=entry.transition_style if entry.transition_style is not None else default_transition_style,
                    transition_duration=entry.transition_duration if entry.transition_duration is not None else default_transition_duration,
                    tiling_enabled=bool(entry.tiling_enabled),
                    tiling_gap=entry.tiling_gap,
                    tiling_padding=entry.tiling_padding,
                    tiling_avoid_task_panel=entry.tiling_avoid_task_panel,
                    tiling_center_on_failure=entry.tiling_center_on_failure,
                    tiling_relayout=bool(entry.tiling_relayout),
                    make_initial=bool(entry.make_initial or (initial_scene_name is not None and scene_name == str(initial_scene_name))),
                )
            )

        if entry.emit_runtime_scene_spec:
            runtime_specs.append(
                runtime_scene_spec_cls(
                    scene_name=scene_name,
                    pristine_asset=entry.pristine_asset,
                    bind_escape_to_exit=bool(entry.bind_escape_to_exit),
                    prewarm=bool(entry.prewarm),
                )
            )

        if entry.emit_scene_root_spec:
            root_id = entry.scene_root_id or f"{scene_name}_root"
            root_specs.append(
                scene_root_spec_cls(
                    scene_name=scene_name,
                    control_id=str(root_id),
                    draw_background=bool(entry.scene_root_draw_background),
                )
            )

        if entry.emit_nav_action_spec:
            action_specs.append(
                action_spec_cls(
                    action_id=str(entry.nav_action_id or f"nav_{scene_name}"),
                    label=str(entry.nav_label or f"Go to {entry.pretty_name or scene_name.replace('_', ' ').title()}"),
                    kind="scene_nav",
                    target=scene_name,
                    category=None if entry.nav_category is None else str(entry.nav_category or default_nav_category),
                )
            )

    return (
        tuple(scene_specs),
        tuple(runtime_specs),
        tuple(root_specs),
        tuple(action_specs),
    )


def build_host_application_config(
    config,
    *,
    host_application_binding_spec_cls,
    host_application_config_cls,
    telemetry_config_cls,
    build_scene_bundle_specs_fn,
    build_scene_setup_specs_fn,
    build_runtime_scene_specs_fn,
    build_action_specs_fn,
    build_scene_root_specs_fn,
    build_feature_window_bundle_specs_fn,
    build_feature_specs_fn,
    build_window_toggle_specs_fn,
    build_font_role_specs_fn,
    build_cursor_specs_fn,
    build_static_accessibility_specs_fn,
):
    if isinstance(config, host_application_config_cls):
        return config
    if not isinstance(config, host_application_binding_spec_cls):
        raise TypeError("config must be HostApplicationBindingSpec or HostApplicationConfig")

    telemetry = config.telemetry if config.telemetry is not None else telemetry_config_cls()

    bundle_scene_specs, bundle_runtime_specs, bundle_root_specs, bundle_action_specs = build_scene_bundle_specs_fn(
        config.scene_bundle_entries,
        default_transition_style=config.scene_default_transition_style,
        default_transition_duration=config.scene_default_transition_duration,
        initial_scene_name=str(config.initial_scene_name),
    )

    explicit_scene_specs = build_scene_setup_specs_fn(
        config.scene_entries,
        default_transition_style=config.scene_default_transition_style,
        default_transition_duration=config.scene_default_transition_duration,
        initial_scene_name=str(config.initial_scene_name),
    )
    explicit_runtime_specs = build_runtime_scene_specs_fn(
        config.runtime_scene_entries,
        pristine_asset=config.runtime_default_pristine_asset,
        bind_escape_to_exit=bool(config.runtime_default_bind_escape_to_exit),
        prewarm=bool(config.runtime_default_prewarm),
    )
    explicit_action_specs = build_action_specs_fn(config.action_entries)
    explicit_root_specs = build_scene_root_specs_fn(config.scene_root_entries)

    bundle_feature_specs, bundle_window_specs = build_feature_window_bundle_specs_fn(
        config.feature_window_bundle_entries
    )

    scene_specs = tuple((*bundle_scene_specs, *explicit_scene_specs))
    runtime_scene_specs = tuple((*bundle_runtime_specs, *explicit_runtime_specs))
    action_specs = tuple((*bundle_action_specs, *explicit_action_specs))
    scene_roots = tuple((*bundle_root_specs, *explicit_root_specs))
    feature_specs = tuple((*build_feature_specs_fn(config.feature_entries), *bundle_feature_specs))
    window_specs = tuple((*bundle_window_specs, *build_window_toggle_specs_fn(config.window_entries)))

    return host_application_config_cls(
        display_size=(int(config.display_size[0]), int(config.display_size[1])),
        window_title=str(config.window_title),
        fonts=dict(config.fonts),
        font_role_specs=build_font_role_specs_fn(config.font_role_entries),
        cursors=build_cursor_specs_fn(config.cursor_entries),
        scene_specs=scene_specs,
        feature_specs=feature_specs,
        window_specs=window_specs,
        runtime_scene_specs=runtime_scene_specs,
        action_specs=action_specs,
        static_accessibility_specs=build_static_accessibility_specs_fn(
            config.static_accessibility_entries,
            role=str(config.static_accessibility_role),
        ),
        initial_scene_name=str(config.initial_scene_name),
        scene_roots=scene_roots,
        telemetry=telemetry,
        target_fps=int(config.target_fps),
        palette_spec=config.palette_spec,
    )
