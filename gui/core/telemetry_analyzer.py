from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
from statistics import mean
from typing import Any, Dict, Iterable, List, Sequence


@dataclass(frozen=True)
class TelemetryHotspot:
    key: str
    count: int
    total_ms: float
    average_ms: float
    max_ms: float
    p95_ms: float


@dataclass(frozen=True)
class TelemetryAnalysis:
    sample_count: int
    systems: tuple[str, ...]
    hotspots: tuple[TelemetryHotspot, ...]
    part_hotspots: tuple[TelemetryHotspot, ...]


def _percentile(values: Sequence[float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(float(value) for value in values)
    if len(ordered) == 1:
        return ordered[0]
    index = int(round((len(ordered) - 1) * max(0.0, min(1.0, float(fraction)))))
    return ordered[index]


def _as_record_dict(record: Any) -> Dict[str, Any]:
    if isinstance(record, dict):
        return dict(record)
    return {
        "timestamp": getattr(record, "timestamp", ""),
        "system": getattr(record, "system", ""),
        "point": getattr(record, "point", ""),
        "elapsed_ms": float(getattr(record, "elapsed_ms", 0.0)),
        "metadata": dict(getattr(record, "metadata", {}) or {}),
    }


def _build_hotspots(groups: Dict[str, List[float]], top_n: int) -> tuple[TelemetryHotspot, ...]:
    hotspots: List[TelemetryHotspot] = []
    for key, samples in groups.items():
        if not samples:
            continue
        total_ms = sum(samples)
        hotspots.append(
            TelemetryHotspot(
                key=key,
                count=len(samples),
                total_ms=total_ms,
                average_ms=mean(samples),
                max_ms=max(samples),
                p95_ms=_percentile(samples, 0.95),
            )
        )
    hotspots.sort(key=lambda item: (-item.total_ms, -item.p95_ms, -item.count, item.key))
    return tuple(hotspots[: max(1, int(top_n))])


def analyze_telemetry_records(records: Iterable[Any], *, top_n: int = 12) -> TelemetryAnalysis:
    by_point: Dict[str, List[float]] = {}
    by_part: Dict[str, List[float]] = {}
    systems: set[str] = set()
    sample_count = 0

    for raw_record in records:
        record = _as_record_dict(raw_record)
        system = str(record.get("system", "")).strip()
        point = str(record.get("point", "")).strip()
        if not system or not point:
            continue
        key = f"{system}.{point}"
        elapsed = max(0.0, float(record.get("elapsed_ms", 0.0)))
        systems.add(system)
        sample_count += 1
        by_point.setdefault(key, []).append(elapsed)

        metadata = dict(record.get("metadata", {}) or {})
        part_name = metadata.get("part_name")
        if isinstance(part_name, str) and part_name.strip():
            by_part.setdefault(str(part_name).strip(), []).append(elapsed)

    return TelemetryAnalysis(
        sample_count=sample_count,
        systems=tuple(sorted(systems)),
        hotspots=_build_hotspots(by_point, top_n),
        part_hotspots=_build_hotspots(by_part, top_n),
    )


def load_telemetry_log_file(path: str | Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            text = line.strip()
            if not text:
                continue
            payload = json.loads(text)
            if isinstance(payload, dict) and payload.get("type") == "sample":
                records.append(payload)
    return records


def analyze_telemetry_log_file(path: str | Path, *, top_n: int = 12) -> TelemetryAnalysis:
    return analyze_telemetry_records(load_telemetry_log_file(path), top_n=top_n)


def render_telemetry_report(
    analysis: TelemetryAnalysis,
    *,
    source: str,
    generated_at: datetime | None = None,
) -> str:
    created = generated_at or datetime.now()
    lines: list[str] = []
    lines.append("gui_do Telemetry Analysis Report")
    lines.append(f"Generated: {created.isoformat(timespec='seconds')}")
    lines.append(f"Source: {source}")
    lines.append(f"Sample count: {analysis.sample_count}")
    lines.append(f"Systems seen: {', '.join(analysis.systems) if analysis.systems else 'none'}")
    lines.append("")
    lines.append("High-Level Hotspots (ranked by total_ms):")
    if not analysis.hotspots:
        lines.append("- No telemetry samples were recorded.")
    else:
        for index, hotspot in enumerate(analysis.hotspots, start=1):
            lines.append(
                f"{index}. {hotspot.key} | total={hotspot.total_ms:.3f} ms | "
                f"avg={hotspot.average_ms:.3f} ms | p95={hotspot.p95_ms:.3f} ms | "
                f"max={hotspot.max_ms:.3f} ms | count={hotspot.count}"
            )

    lines.append("")
    lines.append("Part Hotspots:")
    if not analysis.part_hotspots:
        lines.append("- No per-part telemetry was detected.")
    else:
        for index, hotspot in enumerate(analysis.part_hotspots, start=1):
            lines.append(
                f"{index}. {hotspot.key} | total={hotspot.total_ms:.3f} ms | "
                f"avg={hotspot.average_ms:.3f} ms | p95={hotspot.p95_ms:.3f} ms | "
                f"max={hotspot.max_ms:.3f} ms | count={hotspot.count}"
            )

    lines.append("")
    lines.append("Detailed Guidance:")
    if analysis.hotspots:
        top = analysis.hotspots[0]
        lines.append(
            f"- Start with '{top.key}' because it has the highest cumulative latency."
        )
        if len(analysis.hotspots) > 1:
            second = analysis.hotspots[1]
            lines.append(
                f"- Next inspect '{second.key}' to reduce long-tail frame-time spikes."
            )
    else:
        lines.append("- Enable telemetry and run representative scenes to collect meaningful data.")

    return "\n".join(lines) + "\n"
