"""Statistics Page - Analytics and Charts"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt


class StatisticsPage(QWidget):
    """Statistics and analytics page."""

    def __init__(self, scheduler=None):
        super().__init__()
        self.scheduler = scheduler

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        label = QLabel("📈 Statistics & Analytics")
        label.setStyleSheet("font-size: 18px; font-weight: 600;")
        layout.addWidget(label)

        info = QLabel("Activity execution history and performance metrics")
        info.setStyleSheet("color: #888888; margin-bottom: 20px;")
        layout.addWidget(info)

        layout.addStretch()

    def refresh(self):
        """Refresh statistics."""
        pass
