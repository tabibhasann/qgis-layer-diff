# Architecture

```
qgis-layer-diff
├── plugin.py                  # Main QGIS plugin class — hooks into QGIS toolbar/menu
├── diff_dock.py               # QDockWidget UI — layer pickers, options, results table, export
├── metadata.txt               # QGIS plugin metadata (version, author, min QGIS version)
├── core/
│   ├── models.py              # FeatureRecord, FieldChange, ModifiedFeature, DiffResult
│   ├── differ.py              # compute_diff() — orchestrates matching + comparison
│   ├── matching.py            # match_by_key() + match_by_geometry() (shapely STRtree)
│   └── report.py              # to_html() + to_csv() report generators
├── test/
│   ├── test_differ.py         # compute_diff tests (added/removed/modified/ignore_fields/dupes)
│   ├── test_matching.py       # match_by_key + match_by_geometry tests
│   ├── test_report.py         # HTML/CSV report tests
│   └── test_dock_logic.py     # Dock widget logic tests (mocked QGIS)
└── resources/
    └── icons/icon.svg
```

## Data Flow

```
QGIS User
    │
    ▼
plugin.py → DiffDock (QDockWidget)
    │
    ├──► Layer A / Layer B pickers (QgsMapLayerComboBox)
    ├──► Add PostGIS Layer button → QgsDataSourceUri dialog
    │
    ├──► Options:
    │       ├── Compare geometry (checkbox)
    │       ├── Compare attributes (checkbox)
    │       ├── Geometry tolerance (QDoubleSpinBox, 0–1000000 CRS units)
    │       ├── Ignore fields (QLineEdit, comma-separated)
    │       └── Summary-only report (checkbox)
    │
    ├──► Compute Diff button
    │       │
    │       ▼
    │    _layer_to_records() → FeatureRecord[]
    │       │  (reprojects if CRS mismatch, filters ignore_fields)
    │       │
    │       ▼
    │    compute_diff(records_a, records_b, key, tolerance, ignore_fields)
    │       │
    │       ├── match_by_key()       ← if key field selected
    │       └── match_by_geometry()  ← shapely STRtree + Hausdorff distance
    │               │
    │               ▼
    │           DiffResult (added, removed, modified, unchanged)
    │
    ├──► Results table (modified features, field changes)
    ├──► Styled result layers (green=added, red=removed, orange=modified)
    └──► Export HTML / CSV
```

## Key Design Decisions

- **Pure-logic core**: `core/` has zero QGIS imports — all diff logic is testable without QGIS.
- **Shapely STRtree**: O(n log n) spatial indexing for geometry-based matching.
- **Tolerance matching**: Hausdorff distance ≤ tolerance for approximate geometry equality.
- **Ignore fields**: Excludes specified fields from attribute comparison (e.g., `updated_at`).
- **Summary-only reports**: HTML report can omit per-feature details for quick overviews.
- **PostGIS support**: Dialog to connect to PostGIS and add layer directly to the project.
- **Duplicate key detection**: `match_by_key` reports duplicate keys, uses first occurrence.
