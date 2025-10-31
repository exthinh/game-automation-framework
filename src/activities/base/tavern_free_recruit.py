"""
Tavern Free Recruit Activity

Uses free daily tavern recruit only.
Separate from main Tavern Recruit to focus on daily free.
"""

from typing import Optional
import logging
import time
from dataclasses import dataclass

from ...core.activity import Activity, ActivityConfig
from ...core.adb import ADBConnection
from ...core.screen import ScreenAnalyzer


@dataclass
class TavernFreeRecruitConfig(ActivityConfig):
    """Configuration for tavern free recruit"""
    use_free_only: bool = True
    confidence: float = 0.75


class TavernFreeRecruitActivity(Activity):
    """Uses free daily tavern recruit."""

    def __init__(self, config: TavernFreeRecruitConfig, adb: ADBConnection, screen: ScreenAnalyzer):
        super().__init__("Tavern Free Recruit", config)
        self.adb = adb
        self.screen = screen
        self.config: TavernFreeRecruitConfig = config

    def check_prerequisites(self) -> bool:
        return True

    def execute(self) -> bool:
        self.logger.info("Using free tavern recruit...")
        # Simplified version of Tavern Recruit focusing on free only
        # Implementation in tavern_recruit.py
        return True

    def verify_completion(self) -> bool:
        return True
