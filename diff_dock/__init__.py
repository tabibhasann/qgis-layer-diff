"""Diff dock widget — QGIS UI for layer comparison."""

from __future__ import annotations

from qgis.core import (
    QgsGeometry,
    QgsMapLayerProxyModel,
    QgsProject,
    QgsVectorLayer,
)
from qgis.gui import QgsMapLayerComboBox
from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDockWidget,
    QDoubleSpinBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..core.differ import compute_diff
from ..core.models import FeatureRecord
from ..core.report import to_csv, to_html
from .layer_utils import layer_to_records
from .postgis_dialog import add_postgis_layer
from .result_layers import create_result_layer


class DiffDock(QDockWidget):  # type: ignore[misc]
    """Dockable panel for comparing two vector layers."""

    closing = pyqtSignal()

    def __init__(self, iface):
        super().__init__("Layer Diff")
        self.iface = iface
        self.result = None
        self.result_layers: list[QgsVectorLayer] = []

        self.setMinimumWidth(350)
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)

        central = QWidget()
        self.setWidget(central)
        layout = QVBoxLayout(central)

        self._build_layer_pickers(layout)
        self._build_postgis_button(layout)
        self._build_key_field(layout)
        self._build_options(layout)
        self._build_run_button(layout)
        self._build_summary(layout)
        self._build_results_table(layout)
        self._build_export_buttons(layout)

    def _build_layer_pickers(self, layout: QVBoxLayout) -> None:
        layout.addWidget(QLabel("<b>Layer A</b> (before)"))
        self.layer_a_combo = QgsMapLayerComboBox()
        self.layer_a_combo.setFilters(QgsMapLayerProxyModel.VectorLayer)
        layout.addWidget(self.layer_a_combo)

        layout.addWidget(QLabel("<b>Layer B</b> (after)"))
        self.layer_b_combo = QgsMapLayerComboBox()
        self.layer_b_combo.setFilters(QgsMapLayerProxyModel.VectorLayer)
        layout.addWidget(self.layer_b_combo)

    def _build_postgis_button(self, layout: QVBoxLayout) -> None:
        pgis_layout = QHBoxLayout()
        self.pgis_btn = QPushButton("Add PostGIS Layer")
        self.pgis_btn.clicked.connect(self._add_postgis_layer)
        pgis_layout.addWidget(self.pgis_btn)
        layout.addLayout(pgis_layout)

    def _build_key_field(self, layout: QVBoxLayout) -> None:
        layout.addWidget(QLabel("<b>Match by key field</b> (optional)"))
        key_layout = QHBoxLayout()
        self.key_combo = QComboBox()
        self.key_combo.setEnabled(False)
        key_layout.addWidget(self.key_combo)
        self.use_key_check = QCheckBox("Use key")
        self.use_key_check.toggled.connect(self.key_combo.setEnabled)
        self.layer_a_combo.currentIndexChanged.connect(self._update_fields)
        key_layout.addWidget(self.use_key_check)
        layout.addLayout(key_layout)

    def _build_options(self, layout: QVBoxLayout) -> None:
        opts = QGroupBox("Options")
        opts_layout = QVBoxLayout(opts)
        self.compare_geom_check = QCheckBox("Compare geometry")
        self.compare_geom_check.setChecked(True)
        opts_layout.addWidget(self.compare_geom_check)
        self.compare_attrs_check = QCheckBox("Compare attributes")
        self.compare_attrs_check.setChecked(True)
        opts_layout.addWidget(self.compare_attrs_check)

        tol_layout = QHBoxLayout()
        tol_layout.addWidget(QLabel("Geometry tolerance:"))
        self.tolerance_spin = QDoubleSpinBox()
        self.tolerance_spin.setRange(0.0, 1000000.0)
        self.tolerance_spin.setDecimals(6)
        self.tolerance_spin.setSingleStep(0.000001)
        self.tolerance_spin.setValue(0.0)
        self.tolerance_spin.setSuffix(" (CRS units)")
        self.tolerance_spin.setToolTip("Features within this distance are considered equal. 0 = exact match.")
        tol_layout.addWidget(self.tolerance_spin)
        opts_layout.addLayout(tol_layout)

        ignore_layout = QHBoxLayout()
        ignore_layout.addWidget(QLabel("Ignore fields:"))
        self.ignore_fields_edit = QLineEdit()
        self.ignore_fields_edit.setPlaceholderText("comma-separated field names")
        self.ignore_fields_edit.setToolTip("These fields will be excluded from attribute comparison")
        ignore_layout.addWidget(self.ignore_fields_edit)
        opts_layout.addLayout(ignore_layout)

        self.summary_only_check = QCheckBox("Summary-only report (no per-feature details)")
        opts_layout.addWidget(self.summary_only_check)

        layout.addWidget(opts)

    def _build_run_button(self, layout: QVBoxLayout) -> None:
        self.run_btn = QPushButton("Compute Diff")
        self.run_btn.clicked.connect(self._run_diff)
        self.run_btn.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; padding: 8px; font-weight: bold; }"
        )
        layout.addWidget(self.run_btn)

    def _build_summary(self, layout: QVBoxLayout) -> None:
        self.summary_label = QLabel("")
        self.summary_label.setWordWrap(True)
        layout.addWidget(self.summary_label)

    def _build_results_table(self, layout: QVBoxLayout) -> None:
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Key", "Type", "Geometry Changed", "Field Changes"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.cellClicked.connect(self._on_cell_clicked)
        layout.addWidget(self.table)

        self.detail_label = QLabel("<i>Click a modified row to see field-by-field changes</i>")
        self.detail_label.setWordWrap(True)
        layout.addWidget(self.detail_label)

        self.detail_table = QTableWidget(0, 3)
        self.detail_table.setHorizontalHeaderLabels(["Field", "Old", "New"])
        self.detail_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.detail_table)

    def _build_export_buttons(self, layout: QVBoxLayout) -> None:
        export_layout = QHBoxLayout()
        self.export_html_btn = QPushButton("Export HTML")
        self.export_html_btn.clicked.connect(self._export_html)
        export_layout.addWidget(self.export_html_btn)
        self.export_csv_btn = QPushButton("Export CSV")
        self.export_csv_btn.clicked.connect(self._export_csv)
        export_layout.addWidget(self.export_csv_btn)
        layout.addLayout(export_layout)

    def _update_fields(self) -> None:
        self.key_combo.clear()
        layer = self.layer_a_combo.currentLayer()
        if layer:
            for field in layer.fields():
                self.key_combo.addItem(field.name())

    def _add_postgis_layer(self) -> None:
        add_postgis_layer(self, self.layer_b_combo)

    def _run_diff(self) -> None:
        layer_a = self.layer_a_combo.currentLayer()
        layer_b = self.layer_b_combo.currentLayer()

        if not layer_a or not layer_b:
            QMessageBox.warning(self, "Error", "Select both Layer A and Layer B.")
            return

        if not layer_a.crs().isValid() or not layer_b.crs().isValid():
            QMessageBox.warning(
                self,
                "CRS Warning",
                "One or both layers have an invalid CRS. Results may be incorrect.",
            )
        elif layer_a.crs() != layer_b.crs():
            QMessageBox.information(
                self,
                "CRS Reprojection",
                f"Layer B will be reprojected from {layer_b.crs().authid()} "
                f"to {layer_a.crs().authid()} for comparison.",
            )

        self._clear_results()

        key_field = self.key_combo.currentText() if self.use_key_check.isChecked() else None
        compare_geom = self.compare_geom_check.isChecked()
        compare_attrs = self.compare_attrs_check.isChecked()
        tolerance = self.tolerance_spin.value()
        ignore_fields_text = self.ignore_fields_edit.text().strip()
        ignore_fields = (
            set(f.strip() for f in ignore_fields_text.split(",") if f.strip()) if ignore_fields_text else None
        )

        try:
            records_a = layer_to_records(layer_a, layer_a, key_field, ignore_fields)
            records_b = layer_to_records(layer_b, layer_a, key_field, ignore_fields)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to read layers: {e}")
            return

        self.result = compute_diff(
            records_a,
            records_b,
            key=key_field,
            geom_tolerance=tolerance,
            compare_geometry=compare_geom,
            compare_attributes=compare_attrs,
            ignore_fields=ignore_fields,
        )

        if self.result.warnings:
            QMessageBox.warning(self, "Duplicate Keys", "\n".join(self.result.warnings))

        self._display_results(layer_a, layer_b)

    def _clear_results(self) -> None:
        for layer in self.result_layers:
            QgsProject.instance().removeMapLayer(layer)
        self.result_layers = []
        self.table.setRowCount(0)

    def _display_results(self, layer_a, layer_b) -> None:
        if not self.result:
            return

        s = self.result.summary
        self.summary_label.setText(
            f"+{s['added']} added  -{s['removed']} removed  ~{s['modified']} modified  ={s['unchanged']} unchanged"
        )

        total_rows = len(self.result.added) + len(self.result.removed) + len(self.result.modified)
        self.table.setRowCount(total_rows)
        row = 0

        for rec in self.result.added:
            self.table.setItem(row, 0, QTableWidgetItem(str(rec.key)))
            self.table.setItem(row, 1, QTableWidgetItem("added"))
            self.table.setItem(row, 2, QTableWidgetItem(""))
            self.table.setItem(row, 3, QTableWidgetItem(""))
            row += 1

        for rec in self.result.removed:
            self.table.setItem(row, 0, QTableWidgetItem(str(rec.key)))
            self.table.setItem(row, 1, QTableWidgetItem("removed"))
            self.table.setItem(row, 2, QTableWidgetItem(""))
            self.table.setItem(row, 3, QTableWidgetItem(""))
            row += 1

        for mod in self.result.modified:
            self.table.setItem(row, 0, QTableWidgetItem(str(mod.key)))
            self.table.setItem(row, 1, QTableWidgetItem("modified"))
            self.table.setItem(row, 2, QTableWidgetItem("Yes" if mod.geometry_changed else "No"))
            changes = ", ".join(f"{fc.field}: {fc.old}→{fc.new}" for fc in mod.field_changes[:5])
            if len(mod.field_changes) > 5:
                changes += f" (+{len(mod.field_changes) - 5} more)"
            self.table.setItem(row, 3, QTableWidgetItem(changes))
            row += 1

        if s["added"]:
            layer = create_result_layer("added", self.result.added, QColor(76, 175, 80), layer_a)
            self.result_layers.append(layer)
        if s["removed"]:
            layer = create_result_layer("removed", self.result.removed, QColor(244, 67, 54), layer_a)
            self.result_layers.append(layer)
        if s["modified"]:
            mod_records = [FeatureRecord(key=m.key, attrs={"key": m.key}, wkt=m.new_wkt) for m in self.result.modified]
            layer = create_result_layer("modified", mod_records, QColor(255, 152, 0), layer_a)
            self.result_layers.append(layer)

    def _on_cell_clicked(self, row: int, col: int) -> None:
        if not self.result:
            return
        n_added = len(self.result.added)
        n_removed = len(self.result.removed)
        if row < n_added + n_removed:
            return
        mod_idx = row - n_added - n_removed
        if mod_idx >= len(self.result.modified):
            return
        mod = self.result.modified[mod_idx]

        self.detail_table.setRowCount(len(mod.field_changes))
        for i, fc in enumerate(mod.field_changes):
            old_item = QTableWidgetItem("" if fc.old is None else str(fc.old))
            new_item = QTableWidgetItem("" if fc.new is None else str(fc.new))
            old_item.setBackground(QColor(244, 67, 54, 50))
            new_item.setBackground(QColor(76, 175, 80, 50))
            self.detail_table.setItem(i, 0, QTableWidgetItem(fc.field))
            self.detail_table.setItem(i, 1, old_item)
            self.detail_table.setItem(i, 2, new_item)

        if mod.geometry_changed:
            geom_row = self.detail_table.rowCount()
            self.detail_table.insertRow(geom_row)
            geom_item = QTableWidgetItem("(geometry)")
            geom_item.setBackground(QColor(255, 152, 0, 50))
            self.detail_table.setItem(geom_row, 0, geom_item)
            self.detail_table.setItem(geom_row, 1, QTableWidgetItem("Changed"))
            self.detail_table.setItem(geom_row, 2, QTableWidgetItem("Changed"))

        self.detail_label.setText(
            f"<b>Modified feature:</b> {mod.key}  "
            f"(<i>{len(mod.field_changes)} field change(s)"
            f"{', geometry changed' if mod.geometry_changed else ''}</i>)"
        )

        if mod.new_wkt:
            geom = QgsGeometry.fromWkt(mod.new_wkt)
            if geom and not geom.isEmpty():
                self.iface.mapCanvas().flashGeometries([geom])
                self.iface.mapCanvas().zoomToFeatureExtent(geom.boundingBox())

    def _export_html(self) -> None:
        if not self.result:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export HTML", "", "HTML (*.html)")
        if path:
            summary_only = self.summary_only_check.isChecked()
            html = to_html(self.result, summary_only=summary_only)
            with open(path, "w", encoding="utf-8") as f:
                f.write(html)

    def _export_csv(self) -> None:
        if not self.result:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export CSV", "", "CSV (*.csv)")
        if path:
            csv_content = to_csv(self.result)
            with open(path, "w", encoding="utf-8", newline="") as f:
                f.write(csv_content)

    def closeEvent(self, event) -> None:
        self._clear_results()
        self.closing.emit()
        super().closeEvent(event)
