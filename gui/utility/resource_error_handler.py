import os
from .constants import GuiError


class DataResourceErrorHandler:
    @staticmethod
    def data_display_path(path: str) -> str:
        full_path = os.path.normpath(os.path.abspath(path))
        data_marker = f'{os.sep}data{os.sep}'
        lowered_path = full_path.lower()
        lowered_marker = data_marker.lower()
        marker_index = lowered_path.find(lowered_marker)
        if marker_index >= 0:
            return full_path[marker_index:]
        data_suffix = f'{os.sep}data'
        if lowered_path.endswith(data_suffix.lower()):
            return full_path[len(full_path) - len(data_suffix):]
        return full_path

    @staticmethod
    def raise_load_error(action: str, path: str, exc: Exception) -> None:
        raise GuiError(f'{action}: {DataResourceErrorHandler.data_display_path(path)}') from exc
