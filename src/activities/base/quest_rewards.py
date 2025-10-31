"""
Quest Rewards Activity

Collects completed quest rewards from side quests, challenges, and campaigns.
Different from daily objectives - focuses on story quests and special challenges.

This activity navigates to the quest screen and collects all available rewards.
"""

from typing import List, Tuple, Optional
import logging
import time
from dataclasses import dataclass

from ...core.activity import Activity, ActivityConfig
from ...core.adb import ADBConnection
from ...core.screen import ScreenAnalyzer


@dataclass
class QuestRewardsConfig(ActivityConfig):
    """Configuration for quest rewards collection"""

    # Collection settings
    collect_all: bool = True           # Collect all available quest rewards
    max_quests: int = 30               # Max quests to collect per run

    # Quest types to collect
    collect_main_quests: bool = True   # Collect main storyline quests
    collect_side_quests: bool = True   # Collect side quests
    collect_challenges: bool = True    # Collect challenge rewards

    # Detection settings
    confidence: float = 0.75


class QuestRewardsActivity(Activity):
    """
    Collects completed quest rewards.

    Process:
    1. Navigate to quests screen
    2. Switch between quest tabs (main, side, challenges)
    3. Find completed quests (checkmark/claim indicators)
    4. Collect each quest's rewards
    5. Close and return to city

    Success Criteria:
    - Collected at least one quest reward
    - OR no quests ready to claim
    """

    def __init__(self, config: QuestRewardsConfig, adb: ADBConnection, screen: ScreenAnalyzer):
        super().__init__("Quest Rewards", config)
        self.adb = adb
        self.screen = screen
        self.config: QuestRewardsConfig = config

        self.quests_collected = 0

    def check_prerequisites(self) -> bool:
        """
        Check if we can collect quest rewards.

        Prerequisites:
        - Game is running
        """
        return True

    def execute(self) -> bool:
        """
        Execute quest rewards collection.

        Process:
        1. Navigate to quests screen
        2. For each quest type (main, side, challenges):
           a. Switch to that tab
           b. Collect completed quests
        3. Close and return
        """
        self.logger.info("Collecting quest rewards...")

        # Navigate to quests screen
        if not self._navigate_to_quests():
            self.logger.error("Failed to navigate to quests screen")
            return False

        time.sleep(1.0)

        self.quests_collected = 0

        # Collect from main quests
        if self.config.collect_main_quests:
            self.logger.debug("Checking main quests...")
            if self._switch_to_tab("main"):
                self.quests_collected += self._collect_quests_on_current_tab()

        # Collect from side quests
        if self.config.collect_side_quests:
            self.logger.debug("Checking side quests...")
            if self._switch_to_tab("side"):
                self.quests_collected += self._collect_quests_on_current_tab()

        # Collect from challenges
        if self.config.collect_challenges:
            self.logger.debug("Checking challenges...")
            if self._switch_to_tab("challenges"):
                self.quests_collected += self._collect_quests_on_current_tab()

        # Close quests screen
        self._close_quests_screen()

        # Navigate back to city
        self._navigate_to_city()

        # Summary
        if self.quests_collected > 0:
            self.logger.info(f"Collected {self.quests_collected} quest rewards")
            return True
        else:
            self.logger.info("No quest rewards ready to collect")
            return True  # Not an error

    def verify_completion(self) -> bool:
        """Verify quest collection completed."""
        if not self._is_on_city_view():
            self._navigate_to_city()
        return True

    def _collect_quests_on_current_tab(self) -> int:
        """
        Collect all completed quests visible on the current tab.

        Returns:
            Number of quests collected
        """
        collected = 0

        for i in range(self.config.max_quests):
            screenshot = self.adb.capture_screen_cached()

            # Look for claim/collect button
            claim_button = self.screen.find_template(
                screenshot,
                'templates/buttons/claim_quest.png',
                confidence=self.config.confidence
            )

            if claim_button is None:
                # Try alternative templates
                claim_button = self.screen.find_template(
                    screenshot,
                    'templates/buttons/claim.png',
                    confidence=self.config.confidence
                )

            if claim_button is None:
                # Try looking for checkmark indicator
                checkmark = self.screen.find_template(
                    screenshot,
                    'templates/icons/quest_complete.png',
                    confidence=self.config.confidence
                )

                if checkmark:
                    # Tap checkmark
                    self.adb.tap(checkmark[0], checkmark[1], randomize=True)
                    time.sleep(0.5)
                    collected += 1
                    self._close_reward_popup()
                else:
                    # No more completed quests on this tab
                    break

            else:
                # Tap claim button
                self.adb.tap(claim_button[0], claim_button[1], randomize=True)
                time.sleep(0.5 + (time.time() % 0.3))

                collected += 1

                # Handle reward popup
                self._close_reward_popup()

            # Small delay between collections
            time.sleep(0.3)

        return collected

    def _switch_to_tab(self, tab_name: str) -> bool:
        """
        Switch to a specific quest tab (main, side, challenges).

        Args:
            tab_name: "main", "side", or "challenges"

        Returns:
            True if switched successfully
        """
        screenshot = self.adb.capture_screen_cached()

        # Look for tab button
        tab_template = f'templates/tabs/quest_{tab_name}.png'
        tab_button = self.screen.find_template(
            screenshot,
            tab_template,
            confidence=self.config.confidence
        )

        if tab_button is None:
            self.logger.debug(f"Could not find {tab_name} quest tab")
            return False

        # Tap tab
        self.adb.tap(tab_button[0], tab_button[1], randomize=True)
        time.sleep(0.5)

        return True

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

    def _navigate_to_quests(self) -> bool:
        """Navigate to quests screen."""
        # Ensure on city view first
        if not self._is_on_city_view():
            if not self._navigate_to_city():
                return False

        # Find and tap quests button
        screenshot = self.adb.capture_screen_cached()
        quests_button = self.screen.find_template(
            screenshot,
            'templates/buttons/quests.png',
            confidence=self.config.confidence
        )

        if quests_button is None:
            # Try alternative names
            quests_button = self.screen.find_template(
                screenshot,
                'templates/buttons/missions.png',
                confidence=self.config.confidence
            )

        if quests_button is None:
            self.logger.error("Could not find quests button")
            return False

        # Tap quests button
        self.adb.tap(quests_button[0], quests_button[1], randomize=True)
        time.sleep(1.5 + (time.time() % 0.5))

        # Verify we're on quests screen
        screenshot = self.adb.capture_screen_cached()
        quests_screen = self.screen.find_template(
            screenshot,
            'templates/screens/quests.png',
            confidence=0.7
        )

        return quests_screen is not None

    def _close_quests_screen(self):
        """Close the quests screen."""
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
