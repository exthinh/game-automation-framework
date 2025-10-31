"""
Teleport Safety Check Activity

Prevents bot from running after teleport (different kingdom).
Detects location changes and pauses automation.
"""

from typing import Optional
import logging
import time
from dataclasses import dataclass

from ...core.activity import Activity, ActivityConfig
from ...core.adb import ADBConnection
from ...core.screen import ScreenAnalyzer


@dataclass
class TeleportSafetyConfig(ActivityConfig):
    """Configuration for teleport safety"""
    pause_on_teleport: bool = True
    confidence: float = 0.75


class TeleportSafetyActivity(Activity):
    """Detects teleports and pauses bot."""

    def __init__(self, config: TeleportSafetyConfig, adb: ADBConnection, screen: ScreenAnalyzer):
        super().__init__("Teleport Safety", config)
        self.adb = adb
        self.screen = screen
        self.config: TeleportSafetyConfig = config
        self.last_kingdom = None

    def check_prerequisites(self) -> bool:
        return True

    def execute(self) -> bool:
        """Check if kingdom changed (teleported)."""
        screenshot = self.adb.capture_screen_cached()

        # Look for teleport indicators
        teleport_notification = self.screen.find_template(
            screenshot,
            'templates/notifications/teleported.png',
            confidence=self.config.confidence
        )

        if teleport_notification:
            self.logger.critical("TELEPORT DETECTED! Pausing automation for safety.")
            if self.config.pause_on_teleport:
                return False  # Signal to stop scheduler

        return True

    def verify_completion(self) -> bool:
        return True
