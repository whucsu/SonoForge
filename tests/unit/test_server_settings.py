"""Tests for Orthanc server settings persistence."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from PySide6.QtCore import QSettings

from echo_personal_tool.infrastructure import server_settings as ss
from echo_personal_tool.infrastructure.server_settings import (
    ServerSettings,
    load_server_settings,
    save_server_settings,
)


@pytest.fixture
def isolated_settings(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    org = "echo-personal-tool-test"
    app = "server-test"
    monkeypatch.setattr(ss, "_SETTINGS_ORG", org)
    monkeypatch.setattr(ss, "_SETTINGS_APP", app)
    store = QSettings(org, app)
    store.clear()
    store.sync()
    yield
    store.clear()
    store.sync()


def test_load_defaults(isolated_settings: None) -> None:
    settings = load_server_settings()
    assert settings.url == "http://127.0.0.1:8042"
    assert settings.username == ""
    assert settings.password == ""
    assert settings.use_mock is True


def test_save_and_load_roundtrip(isolated_settings: None) -> None:
    original = ServerSettings(
        url="http://orthanc:8042",
        username="user",
        password="secret",
        use_mock=False,
    )
    save_server_settings(original)
    assert load_server_settings() == original
