# CHANGELOG

All notable changes to qgis-layer-diff are documented here.
This project follows [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Fixed
- Layer pickers now use `QgsMapLayerComboBox`, matching the QGIS API used by
  `setFilters()` and `currentLayer()`.
- Release workflow now uses supported `qgis-plugin-ci` 2.x commands for packaging
  and QGIS Plugin Repository publishing.

### Added
- Packaging scripts stage the root-level plugin into the `qgis_layer_diff/`
  install directory before running `qgis-plugin-ci`.

## [0.2.0] - 2026-06-16

### Fixed
- **LICENSE is now GPL-2.0-or-later** (was MIT, would be rejected by QGIS Plugin Repository)
- Duplicate `[general]` header in `metadata.txt` removed
- Point and line result layers now get proper colored symbols (`QgsMarkerSymbol` /
  `QgsLineSymbol`) instead of an invisible default renderer
- Dock now uses `Qt.RightDockWidgetArea` constant instead of magic number `2`
- Removed unused `QgsApplication` import
- Unused `icon_path` variable in dock no longer leaks

### Added
- **CRS mismatch warning** — users are notified when layers have different or invalid CRS
- **Field-by-field detail view** below the main results table; clicking a modified row
  populates a per-field old → new breakdown with red/green tints and a geometry-change
  row when applicable
- HTML escaping in reports (XSS safety)
- `help/index.html` user guide
- New tests for schema mismatch, progress callback, geometry tolerance on polygons,
  and HTML/CSV escaping edge cases
- `qgis-plugin-ci` is now used to lint, package, and (optionally) publish the plugin

### Changed
- Release workflow uses `qgis-plugin-ci` instead of a raw `zip` command
- README badges and URLs updated to `tabibhasann` (consistent with metadata.txt)
- CI now runs ruff + pytest on every push and PR

## [0.1.0] - 2025-05-31

### Added
- Initial release
- Key-based and geometry-based feature matching
- R-tree (STRtree) accelerated geometry matching with optional tolerance
- Added/removed/modified/unchanged result sets
- Styled memory result layers
- Interactive results table (click to flash + zoom)
- HTML and CSV report export
- CRS auto-reprojection
