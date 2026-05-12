from __future__ import annotations

from collections.abc import Mapping

from ..app.error_handling import logical_error


def setup_standard_font_roles(font_roles, fonts: dict, *role_specs: dict):
    """Register conventional default/title and custom role fonts."""
    if font_roles is None or not fonts:
        return

    normalized_fonts: dict[str, dict[str, object]] = {}
    for key, raw_spec in fonts.items():
        if isinstance(raw_spec, str):
            normalized_fonts[str(key)] = {"file_path": raw_spec}
            continue
        if isinstance(raw_spec, Mapping):
            file_path = raw_spec.get("file_path", raw_spec.get("file", raw_spec.get("path")))
            system_name = raw_spec.get("system_name", raw_spec.get("system"))
            size = raw_spec.get("size")
            normalized_fonts[str(key)] = {
                "file_path": file_path,
                "system_name": system_name,
                "size": size,
                "bold": bool(raw_spec.get("bold", False)),
                "italic": bool(raw_spec.get("italic", False)),
            }

    default_font_spec = normalized_fonts.get("default")
    body_font_spec = normalized_fonts.get("body")
    window_font_spec = normalized_fonts.get("window")

    if default_font_spec is not None:
        default_size = default_font_spec.get("size")
        if default_size is not None:
            font_roles.define(
                "default",
                size=default_size,
                file_path=default_font_spec.get("file_path"),
                system_name=default_font_spec.get("system_name"),
                bold=bool(default_font_spec.get("bold", False)),
                italic=bool(default_font_spec.get("italic", False)),
            )

    def _resolve_font_spec_for_cfg(cfg: Mapping[str, object]) -> tuple[dict[str, object] | None, object | None]:
        font_key = cfg.get("font")
        if font_key is None:
            if default_font_spec is not None:
                font_key = "default"
            else:
                font_key = "body"
        selected_font = normalized_fonts.get(str(font_key))
        if selected_font is None:
            selected_font = default_font_spec if default_font_spec is not None else body_font_spec
        if selected_font is None:
            return None, None
        resolved_size = cfg.get("size", selected_font.get("size"))
        return selected_font, resolved_size

    explicit_title_cfg: Mapping[str, object] | None = None
    explicit_window_title_cfg: Mapping[str, object] | None = None
    for spec in role_specs:
        for role, cfg in spec.items():
            if not isinstance(cfg, Mapping):
                continue
            if role == "title":
                explicit_title_cfg = cfg
            elif role == "window_title":
                explicit_window_title_cfg = cfg

    title_role_resolved = False
    if explicit_title_cfg is not None:
        selected_font, resolved_size = _resolve_font_spec_for_cfg(explicit_title_cfg)
        if selected_font is not None and resolved_size is not None:
            font_roles.define(
                "title",
                size=resolved_size,
                file_path=selected_font.get("file_path"),
                system_name=selected_font.get("system_name"),
                bold=bool(explicit_title_cfg.get("bold", selected_font.get("bold", False))),
                italic=bool(explicit_title_cfg.get("italic", selected_font.get("italic", False))),
            )
            title_role_resolved = True
    elif explicit_window_title_cfg is not None:
        selected_font, resolved_size = _resolve_font_spec_for_cfg(explicit_window_title_cfg)
        if selected_font is not None and resolved_size is not None:
            font_roles.define(
                "title",
                size=resolved_size,
                file_path=selected_font.get("file_path"),
                system_name=selected_font.get("system_name"),
                bold=bool(explicit_window_title_cfg.get("bold", selected_font.get("bold", False))),
                italic=bool(explicit_window_title_cfg.get("italic", selected_font.get("italic", False))),
            )
            title_role_resolved = True
    elif window_font_spec is not None:
        font_roles.define(
            "title",
            size=18,
            file_path=window_font_spec.get("file_path"),
            system_name=window_font_spec.get("system_name"),
            bold=bool(window_font_spec.get("bold", False)),
            italic=bool(window_font_spec.get("italic", False)),
        )
        title_role_resolved = True

    if not title_role_resolved:
        raise logical_error(
            "unable to resolve standard window title font role",
            subsystem="gui.fonts",
            operation="setup_standard_font_roles",
            details={
                "required_role": "title",
                "resolution_steps": (
                    "explicit title",
                    "explicit window_title",
                    "window alias size 18",
                ),
                "has_window_font": window_font_spec is not None,
            },
            source_skip_frames=1,
        )

    for spec in role_specs:
        for role, cfg in spec.items():
            selected_font, resolved_size = _resolve_font_spec_for_cfg(cfg)
            if selected_font is None:
                continue
            if resolved_size is None:
                continue

            font_roles.define(
                role,
                size=resolved_size,
                file_path=selected_font.get("file_path"),
                system_name=selected_font.get("system_name"),
                bold=bool(cfg.get("bold", selected_font.get("bold", False))),
                italic=bool(cfg.get("italic", selected_font.get("italic", False))),
            )
