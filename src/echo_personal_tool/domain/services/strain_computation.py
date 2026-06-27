"""Strain computation from speckle tracking results."""

from __future__ import annotations

import numpy as np


def contour_arc_length(points: np.ndarray, pixel_spacing: tuple[float, float]) -> float:
    """Total arc length of a contour in physical units (mm)."""
    avg = np.mean(pixel_spacing)
    diffs = np.diff(points, axis=0)
    return float(np.sum(np.linalg.norm(diffs, axis=1)) * avg)


def compute_longitudinal_strain_gl(
    positions: np.ndarray,
    ed_index: int,
    pixel_spacing: tuple[float, float],
    endo_indices: list[int],
) -> np.ndarray:
    """Green-Lagrange longitudinal strain from smoothed kernel positions.

    E = 0.5 * ((L/L0)^2 - 1) * 100
    """
    n_frames = positions.shape[0]
    strain = np.zeros(n_frames)
    ed_pts = positions[ed_index, endo_indices, :]
    l0 = contour_arc_length(ed_pts, pixel_spacing)
    if l0 < 1e-6:
        return strain
    for t in range(n_frames):
        lt = contour_arc_length(positions[t, endo_indices, :], pixel_spacing)
        ratio = lt / l0
        strain[t] = 0.5 * (ratio**2 - 1.0) * 100.0
    return strain


def apply_drift_compensation(
    strain: np.ndarray, ed_index: int, end_index: int
) -> np.ndarray:
    """Linear detrend so strain[ed_index]=0 and strain[end_index]=0."""
    out = strain.copy()
    if len(out) < 2 or ed_index == end_index:
        return out
    end_idx = int(np.clip(end_index, 0, len(out) - 1))
    drift_slope = (out[end_idx] - out[ed_index]) / max(end_idx - ed_index, 1)
    for t in range(len(out)):
        out[t] -= drift_slope * (t - ed_index)
    out[ed_index] = 0.0
    return out


def compute_radial_strain_gl(
    positions: np.ndarray,
    ed_index: int,
    pixel_spacing: tuple[float, float],
    endo_indices: list[int],
    epi_indices: list[int],
) -> np.ndarray:
    """Green-Lagrange radial strain from mean wall thickness."""
    n_frames = positions.shape[0]
    strain = np.zeros(n_frames)
    avg_spacing = np.mean(pixel_spacing)

    endo_ed = positions[ed_index, endo_indices, :]
    epi_ed = positions[ed_index, epi_indices, :]
    t0 = float(np.mean(np.linalg.norm(epi_ed - endo_ed, axis=1)) * avg_spacing)
    if t0 < 1e-6:
        return strain

    for t in range(n_frames):
        endo_t = positions[t, endo_indices, :]
        epi_t = positions[t, epi_indices, :]
        tt = float(np.mean(np.linalg.norm(epi_t - endo_t, axis=1)) * avg_spacing)
        ratio = tt / t0
        strain[t] = 0.5 * (ratio**2 - 1.0) * 100.0
    return strain


def compute_gls(
    longitudinal_strain: np.ndarray,
    ed_index: int,
    es_index: int,
) -> float:
    """Global Longitudinal Strain: peak negative strain between ED and ES.

    Args:
        longitudinal_strain: strain curve over all frames.
        ed_index: end-diastole frame index.
        es_index: end-systole frame index.

    Returns:
        GLS as negative percentage (e.g., -18.5%).
    """
    if ed_index == es_index:
        return 0.0
    start, end = min(ed_index, es_index), max(ed_index, es_index)
    segment = longitudinal_strain[start : end + 1]
    if len(segment) == 0:
        return 0.0
    return float(np.min(segment))


def compute_strain_rate(
    strain_curve: np.ndarray,
    frame_times_ms: list[float] | np.ndarray,
) -> np.ndarray:
    """Time derivative of strain curve.

    Args:
        strain_curve: (N,) strain values in percent.
        frame_times_ms: per-frame time intervals in ms.

    Returns:
        (N,) strain rate in %/s.
    """
    n = len(strain_curve)
    rate = np.zeros(n)
    times = np.array(frame_times_ms, dtype=np.float64)
    if len(times) != n:
        times = np.full(n, 33.3)

    for i in range(1, n):
        dt_s = (times[i] - times[i - 1]) / 1000.0
        if dt_s > 1e-6:
            rate[i] = (strain_curve[i] - strain_curve[i - 1]) / dt_s

    return rate
