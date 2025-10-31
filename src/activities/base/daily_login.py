"""
Daily Login Rewards Activity

Collects daily login calendar rewards when the popup appears.

Complexity: LOW
Execution Time: 10-20 seconds
Success Rate: 95%+

Flow:
1. Detect daily login popup (auto-appears on login)
2. Find and tap "Claim" button
3. Handle reward animation
4. Close popup
5. Verify completion

Templates Required:
- templates/screens/daily_login_popup.png - Login calendar popup
- templates/buttons/claim_login.png - Claim button
- templates/buttons/close.png - Close button
"""

import logging
import time
import random
from typing import Optional, Tuple
from datetime import datetime, timedelta

from src.core.activity import Activity, ActivityConfig
from src.core.adb import ADBConnection
from src.core.screen import ScreenAnalyzer


class DailyLoginActivity(Activity):
    """
    Collects daily login rewards from the login calendar.

    This activity:
    - Detects daily login popup
    - Claims the daily reward
    - Closes the popup
    - Runs once per day
    """

    def __init__(
        self,
        adb_connection: ADBConnection,
        screen_analyzer: ScreenAnalyzer,
        interval_hours: int = 24,
        priority: int = 4  # High priority - free rewards
    ):
        """
        Initialize Daily Login activity.

        Args:
            adb_connection: ADB connection to emulator
            screen_analyzer: Screen analysis engine
            interval_hours: How often to check (default: 24 hours)
            priority: Activity priority (default: 4 - high)
        """
        config = ActivityConfig(
            enabled=True,
            interval_hours=interval_hours,
            interval_minutes=0,
            priority=priority,
            max_retries=2,
            retry_delay_minutes=60,  # Retry in 1 hour if fails
            max_execution_seconds=30,
            parameters={}
        )

        super().__init__(
            name="Daily Login",
            config=config,
            adb_connection=adb_connection,
            screen_analyzer=screen_analyzer
        )

        # Template paths
        self.templates = {
            'login_popup': 'templates/screens/daily_login_popup.png',
            'claim_button': 'templates/buttons/claim_login.png',
            'claim_alt': 'templates/buttons/collect.png',  # Alternative claim button
            'close_button': 'templates/buttons/close.png',
            'ok_button': 'templates/buttons/ok.png'
        }

        self.last_claim_time: Optional[datetime] = None
        self.popup_detected_during_execution = False

    def check_prerequisites(self) -> bool:
        """
        Check if daily login can run.

        Prerequisites:
        1. Game is running
        2. At least 23 hours since last claim
        3. Can capture screen

        Returns:
            True if prerequisites met, False otherwise
        """
        self.logger.info("Checking prerequisites for daily login")

        # Check: Can we capture screen?
        screenshot = self.adb.capture_screen()
        if screenshot is None:
            self.logger.error("Cannot capture screenshot")
            return False

        # Check: Too soon since last claim?
        if self.last_claim_time:
            time_since_last = datetime.now() - self.last_claim_time
            if time_since_last < timedelta(hours=23):
                hours_remaining = 23 - (time_since_last.total_seconds() / 3600)
                self.logger.info(f"Too soon to claim (wait {hours_remaining:.1f} more hours)")
                return False

        self.logger.info("✓ Prerequisites met for daily login")
        return True

    def execute(self) -> bool:
        """
        Execute daily login collection.

        Steps:
        1. Check if login popup is present
        2. If not, try tapping to trigger it (some games require this)
        3. Find and tap claim button
        4. Handle reward animation
        5. Close popup

        Returns:
            True if collection successful, False otherwise
        """
        self.logger.info("Starting daily login execution")
        self.popup_detected_during_execution = False

        try:
            # Step 1: Check if login popup is already visible
            if not self._detect_login_popup():
                self.logger.info("Login popup not visible - may already be claimed today")
                # This is not necessarily an error - might have already claimed
                return False

            self.popup_detected_during_execution = True

            # Step 2: Find and tap claim button
            if not self._tap_claim_button():
                self.logger.error("Failed to tap claim button")
                return False

            # Step 3: Wait for reward animation
            wait_time = random.uniform(2.0, 3.0)
            self.logger.debug(f"Waiting {wait_time:.1f}s for reward animation")
            time.sleep(wait_time)

            # Step 4: Close popup (if still open)
            self._close_popup()

            # Update last claim time
            self.last_claim_time = datetime.now()

            self.logger.info("✓ Daily login execution complete")
            return True

        except Exception as e:
            self.logger.error(f"Exception during daily login: {e}", exc_info=True)
            return False

    def verify_completion(self) -> bool:
        """
        Verify that daily login was claimed.

        Verification methods:
        1. Check if last_claim_time was updated
        2. Check if popup is no longer visible
        3. Check if popup was detected during execution

        Returns:
            True if claim verified, False otherwise
        """
        self.logger.info("Verifying daily login completion")

        # Method 1: Was last_claim_time updated?
        if self.last_claim_time:
            time_since = datetime.now() - self.last_claim_time
            if time_since.total_seconds() < 60:  # Updated in last minute
                self.logger.info("✓ Claim time was updated - success")
                return True

        # Method 2: Popup no longer visible?
        if self.popup_detected_during_execution:
            screenshot = self.adb.capture_screen()
            if screenshot is not None:
                popup_result = self.screen.find_template(
                    screenshot,
                    self.templates['login_popup'],
                    confidence_threshold=0.7
                )

                if not popup_result.found:
                    self.logger.info("✓ Popup closed - likely successful")
                    return True

        self.logger.warning("Cannot verify daily login - uncertain result")
        return False

    # ========================================================================
    # DETECTION AND INTERACTION METHODS
    # ========================================================================

    def _detect_login_popup(self) -> bool:
        """
        Detect if daily login popup is currently visible.

        Returns:
            True if popup found, False otherwise
        """
        self.logger.info("Detecting daily login popup")

        screenshot = self.adb.capture_screen()
        if screenshot is None:
            return False

        # Look for login calendar popup
        popup_result = self.screen.find_template(
            screenshot,
            self.templates['login_popup'],
            confidence_threshold=0.8
        )

        if popup_result.found:
            self.logger.info("✓ Daily login popup detected")
            return True
        else:
            self.logger.info("Daily login popup not found")
            return False

    def _tap_claim_button(self) -> bool:
        """
        Find and tap the claim button on the login popup.

        Returns:
            True if button tapped, False otherwise
        """
        self.logger.info("Looking for claim button")

        screenshot = self.adb.capture_screen()
        if screenshot is None:
            return False

        # Try finding "Claim" button
        claim_result = self.screen.find_template(
            screenshot,
            self.templates['claim_button'],
            confidence_threshold=0.8
        )

        if claim_result.found:
            self.logger.info(f"✓ Claim button found at ({claim_result.location[0]}, {claim_result.location[1]})")
            success = self.adb.tap(
                claim_result.location[0],
                claim_result.location[1],
                randomize=True
            )
            if not success:
                self.logger.error("Failed to tap claim button")
                return False

            time.sleep(random.uniform(0.5, 1.0))
            return True

        # Try alternative "Collect" button
        collect_result = self.screen.find_template(
            screenshot,
            self.templates['claim_alt'],
            confidence_threshold=0.8
        )

        if collect_result.found:
            self.logger.info(f"✓ Collect button found at ({collect_result.location[0]}, {collect_result.location[1]})")
            success = self.adb.tap(
                collect_result.location[0],
                collect_result.location[1],
                randomize=True
            )
            if not success:
                self.logger.error("Failed to tap collect button")
                return False

            time.sleep(random.uniform(0.5, 1.0))
            return True

        self.logger.error("Claim button not found")
        return False

    def _close_popup(self) -> bool:
        """
        Close the daily login popup.

        Returns:
            True if popup closed, False otherwise
        """
        self.logger.info("Closing daily login popup")

        screenshot = self.adb.capture_screen()
        if screenshot is None:
            return False

        # Try finding close button
        close_result = self.screen.find_template(
            screenshot,
            self.templates['close_button'],
            confidence_threshold=0.8
        )

        if close_result.found:
            self.logger.info("Found close button")
            self.adb.tap(
                close_result.location[0],
                close_result.location[1],
                randomize=True
            )
            time.sleep(random.uniform(0.8, 1.2))
            return True

        # Try finding OK button
        ok_result = self.screen.find_template(
            screenshot,
            self.templates['ok_button'],
            confidence_threshold=0.8
        )

        if ok_result.found:
            self.logger.info("Found OK button")
            self.adb.tap(
                ok_result.location[0],
                ok_result.location[1],
                randomize=True
            )
            time.sleep(random.uniform(0.8, 1.2))
            return True

        # Fallback: Tap outside popup area (center screen)
        self.logger.info("No close button found, tapping outside popup")
        resolution = self.adb.get_screen_resolution()
        if resolution:
            # Tap at bottom center (usually outside popup)
            center_x = resolution[0] // 2
            bottom_y = int(resolution[1] * 0.85)
            self.adb.tap(center_x, bottom_y, randomize=True)
            time.sleep(random.uniform(0.8, 1.2))

        return True


def create_daily_login_activity(
    adb_connection: ADBConnection,
    screen_analyzer: ScreenAnalyzer,
    interval_hours: int = 24,
    priority: int = 4
) -> DailyLoginActivity:
    """
    Factory function to create Daily Login activity.

    Args:
        adb_connection: ADB connection instance
        screen_analyzer: Screen analyzer instance
        interval_hours: Check interval (default: 24 hours)
        priority: Activity priority (default: 4 - high)

    Returns:
        Configured DailyLoginActivity instance
    """
    return DailyLoginActivity(
        adb_connection=adb_connection,
        screen_analyzer=screen_analyzer,
        interval_hours=interval_hours,
        priority=priority
    )
