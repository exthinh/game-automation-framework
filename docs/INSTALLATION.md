# Installation Guide

Complete setup guide for the Game Automation Framework.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation Steps](#installation-steps)
3. [BlueStacks Setup](#bluestacks-setup)
4. [Tesseract OCR Setup](#tesseract-ocr-setup)
5. [Verification](#verification)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

| Software | Version | Purpose |
|----------|---------|---------|
| **Python** | 3.11+ | Runtime environment |
| **BlueStacks** | 5.0+ | Android emulator |
| **Tesseract OCR** | 5.0+ | Text recognition |
| **Git** | Latest | Version control |

### System Requirements

- **OS**: Windows 10/11 (64-bit)
- **RAM**: 8 GB minimum, 16 GB recommended
- **Storage**: 10 GB free space
- **CPU**: Intel/AMD with virtualization support
- **Screen Resolution**: 1920x1080 recommended

---

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/exthinh/game-automation-framework.git
cd game-automation-framework
```

### 2. Create Virtual Environment

**Windows Command Prompt:**
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

**PowerShell:**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Git Bash:**
```bash
python -m venv venv
source venv/Scripts/activate
```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

**Expected packages:**
- opencv-python >= 4.8.0
- pytesseract >= 0.3.10
- Pillow >= 10.0.0
- numpy >= 1.24.0
- watchdog >= 3.0.0

---

## BlueStacks Setup

### 1. Download and Install

1. Visit https://www.bluestacks.com/
2. Download BlueStacks 5 (latest version)
3. Run installer and follow prompts
4. Launch BlueStacks after installation

### 2. Enable ADB

**Steps:**
1. Open BlueStacks Settings (gear icon)
2. Navigate to **Advanced**
3. Enable **Android Debug Bridge (ADB)**
4. Note the ADB port (usually `5555`)
5. Restart BlueStacks

**Verify ADB:**
```bash
adb devices
```

Expected output:
```
List of devices attached
127.0.0.1:5555  device
```

### 3. Configure BlueStacks

**Recommended Settings:**
- **Resolution**: 1920x1080 (Custom)
- **DPI**: 240
- **CPU cores**: 4
- **Memory**: 4096 MB
- **Performance mode**: High performance
- **Graphics**: DirectX (or OpenGL if DirectX has issues)

### 4. Install Game

1. Open Google Play Store in BlueStacks
2. Sign in with Google account
3. Search for "Rise of Kingdoms" or "Call of Dragons"
4. Install game
5. Launch and complete tutorial

---

## Tesseract OCR Setup

### 1. Download Tesseract

Visit: https://github.com/UB-Mannheim/tesseract/wiki

Download: `tesseract-ocr-w64-setup-5.3.3.20231005.exe` (or latest)

### 2. Install Tesseract

1. Run installer
2. **Important**: Note the installation path (e.g., `C:\Program Files\Tesseract-OCR`)
3. During installation, select **Additional language data**
4. Include English language pack

### 3. Add to PATH

**Option A: During Installation**
- Check "Add Tesseract to PATH" during install

**Option B: Manual**
1. Open System Properties → Advanced → Environment Variables
2. Under System Variables, find `Path`
3. Click Edit → New
4. Add: `C:\Program Files\Tesseract-OCR`
5. Click OK on all dialogs

### 4. Verify Installation

```bash
tesseract --version
```

Expected output:
```
tesseract 5.3.3
```

---

## Configuration

### 1. Configure Accounts

Copy example config and edit:
```bash
cp config/accounts.example.json config/accounts.json
```

Edit `config/accounts.json`:
```json
{
  "accounts": [
    {
      "account_id": "account_001",
      "account_name": "Main Account",
      "server_name": "1234",
      "device_id": "127.0.0.1:5555",
      "enabled": true
    }
  ],
  "emulator": {
    "emulator_type": "BlueStacks",
    "adb_host": "127.0.0.1",
    "adb_port": 5555
  }
}
```

### 2. Configure Activities

Edit `config/activities_rok.json` for Rise of Kingdoms:
```json
{
  "alliance_help": {
    "enabled": true,
    "interval_minutes": 30,
    "priority": 5
  },
  "vip_collection": {
    "enabled": true,
    "interval_hours": 24,
    "priority": 2
  }
}
```

---

## Verification

### 1. Test ADB Connection

```bash
python -c "from src.core.adb import ADBConnection; adb = ADBConnection(); print('Devices:', adb.get_devices())"
```

Expected output:
```
Devices: ['127.0.0.1:5555']
```

### 2. Test Screen Capture

```bash
python -c "from src.core.adb import ADBConnection; adb = ADBConnection(); adb.capture_screen('test.png'); print('Screenshot saved to test.png')"
```

Check that `test.png` exists and shows the emulator screen.

### 3. Test OCR

```bash
python -c "from src.core.screen import ScreenAnalyzer; import cv2; screen = ScreenAnalyzer(); img = cv2.imread('test.png'); print('Text:', screen.read_text(img[:100, :200]))"
```

Should print some text from the screenshot.

### 4. Run Framework

```bash
python main.py --game rok --duration 60
```

This runs the bot for 1 minute in test mode.

---

## Troubleshooting

### ADB Not Found

**Error**: `adb: command not found`

**Solutions**:
1. Ensure BlueStacks is running
2. Enable ADB in BlueStacks settings
3. Add Android Platform Tools to PATH
4. Restart terminal/command prompt

### Tesseract Not Found

**Error**: `TesseractNotFoundError`

**Solutions**:
1. Verify Tesseract installation: `tesseract --version`
2. Add Tesseract to PATH
3. Set `TESSDATA_PREFIX` environment variable
4. Restart terminal

### BlueStacks Connection Failed

**Error**: `error: cannot connect to 127.0.0.1:5555`

**Solutions**:
1. Restart BlueStacks
2. Check ADB is enabled in settings
3. Try: `adb kill-server` then `adb start-server`
4. Check if port 5555 is open: `netstat -an | findstr 5555`

### Template Matching Failed

**Error**: Templates not found or matching fails

**Solutions**:
1. Ensure game resolution matches templates (1920x1080)
2. Capture new templates for your game version
3. Adjust confidence threshold in activity configs
4. See [Template Creation Guide](TEMPLATE_CREATION.md)

### OCR Accuracy Issues

**Error**: Wrong text detected

**Solutions**:
1. Ensure English language pack installed for Tesseract
2. Improve screenshot quality (higher resolution)
3. Preprocess images (see `ScreenAnalyzer.read_text()`)
4. Use template matching instead where possible

---

## Next Steps

1. **Create Templates**: See [Template Creation Guide](TEMPLATE_CREATION.md)
2. **Configure Activities**: Edit `config/activities_rok.json`
3. **Test Activities**: Run in test mode with `--duration 300`
4. **Read Documentation**: Check [Quick Start Guide](../QUICK_START.md)

---

## Getting Help

- **Issues**: https://github.com/exthinh/game-automation-framework/issues
- **Documentation**: See `/docs` folder
- **Configuration Examples**: See `/config` folder

---

**Status**: Installation guide complete ✅
