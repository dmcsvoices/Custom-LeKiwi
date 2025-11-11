# LeKiwi Dual Motor Control Board Implementation Plan

## Overview
This document outlines the implementation plan for supporting dual motor control boards in the LeKiwi robot configuration.

## Current Configuration
- **Single port**: `/dev/ttyACM0` (configurable)
- **Single bus**: One `FeetechMotorsBus` instance controlling all 9 motors
- **Motor IDs**: 1-6 (arm), 7-9 (base) all on same daisy chain

## Target Configuration
- **Board 1**: Motor IDs 1-6 (arm motors including gripper)
- **Board 2**: Motor IDs 7-9 (base wheel motors)
- **Port assignment**: Auto-detected at runtime from `/dev/ttyACM0` and `/dev/ttyACM1`

## Port Auto-Detection Strategy
- Scan candidate ports (`/dev/ttyACM0`, `/dev/ttyACM1`)
- Attempt to ping Motor ID 1 (arm_shoulder_pan) on each port
- Port that responds to Motor ID 1 → arm board
- Other port → base board
- Fallback to manual configuration if auto-detection fails

## Implementation Phases

### Phase 1: Configuration Layer (`config_lekiwi.py`)
**Files**: `lerobot/robots/lekiwi/config_lekiwi.py`

**Changes**:
- Add `use_dual_boards: bool = False` (backwards compatible default)
- Add `arm_port: str | None = None` (auto-detect if None)
- Add `base_port: str | None = None` (auto-detect if None)
- Keep existing `port: str = "/dev/ttyACM0"` for single-board mode

**Commit**: "feat(lekiwi): add dual motor board configuration parameters"

---

### Phase 2: Port Auto-Detection (`lekiwi.py`)
**Files**: `lerobot/robots/lekiwi/lekiwi.py`

**Changes**:
- Add `_detect_board_ports()` method
  - Scans `/dev/ttyACM0` and `/dev/ttyACM1`
  - Attempts to create temporary bus and ping Motor ID 1
  - Returns tuple `(arm_port, base_port)`
  - Raises error if detection fails

**Commit**: "feat(lekiwi): implement port auto-detection for dual boards"

---

### Phase 3: Dual Bus Initialization (`lekiwi.py` - `__init__`)
**Files**: `lerobot/robots/lekiwi/lekiwi.py` (lines 55-71)

**Changes**:
- Check `self.config.use_dual_boards`
- If True:
  - Auto-detect ports if `arm_port`/`base_port` are None
  - Create `self.arm_bus` with motors 1-6
  - Create `self.base_bus` with motors 7-9
  - Create `self.motor_bus_map` routing dictionary
  - Set `self.buses = [self.arm_bus, self.base_bus]`
- If False:
  - Keep existing single-bus implementation
  - Set `self.bus` with all motors
  - Set `self.buses = [self.bus]`

**Commit**: "feat(lekiwi): support dual bus initialization in __init__"

---

### Phase 4: Connection Method (`lekiwi.py` - `connect`)
**Files**: `lerobot/robots/lekiwi/lekiwi.py` (lines 111-126)

**Changes**:
```python
def connect(self) -> None:
    if self.config.use_dual_boards:
        self.arm_bus.connect()
        self.base_bus.connect()
    else:
        self.bus.connect()
    # Rest of calibration check logic...
```

**Commit**: "feat(lekiwi): update connect() for dual boards"

---

### Phase 5: Communication Methods (`lekiwi.py`)
**Files**: `lerobot/robots/lekiwi/lekiwi.py` (lines 341-408)

**Changes to `get_observation()` (lines 341-366)**:
- If dual boards: separate reads from `arm_bus` and `base_bus`, merge results
- If single board: existing implementation

**Changes to `send_action()` (lines 391-408)**:
- If dual boards: split actions by motor group, write to respective buses
- If single board: existing implementation

**Commit**: "feat(lekiwi): update get_observation and send_action for dual boards"

---

### Phase 6: Calibration System (`lekiwi.py` - `calibrate`)
**Files**: `lerobot/robots/lekiwi/lekiwi.py` (lines 132-182)

**Changes**:
- If dual boards:
  - Disable torque on arm motors via `arm_bus`
  - Call `arm_bus.set_half_turn_homings()` for arm motors
  - Set zero offsets for base motors
  - Record ranges on `arm_bus` for non-full-turn motors
- If single board: existing implementation

**Commit**: "feat(lekiwi): update calibration for dual boards"

---

### Phase 7: Motor Setup (`lekiwi.py` - `setup_motors`)
**Files**: `lerobot/robots/lekiwi/lekiwi.py` (lines 202-206)

**Changes**:
- If dual boards:
  - Prompt user to connect ARM board at detected arm_port
  - Setup arm motors sequentially on `arm_bus`
  - Prompt user to connect BASE board at detected base_port
  - Setup base motors sequentially on `base_bus`
- If single board: existing implementation

**Commit**: "feat(lekiwi): update setup_motors for dual boards"

---

### Phase 8: Configure Method (`lekiwi.py` - `configure`)
**Files**: `lerobot/robots/lekiwi/lekiwi.py` (lines 183-200)

**Changes**:
- If dual boards:
  - Configure arm motors on `arm_bus`
  - Configure base motors on `base_bus`
- If single board: existing implementation

**Commit**: "feat(lekiwi): update configure() for dual boards"

---

### Phase 9: Disconnect Method (`lekiwi.py` - `disconnect`)
**Files**: `lerobot/robots/lekiwi/lekiwi.py` (lines 128-130)

**Changes**:
- If dual boards:
  - Disconnect both `arm_bus` and `base_bus`
- If single board: existing single bus disconnect

**Commit**: "feat(lekiwi): update disconnect() for dual boards"

---

### Phase 10: Testing & Validation

**Test Cases**:
1. Single-board mode (backwards compatibility)
2. Dual-board mode with fixed ports
3. Dual-board mode with auto-detection
4. Port auto-detection with swapped USB cables
5. Calibration workflow
6. Motor setup workflow
7. Data collection and playback

**Commit**: "test(lekiwi): add dual board support validation"

---

## Backwards Compatibility

- Default `use_dual_boards=False` preserves existing behavior
- Single `port` parameter still functional
- Existing commands work without changes
- Dual-board mode requires explicit opt-in via config

## Usage Examples

### Single Board (Current - No Changes Required)
```bash
lerobot-calibrate --robot.type=lekiwi --robot.id=my_kiwi
```

### Dual Board with Auto-Detection
```bash
lerobot-calibrate \
    --robot.type=lekiwi \
    --robot.id=my_kiwi \
    --robot.use_dual_boards=true
```

### Dual Board with Manual Ports
```bash
lerobot-calibrate \
    --robot.type=lekiwi \
    --robot.id=my_kiwi \
    --robot.use_dual_boards=true \
    --robot.arm_port=/dev/ttyACM0 \
    --robot.base_port=/dev/ttyACM1
```

## Risk Mitigation

- Frequent commits after each phase
- Each phase is independently testable
- Can revert to previous commit if issues arise
- Backwards compatibility ensures existing setups unaffected

## Files Modified

1. `lerobot/robots/lekiwi/config_lekiwi.py` - Configuration
2. `lerobot/robots/lekiwi/lekiwi.py` - Main robot implementation
