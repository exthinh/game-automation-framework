"""
Lucky Wheel / Spin Events Activity

Uses free daily spins on lucky wheel events.
Wheel events offer random rewards for spinning.
"""

from typing import Optional
import logging
import time
from dataclasses import dataclass

from ...core.activity import Activity, ActivityConfig
from ...core.adb import ADBConnection
from ...core.screen import ScreenAnalyzer


@dataclass
class LuckyWheelConfig(ActivityConfig):
    """Configuration for lucky wheel"""
    use_free_spins_only: bool = True
    max_spins_per_run: int = 10
    confidence: float = 0.75


class LuckyWheelActivity(Activity):
    """Uses free spins on lucky wheel events."""

    def __init__(self, config: LuckyWheelConfig, adb: ADBConnection, screen: ScreenAnalyzer):
        super().__init__("Lucky Wheel", config)
        self.adb = adb
        self.screen = screen
        self.config: LuckyWheelConfig = config
        self.spins_used = 0

    def check_prerequisites(self) -> bool:
        return True

    def execute(self) -> bool:
        self.logger.info("Using lucky wheel...")

        if not self._navigate_to_wheel():
            self.logger.info("Lucky wheel event not available")
            return True

        time.sleep(1.0)
        self.spins_used = self._use_spins()

        self._close_wheel()
        self._navigate_to_city()

        if self.spins_used > 0:
            self.logger.info(f"Used {self.spins_used} wheel spins")
        return True

    def verify_completion(self) -> bool:
        if not self._is_on_city_view():
            self._navigate_to_city()
        return True

    def _use_spins(self) -> int:
        spins = 0
        for i in range(self.config.max_spins_per_run):
            screenshot = self.adb.capture_screen_cached()
            free_spin_button = self.screen.find_template(
                screenshot,
                'templates/buttons/free_spin.png',
                confidence=self.config.confidence
            )
            if not free_spin_button:
                break
            self.adb.tap(free_spin_button[0], free_spin_button[1], randomize=True)
            time.sleep(3.0)  # Wait for spin animation
            self.adb.tap(960, 540, randomize=True)  # Dismiss result
            time.sleep(0.5)
            spins += 1
        return spins

    def _navigate_to_wheel(self) -> bool:
        if not self._is_on_city_view():
            if not self._navigate_to_city():
                return False
        screenshot = self.adb.capture_screen_cached()
        wheel_button = self.screen.find_template(
            screenshot,
            'templates/buttons/lucky_wheel.png',
            confidence=self.config.confidence
        )
        if not wheel_button:
            return False
        self.adb.tap(wheel_button[0], wheel_button[1], randomize=True)
        time.sleep(1.5)
        return True

    def _close_wheel(self):
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
