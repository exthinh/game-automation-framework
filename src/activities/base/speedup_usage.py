"""
Speedup Usage Activity

Uses speedup items on buildings, research, and training based on configured rules.
Helps optimize speedup usage to avoid waste.

Example rules:
- Use 1min speedups if < 5min remaining
- Use 5min speedups if < 1hr remaining
- Never use 24hr+ speedups (save for important upgrades)
"""

from typing import Optional, Dict
import logging
import time
from dataclasses import dataclass

from ...core.activity import Activity, ActivityConfig
from ...core.adb import ADBConnection
from ...core.screen import ScreenAnalyzer


@dataclass
class SpeedupUsageConfig(ActivityConfig):
    """Configuration for speedup usage"""

    # Speedup rules (time in minutes)
    use_1min_if_under: int = 5         # Use 1min speedups if < 5min remaining
    use_5min_if_under: int = 60        # Use 5min speedups if < 1hr remaining
    use_1hr_if_under: int = 480        # Use 1hr speedups if < 8hr remaining
    use_3hr_if_under: int = 1440       # Use 3hr speedups if < 24hr remaining

    # What to speedup
    speedup_buildings: bool = False    # Speedup building upgrades
    speedup_research: bool = False     # Speedup research
    speedup_training: bool = False     # Speedup troop training
    speedup_healing: bool = False      # Speedup healing

    # Limits
    max_speedups_per_run: int = 10     # Max speedups to use per activity run

    # Detection settings
    confidence: float = 0.75


class SpeedupUsageActivity(Activity):
    """
    Uses speedup items based on configured rules.

    Process:
    1. Check what's being upgraded/researched/trained
    2. Read remaining time
    3. Apply appropriate speedup based on rules
    4. Verify speedup was applied

    Success Criteria:
    - Used speedups successfully
    - OR no eligible timers to speedup
    """

    def __init__(self, config: SpeedupUsageConfig, adb: ADBConnection, screen: ScreenAnalyzer):
        super().__init__("Speedup Usage", config)
        self.adb = adb
        self.screen = screen
        self.config: SpeedupUsageConfig = config

        self.speedups_used = 0

    def check_prerequisites(self) -> bool:
        """
        Check if we can use speedups.

        Prerequisites:
        - At least one speedup type enabled
        """
        if not (self.config.speedup_buildings or
                self.config.speedup_research or
                self.config.speedup_training or
                self.config.speedup_healing):
            self.logger.warning("No speedup types enabled")
            return False

        return True

    def execute(self) -> bool:
        """
        Execute speedup usage.

        Process:
        1. Check each speedup type
        2. Apply speedups where appropriate
        3. Return status
        """
        self.logger.info("Using speedups...")

        self.speedups_used = 0

        # Speedup buildings
        if self.config.speedup_buildings:
            self.speedups_used += self._speedup_buildings()

        # Speedup research
        if self.config.speedup_research:
            self.speedups_used += self._speedup_research()

        # Speedup training
        if self.config.speedup_training:
            self.speedups_used += self._speedup_training()

        # Speedup healing
        if self.config.speedup_healing:
            self.speedups_used += self._speedup_healing()

        if self.speedups_used > 0:
            self.logger.info(f"Used {self.speedups_used} speedups")
            return True
        else:
            self.logger.info("No speedups used (no eligible timers)")
            return True

    def verify_completion(self) -> bool:
        """Verify speedup usage completed."""
        return True

    def _speedup_buildings(self) -> int:
        """Speedup building upgrades."""
        # TODO: Implement building speedup
        # Requires:
        # 1. Detect if building is upgrading
        # 2. Read remaining time
        # 3. Apply appropriate speedup
        return 0

    def _speedup_research(self) -> int:
        """Speedup research."""
        # TODO: Implement research speedup
        return 0

    def _speedup_training(self) -> int:
        """Speedup troop training."""
        # TODO: Implement training speedup
        return 0

    def _speedup_healing(self) -> int:
        """Speedup troop healing."""
        # TODO: Implement healing speedup
        return 0

    def _determine_speedup_type(self, remaining_minutes: int) -> Optional[str]:
        """
        Determine which speedup type to use based on remaining time.

        Args:
            remaining_minutes: Time remaining in minutes

        Returns:
            Speedup type ("1min", "5min", "1hr", "3hr") or None
        """
        if remaining_minutes <= self.config.use_1min_if_under:
            return "1min"
        elif remaining_minutes <= self.config.use_5min_if_under:
            return "5min"
        elif remaining_minutes <= self.config.use_1hr_if_under:
            return "1hr"
        elif remaining_minutes <= self.config.use_3hr_if_under:
            return "3hr"

        return None  # Don't use speedup (time too long)

    def get_speedups_used(self) -> int:
        """Get number of speedups used."""
        return self.speedups_used
