"""Extended tests for matching module."""

from core.models import FeatureRecord
from core.matching import match_by_key, match_by_geometry


class TestMatchByKeyExtended:
    def test_empty_inputs(self):
        result = match_by_key([], [])
        assert result["matched"] == []
        assert result["only_a"] == []
        assert result["only_b"] == []
        assert result["duplicate_keys_a"] == []
        assert result["duplicate_keys_b"] == []

    def test_all_matched(self):
        a = [FeatureRecord("1", {}, ""), FeatureRecord("2", {}, "")]
        b = [FeatureRecord("1", {}, ""), FeatureRecord("2", {}, "")]
        result = match_by_key(a, b)
        assert len(result["matched"]) == 2
        assert result["only_a"] == []
        assert result["only_b"] == []

    def test_only_in_a(self):
        a = [FeatureRecord("1", {}, ""), FeatureRecord("2", {}, "")]
        b = [FeatureRecord("1", {}, "")]
        result = match_by_key(a, b)
        assert len(result["matched"]) == 1
        assert len(result["only_a"]) == 1
        assert result["only_a"][0].key == "2"
        assert result["only_b"] == []

    def test_only_in_b(self):
        a = [FeatureRecord("1", {}, "")]
        b = [FeatureRecord("1", {}, ""), FeatureRecord("3", {}, "")]
        result = match_by_key(a, b)
        assert len(result["matched"]) == 1
        assert result["only_a"] == []
        assert len(result["only_b"]) == 1
        assert result["only_b"][0].key == "3"

    def test_duplicates_in_both(self):
        a = [FeatureRecord("1", {}, ""), FeatureRecord("1", {}, "")]
        b = [FeatureRecord("1", {}, ""), FeatureRecord("1", {}, "")]
        result = match_by_key(a, b)
        assert len(result["matched"]) == 1
        assert len(result["duplicate_keys_a"]) == 1
        assert len(result["duplicate_keys_b"]) == 1
        assert len(result["only_a"]) == 1
        assert len(result["only_b"]) == 1


class TestMatchByGeometryExtended:
    def test_exact_match(self):
        a = [FeatureRecord("a", {}, "POINT(0 0)")]
        b = [FeatureRecord("b", {}, "POINT(0 0)")]
        result = match_by_geometry(a, b)
        assert len(result["matched"]) == 1
        assert result["only_a"] == []
        assert result["only_b"] == []

    def test_within_tolerance(self):
        a = [FeatureRecord("a", {}, "POINT(0 0)")]
        b = [FeatureRecord("b", {}, "POINT(0.001 0)")]
        result = match_by_geometry(a, b, tolerance=0.01)
        assert len(result["matched"]) == 1

    def test_empty_b(self):
        a = [FeatureRecord("a", {}, "POINT(0 0)")]
        result = match_by_geometry(a, [])
        assert len(result["matched"]) == 0
        assert len(result["only_a"]) == 1
        assert result["only_b"] == []

    def test_empty_a(self):
        b = [FeatureRecord("b", {}, "POINT(0 0)")]
        result = match_by_geometry([], b)
        assert len(result["matched"]) == 0
        assert result["only_a"] == []
        assert len(result["only_b"]) == 1

    def test_invalid_wkt_in_a(self):
        a = [FeatureRecord("a", {}, "NOT WKT")]
        b = [FeatureRecord("b", {}, "POINT(0 0)")]
        result = match_by_geometry(a, b)
        assert len(result["matched"]) == 0
        assert len(result["only_a"]) == 1

    def test_invalid_wkt_in_b(self):
        a = [FeatureRecord("a", {}, "POINT(0 0)")]
        b = [FeatureRecord("b", {}, "NOT WKT")]
        result = match_by_geometry(a, b)
        assert len(result["matched"]) == 0
        assert len(result["only_a"]) == 1

    def test_multiple_matches(self):
        a = [
            FeatureRecord("a1", {}, "POINT(0 0)"),
            FeatureRecord("a2", {}, "POINT(1 1)"),
        ]
        b = [
            FeatureRecord("b1", {}, "POINT(0 0)"),
            FeatureRecord("b2", {}, "POINT(1 1)"),
        ]
        result = match_by_geometry(a, b)
        assert len(result["matched"]) == 2
        assert result["only_a"] == []
        assert result["only_b"] == []

    def test_progress_callback_called(self):
        calls = []
        a = [FeatureRecord(f"a{i}", {}, f"POINT({i} 0)") for i in range(15)]
        b = [FeatureRecord(f"b{i}", {}, f"POINT({i} 0)") for i in range(15)]
        match_by_geometry(a, b, progress_callback=lambda i, t, msg: calls.append((i, t, msg)))
        assert len(calls) > 0
        assert calls[-1][0] == 15
