"""Matching strategies: by key field or by geometry."""

from typing import Any

from .models import FeatureRecord


def match_by_key(
    records_a: list[FeatureRecord],
    records_b: list[FeatureRecord],
) -> dict[str, Any]:
    """Match features by their key field value.

    Returns a dict with matched pairs and unmatched records.
    """
    a_map: dict[str, FeatureRecord] = {r.key: r for r in records_a}
    b_map: dict[str, FeatureRecord] = {r.key: r for r in records_b}

    a_keys = set(a_map.keys())
    b_keys = set(b_map.keys())

    common_keys = a_keys & b_keys
    only_a_keys = a_keys - b_keys
    only_b_keys = b_keys - a_keys

    return {
        "matched": [(a_map[k], b_map[k]) for k in common_keys],
        "only_a": [a_map[k] for k in only_a_keys],
        "only_b": [b_map[k] for k in only_b_keys],
    }


def match_by_geometry(
    records_a: list[FeatureRecord],
    records_b: list[FeatureRecord],
    tolerance: float = 0.0,
) -> dict[str, Any]:
    """Match features by geometry equality within tolerance.

    Uses shapely for geometry comparison (still pure Python, no QGIS needed).
    """
    from shapely import wkt as _wkt

    # Build spatial index for B
    b_geoms = []
    for r in records_b:
        try:
            b_geoms.append(_wkt.loads(r.wkt))
        except Exception:
            b_geoms.append(None)

    matched_pairs = []
    unmatched_a = []
    used_b = set()

    for rec_a in records_a:
        try:
            ga = _wkt.loads(rec_a.wkt)
        except Exception:
            unmatched_a.append(rec_a)
            continue

        found = False
        for j, gb in enumerate(b_geoms):
            if j in used_b or gb is None:
                continue
            if _geoms_equal(ga, gb, tolerance):
                matched_pairs.append((rec_a, records_b[j]))
                used_b.add(j)
                found = True
                break

        if not found:
            unmatched_a.append(rec_a)

    unmatched_b = [records_b[j] for j in range(len(records_b)) if j not in used_b]

    return {
        "matched": matched_pairs,
        "only_a": unmatched_a,
        "only_b": unmatched_b,
    }


def _geoms_equal(g1, g2, tolerance: float) -> bool:
    """Check if two shapely geometries are equal within tolerance."""
    if tolerance == 0:
        return g1.equals(g2)
    # Use Hausdorff distance for approximate equality
    return g1.hausdorff_distance(g2) <= tolerance
