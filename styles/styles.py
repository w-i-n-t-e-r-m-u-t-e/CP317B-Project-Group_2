from pathlib import Path


STYLE_DIR = Path(__file__).resolve().parent


def image_path(filename: str) -> str:
    """Return an absolute path to an image stored in the styles directory."""
    return str((STYLE_DIR / filename).resolve())


BG1_IMAGE = image_path("bg1.png")

DEVICE_ROW_STYLE = """
QFrame#deviceRow {
    background-color: #f2f4f7;
    border: 1px solid #c8ced8;
    border-radius: 6px;
}
QFrame#deviceRow QLabel {
    color: #202733;
    border: none;
}
"""

DEVICE_DIVIDER_STYLE = "border: 1px solid #c8ced8;"
