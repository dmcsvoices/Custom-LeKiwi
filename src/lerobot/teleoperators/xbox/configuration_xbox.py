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

from dataclasses import dataclass

from ..config import TeleoperatorConfig


@dataclass
class XboxTeleopConfig(TeleoperatorConfig):
    """Configuration for Xbox controller teleoperation."""

    name: str = "xbox"
    type: str = "xbox"

    # Controller settings
    deadzone: float = 0.1  # Ignore stick values below this threshold (prevents drift)
    use_gripper: bool = True  # Enable gripper control

    # Base movement velocities
    base_linear_vel: float = 0.3  # m/s - base translation speed
    base_angular_vel: float = 90.0  # deg/s - base rotation speed

    # Arm movement increments (applied per control loop)
    arm_speed: float = 0.05  # radians per control loop for joint movements
    gripper_speed: float = 0.05  # gripper command increment

    # Stick scaling for proportional control
    stick_scale: float = 1.0  # Scale factor for stick deflection
