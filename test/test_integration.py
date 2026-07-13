"""Integration tests for qgis_layer_diff core pipeline."""

from __future__ import annotations

import json
from pathlib import Path

from core.differ import compute_diff
from core.models import FeatureRecord
from core.report import to_csv, to_html


def _make_geojson(features: list[dict]) -> dict:
    return {"type": "FeatureCollection", "features": features}


def _feature(fid: int, name: str, coords: list[float]) -> dict:
    return {
        "type": "Feature",
        "id": fid,
        "geometry": {"type": "Point", "coordinates": coords},
        "properties": {"id": fid, "name": name},
    }


class TestEndToEndDiff:
    """Full pipeline: GeoJSON → records → diff → report."""

    def test_full_pipeline_added_removed_modified(self, tmp_path: Path) -> None:
        before = _make_geojson([
            _feature(1, "A", [0, 0]),
            _feature(2, "B", [1, 1]),
            _feature(3, "C", [2, 2]),
        ])
        after = _make_geojson([
            _feature(1, "A", [0, 0]),       # unchanged
            _feature(2, "B2", [1, 1]),      # attribute changed
            _feature(4, "D", [3, 3]),       # added
        ])

        before_path = tmp_path / "before.geojson"
        after_path = tmp_path / "after.geojson"
        before_path.write_text(json.dumps(before))
        after_path.write_text(json.dumps(after))

        records_a = [
            FeatureRecord.from_dict(f["id"], f["properties"], f["geometry"]["coordinates"])
            for f in before["features"]
        ]
        records_b = [
            FeatureRecord.from_dict(f["id"], f["properties"], f["geometry"]["coordinates"])
            for f in after["features"]
        ]

        result = compute_diff(records_a, records_b, key="id")

        assert len(result.added) == 1
        assert len(result.removed) == 1
        assert len(result.modified) == 1
        assert result.unchanged_count == 1

    def test_html_report_from_diff(self, tmp_path: Path) -> None:
        records_a = [FeatureRecord(key="1", attrs={"name": "A"}, wkt="POINT (0 0)")]
        records_b = [FeatureRecord(key="1", attrs={"name": "B"}, wkt="POINT (0 0)")]
        result = compute_diff(records_a, records_b, key="id")

        html = to_html(result)
        assert "<html" in html.lower()
        assert "1 Modified" in html or "'modified': 1" in html or ">~1" in html

    def test_csv_report_from_diff(self, tmp_path: Path) -> None:
        records_a = [FeatureRecord(key="1", attrs={"name": "A"}, wkt="POINT (0 0)")]
        records_b = [FeatureRecord(key="1", attrs={"name": "B"}, wkt="POINT (0 0)")]
        result = compute_diff(records_a, records_b, key="id")

        csv_str = to_csv(result)
        assert "modified" in csv_str
        assert "name" in csv_str

    def test_empty_geojson_diff(self) -> None:
        result = compute_diff([], [])
        assert result.summary["total"] == 0
        assert len(result.warnings) == 0

    def test_large_diff_performance(self) -> None:
        records_a = [FeatureRecord(key=str(i), attrs={"v": i}, wkt=f"POINT ({i} {i})") for i in range(500)]
        records_b = [FeatureRecord(key=str(i), attrs={"v": i}, wkt=f"POINT ({i} {i})") for i in range(500)]
        result = compute_diff(records_a, records_b, key="id")
        assert result.unchanged_count == 500
        assert len(result.modified) == 0

    def test_diff_with_geometry_tolerance(self) -> None:
        records_a = [FeatureRecord(key="1", attrs={"name": "A"}, wkt="POINT (0 0)")]
        records_b = [FeatureRecord(key="1", attrs={"name": "A"}, wkt="POINT (0.0001 0.0001)")]
        result = compute_diff(records_a, records_b, key="id", geom_tolerance=0.001)
        # geom_tolerance affects matching, not comparison — with key matching, WKT is compared exactly
        assert len(result.modified) == 1
        assert result.modified[0].geometry_changed

    def test_diff_without_tolerance_detects_change(self) -> None:
        records_a = [FeatureRecord(key="1", attrs={"name": "A"}, wkt="POINT (0 0)")]
        records_b = [FeatureRecord(key="1", attrs={"name": "A"}, wkt="POINT (0.001 0.001)")]
        result = compute_diff(records_a, records_b, key="id", geom_tolerance=0.0)
        assert len(result.modified) == 1
        assert result.modified[0].geometry_changed
