"""Background Orthanc series downloader."""

from __future__ import annotations

from PySide6.QtCore import QObject, QRunnable, Signal, Slot

from echo_personal_tool.domain.ports import DicomWebClient
from echo_personal_tool.infrastructure.orthanc_cache import OrthancSessionCache


class OrthancDownloadSignals(QObject):
    progress = Signal(int, int, str)  # overall_current, overall_total, series_uid
    series_done = Signal(str, str)  # series_uid, status "ok"|"failed"|"cancelled"
    done = Signal(str, str)  # session_id, study_uid
    failed = Signal(str, str)  # study_uid or series_uid, message
    cancelled = Signal(str)  # session_id


class OrthancDownloadWorker(QRunnable):
    """Download study series from Orthanc into session cache."""

    def __init__(
        self,
        client: DicomWebClient,
        cache: OrthancSessionCache,
        session_id: str,
        study_uid: str,
        series_uids: list[str],
        parent: QObject | None = None,
    ) -> None:
        super().__init__()
        self._client = client
        self._cache = cache
        self._session_id = session_id
        self._study_uid = study_uid
        self._series_uids = series_uids
        self._cancelled = False
        self.signals = OrthancDownloadSignals(parent)
        self.setAutoDelete(True)

    def cancel(self) -> None:
        self._cancelled = True

    @Slot()
    def run(self) -> None:
        try:
            series_instances: list[tuple[str, list]] = []
            for series_uid in self._series_uids:
                if self._cancelled:
                    self._finish_cancelled()
                    return
                instances = self._client.query_instances(self._study_uid, series_uid)
                series_instances.append((series_uid, instances))

            total = sum(len(instances) for _, instances in series_instances)
            overall_current = 0
            all_ok = True

            for series_uid, instances in series_instances:
                if self._cancelled:
                    self._finish_cancelled()
                    return
                series_ok = self._download_series(
                    series_uid, instances, total, overall_current
                )
                overall_current += len(instances)
                if not series_ok:
                    all_ok = False

            if self._cancelled:
                self._finish_cancelled()
                return
            if all_ok:
                self.signals.done.emit(self._session_id, self._study_uid)
        except Exception as exc:  # noqa: BLE001
            if self._cancelled:
                self._finish_cancelled()
                return
            self.signals.failed.emit(self._study_uid, str(exc))

    def _finish_cancelled(self) -> None:
        self._cache.clear_session(self._session_id)
        self.signals.cancelled.emit(self._session_id)

    def _download_series(
        self,
        series_uid: str,
        instances: list,
        total: int,
        prior_count: int,
    ) -> bool:
        series_failed = False
        for index, instance in enumerate(instances, start=1):
            if self._cancelled:
                self.signals.series_done.emit(series_uid, "cancelled")
                return False
            data = self._download_instance(series_uid, instance.sop_instance_uid)
            if data is None:
                series_failed = True
            elif not self._cancelled:
                self._cache.save_instance(
                    self._session_id,
                    self._study_uid,
                    series_uid,
                    instance.sop_instance_uid,
                    data,
                )
            overall = prior_count + index
            self.signals.progress.emit(overall, total, series_uid)
        status = "failed" if series_failed else "ok"
        self.signals.series_done.emit(series_uid, status)
        return not series_failed

    def _download_instance(self, series_uid: str, instance_uid: str) -> bytes | None:
        if self._cancelled:
            return None
        for attempt in range(2):
            if self._cancelled:
                return None
            try:
                return self._client.download_instance(
                    self._study_uid, series_uid, instance_uid
                )
            except Exception:
                if attempt == 1:
                    return None
        return None
