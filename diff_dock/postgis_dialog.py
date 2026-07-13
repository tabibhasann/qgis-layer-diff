"""PostGIS connection dialog for adding layers to the project."""

from __future__ import annotations

from qgis.core import QgsDataSourceUri, QgsProject, QgsVectorLayer
from qgis.PyQt.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QWidget,
)


def add_postgis_layer(parent: QWidget, layer_b_combo) -> None:
    """Open a dialog to connect to a PostGIS layer and add it to the project."""
    dialog = QDialog(parent)
    dialog.setWindowTitle("Add PostGIS Layer")
    form = QFormLayout(dialog)

    host_edit = QLineEdit("localhost")
    port_edit = QLineEdit("5432")
    db_edit = QLineEdit()
    user_edit = QLineEdit()
    pw_edit = QLineEdit()
    pw_edit.setEchoMode(QLineEdit.Password)
    table_edit = QLineEdit()
    table_edit.setPlaceholderText("schema.table_name")

    form.addRow("Host:", host_edit)
    form.addRow("Port:", port_edit)
    form.addRow("Database:", db_edit)
    form.addRow("Username:", user_edit)
    form.addRow("Password:", pw_edit)
    form.addRow("Table:", table_edit)

    buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    form.addRow(buttons)

    if dialog.exec_() != QDialog.Accepted:
        return

    uri = QgsDataSourceUri()
    uri.setConnection(
        host_edit.text(),
        port_edit.text(),
        db_edit.text(),
        user_edit.text(),
        pw_edit.text(),
    )
    table = table_edit.text()
    if "." in table:
        schema, name = table.split(".", 1)
    else:
        schema, name = "public", table
    uri.setDataSource(schema, name, "geom")

    layer = QgsVectorLayer(uri.uri(), f"pg_{name}", "postgres")
    if not layer.isValid():
        QMessageBox.critical(parent, "Error", f"Failed to load PostGIS layer: {table}")
        return

    QgsProject.instance().addMapLayer(layer)
    layer_b_combo.setLayer(layer)
