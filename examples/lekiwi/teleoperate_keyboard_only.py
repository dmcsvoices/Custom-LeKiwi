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
Simplified teleoperation script for LeKiwi using ONLY keyboard control.
No leader arm required - just keyboard control for the base.

Usage:
    1. On the robot, run:
       python -m lerobot.robots.lekiwi.lekiwi_host --robot.id=my_awesome_kiwi --robot.use_dual_boards=true --host.connection_time_s=600

    2. On your laptop/client, edit the ROBOT_IP below, then run:
       python examples/lekiwi/teleoperate_keyboard_only.py

Keyboard controls:
    w/s - forward/backward
    a/d - strafe left/right
    z/x - rotate left/right
    r/f - increase/decrease speed
    q - quit
"""

import time

from lerobot.robots.lekiwi import LeKiwiClient, LeKiwiClientConfig
from lerobot.teleoperators.keyboard.teleop_keyboard import KeyboardTeleop, KeyboardTeleopConfig
from lerobot.utils.robot_utils import busy_wait

# ===== CONFIGURE THIS =====
ROBOT_IP = "localhost"  # Change to your robot's IP address (e.g., "192.168.1.100")
FPS = 30
# ==========================

# Create the robot and teleoperator configurations
robot_config = LeKiwiClientConfig(remote_ip=ROBOT_IP, id="my_awesome_kiwi")
keyboard_config = KeyboardTeleopConfig(id="my_laptop_keyboard")

# Initialize the robot and teleoperator
robot = LeKiwiClient(robot_config)
keyboard = KeyboardTeleop(keyboard_config)

print("Connecting to robot...")
# Connect to the robot and teleoperator
# To connect you should already have the host running on LeKiwi:
# python -m lerobot.robots.lekiwi.lekiwi_host --robot.id=my_awesome_kiwi --robot.use_dual_boards=true --host.connection_time_s=600
robot.connect()
keyboard.connect()

if not robot.is_connected or not keyboard.is_connected:
    raise ValueError("Robot or keyboard is not connected!")

print("\n" + "="*60)
print("KEYBOARD TELEOPERATION ACTIVE")
print("="*60)
print("Controls:")
print("  w/s - forward/backward")
print("  a/d - strafe left/right")
print("  z/x - rotate left/right")
print("  r/f - increase/decrease speed")
print("  q - quit")
print("="*60)
print("\nStarting teleop loop...")

try:
    while True:
        t0 = time.perf_counter()

        # Get robot observation
        observation = robot.get_observation()

        # Get keyboard action for base control
        keyboard_keys = keyboard.get_action()
        base_action = robot._from_keyboard_to_base_action(keyboard_keys)

        # For keyboard-only mode, we need to send a complete action
        # If no base action, send zeros to keep the watchdog happy
        if len(base_action) == 0:
            action = {
                "x.vel": 0.0,
                "y.vel": 0.0,
                "theta.vel": 0.0,
            }
        else:
            action = base_action

        # Send action to robot
        _ = robot.send_action(action)

        # Maintain loop frequency
        busy_wait(max(1.0 / FPS - (time.perf_counter() - t0), 0.0))

except KeyboardInterrupt:
    print("\n\nKeyboard interrupt - shutting down...")
finally:
    print("Disconnecting...")
    robot.disconnect()
    keyboard.disconnect()
    print("Done!")
