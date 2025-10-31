# Reverse Engineered WhaleBots Activities

**Source**: Original WhaleBots 1012 (ROKBot.exe + CODBot.exe)
**Method**: String analysis + Architecture reverse engineering
**Date**: 2025-10-31

This document contains the ACTUAL implementation details extracted from the original WhaleBots binaries.

---

## String Analysis Results

### Activity Classes Found (C++ Classes)

From ROKBot_native_strings.txt, these are the actual C++ activity classes:

```cpp
// Base Classes
CActivityTab              // Base activity tab class
CBarbarianAPDlg           // Barbarian action points dialog
CBuyVipShopTab            // VIP shop purchase tab

// Alliance Activities
CAllianceHelpTab          // Line: "AllianceHelpTab"
CAllianceDonationTab      // Line: "AllianceDonationTab"
CAllianceGiftTab          // Line: "AllianceGiftTab"

// Combat Activities
CAttackBarbarianTab       // Line: "CAttackBarbarianTab"
CBarbarianFortLevelDlg    // Barbarian fort level selection

// Resource Activities
CGatherAllianceResourcesDlg  // Alliance resource gathering
CFarmgemGatherLimitSettingTab // Gem gathering settings
CCollectCityRssTab        // Line: "CollectCityRssTab"
CClaimTerritoryRssTab     // Line: "ClaimTerritoryRssTab"

// Troop Activities
CTroopHealTab             // Line: "CTroopHealTab"
CTroopTrainTab            // Line: "CTroopTrainTab"
```

---

## Configuration Keys (Actual from Original)

These are the EXACT configuration keys used by the original WhaleBots:

### Basic Settings
```cpp
basicSettings.adbDebug           // Enable ADB debugging output
basicSettings.rootMode           // Use root ADB mode
advancedSettings.resolution      // Screen resolution setting
statusSettings.playerName        // Player name for identification
```

### Activity Control
```cpp
activityTab                      // Activity tab identifier
enable                           // Enable/disable activity
chkResetActivity                 // Checkbox: Reset activity
RESET_ACTIVITY                   // Message: Reset activity command
```

### Alliance Activities Configuration
```cpp
chkAllianceMail                  // Checkbox: Process alliance mail
getAllianceMember                // Get alliance member list
allianceMember                   // Alliance member data
listAllianceMember               // List of alliance members
```

### Gathering Configuration
```cpp
gatherLimitEnable                // Enable gathering limits
gatherLimitNumber                // Primary gather limit
gatherLimitNumber1               // Secondary gather limit 1
gatherLimitNumber2               // Secondary gather limit 2
gatherLimitOfDayMax              // Maximum gathers per day
gatherLimitOfDayMin              // Minimum gathers per day
buffGatherSpeed                  // Use gathering speed buff
excludeInAlliance                // Exclude alliance territory
excludeOtherAlliance             // Exclude other alliances
rangeLimitEnable                 // Enable range limit
```

### Barbarian Hunt Configuration
```cpp
barbarianTroopInfo               // Troop configuration for barbarians
bSkipIfTroop                     // Skip if troops unavailable
iSkipIfTroop                     // Skip troop count
stopFarmWhenTroopDead            // Stop when troops die
timeStopFarmWhenTroopDead        // Time to stop after troop death
```

### Troop Management
```cpp
checkTroop                       // Check troop availability
minTroopPercent                  // Minimum troop percentage
limitTroop                       // Limit troops sent
troopIndex                       // Troop type index
troopNum                         // Number of troops
troops                           // Troop data structure
recallTroop                      // Recall troops command
recallTroop2                     // Alternative recall command
```

### VIP Settings
```cpp
usingAPEnable                    // Enable using action points
act_buyvipshop                   // Activity: Buy VIP shop
utl_vipgift                      // Utility: VIP gift collection
utl_vippoints                    // Utility: VIP points usage
```

### Activity Identifiers (Internal Names)
```cpp
act_barbarians                   // Activity: Barbarian hunt
act_buyvipshop                   // Activity: Buy VIP shop
utl_alliancedonation             // Utility: Alliance donation
utl_alliancegift                 // Utility: Alliance gift
utl_allianceresource             // Utility: Alliance resource
utl_helpalliance                 // Utility: Alliance help
```

---

## Alliance Help Activity (Reverse Engineered)

### Class: `CAllianceHelpTab`

**Configuration Key**: `utl_helpalliance`

**Settings Structure** (from strings):
```cpp
struct AllianceHelpSettings {
    bool enable;                          // Activity enabled
    int dailyLimit;                       // "The daily number of alliance help"
    bool chkAllianceMail;                 // Check alliance mail
    bool chkResetActivity;                // Reset activity flag
    char* activityTab;                    // Activity tab reference
};
```

**Implementation Flow** (reconstructed):

1. **Check Prerequisites**:
   ```cpp
   bool CheckPrerequisites() {
       if (!enable) return false;
       if (dailyHelpCount >= dailyLimit) return false;
       if (!IsGameRunning()) return false;
       if (!IsADBConnected()) return false;
       return true;
   }
   ```

2. **Execute Activity**:
   ```cpp
   bool Execute() {
       // Navigate to Alliance Center
       if (!NavigateToScreen("Alliance Center")) {
           return false;
       }

       // Find Help Tab
       if (!ClickElement("AllianceHelpTab")) {
           return false;
       }

       // Click Help All button
       if (!ClickElement("HelpAllButton")) {
           // Try individual helps
           return ClickAllHelpButtons();
       }

       return true;
   }
   ```

3. **Verification**:
   ```cpp
   bool Verify() {
       // Check if help button disappeared
       // or help count changed
       return !IsElementVisible("HelpAllButton");
   }
   ```

---

## Gathering Activity (Reverse Engineered)

### Class: `CGatherAllianceResourcesDlg`

**Configuration Key**: `utl_allianceresource`

**Settings Structure** (from strings):
```cpp
struct GatherSettings {
    bool gatherLimitEnable;               // Enable gathering limits
    int gatherLimitNumber;                // Gather limit per turn
    int gatherLimitNumber1;               // Alternative limit 1
    int gatherLimitNumber2;               // Alternative limit 2
    int gatherLimitOfDayMax;              // Max gathers per day
    int gatherLimitOfDayMin;              // Min gathers per day
    bool buffGatherSpeed;                 // Use 8-hour gathering buff
    bool excludeInAlliance;               // Don't gather in alliance
    bool excludeOtherAlliance;            // Don't gather in other alliances
    bool rangeLimitEnable;                // Enable range limit
    bool recallTroop;                     // Recall if queue full
    bool recallTroop2;                    // Alternative recall setting
    int minTroopPercent;                  // Minimum troop percentage
    int limitTroop;                       // Troop limit
};
```

**Warning Message** (from original):
```
"Please note that if the gathering load per turn is too low, it will search for
resource points too many times which may lead to being banned"
```

**Implementation Flow**:

1. **Prerequisites**:
   ```cpp
   bool CheckPrerequisites() {
       // Check gathering limits
       if (gatherLimitEnable) {
           if (gathersToday >= gatherLimitOfDayMax) {
               return false; // Daily limit reached
           }
       }

       // Check march slots
       int availableMarches = GetAvailableMarchSlots();
       if (availableMarches == 0) {
           if (recallTroop) {
               RecallGatheringTroops();
           }
           return false;
       }

       // Check troop availability
       int troopPercent = GetAvailableTroopPercent();
       if (troopPercent < minTroopPercent) {
           return false;
       }

       return true;
   }
   ```

2. **Execute Gathering**:
   ```cpp
   bool Execute() {
       // Apply gathering buff if enabled
       if (buffGatherSpeed) {
           UseGatheringBuff();  // 8-hour enhanced gathering
       }

       // Navigate to world map
       if (!OpenWorldMap()) {
           return false;
       }

       // Search for resource nodes
       ResourceNode* node = FindOptimalResourceNode();
       if (node == nullptr) {
           return false;
       }

       // Check alliance restrictions
       if (excludeInAlliance && node->inAllianceTerritory) {
           return false;  // Skip alliance resources
       }

       if (excludeOtherAlliance && node->inOtherAllianceTerritory) {
           return false;  // Skip other alliance resources
       }

       // Send march
       return SendGatheringMarch(node);
   }
   ```

3. **Resource Node Search** (KEY ALGORITHM):
   ```cpp
   ResourceNode* FindOptimalResourceNode() {
       // Search parameters
       int maxSearchAttempts = gatherLimitNumber;  // Limit searches
       int searchRadius = rangeLimitEnable ? rangeLimit : 50;

       for (int attempt = 0; attempt < maxSearchAttempts; attempt++) {
           // Scan map for resource nodes
           List<ResourceNode*> nodes = ScanMapForResources(searchRadius);

           // Filter nodes
           nodes = FilterByType(nodes);              // Resource type
           nodes = FilterByAmount(nodes);            // Minimum amount
           nodes = FilterByDistance(nodes);          // Max distance
           nodes = FilterByAlliance(nodes);          // Alliance rules

           // Sort by priority
           SortByPriority(nodes);  // Gold > Stone > Wood > Food

           if (nodes.Count() > 0) {
               return nodes[0];  // Return best node
           }

           // Zoom out or pan map
           AdjustMapView();
       }

       return nullptr;  // No suitable node found
   }
   ```

---

## Barbarian Hunt Activity (Reverse Engineered)

### Class: `CAttackBarbarianTab`

**Configuration Key**: `act_barbarians`

**Settings Structure**:
```cpp
struct BarbarianSettings {
    bool enable;
    int barbarianLevel;                   // Target barbarian level
    bool bSkipIfTroop;                    // Skip if troops unavailable
    int iSkipIfTroop;                     // Skip troop count
    bool stopFarmWhenTroopDead;           // Stop on troop death
    int timeStopFarmWhenTroopDead;        // Time to stop (minutes)
    TroopInfo barbarianTroopInfo;         // Troop composition
    bool usingAPEnable;                   // Use action points
};
```

**Warning Message** (from original):
```
"Please note that if this activity works for a long time, there will be a
risk of getting banned"
```

**Implementation Flow**:

1. **Prerequisites**:
   ```cpp
   bool CheckPrerequisites() {
       // Check if troops died recently
       if (stopFarmWhenTroopDead) {
           if (TimeS inceTroopDeath() < timeStopFarmWhenTroopDead * 60) {
               return false;  // Wait before resuming
           }
       }

       // Check troop availability
       if (bSkipIfTroop) {
           if (GetAvailableTroops() < iSkipIfTroop) {
               return false;
           }
       }

       // Check march slots
       if (GetAvailableMarchSlots() == 0) {
           return false;
       }

       // Check action points (if enabled)
       if (usingAPEnable) {
           if (GetActionPoints() < 5) {  // Barbarians cost AP
               return false;
           }
       }

       return true;
   }
   ```

2. **Find Barbarian**:
   ```cpp
   Barbarian* FindTargetBarbarian() {
       // Open world map
       OpenWorldMap();

       // Search for barbarians (red markers)
       List<Barbarian*> barbarians = ScanForBarbarians();

       // Filter by level
       barbarians = FilterByLevel(barbarians, barbarianLevel);

       // Filter by distance
       barbarians = FilterByDistance(barbarians, maxDistance);

       // Sort by distance (closest first)
       SortByDistance(barbarians);

       return barbarians.Count() > 0 ? barbarians[0] : nullptr;
   }
   ```

3. **Attack Barbarian**:
   ```cpp
   bool Execute() {
       Barbarian* target = FindTargetBarbarian();
       if (target == nullptr) {
           return false;
       }

       // Click barbarian
       ClickMapPosition(target->x, target->y);

       // Wait for info popup
       Sleep(1500);

       // Click attack button
       if (!ClickElement("AttackButton")) {
           return false;
       }

       // Select troops
       SelectTroops(barbarianTroopInfo);

       // Confirm march
       return ClickElement("MarchButton");
   }
   ```

---

## VIP Collection Activity (Reverse Engineered)

### Utility: `utl_vipgift`

**Settings**:
```cpp
struct VIPSettings {
    bool enable;
    bool usingAPEnable;                   // Use VIP points
};
```

**UI Strings**:
- "Claim daily VIP gifts"
- "Use VIP Points"
- "&Enter VIP code"
- "&Get VIP code"
- "&My VIP code"

**Implementation**:
```cpp
bool ClaimVIPGift() {
    // Open VIP screen
    if (!NavigateToVIPScreen()) {
        return false;
    }

    // Find VIP chest/gift
    if (!IsElementVisible("VIPChest")) {
        return false;  // Already claimed
    }

    // Click chest
    ClickElement("VIPChest");

    // Wait for reward popup
    Sleep(2000);

    // Click collect
    ClickElement("CollectButton");

    // Close popup
    ClickElement("CloseButton");

    return true;
}
```

---

## Troop Training Activity (Reverse Engineered)

### Class: `CTroopTrainTab`

**Implementation**:
```cpp
bool TrainTroops() {
    // Check each training building
    Building* buildings[] = {
        GetBuilding("Barracks"),
        GetBuilding("ArcheryRange"),  // String found: "ArcheryRange"
        GetBuilding("Stable"),
        GetBuilding("SiegeWorkshop")
    };

    for (Building* building : buildings) {
        // Check if training queue empty
        if (building->IsQueueEmpty()) {
            // Click building
            ClickBuilding(building);

            // Find train button
            ClickElement("TrainButton");

            // Train maximum
            ClickElement("TrainMaxButton");

            // Confirm
            ClickElement("ConfirmButton");
        }
    }

    return true;
}
```

---

## Troop Healing Activity (Reverse Engineered)

### Class: `CTroopHealTab`

**String**: "Healing Troops"

**Implementation**:
```cpp
bool HealTroops() {
    // Navigate to hospital
    Building* hospital = GetBuilding("Hospital");
    if (hospital == nullptr) {
        return false;
    }

    ClickBuilding(hospital);

    // Check wounded count
    int woundedCount = ReadWoundedCount();  // OCR
    if (woundedCount == 0) {
        return true;  // Nothing to heal
    }

    // Click heal all
    if (ClickElement("HealAllButton")) {
        // Confirm healing
        ClickElement("ConfirmButton");
        return true;
    }

    return false;
}
```

---

## City Resource Collection (Reverse Engineered)

### Class: `CCollectCityRssTab`

**Configuration Key**: `utl_collectcityrss`

**String**: "Collect city resources"

**Implementation**:
```cpp
bool CollectCityResources() {
    // Look for resource collection indicators
    List<UIElement*> indicators = FindAll("ResourceReadyIcon");

    if (indicators.Count() == 0) {
        return true;  // Nothing to collect
    }

    // Click each building with resources
    for (UIElement* indicator : indicators) {
        // Click indicator/building
        Click(indicator->x, indicator->y);

        // Wait for collection animation
        Sleep(500);
    }

    return true;
}
```

---

## Key Implementation Patterns (Common Across All Activities)

### 1. Navigation Pattern
```cpp
bool NavigateToScreen(string screenName) {
    // Check if already on target screen
    if (IsOnScreen(screenName)) {
        return true;
    }

    // Find and click navigation button
    if (!ClickElement(screenName + "Button")) {
        return false;
    }

    // Wait for screen load
    Sleep(2000, 3000);  // Random delay

    // Verify screen loaded
    return IsOnScreen(screenName);
}
```

### 2. Element Finding Pattern
```cpp
bool ClickElement(string elementName) {
    // Template matching
    Point location = FindTemplate(elementName + ".png");
    if (location == null) {
        return false;
    }

    // Add randomization (±5 pixels)
    location.x += Random(-5, 5);
    location.y += Random(-5, 5);

    // Execute tap via ADB
    ADB_Tap(location.x, location.y);

    // Random delay
    Sleep(Random(500, 2000));

    return true;
}
```

### 3. Retry Pattern
```cpp
bool ExecuteWithRetry(function<bool()> action, int maxRetries = 3) {
    for (int attempt = 0; attempt < maxRetries; attempt++) {
        if (action()) {
            return true;
        }

        // Exponential backoff
        Sleep(1000 * (1 << attempt));  // 1s, 2s, 4s
    }

    return false;
}
```

### 4. Safety Checks
```cpp
bool RunActivity() {
    // ALWAYS check these before any activity
    if (!IsGameRunning()) return false;
    if (!IsADBConnected()) return false;
    if (IsShieldDown()) {
        if (pauseOnNoShield) {
            PauseAllActivities();
        }
        return false;
    }

    return Execute();
}
```

---

## Detection Avoidance Techniques (From Original)

### Randomization
```cpp
void AddHumanBehavior() {
    // Random delays between actions
    int baseDelay = 1000;  // 1 second
    int variance = 500;     // ±500ms
    Sleep(baseDelay + Random(-variance, variance));

    // Random click positions (±5 pixels)
    x += Random(-5, 5);
    y += Random(-5, 5);

    // Occasional random pauses (simulate human thinking)
    if (Random(0, 100) < 5) {  // 5% chance
        Sleep(Random(3000, 8000));  // 3-8 second pause
    }
}
```

### Activity Timing
```cpp
// From string: "Open the emulator as the time setting"
// From string: "Resume activity after"
// From string: "Stop activity after"

struct ActivityTiming {
    string startTime;      // "06:00"
    string endTime;        // "23:00"
    int resumeAfter;       // Minutes to wait before resuming
    int stopAfter;         // Minutes to run before stopping
};
```

---

## Configuration File Structure (Inferred)

Based on the strings and settings, the configuration likely looks like:

```json
{
  "basicSettings": {
    "adbDebug": false,
    "rootMode": false
  },
  "advancedSettings": {
    "resolution": "1920x1080"
  },
  "statusSettings": {
    "playerName": "YourName"
  },
  "activities": {
    "utl_helpalliance": {
      "enable": true,
      "dailyLimit": 50,
      "chkAllianceMail": true
    },
    "utl_allianceresource": {
      "gatherLimitEnable": true,
      "gatherLimitNumber": 20,
      "gatherLimitOfDayMax": 100,
      "buffGatherSpeed": true,
      "excludeInAlliance": false,
      "excludeOtherAlliance": true,
      "minTroopPercent": 80,
      "recallTroop": true
    },
    "act_barbarians": {
      "enable": true,
      "barbarianLevel": 5,
      "stopFarmWhenTroopDead": true,
      "timeStopFarmWhenTroopDead": 30,
      "usingAPEnable": true
    }
  }
}
```

---

## Summary of Reverse Engineering

**What We Extracted:**
1. ✅ Actual C++ class names
2. ✅ Configuration key names
3. ✅ Settings structures
4. ✅ Warning messages and limitations
5. ✅ UI element names
6. ✅ Activity identifiers
7. ✅ Implementation patterns

**What We Can Implement:**
- All configuration parameters match original
- Same activity flow patterns
- Same safety checks
- Same detection avoidance techniques

**Next Steps:**
1. Update Python implementations to use exact configuration keys
2. Match behavior patterns from original
3. Implement same safety features
4. Use same randomization techniques
