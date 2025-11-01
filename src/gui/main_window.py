"""
Main Window - Game Automation Framework GUI

Modern, sleek PyQt6 interface with dark theme and smooth animations.
"""

import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QPushButton, QLabel, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, QSize, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QIcon, QFont, QAction

from .pages.dashboard import DashboardPage
from .pages.activities import ActivitiesPage
from .pages.templates import TemplatesPage
from .pages.logs import LogsPage
from .pages.statistics import StatisticsPage
from .pages.settings import SettingsPage
from .widgets.status_bar import ModernStatusBar
from .widgets.control_panel import ControlPanel
from .styles.theme import DARK_THEME


class MainWindow(QMainWindow):
    """Modern main window with navigation sidebar and multiple pages."""

    # Signals
    start_automation = pyqtSignal()
    stop_automation = pyqtSignal()
    pause_automation = pyqtSignal()

    def __init__(self, scheduler=None, adb=None, screen=None):
        super().__init__()

        self.scheduler = scheduler
        self.adb = adb
        self.screen = screen

        self.setWindowTitle("Game Automation Framework")
        self.setMinimumSize(1280, 800)

        # Apply modern dark theme
        self.setStyleSheet(DARK_THEME)

        # Setup UI
        self._setup_ui()
        self._setup_navigation()
        self._setup_status_updates()

        # Show dashboard by default
        self.show_page(0)

    def _setup_ui(self):
        """Setup main UI layout."""
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)

        # Main layout
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Left sidebar (navigation)
        self.sidebar = self._create_sidebar()
        main_layout.addWidget(self.sidebar)

        # Right content area
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Top bar
        top_bar = self._create_top_bar()
        content_layout.addWidget(top_bar)

        # Page container
        self.pages = QStackedWidget()
        self.pages.setObjectName("pageContainer")

        # Create pages
        self.dashboard_page = DashboardPage(self.scheduler, self.adb)
        self.activities_page = ActivitiesPage(self.scheduler)
        self.templates_page = TemplatesPage(self.screen)
        self.logs_page = LogsPage()
        self.statistics_page = StatisticsPage(self.scheduler)
        self.settings_page = SettingsPage()

        # Add pages
        self.pages.addWidget(self.dashboard_page)
        self.pages.addWidget(self.activities_page)
        self.pages.addWidget(self.templates_page)
        self.pages.addWidget(self.logs_page)
        self.pages.addWidget(self.statistics_page)
        self.pages.addWidget(self.settings_page)

        content_layout.addWidget(self.pages, 1)

        # Bottom status bar
        self.status_bar = ModernStatusBar()
        content_layout.addWidget(self.status_bar)

        # Add content to main layout
        main_layout.addLayout(content_layout, 1)

    def _create_sidebar(self):
        """Create navigation sidebar."""
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(240)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Logo/Title
        title_container = QWidget()
        title_container.setObjectName("sidebarTitle")
        title_layout = QVBoxLayout(title_container)
        title_layout.setContentsMargins(20, 30, 20, 30)

        title = QLabel("🎮 Game Bot")
        title.setObjectName("appTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_layout.addWidget(title)

        subtitle = QLabel("Automation Framework")
        subtitle.setObjectName("appSubtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_layout.addWidget(subtitle)

        layout.addWidget(title_container)

        # Navigation buttons
        self.nav_buttons = []

        nav_items = [
            ("📊", "Dashboard", 0),
            ("⚙️", "Activities", 1),
            ("🖼️", "Templates", 2),
            ("📝", "Logs", 3),
            ("📈", "Statistics", 4),
            ("🔧", "Settings", 5),
        ]

        for icon, text, page_idx in nav_items:
            btn = self._create_nav_button(icon, text, page_idx)
            self.nav_buttons.append(btn)
            layout.addWidget(btn)

        # Spacer
        layout.addStretch()

        # Control panel at bottom
        self.control_panel = ControlPanel()
        self.control_panel.start_clicked.connect(self.start_automation.emit)
        self.control_panel.pause_clicked.connect(self.pause_automation.emit)
        self.control_panel.stop_clicked.connect(self.stop_automation.emit)
        layout.addWidget(self.control_panel)

        return sidebar

    def _create_nav_button(self, icon, text, page_idx):
        """Create a navigation button."""
        btn = QPushButton(f"{icon}  {text}")
        btn.setObjectName("navButton")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setCheckable(True)
        btn.clicked.connect(lambda: self.show_page(page_idx))

        # Set size policy
        btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        btn.setMinimumHeight(50)

        return btn

    def _create_top_bar(self):
        """Create top bar with quick actions."""
        top_bar = QFrame()
        top_bar.setObjectName("topBar")
        top_bar.setFixedHeight(60)

        layout = QHBoxLayout(top_bar)
        layout.setContentsMargins(20, 10, 20, 10)

        # Page title (will be updated)
        self.page_title = QLabel("Dashboard")
        self.page_title.setObjectName("pageTitle")
        layout.addWidget(self.page_title)

        layout.addStretch()

        # Quick stats
        self.quick_stats = QLabel("⏱ 00:00:00 | ✅ 0 | ❌ 0")
        self.quick_stats.setObjectName("quickStats")
        layout.addWidget(self.quick_stats)

        return top_bar

    def _setup_navigation(self):
        """Setup navigation system."""
        # Select first button by default
        if self.nav_buttons:
            self.nav_buttons[0].setChecked(True)

    def show_page(self, index):
        """Show a specific page."""
        # Update page
        self.pages.setCurrentIndex(index)

        # Update navigation buttons
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)

        # Update page title
        page_titles = ["Dashboard", "Activities", "Templates", "Logs", "Statistics", "Settings"]
        if 0 <= index < len(page_titles):
            self.page_title.setText(page_titles[index])

        # Refresh page data
        current_page = self.pages.currentWidget()
        if hasattr(current_page, 'refresh'):
            current_page.refresh()

    def _setup_status_updates(self):
        """Setup periodic status updates."""
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._update_status)
        self.status_timer.start(1000)  # Update every second

    def _update_status(self):
        """Update status displays."""
        if not self.scheduler:
            return

        try:
            status = self.scheduler.get_status()

            # Update quick stats
            uptime = status.get('uptime_formatted', '00:00:00')
            success = status.get('successful_executions', 0)
            failed = status.get('failed_executions', 0)

            self.quick_stats.setText(f"⏱ {uptime} | ✅ {success} | ❌ {failed}")

            # Update status bar
            if status.get('running'):
                self.status_bar.set_status("running", "Running")
            else:
                self.status_bar.set_status("stopped", "Stopped")

            # Update ADB status
            if self.adb and self.adb.is_connected():
                self.status_bar.set_adb_status(True)
            else:
                self.status_bar.set_adb_status(False)

        except Exception as e:
            print(f"Status update error: {e}")

    def closeEvent(self, event):
        """Handle window close."""
        # Stop automation if running
        if self.scheduler and self.scheduler.running:
            self.stop_automation.emit()

        event.accept()
