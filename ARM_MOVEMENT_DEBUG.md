# ARM Movement Debug Session

## Problem Description
Xbox controller ARM movement was severely limited:
- Wrist movement restricted to ~1 degree total range
- No shoulder or elbow movement at all
- Robot moved to "middle" position on startup but controller started from zero
- Gripper remained closed, no trigger response

## Root Cause Analysis
1. **Position Initialization Mismatch**: Controller initialized all joints to `0.0` but robot was actually at middle positions
2. **Restrictive Joint Limits**: Joints clamped to ±π (±180°) which the robot immediately hit
3. **Control Method Issues**: Initially tried complex proportional control when simple accumulation worked

## Changes Made

### 1. Fixed Position Initialization (`src/lerobot/teleoperators/xbox/teleop_xbox.py`)
```python
# Before: Hard-coded initialization
self.arm_positions = {
    "arm_shoulder_pan": 0.0,  # Wrong!
    ...
}

# After: Dynamic initialization from robot observation
self.arm_positions = {
    "arm_shoulder_pan": None,  # Will be set from robot
    ...
}
self.initialized = False

# Initialization logic added to get_action()
if not self.initialized and observation is not None:
    # Read actual robot position and initialize from that
```

### 2. Expanded Joint Limits
```python
# Before: Restrictive limits
self.arm_positions[joint] = np.clip(joint, -np.pi, np.pi)  # ±180°

# After: Generous limits
self.arm_positions[joint] = np.clip(joint, -2*np.pi, 2*np.pi)  # ±720°
```

### 3. Increased Movement Speed (`src/lerobot/teleoperators/xbox/configuration_xbox.py`)
```python
# Before: Too slow
arm_speed: float = 0.05  # ~3° per input

# After: Much faster
arm_speed: float = 1.0   # ~57° per second at full deflection
gripper_speed: float = 0.2  # 4x faster gripper
```

### 4. Updated Main Script (`examples/lekiwi/teleoperate_xbox.py`)
- Already passing `observation` to `xbox.get_action(observation)`
- Added initialization status messages
- Updated help text to explain initialization

## Technical Details

### Control Flow
1. Robot connects and moves to middle positions
2. First call to `get_action(observation)` reads robot's actual joint positions
3. Controller accumulates deltas from these real positions (not zero)
4. Much larger joint limits prevent artificial restrictions

### Expected Behavior
- **Initialization**: Should print actual starting positions on first run
- **Wrist Movement**: Left stick should give large, visible movements
- **Shoulder/Elbow**: D-pad and LS+stick should move these joints
- **Gripper**: LT/RT triggers should open/close gripper
- **No 1° limit**: Should be able to move through full range

## Status
Fixes applied but still not working properly. Possible remaining issues:
- **Hardware**: Low battery voltage affecting motor performance
- **Communication**: Robot host/client connection issues
- **Joint Safety Limits**: Robot firmware may have additional restrictions
- **Observation Format**: May need to debug observation keys/format

## Next Steps
1. Charge battery and test with full voltage
2. If still not working, run `debug_observation.py` to check observation format
3. Verify robot host is running with proper dual-board configuration
4. Check for any error messages in robot host logs

## Files Modified
- `src/lerobot/teleoperators/xbox/teleop_xbox.py` - Position initialization and limits
- `src/lerobot/teleoperators/xbox/configuration_xbox.py` - Movement speeds
- `examples/lekiwi/teleoperate_xbox.py` - Help text updates
- `examples/lekiwi/debug_observation.py` - Debug script (new)
- `examples/lekiwi/test_initialization_fix.py` - Test script (new)