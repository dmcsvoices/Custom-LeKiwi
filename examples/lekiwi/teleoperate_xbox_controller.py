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
    pip install approxeng.input

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

from approxeng.input.selectbinder import ControllerResource

from lerobot.robots.lekiwi import LeKiwiClient, LeKiwiClientConfig
from lerobot.utils.robot_utils import busy_wait

# ===== CONFIGURE THIS =====
ROBOT_IP = "localhost"  # Change to your robot's IP address (e.g., "192.168.1.100")
FPS = 30

# Base velocities (these get scaled by stick deflection and speed multiplier)
BASE_LINEAR_VEL = 0.5   # m/s - base translation speed
BASE_ANGULAR_VEL = 50.0  # deg/s - base rotation speed

# Controller settings
DEADZONE = 0.1  # Ignore stick values below this threshold (prevents drift)
# ==========================


def controller_to_base_action(joystick, current_speed_multiplier=1.0):
    """
    Convert Xbox controller input to LeKiwi base action.

    Args:
        joystick: approxeng.input controller object
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
    # To connect you should already have the host running on LeKiwi:
    # python -m lerobot.robots.lekiwi.lekiwi_host --robot.id=my_awesome_kiwi --robot.use_dual_boards=true --host.connection_time_s=600
    robot.connect()

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

    try:
        while True:
            # Connect to controller (supports Xbox, PlayStation, etc.)
            try:
                with ControllerResource() as joystick:
                    print(f"\n✓ Connected to: {joystick.name}")
                    print("Ready to control! Use Back/Select to quit.\n")

                    # Main control loop
                    while joystick.connected:
                        t0 = time.perf_counter()

                        # Get robot observation
                        observation = robot.get_observation()

                        # Check for button presses
                        joystick.check_presses()

                        # Back/Select button = quit
                        if joystick.presses.select or joystick.presses.start:
                            if joystick.presses.select:
                                print("\n✓ Back/Select pressed - quitting...")
                                return
                            elif joystick.presses.start:
                                print(f"Current speed multiplier: {current_speed:.2f}x")

                        # B button = emergency stop
                        if joystick.presses.circle:  # 'B' on Xbox (circle in standard naming)
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
                        _ = robot.send_action(action)

                        # Maintain loop frequency
                        busy_wait(max(1.0 / FPS - (time.perf_counter() - t0), 0.0))

                    print("\n⚠ Controller disconnected! Reconnecting...")

            except IOError:
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
