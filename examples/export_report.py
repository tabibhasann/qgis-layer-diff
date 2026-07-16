#!/usr/bin/env python3
"""export_report.py — Export a layer diff report as HTML."""

from qgis.core import QgsVectorLayer
from qgis_layer_diff import compare_layers, export_report

old_layer = QgsVectorLayer("data/v1.shp", "v1", "ogr")
new_layer = QgsVectorLayer("data/v2.shp", "v2", "ogr")

result = compare_layers(old_layer, new_layer, match_by="key", key_field="id")

# Export HTML report
export_report(result, output_path="diff_report.html")
print("Report saved to diff_report.html")
