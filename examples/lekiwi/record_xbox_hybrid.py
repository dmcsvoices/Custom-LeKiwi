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
Hybrid data recording script: Leader arm OR Xbox controller for arm + Keyboard for base.

Records demonstration episodes combining leader arm or Xbox controller arm control with keyboard base control.

Set USE_LEADER_ARM = True to use the leader arm, or False to use Xbox controller.

Usage:
    1. On the robot, run:
       python -m lerobot.robots.lekiwi.lekiwi_host --robot.id=my_awesome_kiwi

    2. Connect your teleoperator:
       - For leader arm: Connect SO100 leader arm via USB
       - For Xbox controller: Connect Xbox controller via USB or Bluetooth

    3. On your laptop/client, edit configuration below, then run:
       python examples/lekiwi/record_xbox_hybrid.py
"""

from lerobot.datasets.lerobot_dataset import LeRobotDataset
from lerobot.datasets.utils import hw_to_dataset_features
from lerobot.processor import make_default_processors
from lerobot.robots.lekiwi.config_lekiwi import LeKiwiClientConfig
from lerobot.robots.lekiwi.lekiwi_client import LeKiwiClient
from lerobot.scripts.lerobot_record import record_loop
from lerobot.teleoperators.keyboard import KeyboardTeleop, KeyboardTeleopConfig
from lerobot.teleoperators.so100_leader import SO100Leader, SO100LeaderConfig
from lerobot.teleoperators.xbox import XboxTeleop, XboxTeleopConfig
from lerobot.utils.constants import ACTION, OBS_STR
from lerobot.utils.control_utils import init_keyboard_listener
from lerobot.utils.utils import log_say
from lerobot.utils.visualization_utils import init_rerun

# Configuration: Set to True to use leader arm, False for Xbox controller
USE_LEADER_ARM = True

NUM_EPISODES = 2
FPS = 30
EPISODE_TIME_SEC = 30
RESET_TIME_SEC = 10
TASK_DESCRIPTION = "My task description"
HF_REPO_ID = "<hf_username>/<dataset_repo_id>"

# Create the robot and teleoperator configurations
robot_config = LeKiwiClientConfig(remote_ip="172.18.134.136", id="lekiwi")
keyboard_config = KeyboardTeleopConfig(id="my_laptop_keyboard")

# Initialize based on chosen arm control method
if USE_LEADER_ARM:
    arm_teleop_config = SO100LeaderConfig(port="/dev/tty.usbmodem585A0077581", id="my_awesome_leader_arm")
    arm_teleop = SO100Leader(arm_teleop_config)
    arm_teleop_name = "Leader arm"
else:
    arm_teleop_config = XboxTeleopConfig(id="my_xbox_controller")
    arm_teleop = XboxTeleop(arm_teleop_config)
    arm_teleop_name = "Xbox controller"

# Initialize the robot and teleoperator
robot = LeKiwiClient(robot_config)
keyboard = KeyboardTeleop(keyboard_config)

# TODO(Steven): Update this example to use pipelines
teleop_action_processor, robot_action_processor, robot_observation_processor = make_default_processors()

# Configure the dataset features
action_features = hw_to_dataset_features(robot.action_features, ACTION)
obs_features = hw_to_dataset_features(robot.observation_features, OBS_STR)
dataset_features = {**action_features, **obs_features}

# Create the dataset
dataset = LeRobotDataset.create(
    repo_id=HF_REPO_ID,
    fps=FPS,
    features=dataset_features,
    robot_type=robot.name,
    use_videos=True,
    image_writer_threads=4,
)

# Connect the robot and teleoperators
# To connect you already should have this script running on LeKiwi:
# `python -m lerobot.robots.lekiwi.lekiwi_host --robot.id=my_awesome_kiwi`
robot.connect()
arm_teleop.connect()
keyboard.connect()

# Initialize the keyboard listener and rerun visualization
listener, events = init_keyboard_listener()
session_name = "lekiwi_record_leader_hybrid" if USE_LEADER_ARM else "lekiwi_record_xbox_hybrid"
init_rerun(session_name=session_name)

if not robot.is_connected or not arm_teleop.is_connected or not keyboard.is_connected:
    raise ValueError("Robot or teleoperators are not connected!")

print(f"Starting record loop with {arm_teleop_name} arm + Keyboard base...")
recorded_episodes = 0
while recorded_episodes < NUM_EPISODES and not events["stop_recording"]:
    log_say(f"Recording episode {recorded_episodes}")

    # Main record loop with both teleoperators
    record_loop(
        robot=robot,
        events=events,
        fps=FPS,
        dataset=dataset,
        teleop=[arm_teleop, keyboard],
        control_time_s=EPISODE_TIME_SEC,
        single_task=TASK_DESCRIPTION,
        display_data=True,
        teleop_action_processor=teleop_action_processor,
        robot_action_processor=robot_action_processor,
        robot_observation_processor=robot_observation_processor,
    )

    # Reset the environment if not stopping or re-recording
    if not events["stop_recording"] and (
        (recorded_episodes < NUM_EPISODES - 1) or events["rerecord_episode"]
    ):
        log_say("Reset the environment")
        record_loop(
            robot=robot,
            events=events,
            fps=FPS,
            teleop=[arm_teleop, keyboard],
            control_time_s=RESET_TIME_SEC,
            single_task=TASK_DESCRIPTION,
            display_data=True,
            teleop_action_processor=teleop_action_processor,
            robot_action_processor=robot_action_processor,
            robot_observation_processor=robot_observation_processor,
        )

    if events["rerecord_episode"]:
        log_say("Re-record episode")
        events["rerecord_episode"] = False
        events["exit_early"] = False
        dataset.clear_episode_buffer()
        continue

    # Save episode
    dataset.save_episode()
    recorded_episodes += 1

# Clean up
log_say("Stop recording")
robot.disconnect()
arm_teleop.disconnect()
keyboard.disconnect()
listener.stop()

dataset.finalize()
dataset.push_to_hub()
