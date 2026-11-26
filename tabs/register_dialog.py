import json
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QFormLayout, QLabel, QLineEdit
from utils.scan import API_URL


class RegisterDialog(QDialog):
    """Registers a new device, or edits one if a device from the backend is passed in."""

    def __init__(self, parent=None, device=None):
        super().__init__(parent)
        self.device = device
        self.setWindowTitle("Edit device" if device else "Register new device")
        layout = QFormLayout(self)

        # the keys are the field names the backend expects, with its length limits
        self.fields = {}
        for key, label, limit in (("Device_Name", "Name", 25), ("IP", "IP", 30), ("Device_Version", "Version", 30),
                                  ("Device_Type", "Type (optional)", 30)):
            self.fields[key] = QLineEdit()
            self.fields[key].setMaxLength(limit)
            layout.addRow(label, self.fields[key])

        if device:
            for key, name in (("Device_Name", "deviceName"), ("IP", "ip"), ("Device_Version", "deviceVersion"),
                              ("Device_Type", "deviceType")):
                self.fields[key].setText(device[name] or "")

        self.error = QLabel()
        layout.addRow(self.error)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def save(self):
        body = {key: field.text().strip() for key, field in self.fields.items()}
        if not all(value for key, value in body.items() if key != "Device_Type"):
            self.error.setText("Fill in name, IP and version.")
            return
        try:
            url = f"{API_URL}/{self.device['id']}" if self.device else API_URL
            request = Request(url, json.dumps(body).encode(), {"Content-Type": "application/json"},
                              method="PUT" if self.device else "POST")
            urlopen(request, timeout=3).close()
        except HTTPError as error:
            try:
                reason = json.load(error)["error"]  # the backend says what was wrong
            except (ValueError, KeyError):
                reason = "The backend rejected these values."
            self.error.setText(reason)
        except OSError:
            self.error.setText("Could not reach the backend. Is it running?")
        else:
            self.accept()  # closes the dialog
