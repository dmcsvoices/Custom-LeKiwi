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
Hybrid teleoperation script: Leader Arm for arm control + Xbox for base movement.

This script combines a leader arm for precise arm/gripper control with Xbox controller
for convenient base movement (translation and rotation).

Requirements:
    pygame (for Xbox controller)

Usage:
    1. On the robot, run:
       python -m lerobot.robots.lekiwi.lekiwi_host --robot.id=my_awesome_kiwi

    2. Connect your leader arm via USB and Xbox controller via USB/Bluetooth

    3. On your laptop/client, edit ROBOT_IP and leader arm port below, then run:
       python examples/lekiwi/teleoperate_xbox_hybrid.py

Leader Arm Layout (for arm and gripper):
    Use your leader arm's native control interface for full arm and gripper control.

Xbox Controller Layout (for base movement only):
    Right Stick:
        - X-axis: Base rotation (left/right)
        - Y-axis: Base forward/backward movement

    Note: Other Xbox controls are not used in this hybrid mode.
"""

import time

from lerobot.robots.lekiwi import LeKiwiClient, LeKiwiClientConfig
from lerobot.teleoperators.so100_leader import SO100Leader, SO100LeaderConfig
from lerobot.teleoperators.xbox import XboxTeleop, XboxTeleopConfig
from lerobot.utils.robot_utils import busy_wait
from lerobot.utils.visualization_utils import init_rerun, log_rerun_data

FPS = 30

# Create the robot and teleoperator configurations
robot_config = LeKiwiClientConfig(remote_ip="192.168.8.157", id="my_lekiwi")
leader_arm_config = SO100LeaderConfig(port="/dev/tty.usbmodem58FD0173401", id="my_awesome_leader_arm")
xbox_config = XboxTeleopConfig(id="my_xbox_controller")

# Initialize the robot and teleoperators
robot = LeKiwiClient(robot_config)
leader_arm = SO100Leader(leader_arm_config)
xbox = XboxTeleop(xbox_config)

# Connect to the robot and teleoperators
robot.connect()
leader_arm.connect()
xbox.connect()

# Init rerun viewer
init_rerun(session_name="lekiwi_leader_xbox_hybrid")

if not robot.is_connected or not leader_arm.is_connected or not xbox.is_connected:
    raise ValueError("Robot or teleoperators are not connected!")

print("Starting hybrid teleoperation (Leader Arm for arm + Xbox for base)...")
print("\nLeader Arm mappings:")
print("  Full arm and gripper control via leader arm")
print("\nXbox Controller mappings:")
print("  Right Stick X: Base rotation (left/right)")
print("  Right Stick Y: Base forward/backward movement")
print()
print("SAFETY NOTE: Deadzone of 0.1 ensures untouched sticks produce NO motion.")
print("Keep Xbox right stick idle for no base motion.")
print()

try:
    while True:
        t0 = time.perf_counter()

        # Get robot observation
        observation = robot.get_observation()

        # Get leader arm action (for arm and gripper control)
        arm_action = leader_arm.get_action()
        arm_action = {f"arm_{k}": v for k, v in arm_action.items()}

        # Get Xbox action (for base movement only) - pass observation for initialization
        xbox_action = xbox.get_action(observation)
        base_keys = ["x.vel", "y.vel", "theta.vel"]
        base_action = {k: v for k, v in xbox_action.items() if k in base_keys}

        # Combine arm and base actions
        action = {**arm_action, **base_action}

        # Send action to robot
        result = robot.send_action(action)

        # Visualize
        log_rerun_data(observation=observation, action=action)

        # Check for Xbox teleop events (like quit button to exit)
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
    leader_arm.disconnect()
    xbox.disconnect()
    print("Done!")
