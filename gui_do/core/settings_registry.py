"""SettingsRegistry — namespaced, disk-backed reactive settings store."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .presentation_model import ObservableValue


class SettingDescriptor:
    """Metadata about a declared setting.

    This is returned by :meth:`SettingsRegistry.describe` and is useful for
    building settings UI (label, default, type hint, etc.).
    """

    __slots__ = ("namespace", "key", "default", "label")

    def __init__(self, namespace: str, key: str, default: Any, label: str = "") -> None:
        self.namespace = str(namespace)
        self.key = str(key)
        self.default = default
        self.label = str(label)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"SettingDescriptor(namespace={self.namespace!r}, key={self.key!r}, "
            f"default={self.default!r}, label={self.label!r})"
        )


class SettingsRegistry:
    """Named registry of typed settings, each backed by an :class:`ObservableValue`.

    Settings are grouped into *namespaces* (typically one per feature or
    subsystem).  Each setting has a default value and an optional human-readable
    label.  Changes to a setting fire all subscribers immediately.

    Persistence is optional: call :meth:`set_file_path` to enable JSON-backed
    load/save.  When a feature declares settings via
    :meth:`on_declare_settings <gui_do.Feature.on_declare_settings>` the
    registry is already populated with defaults; call :meth:`load` once after
    all features have mounted to restore persisted values.

    Usage::

        registry = SettingsRegistry("settings.json")
        volume = registry.declare("audio", "volume", default=1.0, label="Master Volume")
        volume.subscribe(lambda v: audio_backend.set_volume(v))

        registry.load()         # apply saved values
        registry.set_value("audio", "volume", 0.5)
        registry.save()
    """

    def __init__(self, file_path: "str | Path | None" = None) -> None:
        self._file_path: Optional[Path] = Path(file_path) if file_path is not None else None
        # namespace -> key -> ObservableValue
        self._values: Dict[str, Dict[str, ObservableValue[Any]]] = {}
        # namespace -> key -> SettingDescriptor
        self._descriptors: Dict[str, Dict[str, SettingDescriptor]] = {}

    # ------------------------------------------------------------------
    # Declaration
    # ------------------------------------------------------------------

    def declare(
        self,
        namespace: str,
        key: str,
        default: Any,
        *,
        label: str = "",
    ) -> ObservableValue[Any]:
        """Declare a setting and return its :class:`ObservableValue`.

        If the setting has already been declared (e.g., from a previous call),
        the existing observable is returned unchanged so that subscribers
        registered before re-mount are preserved.
        """
        ns = str(namespace).strip()
        k = str(key).strip()
        if not ns:
            raise ValueError("namespace must be a non-empty string")
        if not k:
            raise ValueError("key must be a non-empty string")

        descriptor = SettingDescriptor(ns, k, default, label)
        self._descriptors.setdefault(ns, {})[k] = descriptor

        ns_values = self._values.setdefault(ns, {})
        if k not in ns_values:
            ns_values[k] = ObservableValue(default)
        return ns_values[k]

    # ------------------------------------------------------------------
    # Read / write
    # ------------------------------------------------------------------

    def get(self, namespace: str, key: str) -> ObservableValue[Any]:
        """Return the :class:`ObservableValue` for a declared setting.

        Raises :class:`KeyError` if the setting has not been declared.
        """
        ns = str(namespace).strip()
        k = str(key).strip()
        try:
            return self._values[ns][k]
        except KeyError:
            raise KeyError(f"Setting not declared: {ns!r}/{k!r}") from None

    def get_value(self, namespace: str, key: str) -> Any:
        """Return the raw value of a declared setting."""
        return self.get(namespace, key).value

    def set_value(self, namespace: str, key: str, value: Any) -> None:
        """Update a declared setting, firing subscribers."""
        self.get(namespace, key).value = value

    # ------------------------------------------------------------------
    # Reset
    # ------------------------------------------------------------------

    def reset(self, namespace: str) -> None:
        """Revert all settings in *namespace* to their declared defaults."""
        ns = str(namespace).strip()
        defaults = self._descriptors.get(ns, {})
        ns_values = self._values.get(ns, {})
        for k, desc in defaults.items():
            if k in ns_values:
                ns_values[k].value = desc.default

    def reset_all(self) -> None:
        """Revert every declared setting to its default."""
        for ns in list(self._descriptors.keys()):
            self.reset(ns)

    # ------------------------------------------------------------------
    # Inspection
    # ------------------------------------------------------------------

    def namespaces(self) -> List[str]:
        """Return all declared namespaces, sorted."""
        return sorted(self._values.keys())

    def keys(self, namespace: str) -> List[str]:
        """Return all declared keys in *namespace*, sorted."""
        return sorted(self._values.get(str(namespace).strip(), {}).keys())

    def describe(self, namespace: str, key: str) -> Optional[SettingDescriptor]:
        """Return the :class:`SettingDescriptor` for a setting, or *None*."""
        return self._descriptors.get(str(namespace).strip(), {}).get(str(key).strip())

    def all_descriptors(self) -> List[SettingDescriptor]:
        """Return descriptors for every declared setting, ordered by namespace then key."""
        result: List[SettingDescriptor] = []
        for ns in sorted(self._descriptors.keys()):
            for k in sorted(self._descriptors[ns].keys()):
                result.append(self._descriptors[ns][k])
        return result

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def set_file_path(self, file_path: "str | Path") -> None:
        """Point the registry at a JSON file for load/save operations."""
        self._file_path = Path(file_path)

    @property
    def file_path(self) -> Optional[Path]:
        return self._file_path

    def save(self) -> bool:
        """Write all settings to disk.  Returns True on success."""
        if self._file_path is None:
            return False
        try:
            data: Dict[str, Any] = {
                ns: {k: ov.value for k, ov in entries.items()}
                for ns, entries in self._values.items()
            }
            self._file_path.parent.mkdir(parents=True, exist_ok=True)
            self._file_path.write_text(
                json.dumps(data, indent=2, default=str),
                encoding="utf-8",
            )
            return True
        except Exception:
            return False

    def load(self) -> bool:
        """Read settings from disk and fire subscribers.  Returns True on success.

        Only previously declared settings are updated; unknown keys in the file
        are silently ignored, so load is safe to call before declaring settings
        only for already-declared namespaces.
        """
        if self._file_path is None or not self._file_path.exists():
            return False
        try:
            data: Dict[str, Any] = json.loads(self._file_path.read_text(encoding="utf-8"))
        except Exception:
            return False
        for ns, entries in data.items():
            if not isinstance(entries, dict):
                continue
            ns_values = self._values.get(str(ns), {})
            for k, v in entries.items():
                if k in ns_values:
                    ns_values[k].value = v
        return True
