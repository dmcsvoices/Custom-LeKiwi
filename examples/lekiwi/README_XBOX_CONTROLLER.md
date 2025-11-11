# Xbox Controller Teleoperation for LeKiwi

This script enables Xbox controller-based teleoperation for the LeKiwi robot base, providing intuitive analog control for omnidirectional movement.

## Features

✅ **Universal Controller Support**: Works with Xbox 360, Xbox One, and other compatible controllers
✅ **Analog Control**: Smooth, proportional control via joysticks
✅ **Speed Control**: Dynamic speed adjustment with triggers
✅ **Emergency Stop**: Quick safety stop with B button
✅ **Auto-Reconnect**: Automatically reconnects if controller disconnects
✅ **Dead Zone**: Prevents drift from centered sticks

---

## Installation

### 1. Install approxeng.input Library

```bash
pip install approxeng.input
```

### 2. Connect Your Xbox Controller

**Via USB:**
- Simply plug the controller into your computer/Raspberry Pi
- No pairing needed

**Via Bluetooth (Raspberry Pi):**

```bash
# Enter Bluetooth pairing mode
sudo bluetoothctl

# In the bluetoothctl prompt:
power on
agent on
default-agent
scan on

# Put your Xbox controller in pairing mode:
# - Xbox One: Hold Xbox button + pairing button (top of controller)
# - Xbox 360: Press pairing button on controller and receiver

# When you see the controller's MAC address, pair it:
pair XX:XX:XX:XX:XX:XX
trust XX:XX:XX:XX:XX:XX
connect XX:XX:XX:XX:XX:XX
exit
```

### 3. Verify Controller Connection

```bash
# List input devices
ls /dev/input/

# Test with evtest (optional)
sudo apt install evtest
sudo evtest
# Select your controller from the list
```

---

## Usage

### Step 1: Start the Robot Host

On your Raspberry Pi / robot:

```bash
python -m lerobot.robots.lekiwi.lekiwi_host \
    --robot.id=my_awesome_kiwi \
    --robot.use_dual_boards=true \
    --host.connection_time_s=600
```

### Step 2: Configure the Script

Edit `teleoperate_xbox_controller.py` and set your robot's IP address:

```python
ROBOT_IP = "localhost"  # Change to your robot's IP (e.g., "192.168.1.100")
```

If running the client on the same machine as the host, keep it as `"localhost"`.

### Step 3: Run the Controller Script

```bash
python examples/lekiwi/teleoperate_xbox_controller.py
```

You should see:
```
Connecting to robot...
✓ Robot connected!

XBOX CONTROLLER TELEOPERATION ACTIVE
======================================================================
Waiting for Xbox controller...
✓ Connected to: Xbox Wireless Controller
Ready to control! Use Back/Select to quit.
```

---

## Controller Mapping

### Standard Layout (Xbox Controller)

```
        LT              RT
         ○              ○
    ┌─────────┴────────────┐
    │      [Back] [Start]  │
    │                      │
    │   ◄►                 │  ┌─────┐
    │   ▲▼    (XBOX)    [Y]│  │  RX │ ← Rotation
    │                   [X][B]│  │     │
    │         ○         [A]│  └─────┘
    │        LY              │
    │        LX              │
    └──────────────────────┘

Legend:
  LX/LY = Left Stick (X/Y axes)
  RX = Right Stick (X axis only)
  LT/RT = Left/Right Triggers
```

### Controls

| Input | Function | Range | Description |
|-------|----------|-------|-------------|
| **Left Stick Y** | Forward/Backward | -1.0 to 1.0 | Push forward to move forward, pull back to move backward |
| **Left Stick X** | Strafe Left/Right | -1.0 to 1.0 | Push right to strafe right, push left to strafe left |
| **Right Stick X** | Rotate | -1.0 to 1.0 | Push right to rotate clockwise, push left to rotate counter-clockwise |
| **Right Trigger** | Speed Boost | 0.0 to 1.0 | Hold to increase speed up to 2x |
| **Left Trigger** | Slow Mode | 0.0 to 1.0 | Hold to decrease speed down to 0.3x |
| **B Button** | Emergency Stop | Toggle | Press to stop all motion; press again to resume |
| **Start** | Show Speed | Instant | Display current speed multiplier |
| **Back/Select** | Quit | Instant | Exit the program |

---

## Configuration

Edit the top of `teleoperate_xbox_controller.py` to adjust settings:

```python
# Network
ROBOT_IP = "localhost"  # Robot IP address
FPS = 30                # Control loop frequency (Hz)

# Base velocities
BASE_LINEAR_VEL = 0.5   # Translation speed (m/s)
BASE_ANGULAR_VEL = 50.0 # Rotation speed (deg/s)

# Controller settings
DEADZONE = 0.1          # Stick deadzone (0.0 to 1.0)
```

### Adjusting Speeds

**Too Fast?** Decrease `BASE_LINEAR_VEL` and `BASE_ANGULAR_VEL`:
```python
BASE_LINEAR_VEL = 0.3   # Slower translation
BASE_ANGULAR_VEL = 30.0 # Slower rotation
```

**Too Slow?** Increase the values:
```python
BASE_LINEAR_VEL = 0.8   # Faster translation
BASE_ANGULAR_VEL = 80.0 # Faster rotation
```

**Stick Drift?** Increase the deadzone:
```python
DEADZONE = 0.15  # Larger deadzone to ignore small movements
```

---

## Troubleshooting

### Controller Not Detected

**Error:** `No controller found. Make sure your Xbox controller is connected.`

**Solutions:**
1. **Check USB connection** - Try a different USB port
2. **Check Bluetooth pairing** - Re-pair the controller
3. **Verify device** - Run `ls /dev/input/event*` and check for new device
4. **Install xboxdrv** (if needed):
   ```bash
   sudo apt install xboxdrv
   ```

### Controller Disconnects Randomly

**Bluetooth Range:**
- Stay within 10 meters of the Raspberry Pi
- Ensure no obstacles between controller and Pi

**Low Battery:**
- Replace batteries or charge the controller

**USB Issues:**
- Try a different USB cable or port
- Some USB 3.0 ports can cause interference

### Buttons Not Working / Wrong Mapping

Different controllers may use different button codes. The script uses standardized names from `approxeng.input`:

- **Xbox**: `circle` = B, `cross` = A, `square` = X, `triangle` = Y
- **PlayStation**: `circle` = O, `cross` = X, `square` = □, `triangle` = △

If buttons don't work, check which controller type was detected in the connection message.

### Robot Doesn't Move

1. **Check host is running:**
   ```bash
   # On the robot, you should see:
   INFO ... Waiting for commands...
   ```

2. **Verify network connection:**
   ```bash
   ping <ROBOT_IP>
   ```

3. **Check emergency stop:**
   - Press B button to release emergency stop if active

4. **Verify watchdog timeout:**
   - Default is 500ms - the script sends commands at 30 FPS (33ms intervals), well within the timeout

---

## Advanced Usage

### Running on Different Machines

**Robot (Raspberry Pi):**
```bash
python -m lerobot.robots.lekiwi.lekiwi_host \
    --robot.id=my_awesome_kiwi \
    --robot.use_dual_boards=true \
    --host.connection_time_s=600
```

**Client (Your Laptop):**
1. Find your robot's IP:
   ```bash
   # On the robot
   hostname -I
   ```
2. Edit `ROBOT_IP` in the script to match
3. Run the script from your laptop with the controller connected

### Custom Button Mappings

To change button functions, edit the `main()` function:

```python
# Example: Use A button instead of B for emergency stop
if joystick.presses.cross:  # 'A' on Xbox
    emergency_stopped = not emergency_stopped
```

Available button names (standardized across controllers):
- `cross`, `circle`, `square`, `triangle`
- `l1`, `r1`, `l2`, `r2`
- `select`, `start`, `home`
- `ls`, `rs` (stick buttons)
- `dleft`, `dright`, `dup`, `ddown` (D-pad)

---

## Performance Tips

1. **Reduce FPS if laggy:**
   ```python
   FPS = 20  # Lower rate = less network traffic
   ```

2. **Increase watchdog timeout** if getting disconnection warnings:
   ```bash
   python -m lerobot.robots.lekiwi.lekiwi_host \
       --robot.id=my_awesome_kiwi \
       --robot.use_dual_boards=true \
       --host.connection_time_s=600 \
       --host.watchdog_timeout_ms=1000  # Increase from 500ms to 1000ms
   ```

3. **Use wired connection** for best performance (USB cable is more reliable than Bluetooth)

---

## Comparison: Xbox Controller vs Keyboard

| Feature | Xbox Controller | Keyboard |
|---------|----------------|----------|
| **Movement** | Analog (smooth, proportional) | Digital (on/off) |
| **Control** | One-handed possible | Two-handed required |
| **Precision** | High (analog sticks) | Low (binary keys) |
| **Speed Adjustment** | Real-time (triggers) | Step-based (r/f keys) |
| **Ease of Use** | Intuitive, ergonomic | More learning curve |
| **Setup** | Requires pairing/USB | Works immediately |
| **Portability** | Wireless option | Built into laptop |

---

## License

Copyright 2025 The HuggingFace Inc. team. All rights reserved.

Licensed under the Apache License, Version 2.0.

---

## Credits

- Built on [approxeng.input](https://github.com/ApproxEng/approxeng.input) library
- Based on LeRobot keyboard teleoperation script
- Part of the [Custom LeKiwi](https://github.com/dmcsvoices/Custom-LeKiwi) project
