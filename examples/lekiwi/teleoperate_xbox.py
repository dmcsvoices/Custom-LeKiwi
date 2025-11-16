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
Xbox Controller teleoperation script for LeKiwi robot arm and base control.

This script uses an Xbox controller to control both the arm and mobile base of the LeKiwi robot.
No leader arm required - just Xbox controller for full teleoperation.

Requirements:
    pygame (for Xbox controller input)

Usage:
    1. On the robot, run:
       python -m lerobot.robots.lekiwi.lekiwi_host --robot.id=my_awesome_kiwi

    2. Connect your Xbox controller via USB or Bluetooth

    3. On your laptop/client, edit ROBOT_IP below, then run:
       python examples/lekiwi/teleoperate_xbox.py

Controller Layout:
    Left Stick:
        - X-axis: Arm wrist roll (left/right) / Arm elbow flex when LS pressed
        - Y-axis: Arm wrist flex (up/down)

    Right Stick (Base Control):
        - X-axis: Base rotation (left/right) OR left/right strafe (toggle with RS)
        - Y-axis: Base forward/backward movement (always active)

    D-Pad (Arm Control):
        - Left/Right: Arm shoulder pan (left/right)
        - Up/Down: Arm shoulder lift (up/down)

    Analog Triggers:
        - LT: Decrease gripper (proportional)
        - RT: Increase gripper (proportional)

    Stick & Shoulder Buttons:
        - LS: Left stick press to control elbow flex (left stick X becomes elbow)
        - RS: Right stick press to toggle base mode (rotation ↔ strafe)
        - RB: Speed multiplier (2x arm speed)

    Face Buttons:
        - B: Emergency stop

    Menu Buttons:
        - Back: Quit
        - Start: Reset arm to home position
"""

import time

from lerobot.robots.lekiwi import LeKiwiClient, LeKiwiClientConfig
from lerobot.teleoperators.xbox import XboxTeleop, XboxTeleopConfig
from lerobot.utils.robot_utils import busy_wait
from lerobot.utils.visualization_utils import init_rerun, log_rerun_data

FPS = 30

# Create the robot and teleoperator configurations
robot_config = LeKiwiClientConfig(remote_ip="localhost", id="my_lekiwi")
xbox_config = XboxTeleopConfig(id="my_xbox_controller")

# Initialize the robot and teleoperator
robot = LeKiwiClient(robot_config)
xbox = XboxTeleop(xbox_config)

# Connect to the robot and teleoperator
# To connect you already should have this script running on LeKiwi:
# `python -m lerobot.robots.lekiwi.lekiwi_host --robot.id=my_awesome_kiwi`
robot.connect()
xbox.connect()

# Init rerun viewer
init_rerun(session_name="lekiwi_xbox_teleop")

if not robot.is_connected or not xbox.is_connected:
    raise ValueError("Robot or Xbox controller is not connected!")

print("Starting Xbox controller teleoperation...")
print("\nController mappings:")
print("  Left Stick: Wrist roll (X) & wrist flex (Y)")
print("  Left Stick Press (LS): Hold to control elbow flex with left stick X")
print("  Right Stick: Rotation (X) OR strafe (X) & forward/backward (Y)")
print("  Right Stick Press (RS): Toggle between rotation and strafe modes")
print("  D-Pad: Shoulder pan (left/right) & shoulder lift (up/down)")
print("  LT/RT: Gripper decrease/increase (proportional)")
print("  RB: Speed multiplier (2x arm speed)")
print("  Back: Quit")
print()
print("SAFETY NOTE: Deadzone of 0.1 ensures untouched sticks produce NO motion.")
print("Keep controller idle for no motion. Press Back to exit safely.")

try:
    while True:
        t0 = time.perf_counter()

        # Get robot observation
        observation = robot.get_observation()

        # Get Xbox controller action (includes arm and base)
        xbox_action = xbox.get_action()

        # Create action with proper key format for LeKiwiClient
        # Xbox outputs arm joints without suffix, but LeKiwiClient expects ".pos" suffix
        action = {f"{k}.pos": v for k, v in xbox_action.items() if k.startswith("arm_")}
        action.update({k: v for k, v in xbox_action.items() if k in ["x.vel", "y.vel", "theta.vel"]})

        # Send action to robot
        result = robot.send_action(action)

        # Visualize
        log_rerun_data(observation=observation, action=action)

        # Check for teleop events (like quit button)
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
    print("Done!")
