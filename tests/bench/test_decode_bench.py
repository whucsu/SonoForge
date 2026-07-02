"""Decode / cache benchmarks.

Measures: single frame decode, parallel batch, eviction cost, zero-copy vs copy.

Run:  ECHO_BENCH=1 pytest tests/bench/test_decode_bench.py -v --benchmark-only
"""

from __future__ import annotations

import os
import struct
from io import BytesIO
from pathlib import Path

import numpy as np
import pytest

from echo_personal_tool.application.frame_cache import FrameCache
from echo_personal_tool.infrastructure.dicom_session import _decode_uncompressed_frame

_BENCH = pytest.mark.skipif(
    os.environ.get("ECHO_BENCH", "") != "1",
    reason="Set ECHO_BENCH=1 to run benchmarks",
)


# ── Uncompressed decode: zero-copy vs copy ──────────────────────────

def _make_raw_pixel_data(rows: int, cols: int, bpp: int, n_frames: int) -> bytes:
    """Create synthetic uncompressed DICOM pixel data."""
    frame_bytes = rows * cols * bpp
    return bytes(n_frames * frame_bytes)


@_BENCH
def test_bench_decode_uncompressed_zero_copy(benchmark) -> None:
    """np.frombuffer view without .copy() — zero-copy path."""
    rows, cols, bpp = 256, 256, 2
    raw = _make_raw_pixel_data(rows, cols, bpp, n_frames=10)
    offsets = [(i * rows * cols * bpp, rows * cols * bpp) for i in range(10)]

    def _decode_all() -> None:
        for offset, size in offsets:
            _ = _decode_uncompressed_frame(raw, offset, size, rows, cols, bpp)

    benchmark(_decode_all)


@_BENCH
def test_bench_decode_uncompressed_with_copy(benchmark) -> None:
    """np.frombuffer + .copy() — old path for comparison."""
    rows, cols, bpp = 256, 256, 2
    raw = _make_raw_pixel_data(rows, cols, bpp, n_frames=10)
    offsets = [(i * rows * cols * bpp, rows * cols * bpp) for i in range(10)]

    def _decode_all_copy() -> None:
        for offset, size in offsets:
            chunk = raw[offset : offset + size]
            _ = np.frombuffer(chunk, dtype=np.uint16).reshape(rows, cols).copy()

    benchmark(_decode_all_copy)


# ── FrameCache eviction cost ────────────────────────────────────────

@_BENCH
def test_bench_evict_200_frames_sweep(benchmark, tmp_path: Path) -> None:
    """set_current() sweep over 200-frame cache — measures _evict() cost."""
    n = 200
    frames = np.arange(n * 8 * 8, dtype=np.uint16).reshape(n, 8, 8)
    cache = FrameCache(evict_window=20)
    cache.load(tmp_path / "c.dcm", frames)

    def _sweep() -> None:
        for i in range(0, n, 10):
            cache.set_current(i)

    benchmark(_sweep)


@_BENCH
def test_bench_evict_with_pinned_frames(benchmark, tmp_path: Path) -> None:
    """Eviction with 5 pinned frames — tests pin guard overhead."""
    n = 100
    frames = np.arange(n * 8 * 8, dtype=np.uint16).reshape(n, 8, 8)
    cache = FrameCache(evict_window=20)
    cache.load(tmp_path / "c.dcm", frames)
    for i in range(0, n, 20):
        cache.pin(i)

    def _sweep_pinned() -> None:
        for i in range(0, n, 5):
            cache.set_current(i)

    benchmark(_sweep_pinned)


# ── FrameCache.frames property (memoized) ───────────────────────────

@_BENCH
def test_bench_frames_property_first_call(benchmark, tmp_path: Path) -> None:
    """First .frames call — triggers np.stack reconstruction."""
    n = 60
    frames = np.arange(n * 16 * 16, dtype=np.uint16).reshape(n, 16, 16)
    cache = FrameCache(evict_window=40)
    cache.load(tmp_path / "c.dcm", frames)

    def _rebuild() -> None:
        cache._cached_frames = None  # force rebuild
        _ = cache.frames

    benchmark(_rebuild)


@_BENCH
def test_bench_frames_property_cached(benchmark, tmp_path: Path) -> None:
    """Subsequent .frames calls — should return cached result."""
    n = 60
    frames = np.arange(n * 16 * 16, dtype=np.uint16).reshape(n, 16, 16)
    cache = FrameCache(evict_window=40)
    cache.load(tmp_path / "c.dcm", frames)
    _ = cache.frames  # prime cache

    def _cached_call() -> None:
        _ = cache.frames

    benchmark(_cached_call)


# ── bisect vs linear eviction ───────────────────────────────────────

@_BENCH
def test_bench_sorted_keys_eviction_logic(benchmark, tmp_path: Path) -> None:
    """Sorted keys + bisect eviction — the optimized path."""
    n = 500
    frames = np.arange(n * 4 * 4, dtype=np.uint8).reshape(n, 4, 4)
    cache = FrameCache(evict_window=30)
    cache.load(tmp_path / "c.dcm", frames)

    def _evict_many() -> None:
        for i in range(0, n, 5):
            cache.set_current(i)

    benchmark(_evict_many)
