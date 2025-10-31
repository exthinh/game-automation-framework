"""
Rally Participation Activity

Automatically joins alliance rallies based on configured rules.
Monitors rally notifications and sends troops.
"""

from typing import Optional
import logging
import time
from dataclasses import dataclass

from ...core.activity import Activity, ActivityConfig
from ...core.adb import ADBConnection
from ...core.screen import ScreenAnalyzer


@dataclass
class RallyParticipationConfig(ActivityConfig):
    """Configuration for rally participation"""
    auto_join_rallies: bool = False  # Disabled by default (risky)
    join_leader_rallies_only: bool = True
    allowed_leaders: list = None  # List of leader names to join
    min_rally_capacity: int = 1000000  # Min rally capacity to join
    confidence: float = 0.75


class RallyParticipationActivity(Activity):
    """Joins alliance rallies."""

    def __init__(self, config: RallyParticipationConfig, adb: ADBConnection, screen: ScreenAnalyzer):
        super().__init__("Rally Participation", config)
        self.adb = adb
        self.screen = screen
        self.config: RallyParticipationConfig = config

        if self.config.allowed_leaders is None:
            self.config.allowed_leaders = []

        self.rallies_joined = 0

    def check_prerequisites(self) -> bool:
        if not self.config.auto_join_rallies:
            return False
        return True

    def execute(self) -> bool:
        self.logger.info("Checking for rallies...")

        # Check for rally notification
        screenshot = self.adb.capture_screen_cached()
        rally_notification = self.screen.find_template(
            screenshot,
            'templates/notifications/rally.png',
            confidence=self.config.confidence
        )

        if not rally_notification:
            return True

        # Join rally
        if self._join_rally():
            self.rallies_joined += 1
            self.logger.info("Joined rally")
            return True

        return True

    def verify_completion(self) -> bool:
        return True

    def _join_rally(self) -> bool:
        """Join a rally."""
        # Tap rally notification
        screenshot = self.adb.capture_screen_cached()
        rally = self.screen.find_template(
            screenshot,
            'templates/notifications/rally.png',
            confidence=self.config.confidence
        )

        if not rally:
            return False

        self.adb.tap(rally[0], rally[1], randomize=True)
        time.sleep(1.0)

        # Tap join button
        screenshot = self.adb.capture_screen_cached()
        join_button = self.screen.find_template(
            screenshot,
            'templates/buttons/join_rally.png',
            confidence=self.config.confidence
        )

        if not join_button:
            return False

        self.adb.tap(join_button[0], join_button[1], randomize=True)
        time.sleep(1.0)

        # Confirm
        screenshot = self.adb.capture_screen_cached()
        confirm_button = self.screen.find_template(
            screenshot,
            'templates/buttons/confirm.png',
            confidence=0.75
        )

        if confirm_button:
            self.adb.tap(confirm_button[0], confirm_button[1], randomize=True)
            time.sleep(0.5)
            return True

        return False
