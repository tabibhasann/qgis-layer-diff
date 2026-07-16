"""Comprehensive error path tests for qgis_layer_diff core modules.

Tests invalid inputs, edge cases, empty data, corrupt WKT,
duplicate keys, and error handling across all core modules.
"""

from core.differ import compute_diff
from core.matching import _geoms_equal, match_by_geometry, match_by_key
from core.models import DiffResult, FeatureRecord, FieldChange, ModifiedFeature
from core.report import to_csv, to_html


class TestModelErrorPaths:
    """Error tests for model dataclasses."""

    def test_feature_record_from_dict(self) -> None:
        rec = FeatureRecord.from_dict(42, {"name": "test"}, "POINT (0 0)")
        assert rec.key == "42"
        assert rec.attrs == {"name": "test"}

    def test_feature_record_from_dict_none_key(self) -> None:
        rec = FeatureRecord.from_dict(None, {}, "POINT (0 0)")
        assert rec.key == "None"

    def test_diff_result_empty_summary(self) -> None:
        result = DiffResult()
        s = result.summary
        assert s["added"] == 0
        assert s["removed"] == 0
        assert s["modified"] == 0
        assert s["unchanged"] == 0
        assert s["total"] == 0

    def test_diff_result_with_data_summary(self) -> None:
        result = DiffResult(
            added=[FeatureRecord(key="1", attrs={}, wkt="POINT (0 0)")],
            removed=[FeatureRecord(key="2", attrs={}, wkt="POINT (1 1)")],
            modified=[ModifiedFeature(key="3", geometry_changed=True)],
            unchanged_count=5,
        )
        s = result.summary
        assert s["total"] == 8

    def test_modified_feature_defaults(self) -> None:
        m = ModifiedFeature(key="test", geometry_changed=False)
        assert m.field_changes == []
        assert m.old_wkt == ""
        assert m.new_wkt == ""

    def test_field_change_equality(self) -> None:
        fc1 = FieldChange(field="name", old="A", new="B")
        fc2 = FieldChange(field="name", old="A", new="B")
        fc3 = FieldChange(field="name", old="A", new="C")
        assert fc1 == fc2
        assert fc1 != fc3


class TestMatchingErrorPaths:
    """Error tests for matching strategies."""

    def test_match_by_key_empty_lists(self) -> None:
        result = match_by_key([], [])
        assert result["matched"] == []
        assert result["only_a"] == []
        assert result["only_b"] == []

    def test_match_by_key_all_added(self) -> None:
        records_b = [FeatureRecord(key="1", attrs={}, wkt="POINT (0 0)")]
        result = match_by_key([], records_b)
        assert len(result["only_b"]) == 1
        assert result["matched"] == []

    def test_match_by_key_all_removed(self) -> None:
        records_a = [FeatureRecord(key="1", attrs={}, wkt="POINT (0 0)")]
        result = match_by_key(records_a, [])
        assert len(result["only_a"]) == 1
        assert result["matched"] == []

    def test_match_by_key_duplicate_keys_a(self) -> None:
        records_a = [
            FeatureRecord(key="1", attrs={"v": 1}, wkt="POINT (0 0)"),
            FeatureRecord(key="1", attrs={"v": 2}, wkt="POINT (1 1)"),
        ]
        records_b = [FeatureRecord(key="1", attrs={"v": 1}, wkt="POINT (0 0)")]
        result = match_by_key(records_a, records_b)
        assert len(result["duplicate_keys_a"]) == 1
        assert len(result["matched"]) == 1
        assert len(result["only_a"]) == 1

    def test_match_by_key_duplicate_keys_b(self) -> None:
        records_a = [FeatureRecord(key="1", attrs={"v": 1}, wkt="POINT (0 0)")]
        records_b = [
            FeatureRecord(key="1", attrs={"v": 1}, wkt="POINT (0 0)"),
            FeatureRecord(key="1", attrs={"v": 2}, wkt="POINT (1 1)"),
        ]
        result = match_by_key(records_a, records_b)
        assert len(result["duplicate_keys_b"]) == 1
        assert len(result["only_b"]) == 1

    def test_match_by_geometry_empty_b(self) -> None:
        records_a = [FeatureRecord(key="1", attrs={}, wkt="POINT (0 0)")]
        result = match_by_geometry(records_a, [])
        assert len(result["only_a"]) == 1
        assert result["matched"] == []

    def test_match_by_geometry_invalid_wkt_a(self) -> None:
        records_a = [FeatureRecord(key="1", attrs={}, wkt="NOT VALID WKT")]
        records_b = [FeatureRecord(key="2", attrs={}, wkt="POINT (0 0)")]
        result = match_by_geometry(records_a, records_b)
        assert len(result["only_a"]) == 1
        assert len(result["only_b"]) == 1

    def test_match_by_geometry_invalid_wkt_b(self) -> None:
        records_a = [FeatureRecord(key="1", attrs={}, wkt="POINT (0 0)")]
        records_b = [FeatureRecord(key="2", attrs={}, wkt="NOT VALID WKT")]
        result = match_by_geometry(records_a, records_b)
        assert len(result["only_a"]) == 1
        assert len(result["only_b"]) == 1

    def test_match_by_geometry_empty_wkt_a(self) -> None:
        records_a = [FeatureRecord(key="1", attrs={}, wkt="")]
        records_b = [FeatureRecord(key="2", attrs={}, wkt="POINT (0 0)")]
        result = match_by_geometry(records_a, records_b)
        assert len(result["only_a"]) == 1

    def test_geoms_equal_exact(self) -> None:
        from shapely import wkt as _wkt

        g1 = _wkt.loads("POINT (0 0)")
        g2 = _wkt.loads("POINT (0 0)")
        assert _geoms_equal(g1, g2, 0.0)

    def test_geoms_equal_different(self) -> None:
        from shapely import wkt as _wkt

        g1 = _wkt.loads("POINT (0 0)")
        g2 = _wkt.loads("POINT (1 1)")
        assert not _geoms_equal(g1, g2, 0.0)

    def test_geoms_equal_within_tolerance(self) -> None:
        from shapely import wkt as _wkt

        g1 = _wkt.loads("POINT (0 0)")
        g2 = _wkt.loads("POINT (0.001 0.001)")
        assert _geoms_equal(g1, g2, 0.01)

    def test_geoms_equal_outside_tolerance(self) -> None:
        from shapely import wkt as _wkt

        g1 = _wkt.loads("POINT (0 0)")
        g2 = _wkt.loads("POINT (1 1)")
        assert not _geoms_equal(g1, g2, 0.01)


class TestDifferErrorPaths:
    """Error tests for diff computation."""

    def test_compute_diff_empty_both(self) -> None:
        result = compute_diff([], [])
        assert result.summary["total"] == 0

    def test_compute_diff_empty_a(self) -> None:
        records_b = [FeatureRecord(key="1", attrs={}, wkt="POINT (0 0)")]
        result = compute_diff([], records_b, key="id")
        assert len(result.added) == 1
        assert len(result.removed) == 0

    def test_compute_diff_empty_b(self) -> None:
        records_a = [FeatureRecord(key="1", attrs={}, wkt="POINT (0 0)")]
        result = compute_diff(records_a, [], key="id")
        assert len(result.removed) == 1
        assert len(result.added) == 0

    def test_compute_diff_no_changes(self) -> None:
        records_a = [FeatureRecord(key="1", attrs={"name": "A"}, wkt="POINT (0 0)")]
        records_b = [FeatureRecord(key="1", attrs={"name": "A"}, wkt="POINT (0 0)")]
        result = compute_diff(records_a, records_b, key="id")
        assert result.unchanged_count == 1
        assert len(result.modified) == 0

    def test_compute_diff_attribute_change(self) -> None:
        records_a = [FeatureRecord(key="1", attrs={"name": "A"}, wkt="POINT (0 0)")]
        records_b = [FeatureRecord(key="1", attrs={"name": "B"}, wkt="POINT (0 0)")]
        result = compute_diff(records_a, records_b, key="id")
        assert len(result.modified) == 1
        assert not result.modified[0].geometry_changed
        assert len(result.modified[0].field_changes) == 1

    def test_compute_diff_geometry_change(self) -> None:
        records_a = [FeatureRecord(key="1", attrs={"name": "A"}, wkt="POINT (0 0)")]
        records_b = [FeatureRecord(key="1", attrs={"name": "A"}, wkt="POINT (1 1)")]
        result = compute_diff(records_a, records_b, key="id")
        assert len(result.modified) == 1
        assert result.modified[0].geometry_changed

    def test_compute_diff_ignore_fields(self) -> None:
        records_a = [FeatureRecord(key="1", attrs={"name": "A", "updated": "2024-01"}, wkt="POINT (0 0)")]
        records_b = [FeatureRecord(key="1", attrs={"name": "A", "updated": "2024-02"}, wkt="POINT (0 0)")]
        result = compute_diff(records_a, records_b, key="id", ignore_fields={"updated"})
        assert result.unchanged_count == 1
        assert len(result.modified) == 0

    def test_compute_diff_no_attribute_comparison(self) -> None:
        records_a = [FeatureRecord(key="1", attrs={"name": "A"}, wkt="POINT (0 0)")]
        records_b = [FeatureRecord(key="1", attrs={"name": "B"}, wkt="POINT (0 0)")]
        result = compute_diff(records_a, records_b, key="id", compare_attributes=False)
        assert result.unchanged_count == 1

    def test_compute_diff_no_geometry_comparison(self) -> None:
        records_a = [FeatureRecord(key="1", attrs={"name": "A"}, wkt="POINT (0 0)")]
        records_b = [FeatureRecord(key="1", attrs={"name": "A"}, wkt="POINT (1 1)")]
        result = compute_diff(records_a, records_b, key="id", compare_geometry=False)
        assert result.unchanged_count == 1

    def test_compute_diff_duplicate_key_warning(self) -> None:
        records_a = [
            FeatureRecord(key="1", attrs={"v": 1}, wkt="POINT (0 0)"),
            FeatureRecord(key="1", attrs={"v": 2}, wkt="POINT (1 1)"),
        ]
        records_b = [FeatureRecord(key="1", attrs={"v": 1}, wkt="POINT (0 0)")]
        result = compute_diff(records_a, records_b, key="id")
        assert len(result.warnings) == 1
        assert "Duplicate" in result.warnings[0]

    def test_compute_diff_progress_callback(self) -> None:
        calls: list[tuple] = []
        records_a = [FeatureRecord(key="1", attrs={}, wkt="POINT (0 0)")]
        records_b = [FeatureRecord(key="1", attrs={}, wkt="POINT (0 0)")]
        compute_diff(records_a, records_b, key="id", progress_callback=lambda c, t, m: calls.append((c, t, m)))
        assert len(calls) >= 2  # at least start and end


class TestReportErrorPaths:
    """Error tests for report generation."""

    def test_to_html_empty_result(self) -> None:
        result = DiffResult()
        html_str = to_html(result)
        assert "<html" in html_str
        assert "0 Added" in html_str or "'added': 0" in html_str or ">+0" in html_str

    def test_to_html_summary_only(self) -> None:
        result = DiffResult(
            added=[FeatureRecord(key="1", attrs={}, wkt="POINT (0 0)")],
        )
        html_str = to_html(result, summary_only=True)
        assert "Added Features" not in html_str

    def test_to_html_with_warnings(self) -> None:
        result = DiffResult(warnings=["Test warning"])
        html_str = to_html(result)
        assert "Test warning" in html_str
        assert "warnings" in html_str

    def test_to_html_xss_prevention(self) -> None:
        result = DiffResult(
            added=[FeatureRecord(key="<script>alert(1)</script>", attrs={}, wkt="POINT (0 0)")],
        )
        html_str = to_html(result)
        assert "<script>" not in html_str
        assert "&lt;script&gt;" in html_str

    def test_to_html_custom_title(self) -> None:
        result = DiffResult()
        html_str = to_html(result, title="Custom Report Title")
        assert "Custom Report Title" in html_str

    def test_to_csv_empty_result(self) -> None:
        result = DiffResult()
        csv_str = to_csv(result)
        assert "type" in csv_str
        assert "key" in csv_str

    def test_to_csv_with_data(self) -> None:
        result = DiffResult(
            added=[FeatureRecord(key="1", attrs={}, wkt="POINT (0 0)")],
            removed=[FeatureRecord(key="2", attrs={}, wkt="POINT (1 1)")],
            modified=[
                ModifiedFeature(
                    key="3", geometry_changed=True, field_changes=[FieldChange(field="name", old="A", new="B")]
                )
            ],
        )
        csv_str = to_csv(result)
        assert "added" in csv_str
        assert "removed" in csv_str
        assert "modified" in csv_str
        assert "geometry" in csv_str
        assert "name" in csv_str

    def test_to_csv_none_values(self) -> None:
        result = DiffResult(
            modified=[
                ModifiedFeature(
                    key="1", geometry_changed=False, field_changes=[FieldChange(field="name", old=None, new="B")]
                )
            ],
        )
        csv_str = to_csv(result)
        assert "modified" in csv_str
        # None should be empty string in CSV
        lines = [line for line in csv_str.strip().split("\n") if "modified" in line]
        assert len(lines) == 1
