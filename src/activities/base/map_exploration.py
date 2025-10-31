"""
Map Exploration Activity

Sends scouts to unexplored fog areas to reveal the map.
Provides one-time rewards for exploring new areas.
"""

from typing import Optional
import logging
import time
from dataclasses import dataclass

from ...core.activity import Activity, ActivityConfig
from ...core.adb import ADBConnection
from ...core.screen import ScreenAnalyzer


@dataclass
class MapExplorationConfig(ActivityConfig):
    """Configuration for map exploration"""
    max_scouts_per_run: int = 5
    search_radius: int = 10  # Tiles from city
    confidence: float = 0.75


class MapExplorationActivity(Activity):
    """Explores map fog areas."""

    def __init__(self, config: MapExplorationConfig, adb: ADBConnection, screen: ScreenAnalyzer):
        super().__init__("Map Exploration", config)
        self.adb = adb
        self.screen = screen
        self.config: MapExplorationConfig = config
        self.scouts_sent = 0

    def check_prerequisites(self) -> bool:
        return True

    def execute(self) -> bool:
        self.logger.info("Exploring map...")

        if not self._navigate_to_map():
            self.logger.error("Failed to navigate to map")
            return False

        time.sleep(1.0)
        self.scouts_sent = self._send_scouts()

        self._navigate_to_city()

        if self.scouts_sent > 0:
            self.logger.info(f"Sent {self.scouts_sent} scout marches")
            return True
        else:
            self.logger.info("No fog areas found or scouts unavailable")
            return True

    def verify_completion(self) -> bool:
        if not self._is_on_city_view():
            self._navigate_to_city()
        return True

    def _send_scouts(self) -> int:
        # This is a simplified implementation
        # Full implementation would require fog detection and pathfinding
        scouts = 0
        # TODO: Implement fog area detection and scout sending
        self.logger.warning("Map exploration logic not yet fully implemented")
        return scouts

    def _navigate_to_map(self) -> bool:
        if not self._is_on_city_view():
            if not self._navigate_to_city():
                return False
        screenshot = self.adb.capture_screen_cached()
        map_button = self.screen.find_template(
            screenshot,
            'templates/buttons/world_map.png',
            confidence=self.config.confidence
        )
        if not map_button:
            return False
        self.adb.tap(map_button[0], map_button[1], randomize=True)
        time.sleep(1.5)
        return True

    def _is_on_city_view(self) -> bool:
        screenshot = self.adb.capture_screen_cached()
        return self.screen.find_template(
            screenshot,
            'templates/screens/city_view.png',
            confidence=0.7
        ) is not None

    def _navigate_to_city(self) -> bool:
        for _ in range(3):
            if self._is_on_city_view():
                return True
            screenshot = self.adb.capture_screen_cached()
            back_button = self.screen.find_template(
                screenshot,
                'templates/buttons/back.png',
                confidence=0.75
            )
            if back_button:
                self.adb.tap(back_button[0], back_button[1], randomize=True)
            time.sleep(1.0)
        return False
