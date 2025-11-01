"""
Dashboard Page - Overview and Real-time Status

Shows real-time automation status, activity timeline, and quick stats.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QGridLayout, QScrollArea, QTextEdit
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont


class DashboardPage(QWidget):
    """Main dashboard showing automation overview."""

    def __init__(self, scheduler=None, adb=None):
        super().__init__()

        self.scheduler = scheduler
        self.adb = adb

        self._setup_ui()
        self._setup_updates()

    def _setup_ui(self):
        """Setup dashboard UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Top stats cards
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(15)

        self.uptime_card = self._create_stat_card("⏱", "Uptime", "00:00:00")
        self.success_card = self._create_stat_card("✅", "Successful", "0")
        self.failed_card = self._create_stat_card("❌", "Failed", "0")
        self.rate_card = self._create_stat_card("📊", "Success Rate", "0%")

        stats_layout.addWidget(self.uptime_card)
        stats_layout.addWidget(self.success_card)
        stats_layout.addWidget(self.failed_card)
        stats_layout.addWidget(self.rate_card)

        layout.addLayout(stats_layout)

        # Middle row - Status and System Health
        middle_layout = QHBoxLayout()
        middle_layout.setSpacing(15)

        # Current status card
        status_card = self._create_card("🎯 Current Status")
        status_layout = QVBoxLayout()

        self.current_activity = QLabel("Idle")
        self.current_activity.setObjectName("currentActivity")
        self.current_activity.setStyleSheet("font-size: 18px; font-weight: 600; color: #4a9eff;")
        status_layout.addWidget(self.current_activity)

        self.next_activity = QLabel("Next: --")
        self.next_activity.setStyleSheet("font-size: 14px; color: #b0b0b0; margin-top: 10px;")
        status_layout.addWidget(self.next_activity)

        status_card.layout().addLayout(status_layout)
        middle_layout.addWidget(status_card, 1)

        # System health card
        health_card = self._create_card("💚 System Health")
        health_layout = QVBoxLayout()

        self.adb_status = self._create_status_item("📱 ADB Connection", "Checking...")
        self.emulator_status = self._create_status_item("🎮 Emulator", "Checking...")
        self.screen_status = self._create_status_item("📸 Screenshot", "Checking...")

        health_layout.addWidget(self.adb_status)
        health_layout.addWidget(self.emulator_status)
        health_layout.addWidget(self.screen_status)

        health_card.layout().addLayout(health_layout)
        middle_layout.addWidget(health_card, 1)

        layout.addLayout(middle_layout)

        # Activity Timeline
        timeline_card = self._create_card("📅 Upcoming Activities")
        self.timeline_container = QVBoxLayout()

        self.timeline_items = []
        for i in range(5):
            item = self._create_timeline_item("--", "--", "⏳")
            self.timeline_items.append(item)
            self.timeline_container.addWidget(item)

        timeline_card.layout().addLayout(self.timeline_container)
        layout.addWidget(timeline_card)

        # Live console log
        log_card = self._create_card("📝 Live Console")

        self.console_log = QTextEdit()
        self.console_log.setReadOnly(True)
        self.console_log.setMaximumHeight(200)
        self.console_log.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                color: #e0e0e0;
                border: 1px solid #333333;
                border-radius: 6px;
                padding: 10px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
            }
        """)

        log_card.layout().addWidget(self.console_log)
        layout.addWidget(log_card)

        layout.addStretch()

    def _create_stat_card(self, icon, title, value):
        """Create a stat card."""
        card = QFrame()
        card.setObjectName("statCard")
        card.setProperty("class", "statCard")

        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(5)

        # Icon and title
        header_layout = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 24px;")
        header_layout.addWidget(icon_label)

        title_label = QLabel(title)
        title_label.setStyleSheet("color: #888888; font-size: 11px; font-weight: 600;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        card_layout.addLayout(header_layout)

        # Value
        value_label = QLabel(value)
        value_label.setObjectName(f"{title.lower().replace(' ', '_')}_value")
        value_label.setStyleSheet("font-size: 28px; font-weight: 700; color: #ffffff; margin-top: 10px;")
        card_layout.addWidget(value_label)

        # Store reference
        card.value_label = value_label

        return card

    def _create_card(self, title):
        """Create a standard card with title."""
        card = QFrame()
        card.setProperty("class", "card")
        card.setStyleSheet("""
            QFrame[class="card"] {
                background-color: #252525;
                border: 1px solid #333333;
                border-radius: 8px;
                padding: 0px;
            }
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 16px; font-weight: 600; color: #ffffff;")
        layout.addWidget(title_label)

        return card

    def _create_status_item(self, label, status):
        """Create a system status item."""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 5, 0, 5)

        label_widget = QLabel(label)
        label_widget.setStyleSheet("font-size: 14px; color: #e0e0e0;")
        layout.addWidget(label_widget)

        layout.addStretch()

        status_widget = QLabel(status)
        status_widget.setObjectName(f"{label}_status")
        status_widget.setStyleSheet("font-size: 13px; color: #888888;")
        layout.addWidget(status_widget)

        container.status_widget = status_widget

        return container

    def _create_timeline_item(self, activity, time_str, icon):
        """Create a timeline item."""
        item = QFrame()
        item.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border: 1px solid #404040;
                border-radius: 6px;
                padding: 10px;
                margin: 2px 0;
            }
            QFrame:hover {
                background-color: #323232;
                border-color: #4a9eff;
            }
        """)

        layout = QHBoxLayout(item)
        layout.setContentsMargins(10, 8, 10, 8)

        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 16px;")
        layout.addWidget(icon_label)

        name_label = QLabel(activity)
        name_label.setStyleSheet("font-size: 14px; color: #e0e0e0; font-weight: 500;")
        layout.addWidget(name_label)

        layout.addStretch()

        time_label = QLabel(time_str)
        time_label.setStyleSheet("font-size: 13px; color: #888888; font-family: 'Consolas', monospace;")
        layout.addWidget(time_label)

        item.name_label = name_label
        item.time_label = time_label
        item.icon_label = icon_label

        return item

    def _setup_updates(self):
        """Setup periodic updates."""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.refresh)
        self.update_timer.start(1000)

    def refresh(self):
        """Refresh dashboard data."""
        if not self.scheduler:
            return

        try:
            status = self.scheduler.get_status()

            # Update stat cards
            self.uptime_card.value_label.setText(status.get('uptime_formatted', '00:00:00'))
            self.success_card.value_label.setText(str(status.get('successful_executions', 0)))
            self.failed_card.value_label.setText(str(status.get('failed_executions', 0)))
            self.rate_card.value_label.setText(f"{status.get('success_rate_percent', 0)}%")

            # Update current activity
            current = status.get('current_activity', 'Idle')
            self.current_activity.setText(current if current else "Idle")

            # Update next activities
            next_activities = self.scheduler.get_next_scheduled_activities(5)

            for i, item in enumerate(self.timeline_items):
                if i < len(next_activities):
                    act = next_activities[i]
                    item.name_label.setText(act['name'])

                    time_until = int(act['time_until'])
                    if time_until < 0:
                        time_str = "NOW"
                        icon = "▶️"
                    elif time_until < 60:
                        time_str = f"in {time_until}s"
                        icon = "⏳"
                    else:
                        time_str = f"in {time_until//60}m {time_until%60}s"
                        icon = "⏰"

                    item.time_label.setText(time_str)
                    item.icon_label.setText(icon)
                else:
                    item.name_label.setText("--")
                    item.time_label.setText("--")
                    item.icon_label.setText("⏳")

            # Update system health
            if self.adb:
                if self.adb.is_connected():
                    self.adb_status.status_widget.setText("✅ Connected")
                    self.adb_status.status_widget.setStyleSheet("font-size: 13px; color: #4caf50; font-weight: 600;")
                else:
                    self.adb_status.status_widget.setText("❌ Disconnected")
                    self.adb_status.status_widget.setStyleSheet("font-size: 13px; color: #f44336; font-weight: 600;")

        except Exception as e:
            print(f"Dashboard refresh error: {e}")

    def log_message(self, message):
        """Add message to console log."""
        self.console_log.append(message)

        # Auto-scroll to bottom
        scrollbar = self.console_log.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
