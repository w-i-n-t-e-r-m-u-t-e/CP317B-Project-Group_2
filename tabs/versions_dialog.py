from PySide6.QtWidgets import QDialog, QDialogButtonBox, QFormLayout, QLabel, QLineEdit


class VersionsDialog(QDialog):
    """One 'latest version' box for each device type."""

    def __init__(self, types, latest, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Latest versions")
        layout = QFormLayout(self)
        if not types:
            layout.addRow(QLabel("No device has a type yet. Add one with Edit."))
        self.fields = {}
        for kind in types:
            self.fields[kind] = QLineEdit(latest.get(kind, ""))
            layout.addRow(kind, self.fields[kind])
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def values(self):
        return {kind: field.text().strip() for kind, field in self.fields.items()}
