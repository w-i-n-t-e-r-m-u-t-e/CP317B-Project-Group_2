from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea, QFrame
from schema.schema import DeviceList

def create_devices_tab():
    # setup ui for devices tab
    devices_tab = QWidget()
    device_container = QScrollArea()
    devices_layout = QVBoxLayout(devices_tab)

    # poplate the device list with device data
    for device in DeviceList().devices:
        device_frame = QFrame()
        device_layout = QVBoxLayout(device_frame)
        device_layout.addWidget(QLabel(f"Device ID: {device.device_id} Device Name: {device.device_name} Status: {device.status}"))
        device_container.setWidget(device_frame)

    # add ui to devices tab
    devices_layout.addWidget(QLabel("This is the Devices tab."))
    devices_layout.addWidget(device_container)

    return devices_tab