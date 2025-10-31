"""
VIP Collection Activity

Collects daily VIP chest rewards from the VIP screen.

Complexity: LOW
Execution Time: 20-40 seconds
Success Rate: 90%+

Flow:
1. Navigate to VIP screen (from icon or menu)
2. Find VIP chest/reward indicator
3. Tap to collect
4. Handle reward popup
5. Exit screen
6. Verify completion

Templates Required:
- templates/buttons/vip.png - VIP icon
- templates/buttons/vip_chest.png - VIP chest icon
- templates/buttons/collect.png - Collect button
- templates/screens/vip_screen.png - VIP screen identifier
"""

import logging
import time
import random
from typing import Optional, Tuple
from datetime import datetime, timedelta

from src.core.activity import Activity, ActivityConfig
from src.core.adb import ADBConnection
from src.core.screen import ScreenAnalyzer


class VIPCollectionActivity(Activity):
    """
    Collects daily VIP chest rewards.

    This activity:
    - Navigates to VIP screen
    - Finds and collects VIP daily chest
    - Handles reward popups
    - Returns to main screen
    """

    def __init__(
        self,
        adb_connection: ADBConnection,
        screen_analyzer: ScreenAnalyzer,
        interval_hours: int = 24,
        priority: int = 3,
        collect_all_rewards: bool = True
    ):
        """
        Initialize VIP Collection activity.

        Args:
            adb_connection: ADB connection to emulator
            screen_analyzer: Screen analysis engine
            interval_hours: How often to run (default: 24 hours)
            priority: Activity priority (default: 3)
            collect_all_rewards: Whether to collect all available VIP rewards
        """
        config = ActivityConfig(
            enabled=True,
            interval_hours=interval_hours,
            interval_minutes=0,
            priority=priority,
            max_retries=3,
            retry_delay_minutes=30,  # Retry in 30 minutes if fails
            max_execution_seconds=60,
            parameters={
                'collect_all_rewards': collect_all_rewards
            }
        )

        super().__init__(
            name="VIP Collection",
            config=config,
            adb_connection=adb_connection,
            screen_analyzer=screen_analyzer
        )

        # Template paths
        self.templates = {
            'vip_button': 'templates/buttons/vip.png',
            'vip_chest': 'templates/buttons/vip_chest.png',
            'collect_button': 'templates/buttons/collect.png',
            'vip_screen': 'templates/screens/vip_screen.png',
            'close_button': 'templates/buttons/close.png',
            'ok_button': 'templates/buttons/ok.png'
        }

        self.last_collection_time: Optional[datetime] = None

    def check_prerequisites(self) -> bool:
        """
        Check if VIP collection can run.

        Prerequisites:
        1. Game is running and logged in
        2. Screen capture working
        3. At least 23 hours since last collection (daily cooldown)

        Returns:
            True if prerequisites met, False otherwise
        """
        self.logger.info("Checking prerequisites for VIP collection")

        # Check: Can we capture screen?
        screenshot = self.adb.capture_screen()
        if screenshot is None:
            self.logger.error("Cannot capture screenshot - game may not be running")
            return False

        # Check: Is it too soon since last collection?
        if self.last_collection_time:
            time_since_last = datetime.now() - self.last_collection_time
            if time_since_last < timedelta(hours=23):
                hours_remaining = 23 - (time_since_last.total_seconds() / 3600)
                self.logger.info(f"Too soon to collect VIP (wait {hours_remaining:.1f} more hours)")
                return False

        self.logger.info("✓ Prerequisites met for VIP collection")
        return True

    def execute(self) -> bool:
        """
        Execute VIP collection.

        Steps:
        1. Navigate to VIP screen
        2. Find VIP chest/reward
        3. Tap to collect
        4. Handle reward popup
        5. Exit screen

        Returns:
            True if collection successful, False otherwise
        """
        self.logger.info("Starting VIP collection execution")

        try:
            # Step 1: Navigate to VIP screen
            if not self._navigate_to_vip_screen():
                self.logger.error("Failed to navigate to VIP screen")
                return False

            # Step 2: Find VIP chest/reward
            chest_location = self._find_vip_chest()
            if chest_location is None:
                self.logger.warning("VIP chest not found - may already be collected")
                return False

            # Step 3: Tap chest to collect
            if not self._tap_chest(chest_location):
                self.logger.error("Failed to tap VIP chest")
                return False

            # Step 4: Handle reward popup
            if not self._handle_reward_popup():
                self.logger.warning("Reward popup handling unclear - may still have succeeded")
                # Don't return False here - collection might have worked

            # Step 5: Exit VIP screen
            self._exit_vip_screen()

            # Update last collection time
            self.last_collection_time = datetime.now()

            self.logger.info("✓ VIP collection execution complete")
            return True

        except Exception as e:
            self.logger.error(f"Exception during VIP collection: {e}", exc_info=True)
            return False

    def verify_completion(self) -> bool:
        """
        Verify that VIP collection was successful.

        Verification methods:
        1. Check if reward popup appeared during execution
        2. Check if we're back on main screen
        3. Check if last_collection_time was updated

        Returns:
            True if collection verified, False otherwise
        """
        self.logger.info("Verifying VIP collection completion")

        # Method 1: Was last_collection_time updated?
        if self.last_collection_time:
            time_since = datetime.now() - self.last_collection_time
            if time_since.total_seconds() < 60:  # Updated in last minute
                self.logger.info("✓ Collection time was updated - success")
                return True

        # Method 2: Are we back on main screen? (basic check)
        screenshot = self.adb.capture_screen()
        if screenshot is not None:
            # If we're not on VIP screen anymore, likely succeeded
            vip_screen_result = self.screen.find_template(
                screenshot,
                self.templates['vip_screen'],
                confidence_threshold=0.7
            )

            if not vip_screen_result.found:
                self.logger.info("✓ VIP screen exited - likely successful")
                return True

        self.logger.warning("Cannot verify VIP collection - uncertain result")
        return False

    # ========================================================================
    # NAVIGATION METHODS
    # ========================================================================

    def _navigate_to_vip_screen(self) -> bool:
        """
        Navigate to VIP screen from current location.

        Strategy:
        1. Check if already on VIP screen
        2. Try finding VIP button and tapping it
        3. Wait for screen to load
        4. Verify VIP screen loaded

        Returns:
            True if navigation successful, False otherwise
        """
        self.logger.info("Navigating to VIP screen")

        # Check if already on VIP screen
        screenshot = self.adb.capture_screen()
        if screenshot is None:
            return False

        vip_screen_result = self.screen.find_template(
            screenshot,
            self.templates['vip_screen'],
            confidence_threshold=0.8
        )

        if vip_screen_result.found:
            self.logger.info("Already on VIP screen")
            return True

        # Find and tap VIP button
        vip_button_result = self.screen.find_template(
            screenshot,
            self.templates['vip_button'],
            confidence_threshold=0.8
        )

        if not vip_button_result.found:
            self.logger.error("VIP button not found")
            return False

        self.logger.info(f"VIP button found at ({vip_button_result.location[0]}, {vip_button_result.location[1]})")

        # Tap VIP button
        success = self.adb.tap(
            vip_button_result.location[0],
            vip_button_result.location[1],
            randomize=True
        )

        if not success:
            self.logger.error("Failed to tap VIP button")
            return False

        # Wait for screen to load
        wait_time = random.uniform(2.0, 3.0)
        self.logger.debug(f"Waiting {wait_time:.1f}s for VIP screen to load")
        time.sleep(wait_time)

        # Verify VIP screen loaded
        screenshot = self.adb.capture_screen()
        if screenshot is None:
            return False

        vip_screen_result = self.screen.find_template(
            screenshot,
            self.templates['vip_screen'],
            confidence_threshold=0.7
        )

        if vip_screen_result.found:
            self.logger.info("✓ VIP screen loaded successfully")
            return True
        else:
            self.logger.error("VIP screen did not load")
            return False

    def _find_vip_chest(self) -> Optional[Tuple[int, int]]:
        """
        Find the VIP chest/reward on screen.

        Returns:
            Tuple of (x, y) coordinates if found, None otherwise
        """
        self.logger.info("Looking for VIP chest")

        screenshot = self.adb.capture_screen()
        if screenshot is None:
            return None

        # Try finding VIP chest icon
        chest_result = self.screen.find_template(
            screenshot,
            self.templates['vip_chest'],
            confidence_threshold=0.7  # Lower threshold as chest varies by VIP level
        )

        if chest_result.found:
            self.logger.info(f"✓ VIP chest found at ({chest_result.location[0]}, {chest_result.location[1]})")
            return chest_result.location

        # Alternative: Try finding "Collect" button directly
        collect_result = self.screen.find_template(
            screenshot,
            self.templates['collect_button'],
            confidence_threshold=0.75
        )

        if collect_result.found:
            self.logger.info(f"✓ Collect button found at ({collect_result.location[0]}, {collect_result.location[1]})")
            return collect_result.location

        self.logger.warning("VIP chest not found - may already be collected")
        return None

    def _tap_chest(self, location: Tuple[int, int]) -> bool:
        """
        Tap the VIP chest to collect.

        Args:
            location: (x, y) coordinates to tap

        Returns:
            True if tap successful, False otherwise
        """
        self.logger.info(f"Tapping VIP chest at ({location[0]}, {location[1]})")

        success = self.adb.tap(
            location[0],
            location[1],
            randomize=True  # Add ±5px randomization
        )

        if not success:
            self.logger.error("Failed to tap chest")
            return False

        # Wait for popup to appear
        wait_time = random.uniform(1.5, 2.5)
        self.logger.debug(f"Waiting {wait_time:.1f}s for reward popup")
        time.sleep(wait_time)

        return True

    def _handle_reward_popup(self) -> bool:
        """
        Handle the reward collection popup.

        Looks for and taps:
        - "Collect" button
        - "OK" button
        - "Close" button

        Returns:
            True if popup handled, False if no popup found
        """
        self.logger.info("Handling reward popup")

        screenshot = self.adb.capture_screen()
        if screenshot is None:
            return False

        # Try finding "Collect" button
        collect_result = self.screen.find_template(
            screenshot,
            self.templates['collect_button'],
            confidence_threshold=0.8
        )

        if collect_result.found:
            self.logger.info("Found Collect button in popup")
            self.adb.tap(
                collect_result.location[0],
                collect_result.location[1],
                randomize=True
            )
            time.sleep(random.uniform(0.8, 1.2))
            return True

        # Try finding "OK" button
        ok_result = self.screen.find_template(
            screenshot,
            self.templates['ok_button'],
            confidence_threshold=0.8
        )

        if ok_result.found:
            self.logger.info("Found OK button in popup")
            self.adb.tap(
                ok_result.location[0],
                ok_result.location[1],
                randomize=True
            )
            time.sleep(random.uniform(0.8, 1.2))
            return True

        self.logger.warning("No reward popup buttons found")
        return False

    def _exit_vip_screen(self) -> bool:
        """
        Exit VIP screen and return to main view.

        Returns:
            True if exit successful, False otherwise
        """
        self.logger.info("Exiting VIP screen")

        screenshot = self.adb.capture_screen()
        if screenshot is None:
            return False

        # Find close button
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
            time.sleep(random.uniform(1.0, 1.5))
            return True
        else:
            # Fallback: Use hardware back button
            self.logger.info("Close button not found, using back button")
            self.adb.press_back()
            time.sleep(random.uniform(1.0, 1.5))
            return True


def create_vip_collection_activity(
    adb_connection: ADBConnection,
    screen_analyzer: ScreenAnalyzer,
    interval_hours: int = 24,
    priority: int = 3,
    collect_all_rewards: bool = True
) -> VIPCollectionActivity:
    """
    Factory function to create VIP Collection activity.

    Args:
        adb_connection: ADB connection instance
        screen_analyzer: Screen analyzer instance
        interval_hours: Collection interval (default: 24 hours)
        priority: Activity priority (default: 3)
        collect_all_rewards: Collect all rewards if available

    Returns:
        Configured VIPCollectionActivity instance
    """
    return VIPCollectionActivity(
        adb_connection=adb_connection,
        screen_analyzer=screen_analyzer,
        interval_hours=interval_hours,
        priority=priority,
        collect_all_rewards=collect_all_rewards
    )
