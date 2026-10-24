from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea, QFrame, QHBoxLayout, QStackedLayout
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
from schema.schema import DeviceList
from styles.styles import BG1_IMAGE
from styles.Image_AutoResize import ResizeImage

def create_devices_tab():
    # setup ui for devices tab
    devices_tab = QWidget()
    device_container = QScrollArea()
    device_container.setWidgetResizable(True)
    
    devices_layout = QVBoxLayout(devices_tab)

    # test data for devices
    content = QWidget()
    content_layout = QVBoxLayout(content)

    #'''
    test_devices = [
        {"device_id": "001", "device_name": "Device A", "status": "Active"},
        {"device_id": "002", "device_name": "Device B", "status": "Inactive"},
        {"device_id": "003", "device_name": "Device C", "status": "Active"},
        {"device_id": "004", "device_name": "Device D", "status": "Inactive"},
        {"device_id": "005", "device_name": "Device E", "status": "Active"},
        {"device_id": "006", "device_name": "Device F", "status": "Inactive"},
        {"device_id": "007", "device_name": "Device G", "status": "Active"},
        {"device_id": "008", "device_name": "Device H", "status": "Inactive"},
        {"device_id": "009", "device_name": "Device I", "status": "Active"},
        {"device_id": "010", "device_name": "Device J", "status": "Inactive"},
        {"device_id": "011", "device_name": "Device K", "status": "Active"},
        {"device_id": "012", "device_name": "Device L", "status": "Inactive"},
        {"device_id": "013", "device_name": "Device M", "status": "Active"},
        {"device_id": "014", "device_name": "Device N", "status": "Inactive"},
        {"device_id": "015", "device_name": "Device O", "status": "Active"},
        {"device_id": "016", "device_name": "Device P", "status": "Inactive"},
        {"device_id": "017", "device_name": "Device Q", "status": "Active"},
        {"device_id": "018", "device_name": "Device R", "status": "Inactive"},
        {"device_id": "019", "device_name": "Device S", "status": "Active"},
        {"device_id": "020", "device_name": "Device T", "status": "Inactive"},
    ]

    for device in test_devices:
        content_layout.addWidget(build_row(device))  # Adds this frame below the previous one

    '''
    # poplate the device list with device data
    for device in DeviceList().devices:
        content_layout.addWidget(build_row(device))  # Adds this frame below the previous one
    #'''

    # add ui to devices tab
    device_container.setWidget(content)  # Set the scroll area's content once
    devices_layout.addWidget(QLabel("This is the Devices tab."))
    devices_layout.addWidget(device_container)

    return devices_tab

def build_row(device):
    # build a frame to store row ui
    device_frame = QFrame()

    # create ui stacking
    stack = QStackedLayout(device_frame)
    stack.setStackingMode(QStackedLayout.StackAll)

    row_frame = QFrame()
    row_layout = QHBoxLayout(row_frame)

    # QFrame ui
    line = QFrame()
    line.setFrameShape(QFrame.Shape.VLine)
    line.setFrameShadow(QFrame.Shadow.Sunken)
    line.setStyleSheet("border: 3px solid black;")  # Add a border to the vertical line

    # custom image ui
    row_background = ResizeImage(QPixmap(BG1_IMAGE), True)  # Use the ResizeImage class to handle resizing

    # build custom row ui to display device information
    row_layout.addSpacing(20)
    row_layout.addWidget(QLabel(f"ID: {device['device_id']}"))
    #row_layout.addWidget(QLabel(f"ID: {device.device_id}"))
    row_layout.addSpacing(20)
    row_layout.addWidget(QLabel(f"Name: {device['device_name']}"))
    #row_layout.addWidget(QLabel(f"Name: {device.device_name}"))
    row_layout.addStretch()
    row_layout.addWidget(QLabel(f"Status: {device['status']}"))
    #row_layout.addWidget(QLabel(f"Status: {device.status}"))
    row_layout.addSpacing(20)

    # adds ui based on the order of the addWidget calls, the last added widget will be on top
    stack.addWidget(line)
    stack.addWidget(row_background)
    stack.addWidget(row_frame)
    stack.setCurrentWidget(row_frame)  # Set the current widget to the row frame

    # return QFrame storing ui
    # this allows the QFrame to be added to the QVBoxLayout in the create_devices_tab function
    return device_frame