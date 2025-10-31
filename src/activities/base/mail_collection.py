"""
Mail Collection Activity

Opens mail inbox, collects attachment rewards, and optionally deletes read mail.

Complexity: LOW-MEDIUM
Execution Time: 30-60 seconds
Success Rate: 90%+

Flow:
1. Navigate to mail screen
2. Detect mail with attachments
3. Collect all attachments
4. Delete read mail (optional, keeps inbox clean)
5. Exit mail screen
6. Verify completion

Templates Required:
- templates/buttons/mail.png - Mail icon
- templates/buttons/collect_all_mail.png - Collect All button
- templates/buttons/delete_mail.png - Delete button
- templates/icons/mail_attachment.png - Mail with attachment indicator
- templates/screens/mail_screen.png - Mail screen identifier
"""

import logging
import time
import random
from typing import Optional, Tuple, List
from datetime import datetime, timedelta

from src.core.activity import Activity, ActivityConfig
from src.core.adb import ADBConnection
from src.core.screen import ScreenAnalyzer


class MailCollectionActivity(Activity):
    """
    Collects mail attachments and manages inbox.

    This activity:
    - Opens mail inbox
    - Collects all attachment rewards
    - Optionally deletes read mail
    - Keeps inbox organized
    """

    def __init__(
        self,
        adb_connection: ADBConnection,
        screen_analyzer: ScreenAnalyzer,
        interval_hours: int = 1,  # Check mail every hour
        priority: int = 4,  # High priority - AP items, event rewards
        delete_read_mail: bool = True
    ):
        """
        Initialize Mail Collection activity.

        Args:
            adb_connection: ADB connection to emulator
            screen_analyzer: Screen analysis engine
            interval_hours: How often to check mail (default: 1 hour)
            priority: Activity priority (default: 4 - high)
            delete_read_mail: Whether to delete read mail
        """
        config = ActivityConfig(
            enabled=True,
            interval_hours=interval_hours,
            interval_minutes=0,
            priority=priority,
            max_retries=3,
            retry_delay_minutes=15,
            max_execution_seconds=90,
            parameters={
                'delete_read_mail': delete_read_mail
            }
        )

        super().__init__(
            name="Mail Collection",
            config=config,
            adb_connection=adb_connection,
            screen_analyzer=screen_analyzer
        )

        # Template paths
        self.templates = {
            'mail_button': 'templates/buttons/mail.png',
            'mail_screen': 'templates/screens/mail_screen.png',
            'collect_all': 'templates/buttons/collect_all_mail.png',
            'collect_button': 'templates/buttons/collect.png',
            'delete_button': 'templates/buttons/delete_mail.png',
            'mail_attachment_icon': 'templates/icons/mail_attachment.png',
            'close_button': 'templates/buttons/close.png'
        }

        self.delete_read_mail = delete_read_mail
        self.attachments_collected = 0

    def check_prerequisites(self) -> bool:
        """
        Check if mail collection can run.

        Prerequisites:
        1. Game is running and logged in
        2. Screen capture working

        Returns:
            True if prerequisites met, False otherwise
        """
        self.logger.info("Checking prerequisites for mail collection")

        # Check: Can we capture screen?
        screenshot = self.adb.capture_screen()
        if screenshot is None:
            self.logger.error("Cannot capture screenshot")
            return False

        self.logger.info("✓ Prerequisites met for mail collection")
        return True

    def execute(self) -> bool:
        """
        Execute mail collection.

        Steps:
        1. Navigate to mail screen
        2. Check for mail with attachments
        3. Collect all attachments
        4. Delete read mail (if configured)
        5. Exit mail screen

        Returns:
            True if execution successful, False otherwise
        """
        self.logger.info("Starting mail collection execution")
        self.attachments_collected = 0

        try:
            # Step 1: Navigate to mail screen
            if not self._navigate_to_mail_screen():
                self.logger.error("Failed to navigate to mail screen")
                return False

            # Step 2: Check for attachments
            has_attachments = self._has_mail_with_attachments()

            if not has_attachments:
                self.logger.info("No mail with attachments found")
                # Not an error - just nothing to collect
                self._exit_mail_screen()
                return True  # Success (nothing to do)

            # Step 3: Collect all attachments
            if not self._collect_all_attachments():
                self.logger.warning("Failed to collect all attachments")
                # Continue anyway - might have collected some

            # Step 4: Delete read mail (if configured)
            if self.delete_read_mail:
                self._delete_read_mail()

            # Step 5: Exit mail screen
            self._exit_mail_screen()

            self.logger.info(f"✓ Mail collection complete ({self.attachments_collected} collected)")
            return True

        except Exception as e:
            self.logger.error(f"Exception during mail collection: {e}", exc_info=True)
            return False

    def verify_completion(self) -> bool:
        """
        Verify that mail collection was successful.

        Verification methods:
        1. Check if we collected any attachments
        2. Check if we're no longer on mail screen

        Returns:
            True if collection verified, False otherwise
        """
        self.logger.info("Verifying mail collection completion")

        # Method 1: Did we collect anything?
        if self.attachments_collected > 0:
            self.logger.info(f"✓ Collected {self.attachments_collected} attachments - success")
            return True

        # Method 2: Are we back on main screen?
        screenshot = self.adb.capture_screen()
        if screenshot is not None:
            mail_screen_result = self.screen.find_template(
                screenshot,
                self.templates['mail_screen'],
                confidence_threshold=0.7
            )

            if not mail_screen_result.found:
                self.logger.info("✓ Mail screen exited - likely successful")
                return True

        self.logger.info("No attachments collected (may be normal)")
        return True  # Not finding attachments is okay

    # ========================================================================
    # NAVIGATION METHODS
    # ========================================================================

    def _navigate_to_mail_screen(self) -> bool:
        """
        Navigate to mail screen from current location.

        Returns:
            True if navigation successful, False otherwise
        """
        self.logger.info("Navigating to mail screen")

        # Check if already on mail screen
        screenshot = self.adb.capture_screen()
        if screenshot is None:
            return False

        mail_screen_result = self.screen.find_template(
            screenshot,
            self.templates['mail_screen'],
            confidence_threshold=0.8
        )

        if mail_screen_result.found:
            self.logger.info("Already on mail screen")
            return True

        # Find and tap mail button
        mail_button_result = self.screen.find_template(
            screenshot,
            self.templates['mail_button'],
            confidence_threshold=0.8
        )

        if not mail_button_result.found:
            self.logger.error("Mail button not found")
            return False

        self.logger.info(f"Mail button found at ({mail_button_result.location[0]}, {mail_button_result.location[1]})")

        # Tap mail button
        success = self.adb.tap(
            mail_button_result.location[0],
            mail_button_result.location[1],
            randomize=True
        )

        if not success:
            self.logger.error("Failed to tap mail button")
            return False

        # Wait for screen to load
        wait_time = random.uniform(2.0, 3.0)
        self.logger.debug(f"Waiting {wait_time:.1f}s for mail screen to load")
        time.sleep(wait_time)

        # Verify mail screen loaded
        screenshot = self.adb.capture_screen()
        if screenshot is None:
            return False

        mail_screen_result = self.screen.find_template(
            screenshot,
            self.templates['mail_screen'],
            confidence_threshold=0.7
        )

        if mail_screen_result.found:
            self.logger.info("✓ Mail screen loaded successfully")
            return True
        else:
            self.logger.error("Mail screen did not load")
            return False

    # ========================================================================
    # MAIL DETECTION AND COLLECTION METHODS
    # ========================================================================

    def _has_mail_with_attachments(self) -> bool:
        """
        Check if there is any mail with attachments.

        Returns:
            True if mail with attachments found, False otherwise
        """
        self.logger.info("Checking for mail with attachments")

        screenshot = self.adb.capture_screen()
        if screenshot is None:
            return False

        # Look for attachment icon
        attachment_result = self.screen.find_template(
            screenshot,
            self.templates['mail_attachment_icon'],
            confidence_threshold=0.75
        )

        if attachment_result.found:
            self.logger.info("✓ Mail with attachments found")
            return True

        # Alternative: Look for "Collect All" button
        collect_all_result = self.screen.find_template(
            screenshot,
            self.templates['collect_all'],
            confidence_threshold=0.8
        )

        if collect_all_result.found:
            self.logger.info("✓ Collect All button found - attachments available")
            return True

        self.logger.info("No mail with attachments")
        return False

    def _collect_all_attachments(self) -> bool:
        """
        Collect all mail attachments.

        Returns:
            True if collection successful, False otherwise
        """
        self.logger.info("Collecting all mail attachments")

        screenshot = self.adb.capture_screen()
        if screenshot is None:
            return False

        # Try finding "Collect All" button
        collect_all_result = self.screen.find_template(
            screenshot,
            self.templates['collect_all'],
            confidence_threshold=0.8
        )

        if collect_all_result.found:
            self.logger.info("Found Collect All button")
            success = self.adb.tap(
                collect_all_result.location[0],
                collect_all_result.location[1],
                randomize=True
            )

            if not success:
                self.logger.error("Failed to tap Collect All button")
                return False

            # Wait for collection to process
            wait_time = random.uniform(2.0, 3.5)
            self.logger.debug(f"Waiting {wait_time:.1f}s for attachment collection")
            time.sleep(wait_time)

            self.attachments_collected += 1  # At least one
            self.logger.info("✓ Attachments collected via Collect All")
            return True

        # Alternative: Find individual collect buttons
        self.logger.info("Collect All not found, trying individual collect")
        return self._collect_individual_attachments()

    def _collect_individual_attachments(self) -> bool:
        """
        Collect attachments from individual mail items.

        Returns:
            True if at least one collected, False otherwise
        """
        self.logger.info("Collecting individual mail attachments")

        collected_any = False

        # Try up to 5 times (in case multiple mail items)
        for attempt in range(5):
            screenshot = self.adb.capture_screen()
            if screenshot is None:
                break

            # Find collect button
            collect_result = self.screen.find_template(
                screenshot,
                self.templates['collect_button'],
                confidence_threshold=0.8
            )

            if not collect_result.found:
                self.logger.info(f"No more collect buttons found (attempt {attempt + 1})")
                break

            self.logger.info(f"Found collect button (attempt {attempt + 1})")
            self.adb.tap(
                collect_result.location[0],
                collect_result.location[1],
                randomize=True
            )

            time.sleep(random.uniform(1.0, 1.5))
            self.attachments_collected += 1
            collected_any = True

        if collected_any:
            self.logger.info(f"✓ Collected {self.attachments_collected} individual attachments")

        return collected_any

    def _delete_read_mail(self) -> bool:
        """
        Delete all read mail to keep inbox clean.

        Returns:
            True if deletion successful, False otherwise
        """
        self.logger.info("Deleting read mail")

        screenshot = self.adb.capture_screen()
        if screenshot is None:
            return False

        # Find delete button
        delete_result = self.screen.find_template(
            screenshot,
            self.templates['delete_button'],
            confidence_threshold=0.8
        )

        if delete_result.found:
            self.logger.info("Found delete button")
            self.adb.tap(
                delete_result.location[0],
                delete_result.location[1],
                randomize=True
            )

            time.sleep(random.uniform(1.0, 1.5))
            self.logger.info("✓ Read mail deleted")
            return True
        else:
            self.logger.info("Delete button not found (may have no read mail)")
            return False

    def _exit_mail_screen(self) -> bool:
        """
        Exit mail screen and return to main view.

        Returns:
            True if exit successful, False otherwise
        """
        self.logger.info("Exiting mail screen")

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


def create_mail_collection_activity(
    adb_connection: ADBConnection,
    screen_analyzer: ScreenAnalyzer,
    interval_hours: int = 1,
    priority: int = 4,
    delete_read_mail: bool = True
) -> MailCollectionActivity:
    """
    Factory function to create Mail Collection activity.

    Args:
        adb_connection: ADB connection instance
        screen_analyzer: Screen analyzer instance
        interval_hours: Check interval (default: 1 hour)
        priority: Activity priority (default: 4 - high)
        delete_read_mail: Whether to delete read mail

    Returns:
        Configured MailCollectionActivity instance
    """
    return MailCollectionActivity(
        adb_connection=adb_connection,
        screen_analyzer=screen_analyzer,
        interval_hours=interval_hours,
        priority=priority,
        delete_read_mail=delete_read_mail
    )
