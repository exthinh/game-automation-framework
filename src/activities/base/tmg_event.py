"""
The Mightiest Governor (TMG) Event Activity

Completes TMG daily tasks and claims rewards.
TMG is a recurring event with daily objectives for points and rewards.
"""

from typing import Optional
import logging
import time
from dataclasses import dataclass

from ...core.activity import Activity, ActivityConfig
from ...core.adb import ADBConnection
from ...core.screen import ScreenAnalyzer


@dataclass
class TMGEventConfig(ActivityConfig):
    """Configuration for TMG event"""
    collect_task_rewards: bool = True
    collect_milestone_rewards: bool = True
    max_collections_per_run: int = 20
    confidence: float = 0.75


class TMGEventActivity(Activity):
    """Collects TMG event rewards."""

    def __init__(self, config: TMGEventConfig, adb: ADBConnection, screen: ScreenAnalyzer):
        super().__init__("TMG Event", config)
        self.adb = adb
        self.screen = screen
        self.config: TMGEventConfig = config
        self.rewards_collected = 0

    def check_prerequisites(self) -> bool:
        return True

    def execute(self) -> bool:
        self.logger.info("Collecting TMG event rewards...")

        if not self._navigate_to_tmg():
            self.logger.warning("TMG event not available or not found")
            return True

        time.sleep(1.0)

        if self.config.collect_task_rewards:
            self.rewards_collected += self._collect_task_rewards()

        if self.config.collect_milestone_rewards:
            self.rewards_collected += self._collect_milestone_rewards()

        self._close_tmg()
        self._navigate_to_city()

        if self.rewards_collected > 0:
            self.logger.info(f"Collected {self.rewards_collected} TMG rewards")
        return True

    def verify_completion(self) -> bool:
        if not self._is_on_city_view():
            self._navigate_to_city()
        return True

    def _collect_task_rewards(self) -> int:
        collected = 0
        for i in range(self.config.max_collections_per_run):
            screenshot = self.adb.capture_screen_cached()
            collect_button = self.screen.find_template(
                screenshot,
                'templates/buttons/collect_tmg.png',
                confidence=self.config.confidence
            )
            if not collect_button:
                break
            self.adb.tap(collect_button[0], collect_button[1], randomize=True)
            time.sleep(0.5)
            collected += 1
        return collected

    def _collect_milestone_rewards(self) -> int:
        collected = 0
        screenshot = self.adb.capture_screen_cached()
        milestone_button = self.screen.find_template(
            screenshot,
            'templates/buttons/tmg_milestone.png',
            confidence=self.config.confidence
        )
        if milestone_button:
            self.adb.tap(milestone_button[0], milestone_button[1], randomize=True)
            time.sleep(0.5)
            collected = 1
        return collected

    def _navigate_to_tmg(self) -> bool:
        if not self._is_on_city_view():
            if not self._navigate_to_city():
                return False
        screenshot = self.adb.capture_screen_cached()
        tmg_button = self.screen.find_template(
            screenshot,
            'templates/buttons/tmg.png',
            confidence=self.config.confidence
        )
        if not tmg_button:
            return False
        self.adb.tap(tmg_button[0], tmg_button[1], randomize=True)
        time.sleep(1.5)
        return True

    def _close_tmg(self):
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
