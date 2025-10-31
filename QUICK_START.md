# Quick Start Guide

**Get the bot running in 30 minutes!**

---

## Prerequisites

- ✓ Windows 10/11
- ✓ Python 3.11+ installed
- ✓ BlueStacks installed
- ✓ Rise of Kingdoms or Call of Dragons game installed in BlueStacks

---

## Step 1: Install Dependencies (5 minutes)

```bash
# Navigate to project folder
cd GameAutomationFramework

# Install Python packages
pip install -r requirements.txt
```

**Install Tesseract OCR:**
1. Download: https://github.com/UB-Mannheim/tesseract/wiki
2. Install to default location
3. Add to PATH or set `TESSDATA_PREFIX` environment variable

---

## Step 2: Setup BlueStacks (5 minutes)

1. **Start BlueStacks**
2. **Enable ADB** (if not already):
   - Settings → Advanced → Android Debug Bridge: ON
3. **Start your game** (ROK or COD)
4. **Log in to your account**

---

## Step 3: Test ADB Connection (2 minutes)

```bash
python main.py --test-adb
```

**Expected output:**
```
✓ Found BlueStacks: emulator-5555
✓ Screenshot captured: (1920, 1080, 3)
✓ Screenshot saved to test_screenshot.png
```

If you see errors:
- Make sure BlueStacks is running
- Check ADB is enabled
- Try restarting BlueStacks

---

## Step 4: Create Template Images (15 minutes)

This is CRITICAL - the bot needs these images to recognize buttons!

### 4.1 Create Folders

```bash
mkdir templates
mkdir templates\buttons
mkdir templates\screens
```

### 4.2 Capture Game Screenshots

**In your game (ROK or COD):**

1. **Go to Alliance Screen**
2. **Take screenshot**: `python main.py --test-adb`
   - This saves `test_screenshot.png`

### 4.3 Crop Button Images

Use any image editor (Paint, Photoshop, GIMP, etc.):

**A) Alliance Button** (from city view)
1. Open `test_screenshot.png`
2. Crop just the alliance button (small, maybe 50x50 pixels)
3. Save as: `templates/buttons/alliance.png`

**B) Help All Button** (from alliance screen)
1. Navigate to alliance in game
2. Capture screenshot again
3. Crop the "Help All" button
4. Save as: `templates/buttons/help_all.png`

**C) Alliance Screen Indicator**
1. Crop any unique element from alliance screen (title bar, icon, etc.)
2. Save as: `templates/screens/alliance.png`

### Tips for Good Templates:
- ✓ Crop tight around the button/element
- ✓ No extra space or background
- ✓ Save as PNG (not JPG)
- ✓ Keep original colors
- ✓ Make sure it's a unique element

---

## Step 5: Configure Activities (3 minutes)

Edit `config/activities_rok.json`:

```json
{
  "activities": [
    {
      "id": "alliance_help",
      "name": "Alliance Help",
      "enabled": true,          ← Make sure this is true
      "interval_minutes": 10,    ← How often to run
      ...
    }
  ]
}
```

---

## Step 6: Run the Bot! (1 minute)

```bash
python main.py --game rok
```

**What happens:**
1. Bot connects to BlueStacks
2. Loads configuration
3. Creates activities
4. Starts scheduler
5. Waits for Alliance Help to be due
6. Executes activity every 10 minutes

**You should see:**
```
============================================================
Game Automation Framework
============================================================
Game: ROK
Mode: Normal
============================================================

[2025-10-31 12:00:00] INFO     Main           : ✓ ADB connection successful
[2025-10-31 12:00:00] INFO     Main           : ✓ Screen analyzer ready
[2025-10-31 12:00:00] INFO     Main           : ✓ Configuration loaded
[2025-10-31 12:00:00] INFO     Scheduler      : Scheduler started

🤖 Automation is running!

Registered Activities:
  - Alliance Help             [ENABLED]
    Interval: 0h 10m
    Priority: 5

Press Ctrl+C to stop
```

---

## Troubleshooting

### Problem: "Cannot capture screenshot"
**Solution:**
- Restart BlueStacks
- Check ADB is enabled
- Try: `adb devices` in command prompt
- Try: `adb connect 127.0.0.1:5555`

### Problem: "Template not found: templates/buttons/alliance.png"
**Solution:**
- Make sure you created the template folders
- Make sure you saved the template images
- Check file paths and names match exactly

### Problem: "Activity failed - element not found"
**Solution:**
- Your template images might not match
- Try capturing new templates
- Make sure game resolution is 1920x1080
- Adjust confidence threshold lower (0.7 instead of 0.8)

### Problem: "No activities enabled"
**Solution:**
- Edit `config/activities_rok.json`
- Set `"enabled": true` for alliance_help
- Save file and restart bot

---

## Watching It Work

### Check Logs
Look in `logs/` folder for detailed logs

### Debug Mode
```bash
python main.py --game rok --debug
```
Shows detailed information about template matching, decisions, etc.

### Duration Test
```bash
python main.py --game rok --duration 300
```
Runs for 5 minutes then stops (good for testing)

---

## What's Next?

### After Alliance Help Works:

1. **Add more activities** (VIP Collection, Daily Login, etc.)
2. **Create more templates** for those activities
3. **Enable them** in configuration
4. **Test each one** individually

### Creating New Activities:

See `docs/ACTIVITY_FLOWS.md` for complete implementation guides!

### Integration with Your Project:

Once working, you can:
- Wrap in REST API
- Add Discord bot commands
- Create web dashboard
- Store results in database

---

## Commands Reference

```bash
# Test ADB connection
python main.py --test-adb

# List available activities
python main.py --list

# Run automation (Rise of Kingdoms)
python main.py --game rok

# Run automation (Call of Dragons)
python main.py --game cod

# Debug mode (verbose logging)
python main.py --debug

# Run for specific duration
python main.py --duration 300    # 5 minutes

# Combine options
python main.py --game rok --debug --duration 600
```

---

## Tips for Success

### 1. Start Small
- Get ONE activity working first
- Then add more gradually
- Don't enable everything at once

### 2. Good Templates
- Take high-quality screenshots
- Crop precisely
- Test each template individually

### 3. Monitor First Run
- Watch the bot's first few executions
- Check if it finds buttons correctly
- Adjust templates if needed

### 4. Use Time Windows
```json
"start_time": "06:00",
"end_time": "23:00"
```
Prevents late-night activity

### 5. Adjust Intervals
```json
"interval_minutes": 30  // 30 minutes
"interval_hours": 2     // 2 hours
```
Based on what makes sense for each activity

---

## Safety Reminders

⚠️ **This violates game Terms of Service**
⚠️ **Account ban risk**
⚠️ **Use on test accounts**
⚠️ **Don't run 24/7**
⚠️ **Add randomization** (already built in)

---

## Success Checklist

- [ ] Python 3.11+ installed
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Tesseract OCR installed
- [ ] BlueStacks running with game
- [ ] ADB connection tested successfully
- [ ] Template images created
- [ ] Activities configured
- [ ] First test run completed
- [ ] Alliance Help activity working

---

**Ready to start? Run: `python main.py --test-adb`**
