"""
Account Switcher Activity

Switches between multiple game accounts.
Useful for managing alt accounts on the same emulator.
"""

from typing import List, Optional
import logging
import time
from dataclasses import dataclass

from ...core.activity import Activity, ActivityConfig
from ...core.adb import ADBConnection
from ...core.screen import ScreenAnalyzer


@dataclass
class AccountSwitcherConfig(ActivityConfig):
    """Configuration for account switcher"""
    accounts: List[str] = None  # List of account IDs
    switch_interval_minutes: int = 60  # Time on each account
    confidence: float = 0.75


class AccountSwitcherActivity(Activity):
    """Switches between multiple accounts."""

    def __init__(self, config: AccountSwitcherConfig, adb: ADBConnection, screen: ScreenAnalyzer):
        super().__init__("Account Switcher", config)
        self.adb = adb
        self.screen = screen
        self.config: AccountSwitcherConfig = config

        if self.config.accounts is None:
            self.config.accounts = []

        self.current_account_index = 0

    def check_prerequisites(self) -> bool:
        if len(self.config.accounts) < 2:
            return False
        return True

    def execute(self) -> bool:
        self.logger.info("Switching accounts...")

        # Logout from current account
        if not self._logout():
            self.logger.error("Failed to logout")
            return False

        # Select next account
        self.current_account_index = (self.current_account_index + 1) % len(self.config.accounts)
        next_account = self.config.accounts[self.current_account_index]

        # Login to next account
        if not self._login(next_account):
            self.logger.error(f"Failed to login to account: {next_account}")
            return False

        self.logger.info(f"Switched to account: {next_account}")
        return True

    def verify_completion(self) -> bool:
        return True

    def _logout(self) -> bool:
        """Logout from current account."""
        # Open settings
        screenshot = self.adb.capture_screen_cached()
        settings_button = self.screen.find_template(
            screenshot,
            'templates/buttons/settings.png',
            confidence=self.config.confidence
        )

        if not settings_button:
            return False

        self.adb.tap(settings_button[0], settings_button[1], randomize=True)
        time.sleep(1.0)

        # Find logout button
        screenshot = self.adb.capture_screen_cached()
        logout_button = self.screen.find_template(
            screenshot,
            'templates/buttons/logout.png',
            confidence=self.config.confidence
        )

        if not logout_button:
            return False

        self.adb.tap(logout_button[0], logout_button[1], randomize=True)
        time.sleep(1.0)

        # Confirm logout
        screenshot = self.adb.capture_screen_cached()
        confirm_button = self.screen.find_template(
            screenshot,
            'templates/buttons/confirm.png',
            confidence=0.75
        )

        if confirm_button:
            self.adb.tap(confirm_button[0], confirm_button[1], randomize=True)
            time.sleep(3.0)

        return True

    def _login(self, account_id: str) -> bool:
        """Login to specified account."""
        # This is simplified - actual implementation depends on account system
        # May need to select account from list or enter credentials
        self.logger.warning("Account login logic not yet fully implemented")
        time.sleep(5.0)  # Wait for game to load
        return True
