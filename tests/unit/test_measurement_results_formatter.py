"""Tests for measurement overlay formatting."""

from __future__ import annotations

from echo_personal_tool.domain.models import LvViewMetrics
from echo_personal_tool.domain.models.measurements import ChamberSimpsonResult, MeasurementSnapshot
from echo_personal_tool.domain.services.measurement_results_formatter import (
    format_results_overlay,
)


def test_overlay_includes_rwt() -> None:
    text = format_results_overlay(MeasurementSnapshot(rwt=0.42))
    assert "ОТС: 0.42" in text


def test_overlay_includes_la_simpson_lav() -> None:
    snapshot = MeasurementSnapshot(
        spacing_calibrated=True,
        la_simpson=ChamberSimpsonResult(
            chamber="LA",
            a4c=LvViewMetrics(esv_ml=42.5),
            area_cm2=18.2,
        ),
    )
    text = format_results_overlay(snapshot)
    assert "ОЛП 4C: 42.5 mL" in text
    assert "S ЛП: 18.20 cm²" in text


def test_overlay_includes_ra_simpson_rav() -> None:
    snapshot = MeasurementSnapshot(
        spacing_calibrated=True,
        ra_simpson=ChamberSimpsonResult(
            chamber="RA",
            a4c=LvViewMetrics(esv_ml=35.0),
            area_cm2=15.0,
        ),
    )
    text = format_results_overlay(snapshot)
    assert "ОПП 4C: 35.0 mL" in text
    assert "S ПП: 15.00 cm²" in text
