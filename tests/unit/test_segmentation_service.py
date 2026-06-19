"""Unit tests for segmentation preprocessing and postprocessing."""

from __future__ import annotations

import math

import numpy as np
import pytest

from echo_personal_tool.domain.services.segmentation_service import (
    closed_polygon_to_open_arc,
    exclude_papillary_concavities,
    logits_to_mask,
    mask_to_contour,
    papillary_mask_cleanup,
    prepare_tensor,
    smooth_contour,
)


def _circle_mask(
    *,
    height: int,
    width: int,
    center_y: float,
    center_x: float,
    radius: float,
) -> np.ndarray:
    ys, xs = np.ogrid[:height, :width]
    distance = (ys - center_y) ** 2 + (xs - center_x) ** 2
    return (distance <= radius**2).astype(np.uint8)


def _polygon_area(points: list[tuple[float, float]]) -> float:
    if len(points) < 3:
        return 0.0
    area = 0.0
    for index, (x1, y1) in enumerate(points):
        x2, y2 = points[(index + 1) % len(points)]
        area += x1 * y2 - x2 * y1
    return abs(area) / 2.0


def test_prepare_tensor_grayscale_shape_and_dtype() -> None:
    frame = np.full((64, 48), 128, dtype=np.uint8)

    tensor = prepare_tensor(frame, target_size=112)

    assert tensor.shape == (1, 3, 112, 112)
    assert tensor.dtype == np.float32


def test_prepare_tensor_rgb_shape_and_dtype() -> None:
    frame = np.zeros((80, 60, 3), dtype=np.uint8)
    frame[:, :, 0] = 200
    frame[:, :, 1] = 100
    frame[:, :, 2] = 50

    tensor = prepare_tensor(frame, target_size=112)

    assert tensor.shape == (1, 3, 112, 112)
    assert tensor.dtype == np.float32


def test_prepare_tensor_per_frame_normalization() -> None:
    frame = np.zeros((32, 32, 3), dtype=np.uint8)
    frame[:, :, 0] = 10
    frame[:, :, 1] = 20
    frame[:, :, 2] = 30

    tensor = prepare_tensor(frame, target_size=32)

    for channel in range(3):
        values = tensor[0, channel]
        assert values.mean() == pytest.approx(0.0, abs=1e-5)
        assert values.std() == pytest.approx(0.0, abs=1e-5)


def test_logits_to_mask_from_logits() -> None:
    logits = np.array([[[[-2.0, -0.1, 2.0]]]], dtype=np.float32)

    mask = logits_to_mask(logits)

    assert mask.shape == (1, 3)
    assert mask.dtype == np.uint8
    assert set(np.unique(mask)).issubset({0, 1})
    assert mask[0, 0] == 0
    assert mask[0, 1] == 0
    assert mask[0, 2] == 1


def test_logits_to_mask_from_probabilities() -> None:
    probabilities = np.array([[0.2, 0.8], [0.6, 0.4]], dtype=np.float32)

    mask = logits_to_mask(probabilities, threshold=0.5)

    assert mask.shape == (2, 2)
    assert mask.tolist() == [[0, 1], [1, 0]]


def test_mask_to_contour_circle_area_scales_to_original_shape() -> None:
    mask_size = 64
    radius = 20.0
    mask = _circle_mask(
        height=mask_size,
        width=mask_size,
        center_y=mask_size / 2,
        center_x=mask_size / 2,
        radius=radius,
    )
    original_shape = (128, 128)
    scale = original_shape[0] / mask_size

    contour = mask_to_contour(mask, original_shape)

    assert len(contour) >= 3
    expected_area = math.pi * (radius * scale) ** 2
    assert _polygon_area(contour) == pytest.approx(expected_area, rel=0.05)


def test_smooth_contour_returns_requested_node_count() -> None:
    square = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]

    resampled = smooth_contour(square, num_nodes=32)

    assert len(resampled) == 32
    assert all(len(point) == 2 for point in resampled)


def test_closed_polygon_to_open_arc_uses_longest_chord() -> None:
    polygon = [(0.0, 0.0), (100.0, 0.0), (70.0, 70.0), (30.0, 70.0)]
    arc, annulus = closed_polygon_to_open_arc(polygon)
    assert len(arc) >= 2
    assert arc[0] == annulus[0]
    assert arc[-1] == annulus[1]


def _mask_with_mid_notch(height: int = 64, width: int = 48) -> np.ndarray:
    mask = np.zeros((height, width), dtype=np.uint8)
    mask[8:56, 12:36] = 1
    mask[28:40, 20:28] = 0  # papillary-like notch
    return mask


def test_papillary_mask_cleanup_fills_mid_notch() -> None:
    mask = _mask_with_mid_notch()
    cleaned = papillary_mask_cleanup(mask)
    assert cleaned[32, 24] == 1
    assert cleaned.sum() >= mask.sum()


def test_papillary_mask_cleanup_preserves_largest_component() -> None:
    mask = _mask_with_mid_notch()
    mask[2:6, 2:6] = 1  # speckle
    cleaned = papillary_mask_cleanup(mask)
    assert cleaned[2:6, 2:6].sum() == 0


def _arc_with_inward_bump() -> tuple[list[tuple[float, float]], tuple, tuple]:
    annulus = ((0.0, 0.0), (100.0, 0.0))
    apex = (50.0, 80.0)
    points = [
        annulus[0],
        (25.0, 40.0),
        (50.0, 55.0),  # inward bump (papillary)
        (75.0, 40.0),
        annulus[1],
    ]
    return points, annulus, apex


def test_exclude_papillary_concavities_raises_mid_cavity_bump() -> None:
    points, annulus, apex = _arc_with_inward_bump()
    result = exclude_papillary_concavities(points, annulus, apex)
    assert result[0] == annulus[0]
    assert result[-1] == annulus[1]
    mid_y = result[2][1]
    assert mid_y >= 55.0 - 2.0  # bumped outward toward chord


def test_exclude_papillary_concavities_leaves_smooth_arc_unchanged() -> None:
    annulus = ((0.0, 0.0), (100.0, 0.0))
    apex = (50.0, 80.0)
    points = [annulus[0], (50.0, 70.0), annulus[1]]
    result = exclude_papillary_concavities(points, annulus, apex)
    assert result[1][1] == pytest.approx(70.0, abs=2.0)

