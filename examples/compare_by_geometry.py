#!/usr/bin/env python3
"""compare_by_geometry.py — Compare two vector layers by geometry matching."""
from qgis.core import QgsVectorLayer
from qgis_layer_diff import compare_layers

# Load layers
old_layer = QgsVectorLayer("data/old_buildings.shp", "Old Buildings", "ogr")
new_layer = QgsVectorLayer("data/new_buildings.shp", "New Buildings", "ogr")

# Compare by geometry (uses R-tree spatial indexing)
result = compare_layers(
    old_layer=old_layer,
    new_layer=new_layer,
    match_by="geometry",
    tolerance=0.5,  # meters
)

print(f"Geometry-based comparison:")
print(f"  Added:    {len(result.added)}")
print(f"  Removed:  {len(result.removed)}")
print(f"  Modified: {len(result.modified)} (geometry changed)")
print(f"  Unchanged: {len(result.unchanged)}")
