# Xbox Controller Teleoperation for LeKiwi

This document describes the Xbox controller integration for the LeKiwi robot, including how it works and how to use it.

## Overview

The Xbox controller implementation provides a modern, reliable way to control both the arm and mobile base of the LeKiwi robot using a single Xbox gamepad. This is achieved through:

1. **Custom Xbox Teleoperator Module** (`src/lerobot/teleoperators/xbox/`): A fully-functional teleoperator class that reads Xbox controller input via PyGame and converts it to robot actions.

2. **Multiple Control Scripts**: Different teleoperation scripts for different use cases.

## Architecture Comparison

### Why PyGame over evdev?

The original `teleoperate_xbox_controller.py` used `evdev` (Linux event device interface), which has limitations:
- Lower-level and less standardized
- Different behavior across platforms
- More prone to interpretation issues
- Difficult to handle analog values consistently

The new implementation uses **PyGame**, which offers:
- Cross-platform compatibility (Linux, macOS, Windows)
- Standardized gamepad input handling
- Better deadzone and normalization support
- Cleaner axis/button mapping
- More reliable stick input reading

### Action Space

The LeKiwi robot expects actions in the following format:

```python
{
    "arm_shoulder_pan": float,      # Radians, -π to π
    "arm_shoulder_lift": float,     # Radians, -π to π
    "arm_elbow_flex": float,        # Radians, -π to π
    "arm_wrist_flex": float,        # Radians, -π to π
    "arm_wrist_roll": float,        # Radians, -π to π
    "arm_gripper": float,           # Range -1.0 to 1.0
    "x.vel": float,                 # m/s (forward/backward)
    "y.vel": float,                 # m/s (left/right strafe)
    "theta.vel": float,             # deg/s (rotation)
}
```

The Xbox teleoperator outputs exactly this structure.

## Installation

### Prerequisites

1. **PyGame** (for Xbox controller input):
   ```bash
   pip install pygame
   ```

2. **Xbox Controller**: Connect via USB or Bluetooth
   - Xbox 360 controller
   - Xbox One controller
   - Compatible third-party controllers (most modern gamepads work)

### LeKiwi Robot Host

On the LeKiwi robot, run the host server:

```bash
python -m lerobot.robots.lekiwi.lekiwi_host --robot.id=my_awesome_kiwi
```

For dual-board setup:
```bash
python -m lerobot.robots.lekiwi.lekiwi_host --robot.id=my_awesome_kiwi --robot.use_dual_boards=true
```

## Available Scripts

### 1. **teleoperate_xbox.py** (Recommended - Full Control)

**Use this for**: Complete Xbox control of both arm and mobile base.

```bash
python examples/lekiwi/teleoperate_xbox.py
```

**Controller Mapping**:

| Control | Mapping |
|---------|---------|
| **Left Stick X** | Arm wrist roll (left/right) |
| **Left Stick Y** | Arm wrist flex (up/down) |
| **Right Stick X** | Base rotation (left/right) |
| **Right Stick Y** | Base forward/backward |
| **D-Pad Up/Down** | Arm shoulder pan (forward/backward) |
| **D-Pad Left/Right** | Arm elbow flex (out/in) |
| **Right Stick Y** | Arm shoulder lift (up/down) |
| **LT Trigger** | Decrease gripper |
| **RT Trigger** | Increase gripper |
| **LB Button** | Arm move slower (0.5x speed) |
| **RB Button** | Arm move faster (2.0x speed) |
| **B Button** | Emergency stop |
| **Back Button** | Quit application |

### 2. **teleoperate_xbox_hybrid.py** (Hybrid Control)

**Use this for**: Xbox arm control + Keyboard base control (useful if you prefer keyboard for base).

```bash
python examples/lekiwi/teleoperate_xbox_hybrid.py
```

**Xbox Controller**: Controls arm (same as above)
**Keyboard**: Controls base (arrow keys for movement)

### 3. **record_xbox.py** (Xbox-Only Recording)

**Use this for**: Record demonstration episodes using full Xbox control.

```bash
python examples/lekiwi/record_xbox.py
```

This script records arm and base actions from Xbox controller input into a LeRobot dataset.

### 4. **record_xbox_hybrid.py** (Hybrid Recording)

**Use this for**: Record demonstrations with Xbox arm + keyboard base.

```bash
python examples/lekiwi/record_xbox_hybrid.py
```

## Configuration

### Customizing Controller Behavior

Edit the configuration in any of the teleoperate/record scripts:

```python
xbox_config = XboxTeleopConfig(
    id="my_xbox_controller",
    deadzone=0.1,              # Stick deadzone threshold
    base_linear_vel=0.3,       # m/s for base translation
    base_angular_vel=90.0,     # deg/s for base rotation
    arm_speed=0.05,            # Radians per control loop
    gripper_speed=0.05,        # Gripper increment per loop
    stick_scale=1.0,           # Multiplier for stick sensitivity
)
```

### Key Parameters

- **deadzone**: Analog stick values below this threshold are ignored (prevents drift)
- **base_linear_vel**: How fast the base translates (m/s)
- **base_angular_vel**: How fast the base rotates (degrees/s)
- **arm_speed**: How much each arm joint moves per frame (radians)
- **gripper_speed**: How much the gripper opens/closes per frame
- **stick_scale**: Sensitivity multiplier for stick input (>1 = more sensitive, <1 = less sensitive)

## Implementation Details

### Module Structure

```
src/lerobot/teleoperators/xbox/
├── __init__.py                  # Module exports
├── configuration_xbox.py         # Configuration class
└── teleop_xbox.py              # Main XboxTeleop implementation
```

### Key Components in teleop_xbox.py

1. **XboxTeleop Class**: Inherits from `Teleoperator` base class
   - Implements required interface: `connect()`, `disconnect()`, `get_action()`, `get_teleop_events()`
   - Maintains arm position state (cumulative positions)
   - Handles base velocity commands
   - Provides deadzone filtering for stick inputs

2. **Action Mapping**:
   - **Arm**: Position-based control (targets accumulate with stick deflection)
   - **Base**: Velocity-based control (direct output from sticks)
   - **Gripper**: Proportional control via triggers

3. **Speed Modulation**:
   - LB button: 0.5x speed
   - RB button: 2.0x speed
   - No modifier: 1.0x speed

### How It Integrates

The Xbox teleoperator follows the standard LeRobot teleoperator interface:

```python
# In teleoperate_xbox.py
xbox = XboxTeleop(xbox_config)
xbox.connect()  # Initialize and detect controller

while True:
    action = xbox.get_action()  # Returns action dict
    robot.send_action(action)   # Send to robot
    events = xbox.get_teleop_events()  # Check for quit, etc.
```

## Troubleshooting

### Controller Not Detected

1. **Check connection**:
   ```bash
   lsusb  # List USB devices
   ```

2. **Test with pygame directly**:
   ```python
   import pygame
   pygame.init()
   pygame.joystick.init()
   print(pygame.joystick.get_count())  # Should be > 0
   ```

3. **Try different USB port**: Sometimes the hub or port matters

### Inconsistent Stick Input

1. **Increase deadzone**: In config, increase `deadzone` value (default 0.1)
2. **Calibrate controller**: Some controllers have built-in calibration (consult manual)
3. **Clean stick contacts**: Physical dust can cause drift

### Arm Not Moving

1. **Check action space**: Ensure arm positions are being set
2. **Verify robot connection**: Test with keyboard-based teleoperation first
3. **Check stick mapping**: Confirm left stick is moving arm in expected direction

### Base Not Moving

1. **Right stick test**: Press right stick and watch velocity values
2. **Compare with working script**: Test with original `teleoperate_xbox_controller.py` for base-only control
3. **Check velocity ranges**: Default is 0.3 m/s and 90 deg/s

## Comparison: Old vs. New Implementation

### Old Implementation (teleoperate_xbox_controller.py)

**Strengths**:
- ✓ Simple, focused on base control only
- ✓ Uses evdev (always available on Linux)
- ✓ Good detection of controller connection

**Limitations**:
- ✗ Base-only control (no arm)
- ✗ Linux-specific
- ✗ No position tracking (purely velocity-based)
- ✗ Doesn't follow teleoperator interface
- ✗ Not integrated into teleoperate.py/record.py

### New Implementation (XboxTeleop Module)

**Strengths**:
- ✓ Full arm + base control from single controller
- ✓ Cross-platform (Linux, macOS, Windows)
- ✓ Position-based arm control (more precise)
- ✓ Follows standard LeRobot teleoperator interface
- ✓ Integrates with teleoperate.py/record.py scripts
- ✓ Better deadzone handling
- ✓ Easier configuration

**Advantages**:
- PyGame is more cross-platform than evdev
- Position-based arm control is more precise than raw stick values
- Follows the same pattern as SO100Leader, KeyboardTeleop, etc.
- Can be mixed with other teleoperators (hybrid control)

## Future Enhancements

Potential improvements for future iterations:

1. **Haptic Feedback**: Return force/torque feedback to controller
2. **Button Profiles**: Quick presets for different tasks (pick, place, etc.)
3. **Inverse Kinematics**: Optional IK solver for Cartesian control
4. **Velocity Limiting**: Safety limits on arm speed
5. **Emergency Stop Lock**: Require double-press to clear emergency stop
6. **Arm Home Position**: Quick return to safe position
7. **Gripper Open/Close Presets**: Quick full open/close buttons

## Testing

To test the Xbox controller integration:

1. **Connection test**:
   ```bash
   python -c "from lerobot.teleoperators.xbox import XboxTeleop, XboxTeleopConfig; \
              xbox = XboxTeleop(XboxTeleopConfig()); xbox.connect(); \
              print('Connected successfully')"
   ```

2. **Action output test**:
   ```bash
   python examples/lekiwi/teleoperate_xbox.py
   # Move sticks and check output in terminal
   ```

3. **Integration test**:
   Start with robot host running, then run teleoperate_xbox.py
   Verify arm and base respond to controller input

## References

- **LeRobot Documentation**: https://github.com/huggingface/lerobot
- **PyGame Joystick Docs**: https://www.pygame.org/docs/ref/joystick.html
- **XLeRobot Xbox Implementation**: https://github.com/Vector-Wangel/XLeRobot
- **Controller Mapping Reference**: Common Xbox/Xbox 360 controller button layouts

## Contributing

To improve the Xbox controller implementation:

1. Test with different controller types
2. Report issues with specific controllers
3. Suggest improvements for control mapping
4. Add support for additional features (haptic feedback, etc.)

## License

This implementation maintains the same Apache 2.0 license as the rest of the LeRobot project.
