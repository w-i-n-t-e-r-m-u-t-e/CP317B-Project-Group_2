"""The main screen: a table of devices with the scan and register buttons above it."""
import json
from concurrent.futures import ThreadPoolExecutor
from urllib.request import Request, urlopen
from PySide6.QtCore import QSettings, QTimer
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QAbstractItemView, QHBoxLayout, QHeaderView, QLabel,
                               QLineEdit, QMessageBox,
                               QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)
from tabs.register_dialog import RegisterDialog
from tabs.versions_dialog import VersionsDialog
from utils.scan import API_URL, scan
from utils.version import status_of

# column title -> field name in the backend response
COLUMNS = {"Name": "deviceName", "IP": "ip", "Type": "deviceType", "Version": "deviceVersion",
           "Status": "status", "Last updated": "lastUpdated"}
STATUS_STYLE = {"UPDATED": ("Updated", "#15803d"), "OUTDATED": ("Outdated", "#c2410c"),
                "UNKNOWN": ("Unknown", "#6b7280")}


def create_devices_screen():
    screen = QWidget()
    layout = QVBoxLayout(screen)
    layout.setContentsMargins(20, 20, 20, 20)
    layout.setSpacing(12)

    title = QLabel("Devices")
    title.setObjectName("title")
    scan_button = QPushButton("Scan network")
    scan_button.setToolTip("Only scan networks you have permission to scan.")
    register_button = QPushButton("Register device")
    register_button.setObjectName("primary")
    toolbar = QHBoxLayout()
    toolbar.addWidget(title)
    toolbar.addStretch()
    toolbar.addWidget(scan_button)
    toolbar.addWidget(register_button)

    summary = QLabel()
    # latest version per device type, typed in by hand and remembered on this computer only
    settings = QSettings("CP317-Group2", "DeviceManager")
    types = []  # types of the devices currently listed
    versions_button = QPushButton("Latest versions")
    summary_row = QHBoxLayout()
    summary_row.addWidget(summary)
    summary_row.addStretch()
    summary_row.addWidget(versions_button)
    search = QLineEdit()
    search.setPlaceholderText("Search by name or IP")
    search.setClearButtonEnabled(True)

    table = QTableWidget(0, len(COLUMNS) + 1)  # last column holds the row buttons
    table.setHorizontalHeaderLabels([*COLUMNS, ""])
    table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    table.horizontalHeader().setSectionResizeMode(len(COLUMNS), QHeaderView.ResizeMode.Fixed)
    table.setColumnWidth(len(COLUMNS), 170)
    table.verticalHeader().hide()
    table.verticalHeader().setDefaultSectionSize(44)
    table.setShowGrid(False)
    table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    status = QLabel()

    def apply_search():
        text = search.text().strip().lower()
        for row in range(table.rowCount()):
            name, ip = table.item(row, 0).text(), table.item(row, 1).text()
            table.setRowHidden(row, text not in name.lower() and text not in ip.lower())

    def row_buttons(device):
        box = QWidget()
        box.setStyleSheet("background: transparent;")
        box_layout = QHBoxLayout(box)
        box_layout.setContentsMargins(6, 0, 6, 0)
        for label, action in (("Edit", edit), ("Delete", delete)):
            button = QPushButton(label)
            button.setObjectName("row")
            button.clicked.connect(lambda _, action=action: action(device))
            box_layout.addWidget(button)
        return box

    def edit(device):
        if RegisterDialog(screen, device).exec():
            reload()

    def delete(device):
        answer = QMessageBox.question(screen, "Delete device", f"Delete {device['deviceName']}?")
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            urlopen(Request(f"{API_URL}/{device['id']}", method="DELETE"), timeout=3).close()
        except OSError:
            status.setText("Could not delete. Is the backend running?")
            return
        reload()

    def reload():
        try:
            # ponytail: blocks the UI up to 3s; use a thread if the backend gets slow
            with urlopen(API_URL, timeout=3) as response:
                devices = json.load(response)
        except OSError:
            table.setRowCount(0)
            summary.clear()
            status.setText("Could not reach the backend. Is it running?")
            return
        table.setRowCount(len(devices))
        latest = settings.value("latest_by_type", {}) or {}
        types[:] = sorted({device["deviceType"] for device in devices if device["deviceType"]})
        statuses = [status_of(device["deviceVersion"], latest.get(device["deviceType"], "")) for device in devices]
        for row, device in enumerate(devices):
            for column, key in enumerate(COLUMNS.values()):
                item = QTableWidgetItem(device[key] or "—")
                if key == "status":
                    text, color = STATUS_STYLE[statuses[row]]
                    item.setText(f"● {text}")
                    item.setForeground(QColor(color))
                table.setItem(row, column, item)
            table.setCellWidget(row, len(COLUMNS), row_buttons(device))
        counts = "   ·   ".join(f"{statuses.count(key)} {label.lower()}" for key, (label, _) in STATUS_STYLE.items())
        summary.setText(f"{len(devices)} total   ·   {counts}")
        apply_search()
        status.setText("" if devices else "No devices yet. Scan or register one.")

    def register():
        if RegisterDialog(screen).exec():  # true only after a successful save
            reload()

    # the scan runs on its own thread; only the timer below touches the window
    worker = ThreadPoolExecutor(1)
    timer = QTimer(screen)
    timer.setInterval(200)
    job = None

    def run_scan():
        nonlocal job
        scan_button.setEnabled(False)
        scan_button.setText("Scanning...")
        status.setText("Scanning... only scan networks you have permission to scan.")
        job = worker.submit(scan)
        timer.start()

    def check_scan():
        if not job.done():
            return
        timer.stop()
        scan_button.setEnabled(True)
        scan_button.setText("Scan network")
        try:
            found, added = job.result()
        except OSError:
            status.setText("Scan failed. Check your network and that the backend is running.")
            return
        reload()
        status.setText(f"Scan found {found} devices, added {added} new.")

    timer.timeout.connect(check_scan)

    def edit_versions():
        latest = settings.value("latest_by_type", {}) or {}
        dialog = VersionsDialog(types, latest, screen)
        if dialog.exec():
            settings.setValue("latest_by_type", {**latest, **dialog.values()})
            reload()

    versions_button.clicked.connect(edit_versions)
    search.textChanged.connect(apply_search)
    scan_button.clicked.connect(run_scan)
    register_button.clicked.connect(register)

    layout.addLayout(toolbar)
    layout.addLayout(summary_row)
    layout.addWidget(search)
    layout.addWidget(table)
    layout.addWidget(status)
    reload()
    return screen
