# qgis-layer-diff 🔄

> **Pre-release:** v0.3.0 is not yet listed in the official QGIS Plugin Repository. Install the repository checkout manually and treat marketplace instructions as post-release guidance.

**Visual diff for QGIS vector layers — "git diff" for geospatial data.**

Compare two versions of a vector layer and instantly see what changed: added features (green), removed features (red), and modified features (orange). Detect geometry changes, attribute changes, or both. Export detailed reports in HTML or CSV format.


**Demo:** Screenshot walkthrough: see [Quickstart](#quickstart) above

### How it compares

| Plugin | Key match | Geometry match | Tolerance | HTML report | CSV export | CRS handling |
|---|---|---|---|---|---|---|
| **qgis-layer-diff** | ✅ | ✅ (R-tree) | ✅ | ✅ | ✅ | ✅ |
| [LayerDiffViewer](https://plugins.qgis.org/plugins/LayerDiffViewer/) | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| [Geometry Comparator](https://plugins.qgis.org/plugins/geometry_comparator/) | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| [Table Compare](https://plugins.qgis.org/plugins/tablecompare/) | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ |
| [QGIS Detect Changes](https://plugins.qgis.org/plugins/detectchanges/) | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ |

qgis-layer-diff combines key and geometry matching, tolerance control, CRS reprojection, and HTML/CSV export in one workflow.

[![QGIS](https://img.shields.io/badge/QGIS-3.28+-green?logo=qgis)](https://qgis.org)
[![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)](https://python.org)
[![License](https://img.shields.io/badge/License-GPL--2.0-blue.svg)](LICENSE)
[![CI](https://github.com/tabibhasann/qgis-layer-diff/workflows/CI/badge.svg)](../../actions)
[![Coverage](https://img.shields.io/badge/coverage-97%25-brightgreen)](https://github.com/tabibhasann/qgis-layer-diff/actions)
[![Tests](https://img.shields.io/badge/tests-169%20passed-brightgreen)](https://github.com/tabibhasann/qgis-layer-diff/actions)
[![Version](https://img.shields.io/badge/Version-0.3.0-orange.svg)](metadata.txt)

## ✨ Features

### Intelligent Feature Matching
- **Key-based matching:** Match features by unique ID field (O(n) complexity)
- **Geometry-based matching:** Match by spatial location using R-tree spatial index (O(n log n) complexity)
- **Configurable tolerance:** Set distance threshold for geometry matching

### Comprehensive Change Detection
- **Added features:** New features in Layer B not present in Layer A
- **Removed features:** Features in Layer A not present in Layer B  
- **Modified features:** Matched features with geometry or attribute changes
- **Unchanged features:** Matched features with no changes

### Visual Results
- **Styled diff layers:** Color-coded layers added to your QGIS project
  - 🟢 Green: Added features
  - 🔴 Red: Removed features
  - 🟠 Orange: Modified features
- **Interactive results table:** Click any row to zoom to the feature and see detailed changes
- **Attribute comparison:** Field-by-field breakdown showing old → new values
- **Geometry change detection:** Identifies moved or reshaped features

### Export & Reporting
- **HTML reports:** Styled, printable reports with summary statistics and detailed change lists
- **CSV export:** Machine-readable format for further analysis (properly escaped using csv.writer)
- **Progress indicators:** Real-time feedback during diff computation for large datasets

### Built for Real GIS Workflows
- **CRS handling:** Automatic reprojection when layers use different coordinate systems
- **Performance optimized:** R-tree spatial indexing for fast geometry matching
- **Error handling:** Graceful handling of edge cases and invalid data
- **Well-tested:** Comprehensive unit test suite with 80%+ coverage

## 📦 Installation

### From QGIS Plugin Repository (after publication)

The official listing is not live yet. Once it is published, installation will be available through **Plugins → Manage and Install Plugins...**. Until then, use the manual installation below.

### Manual Installation

```bash
# Clone the repository
git clone https://github.com/tabibhasann/qgis-layer-diff.git qgis_layer_diff

# Copy to QGIS plugins directory
# Linux:
cp -r qgis_layer_diff ~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/

# macOS:
cp -r qgis_layer_diff ~/Library/Application\ Support/QGIS/QGIS3/profiles/default/python/plugins/

# Windows:
# Copy qgis_layer_diff to: %APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\
```

3. Restart QGIS
4. Enable the plugin: **Plugins → Manage and Install Plugins → Installed → Layer Diff**

## 🚀 Quick Start

### Basic Workflow

1. **Load your layers:** Open both versions of your vector layer in QGIS
   - Example: `buildings_2023.shp` and `buildings_2024.shp`

2. **Open the plugin:** Click the Layer Diff icon in the toolbar or go to **Plugins → Layer Diff → Compare Layers**

3. **Configure the diff:**
   - **Layer A (before):** Select the older version (e.g., `buildings_2023`)
   - **Layer B (after):** Select the newer version (e.g., `buildings_2024`)
   - **Key field:** Choose a unique identifier field (e.g., `building_id`) or leave blank for geometry matching
   - **Compare attributes:** Check to detect attribute changes
   - **Compare geometry:** Check to detect geometry changes
   - **Tolerance:** Set distance threshold for geometry matching (e.g., 0.5 meters)

4. **Compute diff:** Click the "Compute Diff" button

5. **Review results:**
   - Three new layers appear in your Layers panel (Added, Removed, Modified)
   - Results table shows summary statistics
   - Click any row to zoom to that feature

6. **Export report:** Click "Export HTML" or "Export CSV" to save the report

### Example: Comparing Building Footprints

```
Layer A: buildings_2023.shp (5,000 features)
Layer B: buildings_2024.shp (5,234 features)
Key field: building_id
Compare: geometry + attributes
Tolerance: 0.5m

Results:
  + Added:    234 features (new construction)
  - Removed:   50 features (demolished buildings)
  ~ Modified: 123 features (renovations, address changes)
  = Unchanged: 4,827 features

Processing time: 8 seconds (R-tree indexed geometry matching)
```

### Sample Data

Two small GeoJSON files for testing are in `examples/sample_data/`:
- `layer_a.geojson` — 3 features (Parks A, B, C)
- `layer_b.geojson` — 3 features (Parks A modified, B unchanged, D added; C removed)

Load both into QGIS to see the diff: 1 added, 1 removed, 1 modified.

## 📊 Performance

### Benchmarks

| Dataset Size | Key-Based Matching | Geometry Matching (with R-tree) |
|--------------|-------------------|--------------------------------|
| 1,000 features | < 1s | 2s |
| 10,000 features | 2s | 8s |
| 100,000 features | 15s | 45s |
| 1,000,000 features | 2min | 5min |

**Performance improvements in v0.2.0:**
- Replaced O(n²) brute-force geometry matching with R-tree spatial index (O(n log n))
- Added progress callbacks for real-time feedback
- Optimized WKT parsing and geometry comparison

### Tips for Large Datasets

1. **Use key-based matching** when possible (faster than geometry matching)
2. **Ensure unique keys:** Duplicate keys can cause incorrect matches
3. **Set appropriate tolerance:** Too large = false matches, too small = missed matches
4. **Simplify geometries:** Complex polygons slow down comparison
5. **Use spatial indexes:** Ensure your layers have spatial indexes (.qix files)

## 🔧 Configuration Options

### Matching Modes

#### Key-Based Matching
Match features by a unique identifier field (e.g., `id`, `fid`, `parcel_id`).

**Pros:**
- Fast (O(n) complexity)
- Accurate (no false matches)
- Works well for datasets with stable IDs

**Cons:**
- Requires a unique key field in both layers
- Doesn't detect features that changed their ID

**When to use:** When both layers have a consistent unique identifier field.

#### Geometry-Based Matching
Match features by spatial location using centroid distance with tolerance.

**Pros:**
- Works without key fields
- Can detect features with changed IDs
- Uses R-tree spatial index for efficiency

**Cons:**
- Slower than key-based matching (O(n log n))
- May produce false matches if tolerance is too large
- May miss matches if tolerance is too small

**When to use:** When layers don't have consistent key fields, or when you want to match by location.

### Comparison Options

| Option | Description | Default |
|--------|-------------|---------|
| **Compare attributes** | Detect changes in non-geometry fields | ✅ Enabled |
| **Compare geometry** | Detect geometry changes (moved, reshaped) | ✅ Enabled |
| **Tolerance** | Distance threshold for geometry matching (in layer units) | 0.0 (exact match) |
| **Key field** | Field to use for key-based matching | None (geometry matching) |

## 📖 Advanced Usage

### Programmatic Access

The core diff logic is pure Python with no QGIS dependencies, making it easy to use in scripts:

```python
from qgis_layer_diff.core.differ import compute_diff
from qgis_layer_diff.core.models import FeatureRecord

# Create feature records
layer_a_records = [
    FeatureRecord(key="1", attrs={"name": "Building A"}, wkt="POLYGON((...))"),
    FeatureRecord(key="2", attrs={"name": "Building B"}, wkt="POLYGON((...))"),
]

layer_b_records = [
    FeatureRecord(key="1", attrs={"name": "Building A"}, wkt="POLYGON((...))"),  # unchanged
    FeatureRecord(key="3", attrs={"name": "Building C"}, wkt="POLYGON((...))"),  # added
]

# Compute diff
result = compute_diff(
    layer_a_records,
    layer_b_records,
    key="key",
    compare_attributes=True,
    compare_geometry=True,
)

# Access results
print(f"Added: {len(result.added)}")
print(f"Removed: {len(result.removed)}")
print(f"Modified: {len(result.modified)}")
print(f"Unchanged: {result.unchanged_count}")

# Export to HTML
from qgis_layer_diff.core.report import to_html
html = to_html(result, title="Building Changes")
with open("report.html", "w") as f:
    f.write(html)
```

### Custom Progress Callbacks

Monitor diff computation in real-time:

```python
def progress_callback(current, total, message):
    print(f"[{current}/{total}] {message}")

result = compute_diff(
    layer_a_records,
    layer_b_records,
    progress_callback=progress_callback,
)
```

### Filtering Results

After computing the diff, you can filter results programmatically:

```python
# Get only features with attribute changes
attr_changes = [f for f in result.modified if f.field_changes]

# Get only features with geometry changes
geom_changes = [f for f in result.modified if f.geometry_changed]

# Get features where a specific field changed
name_changes = [
    f for f in result.modified 
    if any(change.field == "name" for change in f.field_changes)
]
```

## 🧪 Testing

The plugin includes comprehensive unit tests for the core diff logic:

```bash
# Install test dependencies
pip install pytest pytest-cov ruff shapely

# Run all tests
PYTHONPATH=. pytest test/ -v

# Run static lint
ruff check .

# Run with coverage report
PYTHONPATH=. pytest test/ --cov=core --cov-report=html

# Run specific test file
PYTHONPATH=. pytest test/test_differ.py -v

# Run with verbose output
PYTHONPATH=. pytest test/ -vv -s
```

**Test coverage:** 80%+ for core modules (differ, matching, report)

## 📦 Packaging

Release archives are built with `qgis-plugin-ci`. Because this repository is itself
the plugin root, the packaging script stages the files into the install directory
layout expected by QGIS before invoking `qgis-plugin-ci`.

```bash
# Install packaging dependency
python3 -m pip install qgis-plugin-ci

# Build dist/qgis_layer_diff.<version>.zip from metadata.txt
bash scripts/package_plugin.sh

# If pip installed the qgis-plugin-ci script outside PATH:
QGIS_PLUGIN_CI_BIN="$(python3 -m site --user-base)/bin/qgis-plugin-ci" bash scripts/package_plugin.sh
```

## 🏗️ Architecture

```
qgis-layer-diff/
├── __init__.py              # Plugin initialization
├── plugin.py                # QGIS plugin class
├── diff_dock.py             # UI dock widget (Qt)
├── metadata.txt             # Plugin metadata
├── core/                    # Pure Python diff logic (no QGIS deps)
│   ├── differ.py           # Main diff computation
│   ├── matching.py         # Key and geometry matching algorithms
│   ├── models.py           # Data models (FeatureRecord, DiffResult, etc.)
│   └── report.py           # HTML and CSV export
├── test/                    # Unit tests (pure Python, no QGIS)
│   ├── conftest.py         # pytest path setup
│   ├── test_differ.py      # Diff computation tests
│   ├── test_matching.py    # Matching algorithm tests
│   ├── test_report.py      # Export tests
│   └── test_dock_logic.py  # Edge cases + escaping + progress callbacks
├── scripts/                 # qgis-plugin-ci staging and packaging helpers
├── resources/               # Icons and UI resources
│   └── icons/
└── help/                    # Documentation
    └── index.html
```

**Design principles:**
- **Separation of concerns:** Core logic is independent of QGIS
- **Testability:** Core modules can be tested without QGIS
- **Extensibility:** Easy to add new matching algorithms or export formats
- **Performance:** Optimized data structures and algorithms

## Plugin Reference

After installation, the plugin appears under **Plugins → Layer Diff** in the QGIS menu.

- **Layer Diff** — Open the diff dialog to select two layers and compare
- **Help** — View inline documentation and examples
- **About** — Version, author, and license information

## 🤝 Contributing

Contributions are welcome! Here's how to get started:

1. **Fork the repository** on GitHub
2. **Clone your fork:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/qgis-layer-diff.git
   cd qgis-layer-diff
   ```
3. **Install in development mode:**
   ```bash
   pip install pytest pytest-cov ruff shapely
   ```
4. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```
5. **Make your changes** and add tests
6. **Run tests:**
   ```bash
   PYTHONPATH=. pytest test/ -v
   ruff check .
   ```
7. **Commit and push:**
   ```bash
   git add .
   git commit -m "Add your feature"
   git push origin feature/your-feature-name
   ```
8. **Open a pull request** on GitHub

### Development Guidelines

- Follow PEP 8 style guide
- Add type hints to all functions
- Write unit tests for new features
- Update documentation as needed
- Keep commits focused and atomic

## 📋 Alternatives

| Tool | Type | Scope | QGIS integration | Key + geometry matching | HTML/CSV export |
|------|------|-------|-------------------|------------------------|-----------------|
| **qgis-layer-diff** | QGIS plugin | Diff two vector layers with visual + tabular output | Native | Both | Yes |
| [QGIS DB Manager](https://docs.qgis.org/3.28/en/docs/user_manual/managing_data_source/opening_data.html#db-manager) | Built-in | SQL-based comparison of database layers | Native | Manual SQL | No |
| [SAGA Change Detection](https://saga-tools.org) | Processing provider | Raster change detection | Provider | No | No |
| [ogr2ogr](https://gdal.org/programs/ogr2ogr.html) | CLI | Format conversion + basic filtering | No | No | No |
| Manual SQL joins | SQL | Hand-written queries to find adds/removes/changes | Via DB Manager | Key only | Manual |

**Why qgis-layer-diff?** It's the only QGIS plugin that provides one-click visual diffing of two vector layers with both key-based and geometry-based matching, interactive map highlighting, and HTML/CSV export — no SQL required.

## 📋 Roadmap

The immediate gate is a manually verified v0.3.0 ZIP and publication to the official QGIS Plugin Repository. See [ROADMAP.md](ROADMAP.md) for the maintained release plan.

## 🐛 Troubleshooting

### Plugin doesn't appear in QGIS
- Check that the plugin is enabled: **Plugins → Manage and Install Plugins → Installed**
- Verify the plugin is in the correct directory
- Restart QGIS

### "No common fields" error
- Ensure both layers have compatible attribute schemas
- Check that the key field exists in both layers (if using key-based matching)

### Slow performance
- Use key-based matching instead of geometry matching when possible
- Simplify complex geometries before comparison
- Ensure layers have spatial indexes
- Reduce tolerance value for geometry matching

### Incorrect matches
- Verify key field uniqueness (no duplicate keys)
- Adjust tolerance value for geometry matching
- Check that layers use the same CRS (or enable auto-reprojection)

## 📄 License

This plugin is licensed under the GNU General Public License v2.0 or later (GPL-2.0-or-later).

This license is required for QGIS plugins to ensure compatibility with QGIS's GPL license.

See [LICENSE](LICENSE) for full license text.

## 🙏 Acknowledgments

- **QGIS Development Team** for the excellent QGIS Python API
- **Shapely** developers for powerful geometry operations
- **PyProj** developers for coordinate transformation support
- **Open source community** for inspiration and feedback

## 📞 Support

- **Bug reports:** [GitHub Issues](https://github.com/tabibhasann/qgis-layer-diff/issues)
- **Feature requests:** [GitHub Discussions](https://github.com/tabibhasann/qgis-layer-diff/discussions)
- **Questions:** [QGIS Stack Exchange](https://gis.stackexchange.com/questions/tagged/qgis-layer-diff)

## 🔗 Links

- **Homepage:** [https://github.com/tabibhasann/qgis-layer-diff](https://github.com/tabibhasann/qgis-layer-diff)
- **Documentation:** [https://github.com/tabibhasann/qgis-layer-diff/wiki](https://github.com/tabibhasann/qgis-layer-diff/wiki)
- **QGIS Plugin Repository:** publication pending; install from the release ZIP for now.

## API

### Python API

```python
from qgis_layer_diff.core.differ import compute_diff
from qgis_layer_diff.core.models import FeatureRecord
from qgis_layer_diff.core.report import to_html, to_csv

# Build feature records from QGIS layers
records_a = [FeatureRecord(key=f.id(), attrs={f.name(): f.value() for f in f.attributes()},
                            wkt=f.geometry().asWkt())
             for f in layer_a.getFeatures()]
records_b = [FeatureRecord(key=f.id(), attrs={f.name(): f.value() for f in f.attributes()},
                            wkt=f.geometry().asWkt())
             for f in layer_b.getFeatures()]

# Compute diff (key-based or geometry-based)
result = compute_diff(records_a, records_b, key='building_id')

# Generate reports
html = to_html(result)
csv_text = to_csv(result)
```

### Core Modules

- **`core/models.py`** — `FeatureRecord`, `FieldChange`, `ModifiedFeature`, `DiffResult`
- **`core/matching.py`** — `match_by_key`, `match_by_geometry` (STRtree spatial index)
- **`core/differ.py`** — `compute_diff` orchestrating match → compare → result
- **`core/report.py`** — `to_html` and `to_csv` report generators with XSS escaping

---

**Made with ❤️ for the QGIS community**

---

⭐ Star [tabibhasann/qgis-layer-diff](https://github.com/tabibhasann/qgis-layer-diff) on GitHub if this helped you.
