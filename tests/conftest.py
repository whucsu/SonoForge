"""Pytest configuration."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


import pytest


@pytest.fixture(autouse=True)
def _ru_locale():
    """Reset language to Russian before each test."""
    from echo_personal_tool.infrastructure.i18n import set_language

    set_language("ru")
    yield
    set_language("ru")
