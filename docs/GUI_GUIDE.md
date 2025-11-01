# GUI User Guide

## Overview

The Game Automation Framework now includes a **sleek, modern desktop GUI** built with PyQt6. The interface features a dark theme, smooth animations, and professional design that makes bot management accessible to everyone.

## Launching the GUI

```bash
python main_gui.py
```

The GUI will automatically:
- Initialize ADB connection to BlueStacks
- Setup screen analyzer
- Create activity scheduler
- Display the main window

## Interface Layout

```
┌─────────────────────────────────────────────────────────┐
│  [Navigation]  │  [Content Area]                        │
│                │                                         │
│  Dashboard     │  📊 Dashboard / ⚙️ Activities / etc.  │
│  Activities    │                                         │
│  Templates     │  [Dynamic content based on selection]  │
│  Logs          │                                         │
│  Statistics    │                                         │
│  Settings      │                                         │
│                │                                         │
│  [Controls]    │                                         │
│  ▶ START       │                                         │
│  ⏸ PAUSE       │                                         │
│  ⏹ STOP        │                                         │
└─────────────────────────────────────────────────────────┘
```

## Pages

### 1. Dashboard 📊
**Real-time overview of automation status**

- **Stat Cards**: Uptime, Success count, Fail count, Success rate
- **Current Status**: Active activity and next scheduled activity
- **System Health**: ADB, Emulator, Screenshot status
- **Activity Timeline**: Next 5 upcoming activities with countdown
- **Live Console**: Real-time log output

**What it shows:**
- `🟢 RUNNING` or `⚫ STOPPED` status
- Live uptime counter (HH:MM:SS)
- Success/fail execution counts
- Next activity countdown (e.g., "in 4m 23s")

### 2. Activities ⚙️
**Manage all 50 activities**

Each activity card displays:
- **Name** and **Status** (🟢 Enabled / 💤 Disabled)
- **Priority** (1-10 with color-coded slider)
- **Interval** (hours and minutes)
- **Next Run** (countdown timer)
- **Success Rate** (percentage and total count)

**Actions:**
- `▶ Run Now` - Manually trigger activity
- `⚙ Configure` - Open settings dialog
- `✓ Enabled` checkbox - Enable/disable activity

**Filters:**
- Search by name
- Show all / Enabled only / Disabled only / High priority

**Priority Colors:**
- 🔴 Red (9-10): Critical priority
- 🟠 Orange (7-8): High priority
- 🔵 Blue (5-6): Normal priority
- ⚪ Gray (1-4): Low priority

### 3. Templates 🖼️
**Manage UI template images**

- View all template images in grid
- Organize by category (buttons, screens, icons)
- Capture new templates
- Test template matching
- See usage statistics (which activities use which templates)

### 4. Logs 📝
**Live application logs**

- Real-time log viewer with auto-scroll
- Filter by log level (INFO, WARNING, ERROR)
- Search logs
- Export logs to file
- Color-coded log messages

### 5. Statistics 📈
**Performance analytics**

- Execution history chart (daily/weekly/monthly)
- Top 5 most-run activities
- Success rate by activity
- Average execution time
- Activity breakdown pie chart
- Historical trends

### 6. Settings 🔧
**Configuration**

**Emulator:**
- Device ID selection
- ADB path configuration
- Auto-connect on startup

**OCR:**
- Tesseract path
- Language selection
- PSM mode

**Behavior:**
- Click randomization variance (±px)
- Delay ranges (min/max milliseconds)
- Screenshot caching
- Error screenshot saving

**Safety:**
- Emergency stop hotkey
- Pause on error
- Max retry attempts
- Activity timeout

## Control Panel

Located at the bottom of the navigation sidebar:

### ▶ START
- Starts the automation scheduler
- All enabled activities begin running on their intervals
- Button becomes disabled when running
- Status bar shows 🟢 RUNNING

### ⏸ PAUSE
- Pauses the scheduler (disabled when stopped)
- Activities currently running will complete
- No new activities will start
- Status bar shows 🟡 PAUSED

### ⏹ STOP
- Completely stops the scheduler
- Waits for current activities to finish
- Resets all timers
- Status bar shows ⚫ STOPPED

## Status Bar

Bottom status bar shows:
- **Left**: Automation status (🟢 Running / ⚫ Stopped / 🟡 Paused)
- **Right**: ADB connection (📱 ✅ Connected / ❌ Disconnected)

## Keyboard Shortcuts

- `Ctrl+S` - Start automation
- `Ctrl+P` - Pause automation
- `Ctrl+Q` - Stop automation
- `Escape` - Emergency stop (if enabled in settings)
- `Ctrl+L` - Jump to logs
- `Ctrl+D` - Jump to dashboard

## Visual Indicators

### Status Colors
- 🟢 **Green** - Success, running, connected
- 🔴 **Red** - Error, failed, disconnected
- 🟡 **Yellow** - Warning, paused
- 🔵 **Blue** - Info, normal
- ⚪ **Gray** - Disabled, inactive

### Activity States
- `✅ Completed` - Last run succeeded
- `⏳ Scheduled` - Waiting for next run
- `▶️ Running` - Currently executing
- `❌ Failed` - Last run failed
- `💤 Disabled` - Not enabled

## Theme

### Dark Theme (Default)
- Background: `#1a1a1a` (Very dark gray)
- Cards: `#252525` (Dark gray)
- Accent: `#4a9eff` (Blue)
- Success: `#4caf50` (Green)
- Warning: `#ff9800` (Orange)
- Error: `#f44336` (Red)

Modern features:
- Rounded corners (8px)
- Subtle shadows and gradients
- Smooth hover effects
- Professional typography
- Material Design icons

## Tips

1. **First Time Setup:**
   - Go to Settings → Configure ADB path and device ID
   - Test connection before starting automation

2. **Activity Configuration:**
   - Start with high-priority activities enabled
   - Test each activity manually before full automation
   - Adjust intervals based on your playstyle

3. **Monitoring:**
   - Keep Dashboard open for real-time overview
   - Check Logs for detailed execution info
   - Review Statistics weekly for optimization

4. **Performance:**
   - Disable unused activities to reduce overhead
   - Enable screenshot caching for faster execution
   - Set appropriate intervals to avoid detection

5. **Safety:**
   - Always test with a test account first
   - Use randomization to avoid bot detection
   - Don't run 24/7 - use time windows

## Troubleshooting

### GUI won't start
```bash
# Check PyQt6 installation
pip install PyQt6==6.6.1

# Try running with debug output
python main_gui.py --debug
```

### ADB not connecting
- Ensure BlueStacks is running
- Check ADB is enabled in BlueStacks settings
- Verify device ID in Settings page
- Try clicking "🔄 Scan" button

### Activities not running
- Check activity is enabled (✓ checkbox)
- Verify interval has elapsed
- Check scheduler is started (▶ START button)
- Review logs for error messages

## Advanced

### Custom Themes
Edit `src/gui/styles/theme.py` to customize colors and styles.

### Adding New Pages
1. Create page in `src/gui/pages/`
2. Add to `main_window.py` navigation
3. Implement `refresh()` method

### System Tray
Future feature - minimize to system tray for background operation.

## Screenshots

*(Screenshots would be here if this were a real project)*

---

**Made with PyQt6 and lots of love** ❤️
