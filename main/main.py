import sys

from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout, QWidget, QTabWidget


def main():
    app = QApplication(sys.argv)

    window = QWidget()
    window.setWindowTitle("My First PySide6 App")

    message = QLabel("Hello! Welcome to PySide6.")
    button_test = QPushButton("Click me")
    button_test.clicked.connect(lambda: message.setText("You clicked the button!"))

    home_tab = QWidget()
    home_layout = QVBoxLayout(home_tab)
    home_layout.addWidget(message)
    home_layout.addWidget(button_test)

    about_tab = QWidget()
    about_layout = QVBoxLayout(about_tab)
    about_layout.addWidget(QLabel("This is a basic PySide6 tabbed application."))

    tabs = QTabWidget()
    tabs.addTab(home_tab, "Home")
    tabs.addTab(about_tab, "About")

    layout = QVBoxLayout(window)
    layout.addWidget(tabs)

    window.resize(320, 120)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
