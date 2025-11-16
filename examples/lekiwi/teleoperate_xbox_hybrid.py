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
Hybrid teleoperation script: Xbox controller for arm and base, with keyboard fallback.

This script combines Xbox controller for full robot control (arm and base).
You can optionally enable keyboard control for base as an alternative.

Requirements:
    pygame (for Xbox controller)
    pynput (for keyboard input, optional)

Usage:
    1. On the robot, run:
       python -m lerobot.robots.lekiwi.lekiwi_host --robot.id=my_awesome_kiwi

    2. Connect your Xbox controller via USB or Bluetooth

    3. On your laptop/client, edit ROBOT_IP and USE_KEYBOARD_FOR_BASE below, then run:
       python examples/lekiwi/teleoperate_xbox_hybrid.py

Xbox Controller Layout:
    Left Stick:
        - X-axis: Arm wrist roll (left/right)
        - Y-axis: Arm wrist flex (up/down)

    Right Stick:
        - X-axis: Base rotation (left/right)
        - Y-axis: Base forward/backward movement

    D-Pad:
        - Up/Down: Arm shoulder pan (forward/backward)
        - Left/Right: Arm elbow flex (out/in)

    Triggers:
        - LT: Decrease gripper
        - RT: Increase gripper

    Buttons:
        - LB: Arm move slower
        - RB: Arm move faster
        - Back: Quit

Keyboard Layout (optional):
    Arrow Keys: Base movement (only if USE_KEYBOARD_FOR_BASE = True)
    Shift: Speed modulation
"""

import time

from lerobot.robots.lekiwi import LeKiwiClient, LeKiwiClientConfig
from lerobot.teleoperators.keyboard import KeyboardTeleop, KeyboardTeleopConfig
from lerobot.teleoperators.xbox import XboxTeleop, XboxTeleopConfig
from lerobot.utils.robot_utils import busy_wait
from lerobot.utils.visualization_utils import init_rerun, log_rerun_data

FPS = 30

# Configuration: Set to True to use keyboard for base, False for Xbox right stick
USE_KEYBOARD_FOR_BASE = False

# Create the robot and teleoperator configurations
robot_config = LeKiwiClientConfig(remote_ip="localhost", id="my_lekiwi")
xbox_config = XboxTeleopConfig(id="my_xbox_controller")
keyboard_config = KeyboardTeleopConfig(id="my_laptop_keyboard")

# Initialize the robot and teleoperator
robot = LeKiwiClient(robot_config)
xbox = XboxTeleop(xbox_config)

# Connect to the robot and Xbox controller
robot.connect()
xbox.connect()

# Initialize keyboard only if needed for base control
if USE_KEYBOARD_FOR_BASE:
    keyboard = KeyboardTeleop(keyboard_config)
    keyboard.connect()
else:
    keyboard = None

# Init rerun viewer
init_rerun(session_name="lekiwi_xbox_hybrid")

if not robot.is_connected or not xbox.is_connected:
    raise ValueError("Robot or Xbox controller is not connected!")
if USE_KEYBOARD_FOR_BASE and not keyboard.is_connected:
    raise ValueError("Keyboard is not connected!")

print("Starting hybrid teleoperation (Xbox controller)...")
print("\nXbox Controller mappings:")
print("  Left Stick: Arm wrist control")
print("  Right Stick: Base translation & rotation")
print("  D-Pad: Arm shoulder & elbow control")
print("  Triggers: Gripper control")
print("  LB/RB: Arm speed modulation")
print("  Back: Quit")

if USE_KEYBOARD_FOR_BASE:
    print("\nKeyboard mappings (supplemental):")
    print("  Arrow Keys: Base movement")
    print("  Shift: Speed modulation")
else:
    print("\nSAFETY NOTE: Deadzone of 0.1 ensures untouched sticks produce NO motion.")
    print("Keep controller idle for no motion. Press Back to exit safely.")
print()

try:
    while True:
        t0 = time.perf_counter()

        # Get robot observation
        observation = robot.get_observation()

        # Get Xbox controller action
        xbox_action = xbox.get_action()

        # Create action with proper key format for LeKiwiClient
        # Xbox outputs arm joints without suffix, but LeKiwiClient expects ".pos" suffix
        action = {f"{k}.pos": v for k, v in xbox_action.items() if k.startswith("arm_")}

        # Add base control - either from Xbox right stick or keyboard
        base_keys = ["x.vel", "y.vel", "theta.vel"]
        xbox_base_action = {k: v for k, v in xbox_action.items() if k in base_keys}

        if USE_KEYBOARD_FOR_BASE:
            # Get keyboard action for base control (overrides Xbox)
            keyboard_keys = keyboard.get_action()
            keyboard_base_action = robot._from_keyboard_to_base_action(keyboard_keys)
            base_action = keyboard_base_action if len(keyboard_base_action) > 0 else xbox_base_action
        else:
            # Use Xbox right stick for base control
            base_action = xbox_base_action

        # Combine arm and base actions
        action.update(base_action)

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
    if keyboard is not None:
        keyboard.disconnect()
    print("Done!")
