"""Orthanc DICOMweb client (QIDO-RS + WADO-RS over httpx)."""

from __future__ import annotations

import email
import logging
from email import policy
from io import BytesIO

import httpx
import pydicom

logger = logging.getLogger(__name__)

from echo_personal_tool.domain.models.orthanc import InstanceInfo, SeriesInfo, StudyInfo
from echo_personal_tool.infrastructure.orthanc_dicom_json import (
    parse_instances,
    parse_series,
    parse_studies,
)

_STUDY_INCLUDE_FIELDS = (
    "0020000D",  # StudyInstanceUID
    "00100010",  # PatientName
    "00100020",  # PatientID
    "00080020",  # StudyDate
    "00081030",  # StudyDescription
)

_SERIES_INCLUDE_FIELDS = (
    "0020000E",  # SeriesInstanceUID
    "00080060",  # Modality
    "0008103E",  # SeriesDescription
    "00201209",  # NumberOfSeriesRelatedInstances
)

_INSTANCE_INCLUDE_FIELDS = (
    "00080018",  # SOPInstanceUID
)


def _include_params(tags: tuple[str, ...]) -> list[tuple[str, str]]:
    return [("includefield", tag) for tag in tags]


class OrthancDicomWebClient:
    def __init__(self, base_url: str, username: str, password: str, timeout: float = 30.0):
        self._client = httpx.Client(
            base_url=base_url.rstrip("/"),
            auth=(username, password),
            timeout=timeout,
        )

    def ping(self) -> bool:
        try:
            r = self._client.get("/system")
            return r.status_code == 200
        except httpx.HTTPError:
            return False

    def query_studies(self, patient_name: str | None = None) -> list[StudyInfo]:
        params: list[tuple[str, str]] = _include_params(_STUDY_INCLUDE_FIELDS)
        if patient_name:
            params.append(("PatientName", f"*{patient_name}*"))
        r = self._client.get(
            "/dicom-web/studies",
            params=params,
            headers={"Accept": "application/dicom+json"},
        )
        r.raise_for_status()
        return parse_studies(r.json())

    def query_series(self, study_uid: str) -> list[SeriesInfo]:
        r = self._client.get(
            f"/dicom-web/studies/{study_uid}/series",
            params=_include_params(_SERIES_INCLUDE_FIELDS),
            headers={"Accept": "application/dicom+json"},
        )
        r.raise_for_status()
        return parse_series(r.json(), study_uid)

    def query_instances(self, study_uid: str, series_uid: str) -> list[InstanceInfo]:
        r = self._client.get(
            f"/dicom-web/studies/{study_uid}/series/{series_uid}/instances",
            params=_include_params(_INSTANCE_INCLUDE_FIELDS),
            headers={"Accept": "application/dicom+json"},
        )
        r.raise_for_status()
        return parse_instances(r.json(), study_uid, series_uid)

    def download_instance(self, study_uid: str, series_uid: str, instance_uid: str) -> bytes:
        r = self._client.get(
            f"/dicom-web/studies/{study_uid}/series/{series_uid}/instances/{instance_uid}",
            headers={"Accept": "multipart/related; type=application/dicom"},
        )
        if r.status_code != 200:
            logger.error(
                "WADO-RS retrieve failed: status=%d body=%s", r.status_code, r.text[:2000]
            )
        r.raise_for_status()
        return r.content

    def download_series(self, study_uid: str, series_uid: str) -> list[tuple[str, bytes]]:
        r = self._client.get(
            f"/dicom-web/studies/{study_uid}/series/{series_uid}",
            headers={"Accept": "multipart/related; type=application/dicom"},
        )
        if r.status_code != 200:
            logger.error(
                "WADO-RS series retrieve failed: status=%d body=%s",
                r.status_code, r.text[:2000],
            )
        r.raise_for_status()
        raw_parts = _parse_multipart(r.content, r.headers.get("content-type", ""))
        result: list[tuple[str, bytes]] = []
        for data in raw_parts:
            try:
                ds = pydicom.dcmread(BytesIO(data))
                sop_uid = str(getattr(ds, "SOPInstanceUID", ""))
            except Exception:
                sop_uid = ""
            result.append((sop_uid, data))
        return result

    def close(self) -> None:
        self._client.close()


def _parse_multipart(content: bytes, content_type: str) -> list[bytes]:
    """Parse multipart MIME body into list of part payloads."""
    msg = email.message_from_bytes(
        f"Content-Type: {content_type}\n\n".encode() + content,
        policy=policy.compat32,
    )
    if not msg.is_multipart():
        return [content]
    parts: list[bytes] = []
    for part in msg.walk():
        if part.get_content_maintype() == "multipart":
            continue
        data = part.get_payload(decode=True)
        if data:
            parts.append(data)
    return parts
