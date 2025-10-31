"""
Configuration Manager - Complete JSON Configuration System

Handles ALL configuration loading, saving, validation, and hot-reload.
REAL IMPLEMENTATION - fully functional with error handling.

Manages:
- Account configurations (accounts.json)
- Activity configurations (activities_rok.json, activities_cod.json)
- Application settings (settings.json)
- Hot-reload support (auto-detect file changes)
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
import time
import os


@dataclass
class AccountConfig:
    """Complete account configuration"""
    account_id: str
    account_name: str
    server_name: str
    game: str  # "rok" or "cod"
    device_id: Optional[str] = None
    enabled: bool = True
    notes: str = ""

    # Optional credentials (if needed)
    username: Optional[str] = None
    password: Optional[str] = None  # Should be encrypted in production

    # Metadata
    last_active: Optional[str] = None
    created_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'AccountConfig':
        """Create from dictionary"""
        return AccountConfig(**data)


@dataclass
class EmulatorConfig:
    """Emulator connection settings"""
    emulator_type: str = "BlueStacks"
    adb_host: str = "127.0.0.1"
    adb_port: int = 5555
    screen_resolution: str = "1920x1080"
    dpi: int = 240
    auto_detect: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AppSettings:
    """Application-wide settings"""
    # General
    app_version: str = "1.0.0"
    language: str = "en"
    log_level: str = "INFO"
    auto_start: bool = False
    minimize_to_tray: bool = True

    # Randomization (anti-detection)
    randomization_enabled: bool = True
    min_delay_ms: int = 500
    max_delay_ms: int = 2000
    click_variance_px: int = 5

    # Performance
    screenshot_cache_duration_seconds: float = 0.5
    max_parallel_activities: int = 1
    activity_timeout_seconds: int = 300

    # Notifications
    notifications_enabled: bool = True
    notify_on_error: bool = True
    notify_on_complete: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ConfigManager:
    """
    Complete configuration management system.

    Handles loading, saving, validation, and hot-reload of ALL configuration files.
    """

    def __init__(self, config_dir: str = "config"):
        """
        Initialize configuration manager.

        Args:
            config_dir: Directory containing config files
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True, parents=True)

        self.logger = logging.getLogger("Config")

        # Configuration files
        self.accounts_file = self.config_dir / "accounts.json"
        self.settings_file = self.config_dir / "settings.json"
        self.activities_rok_file = self.config_dir / "activities_rok.json"
        self.activities_cod_file = self.config_dir / "activities_cod.json"

        # File modification tracking for hot-reload
        self._file_mtimes: Dict[Path, float] = {}

        # In-memory configuration cache
        self._accounts: List[AccountConfig] = []
        self._settings: AppSettings = AppSettings()
        self._activities_cache: Dict[str, Dict[str, Any]] = {}

        self.logger.info(f"Config Manager initialized (dir: {self.config_dir})")

    # ========================================================================
    # ACCOUNTS CONFIGURATION
    # ========================================================================

    def load_accounts(self) -> List[AccountConfig]:
        """
        Load all account configurations.

        Returns:
            List of AccountConfig objects
        """
        if not self.accounts_file.exists():
            self.logger.warning("No accounts.json file found - creating default")
            self._create_default_accounts_file()
            return []

        try:
            with open(self.accounts_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            accounts = []
            for acc_data in data.get('accounts', []):
                try:
                    account = AccountConfig.from_dict(acc_data)
                    accounts.append(account)
                except Exception as e:
                    self.logger.error(f"Error parsing account {acc_data.get('account_id')}: {e}")

            self._accounts = accounts
            self._update_mtime(self.accounts_file)
            self.logger.info(f"Loaded {len(accounts)} accounts")

            return accounts

        except Exception as e:
            self.logger.error(f"Error loading accounts: {e}")
            return []

    def save_accounts(self, accounts: List[AccountConfig]) -> bool:
        """
        Save account configurations.

        Args:
            accounts: List of AccountConfig to save

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            data = {
                'accounts': [acc.to_dict() for acc in accounts],
                'emulator': EmulatorConfig().to_dict(),
                'last_updated': datetime.now().isoformat()
            }

            with open(self.accounts_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            self._accounts = accounts
            self._update_mtime(self.accounts_file)
            self.logger.info(f"Saved {len(accounts)} accounts")

            return True

        except Exception as e:
            self.logger.error(f"Error saving accounts: {e}")
            return False

    def add_account(self, account: AccountConfig) -> bool:
        """Add new account"""
        accounts = self.load_accounts()
        accounts.append(account)
        return self.save_accounts(accounts)

    def remove_account(self, account_id: str) -> bool:
        """Remove account by ID"""
        accounts = self.load_accounts()
        accounts = [acc for acc in accounts if acc.account_id != account_id]
        return self.save_accounts(accounts)

    def get_account(self, account_id: str) -> Optional[AccountConfig]:
        """Get specific account by ID"""
        accounts = self.load_accounts()
        for account in accounts:
            if account.account_id == account_id:
                return account
        return None

    def get_enabled_accounts(self) -> List[AccountConfig]:
        """Get only enabled accounts"""
        accounts = self.load_accounts()
        return [acc for acc in accounts if acc.enabled]

    # ========================================================================
    # ACTIVITIES CONFIGURATION
    # ========================================================================

    def load_activities(self, game: str) -> Dict[str, Any]:
        """
        Load activity configurations for a specific game.

        Args:
            game: Game identifier ("rok" or "cod")

        Returns:
            Dictionary with activity configurations
        """
        if game.lower() not in ['rok', 'cod']:
            self.logger.error(f"Invalid game: {game}")
            return {}

        filename = f"activities_{game.lower()}.json"
        filepath = self.config_dir / filename

        # Check cache first
        if filepath in self._activities_cache:
            if not self._file_changed(filepath):
                return self._activities_cache[filepath]

        if not filepath.exists():
            self.logger.warning(f"No {filename} found - creating default")
            self._create_default_activities_file(game.lower())
            return {"activities": []}

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self._activities_cache[filepath] = data
            self._update_mtime(filepath)
            self.logger.info(f"Loaded activities for {game.upper()}")

            return data

        except Exception as e:
            self.logger.error(f"Error loading activities for {game}: {e}")
            return {}

    def save_activities(self, game: str, activities_data: Dict[str, Any]) -> bool:
        """
        Save activity configurations.

        Args:
            game: Game identifier ("rok" or "cod")
            activities_data: Full activities configuration dictionary

        Returns:
            True if saved successfully
        """
        if game.lower() not in ['rok', 'cod']:
            self.logger.error(f"Invalid game: {game}")
            return False

        filename = f"activities_{game.lower()}.json"
        filepath = self.config_dir / filename

        try:
            # Add metadata
            activities_data['last_updated'] = datetime.now().isoformat()
            activities_data['game'] = game.upper()

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(activities_data, f, indent=2, ensure_ascii=False)

            self._activities_cache[filepath] = activities_data
            self._update_mtime(filepath)
            self.logger.info(f"Saved activities for {game.upper()}")

            return True

        except Exception as e:
            self.logger.error(f"Error saving activities: {e}")
            return False

    # ========================================================================
    # APPLICATION SETTINGS
    # ========================================================================

    def load_settings(self) -> AppSettings:
        """
        Load application settings.

        Returns:
            AppSettings object
        """
        if not self.settings_file.exists():
            self.logger.warning("No settings.json found - creating default")
            self._create_default_settings_file()
            return AppSettings()

        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            settings = AppSettings(**data.get('app', {}))
            self._settings = settings
            self._update_mtime(self.settings_file)
            self.logger.info("Loaded application settings")

            return settings

        except Exception as e:
            self.logger.error(f"Error loading settings: {e}")
            return AppSettings()

    def save_settings(self, settings: AppSettings) -> bool:
        """
        Save application settings.

        Args:
            settings: AppSettings object to save

        Returns:
            True if saved successfully
        """
        try:
            data = {
                'app': settings.to_dict(),
                'last_updated': datetime.now().isoformat()
            }

            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            self._settings = settings
            self._update_mtime(self.settings_file)
            self.logger.info("Saved application settings")

            return True

        except Exception as e:
            self.logger.error(f"Error saving settings: {e}")
            return False

    # ========================================================================
    # HOT-RELOAD SUPPORT
    # ========================================================================

    def check_for_updates(self) -> List[str]:
        """
        Check if any configuration files have been modified.

        Returns:
            List of changed file names
        """
        changed_files = []

        for filepath in [self.accounts_file, self.settings_file,
                        self.activities_rok_file, self.activities_cod_file]:
            if filepath.exists() and self._file_changed(filepath):
                changed_files.append(filepath.name)

        return changed_files

    def reload_all(self) -> bool:
        """
        Reload all configuration files.

        Returns:
            True if all reloaded successfully
        """
        try:
            self.load_accounts()
            self.load_settings()
            self.load_activities('rok')
            self.load_activities('cod')

            self.logger.info("All configurations reloaded")
            return True

        except Exception as e:
            self.logger.error(f"Error reloading configurations: {e}")
            return False

    def _file_changed(self, filepath: Path) -> bool:
        """Check if file has been modified since last load"""
        if not filepath.exists():
            return False

        current_mtime = filepath.stat().st_mtime
        last_mtime = self._file_mtimes.get(filepath, 0)

        return current_mtime > last_mtime

    def _update_mtime(self, filepath: Path):
        """Update stored modification time for file"""
        if filepath.exists():
            self._file_mtimes[filepath] = filepath.stat().st_mtime

    # ========================================================================
    # DEFAULT FILE CREATION
    # ========================================================================

    def _create_default_accounts_file(self):
        """Create default accounts.json"""
        default = {
            "accounts": [
                {
                    "account_id": "example_001",
                    "account_name": "Example Account",
                    "server_name": "Server 1234",
                    "game": "rok",
                    "device_id": "emulator-5555",
                    "enabled": True,
                    "notes": "This is an example account. Edit or delete this.",
                    "username": None,
                    "password": None,
                    "last_active": None,
                    "created_at": datetime.now().isoformat()
                }
            ],
            "emulator": EmulatorConfig().to_dict(),
            "created_at": datetime.now().isoformat()
        }

        with open(self.accounts_file, 'w', encoding='utf-8') as f:
            json.dump(default, f, indent=2, ensure_ascii=False)

        self.logger.info("Created default accounts.json")

    def _create_default_settings_file(self):
        """Create default settings.json"""
        default = {
            "app": AppSettings().to_dict(),
            "created_at": datetime.now().isoformat()
        }

        with open(self.settings_file, 'w', encoding='utf-8') as f:
            json.dump(default, f, indent=2, ensure_ascii=False)

        self.logger.info("Created default settings.json")

    def _create_default_activities_file(self, game: str):
        """Create default activities file for a game"""
        default = {
            "game": game.upper(),
            "activities": [
                {
                    "id": "alliance_help",
                    "name": "Alliance Help",
                    "enabled": True,
                    "interval_hours": 0,
                    "interval_minutes": 10,
                    "priority": 5,
                    "start_time": None,
                    "end_time": None,
                    "max_retries": 3,
                    "retry_delay_minutes": 5,
                    "max_execution_seconds": 60,
                    "parameters": {
                        "help_all": True,
                        "max_helps": 50
                    }
                },
                {
                    "id": "vip_collection",
                    "name": "VIP Collection",
                    "enabled": True,
                    "interval_hours": 24,
                    "interval_minutes": 0,
                    "priority": 3,
                    "parameters": {}
                },
                {
                    "id": "gathering",
                    "name": "Resource Gathering",
                    "enabled": False,
                    "interval_hours": 0,
                    "interval_minutes": 5,
                    "priority": 2,
                    "parameters": {
                        "resource_types": ["food", "wood", "stone", "gold"],
                        "min_amount": 50000,
                        "max_march_distance": 30
                    }
                }
            ],
            "created_at": datetime.now().isoformat()
        }

        filename = f"activities_{game}.json"
        filepath = self.config_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(default, f, indent=2, ensure_ascii=False)

        self.logger.info(f"Created default {filename}")

    # ========================================================================
    # VALIDATION
    # ========================================================================

    def validate_activity_config(self, activity_data: Dict[str, Any]) -> bool:
        """
        Validate activity configuration.

        Args:
            activity_data: Activity configuration dictionary

        Returns:
            True if valid, False otherwise
        """
        required_fields = ['id', 'name', 'enabled', 'priority']

        for field in required_fields:
            if field not in activity_data:
                self.logger.error(f"Missing required field: {field}")
                return False

        # Validate priority range
        if not (1 <= activity_data.get('priority', 0) <= 10):
            self.logger.error("Priority must be between 1 and 10")
            return False

        return True

    def __repr__(self) -> str:
        """String representation"""
        return f"ConfigManager(dir={self.config_dir}, accounts={len(self._accounts)})"
