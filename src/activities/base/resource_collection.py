"""
Resource Collection (City) Activity

Collects resources from city production buildings (farms, lumber mills, quarries, gold mines).
Detects floating resource indicators and taps them to collect.

Based on: CCollectCityRssTab from original WhaleBots
Configuration Key: utl_collectcityrss
"""

from typing import List, Tuple, Optional
import logging
import time
from dataclasses import dataclass

from ...core.activity import Activity, ActivityConfig
from ...core.adb import ADBConnection
from ...core.screen import ScreenAnalyzer


@dataclass
class ResourceCollectionConfig(ActivityConfig):
    """Configuration for city resource collection"""

    # Collection settings
    collect_all: bool = True           # Collect all available resources
    max_collections_per_run: int = 20  # Maximum buildings to tap per run

    # Resource priorities (if not collecting all)
    prioritize_gold: bool = True       # Collect gold mines first
    prioritize_food: bool = False      # Then food
    prioritize_stone: bool = False     # Then stone
    prioritize_wood: bool = False      # Then wood

    # Detection settings
    confidence: float = 0.70           # Template matching confidence
    search_entire_city: bool = True    # Search whole screen vs specific regions

    # Timing
    delay_between_taps: float = 0.3    # Seconds between collection taps


class ResourceCollectionActivity(Activity):
    """
    Automatically collects resources from city buildings.

    Process:
    1. Ensure on city view
    2. Scan for resource collection indicators (floating icons)
    3. Tap each indicator to collect resources
    4. Count collections and verify

    Success Criteria:
    - Collected at least one resource
    - OR no resources available to collect
    """

    def __init__(self, config: ResourceCollectionConfig, adb: ADBConnection, screen: ScreenAnalyzer):
        super().__init__("Resource Collection (City)", config)
        self.adb = adb
        self.screen = screen
        self.config: ResourceCollectionConfig = config

        self.collections_this_run = 0

    def check_prerequisites(self) -> bool:
        """
        Check if we can collect city resources.

        Prerequisites:
        - On city view screen
        - Game is running and connected
        """
        # Check if on city view
        if not self._is_on_city_view():
            self.logger.info("Not on city view, navigating...")
            if not self._navigate_to_city():
                self.logger.error("Failed to navigate to city view")
                return False

        return True

    def execute(self) -> bool:
        """
        Execute resource collection activity.

        Process:
        1. Scan city view for resource indicators
        2. Tap each indicator to collect
        3. Count successful collections
        """
        self.logger.info("Scanning city for collectible resources...")

        self.collections_this_run = 0

        # Take screenshot
        screenshot = self.adb.capture_screen_cached()
        if screenshot is None:
            self.logger.error("Failed to capture screenshot")
            return False

        # Find all resource indicators
        resource_locations = self._find_resource_indicators(screenshot)

        if not resource_locations:
            self.logger.info("No resources available to collect")
            return True  # Not an error, just nothing to collect

        self.logger.info(f"Found {len(resource_locations)} resources to collect")

        # Limit collections per run
        max_to_collect = min(len(resource_locations), self.config.max_collections_per_run)

        # Tap each resource indicator
        for i, (x, y) in enumerate(resource_locations[:max_to_collect]):
            self.logger.debug(f"Collecting resource {i+1}/{max_to_collect} at ({x}, {y})")

            # Tap the resource indicator
            self.adb.tap(x, y, randomize=True)

            # Wait for collection animation
            time.sleep(self.config.delay_between_taps + (time.time() % 0.2))

            self.collections_this_run += 1

        self.logger.info(f"Collected {self.collections_this_run} resources")

        # Success if we collected anything
        return self.collections_this_run > 0

    def verify_completion(self) -> bool:
        """
        Verify resource collection completed successfully.

        Check:
        - Still on city view
        - Collections counter incremented
        """
        # Verify still on city view
        if not self._is_on_city_view():
            self.logger.warning("Not on city view after collection")
            self._navigate_to_city()

        # Success if we collected at least one resource
        return self.collections_this_run > 0

    def _find_resource_indicators(self, screenshot) -> List[Tuple[int, int]]:
        """
        Find all resource collection indicators on screen.

        Resource indicators are floating icons above buildings that
        indicate resources are ready to collect.

        Returns:
            List of (x, y) coordinates of resource indicators
        """
        locations = []

        # Try to find the generic resource indicator template
        # This is usually a floating icon/sparkle above the building
        resource_icon_templates = [
            'templates/icons/resource_ready.png',
            'templates/icons/resource_collect.png',
            'templates/icons/building_resource.png'
        ]

        for template in resource_icon_templates:
            # Find all instances of this template
            found_locations = self.screen.find_all_templates(
                screenshot,
                template,
                confidence=self.config.confidence
            )

            if found_locations:
                self.logger.debug(f"Found {len(found_locations)} resources using {template}")
                locations.extend(found_locations)

        # Remove duplicates (same location found by multiple templates)
        locations = self._remove_duplicate_locations(locations, min_distance=50)

        # Sort by priority if configured
        if not self.config.collect_all:
            locations = self._sort_by_priority(locations, screenshot)

        return locations

    def _remove_duplicate_locations(
        self,
        locations: List[Tuple[int, int]],
        min_distance: int = 50
    ) -> List[Tuple[int, int]]:
        """
        Remove duplicate locations that are too close together.

        Args:
            locations: List of (x, y) tuples
            min_distance: Minimum distance between locations

        Returns:
            Filtered list of locations
        """
        if not locations:
            return []

        # Sort by y position (top to bottom)
        locations = sorted(locations, key=lambda loc: (loc[1], loc[0]))

        filtered = [locations[0]]

        for x, y in locations[1:]:
            # Check if this location is far enough from all filtered locations
            is_duplicate = False

            for fx, fy in filtered:
                distance = ((x - fx) ** 2 + (y - fy) ** 2) ** 0.5
                if distance < min_distance:
                    is_duplicate = True
                    break

            if not is_duplicate:
                filtered.append((x, y))

        return filtered

    def _sort_by_priority(
        self,
        locations: List[Tuple[int, int]],
        screenshot
    ) -> List[Tuple[int, int]]:
        """
        Sort resource locations by configured priority.

        Priority order (if enabled):
        1. Gold mines (yellow/gold color)
        2. Food farms (green color)
        3. Stone quarries (gray color)
        4. Wood lumber mills (brown color)
        """
        # This is a simplified version
        # In reality, we'd need to detect the resource type by color or icon

        # For now, just return locations as-is
        # TODO: Implement color detection to identify resource types

        return locations

    def _is_on_city_view(self) -> bool:
        """Check if currently on city view screen."""
        screenshot = self.adb.capture_screen_cached()

        # Look for city view indicators
        city_indicator = self.screen.find_template(
            screenshot,
            'templates/screens/city_view.png',
            confidence=0.7
        )

        # Alternative: check for city center building
        if city_indicator is None:
            city_center = self.screen.find_template(
                screenshot,
                'templates/buildings/city_center.png',
                confidence=0.7
            )
            return city_center is not None

        return city_indicator is not None

    def _navigate_to_city(self) -> bool:
        """Navigate back to city view."""
        # Try pressing back button a few times
        for _ in range(3):
            # Look for back button
            screenshot = self.adb.capture_screen_cached()
            back_button = self.screen.find_template(
                screenshot,
                'templates/buttons/back.png',
                confidence=0.75
            )

            if back_button:
                self.adb.tap(back_button[0], back_button[1], randomize=True)
                time.sleep(1.0)

            # Check if on city view now
            if self._is_on_city_view():
                return True

        # If still not on city view, try clicking home button
        screenshot = self.adb.capture_screen_cached()
        home_button = self.screen.find_template(
            screenshot,
            'templates/buttons/home.png',
            confidence=0.75
        )

        if home_button:
            self.adb.tap(home_button[0], home_button[1], randomize=True)
            time.sleep(1.5)
            return self._is_on_city_view()

        return False
