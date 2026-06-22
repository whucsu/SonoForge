"""Tests for generic planimeter area/volume."""

from __future__ import annotations

import pytest

from echo_personal_tool.domain.calculations.planimeter import (
    GENERIC_AREA_CHAMBER,
    GENERIC_VOLUME_CHAMBER,
    closed_polygon_area_cm2,
    closed_polygon_volume_ml,
    next_area_label,
    next_volume_label,
)
from echo_personal_tool.domain.models.contour import Contour
from echo_personal_tool.domain.services.planimeter_formatter import (
    planimeter_results_from_contours,
)


def _square_contour(size: float = 100.0) -> Contour:
    return Contour(
        phase="GEN",
        view="A4C",
        chamber=GENERIC_AREA_CHAMBER,
        points=[
            (0.0, 0.0),
            (size, 0.0),
            (size, size),
            (0.0, size),
        ],
        measurement_label="Площадь1",
    )


def test_next_labels_increment() -> None:
    contours = (
        Contour(chamber=GENERIC_AREA_CHAMBER, phase="GEN", view="A4C", measurement_label="Площадь1"),
        Contour(chamber=GENERIC_VOLUME_CHAMBER, phase="GEN", view="A4C", measurement_label="Объем1"),
    )
    assert next_area_label(contours) == "Площадь2"
    assert next_volume_label(contours) == "Объем2"


def test_closed_polygon_area_square() -> None:
    spacing = (0.5, 0.5)  # mm/px
    area_cm2 = closed_polygon_area_cm2(_square_contour(), spacing)
    assert area_cm2 is not None
    expected_cm2 = ((100.0 * 0.5) ** 2) / 100.0
    assert area_cm2 == pytest.approx(expected_cm2, rel=0.01)


def test_closed_polygon_volume() -> None:
    contour = Contour(
        phase="GEN",
        view="A4C",
        chamber=GENERIC_VOLUME_CHAMBER,
        points=[
            (0.0, 0.0),
            (100.0, 0.0),
            (100.0, 100.0),
            (0.0, 100.0),
        ],
        measurement_label="Объем1",
    )
    spacing = (0.5, 0.5)
    volume = closed_polygon_volume_ml(contour, spacing)
    assert volume is not None
    assert volume > 0.0


def test_planimeter_results_from_contours() -> None:
    results = planimeter_results_from_contours(
        (_square_contour(),),
        (0.5, 0.5),
        spacing_calibrated=True,
    )
    assert len(results) == 1
    assert results[0].label == "Площадь1"
    assert results[0].kind == "area"
    assert results[0].unit == "cm²"
    assert results[0].value > 0.0
