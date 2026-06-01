"""Tests for report formatting."""

import pytest
from core.models import DiffResult, FeatureRecord, ModifiedFeature, FieldChange
from core.report import to_html, to_csv


class TestHTMLReport:
    def test_empty_report(self):
        result = DiffResult()
        html = to_html(result)
        assert "<html" in html.lower()
        assert "0 Added" in html

    def test_with_data(self):
        result = DiffResult(
            added=[FeatureRecord("3", {}, "")],
            removed=[FeatureRecord("1", {}, "")],
            modified=[ModifiedFeature(
                key="2",
                geometry_changed=True,
                field_changes=[FieldChange("name", "Old", "New")],
            )],
        )
        html = to_html(result)
        assert "+1 Added" in html
        assert "-1 Removed" in html
        assert "~1 Modified" in html


class TestCSVReport:
    def test_with_data(self):
        result = DiffResult(
            added=[FeatureRecord("3", {"id": 3}, "POINT(2 2)")],
        )
        csv = to_csv(result)
        assert "added,3" in csv

    def test_csv_always_starts_with_header(self):
        csv = to_csv(DiffResult())
        assert csv.startswith("type,key,field,old_value,new_value")
