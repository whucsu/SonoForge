"""Orthanc DICOMweb client (QIDO-RS + WADO-RS over httpx)."""

from __future__ import annotations

import logging
import threading

import httpx

logger = logging.getLogger(__name__)

from echo_personal_tool.domain.models.orthanc import InstanceInfo, SeriesInfo, StudyInfo
from echo_personal_tool.infrastructure.orthanc_dicom_json import (
    parse_instances,
    parse_series,
    parse_studies,
)
from echo_personal_tool.infrastructure.server_settings import (
    ServerSettings,
    parse_http_headers,
    split_orthanc_urls,
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


class DownloadCancelled(Exception):
    """Raised when an in-flight WADO-RS download is aborted."""


class OrthancDicomWebClient:
    def __init__(
        self,
        base_url: str,
        username: str = "",
        password: str = "",
        *,
        auth_mode: str = "basic",
        http_headers: dict[str, str] | None = None,
        timeout: float = 30.0,
    ):
        self._timeout = timeout
        self._orthanc_root, self._dicom_web_root = split_orthanc_urls(base_url)
        headers = dict(http_headers or {})
        auth: tuple[str, str] | None = None
        has_auth_header = any(k.lower() == "authorization" for k in headers)
        if auth_mode == "basic" and (username or password) and not has_auth_header:
            auth = (username, password)
        self._orthanc_client = httpx.Client(
            base_url=f"{self._orthanc_root}/",
            auth=auth,
            headers=headers,
            timeout=self._timeout,
        )
        self._client = httpx.Client(
            base_url=f"{self._dicom_web_root}/",
            auth=auth,
            headers=headers,
            timeout=self._timeout,
        )
        self._cancel_event = threading.Event()

    @classmethod
    def from_settings(cls, settings: ServerSettings, *, timeout: float = 30.0) -> OrthancDicomWebClient:
        return cls(
            settings.url,
            settings.username,
            settings.password,
            auth_mode=settings.auth_mode,
            http_headers=parse_http_headers(settings.http_headers),
            timeout=timeout,
        )

    def _build_client(self) -> httpx.Client:
        return self._client

    def _check_cancelled(self) -> None:
        if self._cancel_event.is_set():
            raise DownloadCancelled("download cancelled")

    def cancel_inflight(self) -> None:
        self._cancel_event.set()
        try:
            self._client.close()
            self._orthanc_client.close()
        except Exception:  # noqa: BLE001
            logger.debug("Orthanc client close during cancel", exc_info=True)

    def ping(self) -> bool:
        try:
            r = self._orthanc_client.get("system")
            return r.status_code == 200
        except httpx.HTTPError:
            return False

    def query_studies(self, patient_name: str | None = None) -> list[StudyInfo]:
        params: list[tuple[str, str]] = _include_params(_STUDY_INCLUDE_FIELDS)
        if patient_name:
            params.append(("PatientName", f"*{patient_name}*"))
        r = self._client.get(
            "studies",
            params=params,
            headers={"Accept": "application/dicom+json"},
        )
        r.raise_for_status()
        return parse_studies(r.json())

    def query_series(self, study_uid: str) -> list[SeriesInfo]:
        r = self._client.get(
            f"studies/{study_uid}/series",
            params=_include_params(_SERIES_INCLUDE_FIELDS),
            headers={"Accept": "application/dicom+json"},
        )
        r.raise_for_status()
        return parse_series(r.json(), study_uid)

    def query_instances(self, study_uid: str, series_uid: str) -> list[InstanceInfo]:
        r = self._client.get(
            f"studies/{study_uid}/series/{series_uid}/instances",
            params=_include_params(_INSTANCE_INCLUDE_FIELDS),
            headers={"Accept": "application/dicom+json"},
        )
        r.raise_for_status()
        raw = r.json()
        instances = parse_instances(raw, study_uid, series_uid)
        logger.info(
            "[DIAG] query_instances series=%s server_returned=%d parsed=%d status=%d",
            series_uid[:16],
            len(raw) if isinstance(raw, list) else "?",
            len(instances),
            r.status_code,
        )
        return instances

    def download_instance(self, study_uid: str, series_uid: str, instance_uid: str) -> bytes:
        """Download single DICOM instance via WADO-RS per-instance retrieval."""
        self._check_cancelled()
        try:
            r = self._client.get(
                f"studies/{study_uid}/series/{series_uid}/instances/{instance_uid}",
                headers={"Accept": "application/dicom"},
            )
            r.raise_for_status()
            return r.content
        except httpx.HTTPError as exc:
            if self._cancel_event.is_set():
                raise DownloadCancelled("download cancelled") from exc
            raise

    def close(self) -> None:
        try:
            self._client.close()
            self._orthanc_client.close()
        except Exception:  # noqa: BLE001
            logger.debug("Orthanc client close", exc_info=True)
