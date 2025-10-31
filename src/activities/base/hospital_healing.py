"""
Hospital Healing Activity

Automatically heals wounded troops in the hospital.
Important for recovering troops after combat and barbarian hunting.

Based on: CTroopHealTab from original WhaleBots
String: "Healing Troops"
"""

from typing import Optional
import logging
import time
from dataclasses import dataclass

from ...core.activity import Activity, ActivityConfig
from ...core.adb import ADBConnection
from ...core.screen import ScreenAnalyzer


@dataclass
class HospitalHealingConfig(ActivityConfig):
    """Configuration for hospital healing"""

    # Healing behavior
    heal_all: bool = True              # Heal all wounded troops
    min_wounded_count: int = 10        # Minimum wounded before healing (if not heal_all)

    # Resource management
    check_resources: bool = True       # Check if we have resources to heal
    use_speedups: bool = False         # Use healing speedups (not recommended)

    # Timing
    max_healing_time_hours: int = 24   # Don't heal if healing time > this many hours

    # Detection settings
    confidence: float = 0.75


class HospitalHealingActivity(Activity):
    """
    Automatically heals wounded troops in the hospital.

    Process:
    1. Navigate to city view
    2. Find and tap hospital building
    3. Check wounded troop count (OCR)
    4. If wounded troops exist and conditions met:
       a. Tap "Heal All" button
       b. Confirm healing
    5. Close hospital UI
    6. Verify healing started

    Success Criteria:
    - Healing started successfully
    - OR no wounded troops to heal
    """

    def __init__(self, config: HospitalHealingConfig, adb: ADBConnection, screen: ScreenAnalyzer):
        super().__init__("Hospital Healing", config)
        self.adb = adb
        self.screen = screen
        self.config: HospitalHealingConfig = config

        self.wounded_count = 0
        self.healed = False

    def check_prerequisites(self) -> bool:
        """
        Check if we can heal troops.

        Prerequisites:
        - On city view screen
        - Hospital building accessible
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
        Execute hospital healing activity.

        Process:
        1. Find and click hospital
        2. Check wounded count
        3. Heal troops if conditions met
        4. Close hospital UI
        """
        self.logger.info("Opening hospital...")

        # Find hospital building
        screenshot = self.adb.capture_screen_cached()
        hospital_location = self.screen.find_template(
            screenshot,
            'templates/buildings/hospital.png',
            confidence=self.config.confidence
        )

        if hospital_location is None:
            self.logger.error("Could not find hospital building")
            return False

        # Click hospital
        self.adb.tap(hospital_location[0], hospital_location[1], randomize=True)
        time.sleep(1.5 + (time.time() % 0.5))  # Wait for hospital UI

        # Take new screenshot of hospital UI
        screenshot = self.adb.capture_screen_cached()

        # Check wounded troop count
        self.wounded_count = self._read_wounded_count(screenshot)
        self.logger.info(f"Wounded troops: {self.wounded_count}")

        if self.wounded_count == 0:
            self.logger.info("No wounded troops to heal")
            self._close_hospital_ui()
            return True  # Success - nothing to heal

        # Check if we should heal
        if not self.config.heal_all and self.wounded_count < self.config.min_wounded_count:
            self.logger.info(
                f"Wounded count ({self.wounded_count}) below threshold "
                f"({self.config.min_wounded_count}), skipping"
            )
            self._close_hospital_ui()
            return True

        # Try to heal troops
        self.healed = self._heal_troops(screenshot)

        # Close hospital UI
        self._close_hospital_ui()

        if self.healed:
            self.logger.info(f"Successfully started healing {self.wounded_count} troops")
        else:
            self.logger.warning("Failed to start healing")

        return self.healed

    def verify_completion(self) -> bool:
        """
        Verify healing activity completed successfully.

        Check:
        - Back on city view
        - Healing was initiated (if there were wounded troops)
        """
        # Make sure we're back to city view
        if not self._is_on_city_view():
            self.logger.warning("Not on city view after healing")
            self._navigate_to_city()

        return True

    def _heal_troops(self, screenshot) -> bool:
        """
        Attempt to heal wounded troops.

        Returns:
            True if healing started successfully
        """
        # Look for "Heal All" button
        heal_all_button = self.screen.find_template(
            screenshot,
            'templates/buttons/heal_all.png',
            confidence=self.config.confidence
        )

        if heal_all_button is None:
            # Try alternative button name
            heal_all_button = self.screen.find_template(
                screenshot,
                'templates/buttons/heal.png',
                confidence=self.config.confidence
            )

        if heal_all_button is None:
            self.logger.error("Could not find Heal All button")
            return False

        # Click Heal All button
        self.adb.tap(heal_all_button[0], heal_all_button[1], randomize=True)
        time.sleep(1.0 + (time.time() % 0.5))

        # Check healing time (OCR)
        if self.config.check_resources:
            healing_time = self._read_healing_time()
            if healing_time is not None and healing_time > self.config.max_healing_time_hours:
                self.logger.warning(
                    f"Healing time ({healing_time}h) exceeds maximum "
                    f"({self.config.max_healing_time_hours}h), canceling"
                )
                # Cancel healing
                self._press_back()
                return False

        # Look for confirm button
        screenshot = self.adb.capture_screen_cached()
        confirm_button = self.screen.find_template(
            screenshot,
            'templates/buttons/confirm.png',
            confidence=0.75
        )

        if confirm_button is None:
            # Try "Heal" button as confirm
            confirm_button = self.screen.find_template(
                screenshot,
                'templates/buttons/heal_confirm.png',
                confidence=0.75
            )

        if confirm_button:
            # Click confirm
            self.adb.tap(confirm_button[0], confirm_button[1], randomize=True)
            time.sleep(1.0)
            return True
        else:
            self.logger.warning("Could not find confirm button for healing")
            return False

    def _read_wounded_count(self, screenshot) -> int:
        """
        Read the wounded troop count from hospital UI using OCR.

        The wounded count is usually displayed prominently in the hospital UI.

        Returns:
            Number of wounded troops, or 0 if cannot read
        """
        # Define region where wounded count is displayed
        # Typically in the upper portion of the hospital UI
        # For 1920x1080: around (800, 300, 300, 100)

        try:
            # Extract region with wounded count
            wounded_region = screenshot[300:400, 800:1100]

            # Read text using OCR
            text = self.screen.read_text(wounded_region)

            # Parse number from text
            # Expected format: "Wounded: 1,234" or just "1234"
            count = self._parse_number(text)

            return count

        except Exception as e:
            self.logger.warning(f"Could not read wounded count via OCR: {e}")
            return 0

    def _read_healing_time(self) -> Optional[float]:
        """
        Read the healing time from the confirmation dialog using OCR.

        Returns:
            Healing time in hours, or None if cannot read
        """
        screenshot = self.adb.capture_screen_cached()

        try:
            # Define region where healing time is displayed
            # Usually in a confirmation popup
            time_region = screenshot[400:500, 700:1200]

            # Read text
            text = self.screen.read_text(time_region)

            # Parse time
            # Expected formats: "2h 30m", "45m", "1d 5h"
            hours = self._parse_time_to_hours(text)

            return hours

        except Exception as e:
            self.logger.warning(f"Could not read healing time via OCR: {e}")
            return None

    def _parse_number(self, text: str) -> int:
        """
        Parse a number from OCR text.

        Examples:
        "Wounded: 1,234" -> 1234
        "1234" -> 1234
        "1.2K" -> 1200
        """
        if not text:
            return 0

        # Remove common words and punctuation
        text = text.upper()
        text = text.replace('WOUNDED', '').replace('TROOPS', '').replace(':', '')
        text = text.replace(',', '').replace(' ', '')

        # Handle K (thousands) and M (millions)
        if 'K' in text:
            try:
                num = float(text.replace('K', ''))
                return int(num * 1000)
            except:
                return 0
        elif 'M' in text:
            try:
                num = float(text.replace('M', ''))
                return int(num * 1000000)
            except:
                return 0
        else:
            # Try to extract first number
            import re
            numbers = re.findall(r'\d+', text)
            if numbers:
                return int(numbers[0])

        return 0

    def _parse_time_to_hours(self, text: str) -> float:
        """
        Parse time string to hours.

        Examples:
        "2h 30m" -> 2.5
        "45m" -> 0.75
        "1d 5h" -> 29.0
        "30s" -> 0.008
        """
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

        # Find seconds
        seconds_match = re.search(r'(\d+)s', text, re.IGNORECASE)
        if seconds_match:
            hours += int(seconds_match.group(1)) / 3600.0

        return hours

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

    def _close_hospital_ui(self):
        """Close the hospital UI and return to city view."""
        screenshot = self.adb.capture_screen_cached()
        close_button = self.screen.find_template(
            screenshot,
            'templates/buttons/close.png',
            confidence=0.75
        )

        if close_button:
            self.adb.tap(close_button[0], close_button[1], randomize=True)
        else:
            # Fallback: tap outside UI or press back
            self._press_back()

        time.sleep(0.5)

    def _press_back(self):
        """Press the back button."""
        screenshot = self.adb.capture_screen_cached()
        back_button = self.screen.find_template(
            screenshot,
            'templates/buttons/back.png',
            confidence=0.75
        )

        if back_button:
            self.adb.tap(back_button[0], back_button[1], randomize=True)
            time.sleep(0.5)
