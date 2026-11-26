"""The "needs your attention" cards."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget
from utils import releases
from utils.attention import attention
from utils.ports import explain


def newest(device, latest):
    typed = latest.get(device["deviceType"])
    if typed:  # the same version the status was worked out from
        return typed
    release = releases.release_for(device["deviceType"], device["deviceVersion"])
    return (release or {}).get("latest") or "the newest version"

def build_card(kind, device, latest, on_trust, on_rename, on_edit):
    name = device["deviceName"]
    risks = explain(device["openPorts"])
    question, advice = {
        "new": (f"New device: {name}", "Is this yours?"),
        "stranger": (f"You don't recognise: {name}",
                     "If nobody at home owns it, change your Wi-Fi password in your router's settings."),
        "risk": (f"{name} has {' and '.join(service for service, _ in risks)} turned on",
                 "\n".join(text for _, text in risks)),
        "unsupported": (f"{name} no longer gets security updates",
                        "Upgrade to a newer system if it allows it. If not, plan to replace it."),
        "outdated": (f"{name} is out of date",
                     f"It has {device['deviceVersion']}. Install {newest(device, latest)} from Software update."),
    }[kind]
    box = QFrame()
    box.setObjectName("card")
    box_layout = QVBoxLayout(box)
    heading = QLabel(question)
    heading.setObjectName("cardTitle")
    heading.setTextFormat(Qt.TextFormat.PlainText)  # names come from other devices
    text = QLabel(f"{advice}\nAddress: {device['ip']}")
    text.setWordWrap(True)
    box_layout.addWidget(heading)
    box_layout.addWidget(text)
    choices = {
        "new": [("Mine", lambda: on_trust(device, "MINE")),
                ("Guest", lambda: on_trust(device, "GUEST")),
                ("I don't know it", lambda: on_trust(device, "UNKNOWN"))],
        "stranger": [("It's mine", lambda: on_trust(device, "MINE")),
                     ("It's a guest", lambda: on_trust(device, "GUEST"))],
        "outdated": [("Change version", lambda: on_edit(device))],
        "unsupported": [("Change version", lambda: on_edit(device))],
        "risk": [],  # scan again after turning the service off
    }[kind] + [("Rename", lambda: on_rename(device))]
    row = QHBoxLayout()
    for label, action in choices:
        button = QPushButton(label)
        button.clicked.connect(lambda _, action=action: action())
        row.addWidget(button)
    row.addStretch()
    box_layout.addLayout(row)
    return box

def card_list(devices, statuses, latest, on_trust, on_rename, on_edit):
    """A widget holding one card for each thing that needs attention."""
    content = QWidget()
    content_layout = QVBoxLayout(content)
    content_layout.setContentsMargins(0, 0, 0, 0)
    # ponytail: builds every card at once; page them if a network has hundreds of devices
    for kind, device in attention(devices, statuses):
        content_layout.addWidget(build_card(kind, device, latest, on_trust, on_rename, on_edit))
    content_layout.addStretch()
    return content
