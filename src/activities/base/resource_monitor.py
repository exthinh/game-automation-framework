"""
Resource Monitor Activity

Monitors resource levels and prevents overflow.
Alerts when resources are near capacity.
Optionally triggers spending activities (research, training, etc.).
"""

from typing import Dict, Optional
import logging
import time
from dataclasses import dataclass

from ...core.activity import Activity, ActivityConfig
from ...core.adb import ADBConnection
from ...core.screen import ScreenAnalyzer


@dataclass
class ResourceMonitorConfig(ActivityConfig):
    """Configuration for resource monitoring"""

    # Resource cap thresholds (percentage)
    food_threshold: int = 90
    wood_threshold: int = 90
    stone_threshold: int = 90
    gold_threshold: int = 90

    # Resource capacity values (configure based on storehouse level)
    food_capacity: int = 1000000
    wood_capacity: int = 1000000
    stone_capacity: int = 1000000
    gold_capacity: int = 1000000

    # Actions
    alert_on_high_resources: bool = True
    trigger_spending: bool = False      # Trigger resource-spending activities

    # Detection settings
    confidence: float = 0.75


class ResourceMonitorActivity(Activity):
    """
    Monitors resource levels to prevent overflow.

    Process:
    1. Read current resource values (OCR)
    2. Check each resource against capacity threshold
    3. If near cap:
       a. Log warning
       b. Optionally trigger spending activities
    4. Return status

    Success Criteria:
    - Successfully read resource values
    - Alerted if resources near cap
    """

    def __init__(self, config: ResourceMonitorConfig, adb: ADBConnection, screen: ScreenAnalyzer):
        super().__init__("Resource Monitor", config)
        self.adb = adb
        self.screen = screen
        self.config: ResourceMonitorConfig = config

        self.resources = {
            'food': 0,
            'wood': 0,
            'stone': 0,
            'gold': 0
        }

    def check_prerequisites(self) -> bool:
        """Resource monitor always runs."""
        return True

    def execute(self) -> bool:
        """
        Execute resource monitoring.

        Process:
        1. Read all resource values
        2. Check against thresholds
        3. Alert if needed
        """
        self.logger.debug("Checking resource levels...")

        # Read resources
        self._read_resources()

        # Check each resource
        warnings = []

        for resource, amount in self.resources.items():
            if amount == 0:
                continue

            capacity = getattr(self.config, f'{resource}_capacity')
            threshold = getattr(self.config, f'{resource}_threshold')

            percentage = (amount / capacity) * 100

            if percentage >= threshold:
                warnings.append(f"{resource.capitalize()}: {amount:,}/{capacity:,} ({percentage:.1f}%)")

        if warnings and self.config.alert_on_high_resources:
            self.logger.warning("Resources near cap:")
            for warning in warnings:
                self.logger.warning(f"  {warning}")

            if self.config.trigger_spending:
                self.logger.info("Triggering resource-spending activities")
                # The scheduler will handle triggering spending activities

        return True

    def verify_completion(self) -> bool:
        """Verify resource monitoring completed."""
        return True

    def _read_resources(self):
        """Read all resource values using OCR."""
        screenshot = self.adb.capture_screen_cached()

        # Define regions where resources are displayed (top of screen)
        # For 1920x1080: Food ~200, Wood ~500, Stone ~800, Gold ~1100

        resource_regions = {
            'food': (200, 10, 180, 40),    # (x, y, width, height)
            'wood': (500, 10, 180, 40),
            'stone': (800, 10, 180, 40),
            'gold': (1100, 10, 180, 40)
        }

        for resource, (x, y, w, h) in resource_regions.items():
            try:
                region = screenshot[y:y+h, x:x+w]
                text = self.screen.read_text(region)
                amount = self._parse_resource_amount(text)
                self.resources[resource] = amount

            except Exception as e:
                self.logger.debug(f"Could not read {resource}: {e}")

    def _parse_resource_amount(self, text: str) -> int:
        """Parse resource amount from OCR text."""
        if not text:
            return 0

        import re

        # Remove commas and spaces
        text = text.replace(',', '').replace(' ', '').upper()

        # Handle M (millions)
        if 'M' in text:
            try:
                num = float(text.replace('M', ''))
                return int(num * 1000000)
            except:
                return 0

        # Handle K (thousands)
        if 'K' in text:
            try:
                num = float(text.replace('K', ''))
                return int(num * 1000)
            except:
                return 0

        # Regular number
        try:
            return int(re.sub(r'[^\d]', '', text))
        except:
            return 0

    def get_resources(self) -> Dict[str, int]:
        """Get last read resource values."""
        return self.resources.copy()

    def is_any_resource_high(self) -> bool:
        """Check if any resource is near cap."""
        for resource, amount in self.resources.items():
            if amount == 0:
                continue

            capacity = getattr(self.config, f'{resource}_capacity')
            threshold = getattr(self.config, f'{resource}_threshold')

            percentage = (amount / capacity) * 100

            if percentage >= threshold:
                return True

        return False
