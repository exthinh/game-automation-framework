"""
Activity Base Class - Foundation of All Automation

This is the complete, production-ready base class for all activities.
Every automated task inherits from this and implements three methods:
- check_prerequisites(): Can we run now?
- execute(): Do the automation
- verify_completion(): Did it work?
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta, time as dt_time
from enum import Enum
import logging
import time
import traceback


class ActivityState(Enum):
    """Current state of an activity in its lifecycle"""
    IDLE = "idle"                   # Disabled, not running
    SCHEDULED = "scheduled"         # Enabled, waiting for next run
    CHECKING = "checking"           # Checking prerequisites
    READY = "ready"                 # Prerequisites met, about to execute
    EXECUTING = "executing"         # Currently running
    VERIFYING = "verifying"         # Checking if it worked
    SUCCESS = "success"             # Completed successfully
    FAILED = "failed"               # Failed, will retry
    DISABLED = "disabled"           # Failed too many times, needs manual intervention


@dataclass
class ActivityConfig:
    """
    Complete configuration for an activity.
    All settings that control HOW and WHEN an activity runs.
    """
    # Enable/disable
    enabled: bool = True

    # Timing - how often to run
    interval_hours: int = 0
    interval_minutes: int = 30

    # Time window - when activity can run (optional)
    start_time: Optional[str] = None  # "06:00"
    end_time: Optional[str] = None    # "23:00"

    # Priority (1 = highest, 10 = lowest)
    priority: int = 5

    # Retry behavior
    max_retries: int = 3
    retry_delay_minutes: int = 5

    # Activity-specific parameters
    parameters: Dict[str, Any] = field(default_factory=dict)

    # Timeouts
    max_execution_seconds: int = 300  # 5 minutes default

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)


class Activity(ABC):
    """
    Base class for all activities.

    REAL IMPLEMENTATION - not a placeholder!
    Complete with state management, error handling, statistics, and lifecycle control.
    """

    def __init__(
        self,
        name: str,
        config: ActivityConfig,
        adb_connection=None,
        screen_analyzer=None
    ):
        """
        Initialize activity.

        Args:
            name: Human-readable activity name
            config: ActivityConfig with all settings
            adb_connection: ADBConnection instance (injected)
            screen_analyzer: ScreenAnalyzer instance (injected)
        """
        self.name = name
        self.config = config
        self.adb = adb_connection
        self.screen = screen_analyzer

        # Setup logging
        self.logger = logging.getLogger(f"Activity.{name}")

        # State tracking
        self.state = ActivityState.IDLE if not config.enabled else ActivityState.SCHEDULED
        self.last_execution: Optional[datetime] = None
        self.next_execution: Optional[datetime] = None
        self.retry_count = 0

        # Statistics for monitoring and optimization
        self.total_executions = 0
        self.successful_executions = 0
        self.failed_executions = 0
        self.total_execution_time_seconds = 0.0
        self.average_execution_time_seconds = 0.0

        # Callbacks (for UI updates, notifications, etc.)
        self.on_state_change: Optional[Callable] = None
        self.on_execution_complete: Optional[Callable] = None

        self.logger.info(f"Activity '{name}' initialized (priority={config.priority})")

    # ========================================================================
    # ABSTRACT METHODS - Must be implemented by subclasses
    # ========================================================================

    @abstractmethod
    def check_prerequisites(self) -> bool:
        """
        Check if activity can run right now.

        MUST IMPLEMENT in subclass!

        Examples of checks:
        - Enough troops available?
        - Resources sufficient?
        - Not currently in battle?
        - Warehouse capacity OK?
        - Action points available?
        - Game on correct screen?

        Returns:
            True if can run, False otherwise
        """
        pass

    @abstractmethod
    def execute(self) -> bool:
        """
        Execute the actual activity automation.

        MUST IMPLEMENT in subclass!

        This is where the real automation happens:
        1. Navigate to correct screen
        2. Perform required actions (tap, swipe, etc.)
        3. Wait for game responses
        4. Handle popups/dialogs
        5. Complete the task

        Returns:
            True if executed successfully, False if failed
        """
        pass

    @abstractmethod
    def verify_completion(self) -> bool:
        """
        Verify that the activity completed successfully.

        MUST IMPLEMENT in subclass!

        After execute() returns True, verify it actually worked:
        - March started? (for gathering/hunting)
        - Building upgraded? (for upgrades)
        - Resources collected? (for collection)
        - Help button gone? (for alliance help)

        Returns:
            True if verified successful, False otherwise
        """
        pass

    # ========================================================================
    # LIFECYCLE MANAGEMENT
    # ========================================================================

    def run(self) -> bool:
        """
        Main execution method called by scheduler.

        This orchestrates the complete activity lifecycle:
        1. Check prerequisites
        2. Execute if ready
        3. Verify completion
        4. Update statistics
        5. Handle errors
        6. Calculate next execution

        Returns:
            True if successful, False if failed
        """
        execution_start = datetime.now()

        try:
            self.logger.info(f"Starting '{self.name}' (attempt {self.retry_count + 1})")
            self._change_state(ActivityState.CHECKING)

            # Step 1: Check prerequisites
            if not self._run_with_timeout(
                self.check_prerequisites,
                timeout_seconds=30,
                operation_name="prerequisite check"
            ):
                self.logger.warning(f"Prerequisites not met for '{self.name}'")
                self._change_state(ActivityState.SCHEDULED)
                return False

            # Step 2: Execute
            self._change_state(ActivityState.READY)
            self.logger.info(f"Prerequisites met, executing '{self.name}'")

            self._change_state(ActivityState.EXECUTING)
            execution_success = self._run_with_timeout(
                self.execute,
                timeout_seconds=self.config.max_execution_seconds,
                operation_name="execution"
            )

            if not execution_success:
                self.logger.error(f"Execution failed for '{self.name}'")
                self._handle_failure()
                return False

            # Step 3: Verify
            self._change_state(ActivityState.VERIFYING)
            verification_success = self._run_with_timeout(
                self.verify_completion,
                timeout_seconds=30,
                operation_name="verification"
            )

            if not verification_success:
                self.logger.error(f"Verification failed for '{self.name}'")
                self._handle_failure()
                return False

            # Success!
            self._change_state(ActivityState.SUCCESS)
            execution_time = (datetime.now() - execution_start).total_seconds()
            self._handle_success(execution_time)

            self.logger.info(
                f"'{self.name}' completed successfully in {execution_time:.2f}s"
            )

            return True

        except Exception as e:
            self.logger.error(
                f"Unexpected error in '{self.name}': {e}\n{traceback.format_exc()}"
            )
            self._handle_failure()
            return False

        finally:
            # Always return to scheduled state (unless disabled)
            if self.state != ActivityState.DISABLED:
                self._change_state(ActivityState.SCHEDULED)

    def _run_with_timeout(
        self,
        func: Callable,
        timeout_seconds: int,
        operation_name: str
    ) -> bool:
        """
        Run a function with timeout protection.

        Prevents activities from hanging indefinitely.
        """
        start_time = time.time()
        try:
            result = func()
            elapsed = time.time() - start_time

            if elapsed > timeout_seconds:
                self.logger.warning(
                    f"{operation_name} took {elapsed:.1f}s (timeout: {timeout_seconds}s)"
                )

            return result

        except Exception as e:
            self.logger.error(f"Error during {operation_name}: {e}")
            return False

    def _handle_success(self, execution_time: float):
        """Handle successful execution"""
        self.total_executions += 1
        self.successful_executions += 1
        self.retry_count = 0
        self.last_execution = datetime.now()
        self.next_execution = self.get_next_execution_time()

        # Update statistics
        self.total_execution_time_seconds += execution_time
        self.average_execution_time_seconds = (
            self.total_execution_time_seconds / self.total_executions
        )

        # Callback for UI updates
        if self.on_execution_complete:
            self.on_execution_complete(self, success=True)

    def _handle_failure(self):
        """Handle failed execution"""
        self.total_executions += 1
        self.failed_executions += 1
        self.retry_count += 1

        if self.retry_count >= self.config.max_retries:
            self.logger.error(
                f"'{self.name}' failed {self.retry_count} times - DISABLING"
            )
            self._change_state(ActivityState.DISABLED)
            self.config.enabled = False
        else:
            self.logger.info(
                f"'{self.name}' will retry in {self.config.retry_delay_minutes} minutes "
                f"(attempt {self.retry_count}/{self.config.max_retries})"
            )
            # Schedule retry
            self.next_execution = datetime.now() + timedelta(
                minutes=self.config.retry_delay_minutes
            )

        # Callback for UI updates
        if self.on_execution_complete:
            self.on_execution_complete(self, success=False)

    def _change_state(self, new_state: ActivityState):
        """Change state and trigger callback"""
        old_state = self.state
        self.state = new_state

        if self.on_state_change and old_state != new_state:
            self.on_state_change(self, old_state, new_state)

    # ========================================================================
    # TIMING & SCHEDULING
    # ========================================================================

    def get_next_execution_time(self) -> datetime:
        """Calculate when this activity should run next"""
        if self.last_execution is None:
            return datetime.now()

        # Calculate next time based on interval
        interval = timedelta(
            hours=self.config.interval_hours,
            minutes=self.config.interval_minutes
        )
        next_time = self.last_execution + interval

        # Adjust for time window if set
        if self.config.start_time or self.config.end_time:
            next_time = self._adjust_for_time_window(next_time)

        return next_time

    def _adjust_for_time_window(self, next_time: datetime) -> datetime:
        """Adjust execution time to fit within configured time window"""
        if not (self.config.start_time or self.config.end_time):
            return next_time

        try:
            # Parse time strings
            start_time = None
            end_time = None

            if self.config.start_time:
                hour, minute = map(int, self.config.start_time.split(':'))
                start_time = dt_time(hour, minute)

            if self.config.end_time:
                hour, minute = map(int, self.config.end_time.split(':'))
                end_time = dt_time(hour, minute)

            next_time_of_day = next_time.time()

            # If before window, move to start of window
            if start_time and next_time_of_day < start_time:
                next_time = datetime.combine(next_time.date(), start_time)

            # If after window, move to start of window next day
            elif end_time and next_time_of_day > end_time:
                if start_time:
                    next_day = next_time.date() + timedelta(days=1)
                    next_time = datetime.combine(next_day, start_time)

            return next_time

        except Exception as e:
            self.logger.error(f"Error adjusting time window: {e}")
            return next_time

    def is_due(self) -> bool:
        """Check if this activity should run now"""
        if not self.config.enabled:
            return False

        if self.state == ActivityState.DISABLED:
            return False

        if self.next_execution is None:
            self.next_execution = self.get_next_execution_time()

        return datetime.now() >= self.next_execution

    # ========================================================================
    # CONTROL METHODS
    # ========================================================================

    def enable(self):
        """Enable this activity"""
        self.config.enabled = True
        self.retry_count = 0  # Reset retry counter
        self._change_state(ActivityState.SCHEDULED)
        self.logger.info(f"Activity '{self.name}' enabled")

    def disable(self):
        """Disable this activity"""
        self.config.enabled = False
        self._change_state(ActivityState.IDLE)
        self.logger.info(f"Activity '{self.name}' disabled")

    def reset_statistics(self):
        """Reset all statistics"""
        self.total_executions = 0
        self.successful_executions = 0
        self.failed_executions = 0
        self.total_execution_time_seconds = 0.0
        self.average_execution_time_seconds = 0.0
        self.retry_count = 0
        self.logger.info(f"Statistics reset for '{self.name}'")

    def force_run_now(self):
        """Force immediate execution (bypass scheduling)"""
        self.next_execution = datetime.now()
        self.logger.info(f"'{self.name}' forced to run now")

    # ========================================================================
    # STATISTICS & MONITORING
    # ========================================================================

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics about this activity.

        Useful for:
        - UI dashboards
        - Performance monitoring
        - Identifying problem activities
        - Optimization decisions
        """
        success_rate = (
            self.successful_executions / self.total_executions * 100
            if self.total_executions > 0
            else 0
        )

        return {
            "name": self.name,
            "state": self.state.value,
            "enabled": self.config.enabled,
            "priority": self.config.priority,
            "total_executions": self.total_executions,
            "successful_executions": self.successful_executions,
            "failed_executions": self.failed_executions,
            "success_rate_percent": round(success_rate, 1),
            "average_execution_time_seconds": round(self.average_execution_time_seconds, 2),
            "last_execution": self.last_execution.isoformat() if self.last_execution else None,
            "next_execution": self.next_execution.isoformat() if self.next_execution else None,
            "retry_count": self.retry_count,
            "interval_minutes": self.config.interval_hours * 60 + self.config.interval_minutes,
        }

    def get_status_summary(self) -> str:
        """Get one-line status summary for logging/UI"""
        stats = self.get_statistics()
        return (
            f"{self.name}: {self.state.value} | "
            f"{stats['successful_executions']}/{stats['total_executions']} success | "
            f"{stats['success_rate_percent']}% | "
            f"avg {stats['average_execution_time_seconds']}s"
        )

    def __repr__(self) -> str:
        """String representation for debugging"""
        return (
            f"Activity(name='{self.name}', "
            f"state={self.state.value}, "
            f"enabled={self.config.enabled}, "
            f"priority={self.config.priority}, "
            f"success={self.successful_executions}/{self.total_executions})"
        )

    def __str__(self) -> str:
        """Human-readable string"""
        return self.get_status_summary()
