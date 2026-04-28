"""Localization — string table registry with reactive locale switching.

Register one :class:`StringTable` per locale and call :meth:`LocaleRegistry.t`
to look up display strings.  When the active locale changes all subscribers
are notified via an :class:`~gui_do.ObservableValue`.

Usage::

    from gui_do import StringTable, LocaleRegistry

    registry = LocaleRegistry(default_locale="en")
    registry.register(StringTable("en", {
        "app.title":       "My Application",
        "button.ok":       "OK",
        "button.cancel":   "Cancel",
    }))
    registry.register(StringTable("es", {
        "app.title":       "Mi Aplicación",
        "button.ok":       "Aceptar",
        "button.cancel":   "Cancelar",
    }))

    # Look up with active locale:
    label.text = registry.t("app.title")           # "My Application"

    # Switch locale:
    registry.set_locale("es")
    label.text = registry.t("app.title")           # "Mi Aplicación"

    # React to locale changes:
    registry.current_locale.subscribe(lambda _: refresh_ui())

    # Fallback to English when a key is missing in the active locale:
    label.text = registry.t("missing.key", fallback="Unknown")
"""
from __future__ import annotations

from typing import Dict, List, Optional

from .presentation_model import ObservableValue


# ---------------------------------------------------------------------------
# StringTable
# ---------------------------------------------------------------------------


class StringTable:
    """A flat key→text mapping for one locale.

    Parameters
    ----------
    locale_id:
        BCP-47 locale tag (e.g. ``"en"``, ``"fr"``, ``"zh-CN"``).
    entries:
        Mapping of string keys to translated text.
    """

    def __init__(self, locale_id: str, entries: Dict[str, str]) -> None:
        locale_id = str(locale_id).strip()
        if not locale_id:
            raise ValueError("locale_id must be a non-empty string")
        if not isinstance(entries, dict):
            raise TypeError("entries must be a dict")
        self._locale_id = locale_id
        self._entries: Dict[str, str] = {str(k): str(v) for k, v in entries.items()}

    @property
    def locale_id(self) -> str:
        return self._locale_id

    def get(self, key: str, fallback: str = "") -> str:
        """Return the translation for *key*, or *fallback* if not present."""
        return self._entries.get(str(key), fallback)

    def has(self, key: str) -> bool:
        """Return ``True`` when this table contains *key*."""
        return str(key) in self._entries

    def keys(self) -> List[str]:
        """Return a sorted list of all string keys in this table."""
        return sorted(self._entries.keys())

    def __len__(self) -> int:
        return len(self._entries)

    def __repr__(self) -> str:  # pragma: no cover
        return f"StringTable(locale_id={self._locale_id!r}, entries={len(self._entries)})"


# ---------------------------------------------------------------------------
# LocaleRegistry
# ---------------------------------------------------------------------------


class LocaleRegistry:
    """Multi-locale string look-up with reactive locale switching.

    Parameters
    ----------
    default_locale:
        The locale used for :meth:`t` when no *locale* argument is supplied.
        Must be registered via :meth:`register` before locale strings are
        looked up (though the registry will gracefully return the *fallback*
        string when the locale is not registered).
    fallback_locale:
        Secondary locale tried when a key is absent in the active locale.
        Commonly ``"en"``.  Pass ``None`` to disable fallback.
    """

    def __init__(
        self,
        default_locale: str = "en",
        *,
        fallback_locale: Optional[str] = None,
    ) -> None:
        self._tables: Dict[str, StringTable] = {}
        self.current_locale: ObservableValue[str] = ObservableValue(str(default_locale))
        self._fallback_locale: Optional[str] = fallback_locale

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(self, table: StringTable) -> None:
        """Register a :class:`StringTable`.

        Registering a second table for the same locale_id replaces the first.
        """
        if not isinstance(table, StringTable):
            raise TypeError("table must be a StringTable instance")
        self._tables[table.locale_id] = table

    # ------------------------------------------------------------------
    # Locale switching
    # ------------------------------------------------------------------

    def set_locale(self, locale_id: str) -> None:
        """Switch the active locale and notify all subscribers."""
        locale_id = str(locale_id).strip()
        self.current_locale.value = locale_id

    @property
    def active_locale(self) -> str:
        """The currently active locale id."""
        return self.current_locale.value

    @property
    def registered_locales(self) -> List[str]:
        """Sorted list of locale ids that have been registered."""
        return sorted(self._tables.keys())

    # ------------------------------------------------------------------
    # Look-up
    # ------------------------------------------------------------------

    def t(
        self,
        key: str,
        *,
        locale: Optional[str] = None,
        fallback: str = "",
    ) -> str:
        """Return the translated string for *key*.

        Look-up order:

        1. *locale* (if explicitly supplied), or ``current_locale.value``.
        2. ``fallback_locale`` (if set and different from the active locale).
        3. The *fallback* argument.

        Parameters
        ----------
        key:
            Dot-separated string key (e.g. ``"button.ok"``).
        locale:
            Override the active locale for this one look-up.
        fallback:
            String returned when the key is not found in any locale.
        """
        active = locale if locale is not None else self.current_locale.value
        table = self._tables.get(active)
        if table is not None and table.has(key):
            return table.get(key)

        # Fallback locale
        if (
            self._fallback_locale is not None
            and self._fallback_locale != active
        ):
            fb_table = self._tables.get(self._fallback_locale)
            if fb_table is not None and fb_table.has(key):
                return fb_table.get(key)

        return fallback

    def has(self, key: str, *, locale: Optional[str] = None) -> bool:
        """Return ``True`` when *key* exists in the given (or active) locale."""
        active = locale if locale is not None else self.current_locale.value
        table = self._tables.get(active)
        return table is not None and table.has(key)

    def __len__(self) -> int:
        """Return the number of registered locales."""
        return len(self._tables)
