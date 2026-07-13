"""Tests for matching module."""

from core.models import FeatureRecord
from core.matching import match_by_key, match_by_geometry


class TestMatchByKey:
    def test_basic(self):
        a = [FeatureRecord("1", {}, ""), FeatureRecord("2", {}, "")]
        b = [FeatureRecord("2", {}, ""), FeatureRecord("3", {}, "")]
        result = match_by_key(a, b)
        assert len(result["matched"]) == 1
        assert result["matched"][0][0].key == "2"

    def test_duplicate_keys(self):
        a = [FeatureRecord("1", {}, ""), FeatureRecord("1", {}, "")]
        b = [FeatureRecord("1", {}, "")]
        result = match_by_key(a, b)
        assert len(result["matched"]) == 1
        assert "duplicate_keys_a" in result
        assert "1" in result["duplicate_keys_a"]
        assert result["duplicate_keys_b"] == []
        assert len(result["only_a"]) == 1


class TestMatchByGeometry:
    def test_no_tolerance_mismatch(self):
        a = [FeatureRecord("a", {}, "POINT(0 0)")]
        b = [FeatureRecord("b", {}, "POINT(1 0)")]
        result = match_by_geometry(a, b)
        assert len(result["matched"]) == 0
