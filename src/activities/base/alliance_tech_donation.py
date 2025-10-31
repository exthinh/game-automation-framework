"""
Alliance Tech Donation Activity

Donates resources to alliance technology research.
Helps alliance progress and earns personal contribution points.

Based on: CAllianceDonationTab from original WhaleBots
Configuration Key: utl_alliancedonation
"""

from typing import Optional
import logging
import time
from dataclasses import dataclass

from ...core.activity import Activity, ActivityConfig
from ...core.adb import ADBConnection
from ...core.screen import ScreenAnalyzer


@dataclass
class AllianceTechDonationConfig(ActivityConfig):
    """Configuration for alliance tech donation"""

    # Donation settings
    donate_max: bool = False           # Donate maximum allowed (risky if low resources)
    donation_amount: int = 10000       # Amount to donate per tech
    max_donations_per_run: int = 5     # Max donations per activity run

    # Resource limits (don't donate if below these)
    min_food: int = 500000
    min_wood: int = 500000

    # Tech priorities (which techs to donate to)
    prioritize_economy: bool = True
    prioritize_military: bool = True

    # Detection settings
    confidence: float = 0.75


class AllianceTechDonationActivity(Activity):
    """
    Donates resources to alliance technology research.

    Process:
    1. Navigate to alliance screen
    2. Open alliance tech/science tab
    3. Find active research
    4. Donate configured amount
    5. Close and return

    Success Criteria:
    - Donated to at least one tech
    - OR no techs available for donation
    """

    def __init__(self, config: AllianceTechDonationConfig, adb: ADBConnection, screen: ScreenAnalyzer):
        super().__init__("Alliance Tech Donation", config)
        self.adb = adb
        self.screen = screen
        self.config: AllianceTechDonationConfig = config

        self.donations_made = 0

    def check_prerequisites(self) -> bool:
        """
        Check if we can donate to alliance tech.

        Prerequisites:
        - Have sufficient resources
        - Game is running
        """
        # Check resources
        if not self._check_resources():
            self.logger.info("Insufficient resources for donation")
            return False

        return True

    def execute(self) -> bool:
        """
        Execute alliance tech donation.

        Process:
        1. Navigate to alliance screen
        2. Open tech/science tab
        3. Donate to active research
        4. Close and return
        """
        self.logger.info("Donating to alliance technology...")

        # Navigate to alliance screen
        if not self._navigate_to_alliance():
            self.logger.error("Failed to navigate to alliance screen")
            return False

        time.sleep(1.0)

        # Navigate to tech tab
        if not self._navigate_to_tech_tab():
            self.logger.error("Failed to navigate to tech tab")
            self._navigate_to_city()
            return False

        time.sleep(1.0)

        # Make donations
        self.donations_made = self._make_donations()

        # Close tech screen
        self._close_tech_screen()

        # Navigate back to city
        self._navigate_to_city()

        if self.donations_made > 0:
            self.logger.info(f"Made {self.donations_made} alliance tech donations")
            return True
        else:
            self.logger.info("No techs available for donation")
            return True  # Not an error

    def verify_completion(self) -> bool:
        """Verify donation completed."""
        if not self._is_on_city_view():
            self._navigate_to_city()
        return True

    def _make_donations(self) -> int:
        """
        Make donations to active alliance research.

        Returns:
            Number of donations made
        """
        donations = 0

        for i in range(self.config.max_donations_per_run):
            screenshot = self.adb.capture_screen_cached()

            # Look for donate button
            donate_button = self.screen.find_template(
                screenshot,
                'templates/buttons/donate.png',
                confidence=self.config.confidence
            )

            if donate_button is None:
                # Try alternative template
                donate_button = self.screen.find_template(
                    screenshot,
                    'templates/buttons/alliance_donate.png',
                    confidence=self.config.confidence
                )

            if donate_button is None:
                # No more techs to donate to
                break

            # Tap donate button
            self.adb.tap(donate_button[0], donate_button[1], randomize=True)
            time.sleep(1.0 + (time.time() % 0.5))

            # Enter donation amount (if needed)
            if not self.config.donate_max:
                # TODO: Implement amount entry
                # For now, just use default amount
                pass

            # Confirm donation
            screenshot = self.adb.capture_screen_cached()
            confirm_button = self.screen.find_template(
                screenshot,
                'templates/buttons/confirm.png',
                confidence=0.75
            )

            if confirm_button:
                self.adb.tap(confirm_button[0], confirm_button[1], randomize=True)
                time.sleep(0.5)
                donations += 1
            else:
                # Couldn't confirm, cancel
                self._press_back()

            # Small delay between donations
            time.sleep(0.5)

            # Re-check resources after each donation
            if not self._check_resources():
                self.logger.info("Resources depleted, stopping donations")
                break

        return donations

    def _check_resources(self) -> bool:
        """Check if we have sufficient resources."""
        # For now, simplified check
        # TODO: Implement OCR resource reading
        return True

    def _navigate_to_alliance(self) -> bool:
        """Navigate to alliance screen."""
        if not self._is_on_city_view():
            if not self._navigate_to_city():
                return False

        screenshot = self.adb.capture_screen_cached()
        alliance_button = self.screen.find_template(
            screenshot,
            'templates/buttons/alliance.png',
            confidence=self.config.confidence
        )

        if alliance_button is None:
            return False

        self.adb.tap(alliance_button[0], alliance_button[1], randomize=True)
        time.sleep(1.5)
        return True

    def _navigate_to_tech_tab(self) -> bool:
        """Navigate to alliance tech/science tab."""
        screenshot = self.adb.capture_screen_cached()

        # Look for tech tab button
        tech_tab = self.screen.find_template(
            screenshot,
            'templates/buttons/alliance_tech.png',
            confidence=self.config.confidence
        )

        if tech_tab is None:
            # Try alternative names
            tech_tab = self.screen.find_template(
                screenshot,
                'templates/buttons/alliance_science.png',
                confidence=self.config.confidence
            )

        if tech_tab is None:
            return False

        self.adb.tap(tech_tab[0], tech_tab[1], randomize=True)
        time.sleep(1.0)
        return True

    def _close_tech_screen(self):
        """Close the tech screen."""
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
