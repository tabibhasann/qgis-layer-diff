"""Extended tests for differ, models, and report modules."""

from core.differ import compute_diff
from core.matching import match_by_key
from core.models import DiffResult, FeatureRecord, FieldChange, ModifiedFeature
from core.report import to_csv, to_html


class TestDiffResultModels:
    def test_diff_result_defaults(self):
        r = DiffResult()
        assert r.added == []
        assert r.removed == []
        assert r.modified == []
        assert r.unchanged_count == 0
        assert r.warnings == []

    def test_diff_result_summary_empty(self):
        r = DiffResult()
        s = r.summary
        assert s["added"] == 0
        assert s["removed"] == 0
        assert s["modified"] == 0
        assert s["unchanged"] == 0
        assert s["total"] == 0

    def test_diff_result_summary_with_data(self):
        r = DiffResult(
            added=[FeatureRecord("1", {}, "")],
            removed=[FeatureRecord("2", {}, ""), FeatureRecord("3", {}, "")],
            modified=[ModifiedFeature(key="4", geometry_changed=True)],
            unchanged_count=5,
        )
        s = r.summary
        assert s["added"] == 1
        assert s["removed"] == 2
        assert s["modified"] == 1
        assert s["unchanged"] == 5
        assert s["total"] == 9

    def test_field_change_dataclass(self):
        fc = FieldChange(field="name", old="Alice", new="Bob")
        assert fc.field == "name"
        assert fc.old == "Alice"
        assert fc.new == "Bob"

    def test_modified_feature_defaults(self):
        mf = ModifiedFeature(key="1", geometry_changed=False)
        assert mf.field_changes == []
        assert mf.old_wkt == ""
        assert mf.new_wkt == ""

    def test_feature_record_from_dict(self):
        r = FeatureRecord.from_dict(42, {"name": "test"}, "POINT (0 0)")
        assert r.key == "42"
        assert r.attrs == {"name": "test"}
        assert r.wkt == "POINT (0 0)"


class TestComputeDiffExtended:
    def test_empty_inputs(self):
        result = compute_diff([], [], key="id")
        assert result.added == []
        assert result.removed == []
        assert result.modified == []
        assert result.unchanged_count == 0

    def test_all_unchanged(self):
        a = [FeatureRecord("1", {"name": "A"}, "POINT (0 0)")]
        b = [FeatureRecord("1", {"name": "A"}, "POINT (0 0)")]
        result = compute_diff(a, b, key="id")
        assert result.unchanged_count == 1
        assert len(result.added) == 0
        assert len(result.removed) == 0
        assert len(result.modified) == 0

    def test_attribute_change_detected(self):
        a = [FeatureRecord("1", {"name": "A"}, "POINT (0 0)")]
        b = [FeatureRecord("1", {"name": "B"}, "POINT (0 0)")]
        result = compute_diff(a, b, key="id")
        assert len(result.modified) == 1
        assert result.modified[0].field_changes[0].field == "name"
        assert result.modified[0].field_changes[0].old == "A"
        assert result.modified[0].field_changes[0].new == "B"
        assert result.modified[0].geometry_changed is False

    def test_geometry_change_detected(self):
        a = [FeatureRecord("1", {"name": "A"}, "POINT (0 0)")]
        b = [FeatureRecord("1", {"name": "A"}, "POINT (1 1)")]
        result = compute_diff(a, b, key="id")
        assert len(result.modified) == 1
        assert result.modified[0].geometry_changed is True

    def test_both_geometry_and_attribute_change(self):
        a = [FeatureRecord("1", {"name": "A"}, "POINT (0 0)")]
        b = [FeatureRecord("1", {"name": "B"}, "POINT (1 1)")]
        result = compute_diff(a, b, key="id")
        assert len(result.modified) == 1
        assert result.modified[0].geometry_changed is True
        assert len(result.modified[0].field_changes) == 1

    def test_ignore_fields(self):
        a = [FeatureRecord("1", {"name": "A", "updated_at": "2024-01-01"}, "POINT (0 0)")]
        b = [FeatureRecord("1", {"name": "A", "updated_at": "2024-06-01"}, "POINT (0 0)")]
        result = compute_diff(a, b, key="id", ignore_fields={"updated_at"})
        assert result.unchanged_count == 1
        assert len(result.modified) == 0

    def test_compare_attributes_only(self):
        a = [FeatureRecord("1", {"name": "A"}, "POINT (0 0)")]
        b = [FeatureRecord("1", {"name": "A"}, "POINT (1 1)")]
        result = compute_diff(a, b, key="id", compare_geometry=False)
        assert result.unchanged_count == 1

    def test_compare_geometry_only(self):
        a = [FeatureRecord("1", {"name": "A"}, "POINT (0 0)")]
        b = [FeatureRecord("1", {"name": "B"}, "POINT (0 0)")]
        result = compute_diff(a, b, key="id", compare_attributes=False)
        assert result.unchanged_count == 1

    def test_added_features(self):
        a = [FeatureRecord("1", {"name": "A"}, "")]
        b = [FeatureRecord("1", {"name": "A"}, ""), FeatureRecord("2", {"name": "B"}, "")]
        result = compute_diff(a, b, key="id")
        assert len(result.added) == 1
        assert result.added[0].key == "2"

    def test_removed_features(self):
        a = [FeatureRecord("1", {"name": "A"}, ""), FeatureRecord("2", {"name": "B"}, "")]
        b = [FeatureRecord("1", {"name": "A"}, "")]
        result = compute_diff(a, b, key="id")
        assert len(result.removed) == 1
        assert result.removed[0].key == "2"

    def test_duplicate_key_warning(self):
        a = [FeatureRecord("1", {}, ""), FeatureRecord("1", {}, "")]
        b = [FeatureRecord("1", {}, "")]
        result = compute_diff(a, b, key="id")
        assert len(result.warnings) > 0
        assert "Duplicate" in result.warnings[0]

    def test_new_field_added(self):
        a = [FeatureRecord("1", {"name": "A"}, "POINT (0 0)")]
        b = [FeatureRecord("1", {"name": "A", "code": "X"}, "POINT (0 0)")]
        result = compute_diff(a, b, key="id")
        assert len(result.modified) == 1
        fc = result.modified[0].field_changes
        assert any(f.field == "code" and f.old is None and f.new == "X" for f in fc)

    def test_field_removed(self):
        a = [FeatureRecord("1", {"name": "A", "code": "X"}, "POINT (0 0)")]
        b = [FeatureRecord("1", {"name": "A"}, "POINT (0 0)")]
        result = compute_diff(a, b, key="id")
        assert len(result.modified) == 1
        fc = result.modified[0].field_changes
        assert any(f.field == "code" and f.old == "X" and f.new is None for f in fc)

    def test_progress_callback_called(self):
        calls = []
        a = [FeatureRecord("1", {"name": "A"}, "POINT (0 0)")]
        b = [FeatureRecord("1", {"name": "A"}, "POINT (0 0)")]
        compute_diff(a, b, key="id", progress_callback=lambda c, t, m: calls.append((c, t, m)))
        assert len(calls) >= 2  # at least start and end

    def test_multiple_matches(self):
        a = [FeatureRecord(str(i), {"v": i}, "POINT (0 0)") for i in range(10)]
        b = [FeatureRecord(str(i), {"v": i}, "POINT (0 0)") for i in range(10)]
        result = compute_diff(a, b, key="id")
        assert result.unchanged_count == 10


class TestReportExtended:
    def test_to_html_empty_result(self):
        r = DiffResult()
        html = to_html(r)
        assert "<!DOCTYPE html>" in html
        assert "Layer Diff Report" in html

    def test_to_html_with_title(self):
        r = DiffResult()
        html = to_html(r, title="Custom Title")
        assert "Custom Title" in html

    def test_to_html_with_added(self):
        r = DiffResult(added=[FeatureRecord("1", {"name": "A"}, "")])
        html = to_html(r)
        assert "Added Features" in html
        assert ">1<" in html

    def test_to_html_with_removed(self):
        r = DiffResult(removed=[FeatureRecord("2", {}, "")])
        html = to_html(r)
        assert "Removed Features" in html

    def test_to_html_with_modified(self):
        r = DiffResult(modified=[ModifiedFeature(
            key="1", geometry_changed=True,
            field_changes=[FieldChange("name", "A", "B")],
        )])
        html = to_html(r)
        assert "Modified Features" in html
        assert "name" in html

    def test_to_html_escapes_xss(self):
        r = DiffResult(added=[FeatureRecord("<script>alert(1)</script>", {}, "")])
        html = to_html(r)
        assert "<script>alert(1)</script>" not in html
        assert "&lt;script&gt;" in html

    def test_to_html_summary_only(self):
        r = DiffResult(added=[FeatureRecord("1", {}, "")])
        html = to_html(r, summary_only=True)
        assert "Added Features" not in html

    def test_to_html_with_warnings(self):
        r = DiffResult(warnings=["Duplicate key found"])
        html = to_html(r)
        assert "Warnings" in html
        assert "Duplicate key found" in html

    def test_to_csv_empty(self):
        r = DiffResult()
        csv_out = to_csv(r)
        assert "type" in csv_out or "Type" in csv_out

    def test_to_csv_with_data(self):
        r = DiffResult(
            added=[FeatureRecord("1", {"name": "A"}, "")],
            removed=[FeatureRecord("2", {"name": "B"}, "")],
        )
        csv_out = to_csv(r)
        assert "1" in csv_out
        assert "2" in csv_out


class TestMatchByKeyExtended:
    def test_duplicate_keys_in_a(self):
        a = [FeatureRecord("1", {}, ""), FeatureRecord("1", {}, ""), FeatureRecord("2", {}, "")]
        b = [FeatureRecord("1", {}, ""), FeatureRecord("2", {}, "")]
        result = match_by_key(a, b)
        assert "1" in result["duplicate_keys_a"]
        assert len(result["duplicate_keys_b"]) == 0

    def test_duplicate_keys_in_b(self):
        a = [FeatureRecord("1", {}, "")]
        b = [FeatureRecord("1", {}, ""), FeatureRecord("1", {}, "")]
        result = match_by_key(a, b)
        assert "1" in result["duplicate_keys_b"]

    def test_large_key_sets(self):
        a = [FeatureRecord(str(i), {}, "") for i in range(100)]
        b = [FeatureRecord(str(i), {}, "") for i in range(100)]
        result = match_by_key(a, b)
        assert len(result["matched"]) == 100

    def test_no_common_keys(self):
        a = [FeatureRecord("a", {}, "")]
        b = [FeatureRecord("b", {}, "")]
        result = match_by_key(a, b)
        assert len(result["matched"]) == 0
        assert len(result["only_a"]) == 1
        assert len(result["only_b"]) == 1
