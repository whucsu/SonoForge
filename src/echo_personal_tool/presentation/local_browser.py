"""Study tree browser widget."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem

from echo_personal_tool.domain.models import InstanceMetadata, StudyMetadata


class LocalBrowserWidget(QTreeWidget):
    """Tree: Study datetime → Series → Instance."""

    instance_selected = Signal(object)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setHeaderLabels(["Study / Series / Instance"])
        self.itemClicked.connect(self._on_item_clicked)

    def populate(self, studies: list[StudyMetadata]) -> None:
        self.clear()
        for study in studies:
            label = study.study_datetime.strftime("%Y-%m-%d %H:%M:%S")
            study_item = QTreeWidgetItem([label])
            study_item.setData(0, 256, study.study_uid)
            self.addTopLevelItem(study_item)

            for series in study.series:
                series_label = f"{series.modality} — {series.description or series.series_uid[:8]}"
                series_item = QTreeWidgetItem([series_label])
                series_item.setData(0, 256, series.series_uid)
                study_item.addChild(series_item)

                for instance in series.instances:
                    inst_label = (
                        f"{instance.sop_instance_uid[:12]}… "
                        f"({instance.number_of_frames} frames)"
                    )
                    inst_item = QTreeWidgetItem([inst_label])
                    inst_item.setData(0, 256, instance)
                    series_item.addChild(inst_item)

            study_item.setExpanded(True)

    def _on_item_clicked(self, item: QTreeWidgetItem, _column: int) -> None:
        payload = item.data(0, 256)
        if isinstance(payload, InstanceMetadata):
            self.instance_selected.emit(payload)
