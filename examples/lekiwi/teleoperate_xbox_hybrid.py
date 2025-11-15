# !/usr/bin/env python

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
Hybrid teleoperation script: Xbox controller for arm + Keyboard for base.

This script combines Xbox controller for arm control with keyboard input for base control.
Useful if you prefer keyboard-based base movement while using Xbox for arm.

Requirements:
    pygame (for Xbox controller)
    pynput (for keyboard input)

Usage:
    1. On the robot, run:
       python -m lerobot.robots.lekiwi.lekiwi_host --robot.id=my_awesome_kiwi

    2. Connect your Xbox controller via USB or Bluetooth

    3. On your laptop/client, edit ROBOT_IP below, then run:
       python examples/lekiwi/teleoperate_xbox_hybrid.py

Xbox Controller Layout:
    Left Stick:
        - X-axis: Arm wrist roll (left/right)
        - Y-axis: Arm wrist flex (up/down)

    Right Stick:
        - (Not used in hybrid mode - use keyboard for base)

    D-Pad:
        - Up/Down: Arm shoulder pan (forward/backward)
        - Left/Right: Arm elbow flex (out/in)

    Triggers:
        - LT: Decrease gripper
        - RT: Increase gripper

Keyboard Layout:
    Arrow Keys: Base movement
    Shift: Speed modulation
"""

import time

from lerobot.robots.lekiwi import LeKiwiClient, LeKiwiClientConfig
from lerobot.teleoperators.keyboard import KeyboardTeleop, KeyboardTeleopConfig
from lerobot.teleoperators.xbox import XboxTeleop, XboxTeleopConfig
from lerobot.utils.robot_utils import busy_wait
from lerobot.utils.visualization_utils import init_rerun, log_rerun_data

FPS = 30

# Create the robot and teleoperator configurations
robot_config = LeKiwiClientConfig(remote_ip="172.18.134.136", id="my_lekiwi")
xbox_config = XboxTeleopConfig(id="my_xbox_controller")
keyboard_config = KeyboardTeleopConfig(id="my_laptop_keyboard")

# Initialize the robot and teleoperator
robot = LeKiwiClient(robot_config)
xbox = XboxTeleop(xbox_config)
keyboard = KeyboardTeleop(keyboard_config)

# Connect to the robot and teleoperator
robot.connect()
xbox.connect()
keyboard.connect()

# Init rerun viewer
init_rerun(session_name="lekiwi_xbox_keyboard_hybrid")

if not robot.is_connected or not xbox.is_connected or not keyboard.is_connected:
    raise ValueError("Robot or teleoperators are not connected!")

print("Starting hybrid teleoperation (Xbox arm + Keyboard base)...")
print("\nXbox Controller mappings:")
print("  Left Stick: Arm wrist control")
print("  D-Pad: Arm shoulder & elbow control")
print("  Triggers: Gripper control")
print("\nKeyboard mappings:")
print("  Arrow Keys: Base movement")
print("  Shift: Speed modulation")
print()

try:
    while True:
        t0 = time.perf_counter()

        # Get robot observation
        observation = robot.get_observation()

        # Get Xbox controller action (arm only in this mode)
        xbox_action = xbox.get_action()
        arm_action = {f"arm_{k}": v for k, v in xbox_action.items() if k.startswith("arm_")}

        # Get keyboard action (base control)
        keyboard_keys = keyboard.get_action()
        base_action = robot._from_keyboard_to_base_action(keyboard_keys)

        # Combine arm and base actions
        action = {**arm_action, **base_action} if len(base_action) > 0 else arm_action

        # Send action to robot
        result = robot.send_action(action)

        # Visualize
        log_rerun_data(observation=observation, action=action)

        # Check for Xbox teleop events (like quit button)
        events = xbox.get_teleop_events()
        if events.get("terminate_episode", False):
            print("\nQuit button pressed - shutting down...")
            break

        busy_wait(max(1.0 / FPS - (time.perf_counter() - t0), 0.0))

except KeyboardInterrupt:
    print("\n\nKeyboard interrupt - shutting down...")
finally:
    print("\nDisconnecting...")
    robot.disconnect()
    xbox.disconnect()
    keyboard.disconnect()
    print("Done!")
