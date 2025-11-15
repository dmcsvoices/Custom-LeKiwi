#!/usr/bin/env python

# Copyright 2025 The HuggingFace Inc. team. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Xbox Controller teleoperation script for LeKiwi robot base control.
No leader arm required - just Xbox controller for the base.

Requirements:
    None (uses evdev which is typically pre-installed)

Usage:
    1. On the robot, run:
       python -m lerobot.robots.lekiwi.lekiwi_host --robot.id=my_awesome_kiwi --robot.use_dual_boards=true --host.connection_time_s=600

    2. Connect your Xbox controller via USB or Bluetooth

    3. On your laptop/client, edit the ROBOT_IP below, then run:
       python examples/lekiwi/teleoperate_xbox_controller.py

Controller Layout:
    Left Stick:
        - Forward/Backward (Y-axis)
        - Strafe Left/Right (X-axis)

    Right Stick:
        - Rotate Left/Right (X-axis)

    Triggers:
        - Right Trigger (RT): Speed boost (up to 2x)
        - Left Trigger (LT): Slow mode (down to 0.3x)

    Buttons:
        - B Button: Emergency stop (zeros all velocities)
        - Start Button: Show current speed
        - Back/Select: Quit

Notes:
    - Supports Xbox 360, Xbox One, and other compatible controllers
    - Dead zones are applied to prevent drift (threshold: 0.1)
    - Base speed is configurable (default: 50.0 deg/s for rotation, proportional for translation)
"""

import time
import struct
import glob

from evdev import InputDevice, ecodes, list_devices

from lerobot.robots.lekiwi import LeKiwiClient, LeKiwiClientConfig
from lerobot.utils.robot_utils import busy_wait

# ===== CONFIGURE THIS =====
ROBOT_IP = "localhost"  # Change to your robot's IP address (e.g., "192.168.1.100")
FPS = 30

# Base velocities (these get scaled by stick deflection and speed multiplier)
BASE_LINEAR_VEL = 0.5   # m/s - base translation speed
BASE_ANGULAR_VEL = 50.0  # deg/s - base rotation speed

# Controller settings
DEADZONE = 0.08  # Ignore stick values below this threshold (prevents drift)
# ==========================


class XboxController:
    """Xbox controller wrapper using evdev for reliable input detection."""

    def __init__(self, device_path=None):
        """Initialize Xbox controller.

        Args:
            device_path: Path to the controller device (e.g., /dev/input/js0)
                        If None, will auto-detect Xbox controller
        """
        self.device = None
        self.name = "Xbox Controller"
        self.connected = True

        if device_path is None:
            # Auto-detect Xbox controller
            device_path = self._find_xbox_controller()

        if device_path:
            try:
                self.device = InputDevice(device_path)
                self.name = self.device.name
                print(f"✓ Connected to: {self.name}")
            except Exception as e:
                print(f"Error opening device {device_path}: {e}")
                raise
        else:
            raise IOError("No Xbox controller found")

        # Initialize state
        self.analog_state = {
            'ABS_X': 0,      # Left stick X (strafe)
            'ABS_Y': 0,      # Left stick Y (forward/backward)
            'ABS_RX': 0,     # Right stick X (rotate)
            'ABS_RY': 0,     # Right stick Y (not used)
            'ABS_Z': 0,      # Left trigger
            'ABS_RZ': 0,     # Right trigger
        }
        self.button_state = {}

    @staticmethod
    def _find_xbox_controller():
        """Auto-detect Xbox controller from available input devices."""
        for device_path in list_devices():
            try:
                device = InputDevice(device_path)
                name = device.name.lower()
                # Check for Xbox controller indicators
                if 'xbox' in name or 'wireless controller' in name:
                    # Verify it has the expected axes
                    if hasattr(device, 'capabilities'):
                        caps = device.capabilities()
                        if ecodes.EV_ABS in caps:
                            print(f"Found controller: {device.name} at {device_path}")
                            return device_path
            except Exception:
                pass
        return None

    def read_input(self, timeout=0.01):
        """Read and process input events from the controller.

        Args:
            timeout: Timeout in seconds for reading events. Set low to prevent blocking
                    during reconnection attempts while still capturing all queued events.
        """
        import select

        try:
            # Use select with timeout for non-blocking reads
            # This reads all available events without hanging on reconnection
            rlist, _, _ = select.select([self.device], [], [], timeout)

            if rlist:
                # Events are available, read them all
                for event in self.device.read():
                    if event.type == ecodes.EV_ABS:
                        # Analog input (sticks, triggers)
                        axis_name = ecodes.ABS[event.code]
                        # Normalize to 0.0 to 1.0 range for triggers, -1.0 to 1.0 for sticks
                        if axis_name in ['ABS_Z', 'ABS_RZ']:
                            # Triggers: 0 to 1023
                            self.analog_state[axis_name] = max(0.0, event.value / 1023.0)
                        else:
                            # Sticks: -32768 to 32767
                            self.analog_state[axis_name] = event.value / 32768.0

                    elif event.type == ecodes.EV_KEY:
                        # Button input
                        button_name = ecodes.BTN[event.code]
                        # Handle case where button_name might be a list
                        if isinstance(button_name, list):
                            button_name = button_name[0] if button_name else f"BTN_{event.code}"
                        self.button_state[button_name] = event.value

        except (IOError, OSError) as e:
            self.connected = False
            raise

    def debug_print_state(self):
        """Print current controller state for debugging."""
        return f"LX:{self.lx:.2f} LY:{self.ly:.2f} RX:{self.rx:.2f} LT:{self.lt:.2f} RT:{self.rt:.2f}"

    @property
    def lx(self):
        """Left stick X (strafe)."""
        return self.analog_state.get('ABS_X', 0.0)

    @property
    def ly(self):
        """Left stick Y (forward/backward)."""
        return self.analog_state.get('ABS_Y', 0.0)

    @property
    def rx(self):
        """Right stick X (rotate)."""
        return self.analog_state.get('ABS_RX', 0.0)

    @property
    def ry(self):
        """Right stick Y."""
        return self.analog_state.get('ABS_RY', 0.0)

    @property
    def lt(self):
        """Left trigger."""
        return max(0.0, self.analog_state.get('ABS_Z', 0.0))

    @property
    def rt(self):
        """Right trigger."""
        return max(0.0, self.analog_state.get('ABS_RZ', 0.0))

    @property
    def button_b(self):
        """B button (circle on some controllers)."""
        return self.button_state.get('BTN_NORTH', 0)

    @property
    def button_select(self):
        """Back/Select button."""
        return self.button_state.get('BTN_SELECT', 0) or self.button_state.get('BTN_BACK', 0)

    @property
    def button_start(self):
        """Start button."""
        return self.button_state.get('BTN_START', 0)


def controller_to_base_action(joystick, current_speed_multiplier=1.0):
    """
    Convert Xbox controller input to LeKiwi base action.

    Args:
        joystick: XboxController object
        current_speed_multiplier: Current speed multiplier (1.0 = normal)

    Returns:
        dict: Action with x.vel, y.vel, theta.vel keys
    """
    # Read stick values (range: -1.0 to 1.0)
    # Note: ly is inverted (up = -1, down = 1) so we negate it
    forward_back = -joystick.ly if abs(joystick.ly) > DEADZONE else 0.0  # Forward/backward
    strafe = joystick.lx if abs(joystick.lx) > DEADZONE else 0.0         # Strafe left/right
    rotate = joystick.rx if abs(joystick.rx) > DEADZONE else 0.0         # Rotate left/right

    # Read triggers for speed control (range: 0.0 to 1.0)
    # RT = speed boost, LT = slow mode
    rt_value = joystick.rt if joystick.rt > 0.05 else 0.0  # Right trigger
    lt_value = joystick.lt if joystick.lt > 0.05 else 0.0  # Left trigger

    # Calculate speed multiplier based on triggers
    # RT: 1.0 -> 2.0 (boost)
    # LT: 1.0 -> 0.3 (slow)
    # Default: 1.0 (normal)
    if rt_value > 0.05:
        speed_mult = 1.0 + rt_value  # 1.0 to 2.0
    elif lt_value > 0.05:
        speed_mult = 1.0 - (0.7 * lt_value)  # 1.0 to 0.3
    else:
        speed_mult = 1.0

    # Apply base velocities and speed multiplier
    action = {
        "x.vel": forward_back * BASE_LINEAR_VEL * speed_mult,  # Forward/backward
        "y.vel": strafe * BASE_LINEAR_VEL * speed_mult,        # Strafe left/right
        "theta.vel": rotate * BASE_ANGULAR_VEL * speed_mult,   # Rotation
    }

    return action, speed_mult


def main():
    # Create the robot configuration
    robot_config = LeKiwiClientConfig(remote_ip=ROBOT_IP, id="my_awesome_kiwi")

    # Initialize the robot
    robot = LeKiwiClient(robot_config)

    print("Connecting to robot...")
    print(f"  IP: {ROBOT_IP}")
    # To connect you should already have the host running on LeKiwi:
    # python -m lerobot.robots.lekiwi.lekiwi_host --robot.id=my_awesome_kiwi --robot.use_dual_boards=true --host.connection_time_s=600
    try:
        robot.connect()
        print("✓ Connected to robot")
    except Exception as e:
        print(f"✗ Failed to connect: {e}")
        raise

    if not robot.is_connected:
        raise ValueError("Robot is not connected!")

    print("\n" + "="*70)
    print("XBOX CONTROLLER TELEOPERATION ACTIVE")
    print("="*70)
    print("Controller Layout:")
    print("  Left Stick Y    - Forward/Backward")
    print("  Left Stick X    - Strafe Left/Right")
    print("  Right Stick X   - Rotate Left/Right")
    print("  Right Trigger   - Speed Boost (2x)")
    print("  Left Trigger    - Slow Mode (0.3x)")
    print("  B Button        - Emergency Stop")
    print("  Start Button    - Show Speed")
    print("  Back/Select     - Quit")
    print("="*70)
    print("\nWaiting for Xbox controller...")

    current_speed = 1.0
    emergency_stopped = False
    joystick = None
    last_reconnect_attempt = time.time()

    try:
        while True:
            # Connect to controller
            try:
                if joystick is None:
                    # Prevent rapid reconnection attempts (min 2 seconds between attempts)
                    time_since_last = time.time() - last_reconnect_attempt
                    if time_since_last < 2.0:
                        time.sleep(2.0 - time_since_last)

                    last_reconnect_attempt = time.time()
                    joystick = XboxController()
                    print("Ready to control! Use Back/Select to quit.\n")

                # Main control loop
                while joystick and joystick.connected:
                    t0 = time.perf_counter()

                    # Read controller input FIRST (important: non-blocking)
                    try:
                        joystick.read_input()
                    except IOError:
                        print("\n⚠ Controller disconnected!")
                        joystick = None
                        break

                    # Get robot observation (this may block, so do it after reading controller)
                    try:
                        observation = robot.get_observation()
                    except Exception as e:
                        print(f"\n⚠ Robot observation error: {e}")
                        joystick = None
                        break

                    # Back/Select button = quit
                    if joystick.button_select:
                        print("\n✓ Back/Select pressed - quitting...")
                        return

                    # Start button = show speed
                    if joystick.button_start:
                        state = joystick.debug_print_state()
                        print(f"Speed: {current_speed:.2f}x | State: {state}")

                    # B button = emergency stop
                    if joystick.button_b:
                        emergency_stopped = not emergency_stopped
                        if emergency_stopped:
                            print("⚠ EMERGENCY STOP ACTIVATED - Press B to release")
                        else:
                            print("✓ Emergency stop released")

                    # Convert controller input to action
                    if emergency_stopped:
                        # Send zeros if emergency stopped
                        action = {
                            "x.vel": 0.0,
                            "y.vel": 0.0,
                            "theta.vel": 0.0,
                        }
                        current_speed = 0.0
                    else:
                        action, current_speed = controller_to_base_action(joystick)

                    # Send action to robot
                    result = robot.send_action(action)

                    # Debug: Print if any command is being sent
                    if action["x.vel"] != 0 or action["y.vel"] != 0 or action["theta.vel"] != 0:
                        if time.time() - getattr(controller_to_base_action, '_last_print', 0) > 0.5:
                            print(f"Sent: x={action['x.vel']:.3f}, y={action['y.vel']:.3f}, theta={action['theta.vel']:.1f} | Result: {result}")
                            controller_to_base_action._last_print = time.time()

                    # Maintain loop frequency
                    busy_wait(max(1.0 / FPS - (time.perf_counter() - t0), 0.0))

                if joystick is None:
                    print("⚠ No controller found. Make sure your Xbox controller is connected.")
                    print("  Retrying in 2 seconds...")

                    # Send zero velocities while waiting
                    action = {
                        "x.vel": 0.0,
                        "y.vel": 0.0,
                        "theta.vel": 0.0,
                    }
                    robot.send_action(action)

                    time.sleep(2)

            except IOError as e:
                print(f"⚠ Controller error: {e}")
                print("  Retrying in 2 seconds...")

                # Send zero velocities while waiting
                action = {
                    "x.vel": 0.0,
                    "y.vel": 0.0,
                    "theta.vel": 0.0,
                }
                robot.send_action(action)

                joystick = None
                time.sleep(2)

    except KeyboardInterrupt:
        print("\n\n✓ Keyboard interrupt - shutting down...")
    finally:
        print("\nDisconnecting...")
        # Send stop command before disconnecting
        stop_action = {
            "x.vel": 0.0,
            "y.vel": 0.0,
            "theta.vel": 0.0,
        }
        robot.send_action(stop_action)
        robot.disconnect()
        print("Done!")


if __name__ == "__main__":
    main()
