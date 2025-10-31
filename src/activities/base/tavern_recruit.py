"""
Tavern Recruit Activity

Uses silver and gold keys to recruit commanders from the tavern.
Includes free daily recruitment.

Process:
- Navigate to tavern
- Use free daily recruit
- Optionally use silver/gold keys (configured)
- Collect commander sculptures
"""

from typing import Optional
import logging
import time
from dataclasses import dataclass

from ...core.activity import Activity, ActivityConfig
from ...core.adb import ADBConnection
from ...core.screen import ScreenAnalyzer


@dataclass
class TavernRecruitConfig(ActivityConfig):
    """Configuration for tavern recruitment"""

    # Free recruitment
    use_free_recruit: bool = True      # Use free daily recruit

    # Key usage (be careful - keys are valuable!)
    use_silver_keys: bool = False      # Use silver keys
    use_gold_keys: bool = False        # Use gold keys (very valuable!)

    # Limits
    max_silver_keys_per_day: int = 0   # Max silver keys to use
    max_gold_keys_per_day: int = 0     # Max gold keys to use

    # Save keys for events
    save_for_events: bool = True       # Don't use keys unless event active

    # Detection settings
    confidence: float = 0.75


class TavernRecruitActivity(Activity):
    """
    Recruits commanders from the tavern.

    Process:
    1. Navigate to tavern
    2. Use free daily recruit if available
    3. Use silver/gold keys if configured
    4. Collect sculptures
    5. Close and return

    Success Criteria:
    - Used free recruit OR used keys
    - OR no recruits available
    """

    def __init__(self, config: TavernRecruitConfig, adb: ADBConnection, screen: ScreenAnalyzer):
        super().__init__("Tavern Recruit", config)
        self.adb = adb
        self.screen = screen
        self.config: TavernRecruitConfig = config

        self.recruits_done = 0

    def check_prerequisites(self) -> bool:
        """
        Check if we can recruit from tavern.

        Prerequisites:
        - At least one recruit method enabled
        """
        if not (self.config.use_free_recruit or
                self.config.use_silver_keys or
                self.config.use_gold_keys):
            self.logger.warning("No recruit methods enabled")
            return False

        return True

    def execute(self) -> bool:
        """
        Execute tavern recruitment.

        Process:
        1. Navigate to tavern
        2. Use free recruit
        3. Use keys if configured
        4. Close and return
        """
        self.logger.info("Recruiting from tavern...")

        # Navigate to tavern
        if not self._navigate_to_tavern():
            self.logger.error("Failed to navigate to tavern")
            return False

        time.sleep(1.0)

        self.recruits_done = 0

        # Use free recruit
        if self.config.use_free_recruit:
            if self._use_free_recruit():
                self.recruits_done += 1

        # Use silver keys
        if self.config.use_silver_keys and self.config.max_silver_keys_per_day > 0:
            if not self.config.save_for_events or self._is_recruit_event_active():
                silver_used = self._use_silver_keys(self.config.max_silver_keys_per_day)
                self.recruits_done += silver_used

        # Use gold keys
        if self.config.use_gold_keys and self.config.max_gold_keys_per_day > 0:
            if not self.config.save_for_events or self._is_recruit_event_active():
                gold_used = self._use_gold_keys(self.config.max_gold_keys_per_day)
                self.recruits_done += gold_used

        # Close tavern
        self._close_tavern()

        # Navigate back to city
        self._navigate_to_city()

        if self.recruits_done > 0:
            self.logger.info(f"Completed {self.recruits_done} tavern recruits")
            return True
        else:
            self.logger.info("No tavern recruits available")
            return True

    def verify_completion(self) -> bool:
        """Verify tavern recruitment completed."""
        if not self._is_on_city_view():
            self._navigate_to_city()
        return True

    def _use_free_recruit(self) -> bool:
        """Use free daily recruit."""
        screenshot = self.adb.capture_screen_cached()

        # Look for free recruit button
        free_button = self.screen.find_template(
            screenshot,
            'templates/buttons/free_recruit.png',
            confidence=self.config.confidence
        )

        if free_button is None:
            self.logger.debug("Free recruit not available")
            return False

        # Tap free recruit
        self.adb.tap(free_button[0], free_button[1], randomize=True)
        time.sleep(2.0)

        # Handle animation/result
        self._handle_recruit_animation()

        return True

    def _use_silver_keys(self, max_keys: int) -> int:
        """
        Use silver keys to recruit.

        Args:
            max_keys: Maximum number of keys to use

        Returns:
            Number of recruits done
        """
        used = 0

        for i in range(max_keys):
            screenshot = self.adb.capture_screen_cached()

            # Find silver recruit button
            silver_button = self.screen.find_template(
                screenshot,
                'templates/buttons/silver_recruit.png',
                confidence=self.config.confidence
            )

            if silver_button is None:
                break

            # Tap silver recruit
            self.adb.tap(silver_button[0], silver_button[1], randomize=True)
            time.sleep(2.0)

            # Handle animation
            self._handle_recruit_animation()

            used += 1

            # Small delay
            time.sleep(0.5)

        return used

    def _use_gold_keys(self, max_keys: int) -> int:
        """
        Use gold keys to recruit.

        Args:
            max_keys: Maximum number of keys to use

        Returns:
            Number of recruits done
        """
        used = 0

        for i in range(max_keys):
            screenshot = self.adb.capture_screen_cached()

            # Find gold recruit button
            gold_button = self.screen.find_template(
                screenshot,
                'templates/buttons/gold_recruit.png',
                confidence=self.config.confidence
            )

            if gold_button is None:
                break

            # Tap gold recruit
            self.adb.tap(gold_button[0], gold_button[1], randomize=True)
            time.sleep(3.0)  # Gold recruit has longer animation

            # Handle animation
            self._handle_recruit_animation()

            used += 1

            # Small delay
            time.sleep(0.5)

        return used

    def _handle_recruit_animation(self):
        """Handle recruitment animation and result screen."""
        # Wait for animation to complete
        time.sleep(3.0)

        # Tap to skip/dismiss animation
        self.adb.tap(960, 540, randomize=True)
        time.sleep(1.0)

        # Tap again to dismiss result
        self.adb.tap(960, 540, randomize=True)
        time.sleep(0.5)

    def _is_recruit_event_active(self) -> bool:
        """
        Check if a recruitment event is currently active.

        Returns:
            True if event active (recommended to use keys)
        """
        # TODO: Implement event detection
        # For now, return False (don't use keys unless explicitly configured)
        return False

    def _navigate_to_tavern(self) -> bool:
        """Navigate to tavern."""
        if not self._is_on_city_view():
            if not self._navigate_to_city():
                return False

        screenshot = self.adb.capture_screen_cached()
        tavern_button = self.screen.find_template(
            screenshot,
            'templates/buttons/tavern.png',
            confidence=self.config.confidence
        )

        if tavern_button is None:
            # Try finding tavern building
            tavern_building = self.screen.find_template(
                screenshot,
                'templates/buildings/tavern.png',
                confidence=self.config.confidence
            )
            if tavern_building:
                tavern_button = tavern_building

        if tavern_button is None:
            return False

        self.adb.tap(tavern_button[0], tavern_button[1], randomize=True)
        time.sleep(1.5)
        return True

    def _close_tavern(self):
        """Close tavern screen."""
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
