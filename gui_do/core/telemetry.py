from __future__ import annotations

from contextlib import ContextDecorator
from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
from threading import RLock
from time import perf_counter, time
from typing import Any, Dict, Optional

from .telemetry_analyzer import analyze_telemetry_records, render_telemetry_report
from .error_handling import io_error, logical_error


@dataclass(frozen=True)
class TelemetrySample:
    timestamp: float
    system: str
    point: str
    elapsed_ms: float
    metadata: Dict[str, Any]


class _TelemetrySpan(ContextDecorator):
    def __init__(self, collector, system: str, point: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        self._collector = collector
        self._system = str(system)
        self._point = str(point)
        self._metadata = dict(metadata or {})
        self._start = 0.0
        self._active = collector.should_record(self._system, self._point)

    def __enter__(self):
        if self._active:
            self._start = perf_counter()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if not self._active:
            return None
        metadata = dict(self._metadata)
        if exc is not None:
            metadata.setdefault("exception", f"{type(exc).__name__}: {exc}")
        self._collector.record_duration(self._system, self._point, (perf_counter() - self._start) * 1000.0, metadata=metadata)
        return None


class TelemetryCollector:
    """Default-off telemetry collector with optional file logging and report output."""

    def __init__(self) -> None:
        self._enabled = False
        self._live_analysis_enabled = False
        self._file_logging_enabled = False
        self._auto_report_on_shutdown = True
        self._min_duration_ms = 0.0
        self._system_overrides: Dict[str, bool] = {}
        self._point_overrides: Dict[str, bool] = {}
        self._samples: list[TelemetrySample] = []
        self._log_directory = self._default_log_directory()
        self._log_file_path: Optional[Path] = None
        self._run_id: Optional[str] = None
        self._lock = RLock()

    @staticmethod
    def _default_log_directory() -> Path:
        return Path(__file__).resolve().parents[2]

    @staticmethod
    def _normalize_key(system: str, point: str) -> tuple[str, str, str]:
        normalized_system = str(system).strip().lower()
        normalized_point = str(point).strip().lower()
        if not normalized_system:
            raise logical_error(
                "system must be a non-empty string",
                subsystem="gui.telemetry",
                operation="TelemetryCollector._normalize_key",
                exc_type=ValueError,
                details={"system": system},
                source_skip_frames=1,
            )
        if not normalized_point:
            raise logical_error(
                "point must be a non-empty string",
                subsystem="gui.telemetry",
                operation="TelemetryCollector._normalize_key",
                exc_type=ValueError,
                details={"point": point},
                source_skip_frames=1,
            )
        return normalized_system, normalized_point, f"{normalized_system}.{normalized_point}"

    def reset(self) -> None:
        with self._lock:
            self._samples.clear()
            self._log_file_path = None
            self._run_id = None

    def enable(self) -> None:
        with self._lock:
            self._enabled = True

    def disable(self) -> None:
        with self._lock:
            self._enabled = False

    def enabled(self) -> bool:
        with self._lock:
            return self._enabled

    def set_live_analysis_enabled(self, enabled: bool) -> None:
        with self._lock:
            self._live_analysis_enabled = bool(enabled)

    def live_analysis_enabled(self) -> bool:
        with self._lock:
            return self._live_analysis_enabled

    def set_file_logging_enabled(self, enabled: bool) -> None:
        with self._lock:
            self._file_logging_enabled = bool(enabled)
            if not self._file_logging_enabled:
                self._log_file_path = None

    def file_logging_enabled(self) -> bool:
        with self._lock:
            return self._file_logging_enabled

    def set_auto_report_on_shutdown(self, enabled: bool) -> None:
        with self._lock:
            self._auto_report_on_shutdown = bool(enabled)

    def set_min_duration_ms(self, minimum: float) -> None:
        value = float(minimum)
        if value < 0.0:
            raise logical_error(
                "minimum must be >= 0.0",
                subsystem="gui.telemetry",
                operation="TelemetryCollector.set_min_duration_ms",
                exc_type=ValueError,
                details={"minimum": minimum},
                source_skip_frames=1,
            )
        with self._lock:
            self._min_duration_ms = value

    def set_log_directory(self, directory: str | Path) -> None:
        path = Path(directory)
        with self._lock:
            self._log_directory = path
            self._log_file_path = None

    def set_system_enabled(self, system: str, enabled: bool) -> None:
        normalized_system = str(system).strip().lower()
        if not normalized_system:
            raise logical_error(
                "system must be a non-empty string",
                subsystem="gui.telemetry",
                operation="TelemetryCollector.set_system_enabled",
                exc_type=ValueError,
                details={"system": system, "enabled": bool(enabled)},
                source_skip_frames=1,
            )
        with self._lock:
            self._system_overrides[normalized_system] = bool(enabled)

    def set_point_enabled(self, system: str, point: str, enabled: bool) -> None:
        _, _, key = self._normalize_key(system, point)
        with self._lock:
            self._point_overrides[key] = bool(enabled)

    def clear_filters(self) -> None:
        with self._lock:
            self._system_overrides.clear()
            self._point_overrides.clear()

    def should_record(self, system: str, point: str) -> bool:
        normalized_system, _, key = self._normalize_key(system, point)
        with self._lock:
            if not self._enabled:
                return False
            if key in self._point_overrides:
                return bool(self._point_overrides[key])
            if normalized_system in self._system_overrides:
                return bool(self._system_overrides[normalized_system])
            return True

    def span(self, system: str, point: str, metadata: Optional[Dict[str, Any]] = None) -> _TelemetrySpan:
        return _TelemetrySpan(self, system, point, metadata=metadata)

    def record_duration(self, system: str, point: str, elapsed_ms: float, *, metadata: Optional[Dict[str, Any]] = None) -> None:
        normalized_system, normalized_point, key = self._normalize_key(system, point)
        elapsed = max(0.0, float(elapsed_ms))
        payload = dict(metadata or {})
        with self._lock:
            if not self._enabled:
                return
            if key in self._point_overrides and not self._point_overrides[key]:
                return
            if normalized_system in self._system_overrides and not self._system_overrides[normalized_system]:
                return
            if elapsed < self._min_duration_ms:
                return

            sample = TelemetrySample(
                timestamp=time(),
                system=normalized_system,
                point=normalized_point,
                elapsed_ms=elapsed,
                metadata=payload,
            )
            self._samples.append(sample)
            if self._file_logging_enabled:
                self._append_log_sample(sample)

    def snapshot(self) -> list[TelemetrySample]:
        with self._lock:
            return list(self._samples)

    def summary(self, *, top_n: int = 12):
        with self._lock:
            samples = list(self._samples)
        return analyze_telemetry_records(samples, top_n=top_n)

    def write_report(self, *, top_n: int = 12, output_path: str | Path | None = None) -> Optional[str]:
        with self._lock:
            if not self._samples:
                return None
            source = str(self._active_log_file_path() or "in-memory")
            analysis = analyze_telemetry_records(self._samples, top_n=top_n)
            content = render_telemetry_report(analysis, source=source)
            if output_path is None:
                report_path = self._build_output_path("report", "txt")
            else:
                report_path = Path(output_path)
            try:
                report_path.parent.mkdir(parents=True, exist_ok=True)
                report_path.write_text(content, encoding="utf-8")
            except Exception as exc:
                raise io_error(
                    "failed to write telemetry report",
                    subsystem="gui.telemetry",
                    operation="TelemetryCollector.write_report",
                    cause=exc,
                    path=str(report_path),
                    exc_type=RuntimeError,
                    source_skip_frames=1,
                ) from exc
            return str(report_path)

    def shutdown(self) -> Optional[str]:
        with self._lock:
            should_write = self._enabled and self._auto_report_on_shutdown and self._live_analysis_enabled and bool(self._samples)
        if not should_write:
            return None
        return self.write_report()

    def _active_log_file_path(self) -> Optional[Path]:
        if self._log_file_path is None and self._file_logging_enabled:
            self._log_file_path = self._build_output_path("samples", "jsonl")
        return self._log_file_path

    def _append_log_sample(self, sample: TelemetrySample) -> None:
        path = self._active_log_file_path()
        if path is None:
            return
        payload = {
            "type": "sample",
            "timestamp": sample.timestamp,
            "system": sample.system,
            "point": sample.point,
            "elapsed_ms": sample.elapsed_ms,
            "metadata": sample.metadata,
        }
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload, sort_keys=True) + "\n")
        except Exception as exc:
            raise io_error(
                "failed to append telemetry sample to log file",
                subsystem="gui.telemetry",
                operation="TelemetryCollector._append_log_sample",
                cause=exc,
                path=str(path),
                exc_type=RuntimeError,
                details={"system": sample.system, "point": sample.point},
                source_skip_frames=1,
            ) from exc

    def _build_output_path(self, suffix: str, extension: str) -> Path:
        if self._run_id is None:
            self._run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"gui_do_telemetry_{self._run_id}_{suffix}.{extension}"
        return self._log_directory / filename


_GLOBAL_TELEMETRY = TelemetryCollector()


def telemetry_collector() -> TelemetryCollector:
    return _GLOBAL_TELEMETRY


def configure_telemetry(
    *,
    enabled: Optional[bool] = None,
    live_analysis_enabled: Optional[bool] = None,
    file_logging_enabled: Optional[bool] = None,
    min_duration_ms: Optional[float] = None,
    log_directory: Optional[str | Path] = None,
) -> TelemetryCollector:
    collector = telemetry_collector()
    if enabled is not None:
        collector.enable() if enabled else collector.disable()
    if live_analysis_enabled is not None:
        collector.set_live_analysis_enabled(live_analysis_enabled)
    if file_logging_enabled is not None:
        collector.set_file_logging_enabled(file_logging_enabled)
    if min_duration_ms is not None:
        collector.set_min_duration_ms(min_duration_ms)
    if log_directory is not None:
        collector.set_log_directory(log_directory)
    return collector
