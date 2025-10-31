"""
Commander XP Activity

Uses commander XP tomes/books on specific commanders to level them up.
Helps progress commanders faster than just using them in combat.

Based on reverse engineering, commander management is key to game progression.
"""

from typing import List, Optional
import logging
import time
from dataclasses import dataclass

from ...core.activity import Activity, ActivityConfig
from ...core.adb import ADBConnection
from ...core.screen import ScreenAnalyzer


@dataclass
class CommanderXPConfig(ActivityConfig):
    """Configuration for commander XP usage"""

    # Commander priorities (list of commander names in order of priority)
    commander_priority: List[str] = None  # e.g., ["Sun Tzu", "Joan of Arc", "Pelagius"]

    # XP tome usage
    use_small_tomes: bool = True       # Use 50 XP tomes
    use_medium_tomes: bool = True      # Use 500 XP tomes
    use_large_tomes: bool = False      # Use 5000 XP tomes (save for legendaries)

    # Limits
    max_commanders_per_run: int = 5    # Max commanders to level per run
    min_tomes_to_keep: int = 10        # Keep this many tomes in reserve

    # Detection settings
    confidence: float = 0.75


class CommanderXPActivity(Activity):
    """
    Uses XP tomes on commanders to level them up.

    Process:
    1. Navigate to commanders screen
    2. Select first priority commander
    3. Use XP tomes on commander
    4. Repeat for other priority commanders
    5. Close and return

    Success Criteria:
    - Used XP tomes on at least one commander
    - OR no tomes available
    """

    def __init__(self, config: CommanderXPConfig, adb: ADBConnection, screen: ScreenAnalyzer):
        super().__init__("Commander XP", config)
        self.adb = adb
        self.screen = screen
        self.config: CommanderXPConfig = config

        if self.config.commander_priority is None:
            self.config.commander_priority = []

        self.commanders_leveled = 0

    def check_prerequisites(self) -> bool:
        """
        Check if we can use commander XP.

        Prerequisites:
        - Have commander priority list configured
        - Game is running
        """
        if not self.config.commander_priority:
            self.logger.warning("No commander priority list configured")
            return False

        return True

    def execute(self) -> bool:
        """
        Execute commander XP usage.

        Process:
        1. Navigate to commanders screen
        2. For each priority commander:
           a. Find and select commander
           b. Use XP tomes
        3. Close and return
        """
        self.logger.info("Using XP tomes on commanders...")

        # Navigate to commanders screen
        if not self._navigate_to_commanders():
            self.logger.error("Failed to navigate to commanders screen")
            return False

        time.sleep(1.0)

        # Level commanders
        self.commanders_leveled = 0

        for commander_name in self.config.commander_priority[:self.config.max_commanders_per_run]:
            self.logger.debug(f"Looking for commander: {commander_name}")

            if self._level_commander(commander_name):
                self.commanders_leveled += 1

            # Small delay between commanders
            time.sleep(0.5)

        # Close commanders screen
        self._close_commanders_screen()

        # Navigate back to city
        self._navigate_to_city()

        if self.commanders_leveled > 0:
            self.logger.info(f"Leveled {self.commanders_leveled} commanders")
            return True
        else:
            self.logger.info("No commanders leveled (no tomes or already max level)")
            return True  # Not an error

    def verify_completion(self) -> bool:
        """Verify commander XP usage completed."""
        if not self._is_on_city_view():
            self._navigate_to_city()
        return True

    def _level_commander(self, commander_name: str) -> bool:
        """
        Level up a specific commander using XP tomes.

        Args:
            commander_name: Name of commander to level

        Returns:
            True if commander was leveled
        """
        # Find commander in list
        if not self._find_and_select_commander(commander_name):
            self.logger.warning(f"Could not find commander: {commander_name}")
            return False

        time.sleep(1.0)

        # Use XP tomes
        tomes_used = self._use_xp_tomes()

        # Close commander details
        self._close_commander_details()

        return tomes_used > 0

    def _find_and_select_commander(self, commander_name: str) -> bool:
        """
        Find and tap a commander in the commanders list.

        Args:
            commander_name: Name of commander

        Returns:
            True if found and selected
        """
        # Try to find commander by template
        # Each commander should have a template image
        commander_template = f'templates/commanders/{commander_name.lower().replace(" ", "_")}.png'

        screenshot = self.adb.capture_screen_cached()
        commander_location = self.screen.find_template(
            screenshot,
            commander_template,
            confidence=self.config.confidence
        )

        if commander_location:
            # Tap commander
            self.adb.tap(commander_location[0], commander_location[1], randomize=True)
            return True

        # If not found, try scrolling to find them
        # TODO: Implement scrolling through commander list

        return False

    def _use_xp_tomes(self) -> int:
        """
        Use XP tomes on the currently selected commander.

        Returns:
            Number of tomes used
        """
        screenshot = self.adb.capture_screen_cached()

        # Look for level up button / XP button
        level_up_button = self.screen.find_template(
            screenshot,
            'templates/buttons/level_up.png',
            confidence=self.config.confidence
        )

        if level_up_button is None:
            # Commander might be max level
            return 0

        # Tap level up button
        self.adb.tap(level_up_button[0], level_up_button[1], randomize=True)
        time.sleep(1.0)

        tomes_used = 0

        # Use tomes based on configuration
        if self.config.use_large_tomes:
            tomes_used += self._use_tome_type("large")

        if self.config.use_medium_tomes:
            tomes_used += self._use_tome_type("medium")

        if self.config.use_small_tomes:
            tomes_used += self._use_tome_type("small")

        # Confirm level up if needed
        screenshot = self.adb.capture_screen_cached()
        confirm_button = self.screen.find_template(
            screenshot,
            'templates/buttons/confirm.png',
            confidence=0.75
        )

        if confirm_button:
            self.adb.tap(confirm_button[0], confirm_button[1], randomize=True)
            time.sleep(0.5)

        return tomes_used

    def _use_tome_type(self, tome_size: str) -> int:
        """
        Use a specific type of XP tome.

        Args:
            tome_size: "small", "medium", or "large"

        Returns:
            Number of tomes used
        """
        screenshot = self.adb.capture_screen_cached()

        # Find tome button
        tome_template = f'templates/items/xp_tome_{tome_size}.png'
        tome_button = self.screen.find_template(
            screenshot,
            tome_template,
            confidence=self.config.confidence
        )

        if tome_button is None:
            return 0

        # Tap tome button multiple times
        # Usually the game has a slider or + button to use multiple
        tomes_used = 0

        # Look for "use max" or "+" button
        max_button = self.screen.find_template(
            screenshot,
            'templates/buttons/use_max.png',
            confidence=0.75
        )

        if max_button:
            self.adb.tap(max_button[0], max_button[1], randomize=True)
            tomes_used = 1  # Assume at least 1 used
        else:
            # Tap tome button directly
            self.adb.tap(tome_button[0], tome_button[1], randomize=True)
            tomes_used = 1

        time.sleep(0.5)
        return tomes_used

    def _close_commander_details(self):
        """Close commander details screen."""
        screenshot = self.adb.capture_screen_cached()
        close_button = self.screen.find_template(
            screenshot,
            'templates/buttons/close.png',
            confidence=0.75
        )

        if close_button:
            self.adb.tap(close_button[0], close_button[1], randomize=True)
        else:
            self._press_back()

        time.sleep(0.5)

    def _navigate_to_commanders(self) -> bool:
        """Navigate to commanders screen."""
        if not self._is_on_city_view():
            if not self._navigate_to_city():
                return False

        screenshot = self.adb.capture_screen_cached()
        commanders_button = self.screen.find_template(
            screenshot,
            'templates/buttons/commanders.png',
            confidence=self.config.confidence
        )

        if commanders_button is None:
            return False

        self.adb.tap(commanders_button[0], commanders_button[1], randomize=True)
        time.sleep(1.5)
        return True

    def _close_commanders_screen(self):
        """Close commanders screen."""
        screenshot = self.adb.capture_screen_cached()
        close_button = self.screen.find_template(
            screenshot,
            'templates/buttons/close.png',
            confidence=0.75
        )

        if close_button:
            self.adb.tap(close_button[0], close_button[1], randomize=True)
        else:
            self._press_back()

        time.sleep(0.5)

    def _press_back(self):
        """Press back button."""
        screenshot = self.adb.capture_screen_cached()
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
        city_indicator = self.screen.find_template(
            screenshot,
            'templates/screens/city_view.png',
            confidence=0.7
        )
        return city_indicator is not None

    def _navigate_to_city(self) -> bool:
        """Navigate to city view."""
        for _ in range(3):
            screenshot = self.adb.capture_screen_cached()
            back_button = self.screen.find_template(
                screenshot,
                'templates/buttons/back.png',
                confidence=0.75
            )

            if back_button:
                self.adb.tap(back_button[0], back_button[1], randomize=True)
                time.sleep(1.0)

            if self._is_on_city_view():
                return True

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
