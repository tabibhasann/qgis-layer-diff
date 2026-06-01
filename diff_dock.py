"""Diff dock widget — QGIS UI for layer comparison."""

import os

from qgis.PyQt.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QComboBox, QLabel, QTableWidget, QTableWidgetItem, QFileDialog,
    QCheckBox, QGroupBox, QSplitter, QTextEdit, QHeaderView, QMessageBox,
)
from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.core import (
    QgsVectorLayer, QgsProject, QgsMapLayerProxyModel,
    QgsCoordinateTransform, QgsFeature, QgsGeometry, QgsField,
    QgsSingleSymbolRenderer, QgsFillSymbol, QgsCategorizedSymbolRenderer,
    QgsRendererCategory,
)
from qgis.PyQt.QtGui import QColor

from .core.models import FeatureRecord
from .core.differ import compute_diff
from .core.report import to_html, to_csv


class DiffDock(QDockWidget):
    """Dockable panel for comparing two vector layers."""

    closing = pyqtSignal()

    def __init__(self, iface):
        super().__init__("Layer Diff")
        self.iface = iface
        self.result = None
        self.result_layers = []

        self.setMinimumWidth(350)
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)

        central = QWidget()
        self.setWidget(central)
        layout = QVBoxLayout(central)

        # Layer pickers
        layout.addWidget(QLabel("<b>Layer A</b> (before)"))
        self.layer_a_combo = QComboBox()
        self.layer_a_combo.setFilters(QgsMapLayerProxyModel.VectorLayer)
        layout.addWidget(self.layer_a_combo)

        layout.addWidget(QLabel("<b>Layer B</b> (after)"))
        self.layer_b_combo = QComboBox()
        self.layer_b_combo.setFilters(QgsMapLayerProxyModel.VectorLayer)
        layout.addWidget(self.layer_b_combo)

        # Key field
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

        # Options
        opts = QGroupBox("Options")
        opts_layout = QVBoxLayout(opts)
        self.compare_geom_check = QCheckBox("Compare geometry")
        self.compare_geom_check.setChecked(True)
        opts_layout.addWidget(self.compare_geom_check)
        self.compare_attrs_check = QCheckBox("Compare attributes")
        self.compare_attrs_check.setChecked(True)
        opts_layout.addWidget(self.compare_attrs_check)
        layout.addWidget(opts)

        # Run button
        self.run_btn = QPushButton("Compute Diff")
        self.run_btn.clicked.connect(self._run_diff)
        self.run_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; padding: 8px; font-weight: bold; }")
        layout.addWidget(self.run_btn)

        # Summary
        self.summary_label = QLabel("")
        self.summary_label.setWordWrap(True)
        layout.addWidget(self.summary_label)

        # Results table
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Key", "Type", "Geometry Changed", "Field Changes"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.cellClicked.connect(self._on_cell_clicked)
        layout.addWidget(self.table)

        # Export buttons
        export_layout = QHBoxLayout()
        self.export_html_btn = QPushButton("Export HTML")
        self.export_html_btn.clicked.connect(self._export_html)
        export_layout.addWidget(self.export_html_btn)
        self.export_csv_btn = QPushButton("Export CSV")
        self.export_csv_btn.clicked.connect(self._export_csv)
        export_layout.addWidget(self.export_csv_btn)
        layout.addLayout(export_layout)

    def _update_fields(self):
        self.key_combo.clear()
        layer = self.layer_a_combo.currentLayer()
        if layer:
            for field in layer.fields():
                self.key_combo.addItem(field.name())

    def _run_diff(self):
        layer_a = self.layer_a_combo.currentLayer()
        layer_b = self.layer_b_combo.currentLayer()

        if not layer_a or not layer_b:
            QMessageBox.warning(self, "Error", "Select both Layer A and Layer B.")
            return

        self._clear_results()

        key_field = self.key_combo.currentText() if self.use_key_check.isChecked() else None
        compare_geom = self.compare_geom_check.isChecked()
        compare_attrs = self.compare_attrs_check.isChecked()

        try:
            records_a = self._layer_to_records(layer_a, layer_b, key_field)
            records_b = self._layer_to_records(layer_b, layer_a, key_field, is_second=True)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to read layers: {e}")
            return

        self.result = compute_diff(
            records_a, records_b,
            key=key_field,
            compare_geometry=compare_geom,
            compare_attributes=compare_attrs,
        )

        self._display_results(layer_a, layer_b)

    def _layer_to_records(self, layer, other_layer, key_field, is_second=False):
        """Convert a QgsVectorLayer to FeatureRecords, reprojecting if needed."""
        records = []
        needs_reproject = False
        if layer.crs() != other_layer.crs():
            needs_reproject = True
            transform = QgsCoordinateTransform(
                layer.crs(), other_layer.crs(), QgsProject.instance()
            )

        key_idx = layer.fields().indexOf(key_field) if key_field else -1

        for feat in layer.getFeatures():
            key = feat.attribute(key_idx) if key_idx >= 0 else feat.id()

            attrs = {}
            for field in feat.fields():
                fname = field.name()
                if key_field and fname == key_field:
                    continue
                val = feat.attribute(fname)
                if hasattr(val, "toString"):
                    val = val.toString()
                attrs[fname] = val

            geom = feat.geometry()
            if needs_reproject:
                geom.transform(transform)

            wkt = geom.asWkt() if geom and not geom.isEmpty() else ""

            records.append(FeatureRecord(key=str(key), attrs=attrs, wkt=wkt))

        return records

    def _clear_results(self):
        for layer in self.result_layers:
            QgsProject.instance().removeMapLayer(layer)
        self.result_layers = []
        self.table.setRowCount(0)

    def _display_results(self, layer_a, layer_b):
        if not self.result:
            return

        s = self.result.summary
        self.summary_label.setText(
            f"+{s['added']} added  -{s['removed']} removed  "
            f"~{s['modified']} modified  ={s['unchanged']} unchanged"
        )

        self.table.setRowCount(len(self.result.modified))
        for i, mod in enumerate(self.result.modified):
            self.table.setItem(i, 0, QTableWidgetItem(str(mod.key)))
            self.table.setItem(i, 1, QTableWidgetItem("modified"))
            self.table.setItem(i, 2, QTableWidgetItem("Yes" if mod.geometry_changed else "No"))
            changes = ", ".join(f"{fc.field}: {fc.old}→{fc.new}" for fc in mod.field_changes[:5])
            if len(mod.field_changes) > 5:
                changes += f" (+{len(mod.field_changes) - 5} more)"
            self.table.setItem(i, 3, QTableWidgetItem(changes))

        # Create styled result layers
        if s['added']:
            self._create_result_layer("added", self.result.added, QColor(76, 175, 80), layer_b)
        if s['removed']:
            self._create_result_layer("removed", self.result.removed, QColor(244, 67, 54), layer_a)
        if s['modified']:
            mod_records = [
                FeatureRecord(key=m.key, attrs={"key": m.key}, wkt=m.new_wkt)
                for m in self.result.modified
            ]
            self._create_result_layer("modified", mod_records, QColor(255, 152, 0), layer_b)

    def _create_result_layer(self, name, records, color, source_layer):
        geom_type = source_layer.geometryType()
        if geom_type == 0:
            geom_type_str = "Point"
        elif geom_type == 1:
            geom_type_str = "LineString"
        else:
            geom_type_str = "Polygon"

        crs = source_layer.crs().authid()
        uri = f"{geom_type_str}?crs={crs}&field=key:string"
        layer = QgsVectorLayer(uri, f"diff_{name}", "memory")
        dp = layer.dataProvider()

        features = []
        for rec in records:
            if not rec.wkt:
                continue
            feat = QgsFeature()
            feat.setGeometry(QgsGeometry.fromWkt(rec.wkt))
            feat.setAttributes([rec.key])
            features.append(feat)

        dp.addFeatures(features)
        layer.updateExtents()

        symbol = QgsFillSymbol.createSimple({
            "color": color.name(),
            "outline_color": color.darker(120).name(),
            "outline_width": "0.5",
        }) if geom_type > 0 else None

        if symbol:
            layer.setRenderer(QgsSingleSymbolRenderer(symbol))

        QgsProject.instance().addMapLayer(layer)
        self.result_layers.append(layer)

    def _on_cell_clicked(self, row, col):
        if not self.result or row >= len(self.result.modified):
            return
        mod = self.result.modified[row]
        if mod.new_wkt:
            geom = QgsGeometry.fromWkt(mod.new_wkt)
            if geom:
                self.iface.mapCanvas().flashGeometries([geom])
                self.iface.mapCanvas().zoomToFeatureExtent(
                    QgsGeometry.fromWkt(mod.new_wkt).boundingBox()
                )

    def _export_html(self):
        if not self.result:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export HTML", "", "HTML (*.html)")
        if path:
            html = to_html(self.result)
            with open(path, "w") as f:
                f.write(html)

    def _export_csv(self):
        if not self.result:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export CSV", "", "CSV (*.csv)")
        if path:
            csv_content = to_csv(self.result)
            with open(path, "w") as f:
                f.write(csv_content)

    def closeEvent(self, event):
        self.closing.emit()
        super().closeEvent(event)
