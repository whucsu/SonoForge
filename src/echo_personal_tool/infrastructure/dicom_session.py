"""Thread-local DICOM session: read bytes once, decode frames lazily/parallel."""

from __future__ import annotations

import logging
import struct
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO
from pathlib import Path

import cv2
import numpy as np
import pydicom

logger = logging.getLogger(__name__)

_thread_local = threading.local()

_UNCOMPRESSED_SYNTAXES = frozenset({
    "1.2.840.10008.1.2",
    "1.2.840.10008.1.2.1",
    "1.2.840.10008.1.2.2",
})

_ITEM_TAG = 0xE000FFFE
_DELIM_TAG = 0xE0DDFFFE
_MAX_DECODE_WORKERS = 4
_PIXEL_DATA_TAG = struct.pack("<HH", 0x7FE0, 0x0010)


def get_thread_dicom_session() -> DicomSession:
    session = getattr(_thread_local, "dicom_session", None)
    if session is None:
        session = DicomSession()
        _thread_local.dicom_session = session
    return session


def _extract_pixel_data_from_bytes(raw: bytes) -> bytes | None:
    """Scan raw DICOM bytes for PixelData tag and extract its value. No pydicom parse."""
    pos = 132  # skip 128-byte preamble + "DICM"
    while pos + 8 <= len(raw):
        tag = raw[pos : pos + 4]
        if tag == _PIXEL_DATA_TAG:
            vr_bytes = raw[pos + 4 : pos + 6]
            try:
                vr = vr_bytes.decode("ascii")
                is_explicit = all(c.isalpha() for c in vr) and vr in (
                    "OB", "OW", "OF", "SQ", "UC", "UN", "UR", "UT",
                )
            except Exception:
                is_explicit = False

            if is_explicit:
                if vr in ("OB", "OW", "OF", "SQ", "UC", "UN", "UR", "UT"):
                    length = struct.unpack_from("<I", raw, pos + 8)[0]
                    data_start = pos + 12
                else:
                    length = struct.unpack_from("<H", raw, pos + 6)[0]
                    data_start = pos + 8
            else:
                length = struct.unpack_from("<I", raw, pos + 4)[0]
                data_start = pos + 8
            return raw[data_start : data_start + length]

        group = struct.unpack_from("<H", raw, pos)[0]
        vr_bytes = raw[pos + 4 : pos + 6]
        try:
            vr = vr_bytes.decode("ascii")
            is_explicit = all(c.isalpha() for c in vr)
        except Exception:
            is_explicit = False

        if is_explicit and group != 0x7FE0:
            if vr in ("OB", "OW", "OF", "SQ", "UC", "UN", "UR", "UT"):
                length = struct.unpack_from("<I", raw, pos + 8)[0]
                data_start = pos + 12
            else:
                length = struct.unpack_from("<H", raw, pos + 6)[0]
                data_start = pos + 8
        else:
            length = struct.unpack_from("<I", raw, pos + 4)[0]
            data_start = pos + 8

        if length in (0xFFFFFFFF, 0x7FFFFFFF):
            break
        if length < 0 or length > len(raw):
            break
        pos = data_start + length
    return None


def _parse_encapsulated_fragments(pixel_data: bytes) -> list[bytes]:
    """Parse DICOM encapsulated pixel data, excluding the Basic Offset Table."""
    if len(pixel_data) < 8:
        return [pixel_data]

    fragments: list[bytes] = []
    first_item = True
    pos = 0

    while pos + 8 <= len(pixel_data):
        tag = struct.unpack_from("<I", pixel_data, pos)[0]
        length = struct.unpack_from("<I", pixel_data, pos + 4)[0]
        pos += 8

        if tag == _DELIM_TAG:
            break
        if tag != _ITEM_TAG:
            break
        if length == 0:
            continue

        data = pixel_data[pos : pos + length]
        if first_item and _is_bot(data, pixel_data):
            first_item = False
            pos += length
            continue
        first_item = False
        fragments.append(data)
        pos += length

    return fragments if fragments else [pixel_data]


def _is_bot(data: bytes, full_pixel_data: bytes) -> bool:
    """Heuristic: first item is BOT if it contains 4-byte offsets into pixel data."""
    if len(data) < 4 or len(data) % 4 != 0:
        return False
    num_entries = len(data) // 4
    if num_entries < 1:
        return False
    for i in range(min(num_entries, 4)):
        offset = struct.unpack_from("<I", data, i * 4)[0]
        if offset >= len(full_pixel_data):
            return False
    return True


def _decode_fragment_cv2(fragment: bytes, rows: int, cols: int) -> np.ndarray | None:
    """Try to decode a compressed fragment with cv2.imdecode."""
    try:
        buf = np.frombuffer(fragment, dtype=np.uint8)
        img = cv2.imdecode(buf, cv2.IMREAD_UNCHANGED)
        if img is None:
            return None
        if img.ndim == 3:
            if img.shape[2] == 4:
                img = img[..., :3]
            if img.shape[2] == 1:
                img = img[..., 0]
        if img.shape[:2] != (rows, cols):
            return None
        return img
    except Exception:
        return None


def _decode_uncompressed_frame(
    pixel_data: bytes, offset: int, size: int, rows: int, cols: int, bytes_per_pixel: int
) -> np.ndarray:
    """Decode a single uncompressed frame by slicing raw bytes."""
    raw = pixel_data[offset : offset + size]
    if bytes_per_pixel == 1:
        return np.frombuffer(raw, dtype=np.uint8).reshape(rows, cols).copy()
    if bytes_per_pixel == 2:
        return np.frombuffer(raw, dtype=np.uint16).reshape(rows, cols).copy()
    return np.frombuffer(raw, dtype=np.uint8).reshape(rows, cols, bytes_per_pixel).copy()


class DicomSession:
    def __init__(self) -> None:
        self._open_path: Path | None = None
        self._raw_bytes: bytes | None = None
        self._metadata: pydicom.Dataset | None = None
        self._frame_count: int = 0
        self._frames: np.ndarray | None = None
        self._is_uncompressed: bool = True
        self._frame_slices: list[tuple[int, int]] | None = None
        self._pixel_data_raw: bytes | None = None
        self._fragments: list[bytes] | None = None
        self._first_frame: np.ndarray | None = None

    @property
    def frame_count(self) -> int:
        if self._frames is not None:
            return int(self._frames.shape[0])
        return self._frame_count

    @property
    def is_decoded(self) -> bool:
        return self._frames is not None and self._frames.shape[0] == self._frame_count

    def open(self, path: Path | str) -> None:
        resolved = Path(path).resolve()
        if self._open_path == resolved and self._metadata is not None:
            return
        self.release()
        self._open_path = resolved
        self._raw_bytes = resolved.read_bytes()
        self._metadata = pydicom.dcmread(
            BytesIO(self._raw_bytes), stop_before_pixels=True, force=True
        )
        self._frame_count = int(getattr(self._metadata, "NumberOfFrames", 1))
        tsuid = str(
            getattr(self._metadata.file_meta, "TransferSyntaxUID", "1.2.840.10008.1.2.1")
        )
        self._is_uncompressed = tsuid in _UNCOMPRESSED_SYNTAXES
        if self._is_uncompressed:
            self._compute_frame_slices()

    def _compute_frame_slices(self) -> None:
        ds = self._metadata
        rows, cols = int(ds.Rows), int(ds.Columns)
        samples = int(getattr(ds, "SamplesPerPixel", 1))
        bytes_per_pixel = (int(ds.BitsAllocated) // 8) * samples
        frame_size = rows * cols * bytes_per_pixel
        self._frame_slices = [
            (i * frame_size, frame_size) for i in range(self._frame_count)
        ]

    def _ensure_pixel_data(self) -> None:
        """Load raw pixel data bytes, avoiding a second pydicom parse when possible."""
        if self._pixel_data_raw is not None:
            return
        extracted = _extract_pixel_data_from_bytes(self._raw_bytes)
        if extracted is not None:
            self._pixel_data_raw = extracted
        else:
            full_ds = pydicom.dcmread(BytesIO(self._raw_bytes), force=True)
            self._pixel_data_raw = bytes(full_ds.PixelData)
        if not self._is_uncompressed:
            self._fragments = _parse_encapsulated_fragments(self._pixel_data_raw)

    def decode_first_frame(self) -> np.ndarray:
        """Decode only the first frame for fast initial display."""
        if self._open_path is None:
            raise RuntimeError("DICOM is not open; call open() first")
        self._ensure_pixel_data()
        frame = self._decode_single_frame(0)
        self._first_frame = np.ascontiguousarray(frame)
        return self._first_frame

    def decode_all_frames(self) -> np.ndarray:
        """Decode all frames, returning the full (N,H,W) or (N,H,W,C) array."""
        if self._open_path is None:
            raise RuntimeError("DICOM is not open; call open() first")
        if self._frames is not None and self._frames.shape[0] == self._frame_count:
            return self._frames

        self._ensure_pixel_data()

        first_frame = getattr(self, "_first_frame", None)
        if first_frame is None:
            first_frame = self._decode_single_frame(0)
        self._frames = np.empty(
            (self._frame_count,) + first_frame.shape, dtype=first_frame.dtype
        )
        self._frames[0] = first_frame

        remaining = list(range(1, self._frame_count))
        if not remaining:
            return self._frames

        max_workers = min(len(remaining), _MAX_DECODE_WORKERS)
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = {
                pool.submit(self._decode_single_frame, i): i for i in remaining
            }
            for future in as_completed(futures):
                idx = futures[future]
                self._frames[idx] = future.result()

        return self._frames

    def _decode_single_frame(self, index: int) -> np.ndarray:
        ds = self._metadata
        rows, cols = int(ds.Rows), int(ds.Columns)

        if self._is_uncompressed and self._frame_slices is not None:
            samples = int(getattr(ds, "SamplesPerPixel", 1))
            bytes_per_pixel = (int(ds.BitsAllocated) // 8) * samples
            offset, size = self._frame_slices[index]
            return _decode_uncompressed_frame(
                self._pixel_data_raw, offset, size, rows, cols, bytes_per_pixel
            )

        if self._fragments is not None and index < len(self._fragments):
            decoded = _decode_fragment_cv2(self._fragments[index], rows, cols)
            if decoded is not None:
                return decoded

        return self._decode_pydicom_fallback(index)

    def _decode_pydicom_fallback(self, index: int) -> np.ndarray:
        """Fallback: full pydicom decode, extract frame index."""
        full_ds = pydicom.dcmread(BytesIO(self._raw_bytes), force=True)
        pixel_array = full_ds.pixel_array
        frames = stack_pixel_array(pixel_array)
        return np.ascontiguousarray(frames[index])

    def read_frame(self, frame_index: int) -> np.ndarray:
        if self._frames is None:
            raise RuntimeError("Frames not decoded; call decode_all_frames() first")
        if frame_index < 0 or frame_index >= self._frames.shape[0]:
            raise IndexError(
                f"Frame index {frame_index} out of range [0, {self._frames.shape[0]})"
            )
        return np.ascontiguousarray(self._frames[frame_index]).copy()

    def release(self) -> None:
        self._open_path = None
        self._raw_bytes = None
        self._metadata = None
        self._frame_count = 0
        self._frames = None
        self._frame_slices = None
        self._pixel_data_raw = None
        self._fragments = None
        self._first_frame = None


def stack_pixel_array(pixel_array: np.ndarray) -> np.ndarray:
    """Normalize pydicom pixel_array to shape (N,H,W) or (N,H,W,C)."""
    arr = np.asarray(pixel_array)
    if arr.ndim == 2:
        return np.ascontiguousarray(arr[np.newaxis, ...])
    if arr.ndim == 3:
        if arr.shape[-1] in (3, 4):
            frames = arr[np.newaxis, ...]
        else:
            frames = arr
    elif arr.ndim == 4:
        frames = arr
    else:
        raise ValueError(f"Unsupported pixel_array ndim: {arr.ndim}")

    if frames.ndim == 4 and frames.shape[-1] == 4:
        frames = frames[..., :3]
    if frames.ndim == 4 and frames.shape[-1] not in (3,):
        raise ValueError(f"Expected color channels last in {frames.shape}")
    if frames.ndim not in (3, 4):
        raise ValueError(
            f"Expected (N,H,W) or (N,H,W,C) after normalization, got {frames.shape}"
        )
    return np.ascontiguousarray(frames)
