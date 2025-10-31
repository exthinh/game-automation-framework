"""
Resource Gathering Activity

Sends troops to gather resources (food, wood, stone, gold) from map nodes.
Uses color detection to find resource nodes.

This is a CRITICAL activity - the most complex and time-consuming for bots.
Based on: CGatherAllianceResourcesDlg from original WhaleBots
"""

from typing import List, Tuple, Optional, Dict
import logging
import time
from dataclasses import dataclass
import numpy as np

from ...core.activity import Activity, ActivityConfig
from ...core.adb import ADBConnection
from ...core.screen import ScreenAnalyzer


@dataclass
class ResourceGatheringConfig(ActivityConfig):
    """Configuration for resource gathering"""

    # Resource priorities (gather in this order)
    resource_priority: List[str] = None  # ["gold", "stone", "wood", "food"]

    # Resource constraints
    min_resource_amount: int = 50000    # Min node amount
    max_distance_tiles: int = 50        # Max distance from city

    # March management
    max_gathers_per_run: int = 5
    check_march_slots: bool = True
    auto_recall_when_full: bool = False

    # Troop management
    check_troop_availability: bool = True
    min_troop_percent: int = 80
    troop_load_capacity: int = 200000  # Troops can carry this much

    # Territory rules
    exclude_alliance_territory: bool = False
    exclude_other_alliance: bool = True

    # Gathering buffs
    use_gathering_buff: bool = False    # Use 8hr gathering speed buff

    # Map navigation
    max_search_attempts: int = 10
    search_radius_tiles: int = 20

    # Detection settings
    confidence: float = 0.75


class ResourceGatheringActivity(Activity):
    """
    Sends gathering marches to resource nodes.

    Process:
    1. Check prerequisites (marches, troops)
    2. Navigate to world map
    3. Find resource nodes using color detection
    4. Read node amounts (OCR)
    5. Filter by type, amount, distance
    6. Select best node
    7. Send gathering march
    8. Verify march sent
    9. Repeat until max gathers reached

    Success Criteria:
    - Sent at least one gathering march
    - OR no suitable nodes found
    - OR march slots full
    """

    def __init__(self, config: ResourceGatheringConfig, adb: ADBConnection, screen: ScreenAnalyzer):
        super().__init__("Resource Gathering", config)
        self.adb = adb
        self.screen = screen
        self.config: ResourceGatheringConfig = config

        if self.config.resource_priority is None:
            self.config.resource_priority = ["gold", "stone", "wood", "food"]

        self.gathers_sent = 0
        self.available_marches = 0

        # Color detection HSV ranges for resources
        self.resource_colors = {
            'gold': ((20, 100, 100), (30, 255, 255)),    # Yellow
            'stone': ((0, 0, 50), (180, 50, 200)),       # Gray
            'wood': ((40, 50, 50), (80, 255, 255)),      # Green
            'food': ((10, 50, 50), (20, 255, 255))       # Light brown
        }

    def check_prerequisites(self) -> bool:
        """Check if we can send gathering marches."""
        # Check march availability
        if self.config.check_march_slots:
            self.available_marches = self._get_available_march_slots()
            if self.available_marches == 0:
                self.logger.info("No march slots available")
                return False

        # Check troop availability
        if self.config.check_troop_availability:
            troop_percent = self._get_troop_availability_percent()
            if troop_percent < self.config.min_troop_percent:
                self.logger.info(f"Insufficient troops: {troop_percent}%")
                return False

        return True

    def execute(self) -> bool:
        """Execute resource gathering."""
        self.logger.info("Starting resource gathering...")

        # Use gathering buff if configured
        if self.config.use_gathering_buff:
            self._use_gathering_buff()

        # Navigate to world map
        if not self._navigate_to_map():
            self.logger.error("Failed to navigate to world map")
            return False

        time.sleep(1.5)

        self.gathers_sent = 0

        # Send gathering marches
        for i in range(self.config.max_gathers_per_run):
            if self.gathers_sent >= self.available_marches:
                self.logger.info("All march slots used")
                break

            # Find resource node
            node = self._find_resource_node()
            if not node:
                self.logger.info("No suitable resource nodes found")
                break

            # Send gathering march
            if self._send_gathering_march(node):
                self.gathers_sent += 1
                self.logger.info(f"Sent gather {self.gathers_sent}/{self.config.max_gathers_per_run}")
                time.sleep(1.0)
            else:
                self.logger.warning("Failed to send gathering march")
                break

        # Return to city
        self._navigate_to_city()

        if self.gathers_sent > 0:
            self.logger.info(f"Sent {self.gathers_sent} gathering marches")
            return True
        else:
            return True  # Not an error

    def verify_completion(self) -> bool:
        """Verify gathering completed."""
        if not self._is_on_city_view():
            self._navigate_to_city()
        return True

    def _find_resource_node(self) -> Optional[Dict]:
        """
        Find a suitable resource node to gather from.

        Uses color detection to find nodes by resource type.

        Returns:
            Dict with node info {type, location, amount}, or None
        """
        screenshot = self.adb.capture_screen_cached()

        # Search for each resource type in priority order
        for resource_type in self.config.resource_priority:
            lower_hsv, upper_hsv = self.resource_colors[resource_type]

            # Find nodes of this type using color detection
            node_locations = self.screen.find_color_regions(
                screenshot,
                lower_hsv=lower_hsv,
                upper_hsv=upper_hsv
            )

            if not node_locations:
                continue

            # Check each node
            for location in node_locations:
                # Read node amount
                amount = self._read_node_amount(screenshot, location)

                # Filter by amount
                if amount and amount >= self.config.min_resource_amount:
                    return {
                        'type': resource_type,
                        'location': location,
                        'amount': amount
                    }

        return None

    def _read_node_amount(self, screenshot, location: Tuple[int, int]) -> Optional[int]:
        """
        Read resource node amount using OCR.

        Args:
            screenshot: Map screenshot
            location: (x, y) of node

        Returns:
            Resource amount, or None
        """
        x, y = location

        # Extract region around node
        region = screenshot[max(0, y-40):y+40, max(0, x-40):x+40]

        try:
            text = self.screen.read_text(region)
            # Parse amount (e.g., "150K", "1.2M")
            amount = self._parse_resource_amount(text)
            return amount
        except:
            pass

        return None

    def _parse_resource_amount(self, text: str) -> Optional[int]:
        """Parse resource amount from text."""
        if not text:
            return None

        import re

        text = text.upper().replace(',', '').replace(' ', '')

        # Handle K (thousands) and M (millions)
        if 'M' in text:
            match = re.search(r'(\d+\.?\d*)M', text)
            if match:
                return int(float(match.group(1)) * 1000000)

        if 'K' in text:
            match = re.search(r'(\d+\.?\d*)K', text)
            if match:
                return int(float(match.group(1)) * 1000)

        # Direct number
        numbers = re.findall(r'\d+', text)
        if numbers:
            return int(numbers[0])

        return None

    def _send_gathering_march(self, node: Dict) -> bool:
        """
        Send gathering march to node.

        Args:
            node: Dict with node info

        Returns:
            True if march sent successfully
        """
        x, y = node['location']

        # Tap node
        self.adb.tap(x, y, randomize=True)
        time.sleep(1.5)

        # Look for gather button
        screenshot = self.adb.capture_screen_cached()
        gather_button = self.screen.find_template(
            screenshot,
            'templates/buttons/gather.png',
            confidence=self.config.confidence
        )

        if not gather_button:
            return False

        # Tap gather
        self.adb.tap(gather_button[0], gather_button[1], randomize=True)
        time.sleep(1.0)

        # New troops button (select commanders/troops)
        screenshot = self.adb.capture_screen_cached()
        new_troops_button = self.screen.find_template(
            screenshot,
            'templates/buttons/new_troops.png',
            confidence=self.config.confidence
        )

        if new_troops_button:
            self.adb.tap(new_troops_button[0], new_troops_button[1], randomize=True)
            time.sleep(1.0)

        # March button
        screenshot = self.adb.capture_screen_cached()
        march_button = self.screen.find_template(
            screenshot,
            'templates/buttons/march.png',
            confidence=self.config.confidence
        )

        if march_button:
            self.adb.tap(march_button[0], march_button[1], randomize=True)
            time.sleep(0.5)
            return True

        return False

    def _use_gathering_buff(self):
        """Activate 8-hour gathering speed buff."""
        self.logger.info("Using gathering buff...")
        # TODO: Implement buff activation
        # Navigate to items > buffs > use gathering buff

    def _get_available_march_slots(self) -> int:
        """Get number of available march slots."""
        # Simplified
        # TODO: Implement march slot counting
        return 2

    def _get_troop_availability_percent(self) -> int:
        """Get available troops as percentage."""
        # Simplified
        # TODO: Implement troop counting via OCR
        return 100

    def _navigate_to_map(self) -> bool:
        """Navigate to world map."""
        if not self._is_on_city_view():
            if not self._navigate_to_city():
                return False

        screenshot = self.adb.capture_screen_cached()
        map_button = self.screen.find_template(
            screenshot,
            'templates/buttons/world_map.png',
            confidence=self.config.confidence
        )

        if not map_button:
            return False

        self.adb.tap(map_button[0], map_button[1], randomize=True)
        time.sleep(1.5)
        return True

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
