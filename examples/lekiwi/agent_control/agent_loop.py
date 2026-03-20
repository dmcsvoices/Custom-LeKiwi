#!/usr/bin/env python
"""AgentLoop: Control loop connecting AI agent to LeKiwi robot.

This module provides the LeKiwiAgentLoop class which manages the connection
between an AI agent and the LeKiwi robot hardware. It handles the main control
loop that runs at a specified FPS, fetching observations and sending actions.
"""

import threading
import time
from typing import Optional, Callable

from lerobot.robots.lekiwi import LeKiwiClient, LeKiwiClientConfig
from lerobot.utils.robot_utils import busy_wait
from lerobot.utils.visualization_utils import init_rerun, log_rerun_data

from .agent_teleop import AgentTeleop, AgentTeleopConfig


class LeKiwiAgentLoop:
    """Control loop that connects an AI agent to the LeKiwi robot.

    This class manages the connection between an AI agent teleoperator and the
    physical LeKiwi robot. It runs a background control loop at a specified FPS
    that continuously:
    1. Fetches observations from the robot (camera images, joint states)
    2. Updates the agent teleoperator with the latest observation
    3. Gets the action from the agent teleoperator
    4. Sends the action to the robot
    5. Handles visualization and optional observation callbacks

    Attributes:
        robot_ip: IP address of the LeKiwi robot host.
        fps: Target control loop frequency in frames per second.
        enable_visualization: Whether to enable rerun visualization.
        on_observation: Optional callback function for observations.
        robot: The LeKiwiClient instance for robot communication.
        agent_teleop: The AgentTeleop instance for agent interaction.
    """

    def __init__(
        self,
        robot_ip: str = "localhost",
        fps: int = 30,
        enable_visualization: bool = True,
        on_observation: Optional[Callable] = None,
    ):
        """Initialize the LeKiwiAgentLoop.

        Args:
            robot_ip: IP address of the robot host. Defaults to "localhost".
            fps: Control loop frequency in Hz. Defaults to 30.
            enable_visualization: Enable rerun visualization. Defaults to True.
            on_observation: Optional callback function called with each observation.
        """
        self.robot_ip = robot_ip
        self.fps = fps
        self.enable_visualization = enable_visualization
        self.on_observation = on_observation

        self.robot: Optional[LeKiwiClient] = None
        self.agent_teleop: Optional[AgentTeleop] = None

        self._control_thread: Optional[threading.Thread] = None
        self._running = False

    def start(self) -> None:
        """Connect to robot and start the control loop.

        This method:
        1. Creates and configures a LeKiwiClient
        2. Connects to the robot
        3. Creates and connects an AgentTeleop instance
        4. Initializes visualization if enabled
        5. Starts the background control thread

        Raises:
            RuntimeError: If the agent loop is already running.
            ConnectionError: If connection to the robot fails.
        """
        if self._running:
            raise RuntimeError("Agent loop is already running")

        # Create and connect robot
        robot_config = LeKiwiClientConfig(remote_ip=self.robot_ip, id="lekiwi_agent")
        self.robot = LeKiwiClient(robot_config)

        print(f"Connecting to robot at {self.robot_ip}...")
        self.robot.connect()

        if not self.robot.is_connected:
            raise ConnectionError("Failed to connect to robot")
        print("✓ Connected to robot")

        # Create agent teleoperator
        teleop_config = AgentTeleopConfig(id="ai_agent")
        self.agent_teleop = AgentTeleop(teleop_config)
        self.agent_teleop.connect()
        print("✓ Agent teleoperator ready")

        # Initialize visualization
        if self.enable_visualization:
            init_rerun(session_name="lekiwi_agent")

        # Start control loop
        self._running = True
        self._control_thread = threading.Thread(target=self._control_loop, daemon=True)
        self._control_thread.start()
        print("✓ Control loop started")

    def stop(self) -> None:
        """Stop the control loop and disconnect from robot.

        This method:
        1. Stops the control loop
        2. Waits for the control thread to finish
        3. Sends a zero action to stop the robot
        4. Disconnects from the robot
        5. Disconnects the agent teleoperator
        """
        if not self._running:
            return

        print("\nStopping agent loop...")
        self._running = False

        if self._control_thread:
            self._control_thread.join(timeout=2.0)

        # Send stop command
        if self.robot and self.robot.is_connected:
            stop_action = self._get_zero_action()
            self.robot.send_action(stop_action)
            self.robot.disconnect()

        if self.agent_teleop:
            self.agent_teleop.disconnect()

        print("✓ Agent loop stopped")

    def _control_loop(self) -> None:
        """Main control loop running in background thread.

        This method runs continuously at the specified FPS until stopped.
        For each iteration:
        1. Gets observation from robot
        2. Updates teleop with observation
        3. Gets action from teleop
        4. Sends action to robot
        5. Handles visualization and callbacks

        Errors are caught and logged without stopping the loop.
        """
        while self._running:
            t0 = time.perf_counter()

            try:
                # Get observation
                observation = self.robot.get_observation()

                # Update teleoperator
                self.agent_teleop.update_observation(observation)

                # Get action
                action = self.agent_teleop.get_action()

                # Send action
                self.robot.send_action(action)

                # Visualization
                if self.enable_visualization:
                    log_rerun_data(observation=observation, action=action)

                # Callback
                if self.on_observation:
                    self.on_observation(observation)

            except Exception as e:
                print(f"Control loop error: {e}")
                if not self._running:
                    break

            # Maintain loop frequency
            busy_wait(max(1.0 / self.fps - (time.perf_counter() - t0), 0.0))

    def _get_zero_action(self) -> dict:
        """Return a zero action dictionary.

        Returns:
            Dictionary with all action keys set to 0.0.
        """
        return {
            "arm_shoulder_pan.pos": 0.0,
            "arm_shoulder_lift.pos": 0.0,
            "arm_elbow_flex.pos": 0.0,
            "arm_wrist_flex.pos": 0.0,
            "arm_wrist_roll.pos": 0.0,
            "arm_gripper.pos": 0.0,
            "x.vel": 0.0,
            "y.vel": 0.0,
            "theta.vel": 0.0,
        }
