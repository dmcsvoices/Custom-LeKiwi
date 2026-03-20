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

import sys
from typing import Any

import numpy as np

from lerobot.utils.errors import DeviceAlreadyConnectedError, DeviceNotConnectedError

from ..teleoperator import Teleoperator
from ..utils import TeleopEvents
from .configuration_xbox import XboxTeleopConfig


class XboxTeleop(Teleoperator):
    """
    Teleop class to use Xbox controller inputs for arm and base control.

    Controller Mapping:
        Left Stick:
            - X-axis: Base strafe (left/right movement)
            - Y-axis: (Inactive in hybrid mode - arm controlled by leader)

        Right Stick (Base Control):
            - X-axis: Base rotation (left/right)
            - Y-axis: Base forward/backward movement

        D-Pad (Arm Control):
            - Left/Right: Arm shoulder pan (left/right)
            - Up/Down: Arm shoulder lift (up/down)

        Analog Triggers:
            - LT: Gripper decrease (proportional)
            - RT: Gripper increase (proportional)

        Stick Press & Shoulder Buttons:
            - LS: Left stick press to control elbow flex (proportional, via left stick X)
            - RS: (Not used in hybrid mode)
            - RB: Speed multiplier (2x arm speed)

        Face Buttons:
            - A: (Reserved)
            - B: Emergency stop
            - X: (Reserved)
            - Y: (Reserved)

        Menu Buttons:
            - Back: Quit teleoperation
            - Start: Reset arm to home position

    Note: In hybrid mode (teleoperate_xbox_hybrid.py), arm control outputs are
          ignored since the leader arm handles all arm movements. Only base
          velocity commands (x.vel, y.vel, theta.vel) are used.
    """

    config_class = XboxTeleopConfig
    name = "xbox"

    def __init__(self, config: XboxTeleopConfig):
        super().__init__(config)
        self.config = config
        self.robot_type = config.type

        self.controller = None
        self.pygame = None
        self._is_connected = False

        # Arm state tracking - initialize to None, will be set from robot observation
        self.arm_positions = {
            "arm_shoulder_pan": None,
            "arm_shoulder_lift": None,
            "arm_elbow_flex": None,
            "arm_wrist_flex": None,
            "arm_wrist_roll": None,
            "arm_gripper": None,
        }
        self.initialized = False

        # Base velocity state
        self.base_velocities = {
            "x.vel": 0.0,
            "y.vel": 0.0,
            "theta.vel": 0.0,
        }

        # Speed multiplier for arm movements
        self.arm_speed_multiplier = 1.0

    @property
    def action_features(self) -> dict:
        """Define the action output structure for arm and base control."""
        features = {
            "dtype": "float32",
            "shape": (
                11,
            ),  # 6 arm joints + 3 base velocities + 2 extra
            "names": {
                "arm_shoulder_pan": 0,
                "arm_shoulder_lift": 1,
                "arm_elbow_flex": 2,
                "arm_wrist_flex": 3,
                "arm_wrist_roll": 4,
                "arm_gripper": 5,
                "x.vel": 6,
                "y.vel": 7,
                "theta.vel": 8,
            },
        }
        return features

    @property
    def feedback_features(self) -> dict:
        return {}

    @property
    def is_connected(self) -> bool:
        return self._is_connected and self.controller is not None

    @property
    def is_calibrated(self) -> bool:
        """Xbox controller doesn't require calibration."""
        return True

    def connect(self) -> None:
        """Initialize and connect to Xbox controller using PyGame."""
        if self.is_connected:
            raise DeviceAlreadyConnectedError(
                "Xbox controller is already connected. Do not run `connect()` twice."
            )

        try:
            import pygame

            self.pygame = pygame
        except ImportError:
            raise ImportError(
                "pygame is required for Xbox controller support. "
                "Please install it with: pip install pygame"
            )

        # Initialize pygame joystick module
        self.pygame.init()
        self.pygame.joystick.init()

        # Wait for and detect Xbox controller
        if self.pygame.joystick.get_count() == 0:
            raise RuntimeError(
                "No Xbox controller detected. Please connect your Xbox controller."
            )

        self.controller = self.pygame.joystick.Joystick(0)
        self.controller.init()

        print(f"✓ Connected to: {self.controller.get_name()}")
        self._is_connected = True

    def disconnect(self) -> None:
        """Disconnect from Xbox controller."""
        if not self.is_connected:
            raise DeviceNotConnectedError(
                "Xbox controller is not connected. You need to run `connect()` before `disconnect()`."
            )

        self.controller = None
        self._is_connected = False
        if self.pygame:
            self.pygame.quit()

    def calibrate(self) -> None:
        """Xbox controller doesn't require calibration."""
        pass

    def configure(self) -> None:
        """No additional configuration needed for Xbox controller."""
        pass

    def get_action(self, observation: dict = None) -> dict[str, Any]:
        """
        Read Xbox controller input and convert to robot action commands.

        Returns:
            Dictionary with arm joint positions and base velocities.
        """
        if not self.is_connected:
            raise DeviceNotConnectedError(
                "Xbox controller is not connected. You need to run `connect()` before `get_action()`."
            )

        # Process PyGame events to update controller state
        for event in self.pygame.event.get():
            pass  # Just process events, state is read via axis/button queries

        # Read analog inputs (sticks and triggers)
        lx = self._apply_deadzone(self.controller.get_axis(0))  # Left stick X
        ly = self._apply_deadzone(self.controller.get_axis(1))  # Left stick Y
        rx = self._apply_deadzone(self.controller.get_axis(2))  # Right stick X
        ry = self._apply_deadzone(self.controller.get_axis(3))  # Right stick Y
        lt = self._apply_deadzone(max(0.0, self.controller.get_axis(4)))  # Left trigger (axis 4)
        rt = self._apply_deadzone(max(0.0, self.controller.get_axis(5)))  # Right trigger (axis 5)

        # Read D-Pad (hat)
        dpad_x, dpad_y = 0, 0
        if self.controller.get_numhats() > 0:
            dpad_x, dpad_y = self.controller.get_hat(0)

        # Read buttons
        buttons = {
            "A": self.controller.get_button(0),
            "B": self.controller.get_button(1),
            "X": self.controller.get_button(2),
            "Y": self.controller.get_button(3),
            "LB": self.controller.get_button(4),
            "RB": self.controller.get_button(5),
            "Back": self.controller.get_button(6),
            "Start": self.controller.get_button(7),
            "LS": self.controller.get_button(8),  # Left stick press
            "RS": self.controller.get_button(9),  # Right stick press
        }

        # ===== ARM CONTROL (Fixed initialization and limits) =====

        # Initialize arm positions from robot observation on first call
        if not self.initialized and observation is not None:
            print("Initializing arm positions from robot observation...")
            for joint in ["arm_shoulder_pan", "arm_shoulder_lift", "arm_elbow_flex",
                         "arm_wrist_flex", "arm_wrist_roll", "arm_gripper"]:
                key_with_suffix = f"{joint}.pos"
                if key_with_suffix in observation:
                    self.arm_positions[joint] = observation[key_with_suffix]
                    print(f"  {joint}: {observation[key_with_suffix]:.3f}")
                elif joint in observation:
                    self.arm_positions[joint] = observation[joint]
                    print(f"  {joint}: {observation[joint]:.3f}")
                else:
                    # Fallback to zero if not found
                    self.arm_positions[joint] = 0.0
                    print(f"  {joint}: 0.0 (fallback)")
            self.initialized = True
            print("Arm positions initialized!")

        # Skip control if not initialized yet
        if not self.initialized:
            return {
                "arm_shoulder_pan": 0.0,
                "arm_shoulder_lift": 0.0,
                "arm_elbow_flex": 0.0,
                "arm_wrist_flex": 0.0,
                "arm_wrist_roll": 0.0,
                "arm_gripper": 0.0,
                **self.base_velocities,
            }

        # Left stick controls wrist (roll and flex)
        arm_delta = {}
        arm_delta["arm_wrist_roll"] = lx * self.config.arm_speed * self.arm_speed_multiplier
        arm_delta["arm_wrist_flex"] = -ly * self.config.arm_speed * self.arm_speed_multiplier

        # D-Pad controls shoulder pan (left/right) and shoulder lift (up/down)
        arm_delta["arm_shoulder_pan"] = dpad_x * self.config.arm_speed * self.arm_speed_multiplier
        arm_delta["arm_shoulder_lift"] = dpad_y * self.config.arm_speed * self.arm_speed_multiplier

        # Elbow flex: Left stick X, but ONLY when LS (left stick press) is held
        if buttons["LS"]:
            arm_delta["arm_elbow_flex"] = lx * self.config.arm_speed * self.arm_speed_multiplier
        else:
            arm_delta["arm_elbow_flex"] = 0.0

        # Gripper control: Analog triggers LT (decrease) and RT (increase)
        arm_delta["arm_gripper"] = (rt - lt) * self.config.gripper_speed

        # Update arm positions with much more generous limits
        for joint, delta in arm_delta.items():
            self.arm_positions[joint] += delta
            # Much more generous limits - most robot joints can move more than ±180°
            if joint == "arm_gripper":
                self.arm_positions[joint] = np.clip(
                    self.arm_positions[joint], -2.0, 2.0  # Expanded gripper range
                )
            else:
                self.arm_positions[joint] = np.clip(
                    self.arm_positions[joint], -2*np.pi, 2*np.pi  # ±720° instead of ±180°
                )

        # ===== BASE CONTROL =====
        # Left stick X controls strafe (y.vel) - left/right strafing
        self.base_velocities["y.vel"] = (
            -lx * self.config.base_linear_vel * self.config.stick_scale
        )

        # Right stick Y controls forward/backward movement (x.vel)
        self.base_velocities["x.vel"] = (
            -ry * self.config.base_linear_vel * self.config.stick_scale
        )

        # Right stick X controls rotation (theta.vel)
        self.base_velocities["theta.vel"] = (
            -rx * self.config.base_angular_vel * self.config.stick_scale
        )

        # Speed multiplier: RB = faster (always available)
        if buttons["RB"]:  # RB = faster
            self.arm_speed_multiplier = 2.0
        else:
            self.arm_speed_multiplier = 1.0

        # Build action dictionary
        action = {
            **self.arm_positions,
            **self.base_velocities,
        }

        return action

    def send_feedback(self, feedback: dict[str, Any]) -> None:
        """Xbox controller doesn't support feedback."""
        pass

    def get_teleop_events(self) -> dict[str, Any]:
        """
        Get control events from the Xbox controller.

        Returns:
            Dictionary containing teleop events like intervention, episode termination, etc.
        """
        if not self.is_connected:
            return {
                TeleopEvents.IS_INTERVENTION: False,
                TeleopEvents.TERMINATE_EPISODE: False,
                TeleopEvents.SUCCESS: False,
                TeleopEvents.RERECORD_EPISODE: False,
            }

        # Process PyGame events
        for event in self.pygame.event.get():
            pass

        # Read button states
        buttons = {
            "A": self.controller.get_button(0),
            "B": self.controller.get_button(1),
            "X": self.controller.get_button(2),
            "Y": self.controller.get_button(3),
            "LB": self.controller.get_button(4),
            "RB": self.controller.get_button(5),
            "Back": self.controller.get_button(6),
            "Start": self.controller.get_button(7),
        }

        # Back button = quit/terminate
        terminate_episode = buttons.get("Back", False)

        # B button = emergency stop (also terminate)
        is_intervention = buttons.get("B", False)
        if is_intervention:
            terminate_episode = True

        return {
            TeleopEvents.IS_INTERVENTION: is_intervention,
            TeleopEvents.TERMINATE_EPISODE: terminate_episode,
            TeleopEvents.SUCCESS: buttons.get("Start", False),  # Start = success
            TeleopEvents.RERECORD_EPISODE: buttons.get("X", False),  # X = rerecord
        }

    def _apply_deadzone(self, value: float) -> float:
        """
        Apply deadzone to analog stick input to prevent drift.

        This ensures that untouched sticks (which may have slight electrical noise)
        return exactly 0.0, preventing unintended robot motion.
        """
        if abs(value) < self.config.deadzone:
            return 0.0
        # For values outside deadzone, scale to remove the deadzone offset
        # This provides more responsive control near the edges
        sign = 1.0 if value >= 0.0 else -1.0
        scaled_value = (abs(value) - self.config.deadzone) / (1.0 - self.config.deadzone)
        return sign * scaled_value
