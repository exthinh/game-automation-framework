"""
Expedition Activity

Completes expedition stages for rewards.
Expeditions are PVE challenges that give resources, speedups, and other items.

Process:
- Navigate to expedition screen
- Battle available stages
- Collect rewards
"""

from typing import Optional
import logging
import time
from dataclasses import dataclass

from ...core.activity import Activity, ActivityConfig
from ...core.adb import ADBConnection
from ...core.screen import ScreenAnalyzer


@dataclass
class ExpeditionConfig(ActivityConfig):
    """Configuration for expedition"""

    # Battle settings
    auto_battle: bool = True           # Use auto-battle feature
    max_stages_per_run: int = 10       # Max stages to complete per run

    # Stage selection
    continue_from_last: bool = True    # Continue from last completed stage
    start_stage: int = 1               # Stage to start from if not continuing

    # Resource management
    use_energy_potions: bool = False   # Use energy potions if out of energy

    # Detection settings
    confidence: float = 0.75


class ExpeditionActivity(Activity):
    """
    Completes expedition stages.

    Process:
    1. Navigate to expedition screen
    2. Select next available stage
    3. Start battle (auto-battle if enabled)
    4. Wait for battle completion
    5. Collect rewards
    6. Repeat for configured number of stages
    7. Close and return

    Success Criteria:
    - Completed at least one stage
    - OR no stages available / no energy
    """

    def __init__(self, config: ExpeditionConfig, adb: ADBConnection, screen: ScreenAnalyzer):
        super().__init__("Expedition", config)
        self.adb = adb
        self.screen = screen
        self.config: ExpeditionConfig = config

        self.stages_completed = 0

    def check_prerequisites(self) -> bool:
        """
        Check if we can do expedition.

        Prerequisites:
        - Game is running
        """
        return True

    def execute(self) -> bool:
        """
        Execute expedition activity.

        Process:
        1. Navigate to expedition
        2. Battle stages
        3. Collect rewards
        4. Close and return
        """
        self.logger.info("Starting expedition...")

        # Navigate to expedition screen
        if not self._navigate_to_expedition():
            self.logger.error("Failed to navigate to expedition")
            return False

        time.sleep(1.0)

        # Battle stages
        self.stages_completed = self._battle_stages()

        # Close expedition screen
        self._close_expedition_screen()

        # Navigate back to city
        self._navigate_to_city()

        if self.stages_completed > 0:
            self.logger.info(f"Completed {self.stages_completed} expedition stages")
            return True
        else:
            self.logger.info("No expedition stages completed (no energy or all done)")
            return True

    def verify_completion(self) -> bool:
        """Verify expedition completed."""
        if not self._is_on_city_view():
            self._navigate_to_city()
        return True

    def _battle_stages(self) -> int:
        """
        Battle expedition stages.

        Returns:
            Number of stages completed
        """
        completed = 0

        for i in range(self.config.max_stages_per_run):
            # Find next stage to battle
            screenshot = self.adb.capture_screen_cached()

            # Look for battle button
            battle_button = self.screen.find_template(
                screenshot,
                'templates/buttons/battle.png',
                confidence=self.config.confidence
            )

            if battle_button is None:
                # Try alternative template
                battle_button = self.screen.find_template(
                    screenshot,
                    'templates/buttons/expedition_battle.png',
                    confidence=self.config.confidence
                )

            if battle_button is None:
                # No more stages available
                break

            # Tap battle button
            self.adb.tap(battle_button[0], battle_button[1], randomize=True)
            time.sleep(1.5)

            # Start battle
            if not self._start_battle():
                self.logger.warning(f"Failed to start battle for stage {i+1}")
                break

            # Wait for battle to complete
            if not self._wait_for_battle_completion():
                self.logger.warning(f"Battle {i+1} did not complete properly")
                # Try to recover
                self._recover_from_battle()
                break

            # Collect rewards
            self._collect_battle_rewards()

            completed += 1

            # Small delay between stages
            time.sleep(1.0)

        return completed

    def _start_battle(self) -> bool:
        """Start the battle."""
        # Look for start/begin battle button
        screenshot = self.adb.capture_screen_cached()

        # Enable auto-battle if configured
        if self.config.auto_battle:
            auto_button = self.screen.find_template(
                screenshot,
                'templates/buttons/auto_battle.png',
                confidence=0.75
            )

            if auto_button:
                self.adb.tap(auto_button[0], auto_button[1], randomize=True)
                time.sleep(0.5)

        # Find and tap start button
        start_button = self.screen.find_template(
            screenshot,
            'templates/buttons/start_battle.png',
            confidence=self.config.confidence
        )

        if start_button is None:
            start_button = self.screen.find_template(
                screenshot,
                'templates/buttons/begin.png',
                confidence=self.config.confidence
            )

        if start_button:
            self.adb.tap(start_button[0], start_button[1], randomize=True)
            return True

        return False

    def _wait_for_battle_completion(self, timeout: int = 60) -> bool:
        """
        Wait for battle to complete.

        Args:
            timeout: Maximum seconds to wait

        Returns:
            True if battle completed successfully
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            screenshot = self.adb.capture_screen_cached()

            # Look for victory screen
            victory = self.screen.find_template(
                screenshot,
                'templates/screens/victory.png',
                confidence=0.75
            )

            if victory:
                self.logger.debug("Battle victory detected")
                return True

            # Check for defeat (shouldn't happen but handle it)
            defeat = self.screen.find_template(
                screenshot,
                'templates/screens/defeat.png',
                confidence=0.75
            )

            if defeat:
                self.logger.warning("Battle defeat detected")
                return False

            # Wait a bit before checking again
            time.sleep(2.0)

        self.logger.warning("Battle completion timeout")
        return False

    def _collect_battle_rewards(self):
        """Collect rewards after battle."""
        time.sleep(1.0)

        # Tap screen to dismiss victory screen
        self.adb.tap(960, 540, randomize=True)
        time.sleep(0.5)

        # Look for collect button
        screenshot = self.adb.capture_screen_cached()
        collect_button = self.screen.find_template(
            screenshot,
            'templates/buttons/collect_expedition.png',
            confidence=0.75
        )

        if collect_button:
            self.adb.tap(collect_button[0], collect_button[1], randomize=True)
            time.sleep(0.5)

        # Tap to dismiss reward screen
        self.adb.tap(960, 540, randomize=True)
        time.sleep(0.5)

    def _recover_from_battle(self):
        """Attempt to recover from stuck battle."""
        # Press back a few times
        for _ in range(3):
            self._press_back()
            time.sleep(0.5)

    def _navigate_to_expedition(self) -> bool:
        """Navigate to expedition screen."""
        if not self._is_on_city_view():
            if not self._navigate_to_city():
                return False

        screenshot = self.adb.capture_screen_cached()
        expedition_button = self.screen.find_template(
            screenshot,
            'templates/buttons/expedition.png',
            confidence=self.config.confidence
        )

        if expedition_button is None:
            return False

        self.adb.tap(expedition_button[0], expedition_button[1], randomize=True)
        time.sleep(1.5)
        return True

    def _close_expedition_screen(self):
        """Close expedition screen."""
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
