from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

def create_devices_tab():
    devices_tab = QWidget()
    devices_layout = QVBoxLayout(devices_tab)
    devices_layout.addWidget(QLabel("This is the Devices tab."))
    return devices_tab