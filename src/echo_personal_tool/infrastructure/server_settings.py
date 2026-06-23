"""Persistent Orthanc server connection settings."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QSettings

_SETTINGS_ORG = "echo-personal-tool"
_SETTINGS_APP = "server"

_DEFAULT_URL = "http://127.0.0.1:8042"
_DEFAULT_USE_MOCK = True


@dataclass
class ServerSettings:
    url: str
    username: str
    password: str
    use_mock: bool


def _settings_store() -> QSettings:
    return QSettings(_SETTINGS_ORG, _SETTINGS_APP)


def _read_bool(value: object, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes")
    return bool(value)


def load_server_settings() -> ServerSettings:
    store = _settings_store()
    return ServerSettings(
        url=str(store.value("url", _DEFAULT_URL)),
        username=str(store.value("username", "")),
        password=str(store.value("password", "")),
        use_mock=_read_bool(store.value("use_mock"), _DEFAULT_USE_MOCK),
    )


def save_server_settings(settings: ServerSettings) -> None:
    store = _settings_store()
    store.setValue("url", settings.url)
    store.setValue("username", settings.username)
    store.setValue("password", settings.password)
    store.setValue("use_mock", settings.use_mock)
    store.sync()
