"""
Alliance Gifts Activity

Collects alliance gift chests and opens them for rewards.
Alliance gifts are given by alliance members and contain resources/items.

Based on: CAllianceGiftTab from original WhaleBots
Configuration Key: utl_alliancegift
"""

from typing import Optional
import logging
import time
from dataclasses import dataclass

from ...core.activity import Activity, ActivityConfig
from ...core.adb import ADBConnection
from ...core.screen import ScreenAnalyzer


@dataclass
class AllianceGiftsConfig(ActivityConfig):
    """Configuration for alliance gifts collection"""

    # Collection settings
    collect_all_gifts: bool = True     # Collect all available gifts
    max_gifts_per_run: int = 50        # Maximum gifts to collect per run

    # Navigation
    confidence: float = 0.75


class AllianceGiftsActivity(Activity):
    """
    Collects alliance gift chests.

    Process:
    1. Navigate to alliance screen
    2. Find and tap gift icon
    3. Collect all available gifts
    4. Close gift screen
    5. Return to city

    Success Criteria:
    - Collected at least one gift
    - OR no gifts available
    """

    def __init__(self, config: AllianceGiftsConfig, adb: ADBConnection, screen: ScreenAnalyzer):
        super().__init__("Alliance Gifts", config)
        self.adb = adb
        self.screen = screen
        self.config: AllianceGiftsConfig = config

        self.gifts_collected = 0

    def check_prerequisites(self) -> bool:
        """
        Check if we can collect alliance gifts.

        Prerequisites:
        - Game is running
        - Can navigate to alliance screen
        """
        return True

    def execute(self) -> bool:
        """
        Execute alliance gifts collection.

        Process:
        1. Navigate to alliance screen
        2. Open gifts section
        3. Collect all gifts
        4. Close and return
        """
        self.logger.info("Collecting alliance gifts...")

        # Navigate to alliance screen
        if not self._navigate_to_alliance():
            self.logger.error("Failed to navigate to alliance screen")
            return False

        time.sleep(1.0)

        # Find and tap gift icon
        screenshot = self.adb.capture_screen_cached()
        gift_icon = self.screen.find_template(
            screenshot,
            'templates/buttons/alliance_gift.png',
            confidence=self.config.confidence
        )

        if gift_icon is None:
            # Try alternative template
            gift_icon = self.screen.find_template(
                screenshot,
                'templates/icons/gift.png',
                confidence=self.config.confidence
            )

        if gift_icon is None:
            self.logger.warning("Could not find gift icon in alliance screen")
            self._navigate_to_city()
            return False

        # Tap gift icon
        self.adb.tap(gift_icon[0], gift_icon[1], randomize=True)
        time.sleep(1.5 + (time.time() % 0.5))

        # Collect gifts
        self.gifts_collected = self._collect_gifts()

        # Close gift screen
        self._close_gift_screen()

        # Navigate back to city
        self._navigate_to_city()

        if self.gifts_collected > 0:
            self.logger.info(f"Collected {self.gifts_collected} alliance gifts")
            return True
        else:
            self.logger.info("No alliance gifts available")
            return True  # Not an error, just nothing to collect

    def verify_completion(self) -> bool:
        """
        Verify gift collection completed.

        Check:
        - Back on city view
        """
        if not self._is_on_city_view():
            self._navigate_to_city()

        return True

    def _collect_gifts(self) -> int:
        """
        Collect all available gifts.

        Returns:
            Number of gifts collected
        """
        collected = 0

        # Look for "Collect All" button
        screenshot = self.adb.capture_screen_cached()
        collect_all_button = self.screen.find_template(
            screenshot,
            'templates/buttons/collect_all_gifts.png',
            confidence=self.config.confidence
        )

        if collect_all_button:
            # Collect all at once
            self.adb.tap(collect_all_button[0], collect_all_button[1], randomize=True)
            time.sleep(1.5)

            # Try to detect how many were collected (OCR)
            # For now, assume successful if button was found
            collected = 1  # At least 1

        else:
            # Collect individual gifts
            for i in range(self.config.max_gifts_per_run):
                screenshot = self.adb.capture_screen_cached()

                # Look for individual collect button
                collect_button = self.screen.find_template(
                    screenshot,
                    'templates/buttons/collect_gift.png',
                    confidence=self.config.confidence
                )

                if collect_button is None:
                    # No more gifts
                    break

                # Tap collect button
                self.adb.tap(collect_button[0], collect_button[1], randomize=True)
                time.sleep(0.5 + (time.time() % 0.3))

                collected += 1

                # Handle reward popup if it appears
                self._close_reward_popup()

        return collected

    def _close_reward_popup(self):
        """Close reward popup that may appear after collecting."""
        time.sleep(0.5)

        screenshot = self.adb.capture_screen_cached()
        close_button = self.screen.find_template(
            screenshot,
            'templates/buttons/close.png',
            confidence=0.75
        )

        if close_button:
            self.adb.tap(close_button[0], close_button[1], randomize=True)
            time.sleep(0.3)

    def _close_gift_screen(self):
        """Close the gift screen."""
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

    def _navigate_to_alliance(self) -> bool:
        """Navigate to alliance screen."""
        # Ensure on city view first
        if not self._is_on_city_view():
            if not self._navigate_to_city():
                return False

        # Find and tap alliance button
        screenshot = self.adb.capture_screen_cached()
        alliance_button = self.screen.find_template(
            screenshot,
            'templates/buttons/alliance.png',
            confidence=self.config.confidence
        )

        if alliance_button is None:
            self.logger.error("Could not find alliance button")
            return False

        # Tap alliance button
        self.adb.tap(alliance_button[0], alliance_button[1], randomize=True)
        time.sleep(1.5 + (time.time() % 0.5))

        # Verify we're on alliance screen
        screenshot = self.adb.capture_screen_cached()
        alliance_screen = self.screen.find_template(
            screenshot,
            'templates/screens/alliance.png',
            confidence=0.7
        )

        return alliance_screen is not None

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
