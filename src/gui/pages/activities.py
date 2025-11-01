"""
Activities Page - Manage and Configure Activities

View, enable/disable, configure, and manually trigger activities.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QScrollArea, QLineEdit, QComboBox, QDialog,
    QSpinBox, QDoubleSpinBox, QCheckBox, QSlider, QGridLayout
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont


class ActivityCard(QFrame):
    """Card displaying single activity with controls."""

    run_clicked = pyqtSignal(str)  # activity_id
    configure_clicked = pyqtSignal(str)
    toggle_clicked = pyqtSignal(str, bool)

    def __init__(self, activity_data, parent=None):
        super().__init__(parent)

        self.activity_data = activity_data
        self._setup_ui()

    def _setup_ui(self):
        """Setup activity card UI."""
        self.setStyleSheet("""
            ActivityCard {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #2d2d2d,
                    stop:1 #252525
                );
                border: 1px solid #404040;
                border-radius: 12px;
                padding: 0px;
            }
            ActivityCard:hover {
                border-color: #4a9eff;
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #323232,
                    stop:1 #2a2a2a
                );
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(12)

        # Header row
        header_layout = QHBoxLayout()

        # Activity name and status
        name_layout = QVBoxLayout()
        name_layout.setSpacing(5)

        self.name_label = QLabel(self.activity_data.get('name', 'Unknown'))
        self.name_label.setStyleSheet("font-size: 16px; font-weight: 600; color: #ffffff;")
        name_layout.addWidget(self.name_label)

        self.status_label = QLabel(self._get_status_text())
        self.status_label.setStyleSheet("font-size: 12px; color: #888888;")
        name_layout.addWidget(self.status_label)

        header_layout.addLayout(name_layout)
        header_layout.addStretch()

        # Enable toggle
        self.enable_checkbox = QCheckBox("Enabled")
        self.enable_checkbox.setChecked(self.activity_data.get('enabled', False))
        self.enable_checkbox.toggled.connect(self._on_toggle)
        header_layout.addWidget(self.enable_checkbox)

        layout.addLayout(header_layout)

        # Stats row
        stats_layout = QHBoxLayout()

        # Priority
        priority = self.activity_data.get('priority', 5)
        priority_widget = self._create_stat("Priority", f"{priority}/10", self._get_priority_color(priority))
        stats_layout.addWidget(priority_widget)

        # Interval
        hours = self.activity_data.get('interval_hours', 0)
        minutes = self.activity_data.get('interval_minutes', 0)
        interval_text = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
        interval_widget = self._create_stat("Interval", interval_text, "#888888")
        stats_layout.addWidget(interval_widget)

        # Next run
        next_widget = self._create_stat("Next Run", "Calculating...", "#888888")
        self.next_run_label = next_widget.value_label
        stats_layout.addWidget(next_widget)

        # Success rate
        success_widget = self._create_stat("Success", "0/0 (0%)", "#888888")
        self.success_label = success_widget.value_label
        stats_layout.addWidget(success_widget)

        stats_layout.addStretch()

        layout.addLayout(stats_layout)

        # Progress bar for priority
        self.priority_bar = QSlider(Qt.Orientation.Horizontal)
        self.priority_bar.setMinimum(1)
        self.priority_bar.setMaximum(10)
        self.priority_bar.setValue(priority)
        self.priority_bar.setEnabled(False)
        self.priority_bar.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                height: 6px;
                background: #2d2d2d;
                border-radius: 3px;
            }}
            QSlider::sub-page:horizontal {{
                background: {self._get_priority_color(priority)};
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {self._get_priority_color(priority)};
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }}
        """)
        layout.addWidget(self.priority_bar)

        # Action buttons
        actions_layout = QHBoxLayout()

        self.run_button = QPushButton("▶ Run Now")
        self.run_button.setProperty("class", "success")
        self.run_button.clicked.connect(lambda: self.run_clicked.emit(self.activity_data['id']))
        actions_layout.addWidget(self.run_button)

        self.config_button = QPushButton("⚙ Configure")
        self.config_button.clicked.connect(lambda: self.configure_clicked.emit(self.activity_data['id']))
        actions_layout.addWidget(self.config_button)

        actions_layout.addStretch()

        layout.addLayout(actions_layout)

    def _create_stat(self, label, value, color):
        """Create a stat label."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)

        label_widget = QLabel(label)
        label_widget.setStyleSheet("font-size: 11px; color: #888888; font-weight: 600;")
        layout.addWidget(label_widget)

        value_widget = QLabel(value)
        value_widget.setStyleSheet(f"font-size: 14px; color: {color}; font-weight: 600;")
        layout.addWidget(value_widget)

        container.value_label = value_widget

        return container

    def _get_status_text(self):
        """Get activity status text."""
        if not self.activity_data.get('enabled'):
            return "💤 Disabled"
        return "⏳ Scheduled"

    def _get_priority_color(self, priority):
        """Get color based on priority."""
        if priority >= 9:
            return "#f44336"  # Red (critical)
        elif priority >= 7:
            return "#ff9800"  # Orange (high)
        elif priority >= 5:
            return "#4a9eff"  # Blue (normal)
        else:
            return "#888888"  # Gray (low)

    def _on_toggle(self, checked):
        """Handle enable/disable toggle."""
        self.toggle_clicked.emit(self.activity_data['id'], checked)
        self.status_label.setText(self._get_status_text())

    def update_stats(self, next_run_time, success_count, fail_count):
        """Update activity stats."""
        # Update next run
        if next_run_time:
            self.next_run_label.setText(next_run_time)
        else:
            self.next_run_label.setText("--")

        # Update success rate
        total = success_count + fail_count
        if total > 0:
            rate = int((success_count / total) * 100)
            self.success_label.setText(f"{success_count}/{total} ({rate}%)")

            if rate >= 90:
                self.success_label.setStyleSheet("font-size: 14px; color: #4caf50; font-weight: 600;")
            elif rate >= 70:
                self.success_label.setStyleSheet("font-size: 14px; color: #ff9800; font-weight: 600;")
            else:
                self.success_label.setStyleSheet("font-size: 14px; color: #f44336; font-weight: 600;")


class ActivitiesPage(QWidget):
    """Activities management page."""

    def __init__(self, scheduler=None):
        super().__init__()

        self.scheduler = scheduler
        self.activity_cards = {}

        self._setup_ui()

    def _setup_ui(self):
        """Setup activities page UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Header with search and filters
        header_layout = QHBoxLayout()

        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search activities...")
        self.search_input.textChanged.connect(self._filter_activities)
        header_layout.addWidget(self.search_input, 1)

        # Filter combo
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All Activities", "Enabled Only", "Disabled Only", "High Priority"])
        self.filter_combo.currentTextChanged.connect(self._filter_activities)
        header_layout.addWidget(self.filter_combo)

        # Add button
        add_button = QPushButton("+ New Activity")
        add_button.setProperty("class", "primary")
        header_layout.addWidget(add_button)

        layout.addLayout(header_layout)

        # Scroll area for activities
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        scroll_widget = QWidget()
        self.activities_layout = QVBoxLayout(scroll_widget)
        self.activities_layout.setSpacing(15)
        self.activities_layout.setContentsMargins(0, 0, 0, 0)

        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        # Load activities
        self._load_activities()

    def _load_activities(self):
        """Load activities from scheduler."""
        # Clear existing
        while self.activities_layout.count():
            item = self.activities_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.activity_cards.clear()

        if not self.scheduler:
            # Show placeholder
            placeholder = QLabel("No scheduler connected")
            placeholder.setStyleSheet("font-size: 14px; color: #888888; padding: 40px;")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.activities_layout.addWidget(placeholder)
            return

        # Load from config (we'll need to pass activity data)
        # For now, create sample activities
        sample_activities = [
            {"id": "alliance_help", "name": "Alliance Help", "enabled": True, "priority": 9,
             "interval_hours": 0, "interval_minutes": 8},
            {"id": "vip_collection", "name": "VIP Collection", "enabled": True, "priority": 8,
             "interval_hours": 1, "interval_minutes": 0},
            {"id": "daily_login", "name": "Daily Login", "enabled": True, "priority": 10,
             "interval_hours": 24, "interval_minutes": 0},
            {"id": "resource_gathering", "name": "Resource Gathering", "enabled": False, "priority": 5,
             "interval_hours": 2, "interval_minutes": 30},
            {"id": "barbarian_hunt", "name": "Barbarian Hunt", "enabled": True, "priority": 7,
             "interval_hours": 3, "interval_minutes": 0},
        ]

        for activity_data in sample_activities:
            card = ActivityCard(activity_data)
            card.run_clicked.connect(self._run_activity)
            card.configure_clicked.connect(self._configure_activity)
            card.toggle_clicked.connect(self._toggle_activity)

            self.activities_layout.addWidget(card)
            self.activity_cards[activity_data['id']] = card

        self.activities_layout.addStretch()

    def _filter_activities(self):
        """Filter activities based on search and filter."""
        search_text = self.search_input.text().lower()
        filter_type = self.filter_combo.currentText()

        for activity_id, card in self.activity_cards.items():
            # Search filter
            name_match = search_text in card.activity_data['name'].lower()

            # Type filter
            type_match = True
            if filter_type == "Enabled Only":
                type_match = card.activity_data.get('enabled', False)
            elif filter_type == "Disabled Only":
                type_match = not card.activity_data.get('enabled', False)
            elif filter_type == "High Priority":
                type_match = card.activity_data.get('priority', 0) >= 7

            # Show/hide card
            card.setVisible(name_match and type_match)

    def _run_activity(self, activity_id):
        """Run activity manually."""
        print(f"Running activity: {activity_id}")
        # TODO: Implement manual run

    def _configure_activity(self, activity_id):
        """Open configuration dialog."""
        print(f"Configuring activity: {activity_id}")
        # TODO: Implement configuration dialog

    def _toggle_activity(self, activity_id, enabled):
        """Toggle activity enabled state."""
        print(f"Toggle activity {activity_id}: {enabled}")
        # TODO: Update config

    def refresh(self):
        """Refresh activities data."""
        # Update stats for each card
        for activity_id, card in self.activity_cards.items():
            # TODO: Get real stats from scheduler
            card.update_stats("5m 23s", 12, 1)
