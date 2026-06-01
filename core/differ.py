"""Core diff computation — pure logic, no QGIS imports."""

from typing import Any

from .matching import match_by_key, match_by_geometry
from .models import DiffResult, FeatureRecord, FieldChange, ModifiedFeature


def compute_diff(
    records_a: list[FeatureRecord],
    records_b: list[FeatureRecord],
    *,
    key: str | None = None,
    geom_tolerance: float = 0.0,
    compare_geometry: bool = True,
    compare_attributes: bool = True,
) -> DiffResult:
    """Compute the diff between two sets of feature records.

    Args:
        records_a: Features from the "before" layer.
        records_b: Features from the "after" layer.
        key: Optional key field to match features by. If None, uses geometry matching.
        geom_tolerance: Tolerance for geometry-based matching.
        compare_geometry: Whether to check for geometry changes.
        compare_attributes: Whether to check for attribute changes.

    Returns:
        DiffResult with added, removed, modified, and unchanged counts.
    """
    if key:
        match_result = match_by_key(records_a, records_b)
    else:
        match_result = match_by_geometry(records_a, records_b, geom_tolerance)

    result = DiffResult()

    # Added features (only in B)
    result.added = match_result["only_b"]

    # Removed features (only in A)
    result.removed = match_result["only_a"]

    # Check matched pairs for modifications
    for rec_a, rec_b in match_result["matched"]:
        field_changes: list[FieldChange] = []
        geom_changed = False

        if compare_attributes:
            all_keys = set(rec_a.attrs.keys()) | set(rec_b.attrs.keys())
            for fk in sorted(all_keys):
                old_val = rec_a.attrs.get(fk)
                new_val = rec_b.attrs.get(fk)
                if old_val != new_val:
                    field_changes.append(FieldChange(field=fk, old=old_val, new=new_val))

        if compare_geometry:
            geom_changed = rec_a.wkt != rec_b.wkt

        if field_changes or geom_changed:
            result.modified.append(
                ModifiedFeature(
                    key=rec_a.key,
                    geometry_changed=geom_changed,
                    field_changes=field_changes,
                    old_wkt=rec_a.wkt,
                    new_wkt=rec_b.wkt,
                )
            )
        else:
            result.unchanged_count += 1

    return result
