"""Standalone validation harness for high-severity gui package issues.

This script does not modify package source code. It exercises API behavior and
reports whether each issue is confirmed in the current codebase.
"""

from __future__ import annotations

import inspect
import traceback
from dataclasses import dataclass
from typing import Callable, Optional

import pygame
from pygame import Rect

from gui import GuiManager, ButtonStyle, Orientation, ArrowPosition, StateManager


@dataclass
class CaseResult:
    case_id: str
    title: str
    verdict: str
    details: str
    exception_type: Optional[str] = None


def _make_gui() -> GuiManager:
    # Minimal pygame setup for GuiManager/widget construction.
    pygame.init()
    pygame.display.set_mode((320, 240))
    fonts = (
        ("titlebar", "Ubuntu-B.ttf", 14),
        ("normal", "Gimbot.ttf", 16),
    )
    gui = GuiManager(pygame.display.get_surface(), list(fonts))
    gui.bitmap_factory.set_font("normal")
    return gui


def _run_case(case_id: str, title: str, fn: Callable[[], CaseResult]) -> CaseResult:
    try:
        return fn()
    except Exception as exc:  # pragma: no cover - harness safety
        return CaseResult(
            case_id=case_id,
            title=title,
            verdict="INCONCLUSIVE",
            details="Unhandled exception in harness case.",
            exception_type=f"{type(exc).__name__}: {exc}",
        )


def case_sm_unknown_context() -> CaseResult:
    case_id = "C8"
    title = "StateManager unknown context switch should not be silent"

    sm = StateManager()
    try:
        sm.switch_context("does_not_exist")
        active = sm.get_active_context()
        if active is None:
            return CaseResult(
                case_id,
                title,
                "CONFIRMED",
                "switch_context silently ignored unknown context (no exception).",
            )
        return CaseResult(case_id, title, "INCONCLUSIVE", "Unexpected active context created.")
    except Exception as exc:
        return CaseResult(
            case_id,
            title,
            "NOT_CONFIRMED",
            "Unknown context raised explicit exception (behavior improved).",
            exception_type=f"{type(exc).__name__}: {exc}",
        )


def case_scheduler_send_unknown_task() -> CaseResult:
    case_id = "C4A"
    title = "Scheduler.send_message on unknown id should fail explicitly"

    gui = _make_gui()
    try:
        gui.scheduler.send_message("missing-task", {"x": 1})
        return CaseResult(case_id, title, "INCONCLUSIVE", "No exception was raised.")
    except KeyError as exc:
        return CaseResult(
            case_id,
            title,
            "CONFIRMED",
            "Raw KeyError leaked for unknown task id.",
            exception_type=f"{type(exc).__name__}: {exc}",
        )
    except Exception as exc:
        return CaseResult(
            case_id,
            title,
            "NOT_CONFIRMED",
            "Unknown task now raises explicit non-KeyError exception (behavior improved).",
            exception_type=f"{type(exc).__name__}: {exc}",
        )


def case_scheduler_send_missing_handler() -> CaseResult:
    case_id = "C4B"
    title = "Scheduler.send_message without message_method should fail explicitly"

    gui = _make_gui()

    def logic(_task_id):
        yield None

    gui.scheduler.add_task("task-no-handler", logic)
    try:
        gui.scheduler.send_message("task-no-handler", {"x": 1})
        return CaseResult(case_id, title, "INCONCLUSIVE", "No exception was raised.")
    except TypeError as exc:
        return CaseResult(
            case_id,
            title,
            "CONFIRMED",
            "Raw TypeError leaked because message_method is None.",
            exception_type=f"{type(exc).__name__}: {exc}",
        )
    except Exception as exc:
        return CaseResult(
            case_id,
            title,
            "NOT_CONFIRMED",
            "Missing handler now raises explicit non-TypeError exception (behavior improved).",
            exception_type=f"{type(exc).__name__}: {exc}",
        )


def case_button_none_text() -> CaseResult:
    case_id = "C5"
    title = "GuiManager.button(text=None) contract mismatch"

    gui = _make_gui()
    button_text_anno = inspect.signature(GuiManager.button).parameters["text"].annotation
    factory_text_anno = inspect.signature(gui.bitmap_factory._draw_box_style_bitmaps).parameters["text"].annotation

    style_outcomes: list[str] = []
    style_failures: list[str] = []

    for idx, style in enumerate(ButtonStyle):
        try:
            # Create and draw each style so this validates construction and render paths.
            gui.button(f"none-text-{idx}", Rect(10, 10 + (idx * 2), 120, 28), style, None)
            gui.draw_gui()
            style_outcomes.append(style.name)
        except Exception as exc:
            style_failures.append(f"{style.name}: {type(exc).__name__}: {exc}")

    try:
        gui.bitmap_factory.render_text(None)  # type: ignore[arg-type]
        render_text_accepts_none = True
    except Exception:
        render_text_accepts_none = False

    if style_failures:
        return CaseResult(
            case_id,
            title,
            "CONFIRMED",
            "text=None fails for one or more button styles despite Optional[str] API annotation.",
            exception_type="; ".join(style_failures),
        )

    if button_text_anno != factory_text_anno:
        return CaseResult(
            case_id,
            title,
            "CONFIRMED",
            "Public API and internal renderer use incompatible text annotations while all styles currently accept None at runtime.",
            exception_type=(
                f"GuiManager.button.text annotation={button_text_anno}, "
                f"BitmapFactory._draw_box_style_bitmaps.text annotation={factory_text_anno}, "
                f"render_text_accepts_none={render_text_accepts_none}, styles_tested={','.join(style_outcomes)}"
            ),
        )

    return CaseResult(
        case_id,
        title,
        "NOT_CONFIRMED",
        "No runtime or annotation-level mismatch detected for text=None.",
    )


def case_scrollbar_invalid_range() -> CaseResult:
    case_id = "C3"
    title = "Scrollbar accepts invalid range parameters"

    gui = _make_gui()
    try:
        # Invalid params: bar_size > total_range.
        sb = gui.scrollbar(
            "sb-invalid",
            Rect(10, 10, 200, 20),
            Orientation.Horizontal,
            ArrowPosition.Skip,
            (10, 0, 20, 1),
        )
    except Exception as exc:
        return CaseResult(
            case_id,
            title,
            "NOT_CONFIRMED",
            "Invalid range is now rejected with explicit exception (behavior improved).",
            exception_type=f"{type(exc).__name__}: {exc}",
        )

    if sb._bar_size > sb._total_range:
        return CaseResult(
            case_id,
            title,
            "CONFIRMED",
            "Invalid range was accepted with no validation (bar_size > total_range).",
        )
    return CaseResult(
        case_id,
        title,
        "NOT_CONFIRMED",
        "Invalid range appears to be rejected or normalized.",
    )


def main() -> None:
    cases = [
        ("C8", "StateManager unknown context", case_sm_unknown_context),
        ("C4A", "Scheduler unknown task", case_scheduler_send_unknown_task),
        ("C4B", "Scheduler missing message handler", case_scheduler_send_missing_handler),
        ("C5", "Button Optional[str] mismatch", case_button_none_text),
        ("C3", "Scrollbar invalid range", case_scrollbar_invalid_range),
    ]

    results: list[CaseResult] = []

    for case_id, title, fn in cases:
        result = _run_case(case_id, title, fn)
        results.append(result)

    print("=== GUI_DO ISSUE VALIDATION HARNESS ===")
    confirmed = 0
    for r in results:
        if r.verdict == "CONFIRMED":
            confirmed += 1
        print(f"[{r.case_id}] {r.verdict} - {r.title}")
        print(f"  Details: {r.details}")
        if r.exception_type:
            print(f"  Exception: {r.exception_type}")

    print("----------------------------------------")
    print(f"Confirmed: {confirmed}/{len(results)}")
    print("Legend: CONFIRMED=issue reproduced, NOT_CONFIRMED=issue appears fixed, INCONCLUSIVE=needs deeper manual check")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("Harness failed unexpectedly.")
        traceback.print_exc()
    finally:
        pygame.quit()
