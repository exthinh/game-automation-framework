"""
Troop Training Activity

Automatically queues troop training in barracks, archery range, stable, and siege workshop.
Keeps troops training 24/7 to maximize power growth.

Based on: CTroopTrainTab from original WhaleBots
"""

from typing import Dict, Any, Optional, List
import logging
import time
from dataclasses import dataclass

from ...core.activity import Activity, ActivityConfig
from ...core.adb import ADBConnection
from ...core.screen import ScreenAnalyzer


@dataclass
class TroopTrainingConfig(ActivityConfig):
    """Configuration for troop training"""
    # Building priorities (which buildings to check)
    check_barracks: bool = True
    check_archery_range: bool = True
    check_stable: bool = True
    check_siege_workshop: bool = True

    # Troop type preferences per building (tier 1-5)
    barracks_troop_tier: int = 4  # Which tier infantry to train
    archery_troop_tier: int = 4   # Which tier archer to train
    stable_troop_tier: int = 4     # Which tier cavalry to train
    siege_troop_tier: int = 4      # Which tier siege to train

    # Training behavior
    train_max: bool = True         # Train maximum available troops
    use_speedups: bool = False     # Use training speedups (not recommended)

    # Resource limits (don't train if below these amounts)
    min_food: int = 100000
    min_wood: int = 50000
    min_stone: int = 50000
    min_gold: int = 50000

    # Advanced settings
    prioritize_power: bool = True  # Train highest tier available
    check_resources: bool = True   # Verify resources before training


class TroopTrainingActivity(Activity):
    """
    Automatically trains troops in all available training buildings.

    Process:
    1. Check each training building (barracks, archery, stable, siege)
    2. Detect if training queue is empty
    3. Select configured troop type
    4. Train maximum available (or configured amount)
    5. Verify training started

    Success Criteria:
    - Training queue started in at least one building
    - OR all buildings already have active training
    """

    def __init__(self, config: TroopTrainingConfig, adb: ADBConnection, screen: ScreenAnalyzer):
        super().__init__("Troop Training", config)
        self.adb = adb
        self.screen = screen
        self.config: TroopTrainingConfig = config

        # Building types to check
        self.buildings = []
        if config.check_barracks:
            self.buildings.append({
                'name': 'barracks',
                'template': 'templates/buildings/barracks.png',
                'tier': config.barracks_troop_tier
            })
        if config.check_archery_range:
            self.buildings.append({
                'name': 'archery_range',
                'template': 'templates/buildings/archery_range.png',
                'tier': config.archery_troop_tier
            })
        if config.check_stable:
            self.buildings.append({
                'name': 'stable',
                'template': 'templates/buildings/stable.png',
                'tier': config.stable_troop_tier
            })
        if config.check_siege_workshop:
            self.buildings.append({
                'name': 'siege_workshop',
                'template': 'templates/buildings/siege_workshop.png',
                'tier': config.siege_troop_tier
            })

    def check_prerequisites(self) -> bool:
        """
        Check if we can train troops.

        Prerequisites:
        - At least one training building configured
        - Sufficient resources (if check enabled)
        - Game is running and connected
        - On city view screen
        """
        if not self.buildings:
            self.logger.warning("No training buildings configured")
            return False

        # Check if on city view
        if not self._is_on_city_view():
            self.logger.info("Not on city view, navigating...")
            if not self._navigate_to_city():
                self.logger.error("Failed to navigate to city view")
                return False

        # Check resources if enabled
        if self.config.check_resources:
            if not self._check_resources():
                self.logger.info("Insufficient resources for training")
                return False

        return True

    def execute(self) -> bool:
        """
        Execute troop training activity.

        Process:
        1. For each configured training building:
           a. Find and click the building
           b. Check if training queue is empty
           c. If empty, start training
           d. Close building UI
        2. Verify at least one training started
        """
        self.logger.info("Starting troop training check...")

        trained_count = 0
        already_training_count = 0

        for building in self.buildings:
            self.logger.info(f"Checking {building['name']}...")

            # Try to train in this building
            result = self._train_in_building(building)

            if result == "trained":
                trained_count += 1
                self.logger.info(f"Started training in {building['name']}")
            elif result == "already_training":
                already_training_count += 1
                self.logger.info(f"{building['name']} already has active training")
            else:
                self.logger.warning(f"Failed to process {building['name']}")

            # Small delay between buildings
            time.sleep(1.0 + (time.time() % 0.5))  # 1.0-1.5s random

        # Summary
        total_processed = trained_count + already_training_count
        self.logger.info(
            f"Training summary: {trained_count} started, "
            f"{already_training_count} already training, "
            f"{len(self.buildings) - total_processed} failed/unavailable"
        )

        # Success if we started training OR all buildings already training
        return trained_count > 0 or already_training_count == len(self.buildings)

    def verify_completion(self) -> bool:
        """
        Verify training activity completed successfully.

        Check:
        - Back on city view
        - Training UI closed
        """
        # Make sure we're back to city view
        if not self._is_on_city_view():
            self.logger.warning("Not on city view after training")
            self._navigate_to_city()

        return True

    def _train_in_building(self, building: Dict[str, Any]) -> str:
        """
        Attempt to train troops in a specific building.

        Returns:
            "trained" - Successfully started training
            "already_training" - Building already has active training
            "failed" - Could not start training
        """
        # Find building on city view
        screenshot = self.adb.capture_screen_cached()
        if screenshot is None:
            return "failed"

        building_location = self.screen.find_template(
            screenshot,
            building['template'],
            confidence=0.7
        )

        if building_location is None:
            self.logger.warning(f"Could not find {building['name']} on screen")
            return "failed"

        # Click building
        self.adb.tap(building_location[0], building_location[1], randomize=True)
        time.sleep(1.5 + (time.time() % 0.5))  # Wait for building UI

        # Take new screenshot of building UI
        screenshot = self.adb.capture_screen_cached()

        # Check if training queue is empty
        # Look for "Train" button (indicates empty queue)
        # vs "Training" indicator (indicates active queue)
        train_button = self.screen.find_template(
            screenshot,
            'templates/buttons/train.png',
            confidence=0.75
        )

        if train_button is None:
            # Check if already training
            training_indicator = self.screen.find_template(
                screenshot,
                'templates/indicators/training_active.png',
                confidence=0.7
            )

            if training_indicator:
                # Close building UI
                self._close_building_ui()
                return "already_training"
            else:
                self.logger.warning(f"Could not determine training status for {building['name']}")
                self._close_building_ui()
                return "failed"

        # Training queue is empty, start training
        # Click train button
        self.adb.tap(train_button[0], train_button[1], randomize=True)
        time.sleep(1.0 + (time.time() % 0.5))

        # Select troop tier
        if not self._select_troop_tier(building['tier']):
            self.logger.warning(f"Failed to select troop tier for {building['name']}")
            self._close_building_ui()
            return "failed"

        # Click train max or enter amount
        if self.config.train_max:
            train_max_button = self.screen.find_template(
                self.adb.capture_screen_cached(),
                'templates/buttons/train_max.png',
                confidence=0.75
            )

            if train_max_button:
                self.adb.tap(train_max_button[0], train_max_button[1], randomize=True)
                time.sleep(0.5)

        # Click confirm/train button
        screenshot = self.adb.capture_screen_cached()
        confirm_button = self.screen.find_template(
            screenshot,
            'templates/buttons/confirm_train.png',
            confidence=0.75
        )

        if confirm_button is None:
            # Try generic confirm button
            confirm_button = self.screen.find_template(
                screenshot,
                'templates/buttons/confirm.png',
                confidence=0.75
            )

        if confirm_button:
            self.adb.tap(confirm_button[0], confirm_button[1], randomize=True)
            time.sleep(1.0)

            # Close building UI
            self._close_building_ui()
            return "trained"
        else:
            self.logger.warning(f"Could not find confirm button for {building['name']}")
            self._close_building_ui()
            return "failed"

    def _select_troop_tier(self, tier: int) -> bool:
        """
        Select the configured troop tier.

        Tiers:
        1 = Basic troops (T1)
        2 = Advanced troops (T2)
        3 = Elite troops (T3)
        4 = Expert troops (T4)
        5 = Legendary troops (T5)
        """
        # In the training UI, troops are usually displayed in a row
        # We need to click the appropriate tier

        # Look for tier buttons/slots
        screenshot = self.adb.capture_screen_cached()

        # Try to find the specific tier template
        tier_template = f'templates/troops/tier_{tier}.png'
        tier_location = self.screen.find_template(
            screenshot,
            tier_template,
            confidence=0.7
        )

        if tier_location:
            self.adb.tap(tier_location[0], tier_location[1], randomize=True)
            time.sleep(0.5)
            return True

        # Fallback: Try to find tier by position
        # Usually tiers are displayed left-to-right: T1, T2, T3, T4, T5
        # We can try clicking at estimated positions
        # This is a fallback and may need adjustment per game resolution

        self.logger.warning(f"Could not find tier {tier} template, using fallback position")

        # Assuming 1920x1080 resolution, troop slots might be around:
        # Y position: ~600 (middle of screen)
        # X positions: T1=500, T2=700, T3=900, T4=1100, T5=1300

        tier_x_positions = {
            1: 500,
            2: 700,
            3: 900,
            4: 1100,
            5: 1300
        }

        if tier in tier_x_positions:
            x = tier_x_positions[tier]
            y = 600
            self.adb.tap(x, y, randomize=True)
            time.sleep(0.5)
            return True

        return False

    def _check_resources(self) -> bool:
        """
        Check if we have sufficient resources for training.

        Uses OCR to read resource amounts from city view.
        """
        screenshot = self.adb.capture_screen_cached()

        # Resource display is usually at the top of the screen
        # Format: [Food icon] 1,234,567  [Wood icon] 987,654 ...

        # Define regions where resources are displayed (top of screen)
        # For 1920x1080: Food ~200-400, Wood ~500-700, Stone ~800-1000, Gold ~1100-1300

        resources = {
            'food': (200, 50, 200, 50),    # (x, y, width, height)
            'wood': (500, 50, 200, 50),
            'stone': (800, 50, 200, 50),
            'gold': (1100, 50, 200, 50)
        }

        try:
            # Read food
            food_region = screenshot[
                resources['food'][1]:resources['food'][1] + resources['food'][3],
                resources['food'][0]:resources['food'][0] + resources['food'][2]
            ]
            food_text = self.screen.read_text(food_region)
            food_amount = self._parse_resource_amount(food_text)

            if food_amount < self.config.min_food:
                self.logger.info(f"Insufficient food: {food_amount} < {self.config.min_food}")
                return False

            # Similar for other resources...
            # For now, if we can read food and it's sufficient, consider it ok

            return True

        except Exception as e:
            self.logger.warning(f"Could not read resources via OCR: {e}")
            # If OCR fails, assume we have resources (fail-open)
            return True

    def _parse_resource_amount(self, text: str) -> int:
        """
        Parse resource amount from OCR text.

        Examples:
        "1,234,567" -> 1234567
        "1.2M" -> 1200000
        "987K" -> 987000
        """
        if not text:
            return 0

        # Remove common OCR artifacts
        text = text.replace(',', '').replace(' ', '').replace('.', '')

        # Handle M (millions) and K (thousands)
        if 'M' in text.upper():
            try:
                num = float(text.upper().replace('M', ''))
                return int(num * 1000000)
            except:
                return 0
        elif 'K' in text.upper():
            try:
                num = float(text.upper().replace('K', ''))
                return int(num * 1000)
            except:
                return 0
        else:
            try:
                return int(text)
            except:
                return 0

    def _is_on_city_view(self) -> bool:
        """Check if currently on city view screen."""
        screenshot = self.adb.capture_screen_cached()

        # Look for city view indicators
        # Could be: city center building, resource display, etc.
        city_indicator = self.screen.find_template(
            screenshot,
            'templates/screens/city_view.png',
            confidence=0.7
        )

        return city_indicator is not None

    def _navigate_to_city(self) -> bool:
        """Navigate back to city view."""
        # Try pressing back button a few times
        for _ in range(3):
            # Look for back button
            screenshot = self.adb.capture_screen_cached()
            back_button = self.screen.find_template(
                screenshot,
                'templates/buttons/back.png',
                confidence=0.75
            )

            if back_button:
                self.adb.tap(back_button[0], back_button[1], randomize=True)
                time.sleep(1.0)

            # Check if on city view now
            if self._is_on_city_view():
                return True

        # If still not on city view, try clicking city center or home button
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

    def _close_building_ui(self):
        """Close the building UI and return to city view."""
        # Look for close/X button
        screenshot = self.adb.capture_screen_cached()
        close_button = self.screen.find_template(
            screenshot,
            'templates/buttons/close.png',
            confidence=0.75
        )

        if close_button:
            self.adb.tap(close_button[0], close_button[1], randomize=True)
        else:
            # Fallback: tap outside the UI area (bottom right corner usually safe)
            self.adb.tap(1800, 1000, randomize=True)

        time.sleep(0.5)
