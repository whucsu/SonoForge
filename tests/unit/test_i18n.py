"""Tests for i18n locale loading and key parity."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from echo_personal_tool.domain.models import LinearMeasurement
from echo_personal_tool.domain.models.measurements import MeasurementSnapshot
from echo_personal_tool.domain.services.measurement_results_formatter import format_results_overlay
from echo_personal_tool.infrastructure.i18n import set_language, tr

_LOCALES_DIR = Path(__file__).resolve().parents[2] / "src" / "echo_personal_tool" / "infrastructure" / "locales"


def _load_locale(lang: str) -> dict[str, str]:
    path = _LOCALES_DIR / f"{lang}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return {k: v for k, v in data.items() if not k.startswith("_")}


def test_locale_key_parity() -> None:
    ru = _load_locale("ru")
    en = _load_locale("en")
    assert set(ru) == set(en)
    assert len(ru) > 0


def test_tr_substitution() -> None:
    set_language("en")
    text = tr("status.loading", name="study.dcm")
    assert "study.dcm" in text


def test_set_language_switches_linear_measurement_label() -> None:
    measurement = LinearMeasurement("IVSd", 10.0, 5.0)
    set_language("ru")
    assert "МЖП" in measurement.display_text()
    set_language("en")
    assert "IVSd" in measurement.display_text()


def test_overlay_rwt_respects_language() -> None:
    set_language("ru")
    ru_text = format_results_overlay(MeasurementSnapshot(rwt=0.42))
    set_language("en")
    en_text = format_results_overlay(MeasurementSnapshot(rwt=0.42))
    assert "ОТС" in ru_text
    assert "RWT" in en_text


@pytest.fixture(autouse=True)
def restore_russian() -> None:
    yield
    set_language("ru")
