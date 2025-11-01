"""
Game Automation Framework - GUI Launcher

Beautiful PyQt6 interface for the game automation bot.

USAGE:
    python main_gui.py
"""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

from src.gui.main_window import MainWindow
from src.core.adb import ADBConnection, find_bluestacks_device
from src.core.screen import ScreenAnalyzer
from src.core.scheduler import ActivityScheduler


def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] %(levelname)-8s %(name)-15s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    logging.getLogger('PIL').setLevel(logging.WARNING)


def main():
    """Main entry point for GUI."""
    setup_logging()
    logger = logging.getLogger("GUI")

    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("Game Automation Framework")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("GameBot")

    # Set high DPI scaling
    app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)

    logger.info("Starting GUI...")

    try:
        # Initialize ADB
        logger.info("Initializing ADB connection...")
        adb = ADBConnection()

        # Try to find BlueStacks
        device_id = find_bluestacks_device()
        if device_id:
            logger.info(f"Found BlueStacks: {device_id}")
            adb.device_id = device_id
        else:
            logger.warning("BlueStacks not found - will attempt connection on demand")

        # Initialize screen analyzer
        logger.info("Initializing screen analyzer...")
        screen = ScreenAnalyzer(templates_dir="templates")

        # Initialize scheduler
        logger.info("Initializing scheduler...")
        scheduler = ActivityScheduler()

        # Create main window
        logger.info("Creating main window...")
        window = MainWindow(scheduler=scheduler, adb=adb, screen=screen)

        # Connect signals
        window.start_automation.connect(lambda: start_automation(scheduler, window))
        window.stop_automation.connect(lambda: stop_automation(scheduler, window))
        window.pause_automation.connect(lambda: pause_automation(scheduler, window))

        # Show window
        window.show()

        logger.info("GUI started successfully!")

        # Run application
        sys.exit(app.exec())

    except Exception as e:
        logger.error(f"Failed to start GUI: {e}", exc_info=True)

        # Show error dialog
        error_dialog = QMessageBox()
        error_dialog.setIcon(QMessageBox.Icon.Critical)
        error_dialog.setWindowTitle("Error")
        error_dialog.setText("Failed to start application")
        error_dialog.setInformativeText(str(e))
        error_dialog.setStandardButtons(QMessageBox.StandardButton.Ok)
        error_dialog.exec()

        sys.exit(1)


def start_automation(scheduler, window):
    """Start automation."""
    logger = logging.getLogger("GUI")
    logger.info("Starting automation...")

    try:
        scheduler.start()
        window.control_panel.set_running(True)
        window.status_bar.set_status("running", "Running")

        logger.info("Automation started")

    except Exception as e:
        logger.error(f"Failed to start automation: {e}")

        error_dialog = QMessageBox()
        error_dialog.setIcon(QMessageBox.Icon.Warning)
        error_dialog.setWindowTitle("Error")
        error_dialog.setText("Failed to start automation")
        error_dialog.setInformativeText(str(e))
        error_dialog.exec()


def stop_automation(scheduler, window):
    """Stop automation."""
    logger = logging.getLogger("GUI")
    logger.info("Stopping automation...")

    try:
        scheduler.stop()
        window.control_panel.set_running(False)
        window.status_bar.set_status("stopped", "Stopped")

        logger.info("Automation stopped")

    except Exception as e:
        logger.error(f"Failed to stop automation: {e}")


def pause_automation(scheduler, window):
    """Pause automation."""
    logger = logging.getLogger("GUI")
    logger.info("Pausing automation...")

    # TODO: Implement pause functionality
    window.status_bar.set_status("paused", "Paused")

    logger.info("Automation paused")


if __name__ == "__main__":
    main()
