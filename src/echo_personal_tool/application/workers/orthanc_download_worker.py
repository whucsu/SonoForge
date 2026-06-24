"""Background Orthanc series downloader."""

from __future__ import annotations

import logging

from PySide6.QtCore import QObject, QRunnable, Signal, Slot

logger = logging.getLogger(__name__)

from echo_personal_tool.domain.ports import DicomWebClient
from echo_personal_tool.infrastructure.orthanc_cache import OrthancSessionCache
from echo_personal_tool.infrastructure.orthanc_client import OrthancDicomWebClient


class OrthancDownloadSignals(QObject):
    progress = Signal(int, int, str)  # overall_current, overall_total, series_uid
    series_done = Signal(str, str)  # series_uid, status "ok"|"failed"|"cancelled"
    done = Signal(str, str)  # session_id, study_uid
    failed = Signal(str, str)  # study_uid or series_uid, message
    cancelled = Signal(str)  # session_id


class OrthancDownloadWorker(QRunnable):
    """Download study series from Orthanc into session cache.

    Uses WADO-RS series-level retrieval (one request per series)
    instead of per-instance download to avoid Orthanc DICOMweb
    plugin limitation (no instance-level WADO-RS).

    Creates its own httpx.Client in the worker thread to avoid
    thread-safety issues with the shared client from the main thread.
    """

    def __init__(
        self,
        client: DicomWebClient,
        cache: OrthancSessionCache,
        session_id: str,
        study_uid: str,
        series_uids: list[str],
        parent: QObject | None = None,
        *,
        base_url: str | None = None,
        username: str | None = None,
        password: str | None = None,
    ) -> None:
        super().__init__()
        self._client = client
        self._cache = cache
        self._session_id = session_id
        self._study_uid = study_uid
        self._series_uids = series_uids
        self._base_url = base_url
        self._username = username
        self._password = password
        self._cancelled = False
        self._thread_client: OrthancDicomWebClient | None = None
        self.signals = OrthancDownloadSignals(parent)
        self.setAutoDelete(True)

    def cancel(self) -> None:
        self._cancelled = True

    @Slot()
    def run(self) -> None:
        _client: DicomWebClient = self._client
        if self._base_url:
            self._thread_client = OrthancDicomWebClient(
                self._base_url, self._username or "", self._password or "",
                timeout=120.0,
            )
            _client = self._thread_client
        try:
            series_instances: list[tuple[str, list]] = []
            for series_uid in self._series_uids:
                if self._cancelled:
                    self._finish_cancelled()
                    return
                instances = _client.query_instances(self._study_uid, series_uid)
                series_instances.append((series_uid, instances))

            total = sum(len(instances) for _, instances in series_instances)
            overall_current = 0
            all_ok = True

            all_errors: list[str] = []
            for series_uid, instances in series_instances:
                if self._cancelled:
                    self._finish_cancelled()
                    return
                series_ok, errors = self._download_series(
                    _client, series_uid, total, overall_current
                )
                overall_current += len(instances)
                if not series_ok:
                    all_ok = False
                    if errors:
                        all_errors.append(errors)

            if self._cancelled:
                self._finish_cancelled()
                return
            if all_ok:
                self.signals.done.emit(self._session_id, self._study_uid)
            else:
                detail = "; ".join(all_errors) if all_errors else ""
                message = "Одна или несколько серий не загружены"
                if detail:
                    message += f": {detail}"
                self.signals.failed.emit(self._study_uid, message)
        except Exception as exc:  # noqa: BLE001
            if self._cancelled:
                self._finish_cancelled()
                return
            self.signals.failed.emit(self._study_uid, str(exc))
        finally:
            if self._thread_client is not None:
                self._thread_client.close()
                self._thread_client = None

    def _finish_cancelled(self) -> None:
        self._cache.clear_session(self._session_id)
        self.signals.cancelled.emit(self._session_id)

    def _download_series(
        self,
        client: DicomWebClient,
        series_uid: str,
        total: int,
        prior_count: int,
    ) -> tuple[bool, str]:
        try:
            series_data = client.download_series(self._study_uid, series_uid)
        except Exception as exc:
            logger.exception("Download series %s failed: %s", series_uid, exc)
            self.signals.series_done.emit(series_uid, "failed")
            return False, str(exc)

        errors: list[str] = []
        for idx, (sop_uid, data) in enumerate(series_data):
            if self._cancelled:
                self.signals.series_done.emit(series_uid, "cancelled")
                return False, ""
            if data:
                self._cache.save_instance(
                    self._session_id,
                    self._study_uid,
                    series_uid,
                    sop_uid or f"unknown_{idx}",
                    data,
                )
            else:
                errors.append(f"instance {sop_uid or idx}: empty data")
            overall = prior_count + idx + 1
            self.signals.progress.emit(overall, total, series_uid)

        status = "failed" if errors else "ok"
        error_summary = "; ".join(errors) if errors else ""
        self.signals.series_done.emit(series_uid, status)
        return not errors, error_summary
