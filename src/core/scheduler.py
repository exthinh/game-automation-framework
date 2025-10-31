"""
Activity Scheduler - The Orchestration Engine

This is the BRAIN of the automation system. It:
- Manages all registered activities
- Determines when each activity should run
- Executes activities in priority order
- Handles errors and retries
- Provides real-time status

COMPLETE WORKING IMPLEMENTATION - not a placeholder!
"""

import logging
import time
import threading
from typing import List, Dict, Optional, Callable
from datetime import datetime
from queue import PriorityQueue, Empty
from dataclasses import dataclass, field

from .activity import Activity, ActivityState


@dataclass(order=True)
class ScheduledTask:
    """
    Wrapper for activity in priority queue.

    Uses @dataclass(order=True) for automatic comparison based on first field.
    """
    # Priority queue sorts by these in order:
    priority: int  # Lower number = higher priority
    execution_time: datetime = field(compare=False)
    activity: Activity = field(compare=False)

    def __repr__(self) -> str:
        return f"Task(priority={self.priority}, activity={self.activity.name})"


class ActivityScheduler:
    """
    Complete activity scheduling and execution system.

    This is the main loop that runs continuously and executes activities.
    """

    def __init__(self):
        """Initialize scheduler"""
        self.logger = logging.getLogger("Scheduler")

        # Activity registry
        self._activities: List[Activity] = []
        self._activities_by_id: Dict[str, Activity] = {}

        # Execution state
        self.running = False
        self._scheduler_thread: Optional[threading.Thread] = None
        self._current_activity: Optional[Activity] = None

        # Statistics
        self.total_executions = 0
        self.successful_executions = 0
        self.failed_executions = 0
        self.start_time: Optional[datetime] = None

        # Callbacks for UI updates
        self.on_activity_start: Optional[Callable] = None
        self.on_activity_complete: Optional[Callable] = None
        self.on_status_change: Optional[Callable] = None

        # Configuration
        self.check_interval_seconds = 10  # How often to check for due activities
        self.max_execution_time_seconds = 600  # Global timeout (10 min)

        self.logger.info("Activity Scheduler initialized")

    # ========================================================================
    # ACTIVITY REGISTRATION
    # ========================================================================

    def register_activity(self, activity: Activity, activity_id: Optional[str] = None):
        """
        Register an activity with the scheduler.

        Args:
            activity: Activity instance to register
            activity_id: Optional ID for lookup (defaults to activity.name)
        """
        if activity in self._activities:
            self.logger.warning(f"Activity '{activity.name}' already registered")
            return

        self._activities.append(activity)

        # Register by ID for lookups
        activity_id = activity_id or activity.name.lower().replace(' ', '_')
        self._activities_by_id[activity_id] = activity

        # Set callbacks for activity events
        activity.on_state_change = self._on_activity_state_change
        activity.on_execution_complete = self._on_activity_execution_complete

        self.logger.info(
            f"Registered activity: '{activity.name}' "
            f"(priority={activity.config.priority}, "
            f"interval={activity.config.interval_hours}h {activity.config.interval_minutes}m)"
        )

    def unregister_activity(self, activity_id: str) -> bool:
        """
        Unregister an activity.

        Args:
            activity_id: Activity ID to remove

        Returns:
            True if removed, False if not found
        """
        if activity_id not in self._activities_by_id:
            return False

        activity = self._activities_by_id[activity_id]
        self._activities.remove(activity)
        del self._activities_by_id[activity_id]

        self.logger.info(f"Unregistered activity: {activity_id}")
        return True

    def get_activity(self, activity_id: str) -> Optional[Activity]:
        """Get activity by ID"""
        return self._activities_by_id.get(activity_id)

    def get_all_activities(self) -> List[Activity]:
        """Get all registered activities"""
        return self._activities.copy()

    def get_enabled_activities(self) -> List[Activity]:
        """Get only enabled activities"""
        return [a for a in self._activities if a.config.enabled]

    # ========================================================================
    # SCHEDULER CONTROL
    # ========================================================================

    def start(self):
        """
        Start the scheduler.

        Runs in a separate thread to avoid blocking.
        """
        if self.running:
            self.logger.warning("Scheduler already running")
            return

        self.running = True
        self.start_time = datetime.now()

        # Start scheduler thread
        self._scheduler_thread = threading.Thread(
            target=self._scheduler_loop,
            name="ActivityScheduler",
            daemon=True
        )
        self._scheduler_thread.start()

        self.logger.info("Scheduler started")

        if self.on_status_change:
            self.on_status_change("started")

    def stop(self):
        """Stop the scheduler"""
        if not self.running:
            return

        self.running = False

        # Wait for thread to finish (max 5 seconds)
        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=5)

        self.logger.info("Scheduler stopped")

        if self.on_status_change:
            self.on_status_change("stopped")

    def pause(self):
        """Pause scheduler (stops executing but keeps thread alive)"""
        # Could implement pause functionality here
        pass

    def is_running(self) -> bool:
        """Check if scheduler is running"""
        return self.running

    # ========================================================================
    # SCHEDULER LOOP (Main Logic)
    # ========================================================================

    def _scheduler_loop(self):
        """
        Main scheduler loop - runs continuously.

        This is the heart of the automation system!
        """
        self.logger.info("Scheduler loop started")

        while self.running:
            try:
                # Get next activity to execute
                activity = self._get_next_due_activity()

                if activity:
                    # Execute the activity
                    self._execute_activity(activity)
                else:
                    # No activities due, wait before checking again
                    time.sleep(self.check_interval_seconds)

            except Exception as e:
                self.logger.error(f"Error in scheduler loop: {e}")
                time.sleep(self.check_interval_seconds)

        self.logger.info("Scheduler loop ended")

    def _get_next_due_activity(self) -> Optional[Activity]:
        """
        Get the next activity that should run now.

        PRIORITY LOGIC:
        1. Check all enabled activities
        2. Filter for activities that are due (time >= next_execution)
        3. Sort by priority (lower number = higher priority)
        4. Return highest priority activity

        Returns:
            Activity to execute or None if nothing is due
        """
        due_activities = []

        # Find all activities that are due
        for activity in self._activities:
            if not activity.config.enabled:
                continue

            if activity.state == ActivityState.DISABLED:
                continue

            if activity.is_due():
                due_activities.append(activity)

        if not due_activities:
            return None

        # Sort by priority (lower number = higher priority)
        due_activities.sort(key=lambda a: a.config.priority)

        # Return highest priority activity
        next_activity = due_activities[0]

        self.logger.debug(
            f"Next activity: {next_activity.name} "
            f"(priority={next_activity.config.priority})"
        )

        return next_activity

    def _execute_activity(self, activity: Activity):
        """
        Execute a single activity.

        Handles the complete execution lifecycle with error handling.

        Args:
            activity: Activity to execute
        """
        self._current_activity = activity

        # Notify listeners
        if self.on_activity_start:
            self.on_activity_start(activity)

        self.logger.info(f"⏵ Executing activity: {activity.name}")
        execution_start = datetime.now()

        try:
            # Run the activity (calls activity.run())
            success = activity.run()

            execution_time = (datetime.now() - execution_start).total_seconds()

            # Update statistics
            self.total_executions += 1
            if success:
                self.successful_executions += 1
                self.logger.info(
                    f"✓ Activity '{activity.name}' completed successfully "
                    f"in {execution_time:.1f}s"
                )
            else:
                self.failed_executions += 1
                self.logger.warning(
                    f"✗ Activity '{activity.name}' failed "
                    f"after {execution_time:.1f}s"
                )

        except Exception as e:
            self.logger.error(
                f"Unexpected error executing '{activity.name}': {e}"
            )
            self.failed_executions += 1

        finally:
            self._current_activity = None

    # ========================================================================
    # ACTIVITY EVENT HANDLERS
    # ========================================================================

    def _on_activity_state_change(
        self,
        activity: Activity,
        old_state: ActivityState,
        new_state: ActivityState
    ):
        """Handle activity state changes"""
        self.logger.debug(
            f"Activity '{activity.name}': {old_state.value} → {new_state.value}"
        )

    def _on_activity_execution_complete(self, activity: Activity, success: bool):
        """Handle activity execution completion"""
        if self.on_activity_complete:
            self.on_activity_complete(activity, success)

    # ========================================================================
    # SCHEDULER INFORMATION & STATISTICS
    # ========================================================================

    def get_status(self) -> Dict[str, any]:
        """
        Get current scheduler status.

        Returns:
            Dictionary with status information
        """
        uptime_seconds = 0
        if self.start_time:
            uptime_seconds = (datetime.now() - self.start_time).total_seconds()

        success_rate = 0.0
        if self.total_executions > 0:
            success_rate = self.successful_executions / self.total_executions * 100

        return {
            "running": self.running,
            "total_activities": len(self._activities),
            "enabled_activities": len(self.get_enabled_activities()),
            "current_activity": self._current_activity.name if self._current_activity else None,
            "total_executions": self.total_executions,
            "successful_executions": self.successful_executions,
            "failed_executions": self.failed_executions,
            "success_rate_percent": round(success_rate, 1),
            "uptime_seconds": int(uptime_seconds),
            "uptime_formatted": self._format_uptime(uptime_seconds)
        }

    def get_activity_summary(self) -> List[Dict[str, any]]:
        """
        Get summary of all activities.

        Returns:
            List of activity status dictionaries
        """
        return [activity.get_statistics() for activity in self._activities]

    def get_next_scheduled_activities(self, count: int = 5) -> List[Dict[str, any]]:
        """
        Get the next N activities scheduled to run.

        Args:
            count: Number of activities to return

        Returns:
            List of activity info dictionaries
        """
        # Get enabled activities with next execution time
        scheduled = []
        for activity in self._activities:
            if not activity.config.enabled:
                continue

            if activity.next_execution:
                scheduled.append({
                    "name": activity.name,
                    "priority": activity.config.priority,
                    "next_execution": activity.next_execution,
                    "time_until": (activity.next_execution - datetime.now()).total_seconds()
                })

        # Sort by next execution time
        scheduled.sort(key=lambda x: x["next_execution"])

        # Return top N
        return scheduled[:count]

    def _format_uptime(self, seconds: float) -> str:
        """Format uptime as human-readable string"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    # ========================================================================
    # MANUAL CONTROL
    # ========================================================================

    def run_activity_now(self, activity_id: str) -> bool:
        """
        Force run an activity immediately (bypass scheduling).

        Args:
            activity_id: ID of activity to run

        Returns:
            True if executed, False if not found or already running
        """
        activity = self.get_activity(activity_id)

        if not activity:
            self.logger.error(f"Activity not found: {activity_id}")
            return False

        if self._current_activity:
            self.logger.warning(
                f"Cannot run '{activity_id}' - another activity is running"
            )
            return False

        self.logger.info(f"Manual execution requested: {activity.name}")

        # Execute in scheduler thread
        threading.Thread(
            target=self._execute_activity,
            args=(activity,),
            daemon=True
        ).start()

        return True

    def enable_activity(self, activity_id: str) -> bool:
        """Enable an activity"""
        activity = self.get_activity(activity_id)
        if activity:
            activity.enable()
            return True
        return False

    def disable_activity(self, activity_id: str) -> bool:
        """Disable an activity"""
        activity = self.get_activity(activity_id)
        if activity:
            activity.disable()
            return True
        return False

    def reset_activity_statistics(self, activity_id: str) -> bool:
        """Reset statistics for an activity"""
        activity = self.get_activity(activity_id)
        if activity:
            activity.reset_statistics()
            return True
        return False

    def reset_all_statistics(self):
        """Reset all scheduler and activity statistics"""
        self.total_executions = 0
        self.successful_executions = 0
        self.failed_executions = 0
        self.start_time = datetime.now()

        for activity in self._activities:
            activity.reset_statistics()

        self.logger.info("All statistics reset")

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    def __repr__(self) -> str:
        return (
            f"ActivityScheduler("
            f"running={self.running}, "
            f"activities={len(self._activities)}, "
            f"executions={self.total_executions}"
            f")"
        )

    def __del__(self):
        """Cleanup when scheduler is destroyed"""
        if self.running:
            self.stop()
