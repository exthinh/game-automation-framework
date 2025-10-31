"""
KVK Chest Collection Activity

Collects KVK (Kingdom vs Kingdom) honor chests.
Active during KVK events.
"""

from typing import Optional
import logging
import time
from dataclasses import dataclass

from ...core.activity import Activity, ActivityConfig
from ...core.adb import ADBConnection
from ...core.screen import ScreenAnalyzer


@dataclass
class KVKChestCollectionConfig(ActivityConfig):
    """Configuration for KVK chest collection"""
    collect_all_chests: bool = True
    max_chests_per_run: int = 10
    confidence: float = 0.75


class KVKChestCollectionActivity(Activity):
    """Collects KVK honor chests."""

    def __init__(self, config: KVKChestCollectionConfig, adb: ADBConnection, screen: ScreenAnalyzer):
        super().__init__("KVK Chest Collection", config)
        self.adb = adb
        self.screen = screen
        self.config: KVKChestCollectionConfig = config
        self.chests_collected = 0

    def check_prerequisites(self) -> bool:
        return True

    def execute(self) -> bool:
        self.logger.info("Collecting KVK chests...")

        if not self._navigate_to_kvk():
            self.logger.info("KVK not active or not available")
            return True

        time.sleep(1.0)
        self.chests_collected = self._collect_chests()

        self._close_kvk()
        self._navigate_to_city()

        if self.chests_collected > 0:
            self.logger.info(f"Collected {self.chests_collected} KVK chests")
        return True

    def verify_completion(self) -> bool:
        if not self._is_on_city_view():
            self._navigate_to_city()
        return True

    def _collect_chests(self) -> int:
        collected = 0
        for i in range(self.config.max_chests_per_run):
            screenshot = self.adb.capture_screen_cached()
            chest = self.screen.find_template(
                screenshot,
                'templates/buttons/kvk_chest.png',
                confidence=self.config.confidence
            )
            if not chest:
                break
            self.adb.tap(chest[0], chest[1], randomize=True)
            time.sleep(0.5)
            collected += 1
        return collected

    def _navigate_to_kvk(self) -> bool:
        if not self._is_on_city_view():
            if not self._navigate_to_city():
                return False
        screenshot = self.adb.capture_screen_cached()
        kvk_button = self.screen.find_template(
            screenshot,
            'templates/buttons/kvk.png',
            confidence=self.config.confidence
        )
        if not kvk_button:
            return False
        self.adb.tap(kvk_button[0], kvk_button[1], randomize=True)
        time.sleep(1.5)
        return True

    def _close_kvk(self):
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
