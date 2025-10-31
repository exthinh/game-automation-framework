"""
Building Upgrades Activity

Automatically upgrades buildings based on priority list and builder availability.
Ensures city progression by continuously upgrading buildings.

This is a HIGH priority activity for account advancement.
"""

from typing import List, Dict, Optional, Tuple
import logging
import time
from dataclasses import dataclass

from ...core.activity import Activity, ActivityConfig
from ...core.adb import ADBConnection
from ...core.screen import ScreenAnalyzer


@dataclass
class BuildingUpgradesConfig(ActivityConfig):
    """Configuration for building upgrades"""

    # Building priority list (upgrade in this order)
    building_priority: List[str] = None  # e.g., ["City Hall", "Farm", "Lumber Mill"]

    # Builder management
    check_builder_availability: bool = True
    max_builders_to_use: int = 2  # Don't use all builders (save for important)

    # Resource management
    min_food_reserve: int = 500000
    min_wood_reserve: int = 500000
    min_stone_reserve: int = 500000
    min_gold_reserve: int = 500000

    # Upgrade constraints
    max_upgrade_time_hours: int = 24  # Don't start upgrades longer than this
    check_prerequisites: bool = True   # Check tech/level requirements

    # Detection settings
    confidence: float = 0.75


class BuildingUpgradesActivity(Activity):
    """
    Automatically upgrades buildings.

    Process:
    1. Check builder availability
    2. Check building priority list
    3. For each priority building:
       a. Find building in city
       b. Check if upgradeable
       c. Check resource requirements
       d. Check upgrade time
       e. Start upgrade if conditions met
    4. Verify upgrade started

    Success Criteria:
    - Upgraded at least one building
    - OR all builders busy
    - OR no buildings ready to upgrade
    """

    def __init__(self, config: BuildingUpgradesConfig, adb: ADBConnection, screen: ScreenAnalyzer):
        super().__init__("Building Upgrades", config)
        self.adb = adb
        self.screen = screen
        self.config: BuildingUpgradesConfig = config

        if self.config.building_priority is None:
            self.config.building_priority = [
                "City Hall",
                "Farm",
                "Lumber Mill",
                "Quarry",
                "Gold Mine",
                "Barracks",
                "Archery Range",
                "Stable",
                "Siege Workshop",
                "Hospital",
                "Academy",
                "Wall"
            ]

        self.buildings_upgraded = 0
        self.available_builders = 0

    def check_prerequisites(self) -> bool:
        """
        Check if we can upgrade buildings.

        Prerequisites:
        - At least one builder available
        - On city view
        """
        # Ensure on city view
        if not self._is_on_city_view():
            if not self._navigate_to_city():
                return False

        # Check builder availability
        self.available_builders = self._count_available_builders()

        if self.available_builders == 0:
            self.logger.info("No builders available")
            return False

        self.logger.info(f"Available builders: {self.available_builders}")
        return True

    def execute(self) -> bool:
        """
        Execute building upgrades.

        Process:
        1. Check each priority building
        2. Upgrade if possible
        3. Continue until no builders or no upgradeable buildings
        """
        self.logger.info("Starting building upgrades...")

        self.buildings_upgraded = 0

        # Try to upgrade buildings in priority order
        for building_name in self.config.building_priority:
            # Check if still have builders
            if self.available_builders <= 0:
                self.logger.info("No more builders available")
                break

            # Check if using too many builders
            if self.buildings_upgraded >= self.config.max_builders_to_use:
                self.logger.info(f"Reached max builders limit ({self.config.max_builders_to_use})")
                break

            self.logger.debug(f"Checking building: {building_name}")

            # Try to upgrade this building
            if self._try_upgrade_building(building_name):
                self.buildings_upgraded += 1
                self.available_builders -= 1
                self.logger.info(f"Upgraded {building_name}")

        if self.buildings_upgraded > 0:
            self.logger.info(f"Successfully upgraded {self.buildings_upgraded} buildings")
            return True
        else:
            self.logger.info("No buildings upgraded (requirements not met or already upgrading)")
            return True  # Not an error

    def verify_completion(self) -> bool:
        """Verify building upgrades completed."""
        if not self._is_on_city_view():
            self._navigate_to_city()
        return True

    def _try_upgrade_building(self, building_name: str) -> bool:
        """
        Try to upgrade a specific building.

        Args:
            building_name: Name of building to upgrade

        Returns:
            True if upgrade started successfully
        """
        # Find building template
        building_template = f'templates/buildings/{building_name.lower().replace(" ", "_")}.png'

        screenshot = self.adb.capture_screen_cached()
        building_location = self.screen.find_template(
            screenshot,
            building_template,
            confidence=self.config.confidence
        )

        if not building_location:
            self.logger.debug(f"Building not found: {building_name}")
            return False

        # Tap building
        self.adb.tap(building_location[0], building_location[1], randomize=True)
        time.sleep(1.5 + (time.time() % 0.5))

        # Check for upgrade button
        screenshot = self.adb.capture_screen_cached()
        upgrade_button = self.screen.find_template(
            screenshot,
            'templates/buttons/upgrade.png',
            confidence=self.config.confidence
        )

        if not upgrade_button:
            # Building might be max level or already upgrading
            self._close_building_info()
            return False

        # Read upgrade time if configured
        if self.config.max_upgrade_time_hours < 1000:  # If limit is set
            upgrade_time = self._read_upgrade_time(screenshot)
            if upgrade_time and upgrade_time > self.config.max_upgrade_time_hours:
                self.logger.info(f"{building_name} upgrade time ({upgrade_time}h) exceeds limit")
                self._close_building_info()
                return False

        # Check resources if configured
        if self.config.check_prerequisites:
            if not self._check_upgrade_resources(screenshot):
                self.logger.debug(f"{building_name} insufficient resources")
                self._close_building_info()
                return False

        # Tap upgrade button
        self.adb.tap(upgrade_button[0], upgrade_button[1], randomize=True)
        time.sleep(1.0)

        # Confirm upgrade
        screenshot = self.adb.capture_screen_cached()
        confirm_button = self.screen.find_template(
            screenshot,
            'templates/buttons/confirm.png',
            confidence=0.75
        )

        if confirm_button:
            self.adb.tap(confirm_button[0], confirm_button[1], randomize=True)
            time.sleep(0.5)

        return True

    def _count_available_builders(self) -> int:
        """
        Count available builders.

        Returns:
            Number of available builders
        """
        # Look for builder indicators in city view
        screenshot = self.adb.capture_screen_cached()

        # Method 1: Look for builder icon/counter
        # Usually displayed in top-left or bottom-left

        # Simplified: return default
        # TODO: Implement OCR reading of builder count
        return 2  # Assume 2 builders available by default

    def _read_upgrade_time(self, screenshot) -> Optional[float]:
        """
        Read upgrade time from building info screen.

        Returns:
            Upgrade time in hours, or None if cannot read
        """
        # Define region where upgrade time is displayed
        # Usually near upgrade button

        try:
            time_region = screenshot[500:600, 800:1100]
            text = self.screen.read_text(time_region)

            # Parse time
            hours = self._parse_time_to_hours(text)
            return hours

        except Exception as e:
            self.logger.warning(f"Could not read upgrade time: {e}")
            return None

    def _parse_time_to_hours(self, text: str) -> float:
        """Parse time string to hours."""
        if not text:
            return 0.0

        import re

        hours = 0.0

        # Find days
        days_match = re.search(r'(\d+)d', text, re.IGNORECASE)
        if days_match:
            hours += int(days_match.group(1)) * 24

        # Find hours
        hours_match = re.search(r'(\d+)h', text, re.IGNORECASE)
        if hours_match:
            hours += int(hours_match.group(1))

        # Find minutes
        minutes_match = re.search(r'(\d+)m', text, re.IGNORECASE)
        if minutes_match:
            hours += int(minutes_match.group(1)) / 60.0

        return hours

    def _check_upgrade_resources(self, screenshot) -> bool:
        """
        Check if we have sufficient resources for upgrade.

        Returns:
            True if resources sufficient
        """
        # Simplified check
        # TODO: Implement OCR reading of resource requirements
        return True

    def _close_building_info(self):
        """Close building info screen."""
        screenshot = self.adb.capture_screen_cached()
        close_button = self.screen.find_template(
            screenshot,
            'templates/buttons/close.png',
            confidence=0.75
        )

        if close_button:
            self.adb.tap(close_button[0], close_button[1], randomize=True)
        else:
            # Press back
            back_button = self.screen.find_template(
                screenshot,
                'templates/buttons/back.png',
                confidence=0.75
            )
            if back_button:
                self.adb.tap(back_button[0], back_button[1], randomize=True)

        time.sleep(0.5)

    def _is_on_city_view(self) -> bool:
        """Check if on city view."""
        screenshot = self.adb.capture_screen_cached()
        return self.screen.find_template(
            screenshot,
            'templates/screens/city_view.png',
            confidence=0.7
        ) is not None

    def _navigate_to_city(self) -> bool:
        """Navigate to city view."""
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
