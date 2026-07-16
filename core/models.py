"""Pure-logic models — no QGIS imports."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class FeatureRecord:
    """A feature record with a key, attributes dict, and WKT geometry."""

    key: Any
    attrs: dict[str, Any]
    wkt: str  # WKT geometry string for comparison

    @staticmethod
    def from_dict(key: Any, attrs: dict, wkt: str) -> "FeatureRecord":
        return FeatureRecord(key=str(key), attrs=attrs, wkt=wkt)


@dataclass
class FieldChange:
    """A single field change between old and new."""

    field: str
    old: object
    new: object


@dataclass
class ModifiedFeature:
    """A feature present in both layers but with changes."""

    key: str
    geometry_changed: bool
    field_changes: list[FieldChange] = field(default_factory=list)
    old_wkt: str = ""
    new_wkt: str = ""


@dataclass
class DiffResult:
    """Complete diff between two sets of feature records."""

    added: list[FeatureRecord] = field(default_factory=list)
    removed: list[FeatureRecord] = field(default_factory=list)
    modified: list[ModifiedFeature] = field(default_factory=list)
    unchanged_count: int = 0
    warnings: list[str] = field(default_factory=list)

    @property
    def summary(self) -> dict[str, int]:
        return {
            "added": len(self.added),
            "removed": len(self.removed),
            "modified": len(self.modified),
            "unchanged": self.unchanged_count,
            "total": len(self.added) + len(self.removed) + len(self.modified) + self.unchanged_count,
        }
