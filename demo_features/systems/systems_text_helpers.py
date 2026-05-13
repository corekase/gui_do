"""Text-tab helper routines for the systems demo feature."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame
from pygame import Rect

from gui_do import ButtonControl, DropdownControl, DropdownOption, LabelControl, PanelControl, TextInputControl, TextSearcher, TextSpan

if TYPE_CHECKING:
    from .systems_feature import SystemsFeature


def build_text_panel(feature: SystemsFeature, rect: Rect) -> PanelControl:
    panel = PanelControl("systems_text_panel", Rect(rect), draw_background=False)
    locale_label = LabelControl(
        "systems_text_locale_label",
        Rect(0, 0, 96, 28),
        "Locale",
        align="left",
    )

    locale_options = [DropdownOption(code.upper(), code) for code in feature._locale_registry.registered_locales]
    selected_locale = feature._locale_registry.active_locale
    selected_index = next(
        (index for index, option in enumerate(locale_options) if option.value == selected_locale),
        0,
    )
    feature.text_locale_dropdown = DropdownControl(
        "systems_text_locale",
        Rect(0, 0, 160, 32),
        options=locale_options,
        selected_index=selected_index,
        on_change=lambda value, _index: feature._on_text_locale_changed(value),
    )
    feature._place_compact_labeled_row(
        panel,
        left=feature.LEFT_SIDE_INSET_X,
        top=0,
        label=locale_label,
        field=feature.text_locale_dropdown,
        label_width=96,
        gap=2,
    )

    query_label = LabelControl(
        "systems_text_query_label",
        Rect(0, 0, 72, 28),
        "Search",
        align="left",
    )
    feature.text_query_input = TextInputControl(
        "systems_text_query",
        Rect(0, 0, max(180, rect.width - 386), 32),
        value=feature._text_search_query,
        placeholder="release",
        on_change=feature._on_text_query_changed,
    )
    feature._place_compact_labeled_row(
        panel,
        left=278 + feature.LEFT_SIDE_INSET_X,
        top=0,
        label=query_label,
        field=feature.text_query_input,
        label_width=72,
        gap=0,
    )

    labels_top = feature._add_button_rows(
        panel,
        rect,
        44,
        [
            ButtonControl(
                "systems_text_search",
                Rect(0, 0, 140, 32),
                "Run Search",
                feature._run_text_search,
                style="round",
            ),
            ButtonControl(
                "systems_text_next",
                Rect(0, 0, 146, 32),
                "Next Match",
                feature._next_text_match,
                style="round",
            ),
            ButtonControl(
                "systems_text_replace",
                Rect(0, 0, 174, 32),
                "Replace First Match",
                feature._replace_first_text_match,
                style="round",
            ),
            ButtonControl(
                "systems_text_mode_case",
                Rect(0, 0, 140, 32),
                "Case: Off",
                feature._toggle_text_case_sensitive,
                style="round",
            ),
            ButtonControl(
                "systems_text_mode_whole",
                Rect(0, 0, 170, 32),
                "Whole Word: Off",
                feature._toggle_text_whole_word,
                style="round",
            ),
            ButtonControl(
                "systems_text_mode_regex",
                Rect(0, 0, 140, 32),
                "Regex: Off",
                feature._toggle_text_regex,
                style="round",
            ),
            ButtonControl(
                "systems_text_regex_preset",
                Rect(0, 0, 174, 32),
                "Regex Preset",
                feature._apply_text_regex_preset,
                style="round",
            ),
            ButtonControl(
                "systems_text_locale_regex_preset",
                Rect(0, 0, 204, 32),
                "Locale Regex Preset",
                feature._apply_text_locale_regex_preset,
                style="round",
            ),
        ],
        per_row=3,
        left=feature.PANEL_PADDING_X + feature.LEFT_SIDE_INSET_X,
        width=max(
            1,
            rect.width - (feature.PANEL_PADDING_X * 2) - (feature.LEFT_SIDE_INSET_X * 2),
        ),
    )

    for child in panel.children:
        if child.control_id == "systems_text_mode_case":
            feature.text_mode_case_button = child
        elif child.control_id == "systems_text_mode_whole":
            feature.text_mode_whole_word_button = child
        elif child.control_id == "systems_text_mode_regex":
            feature.text_mode_regex_button = child

    feature.text_search_status_label = LabelControl(
        "systems_text_status",
        Rect(0, 0, rect.width, 28),
        "",
        align="left",
    )
    feature.text_search_match_label = LabelControl(
        "systems_text_match_status",
        Rect(0, 0, rect.width, 28),
        "",
        align="left",
    )
    preview_top = labels_top + 80
    preview_height = max(120, rect.height - preview_top - 12)
    preview_width = rect.width - feature.PANEL_PADDING_X * 2
    feature._place_vertical_label_stack(
        panel,
        Rect(
            feature.LABEL_INSET_X,
            labels_top + 8,
            max(1, rect.width - feature.LABEL_INSET_X),
            64,
        ),
        [
            feature.text_search_status_label,
            feature.text_search_match_label,
        ],
        gap=8,
    )
    feature._place_text_preview_region(
        panel,
        top=preview_top,
        width=preview_width,
        height=preview_height,
    )
    feature._refresh_text_labels()
    return panel


def rebuild_text_document(feature: SystemsFeature) -> None:
    title = feature._locale_registry.t("systems.text.title", fallback="Release Notes")
    summary = feature._locale_registry.t("systems.text.summary", fallback="Systems demo summary unavailable.")
    actions = feature._locale_registry.t("systems.text.actions", fallback="Action items unavailable.")
    hint = feature._locale_registry.t("systems.text.hint", fallback="Search for release.")
    feature._text_searcher.text = f"{title}\n{summary}\n{actions}\n{hint}"


def rebuild_text_searcher(feature: SystemsFeature) -> None:
    source_text = feature._text_searcher.text
    feature._text_searcher = TextSearcher(
        source_text,
        case_sensitive=feature._text_case_sensitive,
        whole_word=feature._text_whole_word,
        use_regex=feature._text_use_regex,
    )


def on_text_locale_changed(feature: SystemsFeature, value: str) -> None:
    feature._locale_registry.set_locale(str(value))
    feature._text_search_cursor = 0
    feature._text_last_action = f"Locale switched to {feature._locale_registry.active_locale.upper()}."
    feature._rebuild_text_document()
    feature._refresh_text_labels()


def on_text_query_changed(feature: SystemsFeature, value: str) -> None:
    feature._text_search_query = str(value)


def run_text_search(feature: SystemsFeature) -> None:
    feature._text_search_cursor = 0
    feature._text_last_action = "Search refreshed for current localized note."
    feature._refresh_text_labels()


def toggle_text_case_sensitive(feature: SystemsFeature) -> None:
    feature._text_case_sensitive = not feature._text_case_sensitive
    feature._text_search_cursor = 0
    feature._rebuild_text_searcher()
    feature._text_last_action = f"Case-sensitive mode {'enabled' if feature._text_case_sensitive else 'disabled'}."
    feature._refresh_text_labels()


def toggle_text_whole_word(feature: SystemsFeature) -> None:
    feature._text_whole_word = not feature._text_whole_word
    feature._text_search_cursor = 0
    feature._rebuild_text_searcher()
    feature._text_last_action = f"Whole-word mode {'enabled' if feature._text_whole_word else 'disabled'}."
    feature._refresh_text_labels()


def toggle_text_regex(feature: SystemsFeature) -> None:
    feature._text_use_regex = not feature._text_use_regex
    feature._text_search_cursor = 0
    feature._rebuild_text_searcher()
    feature._text_last_action = f"Regex mode {'enabled' if feature._text_use_regex else 'disabled'}."
    feature._refresh_text_labels()


def apply_text_regex_preset(feature: SystemsFeature) -> None:
    preset = r"\b(?:release|rollout|checks?)\w*\b"
    feature._text_search_query = preset
    if feature.text_query_input is not None:
        feature.text_query_input.set_value(preset)
    if not feature._text_use_regex:
        feature._text_use_regex = True
        feature._rebuild_text_searcher()
    feature._text_search_cursor = 0
    feature._text_last_action = "Applied regex preset for release-note keyword scanning."
    feature._refresh_text_labels()


def apply_text_locale_regex_preset(feature: SystemsFeature) -> None:
    preset = r"\b(?:release|rollout|checks?|lanzamiento|despliegue|pruebas|version|deploiement)\w*\b"
    feature._text_search_query = preset
    if feature.text_query_input is not None:
        feature.text_query_input.set_value(preset)
    if not feature._text_use_regex:
        feature._text_use_regex = True
        feature._rebuild_text_searcher()
    feature._text_search_cursor = 0
    feature._text_last_action = "Applied locale regex preset for EN/ES/FR release terms."
    feature._refresh_text_labels()


def next_text_match(feature: SystemsFeature) -> None:
    query = feature._text_search_query.strip()
    matches = feature._text_searcher.find_all(query)
    if not matches:
        feature._text_last_action = "No matches available for next navigation."
        feature._refresh_text_labels()
        return
    feature._text_search_cursor = (feature._text_search_cursor + 1) % len(matches)
    feature._text_last_action = f"Advanced to match {feature._text_search_cursor + 1} of {len(matches)}."
    feature._refresh_text_labels()


def replace_first_text_match(feature: SystemsFeature) -> None:
    query = feature._text_search_query.strip()
    if not query:
        feature._text_last_action = "Enter a search token before replace."
        feature._refresh_text_labels()
        return
    match = feature._text_searcher.find_next(query, from_pos=0)
    if match is None:
        feature._text_last_action = "No match found to replace."
        feature._refresh_text_labels()
        return
    replacement = feature._locale_registry.t("systems.text.replacement", fallback="deployment")
    feature._text_searcher.text = feature._text_searcher.replace(match, replacement)
    feature._text_search_cursor = 0
    feature._text_last_action = f"Replaced first '{query}' with '{replacement}'."
    feature._refresh_text_labels()


def build_text_preview_spans(_feature: SystemsFeature, text: str, matches: list[object], active_index: int) -> list[TextSpan]:
    if not matches:
        return [TextSpan(text, color=(226, 232, 240), role="body")]
    spans: list[TextSpan] = []
    cursor = 0
    for index, match in enumerate(matches):
        start = int(match.start)
        end = int(match.end)
        if start > cursor:
            spans.append(TextSpan(text[cursor:start], color=(226, 232, 240), role="body"))
        spans.append(
            TextSpan(
                text[start:end],
                bold=True,
                color=(255, 202, 122) if index == active_index else (155, 209, 255),
                role="body",
            )
        )
        cursor = end
    if cursor < len(text):
        spans.append(TextSpan(text[cursor:], color=(226, 232, 240), role="body"))
    return spans


def render_text_preview_fallback(_feature: SystemsFeature, surface, text: str) -> None:
    font = pygame.font.Font(None, 20)
    color = (226, 232, 240)
    y = 8
    max_width = max(8, surface.get_width() - 16)
    for line in text.splitlines():
        words = line.split(" ")
        current = ""
        for word in words:
            test = word if not current else f"{current} {word}"
            if font.size(test)[0] <= max_width:
                current = test
            else:
                surface.blit(font.render(current, True, color), (8, y))
                y += 22
                current = word
        if current:
            surface.blit(font.render(current, True, color), (8, y))
            y += 22
        y += 4
        if y > surface.get_height() - 24:
            break


def render_text_preview(feature: SystemsFeature, matches: list[object], active_index: int) -> None:
    if feature.text_preview_canvas is None:
        return
    surface = feature.text_preview_canvas.get_canvas_surface()
    surface.fill((27, 32, 38))
    text = feature._text_searcher.text
    spans = feature._build_text_preview_spans(text, matches, active_index)
    feature._text_flow.width = max(1, surface.get_width() - 12)
    feature._text_flow.set_content(spans)
    theme = getattr(getattr(feature.demo, "app", None), "theme", None)
    if theme is not None:
        try:
            feature._text_flow.layout(theme)
            feature._text_flow.render(surface, 6, 6)
        except Exception:
            feature._render_text_preview_fallback(surface, text)
    else:
        feature._render_text_preview_fallback(surface, text)
    feature.text_preview_canvas.invalidate()


def refresh_text_labels(feature: SystemsFeature) -> None:
    query = feature._text_search_query.strip()
    matches = feature._text_searcher.find_all(query)
    active_index = min(feature._text_search_cursor, max(0, len(matches) - 1)) if matches else -1
    if feature.text_mode_case_button is not None:
        feature.text_mode_case_button.text = f"Case: {'On' if feature._text_case_sensitive else 'Off'}"
    if feature.text_mode_whole_word_button is not None:
        feature.text_mode_whole_word_button.text = f"Whole Word: {'On' if feature._text_whole_word else 'Off'}"
    if feature.text_mode_regex_button is not None:
        feature.text_mode_regex_button.text = f"Regex: {'On' if feature._text_use_regex else 'Off'}"
    if feature.text_search_status_label is not None:
        locale = feature._locale_registry.active_locale.upper()
        translated_title = feature._locale_registry.t("systems.text.title", fallback="Release Notes")
        feature.text_search_status_label.text = (
            f"LocaleRegistry active={locale} locales={feature._locale_registry.registered_locales} | "
            f"StringTable title='{translated_title}' | modes(case={feature._text_case_sensitive}, whole={feature._text_whole_word}, regex={feature._text_use_regex})"
        )
    if feature.text_search_match_label is not None:
        if not query:
            feature.text_search_match_label.text = "TextSearcher waiting for a search token."
        elif not matches:
            feature.text_search_match_label.text = (
                f"TextSearcher found no matches for '{query}'. {feature._text_last_action}"
            )
        else:
            current = matches[active_index]
            feature.text_search_match_label.text = (
                f"TextSearcher matches={len(matches)} current={active_index + 1} "
                f"span=({current.start},{current.end}) | {feature._text_last_action}"
            )
    feature._render_text_preview(matches, active_index)


__all__ = [
    "apply_text_locale_regex_preset",
    "apply_text_regex_preset",
    "build_text_panel",
    "build_text_preview_spans",
    "next_text_match",
    "on_text_locale_changed",
    "on_text_query_changed",
    "rebuild_text_document",
    "rebuild_text_searcher",
    "refresh_text_labels",
    "render_text_preview",
    "render_text_preview_fallback",
    "replace_first_text_match",
    "run_text_search",
    "toggle_text_case_sensitive",
    "toggle_text_regex",
    "toggle_text_whole_word",
]
