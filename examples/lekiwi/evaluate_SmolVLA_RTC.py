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
SmolVLA Evaluation Script with RTC (Real-Time Chunking) Support

RTC enables smooth, continuous, and reactive motion for flow-matching based policies
like SmolVLA by asynchronously generating action chunks and guiding new chunks to
align smoothly with previously executed actions.

Key benefits:
- No pauses or jerky transitions between chunks
- Smoother robot motion during high-latency inference
- Better reactivity to environment changes

For more information, see: https://huggingface.co/docs/lerobot/rtc
"""

from lerobot.configs.types import RTCAttentionSchedule
from lerobot.datasets.lerobot_dataset import LeRobotDataset
from lerobot.datasets.utils import hw_to_dataset_features
from lerobot.policies.factory import make_pre_post_processors
from lerobot.policies.rtc.configuration_rtc import RTCConfig
from lerobot.policies.smolvla.modeling_smolvla import SmolVLAPolicy
from lerobot.processor import make_default_processors
from lerobot.robots.lekiwi import LeKiwiClient, LeKiwiClientConfig
from lerobot.scripts.lerobot_record import record_loop
from lerobot.utils.constants import ACTION, OBS_STR
from lerobot.utils.control_utils import init_keyboard_listener
from lerobot.utils.utils import log_say
from lerobot.utils.visualization_utils import init_rerun

# ============================================================================
# CONFIGURATION
# ============================================================================

NUM_EPISODES = 5
FPS = 30
EPISODE_TIME_SEC = 180
TASK_DESCRIPTION = "Pick up the yellow toy and put it in the white bowl"
HF_MODEL_ID = "fruityapplebottom/SmolVLA_PickNPlace_YellowDuck"
HF_DATASET_ID = "fruityapplebottom/EVAL_SmolVLA_PnP_YellowDuck_RTC3"

# RTC Configuration Parameters
# See: https://huggingface.co/docs/lerobot/rtc#key-parameters
RTC_ENABLED = True
RTC_EXECUTION_HORIZON = 10  # How many steps to blend with previous chunk (8-12 recommended)
RTC_MAX_GUIDANCE_WEIGHT = 10.0  # How strongly to enforce consistency (10.0 recommended for 10-step flow matching)
RTC_PREFIX_ATTENTION_SCHEDULE = RTCAttentionSchedule.EXP  # Exponential blend (recommended)
RTC_DEBUG = False  # Set to True for debug visualizations
RTC_DEBUG_MAXLEN = 100  # Maximum number of debug entries to store

# Inference delay (timesteps of latency) - should be measured from actual inference time
# This will be calculated dynamically based on policy inference latency
RTC_INFERENCE_DELAY = 4

# ============================================================================
# SETUP
# ============================================================================

# Create the robot configuration & robot
robot_config = LeKiwiClientConfig(remote_ip="192.168.8.157", id="my_lekiwi")
robot = LeKiwiClient(robot_config)

# Create RTC configuration
rtc_config = RTCConfig(
    enabled=RTC_ENABLED,
    execution_horizon=RTC_EXECUTION_HORIZON,
    max_guidance_weight=RTC_MAX_GUIDANCE_WEIGHT,
    prefix_attention_schedule=RTC_PREFIX_ATTENTION_SCHEDULE,
    debug=RTC_DEBUG,
    debug_maxlen=RTC_DEBUG_MAXLEN,
)

# Load SmolVLA policy with RTC configuration
# Note: RTC must be configured BEFORE loading the pretrained model
policy = SmolVLAPolicy.from_pretrained(HF_MODEL_ID)

# Apply RTC configuration to the loaded policy
policy.config.rtc_config = rtc_config

log_say(f"SmolVLA Policy loaded with RTC {'ENABLED' if RTC_ENABLED else 'DISABLED'}")
if RTC_ENABLED:
    log_say(f"RTC Config - Execution Horizon: {RTC_EXECUTION_HORIZON}, "
            f"Max Guidance Weight: {RTC_MAX_GUIDANCE_WEIGHT}, "
            f"Schedule: {RTC_PREFIX_ATTENTION_SCHEDULE.value}")

# Configure the dataset features
action_features = hw_to_dataset_features(robot.action_features, ACTION)
obs_features = hw_to_dataset_features(robot.observation_features, OBS_STR)
dataset_features = {**action_features, **obs_features}

# Create the dataset
dataset = LeRobotDataset.create(
    repo_id=HF_DATASET_ID,
    fps=FPS,
    features=dataset_features,
    robot_type=robot.name,
    use_videos=True,
    image_writer_threads=4,
)

# Build Policy Processors
preprocessor, postprocessor = make_pre_post_processors(
    policy_cfg=policy,
    pretrained_path=HF_MODEL_ID,
    dataset_stats=dataset.meta.stats,
    # The inference device is automatically set to match the detected hardware
    preprocessor_overrides={"device_processor": {"device": str(policy.config.device)}},
)

# Connect the robot
# To connect you already should have this script running on LeKiwi:
# `python -m lerobot.robots.lekiwi.lekiwi_host --robot.id=my_awesome_kiwi`
robot.connect()

# Create default processors
teleop_action_processor, robot_action_processor, robot_observation_processor = make_default_processors()

# Initialize the keyboard listener and rerun visualization
listener, events = init_keyboard_listener()
init_rerun(session_name="lekiwi_evaluate_rtc")

if not robot.is_connected:
    raise ValueError("Robot is not connected!")

# ============================================================================
# EVALUATION LOOP
# ============================================================================

print("Starting evaluate loop with RTC...")
print("="*60)
print("RTC helps SmolVLA produce smooth, continuous motion by:")
print("  1. Asynchronously generating action chunks")
print("  2. Blending new chunks with executed portions of previous chunks")
print("  3. Eliminating pauses and jerky transitions")
print("="*60)

recorded_episodes = 0
while recorded_episodes < NUM_EPISODES and not events["stop_recording"]:
    log_say(f"Running inference with RTC, recording eval episode {recorded_episodes} of {NUM_EPISODES}")

    # Main record loop
    # Note: The record_loop function should handle RTC-enabled policies automatically
    # by calling predict_action_chunk with appropriate parameters
    record_loop(
        robot=robot,
        events=events,
        fps=FPS,
        policy=policy,
        preprocessor=preprocessor,
        postprocessor=postprocessor,
        dataset=dataset,
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
            control_time_s=EPISODE_TIME_SEC,
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

    # Print RTC debug info if enabled
    if RTC_DEBUG and hasattr(policy, 'rtc_processor'):
        debug_data = policy.rtc_processor.get_debug_data()
        log_say(f"RTC Debug: Collected {len(debug_data)} debug entries")

# ============================================================================
# CLEANUP
# ============================================================================

log_say("Stop recording")
robot.disconnect()
listener.stop()

dataset.finalize()
dataset.push_to_hub()

log_say("Evaluation complete! Dataset pushed to hub.")
if RTC_ENABLED:
    log_say("RTC-enabled evaluation should show smoother motion compared to standard inference.")
