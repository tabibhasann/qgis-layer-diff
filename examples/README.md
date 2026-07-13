# qgis-layer-diff examples

Example scripts and usage patterns for the Layer Diff QGIS plugin.

## Files

- [`compare_by_id.py`](compare_by_id.py) — Compare two layers by a key field
- [`compare_by_geometry.py`](compare_by_geometry.py) — Compare two layers by geometry
- [`batch_compare.py`](batch_compare.py) — Batch compare multiple layer pairs
- [`export_report.py`](export_report.py) — Export a diff report as HTML

## Quick Start

In QGIS:
1. Install the Layer Diff plugin
2. Open two vector layers
3. Go to Plugins → Layer Diff
4. Select the old and new layers
5. Choose matching method (key field or geometry)
6. Click "Compare"

Or via the QGIS Python console:

```python
from qgis_layer_diff import compare_layers
result = compare_layers(old_layer, new_layer, key_field='id')
print(f"Added: {len(result.added)}, Removed: {len(result.removed)}, Modified: {len(result.modified)}")
```
