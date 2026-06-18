"""Tests for the dock UI logic and edge cases.

The QDockWidget itself cannot be unit-tested without a running QGIS, so
this file focuses on the pure helpers and additional differ / matching
edge cases that weren't in test_differ.py.
"""


from core.differ import compute_diff
from core.matching import match_by_geometry
from core.models import FeatureRecord, DiffResult
from core.report import to_html, to_csv


def make_record(key, attrs=None, wkt=""):
    return FeatureRecord(key=key, attrs=attrs or {}, wkt=wkt)


class TestComputeDiffEdgeCases:
    def test_schema_mismatch_added_field(self):
        """Field appearing only in B should be reported as a change for matched features."""
        a = [FeatureRecord(key="1", attrs={"name": "A"}, wkt="POINT(0 0)")]
        b = [FeatureRecord(key="1", attrs={"name": "A", "new_field": 42}, wkt="POINT(0 0)")]
        result = compute_diff(a, b, key="key", compare_geometry=False)
        assert len(result.modified) == 1
        fields = {fc.field for fc in result.modified[0].field_changes}
        assert "new_field" in fields

    def test_schema_mismatch_removed_field(self):
        """Field disappearing from B should also be a change."""
        a = [FeatureRecord(key="1", attrs={"name": "A", "old": 1}, wkt="POINT(0 0)")]
        b = [FeatureRecord(key="1", attrs={"name": "A"}, wkt="POINT(0 0)")]
        result = compute_diff(a, b, key="key", compare_geometry=False)
        assert len(result.modified) == 1
        fields = {fc.field for fc in result.modified[0].field_changes}
        assert "old" in fields

    def test_no_key_no_geom_match_falls_through(self):
        """When no key is provided, geometry matching is used."""
        a = [make_record("a", wkt="POINT(0 0)"), make_record("b", wkt="POINT(1 1)")]
        b = [make_record("x", wkt="POINT(0 0)"), make_record("y", wkt="POINT(5 5)")]
        result = compute_diff(a, b)  # no key
        # 1 matched (a/x), 1 removed (b), 1 added (y)
        assert result.summary["added"] == 1
        assert result.summary["removed"] == 1

    def test_progress_callback_called(self):
        calls = []

        def cb(cur, total, msg):
            calls.append((cur, total, msg))

        a = [make_record(str(i), wkt=f"POINT({i} {i})") for i in range(3)]
        b = [make_record(str(i), wkt=f"POINT({i} {i})") for i in range(3)]
        compute_diff(a, b, key="key", progress_callback=cb)
        assert len(calls) >= 1
        # First call should be the start
        assert calls[0][0] == 0
        # Last call should be completion
        assert "complete" in calls[-1][2].lower() or calls[-1][0] == calls[-1][1]

    def test_compare_geometry_off_only_attributes(self):
        """When geometry comparison is off, attribute changes are still detected."""
        a = [make_record("1", {"x": 1}, "POINT(0 0)")]
        b = [make_record("1", {"x": 2}, "POINT(99 99)")]
        result = compute_diff(a, b, key="key", compare_geometry=False, compare_attributes=True)
        # Attribute change is still detected even with geometry comparison off
        assert len(result.modified) == 1
        assert result.unchanged_count == 0
        # The modification is only attribute-based, not geometry
        assert result.modified[0].geometry_changed is False
        assert result.modified[0].field_changes[0].field == "x"

    def test_geometry_tolerance_polygon(self):
        a = [make_record("a", wkt="POLYGON((0 0, 1 0, 1 1, 0 1, 0 0))")]
        b = [make_record("b", wkt="POLYGON((0 0, 1 0, 1 1, 0 1, 0 0))")]
        result = match_by_geometry(a, b, tolerance=0)
        assert len(result["matched"]) == 1


class TestHtmlReport:
    def test_html_contains_modified_rows(self):
        result = DiffResult(modified=[
            FeatureRecord(key="1", attrs={}, wkt="POINT(0 0)"),  # placeholder
        ])
        # Use a real ModifiedFeature for the report
        from core.models import ModifiedFeature, FieldChange
        result = DiffResult(
            added=[],
            removed=[],
            modified=[ModifiedFeature(
                key="42", geometry_changed=True,
                field_changes=[FieldChange("name", "old", "new")],
            )],
        )
        html = to_html(result)
        assert "42" in html
        assert "name" in html
        assert "old" in html
        assert "new" in html

    def test_html_escapes_special_chars(self):
        """XSS attempt in attributes should be HTML-escaped."""
        from core.models import ModifiedFeature, FieldChange
        result = DiffResult(modified=[
            ModifiedFeature(
                key="<script>alert(1)</script>",
                geometry_changed=False,
                field_changes=[FieldChange("name", "<img src=x>", "ok")],
            )
        ])
        html = to_html(result)
        # Raw script tag must not be present
        assert "<script>alert(1)</script>" not in html
        # Escaped form is present
        assert "&lt;script&gt;" in html


class TestCsvReport:
    def test_csv_quotes_correctly(self):
        from core.models import ModifiedFeature, FieldChange
        result = DiffResult(
            added=[make_record("with,comma")],
            modified=[ModifiedFeature(
                key="1", geometry_changed=False,
                field_changes=[FieldChange("name", 'has "quotes"', "fine")],
            )],
        )
        csv = to_csv(result)
        # csv.writer should quote fields containing commas
        assert '"with,comma"' in csv
        assert '"has ""quotes"""' in csv
