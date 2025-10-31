# Template Creation Guide

Learn how to create template images for UI element detection.

---

## Table of Contents

1. [What are Templates?](#what-are-templates)
2. [Tools Needed](#tools-needed)
3. [Capturing Templates](#capturing-templates)
4. [Template Best Practices](#template-best-practices)
5. [Template Organization](#template-organization)
6. [Testing Templates](#testing-templates)
7. [Common Templates Needed](#common-templates-needed)

---

## What are Templates?

Templates are small PNG images of UI elements (buttons, icons, text) that the bot uses to:
- **Find** UI elements on screen (template matching)
- **Click** on buttons and icons
- **Verify** which screen the bot is on
- **Detect** game state changes

**Example**: A template for the "Alliance" button is a cropped PNG of just that button.

---

## Tools Needed

### Screenshot Tool
- **Windows Snipping Tool** (Win + Shift + S)
- **ShareX** (recommended - https://getsharex.com/)
- **Greenshot** (alternative)

### Image Editor
- **Paint.NET** (recommended - https://www.getpaint.net/)
- **GIMP** (advanced)
- **MS Paint** (basic)

---

## Capturing Templates

### Step-by-Step Process

#### 1. Launch Game in BlueStacks

1. Open BlueStacks
2. Launch Rise of Kingdoms / Call of Dragons
3. Navigate to city view (main screen)
4. Set resolution to **1920x1080**

#### 2. Capture Full Screenshot

**Method A: Using ADB (Recommended)**
```bash
python -c "from src.core.adb import ADBConnection; adb = ADBConnection(); adb.capture_screen('screenshots/full_screen.png')"
```

**Method B: Windows Snipping Tool**
- Press Win + Shift + S
- Capture BlueStacks window
- Save as `full_screen.png`

#### 3. Crop UI Element

Open screenshot in image editor:

1. **Zoom in** on the UI element (100-200% zoom)
2. **Select** just the UI element precisely
   - Include full button/icon
   - Exclude background if possible
   - Keep selection tight (no extra pixels)
3. **Crop** selection (Ctrl+C, Ctrl+N, Ctrl+V in Paint.NET)
4. **Save as PNG**

**Naming Convention:**
- Use descriptive names: `alliance_help_button.png`
- Use lowercase with underscores
- Be specific: `rok_alliance_button.png` vs `cod_alliance_button.png`

#### 4. Save to Correct Location

```
templates/
├── buttons/
│   ├── alliance.png
│   ├── help_all.png
│   ├── back.png
│   └── close.png
├── buildings/
│   ├── barracks.png
│   ├── hospital.png
│   └── city_center.png
├── icons/
│   ├── resource_ready.png
│   ├── march_active.png
│   └── shield.png
├── screens/
│   ├── city_view.png
│   ├── alliance.png
│   └── objectives.png
└── troops/
    ├── tier_1.png
    ├── tier_2.png
    └── tier_4.png
```

---

## Template Best Practices

### ✅ DO

1. **Crop Precisely**
   - Include the entire UI element
   - Remove unnecessary background
   - Keep edges clean and sharp

2. **Use High Quality**
   - Capture from 1920x1080 resolution
   - Save as PNG (lossless)
   - Don't resize or compress

3. **Capture Static Elements**
   - Buttons (non-highlighted state)
   - Icons (standard color)
   - Text (clear, not blurry)

4. **Test Multiple States**
   - Buttons: normal, hover, pressed
   - Text: different languages if needed
   - Icons: different colors/states

5. **Include Context Markers**
   - For screen identification, include unique elements
   - Capture distinctive parts (logos, titles)

### ❌ DON'T

1. **Don't Include Variable Content**
   - No numbers that change (resource amounts, timers)
   - No usernames or server-specific text
   - No dynamic animations

2. **Don't Make Templates Too Large**
   - Keep them minimal (just the element)
   - Larger = slower matching
   - Larger = less flexible

3. **Don't Capture Blurry Elements**
   - Ensure game is fully loaded
   - Wait for animations to finish
   - Avoid motion blur

4. **Don't Use Wrong Resolution**
   - Always use 1920x1080
   - Other resolutions won't match properly

---

## Template Organization

### Directory Structure

```
templates/
├── buttons/              # Clickable buttons
│   ├── alliance.png
│   ├── commanders.png
│   ├── quests.png
│   ├── vip.png
│   ├── help_all.png
│   ├── collect.png
│   ├── confirm.png
│   ├── back.png
│   └── close.png
│
├── buildings/            # City buildings
│   ├── city_center.png
│   ├── barracks.png
│   ├── archery_range.png
│   ├── stable.png
│   ├── siege_workshop.png
│   ├── hospital.png
│   ├── tavern.png
│   └── academy.png
│
├── icons/                # Small icons/indicators
│   ├── resource_ready.png
│   ├── mail_attachment.png
│   ├── march_active.png
│   ├── shield.png
│   ├── objective_complete.png
│   └── quest_complete.png
│
├── screens/              # Screen identifiers
│   ├── city_view.png
│   ├── alliance.png
│   ├── commanders.png
│   ├── objectives.png
│   ├── quests.png
│   └── vip_screen.png
│
├── troops/               # Troop tiers
│   ├── tier_1.png
│   ├── tier_2.png
│   ├── tier_3.png
│   ├── tier_4.png
│   └── tier_5.png
│
├── items/                # Items and resources
│   ├── xp_tome_small.png
│   ├── xp_tome_medium.png
│   └── xp_tome_large.png
│
├── tabs/                 # Navigation tabs
│   ├── quest_main.png
│   ├── quest_side.png
│   └── quest_challenges.png
│
└── notifications/        # Popups and alerts
    ├── incoming_attack.png
    ├── disconnected.png
    └── victory.png
```

---

## Testing Templates

### 1. Manual Test

Use this Python script to test a template:

```python
from src.core.adb import ADBConnection
from src.core.screen import ScreenAnalyzer
import cv2

# Initialize
adb = ADBConnection()
screen = ScreenAnalyzer()

# Capture current screen
screenshot = adb.capture_screen_np()

# Try to find template
location = screen.find_template(
    screenshot,
    'templates/buttons/alliance.png',
    confidence=0.75
)

if location:
    print(f"✅ Template found at: {location}")

    # Draw rectangle on screenshot to visualize
    template = cv2.imread('templates/buttons/alliance.png')
    h, w = template.shape[:2]
    cv2.rectangle(screenshot, location, (location[0]+w, location[1]+h), (0, 255, 0), 2)
    cv2.imwrite('test_result.png', screenshot)
    print("Result saved to test_result.png")
else:
    print("❌ Template not found!")
    print("Tips:")
    print("- Check template quality")
    print("- Try lower confidence (0.6-0.7)")
    print("- Verify game screen matches template")
```

### 2. Confidence Tuning

| Confidence | Use Case |
|-----------|----------|
| **0.95-1.0** | Exact matches only (very strict) |
| **0.85-0.95** | High quality templates (recommended) |
| **0.75-0.85** | Good templates (default) |
| **0.65-0.75** | Flexible matching (lower quality) |
| **< 0.65** | Too loose (false positives likely) |

### 3. Batch Test

Test all templates for an activity:

```bash
python -c "
from pathlib import Path
from src.core.adb import ADBConnection
from src.core.screen import ScreenAnalyzer

adb = ADBConnection()
screen = ScreenAnalyzer()
screenshot = adb.capture_screen_np()

templates = list(Path('templates/buttons').glob('*.png'))
for template_path in templates:
    location = screen.find_template(screenshot, str(template_path), confidence=0.75)
    status = '✅' if location else '❌'
    print(f'{status} {template_path.name}')
"
```

---

## Common Templates Needed

### Priority 1: Core Navigation (REQUIRED)

- `templates/buttons/back.png` - Back button (top-left)
- `templates/buttons/close.png` - Close/X button
- `templates/buttons/home.png` - Home/City button
- `templates/screens/city_view.png` - City view identifier

### Priority 2: Alliance Help Activity

- `templates/buttons/alliance.png` - Alliance button from city
- `templates/buttons/help_all.png` - Help All button
- `templates/screens/alliance.png` - Alliance screen identifier

### Priority 3: VIP Collection

- `templates/buttons/vip.png` - VIP icon
- `templates/buttons/vip_chest.png` - VIP chest
- `templates/buttons/collect.png` - Generic collect button
- `templates/screens/vip_screen.png` - VIP screen identifier

### Priority 4: Resource Management

- `templates/icons/resource_ready.png` - Resource collection indicator
- `templates/buttons/confirm.png` - Confirm button

### Priority 5: Troop Training

- `templates/buildings/barracks.png`
- `templates/buildings/archery_range.png`
- `templates/buildings/stable.png`
- `templates/buildings/siege_workshop.png`
- `templates/buttons/train.png`
- `templates/buttons/train_max.png`
- `templates/buttons/confirm_train.png`
- `templates/troops/tier_4.png`

---

## Advanced Tips

### Multi-Scale Templates

For UI elements that may appear at different sizes:

```python
# The framework can search at multiple scales
location = screen.find_template(
    screenshot,
    'template.png',
    confidence=0.75,
    multi_scale=True  # Searches at 0.5x, 1.0x, 1.5x, 2.0x
)
```

### Region-Based Matching

Speed up matching by searching specific regions:

```python
# Only search top-right corner for resources
region = screenshot[0:100, 1600:1920]
location = screen.find_template(region, 'resource_icon.png')
```

### Color-Based Detection

For resource nodes and barbarians, use color detection instead:

```python
# Find gold nodes (yellow color)
gold_nodes = screen.find_color_regions(
    screenshot,
    lower_hsv=(20, 100, 100),  # Yellow lower bound
    upper_hsv=(30, 255, 255)   # Yellow upper bound
)
```

---

## Troubleshooting Templates

### Template Not Found

**Symptoms**: `find_template()` returns `None`

**Solutions**:
1. Lower confidence threshold (try 0.65-0.70)
2. Re-capture template with better quality
3. Ensure game resolution matches (1920x1080)
4. Check template file exists and is valid PNG
5. Verify you're on the correct screen

### False Positives

**Symptoms**: Template matches wrong element

**Solutions**:
1. Increase confidence threshold (try 0.85-0.95)
2. Make template more specific (include more unique features)
3. Crop template more precisely
4. Use region-based matching to limit search area

### Slow Performance

**Symptoms**: Template matching takes too long

**Solutions**:
1. Make templates smaller
2. Use region-based matching
3. Reduce number of templates checked per frame
4. Cache screenshot between multiple template checks

---

## Next Steps

1. **Create Core Templates**: Start with Priority 1 (navigation)
2. **Test Each Template**: Use manual test script
3. **Run Alliance Help Activity**: Test first complete activity
4. **Iterate and Improve**: Adjust templates based on results

---

**Happy Template Creating!** 🎨
