"""Extended model and matching tests for qgis_layer_diff."""

from core.matching import match_by_key
from core.models import DiffResult, FeatureRecord, FieldChange, ModifiedFeature


class TestFeatureRecordExtended:
    def test_from_dict_with_int_key(self):
        r = FeatureRecord.from_dict(12345, {"name": "test"}, "POINT(1 2)")
        assert r.key == "12345"

    def test_from_dict_with_float_key(self):
        r = FeatureRecord.from_dict(3.14, {}, "POINT(0 0)")
        assert r.key == "3.14"

    def test_from_dict_with_none_attrs(self):
        r = FeatureRecord.from_dict(1, {}, "")
        assert r.attrs == {}

    def test_from_dict_preserves_attrs(self):
        attrs = {"name": "test", "value": 42, "active": True}
        r = FeatureRecord.from_dict(1, attrs, "POINT(0 0)")
        assert r.attrs == attrs

    def test_from_dict_with_empty_wkt(self):
        r = FeatureRecord.from_dict(1, {}, "")
        assert r.wkt == ""

    def test_from_dict_with_complex_wkt(self):
        wkt = "POLYGON((0 0, 1 0, 1 1, 0 1, 0 0))"
        r = FeatureRecord.from_dict(1, {}, wkt)
        assert r.wkt == wkt

    def test_feature_record_equality(self):
        r1 = FeatureRecord("1", {"a": 1}, "POINT(0 0)")
        r2 = FeatureRecord("1", {"a": 1}, "POINT(0 0)")
        assert r1 == r2


class TestFieldChangeExtended:
    def test_string_change(self):
        fc = FieldChange(field="name", old="Alice", new="Bob")
        assert fc.field == "name"
        assert fc.old == "Alice"
        assert fc.new == "Bob"

    def test_numeric_change(self):
        fc = FieldChange(field="population", old=1000, new=2000)
        assert fc.old == 1000
        assert fc.new == 2000

    def test_none_to_value(self):
        fc = FieldChange(field="email", old=None, new="test@test.com")
        assert fc.old is None
        assert fc.new == "test@test.com"

    def test_value_to_none(self):
        fc = FieldChange(field="email", old="test@test.com", new=None)
        assert fc.old == "test@test.com"
        assert fc.new is None

    def test_boolean_change(self):
        fc = FieldChange(field="active", old=True, new=False)
        assert fc.old is True
        assert fc.new is False


class TestModifiedFeatureExtended:
    def test_geometry_only_change(self):
        m = ModifiedFeature(key="1", geometry_changed=True)
        assert m.geometry_changed is True
        assert m.field_changes == []

    def test_field_only_change(self):
        m = ModifiedFeature(
            key="1",
            geometry_changed=False,
            field_changes=[FieldChange(field="name", old="A", new="B")],
        )
        assert m.geometry_changed is False
        assert len(m.field_changes) == 1

    def test_both_geometry_and_field_change(self):
        m = ModifiedFeature(
            key="1",
            geometry_changed=True,
            field_changes=[FieldChange(field="pop", old=100, new=200)],
            old_wkt="POINT(0 0)",
            new_wkt="POINT(1 1)",
        )
        assert m.geometry_changed is True
        assert len(m.field_changes) == 1
        assert m.old_wkt == "POINT(0 0)"
        assert m.new_wkt == "POINT(1 1)"

    def test_multiple_field_changes(self):
        changes = [
            FieldChange(field="name", old="A", new="B"),
            FieldChange(field="pop", old=100, new=200),
            FieldChange(field="area", old=50.5, new=60.5),
        ]
        m = ModifiedFeature(key="1", geometry_changed=False, field_changes=changes)
        assert len(m.field_changes) == 3
        assert m.field_changes[2].field == "area"


class TestDiffResultExtended:
    def test_only_added(self):
        r = DiffResult(added=[FeatureRecord("1", {}, "POINT(0 0)")])
        s = r.summary
        assert s["added"] == 1
        assert s["removed"] == 0
        assert s["total"] == 1

    def test_only_removed(self):
        r = DiffResult(removed=[FeatureRecord("1", {}, "POINT(0 0)")])
        s = r.summary
        assert s["removed"] == 1
        assert s["total"] == 1

    def test_only_modified(self):
        r = DiffResult(modified=[ModifiedFeature(key="1", geometry_changed=True)])
        s = r.summary
        assert s["modified"] == 1
        assert s["total"] == 1

    def test_only_unchanged(self):
        r = DiffResult(unchanged_count=10)
        s = r.summary
        assert s["unchanged"] == 10
        assert s["total"] == 10

    def test_all_categories(self):
        r = DiffResult(
            added=[FeatureRecord("1", {}, "")],
            removed=[FeatureRecord("2", {}, "")],
            modified=[ModifiedFeature(key="3", geometry_changed=False)],
            unchanged_count=7,
        )
        s = r.summary
        assert s["total"] == 10

    def test_warnings(self):
        r = DiffResult(warnings=["Field type mismatch", "CRS mismatch"])
        assert len(r.warnings) == 2
        assert "Field type mismatch" in r.warnings

    def test_empty_diff_result(self):
        r = DiffResult()
        assert r.added == []
        assert r.removed == []
        assert r.modified == []
        assert r.unchanged_count == 0
        assert r.warnings == []


class TestMatchByKeyExtended:
    def test_empty_lists(self):
        result = match_by_key([], [])
        assert result["matched"] == []
        assert result["only_a"] == []
        assert result["only_b"] == []

    def test_all_matched(self):
        a = [FeatureRecord("1", {}, "POINT(0 0)"), FeatureRecord("2", {}, "POINT(1 1)")]
        b = [FeatureRecord("1", {}, "POINT(0 0)"), FeatureRecord("2", {}, "POINT(1 1)")]
        result = match_by_key(a, b)
        assert len(result["matched"]) == 2
        assert result["only_a"] == []
        assert result["only_b"] == []

    def test_only_in_a(self):
        a = [FeatureRecord("1", {}, "POINT(0 0)"), FeatureRecord("2", {}, "POINT(1 1)")]
        b = [FeatureRecord("1", {}, "POINT(0 0)")]
        result = match_by_key(a, b)
        assert len(result["matched"]) == 1
        assert len(result["only_a"]) == 1
        assert result["only_b"] == []

    def test_only_in_b(self):
        a = [FeatureRecord("1", {}, "POINT(0 0)")]
        b = [FeatureRecord("1", {}, "POINT(0 0)"), FeatureRecord("2", {}, "POINT(1 1)")]
        result = match_by_key(a, b)
        assert len(result["matched"]) == 1
        assert result["only_a"] == []
        assert len(result["only_b"]) == 1

    def test_no_overlap(self):
        a = [FeatureRecord("1", {}, "POINT(0 0)")]
        b = [FeatureRecord("2", {}, "POINT(1 1)")]
        result = match_by_key(a, b)
        assert result["matched"] == []
        assert len(result["only_a"]) == 1
        assert len(result["only_b"]) == 1

    def test_duplicate_keys_in_a(self):
        a = [FeatureRecord("1", {}, "POINT(0 0)"), FeatureRecord("1", {}, "POINT(1 1)")]
        b = [FeatureRecord("1", {}, "POINT(0 0)")]
        result = match_by_key(a, b)
        assert len(result["matched"]) == 1
        assert "1" in result["duplicate_keys_a"]
        assert len(result["only_a"]) == 1

    def test_duplicate_keys_in_b(self):
        a = [FeatureRecord("1", {}, "POINT(0 0)")]
        b = [FeatureRecord("1", {}, "POINT(0 0)"), FeatureRecord("1", {}, "POINT(1 1)")]
        result = match_by_key(a, b)
        assert len(result["matched"]) == 1
        assert "1" in result["duplicate_keys_b"]

    def test_matched_pairs_contain_correct_records(self):
        a = [FeatureRecord("1", {"name": "A"}, "POINT(0 0)")]
        b = [FeatureRecord("1", {"name": "B"}, "POINT(1 1)")]
        result = match_by_key(a, b)
        pair = result["matched"][0]
        assert pair[0].attrs["name"] == "A"
        assert pair[1].attrs["name"] == "B"

    def test_large_matching(self):
        a = [FeatureRecord(str(i), {}, f"POINT({i} {i})") for i in range(100)]
        b = [FeatureRecord(str(i), {}, f"POINT({i} {i})") for i in range(100)]
        result = match_by_key(a, b)
        assert len(result["matched"]) == 100
