"""Pure NumPy/SciPy segmentation preprocessing and postprocessing."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from scipy import ndimage

from echo_personal_tool.domain.services.contour_geometry import resample_open_arc
from echo_personal_tool.domain.services.contour_geometry import smooth_open_arc

_NEIGHBOR_OFFSETS: tuple[tuple[int, int], ...] = (
    (1, 0),
    (1, 1),
    (0, 1),
    (-1, 1),
    (-1, 0),
    (-1, -1),
    (0, -1),
    (1, -1),
)


@dataclass(frozen=True)
class EchoNetCropTransform:
    """Maps 112×112 ONNX mask back to full-frame pixel coordinates."""

    frame_height: int
    frame_width: int
    crop_y0: int
    crop_x0: int
    crop_size: int


def resolve_echonet_roi_bounds(
    frame_shape: tuple[int, int],
    *,
    roi_xyxy: tuple[float, float, float, float] | None = None,
) -> tuple[int, int, int, int]:
    """B-mode ROI rectangle in pixel coords (y0, x0, y1, x1)."""
    height, width = frame_shape
    if roi_xyxy is None:
        return 0, 0, height, width

    x0f, y0f, x1f, y1f = roi_xyxy
    region_x0 = int(np.clip(round(x0f), 0, max(width - 1, 0)))
    region_y0 = int(np.clip(round(y0f), 0, max(height - 1, 0)))
    region_x1 = int(np.clip(round(x1f), region_x0 + 1, width))
    region_y1 = int(np.clip(round(y1f), region_y0 + 1, height))
    return region_y0, region_x0, region_y1, region_x1


def crop_frame_for_echonet(
    frame: np.ndarray,
    *,
    roi_xyxy: tuple[float, float, float, float] | None = None,
) -> tuple[np.ndarray, EchoNetCropTransform]:
    """Center square within B-mode ROI for EchoNet (resize to 112×112 in prepare_tensor)."""
    array = np.asarray(frame)
    height, width = array.shape[:2]
    y0, x0, y1, x1 = resolve_echonet_roi_bounds((height, width), roi_xyxy=roi_xyxy)
    region_height = y1 - y0
    region_width = x1 - x0
    crop_size = min(region_height, region_width)
    crop_y0 = y0 + (region_height - crop_size) // 2
    crop_x0 = x0 + (region_width - crop_size) // 2
    transform = EchoNetCropTransform(
        frame_height=height,
        frame_width=width,
        crop_y0=crop_y0,
        crop_x0=crop_x0,
        crop_size=crop_size,
    )
    return array[crop_y0 : crop_y0 + crop_size, crop_x0 : crop_x0 + crop_size], transform


def embed_echonet_mask(mask: np.ndarray, transform: EchoNetCropTransform) -> np.ndarray:
    """Place 112×112 ONNX mask into full-frame coordinates."""
    full = np.zeros((transform.frame_height, transform.frame_width), dtype=np.uint8)
    if transform.crop_size <= 0:
        return full

    array = np.asarray(mask)
    if array.ndim != 2 or array.size == 0:
        return full

    zoom = transform.crop_size / array.shape[0]
    upscaled = ndimage.zoom(array.astype(np.float32), (zoom, zoom), order=0)
    upscaled = (upscaled >= 0.5).astype(np.uint8)
    paste = min(transform.crop_size, upscaled.shape[0], upscaled.shape[1])
    y0, x0 = transform.crop_y0, transform.crop_x0
    full[y0 : y0 + paste, x0 : x0 + paste] = upscaled[:paste, :paste]
    return full


def prepare_tensor(frame: np.ndarray, *, target_size: int = 112) -> np.ndarray:
    """RGB/BGR or grayscale H×W → (1, 3, H, W) float32, per-frame mean/std norm."""
    array = np.asarray(frame, dtype=np.float32)
    if array.ndim == 2:
        resized = _resize_spatial(array, target_size=target_size)
        rgb = np.stack([resized, resized, resized], axis=-1)
    elif array.ndim == 3 and array.shape[2] == 3:
        resized = _resize_spatial(array, target_size=target_size)
        rgb = resized
    else:
        msg = "frame must be grayscale H×W or color H×W×3"
        raise ValueError(msg)

    normalized = _normalize_per_frame(rgb)
    chw = np.transpose(normalized, (2, 0, 1))
    return np.expand_dims(chw, axis=0).astype(np.float32, copy=False)


def logits_to_mask(logits: np.ndarray, threshold: float = 0.5) -> np.ndarray:
    """(1,1,h,w) or (h,w) logits → binary mask (h,w) uint8 {0,1}."""
    array = np.asarray(logits, dtype=np.float32)
    if array.ndim == 4:
        array = array[0, 0]
    elif array.ndim == 3:
        array = array[0]
    elif array.ndim != 2:
        msg = "logits must have shape (1, 1, h, w), (1, h, w), or (h, w)"
        raise ValueError(msg)

    if array.min() < 0.0 or array.max() > 1.0:
        array = 1.0 / (1.0 + np.exp(-np.clip(array, -50.0, 50.0)))

    return (array >= threshold).astype(np.uint8)


def papillary_mask_cleanup(
    mask: np.ndarray,
    *,
    long_axis_hint: tuple[tuple[float, float], tuple[float, float]] | None = None,
) -> np.ndarray:
    """Morphological closing along LV long axis to remove papillary notches."""
    del long_axis_hint  # v1: derive from mask bbox
    binary = np.asarray(mask) > 0
    if not binary.any():
        return np.zeros_like(binary, dtype=np.uint8)

    ys, xs = np.where(binary)
    top_y, bottom_y = int(ys.min()), int(ys.max())
    axis_length = float(bottom_y - top_y + 1)
    se_len = int(np.clip(0.04 * axis_length, 5, 15))

    cy, cx = se_len // 2, se_len // 2
    y, x = np.ogrid[:se_len, :se_len]
    ry = max(se_len // 2, 1)
    rx = max(se_len // 2, 1)
    structure = (
        ((y - cy) / ry) ** 2 + ((x - cx) / rx) ** 2 <= 1.0
    ).astype(np.uint8)

    closed = ndimage.binary_closing(binary, structure=structure)
    filled = ndimage.binary_fill_holes(closed)
    labeled, count = ndimage.label(filled)
    if count == 0:
        return filled.astype(np.uint8)
    counts = np.bincount(labeled.ravel())
    counts[0] = 0
    largest = int(np.argmax(counts))
    return (labeled == largest).astype(np.uint8)


def _signed_depth_to_chord(
    point: tuple[float, float],
    chord_start: tuple[float, float],
    chord_end: tuple[float, float],
    *,
    inward_reference: tuple[float, float],
) -> float:
    """Negative depth = point is on inward_reference side of chord (concavity)."""
    x0, y0 = point
    x1, y1 = chord_start
    x2, y2 = chord_end
    ref_cross = (x2 - x1) * (inward_reference[1] - y1) - (y2 - y1) * (inward_reference[0] - x1)
    sign = -1.0 if ref_cross >= 0.0 else 1.0
    numer = abs((y2 - y1) * x0 - (x2 - x1) * y0 + x2 * y1 - y2 * x1)
    denom = math.hypot(x2 - x1, y2 - y1)
    if denom == 0.0:
        return 0.0
    return sign * numer / denom


def _project_onto_segment(
    point: tuple[float, float],
    start: tuple[float, float],
    end: tuple[float, float],
) -> tuple[float, float]:
    sx, sy = start
    ex, ey = end
    px, py = point
    dx, dy = ex - sx, ey - sy
    denom = dx * dx + dy * dy
    if denom == 0.0:
        return start
    t = max(0.0, min(1.0, ((px - sx) * dx + (py - sy) * dy) / denom))
    return (sx + t * dx, sy + t * dy)


def exclude_papillary_concavities(
    open_points: list[tuple[float, float]],
    annulus: tuple[tuple[float, float], tuple[float, float]],
    apex: tuple[float, float],
    *,
    depth_threshold_ratio: float = 0.04,
    min_depth_px: float = 2.0,
) -> list[tuple[float, float]]:
    """Push interior nodes outward when concave vs MA–apex chord (ASE papillary rule)."""
    if len(open_points) < 3:
        return list(open_points)

    septal, lateral = annulus
    ma_mid = (
        (septal[0] + lateral[0]) / 2.0,
        (septal[1] + lateral[1]) / 2.0,
    )
    ma_len = math.hypot(lateral[0] - septal[0], lateral[1] - septal[1])
    threshold = max(min_depth_px, depth_threshold_ratio * ma_len)

    adjusted = [(float(x), float(y)) for x, y in open_points]
    for index in range(1, len(adjusted) - 1):
        depth = _signed_depth_to_chord(
            adjusted[index],
            ma_mid,
            apex,
            inward_reference=septal,
        )
        if depth < -threshold:
            adjusted[index] = _project_onto_segment(adjusted[index], ma_mid, apex)

    return smooth_open_arc(adjusted, annulus, apex=apex, iterations=4, blend=0.0)


def mask_to_contour(
    mask: np.ndarray,
    original_shape: tuple[int, int],
) -> list[tuple[float, float]]:
    """Largest connected component → closed polygon in original pixel coords."""
    binary = np.asarray(mask) > 0
    if not binary.any():
        return []

    labeled, component_count = ndimage.label(binary)
    if component_count == 0:
        return []

    counts = np.bincount(labeled.ravel())
    counts[0] = 0
    largest_label = int(np.argmax(counts))
    component = labeled == largest_label

    boundary = _trace_boundary(component)
    if len(boundary) < 3:
        return []

    mask_height, mask_width = binary.shape
    original_height, original_width = original_shape
    scale_x = original_width / mask_width
    scale_y = original_height / mask_height

    return [
        (x * scale_x, y * scale_y)
        for x, y in boundary
    ]


def smooth_contour(
    points: list[tuple[float, float]],
    *,
    num_nodes: int = 32,
) -> list[tuple[float, float]]:
    """Resample closed contour to num_nodes for spline editing."""
    if num_nodes <= 0:
        return []
    if not points:
        return []
    if len(points) == 1:
        return [points[0]] * num_nodes

    coords = np.asarray(points, dtype=np.float64)
    closed = np.vstack([coords, coords[0]])
    segments = np.diff(closed, axis=0)
    segment_lengths = np.linalg.norm(segments, axis=1)
    cumulative = np.concatenate([[0.0], np.cumsum(segment_lengths)])
    total_length = cumulative[-1]
    if total_length == 0.0:
        return [tuple(coords[0]) for _ in range(num_nodes)]

    targets = np.linspace(0.0, total_length, num_nodes, endpoint=False)
    resampled: list[tuple[float, float]] = []
    for target in targets:
        index = int(np.searchsorted(cumulative, target, side="right") - 1)
        index = min(index, len(coords) - 1)
        start_length = cumulative[index]
        end_length = cumulative[index + 1]
        if end_length > start_length:
            alpha = (target - start_length) / (end_length - start_length)
        else:
            alpha = 0.0
        start = coords[index]
        end = coords[(index + 1) % len(coords)]
        point = start + alpha * (end - start)
        resampled.append((float(point[0]), float(point[1])))
    return resampled


def _resize_spatial(array: np.ndarray, *, target_size: int) -> np.ndarray:
    height, width = array.shape[:2]
    if height == 0 or width == 0:
        msg = "frame must have non-zero height and width"
        raise ValueError(msg)

    zoom_y = target_size / height
    zoom_x = target_size / width
    if array.ndim == 2:
        return ndimage.zoom(array, (zoom_y, zoom_x), order=3)

    return ndimage.zoom(array, (zoom_y, zoom_x, 1.0), order=3)


def _normalize_per_frame(rgb: np.ndarray) -> np.ndarray:
    normalized = np.empty_like(rgb, dtype=np.float32)
    for channel in range(3):
        values = rgb[..., channel]
        mean = float(values.mean())
        std = float(values.std())
        if std > 0.0:
            normalized[..., channel] = (values - mean) / std
        else:
            normalized[..., channel] = values - mean
    return normalized


def _trace_boundary(component: np.ndarray) -> list[tuple[int, int]]:
    """Outer boundary of the largest filled component (x, y) pixel coords."""
    import cv2

    mask_uint8 = (np.asarray(component) > 0).astype(np.uint8) * 255
    if not mask_uint8.any():
        return []

    contours, _ = cv2.findContours(mask_uint8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not contours:
        return []

    largest = max(contours, key=cv2.contourArea)
    if len(largest) < 3:
        return []

    return [(int(point[0][0]), int(point[0][1])) for point in largest]


def _closest_boundary_index(
    boundary: list[tuple[float, float]],
    target: tuple[float, float],
) -> int:
    best_index = 0
    best_distance = float("inf")
    for index, point in enumerate(boundary):
        distance = (point[0] - target[0]) ** 2 + (point[1] - target[1]) ** 2
        if distance < best_distance:
            best_distance = distance
            best_index = index
    return best_index


def _walk_boundary(
    boundary: list[tuple[float, float]],
    start_index: int,
    end_index: int,
    *,
    step: int,
) -> list[tuple[float, float]]:
    if not boundary:
        return []
    path: list[tuple[float, float]] = []
    index = start_index
    for _ in range(len(boundary) + 1):
        path.append(boundary[index])
        if index == end_index:
            break
        index = (index + step) % len(boundary)
    return path


def _boundary_open_arc(
    boundary: list[tuple[float, float]],
    septal: tuple[float, float],
    lateral: tuple[float, float],
    apex: tuple[float, float],
) -> list[tuple[float, float]]:
    """Boundary segment from septal to lateral through the cavity (contains apex)."""
    if len(boundary) < 3:
        return [septal, lateral]

    septal_index = _closest_boundary_index(boundary, septal)
    lateral_index = _closest_boundary_index(boundary, lateral)
    forward = _walk_boundary(boundary, septal_index, lateral_index, step=1)
    backward = _walk_boundary(boundary, septal_index, lateral_index, step=-1)

    def _min_apex_distance(path: list[tuple[float, float]]) -> float:
        if not path:
            return float("inf")
        return min(math.hypot(point[0] - apex[0], point[1] - apex[1]) for point in path)

    chosen = forward if _min_apex_distance(forward) <= _min_apex_distance(backward) else backward
    if len(chosen) < 2:
        return [septal, *chosen, lateral]
    return chosen


def _band_horizontal_width(
    ys: np.ndarray,
    xs: np.ndarray,
    y_low: int,
    y_high: int,
) -> float:
    in_band = (ys >= y_low) & (ys <= y_high)
    if not np.any(in_band):
        return 0.0
    band_xs = xs[in_band]
    return float(np.max(band_xs) - np.min(band_xs))


def _annulus_and_apex_from_mask_pixels(
    ys: np.ndarray,
    xs: np.ndarray,
    *,
    y_min: int,
    y_max: int,
) -> tuple[tuple[float, float], tuple[float, float], tuple[float, float]]:
    """Annulus = wider cavity opening; apex = opposite narrow end (A4C)."""
    height = y_max - y_min + 1
    band_depth = max(3, int(round(0.12 * height)))
    apex_band = max(3, int(round(0.08 * height)))

    top_band = (y_min, y_min + band_depth)
    bottom_band = (y_max - band_depth, y_max)
    top_width = _band_horizontal_width(ys, xs, *top_band)
    bottom_width = _band_horizontal_width(ys, xs, *bottom_band)

    if bottom_width > top_width:
        annulus_mask = (ys >= bottom_band[0]) & (ys <= bottom_band[1])
        apex_mask = (ys >= y_min) & (ys <= y_min + apex_band)
        apex_y = float(y_min + apex_band / 2.0)
    else:
        annulus_mask = (ys >= top_band[0]) & (ys <= top_band[1])
        apex_mask = (ys >= y_max - apex_band) & (ys <= y_max)
        apex_y = float(y_max - apex_band / 2.0)

    ann_xs = xs[annulus_mask]
    ann_ys = ys[annulus_mask]
    if ann_xs.size < 2:
        msg = "cannot locate mitral annulus on cavity mask"
        raise ValueError(msg)

    septal = (float(np.min(ann_xs)), float(np.median(ann_ys)))
    lateral = (float(np.max(ann_xs)), float(np.median(ann_ys)))
    if np.any(apex_mask):
        apex = (float(np.median(xs[apex_mask])), float(np.median(ys[apex_mask])))
    else:
        apex = (float(np.median(xs)), apex_y)
    return septal, lateral, apex


def open_arc_from_cavity_mask(
    mask: np.ndarray,
    *,
    original_shape: tuple[int, int] | None = None,
    num_nodes: int = 32,
    view_hint: str = "A4C",
) -> tuple[
    list[tuple[float, float]],
    tuple[tuple[float, float], tuple[float, float]],
    tuple[float, float],
]:
    """Build A4C LV open arc: annulus = top opening of cavity mask, arc via apex side."""
    del view_hint
    binary = np.asarray(mask) > 0
    if not binary.any():
        msg = "empty cavity mask"
        raise ValueError(msg)

    labeled, component_count = ndimage.label(binary)
    if component_count == 0:
        msg = "empty cavity mask"
        raise ValueError(msg)

    counts = np.bincount(labeled.ravel())
    counts[0] = 0
    largest_label = int(np.argmax(counts))
    component = labeled == largest_label

    ys, xs = np.where(component)
    y_min = int(ys.min())
    y_max = int(ys.max())
    x_min = int(xs.min())
    x_max = int(xs.max())
    height = y_max - y_min + 1
    width = x_max - x_min + 1
    if height < 10 or width < 10:
        msg = "cavity mask bounding box too small"
        raise ValueError(msg)

    septal, lateral, apex = _annulus_and_apex_from_mask_pixels(ys, xs, y_min=y_min, y_max=y_max)
    annulus = (septal, lateral)

    frame_shape = original_shape or binary.shape[:2]
    boundary = mask_to_contour(component.astype(np.uint8), frame_shape)
    if len(boundary) < 4:
        msg = "cavity boundary too short"
        raise ValueError(msg)

    open_points = _boundary_open_arc(boundary, septal, lateral, apex)
    resampled = resample_open_arc(open_points, num_nodes=max(num_nodes, 4))
    if len(resampled) < 3:
        resampled = [septal, apex, lateral]
    resampled[0] = septal
    resampled[-1] = lateral
    return resampled, annulus, apex


def closed_polygon_to_open_arc(
    points: list[tuple[float, float]],
    *,
    view_hint: str = "A4C",
) -> tuple[list[tuple[float, float]], tuple[tuple[float, float], tuple[float, float]]]:
    """Convert closed AI polygon to open arc using longest chord as mitral annulus."""
    del view_hint
    if len(points) < 4:
        msg = "closed polygon must have at least 4 points"
        raise ValueError(msg)

    best_length = -1.0
    best_i = 0
    best_j = 1
    for i in range(len(points)):
        for j in range(i + 1, len(points)):
            dx = points[j][0] - points[i][0]
            dy = points[j][1] - points[i][1]
            length = dx * dx + dy * dy
            if length > best_length:
                best_length = length
                best_i, best_j = i, j

    septal = points[best_i]
    lateral = points[best_j]
    annulus = (septal, lateral)

    ordered: list[tuple[float, float]] = [septal]
    index = (best_i + 1) % len(points)
    while index != best_j:
        ordered.append(points[index])
        index = (index + 1) % len(points)
    ordered.append(lateral)
    return ordered, annulus


def _simplify_contour(contour: list[tuple[int, int]]) -> list[tuple[int, int]]:
    if len(contour) <= 2:
        return contour

    simplified: list[tuple[int, int]] = [contour[0]]
    for point in contour[1:]:
        if point != simplified[-1]:
            simplified.append(point)
    if len(simplified) > 2 and simplified[0] == simplified[-1]:
        simplified.pop()
    return simplified
