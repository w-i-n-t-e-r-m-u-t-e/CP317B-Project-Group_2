from PySide6.QtWidgets import QTabWidget
from .home_tab import create_home_tab
from .devices_tab import create_devices_tab

def tab_container():
    tabs = QTabWidget()
    tabs.addTab(create_home_tab(), "Home")
    tabs.addTab(create_devices_tab(), "Devices")
    return tabs