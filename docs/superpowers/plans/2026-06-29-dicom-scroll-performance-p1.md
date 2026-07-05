# DICOM Scroll Performance P1 — BOT / Fragment Index

**Goal:** O(1) random access to compressed multiframe JPEG via Basic Offset Table, without `pixel_array` full-cine fallback.

**Approach:** Use `pydicom.encaps.generate_frames()` to build per-frame compressed byte blobs once; decode single frame with `cv2.imdecode`.

**Files:**
- `infrastructure/dicom_session.py` — encapsulated frame index
- `tests/fixtures/generate_synthetic_dicom.py` — `write_synthetic_jpeg_multiframe_dicom`
- `tests/unit/test_dicom_session.py` — JPEG multiframe + BOT tests

**Out of scope:** (done in P1c/P1d)

---

## P1b — JPEG-2000 + Extended Offset Table

**Goal:** Random access for JPEG-2000 multiframe via `openjpeg` decode and EOT-aware `generate_frames`.

**Files:** `dicom_session.py`, `generate_synthetic_dicom.py`, `test_dicom_session.py`

---

## P1c — MP4 keyframe index

**Goal:** Keyframe-aware seek in `VideoReader` for backward/random scroll.

**Files:** `video_reader.py`, `test_video_reader.py`

---

## P1d — Scroll min_buffer

**Goal:** Neighbor prefetch fills to `min_buffer` first, then up to `scroll_batch_size`.

**Files:** `app_controller.py`, `test_scroll_min_buffer.py`
