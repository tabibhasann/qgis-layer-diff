"""Main QGIS plugin class — hooks into QGIS and opens the diff dock."""

from __future__ import annotations

import os

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction


class LayerDiffPlugin:
    """QGIS plugin for comparing vector layers."""

    def __init__(self, iface):
        self.iface = iface
        self.action: QAction | None = None
        self.dock = None

    def initGui(self):
        icon_path = os.path.join(os.path.dirname(__file__), "resources", "icons", "icon.svg")
        self.action = QAction(
            QIcon(icon_path),
            "Layer Diff",
            self.iface.mainWindow(),
        )
        self.action.triggered.connect(self.run)
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToVectorMenu("Layer Diff", self.action)

    def unload(self):
        if self.action:
            self.iface.removePluginVectorMenu("Layer Diff", self.action)
            self.iface.removeToolBarIcon(self.action)
        if self.dock:
            self.iface.removeDockWidget(self.dock)
            self.dock = None

    def run(self):
        if not self.dock:
            from .diff_dock import DiffDock
            self.dock = DiffDock(self.iface)
            self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dock)
        self.dock.show()
        self.dock.raise_()
