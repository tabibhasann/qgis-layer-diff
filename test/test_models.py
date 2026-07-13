"""Tests for pure-logic models."""

from core.models import DiffResult, FeatureRecord, FieldChange, ModifiedFeature


class TestFeatureRecord:
    def test_from_dict(self):
        r = FeatureRecord.from_dict(42, {"name": "test"}, "POINT(0 0)")
        assert r.key == "42"
        assert r.attrs == {"name": "test"}
        assert r.wkt == "POINT(0 0)"

    def test_from_dict_string_key(self):
        r = FeatureRecord.from_dict("abc", {}, "")
        assert r.key == "abc"


class TestDiffResult:
    def test_empty_summary(self):
        r = DiffResult()
        s = r.summary
        assert s["added"] == 0
        assert s["removed"] == 0
        assert s["modified"] == 0
        assert s["unchanged"] == 0
        assert s["total"] == 0

    def test_summary_with_changes(self):
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

    def test_warnings_default_empty(self):
        r = DiffResult()
        assert r.warnings == []


class TestModifiedFeature:
    def test_defaults(self):
        m = ModifiedFeature(key="1", geometry_changed=False)
        assert m.field_changes == []
        assert m.old_wkt == ""
        assert m.new_wkt == ""

    def test_with_field_changes(self):
        m = ModifiedFeature(
            key="1",
            geometry_changed=True,
            field_changes=[
                FieldChange(field="name", old="A", new="B"),
                FieldChange(field="pop", old=100, new=200),
            ],
            old_wkt="POINT(0 0)",
            new_wkt="POINT(1 1)",
        )
        assert len(m.field_changes) == 2
        assert m.field_changes[0].field == "name"
        assert m.field_changes[0].old == "A"
        assert m.field_changes[0].new == "B"
