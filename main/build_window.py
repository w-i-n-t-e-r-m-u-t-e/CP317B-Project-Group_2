from PySide6.QtWidgets import QWidget, QVBoxLayout
from tabs.tabs import tab_container

def build_window():
    window = QWidget()
    window.setWindowTitle("My First PySide6 App")

    layout = QVBoxLayout(window)
    layout.addWidget(tab_container())

    window.resize(1000, 500)
    window.show()
    return window