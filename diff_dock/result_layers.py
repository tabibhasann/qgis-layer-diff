"""Result layer creation and symbol helpers for QGIS diff visualization."""

from __future__ import annotations

from qgis.core import (
    QgsFeature,
    QgsFillSymbol,
    QgsGeometry,
    QgsLineSymbol,
    QgsMarkerSymbol,
    QgsProject,
    QgsSingleSymbolRenderer,
    QgsVectorLayer,
)
from qgis.PyQt.QtGui import QColor

from ..core.models import FeatureRecord


def make_symbol(geom_type: int, color: QColor):
    """Build the right QGIS symbol class for the layer's geometry type.

    geom_type: 0=Point, 1=Line, 2=Polygon (QgsWkbTypes enum values).
    """
    if geom_type == 0:  # Point
        return QgsMarkerSymbol.createSimple(
            {
                "color": color.name(),
                "outline_color": color.darker(150).name(),
                "size": "3.0",
            }
        )
    if geom_type == 1:  # Line
        return QgsLineSymbol.createSimple(
            {
                "color": color.name(),
                "width": "1.5",
            }
        )
    return QgsFillSymbol.createSimple(
        {
            "color": color.name(),
            "outline_color": color.darker(120).name(),
            "outline_width": "0.5",
        }
    )


def create_result_layer(
    name: str,
    records: list[FeatureRecord],
    color: QColor,
    source_layer: QgsVectorLayer,
) -> QgsVectorLayer:
    """Create a memory layer with styled features from the diff result."""
    geom_type = source_layer.geometryType()
    if geom_type == 0:
        geom_type_str = "Point"
    elif geom_type == 1:
        geom_type_str = "LineString"
    else:
        geom_type_str = "Polygon"

    crs = source_layer.crs().authid()
    uri = f"{geom_type_str}?crs={crs}&field=key:string"
    layer = QgsVectorLayer(uri, f"diff_{name}", "memory")
    dp = layer.dataProvider()

    features: list[QgsFeature] = []
    for rec in records:
        if not rec.wkt:
            continue
        feat = QgsFeature()
        feat.setGeometry(QgsGeometry.fromWkt(rec.wkt))
        feat.setAttributes([rec.key])
        features.append(feat)

    dp.addFeatures(features)
    layer.updateExtents()

    symbol = make_symbol(geom_type, color)
    if symbol is not None:
        layer.setRenderer(QgsSingleSymbolRenderer(symbol))

    QgsProject.instance().addMapLayer(layer)
    return layer
