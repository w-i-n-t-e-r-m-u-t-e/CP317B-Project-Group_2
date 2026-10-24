from PySide6.QtWidgets import QLabel
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt

class ResizeImage(QLabel):
    def __init__(self, pixmap, ignore_aspect_ratio=False, parent=None):
        super().__init__(parent)
        self.original_pixmap = pixmap
        self.ignore_aspect_ratio = ignore_aspect_ratio
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.ignore_aspect_ratio:
            self.setPixmap(self.original_pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            ))
        else:
            self.setPixmap(self.original_pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            ))