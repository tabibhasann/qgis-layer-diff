"""pytest.raises-based error path tests for qgis_layer_diff.

Tests that verify exceptions are raised where appropriate:
invalid types, missing attributes, shapely errors, and edge cases
that should fail hard rather than silently.
"""

import pytest

from core.differ import compute_diff
from core.matching import _geoms_equal, match_by_key
from core.models import FeatureRecord, FieldChange, ModifiedFeature
from core.report import to_csv, to_html


class TestFeatureRecordRaises:
    """FeatureRecord should raise on missing required fields."""

    def test_missing_attrs(self) -> None:
        with pytest.raises(TypeError):
            FeatureRecord(key="1", wkt="POINT (0 0)")  # type: ignore[call-arg]

    def test_missing_wkt(self) -> None:
        with pytest.raises(TypeError):
            FeatureRecord(key="1", attrs={})  # type: ignore[call-arg]

    def test_missing_key(self) -> None:
        with pytest.raises(TypeError):
            FeatureRecord(attrs={}, wkt="POINT (0 0)")  # type: ignore[call-arg]


class TestComputeDiffRaises:
    """compute_diff should raise on invalid parameter types."""

    def test_invalid_records_a_type(self) -> None:
        with pytest.raises(AttributeError):
            compute_diff(["not a record"], [], key="id")  # type: ignore[list-item]

    def test_invalid_records_b_type(self) -> None:
        with pytest.raises(AttributeError):
            compute_diff([], ["not a record"], key="id")  # type: ignore[list-item]

    def test_invalid_ignore_fields_type(self) -> None:
        records = [FeatureRecord(key="1", attrs={"name": "A"}, wkt="POINT (0 0)")]
        records2 = [FeatureRecord(key="1", attrs={"name": "B"}, wkt="POINT (0 0)")]
        with pytest.raises(TypeError):
            compute_diff(records, records2, key="id", ignore_fields=42)  # type: ignore[arg-type]


class TestMatchByKeyRaises:
    """match_by_key should raise on invalid input types."""

    def test_invalid_records_a_type(self) -> None:
        with pytest.raises(AttributeError):
            match_by_key(["not a record"], [])  # type: ignore[list-item]

    def test_invalid_records_b_type(self) -> None:
        with pytest.raises(AttributeError):
            match_by_key([], ["not a record"])  # type: ignore[list-item]


class TestGeomsEqualRaises:
    """_geoms_equal should raise on non-geometry inputs."""

    def test_geoms_equal_none_input(self) -> None:
        with pytest.raises(AttributeError):
            _geoms_equal(None, None, 0.0)  # type: ignore[arg-type]

    def test_geoms_equal_string_input(self) -> None:
        with pytest.raises(AttributeError):
            _geoms_equal("not a geom", "also not", 0.0)  # type: ignore[arg-type]


class TestReportRaises:
    """Report functions should raise on invalid inputs."""

    def test_to_html_invalid_result_type(self) -> None:
        with pytest.raises(AttributeError):
            to_html("not a DiffResult")  # type: ignore[arg-type]

    def test_to_csv_invalid_result_type(self) -> None:
        with pytest.raises(AttributeError):
            to_csv("not a DiffResult")  # type: ignore[arg-type]


class TestModifiedFeatureRaises:
    """ModifiedFeature should raise on missing required fields."""

    def test_missing_key(self) -> None:
        with pytest.raises(TypeError):
            ModifiedFeature(geometry_changed=True)  # type: ignore[call-arg]

    def test_missing_geometry_changed(self) -> None:
        with pytest.raises(TypeError):
            ModifiedFeature(key="1")  # type: ignore[call-arg]


class TestFieldChangeRaises:
    """FieldChange should raise on missing required fields."""

    def test_missing_field(self) -> None:
        with pytest.raises(TypeError):
            FieldChange(old="A", new="B")  # type: ignore[call-arg]

    def test_missing_old(self) -> None:
        with pytest.raises(TypeError):
            FieldChange(field="name", new="B")  # type: ignore[call-arg]

    def test_missing_new(self) -> None:
        with pytest.raises(TypeError):
            FieldChange(field="name", old="A")  # type: ignore[call-arg]
