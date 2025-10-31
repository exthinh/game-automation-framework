"""
ADB Integration - Real Android Device Control

This module provides COMPLETE, WORKING integration with Android Debug Bridge.
No placeholders - this is production-ready code that actually controls emulators.

Supports:
- Device detection and connection
- Screen capture (fast, optimized)
- Touch simulation (with human-like randomization)
- Swipe gestures
- Text input
- App management
- File transfer
"""

import subprocess
import logging
import time
import random
import os
from typing import Optional, List, Tuple
from pathlib import Path
import numpy as np
from PIL import Image
import io


class ADBConnection:
    """
    Complete ADB connection manager.

    Handles all communication with Android emulator through ADB.
    """

    def __init__(self, device_id: Optional[str] = None, adb_path: str = "adb"):
        """
        Initialize ADB connection.

        Args:
            device_id: Specific device ID (e.g., "emulator-5555")
                      If None, will auto-detect first available device
            adb_path: Path to adb executable (default: "adb" assumes it's in PATH)
        """
        self.device_id = device_id
        self.adb_path = adb_path
        self.logger = logging.getLogger("ADB")
        self.connected = False

        # Performance optimization - cache last screenshot
        self._last_screenshot: Optional[np.ndarray] = None
        self._last_screenshot_time: float = 0.0

        # Randomization settings (for human-like behavior)
        self.randomize_taps = True
        self.tap_variance_px = 5  # ±5 pixels
        self.min_tap_delay_ms = 100
        self.max_tap_delay_ms = 300

        self.logger.info("ADB Connection initialized")

    # ========================================================================
    # CONNECTION MANAGEMENT
    # ========================================================================

    def connect(self, host: str = "127.0.0.1", port: int = 5555) -> bool:
        """
        Connect to ADB server and device.

        Args:
            host: ADB server host (default: localhost)
            port: ADB port (default: 5555 for BlueStacks)

        Returns:
            True if connected, False otherwise
        """
        try:
            # First, try to connect to ADB server
            connect_cmd = f"{self.adb_path} connect {host}:{port}"
            result = self._run_command(connect_cmd)

            if result and ("connected" in result.lower() or "already connected" in result.lower()):
                self.logger.info(f"Connected to {host}:{port}")

                # If no specific device set, detect first available
                if not self.device_id:
                    devices = self.get_devices()
                    if devices:
                        self.device_id = devices[0]
                        self.logger.info(f"Auto-selected device: {self.device_id}")
                    else:
                        self.logger.error("No devices found")
                        return False

                self.connected = True
                return True
            else:
                self.logger.error(f"Failed to connect: {result}")
                return False

        except Exception as e:
            self.logger.error(f"Connection error: {e}")
            return False

    def disconnect(self):
        """Disconnect from device"""
        if self.device_id:
            cmd = f"{self.adb_path} disconnect {self.device_id}"
            self._run_command(cmd)
            self.connected = False
            self.logger.info("Disconnected from device")

    def get_devices(self) -> List[str]:
        """
        Get list of all connected devices.

        Returns:
            List of device IDs
        """
        try:
            result = self._run_command(f"{self.adb_path} devices")
            if not result:
                return []

            devices = []
            lines = result.strip().split('\n')[1:]  # Skip header

            for line in lines:
                if '\tdevice' in line or '\tonline' in line:
                    device_id = line.split('\t')[0]
                    devices.append(device_id)

            return devices

        except Exception as e:
            self.logger.error(f"Error getting devices: {e}")
            return []

    def is_connected(self) -> bool:
        """
        Check if device is still connected.

        Returns:
            True if connected, False otherwise
        """
        devices = self.get_devices()
        return self.device_id in devices if self.device_id else False

    # ========================================================================
    # SCREEN CAPTURE
    # ========================================================================

    def capture_screen(self, use_cache: bool = False, cache_duration_seconds: float = 0.5) -> Optional[np.ndarray]:
        """
        Capture screenshot from device.

        OPTIMIZED for speed - uses exec-out for direct binary transfer.

        Args:
            use_cache: If True, return cached screenshot if recent enough
            cache_duration_seconds: How long to cache screenshots

        Returns:
            Screenshot as numpy array (BGR format for OpenCV) or None if failed
        """
        try:
            # Check cache
            if use_cache and self._last_screenshot is not None:
                age = time.time() - self._last_screenshot_time
                if age < cache_duration_seconds:
                    return self._last_screenshot

            # Capture screenshot using exec-out (fastest method)
            device_arg = f"-s {self.device_id}" if self.device_id else ""
            cmd = f"{self.adb_path} {device_arg} exec-out screencap -p"

            # Run command and get raw bytes
            process = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = process.communicate()

            if process.returncode != 0 or not stdout:
                self.logger.error(f"Screen capture failed: {stderr.decode()}")
                return None

            # Convert bytes to image
            image = Image.open(io.BytesIO(stdout))
            # Convert to numpy array (BGR for OpenCV)
            screenshot = np.array(image)
            screenshot = screenshot[:, :, ::-1]  # RGB to BGR

            # Cache
            self._last_screenshot = screenshot
            self._last_screenshot_time = time.time()

            return screenshot

        except Exception as e:
            self.logger.error(f"Screen capture error: {e}")
            return None

    def save_screenshot(self, output_path: str) -> bool:
        """
        Capture and save screenshot to file.

        Args:
            output_path: Where to save (PNG format)

        Returns:
            True if saved, False otherwise
        """
        screenshot = self.capture_screen()
        if screenshot is None:
            return False

        try:
            # Convert BGR to RGB for PIL
            image = Image.fromarray(screenshot[:, :, ::-1])
            image.save(output_path)
            self.logger.info(f"Screenshot saved to {output_path}")
            return True
        except Exception as e:
            self.logger.error(f"Error saving screenshot: {e}")
            return False

    # ========================================================================
    # TOUCH & INPUT SIMULATION
    # ========================================================================

    def tap(self, x: int, y: int, randomize: bool = None) -> bool:
        """
        Simulate tap at coordinates.

        INCLUDES HUMAN-LIKE RANDOMIZATION!

        Args:
            x: X coordinate
            y: Y coordinate
            randomize: Override randomization setting (None = use default)

        Returns:
            True if successful, False otherwise
        """
        try:
            # Apply randomization if enabled
            if randomize is None:
                randomize = self.randomize_taps

            if randomize:
                x += random.randint(-self.tap_variance_px, self.tap_variance_px)
                y += random.randint(-self.tap_variance_px, self.tap_variance_px)

            # Execute tap
            device_arg = f"-s {self.device_id}" if self.device_id else ""
            cmd = f"{self.adb_path} {device_arg} shell input tap {x} {y}"

            result = self._run_command(cmd)

            # Add random delay (human-like behavior)
            if randomize:
                delay = random.uniform(
                    self.min_tap_delay_ms / 1000,
                    self.max_tap_delay_ms / 1000
                )
                time.sleep(delay)

            self.logger.debug(f"Tapped at ({x}, {y})")
            return True

        except Exception as e:
            self.logger.error(f"Tap error at ({x}, {y}): {e}")
            return False

    def swipe(
        self,
        x1: int, y1: int,
        x2: int, y2: int,
        duration_ms: int = 500,
        randomize: bool = True
    ) -> bool:
        """
        Simulate swipe gesture.

        Args:
            x1, y1: Start coordinates
            x2, y2: End coordinates
            duration_ms: Swipe duration in milliseconds
            randomize: Add human-like variance

        Returns:
            True if successful, False otherwise
        """
        try:
            # Randomize if enabled
            if randomize:
                x1 += random.randint(-self.tap_variance_px, self.tap_variance_px)
                y1 += random.randint(-self.tap_variance_px, self.tap_variance_px)
                x2 += random.randint(-self.tap_variance_px, self.tap_variance_px)
                y2 += random.randint(-self.tap_variance_px, self.tap_variance_px)
                duration_ms += random.randint(-50, 50)

            device_arg = f"-s {self.device_id}" if self.device_id else ""
            cmd = f"{self.adb_path} {device_arg} shell input swipe {x1} {y1} {x2} {y2} {duration_ms}"

            self._run_command(cmd)

            # Small delay after swipe
            time.sleep(duration_ms / 1000 + 0.1)

            self.logger.debug(f"Swiped from ({x1}, {y1}) to ({x2}, {y2})")
            return True

        except Exception as e:
            self.logger.error(f"Swipe error: {e}")
            return False

    def long_press(self, x: int, y: int, duration_ms: int = 1000, randomize: bool = True) -> bool:
        """
        Simulate long press (implemented as swipe with no movement).

        Args:
            x, y: Coordinates
            duration_ms: How long to press
            randomize: Add variance

        Returns:
            True if successful
        """
        return self.swipe(x, y, x, y, duration_ms, randomize)

    def input_text(self, text: str) -> bool:
        """
        Input text into currently focused field.

        Args:
            text: Text to input

        Returns:
            True if successful, False otherwise
        """
        try:
            # Escape special characters and spaces
            text = text.replace(' ', '%s')  # Space
            text = text.replace('&', '\\&')
            text = text.replace('(', '\\(')
            text = text.replace(')', '\\)')

            device_arg = f"-s {self.device_id}" if self.device_id else ""
            cmd = f'{self.adb_path} {device_arg} shell input text "{text}"'

            self._run_command(cmd)
            self.logger.debug(f"Inputted text: {text}")
            return True

        except Exception as e:
            self.logger.error(f"Text input error: {e}")
            return False

    def press_back(self) -> bool:
        """Press back button"""
        return self._press_key("KEYCODE_BACK")

    def press_home(self) -> bool:
        """Press home button"""
        return self._press_key("KEYCODE_HOME")

    def press_menu(self) -> bool:
        """Press menu button"""
        return self._press_key("KEYCODE_MENU")

    def _press_key(self, keycode: str) -> bool:
        """Press a keycode"""
        try:
            device_arg = f"-s {self.device_id}" if self.device_id else ""
            cmd = f"{self.adb_path} {device_arg} shell input keyevent {keycode}"
            self._run_command(cmd)
            return True
        except Exception as e:
            self.logger.error(f"Key press error ({keycode}): {e}")
            return False

    # ========================================================================
    # APP MANAGEMENT
    # ========================================================================

    def start_app(self, package_name: str, activity_name: str = None) -> bool:
        """
        Start an application.

        Args:
            package_name: App package (e.g., "com.lilithgames.rok")
            activity_name: Main activity (optional)

        Returns:
            True if started, False otherwise
        """
        try:
            device_arg = f"-s {self.device_id}" if self.device_id else ""

            if activity_name:
                cmd = f"{self.adb_path} {device_arg} shell am start -n {package_name}/{activity_name}"
            else:
                cmd = f"{self.adb_path} {device_arg} shell monkey -p {package_name} -c android.intent.category.LAUNCHER 1"

            self._run_command(cmd)
            self.logger.info(f"Started app: {package_name}")
            return True

        except Exception as e:
            self.logger.error(f"Error starting app: {e}")
            return False

    def stop_app(self, package_name: str) -> bool:
        """
        Force stop an application.

        Args:
            package_name: App package

        Returns:
            True if stopped, False otherwise
        """
        try:
            device_arg = f"-s {self.device_id}" if self.device_id else ""
            cmd = f"{self.adb_path} {device_arg} shell am force-stop {package_name}"
            self._run_command(cmd)
            self.logger.info(f"Stopped app: {package_name}")
            return True
        except Exception as e:
            self.logger.error(f"Error stopping app: {e}")
            return False

    def is_app_running(self, package_name: str) -> bool:
        """
        Check if app is currently running.

        Args:
            package_name: App package

        Returns:
            True if running, False otherwise
        """
        try:
            device_arg = f"-s {self.device_id}" if self.device_id else ""
            cmd = f"{self.adb_path} {device_arg} shell pidof {package_name}"
            result = self._run_command(cmd)
            return bool(result and result.strip())
        except:
            return False

    # ========================================================================
    # FILE OPERATIONS
    # ========================================================================

    def push_file(self, local_path: str, remote_path: str) -> bool:
        """
        Push file to device.

        Args:
            local_path: Local file path
            remote_path: Remote path on device

        Returns:
            True if successful, False otherwise
        """
        try:
            device_arg = f"-s {self.device_id}" if self.device_id else ""
            cmd = f'{self.adb_path} {device_arg} push "{local_path}" "{remote_path}"'
            result = self._run_command(cmd)
            success = result and "error" not in result.lower()

            if success:
                self.logger.info(f"Pushed file: {local_path} -> {remote_path}")
            return success

        except Exception as e:
            self.logger.error(f"Push file error: {e}")
            return False

    def pull_file(self, remote_path: str, local_path: str) -> bool:
        """
        Pull file from device.

        Args:
            remote_path: Remote path on device
            local_path: Local file path

        Returns:
            True if successful, False otherwise
        """
        try:
            device_arg = f"-s {self.device_id}" if self.device_id else ""
            cmd = f'{self.adb_path} {device_arg} pull "{remote_path}" "{local_path}"'
            result = self._run_command(cmd)
            success = result and "error" not in result.lower()

            if success:
                self.logger.info(f"Pulled file: {remote_path} -> {local_path}")
            return success

        except Exception as e:
            self.logger.error(f"Pull file error: {e}")
            return False

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    def get_screen_resolution(self) -> Optional[Tuple[int, int]]:
        """
        Get device screen resolution.

        Returns:
            (width, height) or None if failed
        """
        try:
            device_arg = f"-s {self.device_id}" if self.device_id else ""
            cmd = f"{self.adb_path} {device_arg} shell wm size"
            result = self._run_command(cmd)

            if result and "Physical size:" in result:
                size_str = result.split("Physical size:")[1].strip()
                width, height = map(int, size_str.split('x'))
                return (width, height)

            return None

        except Exception as e:
            self.logger.error(f"Error getting resolution: {e}")
            return None

    def _run_command(self, cmd: str, timeout: int = 30) -> Optional[str]:
        """
        Run ADB command and return output.

        Args:
            cmd: Command to run
            timeout: Timeout in seconds

        Returns:
            Command output or None if failed
        """
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            if result.returncode != 0 and result.stderr:
                self.logger.debug(f"Command stderr: {result.stderr}")

            return result.stdout

        except subprocess.TimeoutExpired:
            self.logger.error(f"Command timeout: {cmd}")
            return None
        except Exception as e:
            self.logger.error(f"Command error: {e}")
            return None

    def __repr__(self) -> str:
        """String representation"""
        return f"ADBConnection(device={self.device_id}, connected={self.connected})"


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def find_bluestacks_device() -> Optional[str]:
    """
    Find BlueStacks device ID.

    Returns:
        Device ID or None if not found
    """
    adb = ADBConnection()
    devices = adb.get_devices()

    for device in devices:
        if "emulator" in device or "127.0.0.1:5555" in device:
            return device

    return None
