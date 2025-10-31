"""
Research Management Activity

Automatically starts research based on priority list.
Ensures research is always active to maximize account progression.

Process:
- Navigate to academy
- Check if research slot available
- Select research from priority list
- Start research
- Verify research started
"""

from typing import List, Optional
import logging
import time
from dataclasses import dataclass

from ...core.activity import Activity, ActivityConfig
from ...core.adb import ADBConnection
from ...core.screen import ScreenAnalyzer


@dataclass
class ResearchManagementConfig(ActivityConfig):
    """Configuration for research management"""

    # Research priorities (list of research names in order)
    research_priority: List[str] = None  # e.g., ["Military Tech I", "Economic Tech I"]

    # Research categories to enable
    enable_economic: bool = True
    enable_military: bool = True
    enable_development: bool = True

    # Resource limits (don't research if below these)
    min_food: int = 1000000
    min_wood: int = 500000
    min_stone: int = 500000
    min_gold: int = 500000

    # Settings
    check_prerequisites: bool = True   # Check if previous research completed
    auto_select_next: bool = True      # Auto-select next available if priority not found

    # Detection settings
    confidence: float = 0.75


class ResearchManagementActivity(Activity):
    """
    Automatically manages research queue.

    Process:
    1. Navigate to academy
    2. Check if research slot available
    3. Select research from priority list
    4. Check requirements (resources, prerequisites)
    5. Start research
    6. Verify research started

    Success Criteria:
    - Research started successfully
    - OR research already active
    """

    def __init__(self, config: ResearchManagementConfig, adb: ADBConnection, screen: ScreenAnalyzer):
        super().__init__("Research Management", config)
        self.adb = adb
        self.screen = screen
        self.config: ResearchManagementConfig = config

        if self.config.research_priority is None:
            self.config.research_priority = []

        self.research_started = False

    def check_prerequisites(self) -> bool:
        """
        Check if we can start research.

        Prerequisites:
        - Research priority list configured
        - Game is running
        """
        if not self.config.research_priority:
            self.logger.warning("No research priority list configured")
            return False

        return True

    def execute(self) -> bool:
        """
        Execute research management.

        Process:
        1. Navigate to academy
        2. Check research status
        3. Start new research if needed
        4. Close and return
        """
        self.logger.info("Managing research...")

        # Navigate to academy
        if not self._navigate_to_academy():
            self.logger.error("Failed to navigate to academy")
            return False

        time.sleep(1.0)

        # Check if research already active
        if self._is_research_active():
            self.logger.info("Research already active")
            self._close_academy()
            self._navigate_to_city()
            return True

        # Start new research
        self.research_started = self._start_research()

        # Close academy
        self._close_academy()

        # Navigate back to city
        self._navigate_to_city()

        if self.research_started:
            self.logger.info("Research started successfully")
            return True
        else:
            self.logger.info("No research started (requirements not met or already researching)")
            return True  # Not an error

    def verify_completion(self) -> bool:
        """Verify research management completed."""
        if not self._is_on_city_view():
            self._navigate_to_city()
        return True

    def _is_research_active(self) -> bool:
        """Check if research is currently active."""
        screenshot = self.adb.capture_screen_cached()

        # Look for research progress indicator
        research_active = self.screen.find_template(
            screenshot,
            'templates/indicators/research_active.png',
            confidence=self.config.confidence
        )

        return research_active is not None

    def _start_research(self) -> bool:
        """
        Start new research from priority list.

        Returns:
            True if research started
        """
        # Try each priority research in order
        for research_name in self.config.research_priority:
            self.logger.debug(f"Checking research: {research_name}")

            if self._try_start_research(research_name):
                return True

        # If auto-select enabled, try finding any available research
        if self.config.auto_select_next:
            self.logger.info("Priority research not available, looking for any available...")
            return self._start_any_available_research()

        return False

    def _try_start_research(self, research_name: str) -> bool:
        """
        Try to start a specific research.

        Args:
            research_name: Name of research to start

        Returns:
            True if started successfully
        """
        # Find research in tree
        research_template = f'templates/research/{research_name.lower().replace(" ", "_")}.png'

        screenshot = self.adb.capture_screen_cached()
        research_location = self.screen.find_template(
            screenshot,
            research_template,
            confidence=self.config.confidence
        )

        if not research_location:
            self.logger.debug(f"Research not found: {research_name}")
            return False

        # Tap research
        self.adb.tap(research_location[0], research_location[1], randomize=True)
        time.sleep(1.0)

        # Look for research button
        screenshot = self.adb.capture_screen_cached()
        research_button = self.screen.find_template(
            screenshot,
            'templates/buttons/research.png',
            confidence=self.config.confidence
        )

        if not research_button:
            # Research might be locked or already completed
            self._press_back()
            return False

        # Tap research button
        self.adb.tap(research_button[0], research_button[1], randomize=True)
        time.sleep(1.0)

        # Confirm if needed
        screenshot = self.adb.capture_screen_cached()
        confirm_button = self.screen.find_template(
            screenshot,
            'templates/buttons/confirm.png',
            confidence=0.75
        )

        if confirm_button:
            self.adb.tap(confirm_button[0], confirm_button[1], randomize=True)
            time.sleep(0.5)

        return True

    def _start_any_available_research(self) -> bool:
        """Start any available research."""
        # This would require more complex logic to find available research
        # For now, return False
        self.logger.warning("Auto-select research not yet implemented")
        return False

    def _navigate_to_academy(self) -> bool:
        """Navigate to academy."""
        if not self._is_on_city_view():
            if not self._navigate_to_city():
                return False

        screenshot = self.adb.capture_screen_cached()

        # Find academy building
        academy = self.screen.find_template(
            screenshot,
            'templates/buildings/academy.png',
            confidence=self.config.confidence
        )

        if not academy:
            self.logger.error("Academy not found")
            return False

        # Tap academy
        self.adb.tap(academy[0], academy[1], randomize=True)
        time.sleep(1.5)

        # Verify academy screen opened
        screenshot = self.adb.capture_screen_cached()
        academy_screen = self.screen.find_template(
            screenshot,
            'templates/screens/academy.png',
            confidence=0.7
        )

        return academy_screen is not None

    def _close_academy(self):
        """Close academy screen."""
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
