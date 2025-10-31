# Complete Activity Flows - Step-by-Step Documentation

**Purpose**: Detailed flowcharts and logic for EVERY activity.
Each activity includes:
- Prerequisites check logic
- Step-by-step execution flow
- Verification logic
- Error handling
- Configuration parameters
- Screen navigation paths

---

## How to Read This Document

Each activity follows this format:

```
## Activity Name

### Configuration
{All parameters this activity needs}

### Prerequisites Check
{What must be true before running}

### Execution Flow
{Step-by-step what happens}

### Verification
{How we know it worked}

### Error Scenarios
{What can go wrong and how to handle it}
```

---

# BASIC ACTIVITIES (Easy - 1 day each)

## 1. Alliance Help

**Complexity**: LOW
**Execution Time**: 30-60 seconds
**Success Rate**: 95%+

### Configuration Parameters
```json
{
  "id": "alliance_help",
  "interval_minutes": 10,
  "priority": 5,
  "parameters": {
    "help_all": true,
    "max_helps": 50
  }
}
```

### Prerequisites Check Flow
```
START check_prerequisites()
│
├─ Check: Is game running?
│  └─ NO → Return FALSE
│  └─ YES → Continue
│
├─ Check: Are we logged in?
│  └─ NO → Return FALSE
│  └─ YES → Continue
│
├─ Check: Is alliance screen accessible?
│  └─ NO → Return FALSE
│  └─ YES → Continue
│
└─ Return TRUE
END
```

### Execution Flow
```
START execute()
│
STEP 1: Navigate to Alliance Screen
├─ Capture current screenshot
├─ Check: Are we already on alliance screen?
│  ├─ YES → Skip to Step 2
│  └─ NO → Continue
├─ Find "Alliance" button using template matching
│  ├─ Template: templates/buttons/alliance.png
│  ├─ Confidence: 0.8
│  └─ If NOT found → Return FALSE
├─ Tap alliance button coordinates
├─ Wait 2-3 seconds (random delay)
├─ Verify: Alliance screen loaded
│  └─ Check for alliance screen indicators
│
STEP 2: Find "Help All" Button
├─ Capture screenshot
├─ Template match: templates/buttons/help_all.png
│  ├─ Confidence threshold: 0.8
│  └─ Multi-scale: YES
├─ If NOT found:
│  ├─ Log: "Help All button not found"
│  ├─ Possible reasons:
│  │   ├─ No members need help
│  │   ├─ Daily help limit reached
│  │   └─ Wrong screen
│  └─ Return FALSE
├─ If found: Record button location (x, y)
│
STEP 3: Tap "Help All" Button
├─ Add randomization: ±5 pixels
├─ Final coordinates: (x + random(-5, 5), y + random(-5, 5))
├─ Execute tap command via ADB
├─ Random delay: 100-300ms
│
STEP 4: Wait for Action
├─ Wait 1-2 seconds (random)
├─ Allow time for game to process
│
STEP 5: Check for Confirmation
├─ Capture new screenshot
├─ Look for success indicators:
│  ├─ Help button disappeared?
│  ├─ Help count decreased?
│  └─ Success animation appeared?
│
└─ Return TRUE
END execute()
```

### Verification Flow
```
START verify_completion()
│
METHOD 1: Button Disappeared
├─ Capture screenshot
├─ Try to find "Help All" button again
├─ If NOT found → Help was successful
│  └─ Return TRUE
│
METHOD 2: Help Count Changed (Alternative)
├─ Read help count from screen (OCR)
├─ Compare with pre-execution count
├─ If decreased → Success
│  └─ Return TRUE
│
METHOD 3: Timeout Check
├─ If waited > 5 seconds with no change
│  └─ Return FALSE (uncertain)
│
└─ Default: Return FALSE if unsure
END
```

### Error Scenarios

**Error 1: Can't find Alliance button**
```
Cause: Different screen, UI changed, wrong resolution
Solution:
1. Try alternative navigation (home → alliance)
2. Check if templates need updating
3. Return FALSE to retry later
```

**Error 2: Help All button not found**
```
Cause: No members need help OR daily limit reached
Solution:
1. This is NORMAL, not an error
2. Log as INFO, not ERROR
3. Return FALSE (will retry in 10 minutes)
4. Don't increment failure count
```

**Error 3: Button found but tap doesn't work**
```
Cause: Button moved, lag, wrong coordinates
Solution:
1. Retry tap once
2. Verify screen didn't change
3. If still fails, return FALSE
```

---

## 2. VIP Collection

**Complexity**: LOW
**Execution Time**: 20-40 seconds
**Success Rate**: 90%+

### Configuration
```json
{
  "id": "vip_collection",
  "interval_hours": 24,
  "priority": 3,
  "parameters": {
    "collect_all_rewards": true
  }
}
```

### Prerequisites Flow
```
START check_prerequisites()
│
├─ Check: Game running and logged in?
│  └─ NO → Return FALSE
│
├─ Check: VIP level > 0?
│  └─ NO → Return FALSE (no VIP rewards)
│
├─ Check: Last collection was >23 hours ago?
│  └─ NO → Return FALSE (too soon)
│
└─ Return TRUE
END
```

### Execution Flow
```
START execute()
│
STEP 1: Open VIP Screen
├─ Current location: Unknown (could be anywhere)
├─ Option A: Navigate from city view
│  ├─ Find "VIP" icon/button
│  ├─ Template: templates/buttons/vip.png
│  └─ Tap if found
├─ Option B: Navigate from menu
│  ├─ Open main menu
│  ├─ Find VIP option
│  └─ Tap
├─ Wait 2-3 seconds for screen load
│
STEP 2: Find VIP Chest/Reward
├─ Capture VIP screen
├─ Look for collection indicators:
│  ├─ Red notification dot?
│  ├─ Chest icon?
│  ├─ "Collect" button?
│  └─ Glowing animation?
├─ Template match:
│  ├─ templates/vip/daily_chest.png
│  ├─ templates/vip/collect_button.png
│  └─ Confidence: 0.7 (lower because varies by VIP level)
│
STEP 3: Tap Collection Element
├─ If found chest: Tap chest location
├─ Random offset: ±5 pixels
├─ Wait 1-2 seconds
│
STEP 4: Handle Popup/Confirmation
├─ Capture screen
├─ Check for reward popup
├─ If popup found:
│  ├─ Find "Collect" or "OK" button
│  ├─ Tap button
│  └─ Wait 1 second
│
STEP 5: Exit Screen
├─ Tap back button or close button
├─ Return to main screen
│
└─ Return TRUE
END
```

### Verification Flow
```
START verify_completion()
│
CHECK 1: Notification Gone?
├─ Look for red dot on VIP icon
├─ If gone → Collection likely successful
│
CHECK 2: Reward Popup Showed?
├─ Did we detect reward popup in execution?
├─ If YES → Success
│
CHECK 3: Chest Animation?
├─ Did chest appearance change?
├─ Closed/opened animation?
│
RESULT:
├─ If any check passes → Return TRUE
└─ If all fail → Return FALSE
END
```

---

## 3. Resource Gathering (COMPLEX)

**Complexity**: HIGH
**Execution Time**: 2-5 minutes
**Success Rate**: 80-90%

This is THE MOST IMPORTANT activity - used constantly.

### Configuration
```json
{
  "id": "gathering",
  "interval_minutes": 5,
  "priority": 2,
  "parameters": {
    "resource_types": ["food", "wood", "stone", "gold"],
    "resource_priority": ["gold", "stone", "wood", "food"],
    "min_amount": 50000,
    "max_march_distance": 30,
    "min_troops_for_gather": 5000,
    "auto_return_on_full": true,
    "avoid_enemy_territory": true
  }
}
```

### Prerequisites Flow (Detailed)
```
START check_prerequisites()
│
CHECK 1: March Slots Available?
├─ Navigate to march management screen
├─ Count current active marches
├─ Get max marches (from VIP level, tech)
├─ Calculate: available_slots = max_marches - active_marches
├─ If available_slots == 0:
│  ├─ Log: "No march slots available"
│  ├─ Calculate: time_until_return = earliest_march_return_time
│  ├─ Schedule next check: current_time + time_until_return
│  └─ Return FALSE
├─ If available_slots > 0: Continue
│
CHECK 2: Troops Available?
├─ Go to city/barracks screen
├─ Count idle troops (not in marches, not healing)
├─ Calculate: total_available = infantry + cavalry + archers
├─ If total_available < min_troops_for_gather:
│  ├─ Log: "Not enough troops (need {min}, have {total})"
│  └─ Return FALSE
│
CHECK 3: Warehouse Capacity?
├─ Check current resource amounts
├─ Check warehouse capacity
├─ Calculate: usage_percent = current / capacity * 100
├─ If usage_percent > 90:
│  ├─ Log: "Warehouse nearly full ({usage_percent}%)"
│  ├─ Note: Should trigger resource spending activities
│  └─ Return FALSE
│
CHECK 4: Action Points/Stamina?
├─ Check current action points (if game has this)
├─ If AP < cost_to_gather:
│  └─ Return FALSE
│
ALL CHECKS PASSED:
└─ Return TRUE
END
```

### Execution Flow (Complete)
```
START execute()
│
PHASE 1: Navigate to Map
├─ Capture current screen
├─ Identify current location:
│  ├─ City view? → Continue
│  ├─ Map view? → Skip to Phase 2
│  └─ Other? → Return to city first
├─ Find "Map" button
│  ├─ Template: templates/buttons/map.png
│  └─ Confidence: 0.8
├─ Tap map button
├─ Wait for map to load (2-4 seconds, random)
├─ Verify map loaded:
│  ├─ Look for map indicators
│  ├─ Zoom controls visible?
│  ├─ Resource search button visible?
│  └─ If not found after 5s → Return FALSE
│
PHASE 2: Select Resource Type
├─ Determine which resource to gather:
│  ├─ Check current resource levels
│  ├─ Which is lowest relative to capacity?
│  ├─ Apply priority from config
│  ├─ Result: selected_resource = "gold" (example)
│  └─ Log: "Gathering {selected_resource}"
│
├─ Find resource search button
│  ├─ Template: templates/map/search.png
│  └─ Tap search button
│
├─ Wait for search menu (1-2 seconds)
│
├─ Select resource type:
│  ├─ Template: templates/map/{selected_resource}.png
│  ├─ Example: templates/map/gold.png
│  └─ Tap resource icon
│
├─ Wait 1 second
│
PHASE 3: Find Optimal Node
├─ After search, map shows resource nodes
├─ Capture map screenshot
│
├─ DETECTION STRATEGY:
│  ├─ Method 1: Template Matching
│  │   ├─ Template: templates/resources/gold_node.png
│  │   ├─ Find ALL instances (find_all_templates)
│  │   └─ Returns list of node locations
│  │
│  ├─ Method 2: Color Detection (Fallback)
│  │   ├─ Gold nodes are yellowish: RGB(255, 215, 0)
│  │   ├─ Find all yellow pixels on map
│  │   ├─ Group nearby pixels into clusters
│  │   └─ Each cluster = potential node
│  │
│  └─ Method 3: OCR Numbers (Advanced)
│      ├─ Look for numbers near nodes
│      └─ Numbers indicate resource amount
│
├─ FILTERING:
│  ├─ For each detected node:
│  │   ├─ Calculate distance from city
│  │   │   └─ Use Euclidean distance formula
│  │   ├─ If distance > max_march_distance → Skip
│  │   │
│  │   ├─ Try to read resource amount (OCR)
│  │   │   ├─ Region: node_location + offset
│  │   │   └─ Extract number
│  │   ├─ If amount < min_amount → Skip
│  │   │
│  │   ├─ Check if in enemy territory (optional)
│  │   │   ├─ Look for red zone indicators
│  │   │   └─ If enemy territory and avoid_enemy → Skip
│  │   │
│  │   └─ Node passes all filters → Add to candidates
│  │
│  └─ SORTING:
│      ├─ Sort candidates by:
│      │   1. Resource amount (higher better)
│      │   2. Distance (closer better)
│      │   3. Weighted score = amount * 0.7 + (max_dist - distance) * 0.3
│      └─ Select best_node = candidates[0]
│
├─ If NO valid nodes found:
│  ├─ Log: "No suitable nodes found"
│  ├─ Try different resource type?
│  └─ Return FALSE
│
PHASE 4: Send Gathering March
├─ Tap on selected node coordinates
│  ├─ Add randomization: ±3 pixels
│  └─ Wait 1-2 seconds
│
├─ Node details popup should appear
│  ├─ Verify popup:
│  │   ├─ Look for "Gather" button
│  │   └─ If not found after 3s → Return FALSE
│  │
│  ├─ OCR resource amount (verify it's good)
│  │   └─ Region: popup_area + amount_offset
│  │
│  └─ Check if node is occupied
│      ├─ Look for "Occupied" text
│      └─ If occupied → Close popup, retry different node
│
├─ Find "Gather" button
│  ├─ Template: templates/buttons/gather.png
│  └─ Tap gather button
│
├─ Wait 1 second
│
├─ Troop selection screen appears
│  ├─ STRATEGY: How many troops to send?
│  │   ├─ Read node capacity (e.g., 500k)
│  │   ├─ Read troop load capacity
│  │   │   └─ Each troop carries X resources
│  │   ├─ Calculate: troops_needed = node_capacity / troop_load
│  │   ├─ Round up to nearest 1000
│  │   └─ Cap at available troops
│  │
│  ├─ TROOP SELECTION:
│  │   ├─ Option A: Use "Max" button
│  │   │   ├─ Find: templates/buttons/max_troops.png
│  │   │   └─ Tap max button
│  │   │
│  │   ├─ Option B: Manual input
│  │   │   ├─ Find troop input field
│  │   │   ├─ Tap field
│  │   │   ├─ Clear existing number
│  │   │   └─ Input calculated troops_needed
│  │   │
│  │   └─ Wait 1 second
│  │
│  ├─ Commander selection (optional)
│  │   ├─ If game has commanders
│  │   ├─ Select gathering-specialized commander
│  │   └─ Template: templates/commanders/gathering.png
│  │
│  └─ Find "Confirm" or "March" button
│      ├─ Template: templates/buttons/confirm_march.png
│      └─ Tap confirm
│
├─ Wait for march to start (1-2 seconds)
│
PHASE 5: Track March
├─ Capture screenshot
├─ Verify march started:
│  ├─ Look for march indicator on map
│  ├─ Look for march in march list
│  └─ If found → Success!
│
├─ Calculate return time:
│  ├─ Read march duration (OCR)
│  ├─ Example: "2:30:00" = 2.5 hours
│  ├─ return_time = current_time + duration + gather_time
│  └─ Schedule next gathering check before return
│
└─ Return TRUE
END execute()
```

### Verification Flow
```
START verify_completion()
│
CHECK 1: March Visible on Map?
├─ Capture map view
├─ Look for march indicator
│  ├─ Green arrow moving from city?
│  ├─ March line visible?
│  └─ Template: templates/march/active_march.png
├─ If found → Return TRUE
│
CHECK 2: March in March List?
├─ Navigate to march management
├─ Check active marches list
├─ Look for newly created march
│  ├─ Match destination
│  ├─ Match troop count
│  └─ Match resource type
├─ If found → Return TRUE
│
CHECK 3: Troop Count Decreased?
├─ Check current idle troops
├─ Compare with pre-execution count
├─ If decreased by sent_troop_count → Return TRUE
│
FALLBACK:
├─ If any check passes → Success
└─ If all fail → Return FALSE
END
```

### Error Scenarios & Handling

**Error 1: Can't find any nodes**
```
Root Causes:
1. Wrong map zoom level
2. Need to search different area
3. All nearby nodes occupied
4. Wrong resource type selected

Solution Flow:
IF no_nodes_found:
    IF attempts < 3:
        ├─ Try different resource type
        ├─ Try zooming out/in
        ├─ Try moving map view
        └─ Retry search
    ELSE:
        ├─ Log: "No nodes available after 3 attempts"
        ├─ Set next_check = current_time + 30 minutes
        └─ Return FALSE
```

**Error 2: Node became occupied**
```
Timing Issue: Someone took the node while we were clicking

Solution:
IF node_occupied:
    ├─ Close popup
    ├─ Select next best node from candidates list
    ├─ If no more candidates → Re-search
    └─ Retry (max 3 times)
```

**Error 3: Not enough troops**
```
Happens if: Troops healing, or used in other marches

Solution:
IF not_enough_troops:
    ├─ Recalculate available troops
    ├─ If still enough for smaller node:
    │   └─ Find smaller node and retry
    ├─ Else:
    │   ├─ Wait for troops to heal
    │   └─ Schedule next check in 1 hour
```

**Error 4: March didn't start**
```
Could be: Game lag, wrong button, connection issue

Solution:
IF march_not_started:
    ├─ Wait additional 3 seconds
    ├─ Re-verify march list
    ├─ If still not found:
    │   ├─ Check if troops returned to city
    │   ├─ Check if resources deducted (march cost)
    │   └─ If uncertain → Return FALSE to retry
```

---

## 4. Barbarian Hunt

**Complexity**: MEDIUM
**Execution Time**: 1-3 minutes
**Success Rate**: 85%+

### Configuration
```json
{
  "id": "barbarian_hunt",
  "interval_hours": 2,
  "priority": 1,
  "parameters": {
    "target_level": 5,
    "min_level": 3,
    "max_level": 7,
    "min_troops": 50,
    "auto_heal": true,
    "commander_preset": "combat_1",
    "search_radius": 50
  }
}
```

### Prerequisites Flow
```
START check_prerequisites()
│
CHECK 1: Troops Available?
├─ Count idle troops (not healing, not marching)
├─ If idle_troops < min_troops:
│  └─ Return FALSE
│
CHECK 2: Action Points?
├─ Read current AP from screen
├─ Hunt cost = 10 AP (example)
├─ If current_AP < hunt_cost:
│  └─ Return FALSE
│
CHECK 3: March Slots?
├─ Check active marches
├─ If all slots used:
│  └─ Return FALSE
│
└─ Return TRUE
END
```

### Execution Flow
```
START execute()
│
PHASE 1: Navigate to Map
├─ [Same as Gathering - map navigation]
│
PHASE 2: Search for Barbarians
├─ Find search button
│  └─ Template: templates/buttons/search.png
├─ Tap search
├─ Wait for search menu (1-2s)
│
├─ Select "Barbarians" category
│  ├─ Template: templates/search/barbarians.png
│  └─ Tap
│
├─ Filter by level (optional):
│  ├─ If level_filter_exists:
│  │   ├─ Set min_level from config
│  │   └─ Set max_level from config
│  └─ Tap search/confirm
│
├─ Wait for results (2-3s)
│
PHASE 3: Detect Barbarians on Map
├─ Capture map screenshot
│
├─ DETECTION METHODS:
│  │
│  ├─ Method 1: Template Matching
│  │   ├─ Templates for each barbarian level:
│  │   │   ├─ templates/barbarians/level_3.png
│  │   │   ├─ templates/barbarians/level_4.png
│  │   │   ├─ templates/barbarians/level_5.png
│  │   │   └─ ...
│  │   ├─ Find ALL instances (multiple barbarians)
│  │   └─ Returns: [(x1, y1, level), (x2, y2, level), ...]
│  │
│  ├─ Method 2: Icon Detection
│  │   ├─ Barbarians have unique icon color
│  │   ├─ Use color detection
│  │   └─ Filter by icon shape/size
│  │
│  └─ Method 3: OCR Level Numbers
│      ├─ After finding icons, read level numbers
│      └─ Verify level matches target
│
├─ FILTERING & PRIORITIZATION:
│  ├─ For each detected barbarian:
│  │   ├─ Verify level in range [min_level, max_level]
│  │   ├─ Calculate distance from city
│  │   ├─ Check if within search_radius
│  │   ├─ Check if already defeated (grayed out)
│  │   └─ Add to candidates if valid
│  │
│  └─ SORT candidates by:
│      ├─ Priority 1: Exact target_level match
│      ├─ Priority 2: Closer distance
│      └─ Priority 3: Higher level (more rewards)
│
├─ SELECT best_target = candidates[0]
│  └─ If no candidates → Return FALSE
│
PHASE 4: Attack Barbarian
├─ Tap on barbarian coordinates
│  ├─ Add random offset: ±4 pixels
│  └─ Wait 1-2s
│
├─ Barbarian details popup appears
│  ├─ VERIFY popup:
│  │   ├─ Read barbarian level (OCR)
│  │   ├─ Read recommended power
│  │   └─ Check if already attacked
│  │
│  ├─ If already defeated:
│  │   ├─ Close popup
│  │   ├─ Try next candidate
│  │   └─ Retry (max 3 barbarians)
│  │
│  └─ Find "Attack" button
│      ├─ Template: templates/buttons/attack.png
│      └─ Tap attack
│
├─ Wait 1s
│
├─ Troop selection screen
│  ├─ STRATEGY:
│  │   ├─ Read recommended power
│  │   ├─ Calculate troops needed to match
│  │   ├─ Add 10% safety margin
│  │   └─ troops_to_send = recommended * 1.1
│  │
│  ├─ Option A: Use preset
│  │   ├─ If commander_preset configured:
│  │   ├─ Find preset button
│  │   └─ Tap preset (auto-fills troops + commander)
│  │
│  ├─ Option B: Manual selection
│  │   ├─ Select commander:
│  │   │   └─ templates/commanders/combat.png
│  │   ├─ Add troops:
│  │   │   ├─ Prefer cavalry (fastest)
│  │   │   └─ Input calculated amount
│  │   └─ Confirm
│  │
│  └─ Tap "March" or "Attack" button
│
├─ Wait for march to start (1-2s)
│
PHASE 5: Verification
├─ Check if march started
│  ├─ Look for march indicator on map
│  └─ Check march list
│
└─ Return TRUE
END execute()
```

### Verification Flow
```
START verify_completion()
│
CHECK: March Started?
├─ Capture map
├─ Look for attack march indicator
│  ├─ Red/orange march line?
│  ├─ Sword icon moving?
│  └─ Template: templates/march/attack_march.png
│
├─ If found → Return TRUE
│
ALTERNATIVE: Check March List
├─ Open march management
├─ Look for new attack march
│  ├─ Destination = barbarian coordinates
│  ├─ March type = "Attack"
│  └─ If matches → Return TRUE
│
└─ Default: Return FALSE if not verified
END
```

---

## 5. Building Upgrade

**Complexity**: MEDIUM
**Execution Time**: 1-2 minutes
**Success Rate**: 90%+

### Configuration
```json
{
  "id": "building_upgrade",
  "interval_hours": 1,
  "priority": 2,
  "parameters": {
    "upgrade_priority": [
      "Town Hall",
      "Castle",
      "Research Lab",
      "Training Grounds",
      "Hospital",
      "Warehouse"
    ],
    "min_resources": {
      "food": 100000,
      "wood": 100000,
      "stone": 100000,
      "gold": 50000
    },
    "use_speedups": false,
    "max_queue_slots": 2,
    "save_for_important": true
  }
}
```

### Prerequisites Flow
```
START check_prerequisites()
│
CHECK 1: Builder Available?
├─ Check active building upgrades
├─ Count builders: active_builders / max_builders
├─ If all builders busy:
│  ├─ Calculate time until builder free
│  ├─ Schedule next check at that time
│  └─ Return FALSE
│
CHECK 2: Enough Resources?
├─ Read current resources from city screen
├─ For each resource type:
│  ├─ If current < min_resources[type]:
│  │   └─ Missing resources, can't upgrade
│  └─ Continue if all sufficient
│
CHECK 3: Any Buildings Ready to Upgrade?
├─ Scan city for upgrade indicators
│  ├─ Green arrow icons?
│  ├─ "Upgrade" notifications?
│  └─ Template: templates/indicators/upgrade_available.png
├─ If none found:
│  └─ Return FALSE (nothing to upgrade)
│
└─ Return TRUE (all checks passed)
END
```

### Execution Flow
```
START execute()
│
PHASE 1: Navigate to City
├─ If on map → Press home/city button
├─ Wait for city to load (1-2s)
├─ Verify city view loaded:
│  └─ Look for city indicators
│
PHASE 2: Scan for Upgradeable Buildings
├─ Capture city screenshot
│
├─ METHOD: Find upgrade indicators
│  ├─ Template: templates/indicators/upgrade_arrow.png
│  ├─ Find ALL instances (multiple buildings might be ready)
│  └─ Returns: list of (x, y) coordinates
│
├─ If no indicators found:
│  ├─ Alternative: Manually check priority buildings
│  │   ├─ For each building in upgrade_priority:
│  │   │   ├─ Find building by template
│  │   │   ├─ Tap building
│  │   │   ├─ Check if upgrade available
│  │   │   └─ If yes, break
│  │   └─ Continue with that building
│  └─ If still none → Return FALSE
│
PHASE 3: Select Building by Priority
├─ If multiple buildings ready:
│  │
│  ├─ PRIORITY MATCHING:
│  │   ├─ For each detected building location:
│  │   │   ├─ Tap building (temporary)
│  │   │   ├─ Read building name (OCR)
│  │   │   ├─ Close popup
│  │   │   └─ Record: (name, location)
│  │   │
│  │   ├─ Sort buildings by priority list
│  │   │   └─ Higher in list = higher priority
│  │   │
│  │   └─ Select highest priority building
│  │
│  └─ SPECIAL CASE: Save resources?
│      ├─ If save_for_important == true:
│      │   ├─ Check if Town Hall upgradeable soon
│      │   ├─ If yes and current != Town Hall:
│      │   │   └─ Skip other upgrades, save resources
│      │   └─ Only upgrade Town Hall
│      └─ Continue with selected building
│
PHASE 4: Execute Upgrade
├─ Tap on selected building
│  ├─ Add randomization: ±5px
│  └─ Wait 1-2s
│
├─ Building popup appears
│  ├─ VERIFY correct building:
│  │   ├─ OCR building name
│  │   └─ Confirm matches expected
│  │
│  ├─ Find "Upgrade" button
│  │   ├─ Template: templates/buttons/upgrade.png
│  │   ├─ Confidence: 0.8
│  │   └─ If NOT found:
│  │       ├─ Check if already max level
│  │       ├─ Check if requirements not met
│  │       └─ Return FALSE
│  │
│  └─ READ upgrade requirements:
│      ├─ OCR resource costs
│      │   ├─ Food: X
│      │   ├─ Wood: Y
│      │   ├─ Stone: Z
│      │   └─ Gold: W
│      ├─ OCR upgrade time
│      │   └─ Example: "2h 30m"
│      └─ Store for verification
│
├─ TAP "Upgrade" button
│  └─ Random delay: 200-400ms
│
├─ CONFIRMATION PROMPT (if exists):
│  ├─ Some games have "Are you sure?" prompt
│  ├─ Look for confirm button
│  │   └─ Template: templates/buttons/confirm.png
│  └─ Tap confirm
│
├─ SPEEDUP PROMPT (optional):
│  ├─ If use_speedups == true:
│  │   ├─ Game may ask "Use speedup?"
│  │   ├─ Find speedup options
│  │   └─ Apply appropriate speedup
│  └─ Else: Skip/Cancel speedup
│
├─ Wait for upgrade to start (1-2s)
│
PHASE 5: Verify Upgrade Started
├─ VISUAL VERIFICATION:
│  ├─ Check building for construction indicator
│  │   ├─ Scaffolding visible?
│  │   ├─ Hammer/construction icon?
│  │   └─ Timer showing?
│  │
│  └─ Check builder indicator
│      ├─ Builder icon on building?
│      └─ Active upgrade counter increased?
│
└─ Return TRUE if verified
END execute()
```

### Verification Flow
```
START verify_completion()
│
CHECK 1: Resources Deducted?
├─ Read current resources
├─ Compare with pre-upgrade resources
├─ Expected decrease:
│  └─ current ≈ previous - upgrade_cost
├─ If matches (within 5% tolerance) → Success
│
CHECK 2: Building Has Construction Indicator?
├─ Capture city screen
├─ Look at upgraded building location
├─ Check for:
│  ├─ Construction animation
│  ├─ Timer overlay
│  └─ Builder icon
├─ If found → Return TRUE
│
CHECK 3: Active Builders Increased?
├─ Read builder count: "Builders: 2/2"
├─ Compare with pre-upgrade count
├─ If increased by 1 → Return TRUE
│
RESULT:
├─ If any check confirms → Return TRUE
└─ If all fail → Return FALSE
END
```

---

## Template Matching Details

### How Template Matching Works

```
PROCESS: find_template(screenshot, template_path)
│
STEP 1: Load Images
├─ screenshot = Current game screen (1920x1080)
├─ template = Small image to find (e.g., 50x50 button)
│
STEP 2: Convert to Grayscale
├─ WHY: Color varies with lighting, grayscale more reliable
├─ screenshot_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
├─ template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
│
STEP 3: Template Matching
├─ result = cv2.matchTemplate(screenshot_gray, template_gray, method)
├─ METHOD: cv2.TM_CCOEFF_NORMED
│   └─ Returns correlation coefficient (0.0 to 1.0)
│       ├─ 1.0 = Perfect match
│       ├─ 0.8+ = Very good match
│       ├─ 0.6-0.8 = Acceptable
│       └─ <0.6 = Poor match
│
├─ result is a matrix showing match quality at each position
│
STEP 4: Find Best Match
├─ (min_val, max_val, min_loc, max_loc) = cv2.minMaxLoc(result)
├─ max_val = confidence score
├─ max_loc = (x, y) top-left corner of best match
│
STEP 5: Check Confidence Threshold
├─ IF max_val >= threshold (usually 0.8):
│  ├─ Match found!
│  ├─ Calculate center: (x + w/2, y + h/2)
│  └─ Return MatchResult(found=True, location=(x,y), confidence=max_val)
├─ ELSE:
│  └─ Return MatchResult(found=False, confidence=max_val)
│
END
```

### Multi-Scale Matching

```
WHY: UI elements can be different sizes
     (different resolutions, zoom levels, etc.)

PROCESS:
FOR each scale in [0.8, 0.9, 1.0, 1.1, 1.2]:
    ├─ Resize template by scale
    ├─ Try template matching
    ├─ Record confidence
    └─ Keep best result

EXAMPLE:
├─ Scale 0.8: confidence = 0.65 (too small)
├─ Scale 0.9: confidence = 0.72 (better)
├─ Scale 1.0: confidence = 0.89 (best!)
├─ Scale 1.1: confidence = 0.74 (too large)
└─ Result: Use scale 1.0 match
```

---

## OCR (Text Recognition) Details

### How OCR Works

```
PROCESS: read_text(screenshot, region)
│
STEP 1: Extract Region
├─ IF region specified (x, y, width, height):
│  └─ image = screenshot[y:y+h, x:x+w]
├─ ELSE:
│  └─ image = full screenshot
│
STEP 2: Preprocessing
├─ Convert to grayscale
├─ Resize if text is small (< 30px height)
│   └─ Tesseract works better on larger text
├─ Apply thresholding:
│   ├─ Convert to binary (black/white)
│   └─ Removes noise, makes text clearer
├─ Denoise
│   └─ Remove artifacts that confuse OCR
│
STEP 3: Run Tesseract
├─ text = pytesseract.image_to_string(image, config)
├─ CONFIG options:
│   ├─ --oem 3: LSTM neural net mode (best accuracy)
│   ├─ --psm 6: Assume uniform block of text
│   ├─ --psm 7: Single text line
│   └─ digits: Only recognize numbers
│
STEP 4: Post-Processing
├─ text = text.strip()  # Remove whitespace
├─ text = text.replace('\n', ' ')  # Remove newlines
├─ Clean up common OCR errors:
│   ├─ '0' vs 'O'
│   ├─ '1' vs 'l' vs 'I'
│   └─ '5' vs 'S'
│
└─ Return cleaned text
END
```

### Reading Numbers (Resource Counts)

```
EXAMPLE: Reading gold count from screen

SCREEN LAYOUT:
┌─────────────────┐
│ Gold: 1,234,567 │
└─────────────────┘

PROCESS:
├─ STEP 1: Find gold icon (template matching)
│  └─ Location: (100, 50)
│
├─ STEP 2: Calculate text region
│  ├─ Gold numbers are to the right of icon
│  ├─ Offset: icon_x + icon_width + 10px
│  └─ Region: (150, 45, 150, 30) # x, y, w, h
│
├─ STEP 3: Extract region
│  └─ number_image = screenshot[45:75, 150:300]
│
├─ STEP 4: Preprocess
│  ├─ Grayscale
│  ├─ Threshold (make numbers pure black on white)
│  └─ Resize 2x (better OCR on larger text)
│
├─ STEP 5: OCR with digits mode
│  ├─ text = pytesseract.image_to_string(image, config='digits')
│  └─ Result: "1234567" or "1,234,567"
│
├─ STEP 6: Clean and parse
│  ├─ Remove commas: text.replace(',', '')
│  ├─ Remove non-digits: ''.join(filter(str.isdigit, text))
│  └─ Convert: int(text) = 1234567
│
└─ Return: 1234567
END
```

---

## Error Handling Patterns

### Global Error Handling Strategy

```
FOR ANY activity execution:

TRY:
    ├─ Execute activity logic
    │
EXCEPT ScreenshotFailed:
    ├─ Log error
    ├─ Try reconnect ADB
    ├─ Retry once
    └─ If still fails → Return FALSE
    │
EXCEPT ElementNotFound:
    ├─ Could be:
    │   ├─ Wrong screen
    │   ├─ UI changed (game update)
    │   └─ Template needs updating
    ├─ Try alternative detection method
    ├─ If still not found → Return FALSE
    │
EXCEPT GameCrashed:
    ├─ Detect: Black screen, "Game crashed" popup
    ├─ Restart game automatically
    ├─ Wait for login
    └─ Return FALSE (retry later)
    │
EXCEPT NetworkError:
    ├─ Detect: "Connection lost" popup
    ├─ Wait 30 seconds
    ├─ Retry activity
    └─ If persists → Disable activity temporarily
    │
EXCEPT Timeout:
    ├─ Activity took too long (> max_execution_seconds)
    ├─ Force stop activity
    ├─ Return to city/safe state
    └─ Return FALSE
    │
EXCEPT UnexpectedPopup:
    ├─ Random event popup, gift, etc.
    ├─ Try to close popup:
    │   ├─ Find X button
    │   ├─ Find "Close" button
    │   └─ Press back button
    ├─ Retry activity
    │
EXCEPT CaptchaDetected:
    ├─ STOP ALL ACTIVITIES
    ├─ Send notification to user
    ├─ Log: "Captcha detected - manual intervention required"
    ├─ Wait for user to solve
    └─ Do NOT retry automatically
    │
FINALLY:
    ├─ Always log what happened
    ├─ Always update statistics
    └─ Always calculate next execution time
END
```

---

## Next Steps

This document provides the COMPLETE logic for basic activities.

**To integrate into your Kozan Citadel project:**

1. **Extract the logic**: Each flow can become a function
2. **Create API endpoints**: Wrap activities in REST API
3. **Discord commands**: `/rok gather start` calls the API
4. **Web dashboard**: Buttons call the same API
5. **Database**: Store activity configs and results

Want me to continue with:
- Remaining 45+ activity flows?
- Integration examples for your web app?
- API design for remote control?
