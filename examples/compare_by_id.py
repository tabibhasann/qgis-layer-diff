#!/usr/bin/env python3
"""compare_by_id.py — Compare two vector layers by a key field in QGIS."""

from qgis.core import QgsVectorLayer
from qgis_layer_diff import compare_layers

# Load layers
old_layer = QgsVectorLayer("data/old_parcels.shp", "Old Parcels", "ogr")
new_layer = QgsVectorLayer("data/new_parcels.shp", "New Parcels", "ogr")

if not old_layer.isValid() or not new_layer.isValid():
    print("Failed to load layers")
    exit(1)

# Compare by key field
result = compare_layers(
    old_layer=old_layer,
    new_layer=new_layer,
    match_by="key",
    key_field="parcel_id",
)

print("Comparison complete:")
print(f"  Added:    {len(result.added)} features")
print(f"  Removed:  {len(result.removed)} features")
print(f"  Modified: {len(result.modified)} features")
print(f"  Unchanged: {len(result.unchanged)} features")
