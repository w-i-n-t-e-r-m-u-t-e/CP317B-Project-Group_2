from PySide6.QtWidgets import QFrame, QStackedLayout, QWidget, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon
from styles.styles import REGISTER_BUTTON_IMAGE

def create_home_tab():
    home_tab = QWidget()
    home_layout = QVBoxLayout(home_tab)
    reg_frame = QFrame()
    device_registration_frame = QStackedLayout(reg_frame)
    device_registration_frame.setStackingMode(QStackedLayout.StackAll)
    device_registration_boarder = QFrame()

    device_registration_boarder.setFrameShape(QFrame.Shape.VLine)
    device_registration_boarder.setFrameShadow(QFrame.Shadow.Sunken)
    device_registration_boarder.setStyleSheet("border: 3px solid black;")  # Add a border to the vertical line

    registration_button = QPushButton()
    registration_button.setIcon(QIcon(REGISTER_BUTTON_IMAGE))
    registration_button.clicked.connect(refresh)  # Connect the button click to the refresh function
    registration_button.setIconSize(QSize(100, 100))  # Set the icon size by pixel count

    # add the ui to the device registration frame
    device_registration_frame.addWidget(device_registration_boarder)
    device_registration_frame.addWidget(registration_button)
    device_registration_frame.setCurrentWidget(registration_button)

    # add the ui to main layout
    home_layout.addWidget(reg_frame)
    home_layout.addWidget(QLabel("This is the Home tab."))
    return home_tab

def refresh():
    print("Refreshing Home tab...")