"""Layer conversion utilities — QgsVectorLayer to FeatureRecords."""

from __future__ import annotations

from qgis.core import QgsCoordinateTransform, QgsProject, QgsVectorLayer

from ..core.models import FeatureRecord


def layer_to_records(
    layer: QgsVectorLayer,
    other_layer: QgsVectorLayer,
    key_field: str | None,
    ignore_fields: set[str] | None = None,
) -> list[FeatureRecord]:
    """Convert a QgsVectorLayer to FeatureRecords, reprojecting if needed."""
    records: list[FeatureRecord] = []
    needs_reproject = False
    transform = None
    if layer.crs() != other_layer.crs():
        needs_reproject = True
        transform = QgsCoordinateTransform(layer.crs(), other_layer.crs(), QgsProject.instance())

    key_idx = layer.fields().indexOf(key_field) if key_field else -1

    for feat in layer.getFeatures():
        key = feat.attribute(key_idx) if key_idx >= 0 else feat.id()

        attrs: dict[str, object] = {}
        for field in feat.fields():
            fname = field.name()
            if key_field and fname == key_field:
                continue
            if ignore_fields and fname in ignore_fields:
                continue
            val = feat.attribute(fname)
            if hasattr(val, "toString"):
                val = val.toString()
            attrs[fname] = val

        geom = feat.geometry()
        if needs_reproject and transform is not None:
            geom.transform(transform)

        wkt = geom.asWkt() if geom and not geom.isEmpty() else ""
        if wkt is None:
            wkt = ""

        records.append(FeatureRecord(key=str(key), attrs=attrs, wkt=wkt))

    return records
