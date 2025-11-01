"""Control Panel Widget"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QFrame
from PyQt6.QtCore import Qt, pyqtSignal


class ControlPanel(QWidget):
    """Control panel with start/stop/pause buttons."""

    start_clicked = pyqtSignal()
    pause_clicked = pyqtSignal()
    stop_clicked = pyqtSignal()

    def __init__(self):
        super().__init__()

        self.setStyleSheet("""
            ControlPanel {
                background-color: #2d2d2d;
                border-top: 1px solid #404040;
                padding: 15px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # Title
        label = QWidget()
        label.setStyleSheet("font-size: 12px; color: #888888; font-weight: 600; margin-bottom: 10px;")

        # Start button
        self.start_button = QPushButton("▶ START")
        self.start_button.setProperty("class", "success")
        self.start_button.setMinimumHeight(45)
        self.start_button.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                font-weight: 700;
                border-radius: 8px;
            }
        """)
        self.start_button.clicked.connect(self.start_clicked.emit)
        layout.addWidget(self.start_button)

        # Pause button
        self.pause_button = QPushButton("⏸ PAUSE")
        self.pause_button.setProperty("class", "warning")
        self.pause_button.setMinimumHeight(40)
        self.pause_button.setEnabled(False)
        self.pause_button.clicked.connect(self.pause_clicked.emit)
        layout.addWidget(self.pause_button)

        # Stop button
        self.stop_button = QPushButton("⏹ STOP")
        self.stop_button.setProperty("class", "danger")
        self.stop_button.setMinimumHeight(40)
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_clicked.emit)
        layout.addWidget(self.stop_button)

    def set_running(self, running):
        """Update button states based on running status."""
        self.start_button.setEnabled(not running)
        self.pause_button.setEnabled(running)
        self.stop_button.setEnabled(running)
