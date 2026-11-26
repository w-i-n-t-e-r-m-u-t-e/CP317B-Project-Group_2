"""The table of every device."""
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QAbstractItemView, QHBoxLayout, QHeaderView, QPushButton, QTableWidget,
                               QTableWidgetItem, QWidget)

# column title -> field name in the backend response
COLUMNS = {"Name": "deviceName", "IP": "ip", "Owner": "trust", "Type": "deviceType", "Version": "deviceVersion",
           "Status": "status", "Last updated": "lastUpdated"}
STATUS_STYLE = {"UPDATED": ("Updated", "#15803d"), "OUTDATED": ("Outdated", "#c2410c"),
                "SUPPORTED": ("Supported", "#15803d"), "UNSUPPORTED": ("No updates", "#b91c1c"),
                "UNKNOWN": ("Unknown", "#6b7280")}
OWNER = {"MINE": "Mine", "GUEST": "Guest", "UNKNOWN": "Don't know", None: "New"}


def create_table():
    table = QTableWidget(0, len(COLUMNS) + 1)  # last column holds the row buttons
    table.setHorizontalHeaderLabels([*COLUMNS, ""])
    table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    table.horizontalHeader().setSectionResizeMode(len(COLUMNS), QHeaderView.ResizeMode.Fixed)
    table.setColumnWidth(len(COLUMNS), 170)
    table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
    table.setColumnWidth(0, 200)  # names are what people recognise
    table.verticalHeader().hide()
    table.verticalHeader().setDefaultSectionSize(44)
    table.setShowGrid(False)
    table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    return table


def row_buttons(device, on_edit, on_delete):
    box = QWidget()
    box.setStyleSheet("background: transparent;")
    box_layout = QHBoxLayout(box)
    box_layout.setContentsMargins(6, 0, 6, 0)
    for label, action in (("Edit", on_edit), ("Delete", on_delete)):
        button = QPushButton(label)
        button.setObjectName("row")
        button.clicked.connect(lambda _, action=action: action(device))
        box_layout.addWidget(button)
    return box

def fill_table(table, devices, statuses, on_edit, on_delete):
    table.setRowCount(len(devices))
    for row, device in enumerate(devices):
        for column, key in enumerate(COLUMNS.values()):
            item = QTableWidgetItem(OWNER[device[key]] if key == "trust" else device[key] or "—")
            item.setToolTip(item.text())  # long values such as IPv6 addresses get cut off
            if key == "status":
                text, color = STATUS_STYLE[statuses[row]]
                item.setText(f"● {text}")
                item.setForeground(QColor(color))
            table.setItem(row, column, item)
        table.setCellWidget(row, len(COLUMNS), row_buttons(device, on_edit, on_delete))


def filter_rows(table, query):
    """Hide the rows whose name and IP do not contain the query."""
    text = query.strip().lower()
    for row in range(table.rowCount()):
        name, ip = table.item(row, 0).text(), table.item(row, 1).text()
        table.setRowHidden(row, text not in name.lower() and text not in ip.lower())
