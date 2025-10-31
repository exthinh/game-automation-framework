# API Reference

Complete API documentation for the Game Automation Framework.

---

## Table of Contents

1. [Core Classes](#core-classes)
2. [Activity Base Class](#activity-base-class)
3. [ADB Integration](#adb-integration)
4. [Screen Analysis](#screen-analysis)
5. [Configuration](#configuration)
6. [Scheduler](#scheduler)
7. [Creating Custom Activities](#creating-custom-activities)

---

## Core Classes

### Activity

Base class for all automation activities.

**Location**: `src/core/activity.py`

```python
from src.core.activity import Activity, ActivityConfig
from dataclasses import dataclass

@dataclass
class MyActivityConfig(ActivityConfig):
    my_parameter: int = 10

class MyActivity(Activity):
    def __init__(self, config: MyActivityConfig, adb, screen):
        super().__init__("My Activity", config)
        self.adb = adb
        self.screen = screen

    def check_prerequisites(self) -> bool:
        # Check if activity can run
        return True

    def execute(self) -> bool:
        # Main activity logic
        return True

    def verify_completion(self) -> bool:
        # Verify activity succeeded
        return True
```

**Methods:**

| Method | Description | Returns |
|--------|-------------|---------|
| `check_prerequisites()` | Check if activity can run | `bool` |
| `execute()` | Main activity logic | `bool` |
| `verify_completion()` | Verify success | `bool` |
| `get_next_execution_time()` | Calculate next run time | `datetime` |

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `name` | `str` | Activity name |
| `config` | `ActivityConfig` | Configuration object |
| `state` | `ActivityState` | Current state |
| `last_execution` | `datetime` | Last execution time |
| `statistics` | `dict` | Execution statistics |

---

### ADBConnection

Controls Android emulator via ADB.

**Location**: `src/core/adb.py`

```python
from src.core.adb import ADBConnection

adb = ADBConnection(device_id="127.0.0.1:5555")

# Connect to emulator
adb.connect()

# Get connected devices
devices = adb.get_devices()

# Capture screenshot
adb.capture_screen("screenshot.png")

# Tap at coordinates
adb.tap(960, 540, randomize=True)

# Swipe gesture
adb.swipe(500, 900, 500, 300, duration_ms=500)

# Input text
adb.input_text("Hello")

# Launch app
adb.start_app("com.lilithgame.roc.gp")
```

**Methods:**

#### `connect(host: str, port: int) -> bool`
Connect to ADB server.

**Parameters:**
- `host`: ADB host (default: "127.0.0.1")
- `port`: ADB port (default: 5555)

**Returns:** `True` if connected

#### `get_devices() -> List[str]`
Get list of connected devices.

**Returns:** List of device IDs

#### `capture_screen(output_path: str) -> bool`
Capture screenshot to file.

**Parameters:**
- `output_path`: Path to save PNG

**Returns:** `True` if successful

#### `capture_screen_np() -> np.ndarray`
Capture screenshot as NumPy array.

**Returns:** OpenCV image (BGR format)

#### `capture_screen_cached() -> np.ndarray`
Get cached screenshot (faster for multiple checks).

**Returns:** OpenCV image

#### `tap(x: int, y: int, randomize: bool = True) -> bool`
Simulate tap at coordinates.

**Parameters:**
- `x`, `y`: Screen coordinates
- `randomize`: Add ±5px randomization

**Returns:** `True` if successful

#### `swipe(x1, y1, x2, y2, duration_ms: int = 500) -> bool`
Simulate swipe gesture.

**Parameters:**
- `x1`, `y1`: Start coordinates
- `x2`, `y2`: End coordinates
- `duration_ms`: Swipe duration

**Returns:** `True` if successful

#### `input_text(text: str) -> bool`
Input text into focused field.

**Parameters:**
- `text`: Text to input

**Returns:** `True` if successful

#### `start_app(package: str) -> bool`
Launch app by package name.

**Parameters:**
- `package`: App package (e.g., "com.lilithgame.roc.gp")

**Returns:** `True` if successful

---

### ScreenAnalyzer

Computer vision and screen analysis.

**Location**: `src/core/screen.py`

```python
from src.core.screen import ScreenAnalyzer
import cv2

screen = ScreenAnalyzer()
screenshot = cv2.imread("screenshot.png")

# Find template
location = screen.find_template(
    screenshot,
    "templates/buttons/alliance.png",
    confidence=0.75
)
if location:
    x, y = location
    print(f"Found at ({x}, {y})")

# Find all instances
locations = screen.find_all_templates(
    screenshot,
    "templates/icons/resource.png",
    confidence=0.70
)

# Read text with OCR
region = screenshot[100:150, 500:700]
text = screen.read_text(region)

# Find color regions
gold_nodes = screen.find_color_regions(
    screenshot,
    lower_hsv=(20, 100, 100),
    upper_hsv=(30, 255, 255)
)
```

**Methods:**

#### `find_template(image, template_path, confidence=0.75) -> Optional[Tuple[int, int]]`
Find template in image.

**Parameters:**
- `image`: OpenCV image (np.ndarray)
- `template_path`: Path to template PNG
- `confidence`: Match confidence (0.0-1.0)

**Returns:** `(x, y)` tuple or `None`

#### `find_all_templates(image, template_path, confidence=0.75) -> List[Tuple[int, int]]`
Find all instances of template.

**Returns:** List of `(x, y)` tuples

#### `read_text(image, lang='eng') -> str`
Extract text using OCR.

**Parameters:**
- `image`: OpenCV image region
- `lang`: Tesseract language

**Returns:** Detected text

#### `find_color_regions(image, lower_hsv, upper_hsv) -> List[Tuple[int, int]]`
Find colored regions.

**Parameters:**
- `image`: OpenCV image
- `lower_hsv`: Lower HSV bound tuple
- `upper_hsv`: Upper HSV bound tuple

**Returns:** List of region centers

---

### ConfigManager

Manage JSON configurations.

**Location**: `src/core/config.py`

```python
from src.core.config import ConfigManager

config = ConfigManager(config_dir="config")

# Load accounts
accounts = config.load_accounts()

# Save accounts
config.save_accounts(accounts)

# Load activities
activities = config.load_activities("rok")

# Save activities
config.save_activities("rok", activities)
```

**Methods:**

#### `load_accounts() -> List[AccountConfig]`
Load account configurations.

#### `save_accounts(accounts: List[AccountConfig])`
Save account configurations.

#### `load_activities(game: str) -> Dict[str, Any]`
Load activity configurations for a game.

**Parameters:**
- `game`: "rok" or "cod"

#### `save_activities(game: str, activities: Dict[str, Any])`
Save activity configurations.

---

### ActivityScheduler

Orchestrate and execute activities.

**Location**: `src/core/scheduler.py`

```python
from src.core.scheduler import ActivityScheduler

scheduler = ActivityScheduler()

# Register activities
scheduler.register_activity(alliance_help_activity)
scheduler.register_activity(vip_collection_activity)

# Start scheduler (blocking)
scheduler.start()

# Or run for duration
scheduler.run_for_duration(seconds=300)

# Stop scheduler
scheduler.stop()
```

**Methods:**

#### `register_activity(activity: Activity)`
Register an activity.

#### `start()`
Start scheduler (blocking).

#### `run_for_duration(seconds: int)`
Run for specified duration.

#### `stop()`
Stop scheduler gracefully.

#### `get_statistics() -> Dict[str, Any]`
Get execution statistics.

---

## Creating Custom Activities

### Step 1: Define Configuration

```python
from dataclasses import dataclass
from src.core.activity import ActivityConfig

@dataclass
class MyActivityConfig(ActivityConfig):
    # Activity-specific parameters
    my_setting: bool = True
    threshold: int = 100
```

### Step 2: Implement Activity Class

```python
from src.core.activity import Activity
from src.core.adb import ADBConnection
from src.core.screen import ScreenAnalyzer
import time

class MyActivity(Activity):
    def __init__(self, config: MyActivityConfig, adb: ADBConnection, screen: ScreenAnalyzer):
        super().__init__("My Activity", config)
        self.adb = adb
        self.screen = screen
        self.config: MyActivityConfig = config

    def check_prerequisites(self) -> bool:
        """Check if activity can run."""
        # Example: check if on correct screen
        screenshot = self.adb.capture_screen_cached()
        correct_screen = self.screen.find_template(
            screenshot,
            'templates/screens/target_screen.png',
            confidence=0.7
        )

        if not correct_screen:
            self.logger.warning("Not on correct screen")
            return False

        return True

    def execute(self) -> bool:
        """Execute the activity."""
        self.logger.info("Starting my activity...")

        # Step 1: Navigate
        if not self._navigate():
            return False

        # Step 2: Perform action
        if not self._perform_action():
            return False

        # Step 3: Collect results
        self._collect_results()

        return True

    def verify_completion(self) -> bool:
        """Verify activity completed successfully."""
        # Check success indicators
        screenshot = self.adb.capture_screen_cached()
        success = self.screen.find_template(
            screenshot,
            'templates/indicators/success.png'
        )

        return success is not None

    def _navigate(self) -> bool:
        """Navigate to target screen."""
        # Implementation
        return True

    def _perform_action(self) -> bool:
        """Perform main action."""
        # Implementation
        return True

    def _collect_results(self):
        """Collect any results."""
        # Implementation
        pass
```

### Step 3: Add Configuration

`config/activities_rok.json`:
```json
{
  "my_activity": {
    "enabled": true,
    "interval_hours": 1,
    "priority": 5,
    "my_setting": true,
    "threshold": 100
  }
}
```

### Step 4: Register with Scheduler

```python
# In main.py
from src.activities.base.my_activity import MyActivity, MyActivityConfig

# Create activity instance
config = MyActivityConfig(**activity_config)
activity = MyActivity(config, adb, screen)

# Register
scheduler.register_activity(activity)
```

---

## Common Patterns

### Template Matching Pattern

```python
def _find_and_click_button(self, template_path: str) -> bool:
    """Find button and click it."""
    screenshot = self.adb.capture_screen_cached()

    button_location = self.screen.find_template(
        screenshot,
        template_path,
        confidence=0.75
    )

    if button_location:
        self.adb.tap(button_location[0], button_location[1], randomize=True)
        time.sleep(0.5)
        return True

    return False
```

### Navigation Pattern

```python
def _navigate_to_screen(self, screen_name: str) -> bool:
    """Navigate to a specific screen."""
    # Check if already there
    screenshot = self.adb.capture_screen_cached()
    already_there = self.screen.find_template(
        screenshot,
        f'templates/screens/{screen_name}.png',
        confidence=0.7
    )

    if already_there:
        return True

    # Find and click navigation button
    button = self.screen.find_template(
        screenshot,
        f'templates/buttons/{screen_name}.png',
        confidence=0.75
    )

    if button:
        self.adb.tap(button[0], button[1], randomize=True)
        time.sleep(1.5)
        return True

    return False
```

### OCR Reading Pattern

```python
def _read_value(self, region: tuple) -> int:
    """Read numeric value from screen region."""
    screenshot = self.adb.capture_screen_cached()
    x, y, w, h = region
    roi = screenshot[y:y+h, x:x+w]

    text = self.screen.read_text(roi)

    # Parse number
    import re
    numbers = re.findall(r'\d+', text)
    if numbers:
        return int(numbers[0])

    return 0
```

---

## Error Handling

### Recommended Pattern

```python
def execute(self) -> bool:
    try:
        # Activity logic
        result = self._do_something()

        if not result:
            self.logger.warning("Step failed")
            return False

        return True

    except Exception as e:
        self.logger.error(f"Error in activity: {e}")
        return False
```

### Retry Logic

```python
def _execute_with_retry(self, action, max_retries: int = 3) -> bool:
    """Execute action with retries."""
    for attempt in range(max_retries):
        try:
            if action():
                return True

            self.logger.warning(f"Attempt {attempt + 1} failed")
            time.sleep(1.0 * (attempt + 1))  # Exponential backoff

        except Exception as e:
            self.logger.error(f"Attempt {attempt + 1} error: {e}")

    return False
```

---

## Next Steps

- **Review Example Activities**: Check `src/activities/base/` for examples
- **Create Custom Activity**: Follow the pattern above
- **Test Thoroughly**: Use `--duration` flag for testing
- **Read Guides**: See [Template Creation](TEMPLATE_CREATION.md)

---

**Happy Coding!** 🚀
