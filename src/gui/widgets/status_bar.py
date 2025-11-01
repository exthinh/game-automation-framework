"""Modern Status Bar"""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt


class ModernStatusBar(QWidget):
    """Modern status bar at bottom of window."""

    def __init__(self):
        super().__init__()

        self.setFixedHeight(30)
        self.setStyleSheet("""
            ModernStatusBar {
                background-color: #252525;
                border-top: 1px solid #333333;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 5, 15, 5)

        # Status indicator
        self.status_label = QLabel("⚫ Stopped")
        self.status_label.setStyleSheet("color: #888888; font-size: 12px;")
        layout.addWidget(self.status_label)

        layout.addStretch()

        # ADB status
        self.adb_label = QLabel("📱 ADB: Checking...")
        self.adb_label.setStyleSheet("color: #888888; font-size: 12px;")
        layout.addWidget(self.adb_label)

    def set_status(self, status, text):
        """Set automation status."""
        colors = {
            "running": "#4caf50",
            "stopped": "#888888",
            "paused": "#ff9800",
            "error": "#f44336"
        }

        icons = {
            "running": "🟢",
            "stopped": "⚫",
            "paused": "🟡",
            "error": "🔴"
        }

        color = colors.get(status, "#888888")
        icon = icons.get(status, "⚫")

        self.status_label.setText(f"{icon} {text}")
        self.status_label.setStyleSheet(f"color: {color}; font-size: 12px; font-weight: 600;")

    def set_adb_status(self, connected):
        """Set ADB connection status."""
        if connected:
            self.adb_label.setText("📱 ADB: ✅ Connected")
            self.adb_label.setStyleSheet("color: #4caf50; font-size: 12px;")
        else:
            self.adb_label.setText("📱 ADB: ❌ Disconnected")
            self.adb_label.setStyleSheet("color: #f44336; font-size: 12px;")
