"""Tests for the core differ — pure Python, no QGIS needed."""

from __future__ import annotations

from core.differ import compute_diff
from core.matching import match_by_geometry, match_by_key
from core.models import DiffResult, FeatureRecord, FieldChange, ModifiedFeature


def make_record(key: str, attrs: dict | None = None, wkt: str = "") -> FeatureRecord:
    return FeatureRecord(key=key, attrs=attrs or {}, wkt=wkt)


class TestMatchingByKey:
    def test_exact_match(self):
        a = [make_record("1"), make_record("2"), make_record("3")]
        b = [make_record("2"), make_record("3"), make_record("4")]
        result = match_by_key(a, b)
        assert len(result["matched"]) == 2
        assert len(result["only_a"]) == 1
        assert len(result["only_b"]) == 1
        assert result["only_a"][0].key == "1"
        assert result["only_b"][0].key == "4"

    def test_empty_lists(self):
        result = match_by_key([], [])
        assert len(result["matched"]) == 0
        assert len(result["only_a"]) == 0
        assert len(result["only_b"]) == 0


class TestMatchingByGeometry:
    def test_equal_points(self):
        a = [FeatureRecord(key="a", attrs={}, wkt="POINT(0 0)")]
        b = [FeatureRecord(key="b", attrs={}, wkt="POINT(0 0)")]
        result = match_by_geometry(a, b, tolerance=0)
        assert len(result["matched"]) == 1
        assert len(result["only_a"]) == 0
        assert len(result["only_b"]) == 0

    def test_different_points(self):
        a = [FeatureRecord(key="a", attrs={}, wkt="POINT(0 0)")]
        b = [FeatureRecord(key="b", attrs={}, wkt="POINT(1 1)")]
        result = match_by_geometry(a, b, tolerance=0)
        assert len(result["matched"]) == 0
        assert len(result["only_a"]) == 1
        assert len(result["only_b"]) == 1

    def test_with_tolerance(self):
        a = [FeatureRecord(key="a", attrs={}, wkt="POINT(0 0)")]
        b = [FeatureRecord(key="b", attrs={}, wkt="POINT(0.00001 0)")]
        result = match_by_geometry(a, b, tolerance=0.001)
        assert len(result["matched"]) == 1


class TestComputeDiff:
    def test_added_removed(self):
        a = [
            FeatureRecord(key="1", attrs={"name": "A"}, wkt="POINT(0 0)"),
            FeatureRecord(key="2", attrs={"name": "B"}, wkt="POINT(1 1)"),
        ]
        b = [
            FeatureRecord(key="2", attrs={"name": "B"}, wkt="POINT(1 1)"),
            FeatureRecord(key="3", attrs={"name": "C"}, wkt="POINT(2 2)"),
        ]
        result = compute_diff(a, b, key="key")
        assert len(result.added) == 1
        assert result.added[0].key == "3"
        assert len(result.removed) == 1
        assert result.removed[0].key == "1"
        assert len(result.modified) == 0
        assert result.unchanged_count == 1

    def test_modified_attributes(self):
        a = [FeatureRecord(key="1", attrs={"name": "Old Name"}, wkt="POINT(0 0)")]
        b = [FeatureRecord(key="1", attrs={"name": "New Name"}, wkt="POINT(0 0)")]
        result = compute_diff(a, b, key="key")
        assert len(result.modified) == 1
        assert result.modified[0].field_changes[0].old == "Old Name"
        assert result.modified[0].field_changes[0].new == "New Name"

    def test_modified_geometry(self):
        a = [FeatureRecord(key="1", attrs={}, wkt="POINT(0 0)")]
        b = [FeatureRecord(key="1", attrs={}, wkt="POINT(1 1)")]
        result = compute_diff(a, b, key="key", compare_attributes=False)
        assert len(result.modified) == 1
        assert result.modified[0].geometry_changed is True

    def test_unchanged(self):
        a = [FeatureRecord(key="1", attrs={"x": 1}, wkt="POINT(0 0)")]
        b = [FeatureRecord(key="1", attrs={"x": 1}, wkt="POINT(0 0)")]
        result = compute_diff(a, b, key="key")
        assert result.unchanged_count == 1
        assert len(result.modified) == 0

    def test_summary_totals(self):
        a = [FeatureRecord(key=str(i), attrs={}, wkt=f"POINT({i} {i})") for i in range(5)]
        b = [FeatureRecord(key=str(i), attrs={}, wkt=f"POINT({i} {i})") for i in range(2, 8)]
        result = compute_diff(a, b, key="key")
        s = result.summary
        assert s["added"] == 3  # keys 5, 6, 7
        assert s["removed"] == 2  # keys 0, 1
        assert s["unchanged"] == 3  # keys 2, 3, 4 unchanged


class TestIgnoreFields:
    def test_ignore_fields_excludes_from_comparison(self):
        a = [FeatureRecord(key="1", attrs={"name": "A", "updated_at": "2024-01-01"}, wkt="POINT(0 0)")]
        b = [FeatureRecord(key="1", attrs={"name": "A", "updated_at": "2024-06-01"}, wkt="POINT(0 0)")]
        result = compute_diff(a, b, key="key", ignore_fields={"updated_at"})
        assert result.unchanged_count == 1
        assert len(result.modified) == 0

    def test_ignore_fields_still_detects_other_changes(self):
        a = [FeatureRecord(key="1", attrs={"name": "Old", "updated_at": "2024-01-01"}, wkt="POINT(0 0)")]
        b = [FeatureRecord(key="1", attrs={"name": "New", "updated_at": "2024-06-01"}, wkt="POINT(0 0)")]
        result = compute_diff(a, b, key="key", ignore_fields={"updated_at"})
        assert len(result.modified) == 1
        assert result.modified[0].field_changes[0].field == "name"


class TestDuplicateKeys:
    def test_duplicate_keys_reported(self):
        a = [
            FeatureRecord(key="1", attrs={"name": "A"}, wkt="POINT(0 0)"),
            FeatureRecord(key="1", attrs={"name": "A2"}, wkt="POINT(1 1)"),
        ]
        b = [FeatureRecord(key="1", attrs={"name": "A"}, wkt="POINT(0 0)")]
        result = compute_diff(a, b, key="key")
        assert result.unchanged_count == 1
        assert len(result.modified) == 0
        assert len(result.removed) == 1

    def test_duplicate_keys_warning_surfaced(self):
        a = [
            FeatureRecord(key="1", attrs={"name": "A"}, wkt="POINT(0 0)"),
            FeatureRecord(key="1", attrs={"name": "A2"}, wkt="POINT(1 1)"),
        ]
        b = [FeatureRecord(key="1", attrs={"name": "A"}, wkt="POINT(0 0)")]
        result = compute_diff(a, b, key="key")
        assert len(result.warnings) > 0
        assert "Duplicate key" in result.warnings[0]

    def test_no_warnings_without_duplicates(self):
        a = [FeatureRecord(key="1", attrs={}, wkt="POINT(0 0)")]
        b = [FeatureRecord(key="1", attrs={}, wkt="POINT(0 0)")]
        result = compute_diff(a, b, key="key")
        assert len(result.warnings) == 0


class TestReport:
    def test_html_contains_summary(self):
        from core.report import to_html

        result = DiffResult()
        html = to_html(result)
        assert "Layer Diff Report" in html
        assert "Added" in html

    def test_html_summary_only(self):
        from core.report import to_html

        result = DiffResult(
            modified=[
                ModifiedFeature(
                    key="1",
                    geometry_changed=True,
                    field_changes=[FieldChange("name", "Old", "New")],
                )
            ],
        )
        html = to_html(result, summary_only=True)
        assert "Modified Features" not in html
        assert "~1 Modified" in html

    def test_html_with_details(self):
        from core.report import to_html

        result = DiffResult(
            modified=[
                ModifiedFeature(
                    key="1",
                    geometry_changed=True,
                    field_changes=[FieldChange("name", "Old", "New")],
                )
            ],
        )
        html = to_html(result, summary_only=False)
        assert "Modified Features" in html
        assert "Old" in html
        assert "New" in html

    def test_html_with_added_removed(self):
        from core.report import to_html

        result = DiffResult(
            added=[FeatureRecord(key="2", attrs={}, wkt="POINT(2 2)")],
            removed=[FeatureRecord(key="0", attrs={}, wkt="POINT(0 0)")],
        )
        html = to_html(result, summary_only=False)
        assert "Added Features" in html
        assert "Removed Features" in html
        assert ">2<" in html
        assert ">0<" in html

    def test_html_with_warnings(self):
        from core.report import to_html

        result = DiffResult(warnings=["Duplicate key(s) found: 1"])
        html = to_html(result, summary_only=False)
        assert "Warnings" in html
        assert "Duplicate key" in html

    def test_csv_empty(self):
        from core.report import to_csv

        result = DiffResult()
        csv = to_csv(result)
        assert csv.startswith("type,key,field,old_value,new_value")
