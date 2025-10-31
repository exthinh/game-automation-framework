"""
Game Automation Framework - Main Entry Point

This demonstrates the COMPLETE WORKING SYSTEM with:
- ADB connection to emulator
- Configuration loading
- Activity registration
- Scheduler running activities
- Real automation!

USAGE:
    python main.py                  # Run with default settings
    python main.py --game rok       # Specify game
    python main.py --test-adb       # Test ADB connection only
    python main.py --list           # List activities
"""

import sys
import logging
import argparse
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.adb import ADBConnection, find_bluestacks_device
from src.core.screen import ScreenAnalyzer
from src.core.config import ConfigManager
from src.core.scheduler import ActivityScheduler
from src.core.activity import ActivityConfig

# Activities
from src.activities.base.alliance_help import create_alliance_help_activity


def setup_logging(level=logging.INFO):
    """Setup logging configuration"""
    logging.basicConfig(
        level=level,
        format='[%(asctime)s] %(levelname)-8s %(name)-15s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Reduce noise from some modules
    logging.getLogger('PIL').setLevel(logging.WARNING)


def test_adb_connection():
    """Test ADB connection to emulator"""
    print("\n" + "="*60)
    print("Testing ADB Connection")
    print("="*60 + "\n")

    # Initialize ADB
    adb = ADBConnection()

    # Try to find BlueStacks
    print("Looking for BlueStacks emulator...")
    device_id = find_bluestacks_device()

    if device_id:
        print(f"✓ Found BlueStacks: {device_id}")
        adb.device_id = device_id
    else:
        print("✗ BlueStacks not found - trying to connect...")
        if not adb.connect():
            print("✗ Failed to connect to emulator")
            return False

    # Test screenshot
    print("\nTesting screenshot capture...")
    screenshot = adb.capture_screen()

    if screenshot is not None:
        print(f"✓ Screenshot captured: {screenshot.shape}")

        # Save test screenshot
        adb.save_screenshot("test_screenshot.png")
        print("✓ Screenshot saved to test_screenshot.png")

        # Get resolution
        resolution = adb.get_screen_resolution()
        if resolution:
            print(f"✓ Screen resolution: {resolution[0]}x{resolution[1]}")

        return True
    else:
        print("✗ Failed to capture screenshot")
        return False


def list_activities(game: str = "rok"):
    """List available activities"""
    print("\n" + "="*60)
    print(f"Available Activities for {game.upper()}")
    print("="*60 + "\n")

    config_mgr = ConfigManager()
    activities_data = config_mgr.load_activities(game)

    for idx, activity in enumerate(activities_data.get('activities', []), 1):
        enabled_status = "✓ ENABLED" if activity['enabled'] else "✗ disabled"
        print(f"{idx}. {activity['name']:<25} {enabled_status}")
        print(f"   Priority: {activity['priority']}")
        print(f"   Interval: {activity['interval_hours']}h {activity['interval_minutes']}m")
        print()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Game Automation Framework")
    parser.add_argument('--game', default='rok', choices=['rok', 'cod'],
                       help='Game to automate (rok or cod)')
    parser.add_argument('--test-adb', action='store_true',
                       help='Test ADB connection and exit')
    parser.add_argument('--list', action='store_true',
                       help='List available activities and exit')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug logging')
    parser.add_argument('--duration', type=int, default=0,
                       help='Run for N seconds then stop (0 = run forever)')

    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    setup_logging(log_level)

    logger = logging.getLogger("Main")

    # Handle special modes
    if args.test_adb:
        test_adb_connection()
        return

    if args.list:
        list_activities(args.game)
        return

    # ========================================================================
    # MAIN AUTOMATION FLOW
    # ========================================================================

    print("\n" + "="*60)
    print("Game Automation Framework")
    print("="*60)
    print(f"Game: {args.game.upper()}")
    print(f"Mode: {'Debug' if args.debug else 'Normal'}")
    print("="*60 + "\n")

    try:
        # ====================================================================
        # STEP 1: Initialize ADB Connection
        # ====================================================================
        logger.info("Initializing ADB connection...")
        adb = ADBConnection()

        # Auto-detect BlueStacks
        device_id = find_bluestacks_device()
        if device_id:
            logger.info(f"Found BlueStacks: {device_id}")
            adb.device_id = device_id
        else:
            logger.info("Attempting to connect to emulator...")
            if not adb.connect():
                logger.error("Failed to connect to emulator!")
                print("\n⚠️  Make sure BlueStacks is running and ADB is enabled")
                return 1

        # Verify connection
        screenshot = adb.capture_screen()
        if screenshot is None:
            logger.error("Cannot capture screenshots!")
            return 1

        logger.info("✓ ADB connection successful")

        # ====================================================================
        # STEP 2: Initialize Screen Analyzer
        # ====================================================================
        logger.info("Initializing screen analyzer...")
        screen = ScreenAnalyzer(templates_dir="templates")
        logger.info("✓ Screen analyzer ready")

        # ====================================================================
        # STEP 3: Load Configuration
        # ====================================================================
        logger.info("Loading configuration...")
        config_mgr = ConfigManager(config_dir="config")

        # Load accounts
        accounts = config_mgr.load_accounts()
        if not accounts:
            logger.warning("No accounts configured")
        else:
            logger.info(f"Loaded {len(accounts)} account(s)")

        # Load activities
        activities_data = config_mgr.load_activities(args.game)
        logger.info(f"Loaded {len(activities_data.get('activities', []))} activity configurations")

        # Load settings
        settings = config_mgr.load_settings()
        logger.info("✓ Configuration loaded")

        # ====================================================================
        # STEP 4: Create Activity Instances
        # ====================================================================
        logger.info("Creating activity instances...")

        activities = []

        # For now, just create Alliance Help as example
        # In full implementation, we'd create all enabled activities

        for activity_data in activities_data.get('activities', []):
            if activity_data['id'] == 'alliance_help' and activity_data['enabled']:
                # Create configuration
                config = ActivityConfig(
                    enabled=activity_data['enabled'],
                    interval_hours=activity_data['interval_hours'],
                    interval_minutes=activity_data['interval_minutes'],
                    priority=activity_data['priority'],
                    max_retries=activity_data.get('max_retries', 3),
                    retry_delay_minutes=activity_data.get('retry_delay_minutes', 5),
                    max_execution_seconds=activity_data.get('max_execution_seconds', 120),
                    parameters=activity_data.get('parameters', {})
                )

                # Create activity
                activity = create_alliance_help_activity(
                    adb_connection=adb,
                    screen_analyzer=screen,
                    interval_minutes=config.interval_minutes,
                    priority=config.priority,
                    help_all=config.parameters.get('help_all', True)
                )

                activities.append(activity)
                logger.info(f"Created activity: {activity.name}")

        if not activities:
            logger.warning("No activities enabled!")
            print("\n⚠️  No activities are enabled in config/activities_rok.json")
            print("   Enable at least one activity and try again")
            return 1

        logger.info(f"✓ Created {len(activities)} activity instance(s)")

        # ====================================================================
        # STEP 5: Initialize Scheduler
        # ====================================================================
        logger.info("Initializing scheduler...")
        scheduler = ActivityScheduler()

        # Register activities
        for activity in activities:
            scheduler.register_activity(activity)

        logger.info("✓ Scheduler initialized")

        # ====================================================================
        # STEP 6: Start Scheduler
        # ====================================================================
        print("\n" + "="*60)
        print("Starting Automation")
        print("="*60)
        print("\n✓ All systems initialized")
        print("✓ Scheduler starting...\n")

        scheduler.start()

        # Show status
        print("🤖 Automation is running!")
        print("\nRegistered Activities:")
        for activity in activities:
            status = "ENABLED" if activity.config.enabled else "disabled"
            print(f"  - {activity.name:<25} [{status}]")
            print(f"    Interval: {activity.config.interval_hours}h {activity.config.interval_minutes}m")
            print(f"    Priority: {activity.config.priority}")

        print("\nPress Ctrl+C to stop\n")
        print("-" * 60)

        # ====================================================================
        # STEP 7: Run Until Stopped
        # ====================================================================
        start_time = time.time()

        try:
            while True:
                time.sleep(5)  # Check every 5 seconds

                # Show status every 30 seconds
                if int(time.time() - start_time) % 30 == 0:
                    status = scheduler.get_status()
                    print(f"\n[Status] Running: {status['running']}, "
                          f"Executions: {status['total_executions']}, "
                          f"Success: {status['successful_executions']}, "
                          f"Failed: {status['failed_executions']}")

                    # Show next scheduled activities
                    next_activities = scheduler.get_next_scheduled_activities(3)
                    if next_activities:
                        print("\nNext scheduled:")
                        for act in next_activities:
                            time_until = int(act['time_until'])
                            if time_until < 0:
                                time_str = "NOW"
                            elif time_until < 60:
                                time_str = f"{time_until}s"
                            else:
                                time_str = f"{time_until//60}m"
                            print(f"  - {act['name']}: {time_str}")

                # Check duration limit
                if args.duration > 0 and (time.time() - start_time) >= args.duration:
                    logger.info(f"Duration limit reached ({args.duration}s)")
                    break

        except KeyboardInterrupt:
            print("\n\n⏸️  Stopping automation...\n")

        # ====================================================================
        # STEP 8: Cleanup
        # ====================================================================
        scheduler.stop()

        # Final statistics
        print("\n" + "="*60)
        print("Final Statistics")
        print("="*60)

        status = scheduler.get_status()
        print(f"\nTotal Executions: {status['total_executions']}")
        print(f"Successful: {status['successful_executions']}")
        print(f"Failed: {status['failed_executions']}")
        print(f"Success Rate: {status['success_rate_percent']}%")
        print(f"Uptime: {status['uptime_formatted']}")

        print("\n" + "="*60)
        print("Automation stopped")
        print("="*60 + "\n")

        return 0

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
