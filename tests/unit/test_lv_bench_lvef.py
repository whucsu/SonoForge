"""Unit tests for LVEF pairing helpers in the bench runner."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from echo_personal_tool.domain.models.contour import Contour
from echo_personal_tool.domain.services.bench_lvef_helpers import (
    compute_pair_lvef,
    gold_frame_to_contour,
    resolve_pixel_spacing,
)


# ---------------------------------------------------------------------------
# Tests: gold_frame_to_contour
# ---------------------------------------------------------------------------


def test_gold_frame_to_contour_builds_open_arc():
    gf = {
        "phase": "ED",
        "points": [[10, 20], [30, 40], [50, 20]],
        "mitral_annulus": [[10, 60], [50, 60]],
    }
    c = gold_frame_to_contour(gf)
    assert c.phase == "ed"
    assert c.mitral_annulus is not None
    assert len(c.points) == 3
    assert c.source == "gold"
    assert c.view == "A4C"
    assert c.chamber == "LV"


def test_gold_frame_to_contour_es_phase():
    gf = {
        "phase": "ES",
        "points": [[15, 25], [35, 45], [55, 25]],
        "mitral_annulus": [[15, 55], [55, 55]],
    }
    c = gold_frame_to_contour(gf)
    assert c.phase == "es"


def test_gold_frame_to_contour_no_annulus():
    gf = {
        "phase": "ED",
        "points": [[10, 20], [30, 40], [50, 20]],
    }
    c = gold_frame_to_contour(gf)
    assert c.mitral_annulus is None
    assert c.is_open_arc is False


# ---------------------------------------------------------------------------
# Tests: resolve_pixel_spacing
# ---------------------------------------------------------------------------


def test_resolve_pixel_spacing_from_gold():
    gold = {"pixel_spacing_mm": [0.5, 0.5]}
    result = resolve_pixel_spacing(gold, Path("/fake/instance.dcm"))
    assert result == (0.5, 0.5)


def test_resolve_pixel_spacing_gold_none_falls_back():
    gold = {}
    with patch(
        "echo_personal_tool.domain.services.bench_lvef_helpers.DicomReaderImpl"
    ) as MockReader:
        mock_meta = MagicMock()
        mock_meta.pixel_spacing = (0.4, 0.4)
        MockReader.return_value.read_metadata.return_value = mock_meta
        result = resolve_pixel_spacing(gold, Path("/fake/instance.dcm"))
    assert result == (0.4, 0.4)


def test_resolve_pixel_spacing_both_missing_returns_none():
    gold = {}
    with patch(
        "echo_personal_tool.domain.services.bench_lvef_helpers.DicomReaderImpl"
    ) as MockReader:
        mock_meta = MagicMock()
        mock_meta.pixel_spacing = None
        MockReader.return_value.read_metadata.return_value = mock_meta
        result = resolve_pixel_spacing(gold, Path("/fake/instance.dcm"))
    assert result is None


# ---------------------------------------------------------------------------
# Tests: compute_pair_lvef
# ---------------------------------------------------------------------------


def _make_contour(phase: str, points: list, ma: list | None = None) -> Contour:
    kwargs = {
        "phase": phase,
        "view": "A4C",
        "chamber": "LV",
        "points": points,
        "source": "test",
    }
    if ma:
        kwargs["mitral_annulus"] = (tuple(ma[0]), tuple(ma[1]))
    return Contour(**kwargs)


def test_compute_pair_lvef_returns_dict():
    ed_pts = [(10, 60), (20, 80), (30, 60)]
    es_pts = [(15, 60), (20, 70), (25, 60)]
    ma = [[5, 55], [35, 55]]

    auto_ed = _make_contour("ed", ed_pts, ma)
    auto_es = _make_contour("es", es_pts, ma)
    gold_ed = _make_contour("ed", ed_pts, ma)
    gold_es = _make_contour("es", es_pts, ma)

    result = compute_pair_lvef(auto_ed, auto_es, gold_ed, gold_es, (1.0, 1.0))

    assert "lvef_auto" in result
    assert "lvef_gold" in result
    assert "lvef_delta" in result
    # Same contours → delta should be 0
    assert result["lvef_delta"] == pytest.approx(0.0, abs=0.1)


def test_compute_pair_lvef_different_contours_gives_nonzero_delta():
    ed_pts = [(10, 60), (20, 80), (30, 60)]
    es_pts_auto = [(15, 60), (20, 70), (25, 60)]
    es_pts_gold = [(12, 60), (20, 75), (28, 60)]
    ma = [[5, 55], [35, 55]]

    auto_ed = _make_contour("ed", ed_pts, ma)
    auto_es = _make_contour("es", es_pts_auto, ma)
    gold_ed = _make_contour("ed", ed_pts, ma)
    gold_es = _make_contour("es", es_pts_gold, ma)

    result = compute_pair_lvef(auto_ed, auto_es, gold_ed, gold_es, (1.0, 1.0))

    assert result["lvef_delta"] is not None
    assert result["lvef_delta"] > 0.0


def test_compute_pair_lvef_missing_spacing_returns_skip():
    ed_pts = [(10, 60), (20, 80), (30, 60)]
    es_pts = [(15, 60), (20, 70), (25, 60)]
    ma = [[5, 55], [35, 55]]

    auto_ed = _make_contour("ed", ed_pts, ma)
    auto_es = _make_contour("es", es_pts, ma)
    gold_ed = _make_contour("ed", ed_pts, ma)
    gold_es = _make_contour("es", es_pts, ma)

    result = compute_pair_lvef(auto_ed, auto_es, gold_ed, gold_es, None)  # type: ignore[arg-type]

    assert result["lvef_auto"] is None
    assert result["lvef_gold"] is None
    assert result["lvef_delta"] is None
    assert result["lvef_skip_reason"] == "no_pixel_spacing"
