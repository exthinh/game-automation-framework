"""
Barbarian Hunt Activity

Hunts barbarians on the map for commander XP and loot.
Uses color detection to find barbarians (red markers).

This is a HIGH priority activity for commander progression.
Based on: CAttackBarbarianTab from original WhaleBots
"""

from typing import List, Tuple, Optional
import logging
import time
from dataclasses import dataclass
import numpy as np

from ...core.activity import Activity, ActivityConfig
from ...core.adb import ADBConnection
from ...core.screen import ScreenAnalyzer


@dataclass
class BarbarianHuntConfig(ActivityConfig):
    """Configuration for barbarian hunting"""

    # Target configuration
    target_level: int = 5              # Barbarian level to hunt
    target_level_range: Tuple[int, int] = (4, 6)  # Or range

    # March management
    max_hunts_per_run: int = 5
    check_march_slots: bool = True
    auto_return_marches: bool = False

    # Troop management
    check_troop_availability: bool = True
    min_troop_percent: int = 80        # Min troops % before hunting
    stop_on_troop_death: bool = True
    death_cooldown_minutes: int = 30

    # AP management
    use_action_points: bool = True
    min_ap_reserve: int = 50           # Keep this much AP in reserve

    # Map navigation
    max_search_attempts: int = 10
    search_radius_tiles: int = 20

    # Detection settings
    confidence: float = 0.75


class BarbarianHuntActivity(Activity):
    """
    Hunts barbarians for commander XP.

    Process:
    1. Check prerequisites (marches, troops, AP)
    2. Navigate to world map
    3. Find barbarians using color detection (red markers)
    4. Read barbarian level (OCR)
    5. Filter by target level
    6. Select closest/best barbarian
    7. Send attack march
    8. Verify march sent
    9. Repeat until max hunts reached

    Success Criteria:
    - Sent at least one attack march
    - OR no barbarians found
    - OR march slots full
    """

    def __init__(self, config: BarbarianHuntConfig, adb: ADBConnection, screen: ScreenAnalyzer):
        super().__init__("Barbarian Hunt", config)
        self.adb = adb
        self.screen = screen
        self.config: BarbarianHuntConfig = config

        self.hunts_sent = 0
        self.available_marches = 0

    def check_prerequisites(self) -> bool:
        """Check if we can hunt barbarians."""
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
                self.logger.info(f"Insufficient troops: {troop_percent}% < {self.config.min_troop_percent}%")
                return False

        # Check AP
        if self.config.use_action_points:
            ap = self._get_current_ap()
            if ap < self.config.min_ap_reserve:
                self.logger.info(f"Insufficient AP: {ap} < {self.config.min_ap_reserve}")
                return False

        return True

    def execute(self) -> bool:
        """Execute barbarian hunting."""
        self.logger.info("Starting barbarian hunt...")

        # Navigate to world map
        if not self._navigate_to_map():
            self.logger.error("Failed to navigate to world map")
            return False

        time.sleep(1.5)

        self.hunts_sent = 0

        # Hunt barbarians
        for i in range(self.config.max_hunts_per_run):
            if self.hunts_sent >= self.available_marches:
                self.logger.info("All march slots used")
                break

            # Find barbarian
            barbarian = self._find_target_barbarian()
            if not barbarian:
                self.logger.info("No suitable barbarians found")
                break

            # Attack barbarian
            if self._attack_barbarian(barbarian):
                self.hunts_sent += 1
                self.logger.info(f"Sent hunt {self.hunts_sent}/{self.config.max_hunts_per_run}")
                time.sleep(1.0)
            else:
                self.logger.warning("Failed to send attack")
                break

        # Return to city
        self._navigate_to_city()

        if self.hunts_sent > 0:
            self.logger.info(f"Sent {self.hunts_sent} barbarian hunt marches")
            return True
        else:
            return True  # Not an error, just nothing to hunt

    def verify_completion(self) -> bool:
        """Verify barbarian hunt completed."""
        if not self._is_on_city_view():
            self._navigate_to_city()
        return True

    def _find_target_barbarian(self) -> Optional[Tuple[int, int]]:
        """
        Find a suitable barbarian to attack.

        Uses color detection to find red markers (barbarians).

        Returns:
            (x, y) coordinates of barbarian, or None
        """
        screenshot = self.adb.capture_screen_cached()

        # Find red markers (barbarians) using color detection
        # Barbarians appear as red markers on the map
        barbarian_locations = self.screen.find_color_regions(
            screenshot,
            lower_hsv=(0, 100, 100),    # Red lower bound
            upper_hsv=(10, 255, 255)    # Red upper bound
        )

        if not barbarian_locations:
            self.logger.debug("No barbarians detected on screen")
            return None

        # Filter barbarians by level
        valid_barbarians = []
        for location in barbarian_locations:
            level = self._read_barbarian_level(screenshot, location)
            if level and self._is_target_level(level):
                valid_barbarians.append((location, level))

        if not valid_barbarians:
            self.logger.debug("No barbarians matching target level")
            return None

        # Select closest barbarian
        # Simplified: just take first one
        # TODO: Calculate distance and select closest
        return valid_barbarians[0][0]

    def _read_barbarian_level(self, screenshot, location: Tuple[int, int]) -> Optional[int]:
        """
        Read barbarian level using OCR.

        Args:
            screenshot: Map screenshot
            location: (x, y) of barbarian marker

        Returns:
            Barbarian level, or None
        """
        x, y = location

        # Extract region around barbarian marker
        # Level is usually displayed near the marker
        region = screenshot[max(0, y-30):y+30, max(0, x-30):x+30]

        try:
            text = self.screen.read_text(region)
            # Extract first number from text
            import re
            numbers = re.findall(r'\d+', text)
            if numbers:
                return int(numbers[0])
        except:
            pass

        return None

    def _is_target_level(self, level: int) -> bool:
        """Check if barbarian level matches target."""
        if self.config.target_level_range:
            min_level, max_level = self.config.target_level_range
            return min_level <= level <= max_level
        else:
            return level == self.config.target_level

    def _attack_barbarian(self, location: Tuple[int, int]) -> bool:
        """
        Send attack march to barbarian.

        Args:
            location: (x, y) of barbarian

        Returns:
            True if attack sent successfully
        """
        x, y = location

        # Tap barbarian
        self.adb.tap(x, y, randomize=True)
        time.sleep(1.5)

        # Look for attack button
        screenshot = self.adb.capture_screen_cached()
        attack_button = self.screen.find_template(
            screenshot,
            'templates/buttons/attack.png',
            confidence=self.config.confidence
        )

        if not attack_button:
            return False

        # Tap attack
        self.adb.tap(attack_button[0], attack_button[1], randomize=True)
        time.sleep(1.0)

        # New troops button (select commanders/troops)
        screenshot = self.adb.capture_screen_cached()
        new_troops_button = self.screen.find_template(
            screenshot,
            'templates/buttons/new_troops_combat.png',
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

    def _get_current_ap(self) -> int:
        """Get current action points."""
        # Simplified
        # TODO: Implement AP reading via OCR
        return 1000

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
