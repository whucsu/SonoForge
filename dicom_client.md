# Session Log: Orthanc DICOMweb WADO-RS Fix

**Date:** 2026-06-24  
**Project:** ECHO2026  
**Server:** http://192.168.1.111:8042 (Orthanc DICOMweb, Basic auth pacs:pppSScADDR)  

---

## Problem

Диалог загрузки DICOM-серий с Orthanc через DICOMweb не закрывается — все экземпляры возвращают 400 Bad Request.

### Initial Logs

URL pattern failing:
```
GET /dicom-web/studies/{StudyUID}/series/{SeriesUID}/instances/{InstanceUID}
Accept: application/dicom
→ HTTP 400 Bad Request
```

---

## Step 1: Add error logging + thread-local client

We modified `orthanc_client.py` and `orthanc_download_worker.py` to:
- Add `logger.exception()` — traceback in console on failed download
- Make worker create its own `httpx.Client` in thread (thread-safety)
- Emit `failed` signal when `all_ok=False`
- Return error text from `_download_instance` as tuple `(bytes | None, str)`

**Files changed:**
- `src/echo_personal_tool/infrastructure/orthanc_client.py`
- `src/echo_personal_tool/application/workers/orthanc_download_worker.py`

---

## Step 2: Fix dialog (sorting, progress, close)

Modified `orthanc_study_dialog.py` and `main_window.py`:
- Sorting by date DESC + patient name
- Indeterminate progress bar during download
- Tree widget blocking during download
- closeEvent with fallback
- Connected `series_done` signal
- Pass `base_url/username/password` from `MainWindow` to dialog
- Added `logging.basicConfig(level=DEBUG)` in `main.py`

**Files changed:**
- `src/echo_personal_tool/presentation/orthanc_study_dialog.py`
- `src/echo_personal_tool/presentation/main_window.py`
- `src/echo_personal_tool/main.py`

---

## Step 3: Change Accept header → 400 persists

Changed Accept from `application/dicom` to `multipart/related; type=application/dicom`.

Ran the app. Still got 400. But now with error logging we could see the body:

```json
{
    "Details" : "This WADO-RS plugin cannot generate the following content type: application/dicom",
    "HttpError" : "Bad Request",
    "HttpStatus" : 400,
    "OrthancError" : "Bad request",
    "OrthancStatus" : 8
}
```

**Diagnosis:** Orthanc DICOMweb WADO-RS plugin does NOT support instance-level retrieval. The URL path `/dicom-web/studies/{study}/series/{series}/instances/{instance}` fails regardless of Accept header.

---

## Step 4: Implement series-level WADO-RS

Changed approach: instead of N requests per instance (which Orthanc rejects), make **1 request per series** using `GET /dicom-web/studies/{study}/series/{series}` with `Accept: multipart/related; type=application/dicom`.

### Changes

**`src/echo_personal_tool/domain/ports.py`:**
- Added `download_series(study_uid, series_uid) -> list[tuple[str, bytes]]` to `DicomWebClient` protocol

**`src/echo_personal_tool/infrastructure/orthanc_client.py`:**
- New imports: `email`, `pydicom`, `BytesIO`
- Added `_parse_multipart(content, content_type)` — parses multipart/related MIME response using `email.message_from_bytes`
- Added `download_series()` — series-level WADO-RS, parses multipart, extracts SOPInstanceUID via pydicom

**`src/echo_personal_tool/infrastructure/fake_dicom_web_client.py`:**
- Added `download_series()` stub (queries instances, returns sample DICOM data)

**`src/echo_personal_tool/application/workers/orthanc_download_worker.py`:**
- Removed `_download_instance()` (per-instance with retry — no longer needed)
- `_download_series()` now calls `client.download_series()` — single HTTP request per series
- Progress tracking uses index from returned multipart data

**`tests/unit/test_orthanc_download_worker.py`:**
- Changed test clients to override `download_series` instead of `download_instance`
- Removed `test_download_retries_once_then_succeeds` (retry logic removed)
- Updated assertions for `test_series_failed_when_download_fails` (now emits `failed` signal)
- Updated `test_cancel_clears_session_and_emits_cancelled` (now emits `series_done` with "cancelled")

---

## Final State

All 4 unit tests pass:
```
tests/unit/test_orthanc_download_worker.py ....                          [100%]
```

### Summary of all changed files

| File | Change |
|------|--------|
| `src/echo_personal_tool/domain/ports.py` | Added `download_series` to protocol |
| `src/echo_personal_tool/infrastructure/orthanc_client.py` | Added `_parse_multipart` + `download_series`; imports: email, pydicom |
| `src/echo_personal_tool/infrastructure/fake_dicom_web_client.py` | Added `download_series` stub |
| `src/echo_personal_tool/application/workers/orthanc_download_worker.py` | Removed `_download_instance`; switched to `download_series` |
| `src/echo_personal_tool/presentation/orthanc_study_dialog.py` | Sorting, progress, closeEvent, series_done signal |
| `src/echo_personal_tool/presentation/main_window.py` | Pass credentials to dialog |
| `src/echo_personal_tool/main.py` | Added `logging.basicConfig` |
| `tests/unit/test_orthanc_download_worker.py` | Updated for new worker logic |

### How to test

1. Run the app
2. Orthanc → search patient → select study → expand → check series → Load
3. Console should show no `400 Bad Request`
4. DICOM files saved to session cache
5. Dialog closes automatically on success
