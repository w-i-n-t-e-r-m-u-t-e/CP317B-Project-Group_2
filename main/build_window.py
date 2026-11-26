from PySide6.QtWidgets import QWidget, QVBoxLayout
from tabs.devices_tab import create_devices_screen
from styles.styles import APP_STYLE

def build_window():
    window = QWidget()
    window.setWindowTitle("System Security & Update Manager")

    layout = QVBoxLayout(window)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(create_devices_screen())
    window.setStyleSheet(APP_STYLE)

    window.resize(1000, 500)
    window.show()
    return window