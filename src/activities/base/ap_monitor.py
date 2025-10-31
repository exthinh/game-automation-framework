"""
AP (Action Points) Monitor Activity

Monitors action points and prevents cap waste.
Triggers AP-consuming activities (barbarians, etc.) when AP is near cap.

Based on reverse engineering - AP management is important for efficiency.
"""

from typing import Optional
import logging
import time
from dataclasses import dataclass

from ...core.activity import Activity, ActivityConfig
from ...core.adb import ADBConnection
from ...core.screen import ScreenAnalyzer


@dataclass
class APMonitorConfig(ActivityConfig):
    """Configuration for AP monitoring"""

    # AP thresholds
    ap_cap_threshold: int = 90         # Alert when AP >= this percentage of cap
    ap_cap_value: int = 1000           # Total AP cap (configure based on VIP level)

    # Actions
    alert_on_high_ap: bool = True      # Log warning when AP near cap
    trigger_barbarian_hunt: bool = True  # Trigger barbarian activity

    # Detection settings
    confidence: float = 0.75


class APMonitorActivity(Activity):
    """
    Monitors action points to prevent waste.

    Process:
    1. Read current AP value (OCR)
    2. Check if AP is near cap
    3. If near cap:
       a. Log warning
       b. Optionally trigger AP-consuming activities
    4. Return status

    Success Criteria:
    - Successfully read AP value
    - Taken appropriate action if needed
    """

    def __init__(self, config: APMonitorConfig, adb: ADBConnection, screen: ScreenAnalyzer):
        super().__init__("AP Monitor", config)
        self.adb = adb
        self.screen = screen
        self.config: APMonitorConfig = config

        self.current_ap = 0

    def check_prerequisites(self) -> bool:
        """AP monitor always runs."""
        return True

    def execute(self) -> bool:
        """
        Execute AP monitoring.

        Process:
        1. Read current AP
        2. Check against threshold
        3. Alert/trigger if needed
        """
        self.logger.debug("Checking action points...")

        # Read AP value
        self.current_ap = self._read_ap_value()

        if self.current_ap == 0:
            self.logger.warning("Could not read AP value")
            return True  # Not a failure

        # Calculate percentage
        ap_percentage = (self.current_ap / self.config.ap_cap_value) * 100

        self.logger.debug(f"Current AP: {self.current_ap}/{self.config.ap_cap_value} ({ap_percentage:.1f}%)")

        # Check threshold
        if ap_percentage >= self.config.ap_cap_threshold:
            self.logger.warning(
                f"AP near cap: {self.current_ap}/{self.config.ap_cap_value} ({ap_percentage:.1f}%)"
            )

            if self.config.trigger_barbarian_hunt:
                self.logger.info("Triggering barbarian hunt to use AP")
                # The scheduler will handle triggering the barbarian activity
                # We just log the recommendation here

        return True

    def verify_completion(self) -> bool:
        """Verify AP monitoring completed."""
        return True

    def _read_ap_value(self) -> int:
        """
        Read current AP value using OCR.

        AP is usually displayed in the top-right corner of the screen.

        Returns:
            Current AP value, or 0 if cannot read
        """
        screenshot = self.adb.capture_screen_cached()

        # Define region where AP is displayed
        # For 1920x1080: Usually top-right area
        # Format: [Icon] 123/1000

        try:
            # Extract AP region
            ap_region = screenshot[10:50, 1600:1850]

            # Read text
            text = self.screen.read_text(ap_region)

            # Parse AP value
            # Expected format: "123/1000" or just "123"
            ap = self._parse_ap_text(text)

            return ap

        except Exception as e:
            self.logger.warning(f"Could not read AP value: {e}")
            return 0

    def _parse_ap_text(self, text: str) -> int:
        """
        Parse AP value from OCR text.

        Examples:
        "123/1000" -> 123
        "123" -> 123
        "1.2K/2K" -> 1200
        """
        if not text:
            return 0

        import re

        # Remove spaces
        text = text.replace(' ', '')

        # Handle fraction format (123/1000)
        if '/' in text:
            numerator = text.split('/')[0]
            return self._parse_number(numerator)

        # Handle direct number
        return self._parse_number(text)

    def _parse_number(self, text: str) -> int:
        """Parse a number from text (handles K, M suffixes)."""
        if not text:
            return 0

        text = text.upper()

        # Handle K (thousands)
        if 'K' in text:
            try:
                num = float(text.replace('K', ''))
                return int(num * 1000)
            except:
                return 0

        # Handle M (millions)
        if 'M' in text:
            try:
                num = float(text.replace('M', ''))
                return int(num * 1000000)
            except:
                return 0

        # Regular number
        try:
            return int(re.sub(r'[^\d]', '', text))
        except:
            return 0

    def get_current_ap(self) -> int:
        """Get the last read AP value."""
        return self.current_ap

    def is_ap_high(self) -> bool:
        """Check if AP is currently high."""
        if self.current_ap == 0:
            return False

        ap_percentage = (self.current_ap / self.config.ap_cap_value) * 100
        return ap_percentage >= self.config.ap_cap_threshold
