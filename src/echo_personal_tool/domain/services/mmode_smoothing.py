"""Smart M-mode smoothing: contrast enhancement, spatial Gaussian, temporal EMA."""

from __future__ import annotations

import numpy as np
from scipy.ndimage import gaussian_filter1d


def enhance_contrast(column: np.ndarray, clip_pct: float = 1.0) -> np.ndarray:
    """Percentile-based contrast stretching.

    Maps [p_low, p_high] → [0, 255], clipping outliers.
    Preserves original brightness relationships while maximizing contrast.
    """
    f32 = column.astype(np.float32)
    p_low = np.percentile(f32, clip_pct)
    p_high = np.percentile(f32, 100.0 - clip_pct)
    if p_high - p_low < 1.0:
        return column
    stretched = (f32 - p_low) / (p_high - p_low) * 255.0
    return np.clip(stretched, 0, 255).astype(np.uint8)


def adjust_brightness(column: np.ndarray, shift: int = -15) -> np.ndarray:
    """Shift brightness. Negative values darken the image."""
    f32 = column.astype(np.float32) + shift
    return np.clip(f32, 0, 255).astype(np.uint8)


def gamma_correct(column: np.ndarray, gamma: float = 1.3) -> np.ndarray:
    """Apply gamma correction. gamma > 1 darkens shadows (chambers darker)."""
    f32 = column.astype(np.float32) / 255.0
    corrected = np.power(f32, gamma) * 255.0
    return np.clip(corrected, 0, 255).astype(np.uint8)


def spatial_smooth(column: np.ndarray, sigma: float = 1.0) -> np.ndarray:
    """1D Gaussian smoothing along depth (axis=0) to remove pixel jaggedness.

    sigma=1.0 gives stronger smoothing than 0.8.
    """
    return gaussian_filter1d(column.astype(np.float32), sigma=sigma, axis=0, mode="nearest")


def temporal_smooth(
    current: np.ndarray,
    previous: np.ndarray | None,
    alpha: float = 0.3,
) -> np.ndarray:
    """Exponential moving average between consecutive frames.

    alpha=0.0 → no change, alpha=1.0 → fully current.
    0.3 gives smooth result while tracking motion.
    """
    if previous is None:
        return current
    return (alpha * current + (1.0 - alpha) * previous).astype(current.dtype)
