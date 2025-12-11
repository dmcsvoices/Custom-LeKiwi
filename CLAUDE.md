# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Custom LeKiwi is a specialized fork of HuggingFace's LeRobot project, enhanced for the LeKiwi mobile manipulation robot with dual motor control board support. This is a **custom fork** - all development happens here and should NOT be pushed to HuggingFace upstream.

**Key Enhancement**: Supports splitting arm motors (1-6, 12V) and base motors (7-9, 7V) across two independent control boards for optimal power management and performance.

## Common Development Commands

### Environment Setup
```bash
# Create environment
conda create -y -n lerobot python=3.10
conda activate lerobot

# Install dependencies
conda install ffmpeg -c conda-forge
pip install -e ".[lekiwi]"  # Includes feetech and pyzmq
pip install pygame          # For Xbox controller support
```

### Robot Control Flow
```bash
# Terminal 1: Start robot host (on LeKiwi device)
python -m lerobot.robots.lekiwi.lekiwi_host \
    --robot.id=my_awesome_kiwi \
    --robot.use_dual_boards=true \
    --host.connection_time_s=600

# Terminal 2: Run teleoperation (on laptop)
python examples/lekiwi/teleoperate_xbox.py        # Xbox controller (recommended)
python examples/lekiwi/teleoperate_keyboard_only.py  # Keyboard only
python examples/lekiwi/teleoperate.py             # Leader arm + keyboard
```

### Calibration & Setup
```bash
# Set up motor IDs (dual board)
lerobot-setup-motors --robot.type=lekiwi --robot.use_dual_boards=true

# Calibrate robot (dual board)
lerobot-calibrate \
    --robot.type=lekiwi \
    --robot.id=my_awesome_kiwi \
    --robot.use_dual_boards=true

# Manual port assignment (if auto-detection fails)
lerobot-calibrate \
    --robot.type=lekiwi \
    --robot.id=my_awesome_kiwi \
    --robot.use_dual_boards=true \
    --robot.arm_port=/dev/ttyACM0 \
    --robot.base_port=/dev/ttyACM1
```

### Recording & Evaluation
```bash
# Record demonstrations
python examples/lekiwi/record_xbox.py             # Xbox controller
python examples/lekiwi/record_xbox_hybrid.py      # Xbox arm + keyboard base
python examples/lekiwi/record.py                  # Leader arm + keyboard

# Evaluate trained policies
python examples/lekiwi/evaluate.py

# Replay recorded episodes
python examples/lekiwi/replay.py
```

### Testing & Troubleshooting
```bash
# Test Xbox controller connection
python -c "from lerobot.teleoperators.xbox import XboxTeleop, XboxTeleopConfig; \
           xbox = XboxTeleop(XboxTeleopConfig()); xbox.connect(); \
           print('Connected successfully')"

# Check USB devices and permissions
lsusb
sudo usermod -aG dialout $USER  # Add user to dialout group
```

## Architecture & Code Structure

### Main Entry Points (`examples/lekiwi/`)

**Teleoperation Scripts**:
- `teleoperate_xbox.py` (143 lines) - **Primary script**: Full Xbox arm + base control
- `teleoperate_xbox_hybrid.py` (128 lines) - Xbox arm + keyboard base
- `teleoperate.py` (72 lines) - Leader arm + keyboard base
- `teleoperate_keyboard_only.py` (111 lines) - Keyboard base-only
- `teleoperate_xbox_controller.py` (432 lines) - Legacy evdev-based Xbox (base-only)

**Recording Scripts**:
- `record_xbox.py`, `record_xbox_hybrid.py`, `record.py`

**Evaluation Scripts**:
- `evaluate.py`, `replay.py`

### Core Robot Implementation (`src/lerobot/`)

```
robots/lekiwi/
├── config_lekiwi.py       # Configuration with dual-board support
├── lekiwi_client.py       # Client interface
└── lekiwi_host             # Robot host server

teleoperators/
├── xbox/                   # NEW: Xbox controller module
│   ├── configuration_xbox.py (43 lines)
│   └── teleop_xbox.py     (~320 lines)
├── keyboard/               # Keyboard input
├── so100_leader/          # Leader arm input
└── config.py              # Base config classes
```

### Control Loop Pattern

All teleoperation scripts follow this standard pattern:
```python
while True:
    observation = robot.get_observation()       # Get robot state
    action = teleop.get_action()               # Get user input
    robot.send_action(action)                  # Send to robot
    events = teleop.get_teleop_events()       # Check quit events
    if events.get("terminate_episode"): break
    busy_wait(max(1.0/FPS - elapsed_time, 0))  # Maintain 30 Hz
```

### Action Space Format

All teleoperators output actions in this standardized format:
```python
{
    "arm_shoulder_pan": float,      # Radians
    "arm_shoulder_lift": float,     # Radians
    "arm_elbow_flex": float,        # Radians
    "arm_wrist_flex": float,        # Radians
    "arm_wrist_roll": float,        # Radians
    "arm_gripper": float,           # -1.0 to 1.0
    "x.vel": float,                 # m/s (forward/backward)
    "y.vel": float,                 # m/s (strafe left/right)
    "theta.vel": float,             # deg/s (rotation)
}
```

## Dual Motor Board Architecture

### Hardware Configuration
- **Board 1 (Arm)**: Motors 1-6 @ 12V for torque
- **Board 2 (Base)**: Motors 7-9 @ 7V for speed
- **Auto-detection**: Tests which USB port has which board by pinging Motor ID 1
- **Manual override**: Can specify ports explicitly if auto-detection fails

### Key Configuration Parameters
```python
# Enable dual board mode
use_dual_boards=True

# Manual port assignment (optional)
arm_port="/dev/ttyACM0"
base_port="/dev/ttyACM1"
```

## Xbox Controller Implementation

### Current Architecture (PyGame-based)
- **Cross-platform**: Linux, macOS, Windows support via PyGame
- **Full control**: Both arm (position-based) and base (velocity-based)
- **Action mapping**:
  - Left stick: Wrist roll/flex
  - Right stick: Base translation/rotation
  - D-pad: Shoulder pan/elbow flex
  - Triggers: Gripper control
  - LB/RB: Speed modulation (0.5x/2.0x)

### Configuration (`XboxTeleopConfig`)
```python
deadzone=0.1              # Stick deadzone threshold
base_linear_vel=0.3       # m/s for base translation
base_angular_vel=90.0     # deg/s for base rotation
arm_speed=0.05            # Radians per control loop
gripper_speed=0.05        # Gripper increment per loop
stick_scale=1.0           # Sensitivity multiplier
```

### Migration from evdev
- **Old**: `teleoperate_xbox_controller.py` (Linux-only, base-only, evdev)
- **New**: `XboxTeleop` module (cross-platform, full control, PyGame)

## Robot IP Configuration

**Important**: Update `ROBOT_IP` in teleoperation scripts:
- `"localhost"` - When running on the robot itself
- `"192.168.8.157"` - Current network IP (based on recent commits)
- Update based on your robot's actual IP address

## Key Dependencies

### Required for LeKiwi
```toml
[project.optional-dependencies]
lekiwi = ["lerobot[feetech]", "pyzmq>=26.2.1,<28.0.0"]
feetech = ["feetech-servo-sdk>=1.0.0,<2.0.0"]
```

### Xbox Controller Support
```toml
pygame-dep = ["pygame>=2.5.1,<2.7.0"]
```

### Core Stack
- Python 3.10+
- PyTorch for ML policies
- OpenCV for vision
- Rerun SDK for visualization

## Common Issues & Solutions

### Port Auto-Detection Fails
1. Check both boards are powered and connected via USB
2. Verify Motor ID 1 exists on arm board using `lerobot-setup-motors`
3. Use manual port assignment with `--robot.arm_port` and `--robot.base_port`

### Xbox Controller Issues
1. Install pygame: `pip install pygame`
2. Test connection: `lsusb` should show controller
3. Increase deadzone in config if experiencing drift
4. Refer to `XBOX_CONTROLLER_README.md` for detailed troubleshooting

### USB Permissions
```bash
sudo usermod -aG dialout $USER
# Log out and log back in
```

### Connection Timeouts
```bash
# Increase timeout for testing
--host.connection_time_s=600
```

## Recent Development Focus

Based on git history, recent work has focused on:
1. **Xbox Controller Redesign**: Migration from evdev to PyGame architecture
2. **Hybrid Teleoperation**: Xbox arm + keyboard base combinations
3. **Controller Mapping**: Improved stick-to-joint assignments
4. **Network Configuration**: Active testing with physical robot (IP: 192.168.8.157)

## Important Development Notes

1. **Custom Fork Only**: Never push to HuggingFace upstream repository
2. **Dual Board Emphasis**: Most development assumes dual-board setup
3. **Xbox Primary**: Xbox controller is the recommended control method
4. **Cross-Platform**: PyGame ensures Mac/Windows compatibility
5. **Position vs Velocity**: Arm uses position control, base uses velocity control

## Testing Workflow

1. **Connect Hardware**: Ensure both motor boards powered and connected
2. **Start Host**: Run `lekiwi_host` on robot with dual boards enabled
3. **Test Controller**: Verify Xbox controller detection
4. **Run Teleoperation**: Start with `teleoperate_xbox.py`
5. **Monitor Output**: Check action values in terminal for expected ranges
6. **Record Data**: Use `record_xbox.py` for dataset collection

## Documentation References

- `README.md` - Main project overview and dual-board setup
- `XBOX_CONTROLLER_README.md` - Complete Xbox controller guide
- `IMPLEMENTATION_SUMMARY.md` - Technical implementation details
- `docs/README.md` - Extended documentation