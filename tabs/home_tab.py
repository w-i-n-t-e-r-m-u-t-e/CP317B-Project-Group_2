from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

def create_home_tab():
    home_tab = QWidget()
    home_layout = QVBoxLayout(home_tab)
    home_layout.addWidget(QLabel("This is the Home tab."))
    return home_tab