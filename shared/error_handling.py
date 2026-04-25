from __future__ import annotations

from dataclasses import dataclass
import inspect
import logging
from pathlib import Path
from typing import Any, Mapping, Optional

_LOGGER = logging.getLogger("gui_do.errors")


@dataclass(frozen=True)
class ErrorContext:
    kind: str
    subsystem: str
    operation: str
    reason: str
    source: str
    path: Optional[str] = None
    details: Optional[Mapping[str, Any]] = None
    cause: Optional[BaseException] = None


def _safe_text(value: Any) -> str:
    text = str(value).strip()
    return text or "unknown"


def discover_error_source(*, skip_frames: int = 0, exclude_module_prefixes: tuple[str, ...] = ("gui.", "shared.")) -> str:
    """Best-effort source attribution for user-facing diagnostics.

    Returns the nearest call frame that is not inside gui/shared internals when
    possible, so diagnostics point users to their calling site.
    """
    stack = inspect.stack(context=0)
    try:
        start_index = max(0, int(skip_frames) + 1)
        for frame_info in stack[start_index:]:
            module = inspect.getmodule(frame_info.frame)
            module_name = "" if module is None else str(module.__name__)
            if module_name.startswith(exclude_module_prefixes):
                continue
            filename = Path(frame_info.filename).name
            return f"{module_name or filename}:{frame_info.function}:{frame_info.lineno}"
        fallback = stack[start_index] if start_index < len(stack) else stack[-1]
        fallback_name = Path(fallback.filename).name
        return f"{fallback_name}:{fallback.function}:{fallback.lineno}"
    finally:
        del stack


def format_error_message(context: ErrorContext) -> str:
    parts = [
        _safe_text(context.reason),
        (
            f"[kind={_safe_text(context.kind)} "
            f"subsystem={_safe_text(context.subsystem)} "
            f"operation={_safe_text(context.operation)} "
            f"source={_safe_text(context.source)}"
        ),
    ]
    if context.path is not None:
        parts.append(f" path={context.path!r}")
    details = dict(context.details or {})
    if details:
        detail_pairs = ", ".join(f"{key}={value!r}" for key, value in sorted(details.items(), key=lambda item: str(item[0])))
        parts.append(f" details={{{detail_pairs}}}")
    if context.cause is not None:
        parts.append(f" cause={type(context.cause).__name__}: {context.cause}")
    parts.append("]")
    return "".join(parts)


def _build_context(
    *,
    kind: str,
    subsystem: str,
    operation: str,
    reason: str,
    source: Optional[str],
    path: Optional[str],
    details: Optional[Mapping[str, Any]],
    cause: Optional[BaseException],
    source_skip_frames: int,
) -> ErrorContext:
    resolved_source = source or discover_error_source(skip_frames=source_skip_frames + 1)
    resolved_path = None if path is None else str(path)
    return ErrorContext(
        kind=kind,
        subsystem=subsystem,
        operation=operation,
        reason=reason,
        source=resolved_source,
        path=resolved_path,
        details=None if details is None else dict(details),
        cause=cause,
    )


def logical_error(
    reason: str,
    *,
    subsystem: str,
    operation: str,
    exc_type: type[Exception] = ValueError,
    source: Optional[str] = None,
    details: Optional[Mapping[str, Any]] = None,
    source_skip_frames: int = 0,
) -> Exception:
    context = _build_context(
        kind="logical",
        subsystem=subsystem,
        operation=operation,
        reason=reason,
        source=source,
        path=None,
        details=details,
        cause=None,
        source_skip_frames=source_skip_frames + 1,
    )
    return exc_type(format_error_message(context))


def io_error(
    reason: str,
    *,
    subsystem: str,
    operation: str,
    cause: BaseException,
    path: Optional[str] = None,
    exc_type: type[Exception] = RuntimeError,
    source: Optional[str] = None,
    details: Optional[Mapping[str, Any]] = None,
    source_skip_frames: int = 0,
) -> Exception:
    context = _build_context(
        kind="io",
        subsystem=subsystem,
        operation=operation,
        reason=reason,
        source=source,
        path=path,
        details=details,
        cause=cause,
        source_skip_frames=source_skip_frames + 1,
    )
    return exc_type(format_error_message(context))


def report_nonfatal_error(
    reason: str,
    *,
    kind: str,
    subsystem: str,
    operation: str,
    cause: Optional[BaseException] = None,
    path: Optional[str] = None,
    source: Optional[str] = None,
    details: Optional[Mapping[str, Any]] = None,
    source_skip_frames: int = 0,
) -> None:
    context = _build_context(
        kind=kind,
        subsystem=subsystem,
        operation=operation,
        reason=reason,
        source=source,
        path=path,
        details=details,
        cause=cause,
        source_skip_frames=source_skip_frames + 1,
    )
    message = format_error_message(context)
    if cause is None:
        _LOGGER.warning(message)
        return
    _LOGGER.warning(message, exc_info=(type(cause), cause, cause.__traceback__))
