"""
Emergency Stop Activity

CRITICAL SAFETY FEATURE

Detects critical situations and immediately stops the bot to prevent account loss.
This activity runs frequently (higher priority) to monitor for dangerous conditions.

Emergency Conditions:
- Incoming attack detected
- City shield dropped below threshold
- Kingdom migration detected
- Suspicious activity detected
- Connection lost to game

When triggered, this activity will:
1. Stop all other activities
2. Alert the user (log + notification)
3. Optionally teleport to safety
4. Pause automation until manual resume
"""

from typing import List, Tuple, Optional
import logging
import time
from dataclasses import dataclass
from enum import Enum

from ...core.activity import Activity, ActivityConfig
from ...core.adb import ADBConnection
from ...core.screen import ScreenAnalyzer


class EmergencyType(Enum):
    """Types of emergencies"""
    INCOMING_ATTACK = "incoming_attack"
    SHIELD_DOWN = "shield_down"
    LOW_SHIELD = "low_shield"
    KINGDOM_MIGRATION = "kingdom_migration"
    CONNECTION_LOST = "connection_lost"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    RESOURCE_OVERFLOW = "resource_overflow"


@dataclass
class EmergencyStopConfig(ActivityConfig):
    """Configuration for emergency stop"""

    # Shield monitoring
    monitor_shield: bool = True
    min_shield_hours: int = 8          # Stop if shield < 8 hours
    stop_on_no_shield: bool = True     # Stop if shield completely gone

    # Attack monitoring
    monitor_attacks: bool = True
    stop_on_incoming_attack: bool = True

    # Kingdom monitoring
    monitor_kingdom: bool = True
    stop_on_migration: bool = True

    # Connection monitoring
    monitor_connection: bool = True
    stop_on_disconnect: bool = True

    # Actions on emergency
    pause_all_activities: bool = True   # Pause all automation
    send_notification: bool = True      # Send notification to user
    teleport_to_safety: bool = False    # Use random teleport (risky!)

    # Detection settings
    confidence: float = 0.80            # High confidence for safety


class EmergencyStopActivity(Activity):
    """
    Monitors for emergency conditions and stops bot if detected.

    This activity should run frequently (every 1-2 minutes) with HIGH priority.

    Process:
    1. Check shield status
    2. Check for incoming attacks
    3. Check for kingdom migration
    4. Check game connection
    5. If emergency detected:
       a. Log critical alert
       b. Pause all activities
       c. Optionally take safety actions
       d. Send notification

    Success Criteria:
    - Checked all emergency conditions
    - Taken appropriate action if emergency detected
    """

    def __init__(self, config: EmergencyStopConfig, adb: ADBConnection, screen: ScreenAnalyzer):
        super().__init__("Emergency Stop", config)
        self.adb = adb
        self.screen = screen
        self.config: EmergencyStopConfig = config

        self.emergency_active = False
        self.emergency_type = None
        self.last_check_time = 0

    def check_prerequisites(self) -> bool:
        """
        Emergency stop always runs - no prerequisites.
        """
        return True

    def execute(self) -> bool:
        """
        Execute emergency checks.

        Process:
        1. Check all emergency conditions
        2. If emergency detected, trigger stop
        3. Return status
        """
        self.logger.debug("Running emergency checks...")

        # Check shield status
        if self.config.monitor_shield:
            if self._check_shield_emergency():
                return self._trigger_emergency(EmergencyType.SHIELD_DOWN)

        # Check for incoming attacks
        if self.config.monitor_attacks:
            if self._check_attack_emergency():
                return self._trigger_emergency(EmergencyType.INCOMING_ATTACK)

        # Check kingdom migration
        if self.config.monitor_kingdom:
            if self._check_migration_emergency():
                return self._trigger_emergency(EmergencyType.KINGDOM_MIGRATION)

        # Check connection
        if self.config.monitor_connection:
            if self._check_connection_emergency():
                return self._trigger_emergency(EmergencyType.CONNECTION_LOST)

        # No emergencies detected
        self.emergency_active = False
        self.logger.debug("No emergencies detected")
        return True

    def verify_completion(self) -> bool:
        """Verify emergency check completed."""
        return True

    def _check_shield_emergency(self) -> bool:
        """
        Check if city shield is in emergency state.

        Returns:
            True if shield emergency detected
        """
        screenshot = self.adb.capture_screen_cached()

        # Look for shield icon in city view
        shield_icon = self.screen.find_template(
            screenshot,
            'templates/icons/shield.png',
            confidence=self.config.confidence
        )

        if shield_icon is None:
            # No shield detected - EMERGENCY!
            if self.config.stop_on_no_shield:
                self.logger.critical("NO SHIELD DETECTED!")
                return True
            else:
                self.logger.warning("No shield detected, but continue_without_shield enabled")
                return False

        # Shield exists, check duration using OCR
        shield_time = self._read_shield_time(screenshot, shield_icon)

        if shield_time is not None:
            if shield_time < self.config.min_shield_hours:
                self.logger.warning(
                    f"Shield time ({shield_time}h) below minimum ({self.config.min_shield_hours}h)"
                )
                return True

        return False

    def _check_attack_emergency(self) -> bool:
        """
        Check for incoming attacks.

        Returns:
            True if attack detected
        """
        screenshot = self.adb.capture_screen_cached()

        # Look for attack notification/indicator
        attack_indicators = [
            'templates/notifications/incoming_attack.png',
            'templates/icons/attack_warning.png',
            'templates/notifications/under_attack.png'
        ]

        for template in attack_indicators:
            attack = self.screen.find_template(
                screenshot,
                template,
                confidence=self.config.confidence
            )

            if attack:
                self.logger.critical("INCOMING ATTACK DETECTED!")
                return True

        return False

    def _check_migration_emergency(self) -> bool:
        """
        Check if kingdom migration occurred.

        This can happen if:
        - Player manually teleported
        - Someone used teleport item on player
        - Kingdom reset/migration event

        Returns:
            True if migration detected
        """
        screenshot = self.adb.capture_screen_cached()

        # Look for migration indicators
        migration_indicators = [
            'templates/notifications/migrated.png',
            'templates/screens/new_kingdom.png',
            'templates/notifications/teleported.png'
        ]

        for template in migration_indicators:
            migration = self.screen.find_template(
                screenshot,
                template,
                confidence=self.config.confidence
            )

            if migration:
                self.logger.critical("KINGDOM MIGRATION DETECTED!")
                return True

        return False

    def _check_connection_emergency(self) -> bool:
        """
        Check if game connection lost.

        Returns:
            True if connection lost
        """
        # Check if game is still running
        screenshot = self.adb.capture_screen_cached()

        if screenshot is None:
            self.logger.critical("CANNOT CAPTURE SCREENSHOT - CONNECTION LOST!")
            return True

        # Look for disconnection indicators
        disconnect_indicators = [
            'templates/notifications/disconnected.png',
            'templates/notifications/reconnecting.png',
            'templates/errors/connection_error.png'
        ]

        for template in disconnect_indicators:
            disconnect = self.screen.find_template(
                screenshot,
                template,
                confidence=0.70
            )

            if disconnect:
                self.logger.critical("GAME DISCONNECTED!")
                return True

        return False

    def _trigger_emergency(self, emergency_type: EmergencyType) -> bool:
        """
        Trigger emergency stop procedure.

        Args:
            emergency_type: Type of emergency detected

        Returns:
            False to signal activity failure (stops scheduler)
        """
        self.emergency_active = True
        self.emergency_type = emergency_type

        self.logger.critical("=" * 80)
        self.logger.critical(f"EMERGENCY STOP TRIGGERED: {emergency_type.value.upper()}")
        self.logger.critical("=" * 80)

        # Take emergency actions
        if self.config.pause_all_activities:
            self.logger.critical("Pausing all activities...")
            # The scheduler will handle pausing when this activity returns False

        if self.config.send_notification:
            self._send_notification(emergency_type)

        if self.config.teleport_to_safety and emergency_type == EmergencyType.INCOMING_ATTACK:
            self.logger.warning("Attempting emergency teleport...")
            self._emergency_teleport()

        # Return False to stop the scheduler
        return False

    def _send_notification(self, emergency_type: EmergencyType):
        """
        Send notification to user about emergency.

        This can be extended to send:
        - Email alerts
        - SMS alerts
        - Discord/Telegram notifications
        - Desktop notifications

        For now, just log prominently.
        """
        message = f"EMERGENCY: {emergency_type.value} detected! Bot stopped for safety."

        self.logger.critical(message)
        self.logger.critical("Manual intervention required to resume automation.")

        # TODO: Implement actual notification system
        # Could use:
        # - Windows toast notifications
        # - Email via SMTP
        # - Discord webhook
        # - Telegram bot API

    def _emergency_teleport(self):
        """
        Attempt emergency teleport to safety.

        WARNING: This is risky and may not work if:
        - No teleport items available
        - Already under attack
        - In combat
        """
        self.logger.warning("Emergency teleport feature not yet implemented")
        # TODO: Implement teleport logic
        # 1. Open items bag
        # 2. Find random teleport item
        # 3. Use teleport
        # 4. Confirm teleport

    def _read_shield_time(self, screenshot, shield_location: Tuple[int, int]) -> Optional[float]:
        """
        Read shield time from OCR.

        Args:
            screenshot: Screenshot image
            shield_location: (x, y) of shield icon

        Returns:
            Shield time in hours, or None if cannot read
        """
        x, y = shield_location

        # Define region near shield icon where time is displayed
        # Usually below or next to the shield icon
        time_region = screenshot[y + 10:y + 40, x - 50:x + 100]

        try:
            # Read text
            text = self.screen.read_text(time_region)

            # Parse time
            hours = self._parse_time_to_hours(text)

            return hours

        except Exception as e:
            self.logger.warning(f"Could not read shield time: {e}")
            return None

    def _parse_time_to_hours(self, text: str) -> float:
        """
        Parse time string to hours.

        Examples:
        "2h 30m" -> 2.5
        "45m" -> 0.75
        "1d 5h" -> 29.0
        "30s" -> 0.008
        """
        if not text:
            return 0.0

        import re

        hours = 0.0

        # Find days
        days_match = re.search(r'(\d+)d', text, re.IGNORECASE)
        if days_match:
            hours += int(days_match.group(1)) * 24

        # Find hours
        hours_match = re.search(r'(\d+)h', text, re.IGNORECASE)
        if hours_match:
            hours += int(hours_match.group(1))

        # Find minutes
        minutes_match = re.search(r'(\d+)m', text, re.IGNORECASE)
        if minutes_match:
            hours += int(minutes_match.group(1)) / 60.0

        # Find seconds
        seconds_match = re.search(r'(\d+)s', text, re.IGNORECASE)
        if seconds_match:
            hours += int(seconds_match.group(1)) / 3600.0

        return hours

    def is_emergency_active(self) -> bool:
        """Check if an emergency is currently active."""
        return self.emergency_active

    def get_emergency_type(self) -> Optional[EmergencyType]:
        """Get the type of emergency if active."""
        return self.emergency_type

    def clear_emergency(self):
        """Clear emergency state (for manual resume)."""
        self.logger.info("Emergency cleared manually")
        self.emergency_active = False
        self.emergency_type = None
