"""The main screen: what needs attention first, with the full device table one click away."""
import json
import traceback
from concurrent.futures import ThreadPoolExecutor
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from PySide6.QtCore import QSettings, Qt, QTimer
from PySide6.QtWidgets import (QApplication, QCheckBox, QFrame, QHBoxLayout, QInputDialog, QLabel, QLineEdit,
                               QMessageBox, QPushButton, QScrollArea, QVBoxLayout, QWidget)
from tabs.attention_cards import card_list
from tabs.device_table import STATUS_STYLE, create_table, fill_table, filter_rows
from tabs.register_dialog import RegisterDialog
from tabs.versions_dialog import VersionsDialog
from utils import releases
from utils.attention import headline
from utils.scan import API_URL, save, scan
from utils.version import status_of


def create_devices_screen():
    screen = QWidget()
    layout = QVBoxLayout(screen)
    layout.setContentsMargins(20, 20, 20, 20)
    layout.setSpacing(12)

    title = QLabel("My network")
    title.setObjectName("title")
    scan_button = QPushButton("Scan network")
    scan_button.setObjectName("primary")
    scan_button.setToolTip("Only scan networks you have permission to scan.")
    register_button = QPushButton("Add by hand")
    toolbar = QHBoxLayout()
    toolbar.addWidget(title)
    toolbar.addStretch()
    # off unless ticked each time, so the app never scans a new network on its own
    auto_rescan = QCheckBox("Rescan every 15 min")
    toolbar.addWidget(auto_rescan)
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

    table = create_table()
    status = QLabel()

    verdict = QLabel()
    verdict.setObjectName("verdict")
    verdict.setWordWrap(True)
    cards = QScrollArea()
    cards.setWidgetResizable(True)
    cards.setFrameShape(QFrame.Shape.NoFrame)
    details_button = QPushButton("Show all devices")
    details_button.setCheckable(True)

    def change(device, name=None, trust=None):
        body = {"Device_Name": name or device["deviceName"], "IP": device["ip"],
                "Device_Version": device["deviceVersion"], "Trust": trust}
        try:
            save(body, device["id"])
        except HTTPError as error:
            try:
                status.setText("Could not save: " + json.load(error)["error"])
            except (ValueError, KeyError):
                status.setText("The backend rejected that change.")
            return
        except OSError:
            status.setText("Could not save that. Is the backend running?")
            return
        reload()

    def rename(device):
        name, ok = QInputDialog.getText(screen, "Rename device", "Name:", QLineEdit.EchoMode.Normal,
                                        device["deviceName"])
        if ok and name.strip():
            change(device, name=name.strip()[:25])

    def show_attention(devices, statuses, latest):
        verdict.setText(headline(devices, statuses))
        # replaces the old cards
        cards.setWidget(card_list(devices, statuses, latest, lambda device, trust: change(device, trust=trust), rename, edit))

    def toggle_details(shown):
        details_button.setText("Back to summary" if shown else "Show all devices")
        for widget in (summary, versions_button, search, table):
            widget.setVisible(shown)
        cards.setVisible(not shown)

    def apply_search():
        filter_rows(table, search.text())

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
            verdict.setText("Can't check your network right now.")
            cards.setWidget(QWidget())
            status.setText("Could not reach the backend. Is it running?")
            return
        latest = settings.value("latest_by_type", {}) or {}
        types[:] = sorted({device["deviceType"] for device in devices if device["deviceType"]})
        # a version typed under "Latest versions" wins; otherwise use the published release data
        statuses = [status_of(device["deviceVersion"], latest[device["deviceType"]])
                    if latest.get(device["deviceType"]) else
                    releases.status(device["deviceType"], device["deviceVersion"]) for device in devices]
        fetch_releases(types)
        fill_table(table, devices, statuses, edit, delete)
        counts = "   ·   ".join(f"{statuses.count(key)} {label.lower()}" for key, (label, _) in STATUS_STYLE.items())
        summary.setText(f"{len(devices)} total   ·   {counts}")
        apply_search()
        show_attention(devices, statuses, latest)
        status.setText("" if devices else "No devices yet. Scan or register one.")

    # release data comes from the internet, so fetch it off the window's thread
    loader = ThreadPoolExecutor(1)
    loading = None
    loading_timer = QTimer(screen)
    loading_timer.setInterval(300)

    def fetch_releases(kinds):
        nonlocal loading
        wanted = releases.missing(kinds)
        if wanted and (loading is None or loading.done()):
            loading = loader.submit(releases.load, wanted)
            loading_timer.start()

    def releases_ready():
        if loading.done():
            loading_timer.stop()
            reload()

    loading_timer.timeout.connect(releases_ready)

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
        except Exception as error:  # never leave the screen saying "Scanning..."
            traceback.print_exc()  # keep the details for whoever has to fix it
            status.setText(f"Scan failed unexpectedly ({type(error).__name__}).")
            return
        reload()
        status.setText(f"Scan found {found} devices, added {added} new.")
        if added:
            QApplication.alert(screen.window())  # draw attention if the app is in the background

    timer.timeout.connect(check_scan)

    def edit_versions():
        latest = settings.value("latest_by_type", {}) or {}
        dialog = VersionsDialog(types, latest, screen)
        if dialog.exec():
            settings.setValue("latest_by_type", {**latest, **dialog.values()})
            reload()

    versions_button.clicked.connect(edit_versions)
    search.textChanged.connect(apply_search)
    rescan_timer = QTimer(screen)
    rescan_timer.setInterval(15 * 60 * 1000)
    rescan_timer.timeout.connect(lambda: run_scan() if scan_button.isEnabled() else None)
    auto_rescan.toggled.connect(lambda on: rescan_timer.start() if on else rescan_timer.stop())
    details_button.toggled.connect(toggle_details)
    scan_button.clicked.connect(run_scan)
    register_button.clicked.connect(register)

    layout.addLayout(toolbar)
    layout.addWidget(verdict)
    layout.addWidget(cards)
    layout.addWidget(details_button, alignment=Qt.AlignmentFlag.AlignLeft)
    layout.addLayout(summary_row)
    layout.addWidget(search)
    layout.addWidget(table)
    layout.addWidget(status)
    toggle_details(False)
    reload()
    return screen
