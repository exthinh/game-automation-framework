"""
March Monitor Activity

Tracks active marches and prevents exceeding march limit.
Monitors march status and return times.

CRITICAL for preventing activity errors (trying to send march when all slots full).
"""

from typing import List, Dict, Optional
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta

from ...core.activity import Activity, ActivityConfig
from ...core.adb import ADBConnection
from ...core.screen import ScreenAnalyzer


@dataclass
class MarchMonitorConfig(ActivityConfig):
    """Configuration for march monitoring"""

    # March limits (configure based on VIP level and buildings)
    max_marches: int = 2               # Total march slots available

    # Monitoring
    track_march_types: bool = True      # Track what each march is doing
    track_return_times: bool = True     # Track when marches return

    # Actions
    prevent_new_marches: bool = True    # Prevent activities from creating new marches when full
    recall_gathering: bool = False      # Auto-recall gathering marches if needed

    # Detection settings
    confidence: float = 0.75


class MarchMonitorActivity(Activity):
    """
    Monitors active marches.

    Process:
    1. Count active marches
    2. Read march types (gathering, attacking, etc.)
    3. Read return times
    4. Update march status
    5. Prevent march-creating activities if at limit

    Success Criteria:
    - Successfully read march count
    - Updated march tracking
    """

    def __init__(self, config: MarchMonitorConfig, adb: ADBConnection, screen: ScreenAnalyzer):
        super().__init__("March Monitor", config)
        self.adb = adb
        self.screen = screen
        self.config: MarchMonitorConfig = config

        self.active_marches = 0
        self.march_info: List[Dict] = []

    def check_prerequisites(self) -> bool:
        """March monitor always runs."""
        return True

    def execute(self) -> bool:
        """
        Execute march monitoring.

        Process:
        1. Read march count
        2. Read march details if enabled
        3. Update status
        """
        self.logger.debug("Checking active marches...")

        # Read march count
        self.active_marches = self._count_active_marches()

        self.logger.debug(f"Active marches: {self.active_marches}/{self.config.max_marches}")

        # Read march details if enabled
        if self.config.track_march_types or self.config.track_return_times:
            self.march_info = self._read_march_details()

        # Check if at limit
        if self.active_marches >= self.config.max_marches:
            self.logger.warning(f"March slots full ({self.active_marches}/{self.config.max_marches})")

            if self.config.recall_gathering:
                self._recall_gathering_marches()

        return True

    def verify_completion(self) -> bool:
        """Verify march monitoring completed."""
        return True

    def _count_active_marches(self) -> int:
        """
        Count active marches.

        Marches are usually displayed in the bottom-left corner of the screen.

        Returns:
            Number of active marches
        """
        screenshot = self.adb.capture_screen_cached()

        # Look for march indicators in bottom-left area
        # Usually there are icons for each active march

        try:
            # Method 1: Count march icons
            march_icons = self.screen.find_all_templates(
                screenshot,
                'templates/icons/march_active.png',
                confidence=self.config.confidence
            )

            if march_icons:
                return len(march_icons)

            # Method 2: Read march counter text (e.g., "2/3")
            march_counter_region = screenshot[950:1000, 50:200]
            text = self.screen.read_text(march_counter_region)

            # Parse "2/3" format
            if '/' in text:
                current = text.split('/')[0].strip()
                return int(current)

        except Exception as e:
            self.logger.debug(f"Could not count marches: {e}")

        return 0

    def _read_march_details(self) -> List[Dict]:
        """
        Read details about each active march.

        Returns:
            List of march info dicts
        """
        marches = []

        # This requires clicking on march queue/list
        # For now, return empty list
        # TODO: Implement detailed march reading

        return marches

    def _recall_gathering_marches(self):
        """Recall gathering marches to free up slots."""
        self.logger.info("Recalling gathering marches...")

        # This requires:
        # 1. Opening march list
        # 2. Identifying gathering marches
        # 3. Recalling them

        # TODO: Implement gathering march recall
        self.logger.warning("Auto-recall not yet implemented")

    def get_active_march_count(self) -> int:
        """Get number of active marches."""
        return self.active_marches

    def is_march_limit_reached(self) -> bool:
        """Check if march limit is reached."""
        return self.active_marches >= self.config.max_marches

    def get_available_march_slots(self) -> int:
        """Get number of available march slots."""
        return max(0, self.config.max_marches - self.active_marches)
