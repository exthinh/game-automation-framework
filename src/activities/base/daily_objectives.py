"""
Daily Objectives Activity

Collects completed daily objective rewards.
Daily objectives are tasks like "Kill 10 barbarians", "Gather 100K resources", etc.

This activity navigates to the objectives screen and collects all available rewards.
"""

from typing import List, Tuple
import logging
import time
from dataclasses import dataclass

from ...core.activity import Activity, ActivityConfig
from ...core.adb import ADBConnection
from ...core.screen import ScreenAnalyzer


@dataclass
class DailyObjectivesConfig(ActivityConfig):
    """Configuration for daily objectives collection"""

    # Collection settings
    collect_daily_chest: bool = True   # Collect daily activity chest
    collect_individual: bool = True    # Collect individual objectives
    max_objectives: int = 20           # Max objectives to collect per run

    # Detection settings
    confidence: float = 0.75


class DailyObjectivesActivity(Activity):
    """
    Collects completed daily objective rewards.

    Process:
    1. Navigate to objectives/quests screen
    2. Find completed objectives (checkmark indicators)
    3. Collect each objective's rewards
    4. Collect daily chest if available
    5. Close and return to city

    Success Criteria:
    - Collected at least one objective reward
    - OR no objectives ready to collect
    """

    def __init__(self, config: DailyObjectivesConfig, adb: ADBConnection, screen: ScreenAnalyzer):
        super().__init__("Daily Objectives", config)
        self.adb = adb
        self.screen = screen
        self.config: DailyObjectivesConfig = config

        self.objectives_collected = 0
        self.chest_collected = False

    def check_prerequisites(self) -> bool:
        """
        Check if we can collect objectives.

        Prerequisites:
        - Game is running
        """
        return True

    def execute(self) -> bool:
        """
        Execute daily objectives collection.

        Process:
        1. Navigate to objectives screen
        2. Collect individual objectives
        3. Collect daily chest
        4. Close and return
        """
        self.logger.info("Collecting daily objectives...")

        # Navigate to objectives screen
        if not self._navigate_to_objectives():
            self.logger.error("Failed to navigate to objectives screen")
            return False

        time.sleep(1.0)

        # Collect individual objectives
        if self.config.collect_individual:
            self.objectives_collected = self._collect_objectives()

        # Collect daily chest
        if self.config.collect_daily_chest:
            self.chest_collected = self._collect_daily_chest()

        # Close objectives screen
        self._close_objectives_screen()

        # Navigate back to city
        self._navigate_to_city()

        # Summary
        if self.objectives_collected > 0 or self.chest_collected:
            self.logger.info(
                f"Collected {self.objectives_collected} objectives, "
                f"chest: {self.chest_collected}"
            )
            return True
        else:
            self.logger.info("No objectives ready to collect")
            return True  # Not an error

    def verify_completion(self) -> bool:
        """Verify objectives collection completed."""
        if not self._is_on_city_view():
            self._navigate_to_city()
        return True

    def _collect_objectives(self) -> int:
        """
        Collect all completed individual objectives.

        Returns:
            Number of objectives collected
        """
        collected = 0

        for i in range(self.config.max_objectives):
            screenshot = self.adb.capture_screen_cached()

            # Look for completed objective indicator (checkmark icon)
            checkmark = self.screen.find_template(
                screenshot,
                'templates/icons/objective_complete.png',
                confidence=self.config.confidence
            )

            if checkmark is None:
                # Try alternative template
                checkmark = self.screen.find_template(
                    screenshot,
                    'templates/icons/checkmark_complete.png',
                    confidence=self.config.confidence
                )

            if checkmark is None:
                # No more completed objectives
                break

            # Look for collect button near the checkmark
            # Usually the collect button is to the right of the objective
            collect_button = self._find_collect_button_near(screenshot, checkmark)

            if collect_button:
                # Tap collect button
                self.adb.tap(collect_button[0], collect_button[1], randomize=True)
                time.sleep(0.5 + (time.time() % 0.3))

                collected += 1

                # Handle reward popup
                self._close_reward_popup()

            else:
                # Try tapping the checkmark itself
                self.adb.tap(checkmark[0], checkmark[1], randomize=True)
                time.sleep(0.5)
                collected += 1
                self._close_reward_popup()

            # Small delay between collections
            time.sleep(0.3)

        return collected

    def _collect_daily_chest(self) -> bool:
        """
        Collect the daily activity chest (if available).

        The daily chest requires completing a certain number of objectives.

        Returns:
            True if chest was collected
        """
        screenshot = self.adb.capture_screen_cached()

        # Look for daily chest icon/button
        chest_button = self.screen.find_template(
            screenshot,
            'templates/buttons/daily_chest.png',
            confidence=self.config.confidence
        )

        if chest_button is None:
            # Try alternative template
            chest_button = self.screen.find_template(
                screenshot,
                'templates/icons/activity_chest.png',
                confidence=self.config.confidence
            )

        if chest_button is None:
            self.logger.debug("Daily chest not available")
            return False

        # Tap chest
        self.adb.tap(chest_button[0], chest_button[1], randomize=True)
        time.sleep(1.0)

        # Handle reward popup
        self._close_reward_popup()

        return True

    def _find_collect_button_near(
        self,
        screenshot,
        location: Tuple[int, int],
        search_radius: int = 200
    ) -> Optional[Tuple[int, int]]:
        """
        Find a collect button near a given location.

        Args:
            screenshot: Screenshot image
            location: (x, y) tuple of reference location
            search_radius: How far to search from location

        Returns:
            (x, y) of collect button or None
        """
        x, y = location

        # Define search region (to the right of the checkmark)
        # Most collect buttons are to the right of the objective text
        search_region = screenshot[
            max(0, y - 50):min(screenshot.shape[0], y + 50),
            x:min(screenshot.shape[1], x + search_radius)
        ]

        # Look for collect button template in this region
        collect_button = self.screen.find_template(
            search_region,
            'templates/buttons/collect_objective.png',
            confidence=self.config.confidence
        )

        if collect_button:
            # Adjust coordinates back to full screenshot
            return (collect_button[0] + x, collect_button[1] + (y - 50))

        # Try generic collect button
        collect_button = self.screen.find_template(
            search_region,
            'templates/buttons/collect.png',
            confidence=self.config.confidence
        )

        if collect_button:
            return (collect_button[0] + x, collect_button[1] + (y - 50))

        return None

    def _close_reward_popup(self):
        """Close reward popup that may appear after collecting."""
        time.sleep(0.5)

        screenshot = self.adb.capture_screen_cached()

        # Look for close button
        close_button = self.screen.find_template(
            screenshot,
            'templates/buttons/close.png',
            confidence=0.75
        )

        if close_button:
            self.adb.tap(close_button[0], close_button[1], randomize=True)
            time.sleep(0.3)
        else:
            # Try tapping in middle of screen to close popup
            self.adb.tap(960, 540, randomize=True)
            time.sleep(0.3)

    def _navigate_to_objectives(self) -> bool:
        """Navigate to objectives/quests screen."""
        # Ensure on city view first
        if not self._is_on_city_view():
            if not self._navigate_to_city():
                return False

        # Find and tap objectives button
        # Usually a quest icon or objectives icon
        screenshot = self.adb.capture_screen_cached()
        objectives_button = self.screen.find_template(
            screenshot,
            'templates/buttons/objectives.png',
            confidence=self.config.confidence
        )

        if objectives_button is None:
            # Try alternative names
            objectives_button = self.screen.find_template(
                screenshot,
                'templates/buttons/quests.png',
                confidence=self.config.confidence
            )

        if objectives_button is None:
            self.logger.error("Could not find objectives button")
            return False

        # Tap objectives button
        self.adb.tap(objectives_button[0], objectives_button[1], randomize=True)
        time.sleep(1.5 + (time.time() % 0.5))

        # Verify we're on objectives screen
        screenshot = self.adb.capture_screen_cached()
        objectives_screen = self.screen.find_template(
            screenshot,
            'templates/screens/objectives.png',
            confidence=0.7
        )

        return objectives_screen is not None

    def _close_objectives_screen(self):
        """Close the objectives screen."""
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
        """Check if currently on city view screen."""
        screenshot = self.adb.capture_screen_cached()
        city_indicator = self.screen.find_template(
            screenshot,
            'templates/screens/city_view.png',
            confidence=0.7
        )
        return city_indicator is not None

    def _navigate_to_city(self) -> bool:
        """Navigate back to city view."""
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

        # Try home button
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
