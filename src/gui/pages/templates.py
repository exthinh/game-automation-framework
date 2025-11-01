"""Templates Page - Manage Template Images"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGridLayout, QScrollArea, QFrame, QPushButton
)
from PyQt6.QtCore import Qt


class TemplatesPage(QWidget):
    """Template management page."""

    def __init__(self, screen=None):
        super().__init__()
        self.screen = screen

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        label = QLabel("🖼️ Template Manager")
        label.setStyleSheet("font-size: 18px; font-weight: 600;")
        layout.addWidget(label)

        info = QLabel("Manage and test template images for UI recognition")
        info.setStyleSheet("color: #888888; margin-bottom: 20px;")
        layout.addWidget(info)

        layout.addStretch()

    def refresh(self):
        """Refresh template list."""
        pass
