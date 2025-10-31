"""
Shrine Blessing Activity

Collects shrine blessings (free buffs).
Shrines provide temporary buffs for various activities.
"""

from typing import Optional
import logging
import time
from dataclasses import dataclass

from ...core.activity import Activity, ActivityConfig
from ...core.adb import ADBConnection
from ...core.screen import ScreenAnalyzer


@dataclass
class ShrineBlessingConfig(ActivityConfig):
    """Configuration for shrine blessing"""
    collect_all_blessings: bool = True
    confidence: float = 0.75


class ShrineBlessingActivity(Activity):
    """Collects shrine blessings."""

    def __init__(self, config: ShrineBlessingConfig, adb: ADBConnection, screen: ScreenAnalyzer):
        super().__init__("Shrine Blessing", config)
        self.adb = adb
        self.screen = screen
        self.config: ShrineBlessingConfig = config
        self.blessings_collected = 0

    def check_prerequisites(self) -> bool:
        return True

    def execute(self) -> bool:
        self.logger.info("Collecting shrine blessings...")

        if not self._navigate_to_shrine():
            self.logger.info("Shrine not available")
            return True

        time.sleep(1.0)
        self.blessings_collected = self._collect_blessings()

        self._close_shrine()
        self._navigate_to_city()

        if self.blessings_collected > 0:
            self.logger.info(f"Collected {self.blessings_collected} shrine blessings")
        return True

    def verify_completion(self) -> bool:
        if not self._is_on_city_view():
            self._navigate_to_city()
        return True

    def _collect_blessings(self) -> int:
        collected = 0
        screenshot = self.adb.capture_screen_cached()
        collect_button = self.screen.find_template(
            screenshot,
            'templates/buttons/collect_blessing.png',
            confidence=self.config.confidence
        )
        if collect_button:
            self.adb.tap(collect_button[0], collect_button[1], randomize=True)
            time.sleep(0.5)
            collected = 1
        return collected

    def _navigate_to_shrine(self) -> bool:
        if not self._is_on_city_view():
            if not self._navigate_to_city():
                return False
        screenshot = self.adb.capture_screen_cached()
        shrine = self.screen.find_template(
            screenshot,
            'templates/buildings/shrine.png',
            confidence=self.config.confidence
        )
        if not shrine:
            return False
        self.adb.tap(shrine[0], shrine[1], randomize=True)
        time.sleep(1.5)
        return True

    def _close_shrine(self):
        screenshot = self.adb.capture_screen_cached()
        close_button = self.screen.find_template(
            screenshot,
            'templates/buttons/close.png',
            confidence=0.75
        )
        if close_button:
            self.adb.tap(close_button[0], close_button[1], randomize=True)
        time.sleep(0.5)

    def _is_on_city_view(self) -> bool:
        screenshot = self.adb.capture_screen_cached()
        return self.screen.find_template(
            screenshot,
            'templates/screens/city_view.png',
            confidence=0.7
        ) is not None

    def _navigate_to_city(self) -> bool:
        for _ in range(3):
            if self._is_on_city_view():
                return True
            screenshot = self.adb.capture_screen_cached()
            back_button = self.screen.find_template(
                screenshot,
                'templates/buttons/back.png',
                confidence=0.75
            )
            if back_button:
                self.adb.tap(back_button[0], back_button[1], randomize=True)
            time.sleep(1.0)
        return False
