"""qgis-layer-diff: Visual diff for vector layers in QGIS.

Entry point for QGIS plugin loader.
"""


def classFactory(iface):
    """Load LayerDiffPlugin class from the plugin module."""
    from .plugin import LayerDiffPlugin

    return LayerDiffPlugin(iface)  # type: ignore[no-untyped-call]
