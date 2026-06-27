"""Spatial and temporal spline smoothing for STE trajectories."""

from __future__ import annotations

import numpy as np
from scipy.interpolate import UnivariateSpline

from echo_personal_tool.domain.models.speckle import (
    SpeckleConfig,
    TrackingKernel,
    TrackingResult,
)


def _layer_groups(kernels: list[TrackingKernel]) -> dict[str, list[int]]:
    groups: dict[str, list[int]] = {}
    for i, kernel in enumerate(kernels):
        groups.setdefault(kernel.layer, []).append(i)
    return groups


def _fit_cubic_smoothing_spline(
    x: np.ndarray,
    y: np.ndarray,
    smoothing: float,
) -> UnivariateSpline:
    """Cubic smoothing spline; CubicSpline has no smoothing parameter ``s``."""
    return UnivariateSpline(x, y, s=max(float(smoothing), 0.0), k=3)


def interpolate_invalid_kernels(
    positions: np.ndarray,
    ncc_scores: np.ndarray,
    kernels: list[TrackingKernel],
    ncc_threshold: float = 0.3,
) -> np.ndarray:
    """Replace invalid kernel positions with interpolated values from valid neighbors.

    For each frame, if a kernel is invalid (NCC < threshold), interpolate its
    position from the nearest valid kernels along the contour.

    Args:
        positions: (n_frames, n_kernels, 2) kernel positions.
        ncc_scores: (n_frames, n_kernels) NCC scores.
        kernels: list of TrackingKernel with layer info.
        ncc_threshold: minimum NCC to consider a kernel valid.

    Returns:
        (n_frames, n_kernels, 2) interpolated positions.
    """
    out = positions.copy()
    n_frames, n_kernels, _ = out.shape

    groups = _layer_groups(kernels)
    for _layer, indices in groups.items():
        idx = sorted(indices, key=lambda i: kernels[i].node_index)
        n_layer = len(idx)
        if n_layer < 3:
            continue

        for t in range(n_frames):
            layer_ncc = ncc_scores[t, idx]
            valid = layer_ncc >= ncc_threshold

            if valid.all():
                continue

            valid_positions = out[t, idx[valid], :]
            valid_indices = np.where(valid)[0]

            if len(valid_indices) < 2:
                continue

            for j in range(n_layer):
                if valid[j]:
                    continue

                left_valid = valid_indices[valid_indices < j]
                right_valid = valid_indices[valid_indices > j]

                if len(left_valid) > 0 and len(right_valid) > 0:
                    li = left_valid[-1]
                    ri = right_valid[0]
                    dist_total = ri - li
                    if dist_total > 0:
                        alpha = (j - li) / dist_total
                        out[t, idx[j], :] = (
                            out[t, idx[li], :] * (1.0 - alpha) +
                            out[t, idx[ri], :] * alpha
                        )
                elif len(left_valid) > 0:
                    li = left_valid[-1]
                    out[t, idx[j], :] = out[t, idx[li], :]
                elif len(right_valid) > 0:
                    ri = right_valid[0]
                    out[t, idx[j], :] = out[t, idx[ri], :]

    return out


def smooth_trajectories(
    positions: np.ndarray,
    ncc_scores: np.ndarray,
    kernels: list[TrackingKernel],
    config: SpeckleConfig,
) -> np.ndarray:
    """Apply quality-weighted spatial then temporal smoothing."""
    out = positions.copy()
    n_frames, n_kernels, _ = out.shape
    if config.spatial_smoothing <= 0 and config.temporal_smoothing <= 0:
        return out

    groups = _layer_groups(kernels)
    for _layer, indices in groups.items():
        idx = sorted(indices, key=lambda i: kernels[i].node_index)
        if len(idx) < 4:
            continue
        if config.spatial_smoothing > 0:
            for t in range(n_frames):
                pts = out[t, idx, :]
                s = config.spatial_smoothing * len(idx)
                if config.quality_weighted_smoothing:
                    weights = np.clip(ncc_scores[t, idx], 0.01, 1.0)
                    s *= float(np.mean(1.0 - weights) + 0.1)
                t_param = np.arange(len(idx), dtype=np.float64)
                cs_x = _fit_cubic_smoothing_spline(t_param, pts[:, 0], s)
                cs_y = _fit_cubic_smoothing_spline(t_param, pts[:, 1], s)
                out[t, idx, 0] = cs_x(t_param)
                out[t, idx, 1] = cs_y(t_param)

    if config.temporal_smoothing > 0:
        times = np.arange(n_frames, dtype=np.float64)
        for i in range(n_kernels):
            s = config.temporal_smoothing * n_frames
            if config.quality_weighted_smoothing:
                s *= float(
                    np.mean(1.0 - np.clip(ncc_scores[:, i], 0.01, 1.0)) + 0.1
                )
            cs_x = _fit_cubic_smoothing_spline(times, out[:, i, 0], s)
            cs_y = _fit_cubic_smoothing_spline(times, out[:, i, 1], s)
            out[:, i, 0] = cs_x(times)
            out[:, i, 1] = cs_y(times)
    return out


def extract_trajectories(
    tracking_results: list[TrackingResult],
    initial_kernels: list[TrackingKernel],
    ed_index: int = 0,
) -> tuple[np.ndarray, np.ndarray]:
    """Build (n_frames, n_kernels, 2) positions and NCC matrix from results."""
    n_kernels = len(initial_kernels)
    n_frames = len(tracking_results) + 1
    positions = np.zeros((n_frames, n_kernels, 2), dtype=np.float64)
    ncc_matrix = np.zeros((n_frames, n_kernels), dtype=np.float64)

    positions[ed_index] = np.array(
        [kernel.center for kernel in initial_kernels],
        dtype=np.float64,
    )
    ncc_matrix[ed_index] = 1.0

    for result in tracking_results:
        frame = int(result.frame_index)
        positions[frame] = result.kernel_positions
        ncc_matrix[frame] = result.ncc_scores

    last_valid = positions[ed_index].copy()
    for t in range(n_frames):
        if t == ed_index:
            continue
        if np.allclose(positions[t], 0.0):
            positions[t] = last_valid
        else:
            last_valid = positions[t]

    return positions, ncc_matrix
