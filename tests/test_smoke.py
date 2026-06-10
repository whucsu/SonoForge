"""Smoke tests for package bootstrap."""

from echo_personal_tool import __version__


def test_version_is_set() -> None:
    assert __version__ == "0.1.0"
