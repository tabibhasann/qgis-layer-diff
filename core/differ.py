"""Core diff computation — pure logic, no QGIS imports."""

from __future__ import annotations

from collections.abc import Callable

from .matching import match_by_geometry, match_by_key
from .models import DiffResult, FeatureRecord, FieldChange, ModifiedFeature


def compute_diff(
    records_a: list[FeatureRecord],
    records_b: list[FeatureRecord],
    *,
    key: str | None = None,
    geom_tolerance: float = 0.0,
    compare_geometry: bool = True,
    compare_attributes: bool = True,
    ignore_fields: set[str] | None = None,
    progress_callback: Callable | None = None,
) -> DiffResult:
    """Compute the diff between two sets of feature records.

    Args:
        records_a: Features from the "before" layer.
        records_b: Features from the "after" layer.
        key: Optional key field to match features by. If None, uses geometry matching.
        geom_tolerance: Tolerance for geometry-based matching.
        compare_geometry: Whether to check for geometry changes.
        compare_attributes: Whether to check for attribute changes.
        ignore_fields: Set of field names to exclude from attribute comparison.
        progress_callback: Optional callback(current, total, message) for progress updates.

    Returns:
        DiffResult with added, removed, modified, and unchanged counts.
    """
    if progress_callback:
        progress_callback(0, len(records_a), "Starting diff computation")

    if key:
        match_result = match_by_key(records_a, records_b)
    else:
        match_result = match_by_geometry(records_a, records_b, geom_tolerance, progress_callback)

    result = DiffResult()

    # Surface duplicate key warnings
    if key:
        dupes_a = match_result.get("duplicate_keys_a", [])
        dupes_b = match_result.get("duplicate_keys_b", [])
        if dupes_a or dupes_b:
            all_dupes = sorted(set(dupes_a) | set(dupes_b))
            warning_msg = f"Duplicate key(s) found: {', '.join(all_dupes[:10])}"
            if len(all_dupes) > 10:
                warning_msg += f" (+{len(all_dupes) - 10} more)"
            warning_msg += " — only first occurrence used for matching, duplicates appear as removed/added."
            result.warnings.append(warning_msg)
            if progress_callback:
                progress_callback(0, 0, f"Warning: {len(all_dupes)} duplicate key(s) found")

    # Added features (only in B)
    result.added = match_result["only_b"]

    # Removed features (only in A)
    result.removed = match_result["only_a"]

    # Check matched pairs for modifications
    matched = match_result["matched"]
    for i, (rec_a, rec_b) in enumerate(matched):
        if progress_callback and i % 10 == 0:
            progress_callback(i, len(matched), "Comparing features")

        field_changes: list[FieldChange] = []
        geom_changed = False

        if compare_attributes:
            all_keys = set(rec_a.attrs.keys()) | set(rec_b.attrs.keys())
            for fk in sorted(all_keys):
                if ignore_fields and fk in ignore_fields:
                    continue
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

    if progress_callback:
        progress_callback(len(matched), len(matched), "Diff complete")

    return result
