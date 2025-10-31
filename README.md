# Game Automation Framework

**A standalone game automation framework rebuilt from WhaleBots analysis**

## Purpose

This is a **complete rebuild** of game automation for:
- **Learning**: Understand how game automation works
- **Testing**: See what's feasible and what's not
- **Research**: Explore automation techniques
- **Future Integration**: Decide what to integrate into larger projects

## Features

- ✅ **No Licensing** - Completely free, no restrictions
- ✅ **All Activities Unlocked** - 50+ automation activities
- ✅ **Unlimited Instances** - Run as many as your hardware allows
- ✅ **Open Architecture** - Easy to understand and modify
- ✅ **Well Documented** - Every component explained
- ✅ **Configurable** - JSON-based configuration
- ✅ **Multi-Game Support** - Rise of Kingdoms, Call of Dragons

## Project Structure

```
GameAutomationFramework/
├── src/
│   ├── core/                    # Core automation engine
│   │   ├── activity.py          # Activity base class
│   │   ├── scheduler.py         # Activity scheduler
│   │   ├── adb.py               # Android Debug Bridge integration
│   │   ├── screen.py            # Screen capture and analysis
│   │   └── config.py            # Configuration management
│   │
│   ├── activities/              # Activity implementations
│   │   ├── base/                # Base activity types
│   │   ├── cod/                 # Call of Dragons activities
│   │   └── rok/                 # Rise of Kingdoms activities
│   │
│   ├── ui/                      # User interface
│   │   ├── main_window.py       # Main application window
│   │   ├── activity_editor.py   # Activity configuration UI
│   │   └── dashboard.py         # Statistics dashboard
│   │
│   └── utils/                   # Utility functions
│       ├── logger.py            # Logging system
│       ├── ocr.py               # Text recognition
│       └── image.py             # Image processing
│
├── config/                      # Configuration files
│   ├── accounts.json            # Account settings
│   ├── activities_cod.json      # COD activities
│   ├── activities_rok.json      # ROK activities
│   └── settings.json            # App settings
│
├── tests/                       # Unit tests
├── docs/                        # Documentation
└── logs/                        # Log files
```

## How It Works

### 1. Architecture Overview

```
User → UI → Scheduler → Activities → ADB → Emulator → Game
                  ↑          ↓
              Config     Screen
                        Analysis
```

### 2. Core Components

**Activity**: Base class for all automation tasks
- Defines what to do (gather resources, hunt barbarians, etc.)
- Checks prerequisites (enough troops, resources, etc.)
- Executes the task
- Verifies completion

**Scheduler**: Manages when activities run
- Checks which activities are due
- Executes based on priority
- Handles errors and retries
- Updates next execution time

**ADB Integration**: Communicates with Android emulator
- Captures screenshots
- Simulates touch/swipe
- Inputs text
- Launches apps

**Screen Analysis**: Understands game state
- OCR for reading text
- Image matching for UI elements
- Resource detection
- State verification

### 3. Activity Lifecycle

```
[SCHEDULED]
    ↓
Check Prerequisites
    ↓
[READY] → Execute Activity → Verify Completion
    ↓              ↓                ↓
Success        Failure          Success
    ↓              ↓                ↓
Update Next    Retry or         Log Result
Execution      Disable
```

## Installation

### Requirements

- Python 3.11+
- Android Emulator (BlueStacks recommended)
- ADB (Android Debug Bridge)

### Setup

1. **Clone/Download this project**

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Install ADB**
   - Windows: Download Android Platform Tools
   - Add to PATH

4. **Setup Emulator**
   - Install BlueStacks
   - Enable ADB debugging
   - Install game (ROK or COD)

5. **Configure**
   - Edit `config/accounts.json`
   - Edit `config/activities_rok.json` or `config/activities_cod.json`
   - Edit `config/settings.json`

## Usage

### Command Line

```bash
# Start automation
python main.py

# With specific game
python main.py --game rok

# With specific account
python main.py --account account_001

# List activities
python main.py --list-activities

# Test ADB connection
python main.py --test-adb
```

### GUI

```bash
python main_gui.py
```

## Configuration

### accounts.json

```json
{
  "accounts": [
    {
      "account_id": "account_001",
      "account_name": "Main Account",
      "server_name": "Server 1234",
      "device_id": "emulator-5555",
      "enabled": true
    }
  ]
}
```

### activities_rok.json

```json
{
  "activities": [
    {
      "id": "barbarian_hunt",
      "name": "Barbarian Hunt",
      "enabled": true,
      "interval_hours": 2,
      "priority": 1,
      "parameters": {
        "target_level": 5,
        "min_troops": 50
      }
    }
  ]
}
```

## Development

### Adding a New Activity

1. Create activity class in `src/activities/{game}/`
2. Inherit from `Activity` base class
3. Implement required methods:
   - `check_prerequisites()`
   - `execute()`
   - `verify_completion()`
4. Register in config file
5. Test!

### Example Activity

```python
from src.core.activity import Activity

class BarbarianHunt(Activity):
    def check_prerequisites(self):
        # Check if enough troops available
        return self.get_available_troops() >= 50

    def execute(self):
        # Navigate to map
        # Find barbarian
        # Send troops
        return True

    def verify_completion(self):
        # Check if march started
        return True
```

## Learning Path

### Phase 1: Understand Core (Week 1)
- Read `src/core/activity.py` - Base class for all activities
- Read `src/core/scheduler.py` - How activities are scheduled
- Read `src/core/adb.py` - How to control Android
- Run simple test scripts

### Phase 2: Implement Basic Activities (Week 2)
- Implement `gathering.py` - Resource gathering
- Implement `alliance_help.py` - Simple button clicking
- Test with real emulator
- Learn screen analysis

### Phase 3: Advanced Activities (Week 3)
- Implement `barbarian_hunt.py` - Complex decision making
- Implement `building_upgrade.py` - Queue management
- Add error handling
- Add randomization

### Phase 4: UI and Polish (Week 4)
- Build PyQt6 interface
- Add configuration editor
- Add statistics dashboard
- Add logging viewer

## Testing

```bash
# Run all tests
pytest tests/

# Test specific component
pytest tests/test_scheduler.py

# Test with emulator
pytest tests/test_adb.py --emulator
```

## Packaging to .exe

```bash
# Install PyInstaller
pip install pyinstaller

# Create single .exe
pyinstaller --onefile --windowed --icon=icon.ico main_gui.py

# Output in dist/main_gui.exe
```

## Security & Legal

### ⚠️ Important Warnings

- **Violates Game TOS**: This automation violates Terms of Service
- **Account Ban Risk**: Your account may be banned
- **Educational Only**: For learning automation techniques
- **No Warranty**: Use at your own risk

### Detection Risks

- Games actively detect automation
- Randomization helps but not guaranteed
- Network traffic analysis can detect patterns
- Precision timing is suspicious

### Recommendations

- Use on test accounts only
- Don't run 24/7
- Add randomization
- Monitor for captcha/bans
- Use VPN if needed

## Future Integration Ideas

Once you understand how this works, you can:

1. **Web Dashboard Integration**
   - Expose REST API for control
   - Web UI for configuration
   - Real-time status updates

2. **Discord Bot Integration**
   - `/rok gather start` commands
   - Status notifications
   - Error alerts

3. **Database Integration**
   - Store configurations
   - Track statistics
   - Multi-user support

4. **Permission System**
   - Owner/Leader/User tiers
   - Feature access control
   - Usage limits

5. **Cloud Deployment**
   - Run on VPS
   - Remote control
   - Scheduled automation

## Next Steps

1. **Read the code** - Start with `src/core/activity.py`
2. **Run examples** - Try the test scripts
3. **Configure** - Set up your accounts
4. **Test** - Run with emulator
5. **Learn** - Understand what works
6. **Decide** - What to integrate later

## Questions to Answer

As you build and test:

- ✅ How fast can activities execute?
- ✅ How reliable is screen analysis?
- ✅ How often does it get detected?
- ✅ What's the resource usage?
- ✅ Can it run multiple accounts?
- ✅ Is remote control feasible?
- ✅ What breaks when game updates?

## License

**Private Project** - Not open source

For educational and research purposes only.

## Credits

Built from analysis of WhaleBots 1012 for educational purposes.

---

**Ready to start building and learning!**
