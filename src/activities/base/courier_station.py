"""
Courier Station Activity

Opens courier station chests for rewards.
Courier stations provide resources, speedups, and other items periodically.
"""

from typing import Optional
import logging
import time
from dataclasses import dataclass

from ...core.activity import Activity, ActivityConfig
from ...core.adb import ADBConnection
from ...core.screen import ScreenAnalyzer


@dataclass
class CourierStationConfig(ActivityConfig):
    """Configuration for courier station"""

    # Collection settings
    collect_all_chests: bool = True
    max_chests_per_run: int = 10

    # Detection settings
    confidence: float = 0.75


class CourierStationActivity(Activity):
    """
    Collects courier station chests.

    Process:
    1. Navigate to courier station
    2. Open available chests
    3. Collect rewards
    4. Close and return
    """

    def __init__(self, config: CourierStationConfig, adb: ADBConnection, screen: ScreenAnalyzer):
        super().__init__("Courier Station", config)
        self.adb = adb
        self.screen = screen
        self.config: CourierStationConfig = config

        self.chests_opened = 0

    def check_prerequisites(self) -> bool:
        return True

    def execute(self) -> bool:
        self.logger.info("Opening courier station chests...")

        if not self._navigate_to_courier_station():
            self.logger.error("Failed to navigate to courier station")
            return False

        time.sleep(1.0)

        self.chests_opened = self._open_chests()

        self._close_courier_station()
        self._navigate_to_city()

        if self.chests_opened > 0:
            self.logger.info(f"Opened {self.chests_opened} courier station chests")
            return True
        else:
            self.logger.info("No courier station chests available")
            return True

    def verify_completion(self) -> bool:
        if not self._is_on_city_view():
            self._navigate_to_city()
        return True

    def _open_chests(self) -> int:
        opened = 0

        for i in range(self.config.max_chests_per_run):
            screenshot = self.adb.capture_screen_cached()

            chest = self.screen.find_template(
                screenshot,
                'templates/buttons/courier_chest.png',
                confidence=self.config.confidence
            )

            if not chest:
                break

            self.adb.tap(chest[0], chest[1], randomize=True)
            time.sleep(1.0)

            self._collect_rewards()
            opened += 1

            time.sleep(0.5)

        return opened

    def _collect_rewards(self):
        time.sleep(0.5)
        self.adb.tap(960, 540, randomize=True)
        time.sleep(0.5)

    def _navigate_to_courier_station(self) -> bool:
        if not self._is_on_city_view():
            if not self._navigate_to_city():
                return False

        screenshot = self.adb.capture_screen_cached()
        courier_button = self.screen.find_template(
            screenshot,
            'templates/buttons/courier_station.png',
            confidence=self.config.confidence
        )

        if not courier_button:
            return False

        self.adb.tap(courier_button[0], courier_button[1], randomize=True)
        time.sleep(1.5)
        return True

    def _close_courier_station(self):
        screenshot = self.adb.capture_screen_cached()
        close_button = self.screen.find_template(
            screenshot,
            'templates/buttons/close.png',
            confidence=0.75
        )

        if close_button:
            self.adb.tap(close_button[0], close_button[1], randomize=True)
        else:
            self._press_back()

        time.sleep(0.5)

    def _press_back(self):
        screenshot = self.adb.capture_screen_cached()
        back_button = self.screen.find_template(
            screenshot,
            'templates/buttons/back.png',
            confidence=0.75
        )
        if back_button:
            self.adb.tap(back_button[0], back_button[1], randomize=True)
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
            self._press_back()
            time.sleep(1.0)
        return False
