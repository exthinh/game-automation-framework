"""
Commander Leveling Activity (via Barbarians)

Rotates commanders through barbarian hunting for XP.
Automatically switches commanders once they reach target level/XP.
"""

from typing import List, Optional
import logging
import time
from dataclasses import dataclass

from ...core.activity import Activity, ActivityConfig
from ...core.adb import ADBConnection
from ...core.screen import ScreenAnalyzer


@dataclass
class CommanderLevelingConfig(ActivityConfig):
    """Configuration for commander leveling"""
    commander_rotation: List[str] = None
    xp_per_commander: int = 100000
    confidence: float = 0.75


class CommanderLevelingActivity(Activity):
    """Rotates commanders for XP farming."""

    def __init__(self, config: CommanderLevelingConfig, adb: ADBConnection, screen: ScreenAnalyzer):
        super().__init__("Commander Leveling", config)
        self.adb = adb
        self.screen = screen
        self.config: CommanderLevelingConfig = config

        if self.config.commander_rotation is None:
            self.config.commander_rotation = []

        self.current_commander_index = 0

    def check_prerequisites(self) -> bool:
        if not self.config.commander_rotation:
            return False
        return True

    def execute(self) -> bool:
        self.logger.info("Managing commander rotation...")
        # This is integrated with Barbarian Hunt activity
        # Tracks XP and rotates commanders
        self.logger.warning("Commander leveling integrated with Barbarian Hunt")
        return True

    def verify_completion(self) -> bool:
        return True
