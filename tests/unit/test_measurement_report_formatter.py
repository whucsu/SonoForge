"""Tests for study measurement report formatting."""

from __future__ import annotations

from echo_personal_tool.domain.models import LinearMeasurement, MeasurementSnapshot
from echo_personal_tool.domain.services.measurement_report_formatter import (
    dedupe_linear_measurements_latest,
    format_measurement_report,
)


def test_report_dedupes_linear_by_latest_label() -> None:
    measurements = (
        LinearMeasurement(label="LVEDD", pixel_length=100.0, millimeter_length=48.0),
        LinearMeasurement(label="LVEDD", pixel_length=110.0, millimeter_length=52.0),
        LinearMeasurement(label="IVSd", pixel_length=50.0, millimeter_length=9.0),
    )
    deduped = dedupe_linear_measurements_latest(measurements)
    assert len(deduped) == 2
    lvedd = next(item for item in deduped if item.label == "LVEDD")
    assert lvedd.millimeter_length == 52.0


def test_report_includes_deduped_linear_once() -> None:
    snapshot = MeasurementSnapshot(
        linear_measurements=(
            LinearMeasurement(label="LVEDD", pixel_length=100.0, millimeter_length=48.0),
            LinearMeasurement(label="LVEDD", pixel_length=110.0, millimeter_length=52.0),
        ),
    )
    text = format_measurement_report(snapshot)
    assert text.count("КДР ЛЖ") == 1
    assert "52.0 mm" in text


def test_report_empty_snapshot() -> None:
    assert format_measurement_report(None) == "Нет измерений."
