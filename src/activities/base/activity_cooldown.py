"""
Activity Cooldown Manager

Adds randomized delays between activities to appear human-like.
Helps avoid detection by varying timing patterns.
"""

from typing import Optional
import logging
import time
import random
from dataclasses import dataclass

from ...core.activity import Activity, ActivityConfig
from ...core.adb import ADBConnection
from ...core.screen import ScreenAnalyzer


@dataclass
class ActivityCooldownConfig(ActivityConfig):
    """Configuration for activity cooldown"""
    min_delay_seconds: int = 30
    max_delay_seconds: int = 300
    random_breaks: bool = True
    break_probability: float = 0.1  # 10% chance of extended break
    break_duration_minutes: int = 5
    confidence: float = 0.75


class ActivityCooldownActivity(Activity):
    """Adds human-like delays between activities."""

    def __init__(self, config: ActivityCooldownConfig, adb: ADBConnection, screen: ScreenAnalyzer):
        super().__init__("Activity Cooldown", config)
        self.adb = adb
        self.screen = screen
        self.config: ActivityCooldownConfig = config

    def check_prerequisites(self) -> bool:
        return True

    def execute(self) -> bool:
        """Add randomized delay."""
        # Random delay
        delay = random.randint(self.config.min_delay_seconds, self.config.max_delay_seconds)

        self.logger.debug(f"Cooldown: waiting {delay} seconds")
        time.sleep(delay)

        # Random extended break
        if self.config.random_breaks and random.random() < self.config.break_probability:
            break_duration = self.config.break_duration_minutes * 60
            self.logger.info(f"Taking extended break: {self.config.break_duration_minutes} minutes")
            time.sleep(break_duration)

        return True

    def verify_completion(self) -> bool:
        return True
