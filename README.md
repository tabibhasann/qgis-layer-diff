# qgis-layer-diff 🔄

> Visual diff for vector layers in QGIS — a "git diff" for map data.

Pick two versions of a vector layer and instantly see what was **added, removed, and modified** — geometry changes on the map and attribute changes field-by-field — with an exportable report.

![License](https://img.shields.io/badge/License-GPL--2.0-blue.svg)

## Quickstart

1. Install via QGIS Plugin Manager (experimental first)
2. Click the Layer Diff toolbar button
3. Select Layer A (before) and Layer B (after)
4. Optionally pick a key field for matching
5. Click "Compute Diff"

## Features

- **Key-based matching** (by ID field) or **geometry-based matching** (with tolerance)
- **Styled result layers**: green (added), red (removed), amber (modified)
- **Interactive table**: click a row to flash/zoom to the feature, see old→new values
- **Export reports**: HTML and CSV
- **CRS handling**: auto-reprojects if layers use different CRS

## Development

The diff logic lives in `core/` — pure Python with **no QGIS imports**, fully testable:

```bash
PYTHONPATH=. python -m pytest test/ -v
```

## License

GPL-2.0-or-later (required for QGIS plugins)
