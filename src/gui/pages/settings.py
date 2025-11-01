"""Settings Page - Application Configuration"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QSpinBox, QCheckBox, QGroupBox
)
from PyQt6.QtCore import Qt


class SettingsPage(QWidget):
    """Settings configuration page."""

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        label = QLabel("🔧 Settings")
        label.setStyleSheet("font-size: 18px; font-weight: 600;")
        layout.addWidget(label)

        # Emulator settings
        emulator_group = QGroupBox("Emulator Connection")
        emulator_layout = QVBoxLayout(emulator_group)

        device_layout = QHBoxLayout()
        device_layout.addWidget(QLabel("Device ID:"))
        device_input = QLineEdit("127.0.0.1:5555")
        device_layout.addWidget(device_input, 1)
        device_layout.addWidget(QPushButton("🔄 Scan"))
        emulator_layout.addLayout(device_layout)

        layout.addWidget(emulator_group)

        # Behavior settings
        behavior_group = QGroupBox("Behavior")
        behavior_layout = QVBoxLayout(behavior_group)

        variance_layout = QHBoxLayout()
        variance_layout.addWidget(QLabel("Click Variance:"))
        variance_spin = QSpinBox()
        variance_spin.setValue(5)
        variance_spin.setSuffix(" px")
        variance_layout.addWidget(variance_spin)
        variance_layout.addStretch()
        behavior_layout.addLayout(variance_layout)

        behavior_layout.addWidget(QCheckBox("Enable Screenshot Cache"))
        behavior_layout.addWidget(QCheckBox("Save Screenshots on Error"))

        layout.addWidget(behavior_group)

        layout.addStretch()

        # Save button
        save_button = QPushButton("💾 Save Settings")
        save_button.setProperty("class", "primary")
        layout.addWidget(save_button)

    def refresh(self):
        """Refresh settings."""
        pass
