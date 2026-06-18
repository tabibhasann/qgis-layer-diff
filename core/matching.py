"""Matching strategies: by key field or by geometry."""

from typing import Any, Callable

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
    progress_callback: Callable | None = None,
) -> dict[str, Any]:
    """Match features by geometry equality within tolerance.

    Uses shapely STRtree spatial index for efficient O(n log n) matching.
    """
    from shapely import wkt as _wkt
    from shapely import STRtree

    # Parse geometries for B and build spatial index
    b_geoms = []
    valid_b_indices = []
    for i, r in enumerate(records_b):
        try:
            geom = _wkt.loads(r.wkt)
            if geom is not None and not geom.is_empty:
                b_geoms.append(geom)
                valid_b_indices.append(i)
        except Exception:
            pass

    # Build R-tree spatial index for B
    tree = STRtree(b_geoms)
    
    matched_pairs = []
    unmatched_a = []
    used_b = set()

    total = len(records_a)
    for idx, rec_a in enumerate(records_a):
        if progress_callback and idx % 10 == 0:
            progress_callback(idx, total, "Matching features")
        
        try:
            ga = _wkt.loads(rec_a.wkt)
            if ga is None or ga.is_empty:
                unmatched_a.append(rec_a)
                continue
        except Exception:
            unmatched_a.append(rec_a)
            continue

        # Query spatial index for candidates (bounding box intersection)
        # When tolerance > 0, buffer the query geometry to expand the search area
        query_geom = ga.buffer(tolerance) if tolerance > 0 else ga
        candidates = tree.query(query_geom)
        
        found = False
        for candidate_idx in candidates:
            j = valid_b_indices[candidate_idx]
            if j in used_b:
                continue
            
            gb = b_geoms[candidate_idx]
            if _geoms_equal(ga, gb, tolerance):
                matched_pairs.append((rec_a, records_b[j]))
                used_b.add(j)
                found = True
                break

        if not found:
            unmatched_a.append(rec_a)

    if progress_callback:
        progress_callback(total, total, "Matching complete")

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
