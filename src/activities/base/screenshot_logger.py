"""
Screenshot Logger Activity

Takes periodic screenshots for debugging and record-keeping.
Automatically cleans old screenshots to manage disk space.
"""

from typing import Optional
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime, timedelta

from ...core.activity import Activity, ActivityConfig
from ...core.adb import ADBConnection
from ...core.screen import ScreenAnalyzer


@dataclass
class ScreenshotLoggerConfig(ActivityConfig):
    """Configuration for screenshot logger"""
    screenshot_interval_minutes: int = 30
    save_directory: str = "logs/screenshots"
    max_age_days: int = 7  # Delete screenshots older than this
    max_screenshots: int = 100  # Maximum screenshots to keep
    confidence: float = 0.75


class ScreenshotLoggerActivity(Activity):
    """Takes periodic screenshots for logging."""

    def __init__(self, config: ScreenshotLoggerConfig, adb: ADBConnection, screen: ScreenAnalyzer):
        super().__init__("Screenshot Logger", config)
        self.adb = adb
        self.screen = screen
        self.config: ScreenshotLoggerConfig = config

        # Create screenshot directory
        self.screenshot_dir = Path(self.config.save_directory)
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)

    def check_prerequisites(self) -> bool:
        return True

    def execute(self) -> bool:
        """Take a screenshot and clean old ones."""
        # Take screenshot
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.png"
        filepath = self.screenshot_dir / filename

        success = self.adb.capture_screen(str(filepath))

        if success:
            self.logger.debug(f"Screenshot saved: {filename}")
        else:
            self.logger.warning("Failed to capture screenshot")

        # Clean old screenshots
        self._clean_old_screenshots()

        return True

    def verify_completion(self) -> bool:
        return True

    def _clean_old_screenshots(self):
        """Remove screenshots older than max_age_days."""
        try:
            screenshots = sorted(self.screenshot_dir.glob("screenshot_*.png"))

            # Remove by age
            cutoff_date = datetime.now() - timedelta(days=self.config.max_age_days)

            for screenshot in screenshots:
                file_time = datetime.fromtimestamp(screenshot.stat().st_mtime)
                if file_time < cutoff_date:
                    screenshot.unlink()
                    self.logger.debug(f"Deleted old screenshot: {screenshot.name}")

            # Remove by count (keep only most recent max_screenshots)
            screenshots = sorted(self.screenshot_dir.glob("screenshot_*.png"),
                               key=lambda p: p.stat().st_mtime, reverse=True)

            if len(screenshots) > self.config.max_screenshots:
                for screenshot in screenshots[self.config.max_screenshots:]:
                    screenshot.unlink()
                    self.logger.debug(f"Deleted excess screenshot: {screenshot.name}")

        except Exception as e:
            self.logger.error(f"Error cleaning screenshots: {e}")
