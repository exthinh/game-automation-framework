"""
Modern Dark Theme - Sleek and Professional

A beautiful dark theme with smooth gradients, subtle shadows,
and modern color accents for the Game Automation Framework.
"""

DARK_THEME = """
/* ===================================================================
   GLOBAL STYLES
   =================================================================== */

QMainWindow, QWidget {
    background-color: #1a1a1a;
    color: #e0e0e0;
    font-family: 'Segoe UI', 'San Francisco', 'Helvetica Neue', Arial, sans-serif;
    font-size: 13px;
}

/* ===================================================================
   SIDEBAR
   =================================================================== */

QFrame#sidebar {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #1e1e1e,
        stop:1 #252525
    );
    border-right: 1px solid #333333;
}

QWidget#sidebarTitle {
    background-color: #252525;
    border-bottom: 2px solid #4a9eff;
}

QLabel#appTitle {
    color: #ffffff;
    font-size: 24px;
    font-weight: bold;
    letter-spacing: 1px;
}

QLabel#appSubtitle {
    color: #888888;
    font-size: 11px;
    letter-spacing: 0.5px;
    margin-top: 5px;
}

/* Navigation Buttons */
QPushButton#navButton {
    background-color: transparent;
    color: #b0b0b0;
    border: none;
    border-left: 3px solid transparent;
    padding: 12px 20px;
    text-align: left;
    font-size: 14px;
    font-weight: 500;
}

QPushButton#navButton:hover {
    background-color: rgba(74, 158, 255, 0.1);
    color: #4a9eff;
}

QPushButton#navButton:checked {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 rgba(74, 158, 255, 0.15),
        stop:1 transparent
    );
    color: #4a9eff;
    border-left: 3px solid #4a9eff;
    font-weight: 600;
}

/* ===================================================================
   TOP BAR
   =================================================================== */

QFrame#topBar {
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #252525,
        stop:1 #1e1e1e
    );
    border-bottom: 1px solid #333333;
}

QLabel#pageTitle {
    color: #ffffff;
    font-size: 20px;
    font-weight: 600;
    letter-spacing: 0.5px;
}

QLabel#quickStats {
    color: #b0b0b0;
    font-size: 13px;
    font-family: 'Consolas', 'Monaco', monospace;
    padding: 8px 16px;
    background-color: #252525;
    border-radius: 6px;
}

/* ===================================================================
   CONTENT AREA
   =================================================================== */

QStackedWidget#pageContainer {
    background-color: #1a1a1a;
}

/* Cards */
QFrame.card {
    background-color: #252525;
    border: 1px solid #333333;
    border-radius: 8px;
    padding: 20px;
}

QFrame.card:hover {
    border-color: #444444;
    background-color: #282828;
}

/* Section Headers */
QLabel.sectionHeader {
    color: #ffffff;
    font-size: 16px;
    font-weight: 600;
    padding: 10px 0;
    border-bottom: 2px solid #4a9eff;
    margin-bottom: 15px;
}

/* ===================================================================
   BUTTONS
   =================================================================== */

QPushButton {
    background-color: #2d2d2d;
    color: #e0e0e0;
    border: 1px solid #404040;
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #353535;
    border-color: #4a9eff;
}

QPushButton:pressed {
    background-color: #404040;
}

QPushButton:disabled {
    background-color: #222222;
    color: #555555;
    border-color: #333333;
}

/* Primary Button */
QPushButton.primary {
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #5aa3ff,
        stop:1 #4a9eff
    );
    color: #ffffff;
    border: none;
    font-weight: 600;
}

QPushButton.primary:hover {
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #6ab0ff,
        stop:1 #5aa3ff
    );
}

QPushButton.primary:pressed {
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #4a9eff,
        stop:1 #3a8eef
    );
}

/* Success Button */
QPushButton.success {
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #5ec96e,
        stop:1 #4caf50
    );
    color: #ffffff;
    border: none;
    font-weight: 600;
}

QPushButton.success:hover {
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #6ed97e,
        stop:1 #5ec96e
    );
}

/* Danger Button */
QPushButton.danger {
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #f55246,
        stop:1 #f44336
    );
    color: #ffffff;
    border: none;
    font-weight: 600;
}

QPushButton.danger:hover {
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #ff6256,
        stop:1 #f55246
    );
}

/* Warning Button */
QPushButton.warning {
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #ffa910,
        stop:1 #ff9800
    );
    color: #ffffff;
    border: none;
    font-weight: 600;
}

/* Icon Buttons */
QPushButton.iconButton {
    background-color: transparent;
    border: none;
    padding: 8px;
    border-radius: 4px;
}

QPushButton.iconButton:hover {
    background-color: rgba(74, 158, 255, 0.1);
}

/* ===================================================================
   INPUT FIELDS
   =================================================================== */

QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox {
    background-color: #2d2d2d;
    color: #e0e0e0;
    border: 1px solid #404040;
    border-radius: 6px;
    padding: 8px 12px;
    selection-background-color: #4a9eff;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border-color: #4a9eff;
    background-color: #323232;
}

QLineEdit:disabled, QTextEdit:disabled {
    background-color: #222222;
    color: #555555;
}

/* ===================================================================
   COMBO BOX
   =================================================================== */

QComboBox {
    background-color: #2d2d2d;
    color: #e0e0e0;
    border: 1px solid #404040;
    border-radius: 6px;
    padding: 8px 12px;
    padding-right: 30px;
}

QComboBox:hover {
    border-color: #4a9eff;
}

QComboBox:focus {
    border-color: #4a9eff;
    background-color: #323232;
}

QComboBox::drop-down {
    border: none;
    width: 30px;
}

QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 6px solid #b0b0b0;
    margin-right: 10px;
}

QComboBox QAbstractItemView {
    background-color: #2d2d2d;
    color: #e0e0e0;
    border: 1px solid #4a9eff;
    selection-background-color: #4a9eff;
    selection-color: #ffffff;
    outline: none;
}

/* ===================================================================
   CHECKBOXES & RADIO BUTTONS
   =================================================================== */

QCheckBox, QRadioButton {
    color: #e0e0e0;
    spacing: 8px;
}

QCheckBox::indicator, QRadioButton::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid #404040;
    background-color: #2d2d2d;
    border-radius: 4px;
}

QRadioButton::indicator {
    border-radius: 9px;
}

QCheckBox::indicator:hover, QRadioButton::indicator:hover {
    border-color: #4a9eff;
}

QCheckBox::indicator:checked, QRadioButton::indicator:checked {
    background-color: #4a9eff;
    border-color: #4a9eff;
}

QCheckBox::indicator:checked {
    image: none;
    background: qradialgradient(
        cx:0.5, cy:0.5, radius:0.5,
        stop:0 #ffffff,
        stop:0.3 #ffffff,
        stop:0.4 #4a9eff,
        stop:1 #4a9eff
    );
}

/* ===================================================================
   SLIDERS
   =================================================================== */

QSlider::groove:horizontal {
    height: 6px;
    background: #2d2d2d;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: #4a9eff;
    width: 18px;
    height: 18px;
    margin: -6px 0;
    border-radius: 9px;
}

QSlider::handle:horizontal:hover {
    background: #5aa3ff;
}

QSlider::sub-page:horizontal {
    background: #4a9eff;
    border-radius: 3px;
}

/* ===================================================================
   PROGRESS BAR
   =================================================================== */

QProgressBar {
    background-color: #2d2d2d;
    border: 1px solid #404040;
    border-radius: 6px;
    height: 24px;
    text-align: center;
    color: #e0e0e0;
    font-weight: 600;
}

QProgressBar::chunk {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #4a9eff,
        stop:1 #5aa3ff
    );
    border-radius: 5px;
}

QProgressBar.success::chunk {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #4caf50,
        stop:1 #5ec96e
    );
}

QProgressBar.danger::chunk {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #f44336,
        stop:1 #f55246
    );
}

/* ===================================================================
   SCROLLBARS
   =================================================================== */

QScrollBar:vertical {
    background-color: #1e1e1e;
    width: 12px;
    border-radius: 6px;
}

QScrollBar::handle:vertical {
    background-color: #404040;
    border-radius: 6px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #4a9eff;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background-color: #1e1e1e;
    height: 12px;
    border-radius: 6px;
}

QScrollBar::handle:horizontal {
    background-color: #404040;
    border-radius: 6px;
    min-width: 30px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #4a9eff;
}

/* ===================================================================
   TABLES
   =================================================================== */

QTableWidget, QTableView {
    background-color: #1e1e1e;
    alternate-background-color: #242424;
    gridline-color: #333333;
    border: 1px solid #333333;
    border-radius: 8px;
}

QHeaderView::section {
    background-color: #252525;
    color: #b0b0b0;
    border: none;
    border-bottom: 2px solid #4a9eff;
    padding: 8px;
    font-weight: 600;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

QTableWidget::item {
    padding: 8px;
    color: #e0e0e0;
}

QTableWidget::item:selected {
    background-color: rgba(74, 158, 255, 0.3);
    color: #ffffff;
}

QTableWidget::item:hover {
    background-color: rgba(74, 158, 255, 0.1);
}

/* ===================================================================
   LIST WIDGETS
   =================================================================== */

QListWidget {
    background-color: #1e1e1e;
    border: 1px solid #333333;
    border-radius: 8px;
    outline: none;
}

QListWidget::item {
    padding: 10px;
    border-bottom: 1px solid #2a2a2a;
    color: #e0e0e0;
}

QListWidget::item:hover {
    background-color: rgba(74, 158, 255, 0.1);
}

QListWidget::item:selected {
    background-color: rgba(74, 158, 255, 0.25);
    color: #ffffff;
}

/* ===================================================================
   TAB WIDGET
   =================================================================== */

QTabWidget::pane {
    background-color: #1e1e1e;
    border: 1px solid #333333;
    border-radius: 8px;
    top: -1px;
}

QTabBar::tab {
    background-color: #2d2d2d;
    color: #b0b0b0;
    padding: 10px 20px;
    margin-right: 2px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-weight: 500;
}

QTabBar::tab:hover {
    background-color: #353535;
    color: #e0e0e0;
}

QTabBar::tab:selected {
    background-color: #4a9eff;
    color: #ffffff;
    font-weight: 600;
}

/* ===================================================================
   TOOLTIPS
   =================================================================== */

QToolTip {
    background-color: #2d2d2d;
    color: #e0e0e0;
    border: 1px solid #4a9eff;
    padding: 8px;
    border-radius: 6px;
    font-size: 12px;
}

/* ===================================================================
   STATUS BAR
   =================================================================== */

QStatusBar {
    background-color: #252525;
    color: #b0b0b0;
    border-top: 1px solid #333333;
}

/* ===================================================================
   MENU BAR
   =================================================================== */

QMenuBar {
    background-color: #252525;
    color: #e0e0e0;
    border-bottom: 1px solid #333333;
}

QMenuBar::item:selected {
    background-color: #4a9eff;
    color: #ffffff;
}

QMenu {
    background-color: #2d2d2d;
    color: #e0e0e0;
    border: 1px solid #404040;
}

QMenu::item:selected {
    background-color: #4a9eff;
    color: #ffffff;
}

/* ===================================================================
   LABELS WITH STATES
   =================================================================== */

QLabel.success {
    color: #4caf50;
    font-weight: 600;
}

QLabel.danger {
    color: #f44336;
    font-weight: 600;
}

QLabel.warning {
    color: #ff9800;
    font-weight: 600;
}

QLabel.info {
    color: #4a9eff;
    font-weight: 600;
}

/* ===================================================================
   SPECIAL WIDGETS
   =================================================================== */

/* Status Badge */
QLabel.statusBadge {
    background-color: #2d2d2d;
    color: #e0e0e0;
    border-radius: 12px;
    padding: 4px 12px;
    font-size: 11px;
    font-weight: 600;
}

QLabel.statusBadge[state="running"] {
    background-color: #4caf50;
    color: #ffffff;
}

QLabel.statusBadge[state="stopped"] {
    background-color: #f44336;
    color: #ffffff;
}

QLabel.statusBadge[state="paused"] {
    background-color: #ff9800;
    color: #ffffff;
}

/* Stat Card */
QFrame.statCard {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0 #2d2d2d,
        stop:1 #252525
    );
    border: 1px solid #404040;
    border-radius: 12px;
    padding: 20px;
}

QFrame.statCard:hover {
    border-color: #4a9eff;
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0 #323232,
        stop:1 #2a2a2a
    );
}
"""
