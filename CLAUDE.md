# WHALEBOTS GAME AUTOMATION PROJECT
*Project-specific instructions for game automation bot*

---

## PROJECT IDENTITY
- **Project**: WhaleBots (rebuilt without licensing)
- **Type**: Standalone desktop automation for Rise of Kingdoms / Call of Dragons
- **Status**: Development (Day 1 core complete)
- **Integration**: None (standalone, no connection to Kozan Citadel yet)

---

## CRITICAL DEVELOPMENT RULES

### 1. NO PLACEHOLDERS
- **NEVER** create abstract/placeholder/framework code
- **ALWAYS** write complete, working implementations
- Use real OpenCV code (`cv2.matchTemplate`, actual thresholds)
- Use real ADB commands (`adb shell input tap`, actual device IDs)
- Use real Tesseract OCR (`pytesseract.image_to_string`, actual preprocessing)
- If you write a function, it must WORK with real hardware/emulator

### 2. COMPLETE IMPLEMENTATIONS ONLY
Every activity implementation must include:
- ✅ Complete prerequisites check logic
- ✅ Step-by-step execution flow
- ✅ Verification methods
- ✅ Error handling with retry logic
- ✅ Configuration parameters
- ✅ Real template matching code
- ✅ Navigation logic between screens

### 3. DOCUMENTATION FIRST
Before implementing new activities:
- Document complete flow in ACTIVITY_FLOWS.md
- Include decision trees and conditional logic
- Specify all templates needed
- Define success/failure criteria
- Map out error recovery paths

### 4. TESTING PRIORITY
- Test with real BlueStacks emulator
- Verify template matching accuracy
- Check ADB connection stability
- Validate activity success rates
- Integration with Kozan Citadel comes AFTER proving feasibility

---

## PROJECT STRUCTURE
Single Python project (NOT a monorepo):
```
GameAutomationFramework/
├── src/core/           # Core systems (ADB, Screen, Activity, Config, Scheduler)
├── src/activities/     # Activity implementations
│   └── base/          # Shared activities (ROK + COD)
├── config/            # JSON configuration files
├── docs/              # Documentation (ACTIVITY_FLOWS.md, etc.)
├── templates/         # UI element images for template matching
└── main.py            # Entry point
```

**NO reorganization needed** - current structure is optimal for this use case.

---

## ACTIVITY IMPLEMENTATION WORKFLOW

1. **Document in ACTIVITY_FLOWS.md**
   - Prerequisites logic
   - Execution flow (step-by-step)
   - Verification method
   - Error handling
   - Configuration example

2. **Create activity class in `src/activities/base/`**
   - Inherit from `Activity` base class
   - Implement `check_prerequisites()`
   - Implement `execute()`
   - Implement `verify_completion()`

3. **Add configuration to `config/activities_rok.json`**
   - Activity ID, name, interval, priority
   - Parameters specific to activity
   - Enable/disable flag

4. **Create template images in `templates/`**
   - Capture from real game screenshots
   - Crop precisely around UI elements
   - Save as PNG with descriptive names

5. **Test end-to-end**
   - Run with `python main.py --game rok --duration 300`
   - Verify activity executes successfully
   - Check logs for errors
   - Adjust templates/thresholds as needed

---

## TIMELINE & PRIORITIES

### IMMEDIATE (Current Phase)
- [ ] Create template images for Alliance Help
- [ ] Test Alliance Help end-to-end
- [ ] Fix any bugs discovered during testing

### SHORT TERM (This Week)
- [ ] Implement VIP Collection (4 hours)
- [ ] Implement Daily Login (4 hours)
- [ ] Implement Building Upgrades (16 hours)
- [ ] Test all activities

### MEDIUM TERM (Week 2)
- [ ] Resource Gathering (40 hours - most complex)
- [ ] Barbarian Hunt (24 hours)
- [ ] 40+ remaining activities (parallel development)

### LONG TERM (Week 3+)
- [ ] PyQt6 desktop UI
- [ ] Unit/integration testing
- [ ] Packaging (.exe with PyInstaller)
- [ ] Consider Kozan Citadel integration

---

## TECHNICAL CONSTRAINTS

### Detection Avoidance
- Randomize click positions (±5px variance)
- Random delays between actions (500-2000ms)
- Human-like timing patterns
- Avoid perfect repeatability

### Performance Requirements
- Screenshot capture: <1 second
- Template matching: <500ms per image
- Activity execution: <5 minutes typical
- Success rate: >80% target

### Platform Requirements
- BlueStacks emulator (ADB enabled)
- Windows 10/11
- Python 3.11+
- Tesseract OCR installed
- Screen resolution: 1920x1080

---

## SAFETY REMINDERS
⚠️ **This violates game Terms of Service**
⚠️ **Account ban risk exists**
⚠️ **Use on test accounts only**
⚠️ **Don't run 24/7 - use time windows**
⚠️ **Randomization is critical for safety**

---

## INTEGRATION RULES (Future)
When eventually integrating with Kozan Citadel:
- Wrap scheduler in REST API (FastAPI)
- Expose start/stop/status endpoints
- Database integration for statistics
- Multi-account management
- Web dashboard control

**But NOT YET** - prove standalone works first!

---

## COMMON PITFALLS TO AVOID
❌ Creating abstract frameworks instead of working code
❌ Using placeholder template paths
❌ Skipping verification logic
❌ Not handling edge cases (disconnects, wrong screen, etc.)
❌ Reorganizing structure instead of building features
❌ Planning integration before testing standalone
❌ Using perfect timing (makes detection easy)

✅ Write complete, testable, working code
✅ Handle all error cases
✅ Focus on making one activity work before adding more
✅ Test with real hardware early and often
