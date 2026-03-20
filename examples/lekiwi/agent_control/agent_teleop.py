#!/usr/bin/env python
"""AgentTeleop: Teleoperator interface for AI agents to control LeKiwi robot.

This module provides a teleoperator implementation that allows AI agents to send
high-level commands to the LeKiwi mobile manipulator robot. It handles command
queuing, safety limits, inactivity timeouts, and thread-safe operation.

Example:
    >>> from agent_control.agent_teleop import AgentTeleop, AgentTeleopConfig
    >>> config = AgentTeleopConfig(id="my_agent")
    >>> teleop = AgentTeleop(config)
    >>> teleop.connect()
    >>> teleop.queue_base_command(x_vel=0.2, duration=1.0)
    >>> action = teleop.get_action()  # Called by control loop at 30 FPS
"""

import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import numpy as np
from lerobot.teleoperators.teleoperator import Teleoperator
from lerobot.teleoperators.config import TeleoperatorConfig
from lerobot.teleoperators.utils import TeleopEvents
from lerobot.utils.errors import DeviceAlreadyConnectedError, DeviceNotConnectedError


@dataclass(kw_only=True)
class AgentTeleopConfig(TeleoperatorConfig):
    """Configuration for AgentTeleop.
    
    Attributes:
        id: Unique identifier for this teleoperator instance (inherited).
        calibration_dir: Directory for calibration files (inherited).
        default_arm_speed: Default speed for arm movements in rad/s.
        default_base_linear_speed: Default linear speed for base in m/s.
        default_base_angular_speed: Default angular speed for base in deg/s.
        max_arm_velocity: Maximum allowed arm joint velocity in rad/s.
        max_base_linear_vel: Maximum allowed base linear velocity in m/s.
        max_base_angular_vel: Maximum allowed base angular velocity in deg/s.
        inactivity_timeout_s: Timeout in seconds after which the robot auto-stops.
    """
    # Motion parameters
    default_arm_speed: float = 0.5  # rad/s
    default_base_linear_speed: float = 0.2  # m/s
    default_base_angular_speed: float = 45.0  # deg/s
    
    # Safety limits
    max_arm_velocity: float = 2.0  # rad/s
    max_base_linear_vel: float = 0.5  # m/s
    max_base_angular_vel: float = 90.0  # deg/s
    
    # Inactivity timeout
    inactivity_timeout_s: float = 5.0


class AgentCommand:
    """Represents a single robot command in the command queue.
    
    This class encapsulates a command with its target values, duration,
    and execution state. Commands are processed by the AgentTeleop in
    a first-in-first-out manner.
    
    Attributes:
        action_type: Type of command - "base" for base movement or "arm" for arm movement.
        target_values: Dictionary mapping action keys to target values.
        duration: Optional duration in seconds for timed commands.
        start_time: Timestamp when command execution started (set internally).
        completed: Flag indicating if command has been completed.
    """
    
    def __init__(
        self,
        action_type: str,
        target_values: Dict[str, float],
        duration: Optional[float] = None,
    ):
        """Initialize an AgentCommand.
        
        Args:
            action_type: Type of action ("base" or "arm").
            target_values: Dictionary of target values for the action.
            duration: Optional duration for the command in seconds.
        """
        self.action_type = action_type
        self.target_values = target_values
        self.duration = duration
        self.start_time: Optional[float] = None
        self.completed = False


class AgentTeleop(Teleoperator):
    """Teleoperator that receives commands from an AI agent.
    
    This teleoperator provides an interface for AI agents to control the LeKiwi
    robot. It implements the standard LeRobot Teleoperator interface while adding
    agent-specific features like command queuing, safety limits, and inactivity
    timeouts.
    
    The teleoperator maintains a command queue that is processed in the get_action()
    method, which is called by the control loop at the configured frame rate (30 FPS).
    
    Thread Safety:
        All public methods use threading.Lock() to ensure thread-safe operation
        between the agent thread (queuing commands) and the control loop thread
        (processing commands).
    
    Safety Features:
        - Velocity clamping to configured maximums
        - Inactivity timeout that stops the robot if no commands are received
        - Emergency stop functionality
    
    Attributes:
        config: AgentTeleopConfig instance with configuration parameters.
        config_class: Dataclass used for configuration.
        name: Identifier for this teleoperator type.
    
    Example:
        >>> config = AgentTeleopConfig(max_base_linear_vel=0.3)
        >>> teleop = AgentTeleop(config)
        >>> teleop.connect()
        >>> teleop.queue_base_command(x_vel=0.2, duration=2.0)
        >>> teleop.set_gripper(0.5)
    """
    
    config_class = AgentTeleopConfig
    name = "agent"
    
    def __init__(self, config: AgentTeleopConfig):
        """Initialize the AgentTeleop instance.
        
        Args:
            config: Configuration object with teleoperator parameters.
        """
        super().__init__(config)
        self.config = config
        
        self._is_connected = False
        self._current_action = self._get_zero_action()
        self._command_queue: List[AgentCommand] = []
        self._active_command: Optional[AgentCommand] = None
        self._latest_observation: Optional[Dict[str, Any]] = None
        self._lock = threading.Lock()
        self._last_command_time = time.time()
    
    @property
    def is_connected(self) -> bool:
        """Check if the teleoperator is connected.
        
        Returns:
            True if connected, False otherwise.
        """
        return self._is_connected
    
    @property
    def is_calibrated(self) -> bool:
        """Check if the teleoperator is calibrated.
        
        Returns:
            Always True for AgentTeleop as no calibration is required.
        """
        return True
    
    def connect(self) -> None:
        """Connect the teleoperator.
        
        Raises:
            DeviceAlreadyConnectedError: If already connected.
        """
        if self._is_connected:
            raise DeviceAlreadyConnectedError("AgentTeleop already connected")
        self._is_connected = True
        self._last_command_time = time.time()
    
    def disconnect(self) -> None:
        """Disconnect the teleoperator and reset state.
        
        Clears the command queue and resets the current action to zero.
        
        Raises:
            DeviceNotConnectedError: If not connected.
        """
        if not self._is_connected:
            raise DeviceNotConnectedError("AgentTeleop not connected")
        self._is_connected = False
        self._current_action = self._get_zero_action()
        self._command_queue.clear()
    
    def calibrate(self) -> None:
        """Calibrate the teleoperator.
        
        No-op for AgentTeleop as no calibration is required.
        """
        pass
    
    def configure(self) -> None:
        """Configure the teleoperator.
        
        No-op for AgentTeleop as configuration is done via config object.
        """
        pass
    
    @property
    def action_features(self) -> Dict[str, type]:
        """Get the action feature specifications.
        
        Returns:
            Dictionary mapping action keys to their expected types.
        """
        return {
            "arm_shoulder_pan.pos": float,
            "arm_shoulder_lift.pos": float,
            "arm_elbow_flex.pos": float,
            "arm_wrist_flex.pos": float,
            "arm_wrist_roll.pos": float,
            "arm_gripper.pos": float,
            "x.vel": float,
            "y.vel": float,
            "theta.vel": float,
        }
    
    @property
    def feedback_features(self) -> Dict:
        """Get the feedback feature specifications.
        
        Returns:
            Empty dictionary as AgentTeleop does not use feedback features.
        """
        return {}
    
    def get_action(self) -> Dict[str, float]:
        """Get the current action to be sent to the robot.
        
        This method is called by the control loop at the configured frame rate
        (typically 30 FPS). It processes the command queue and applies any
        active commands to the current action.
        
        Also implements inactivity timeout - if no commands have been received
        for longer than inactivity_timeout_s, base velocities are set to zero
        as a safety measure.
        
        Returns:
            Dictionary mapping action keys to their current values.
            
        Raises:
            DeviceNotConnectedError: If not connected.
        """
        if not self._is_connected:
            raise DeviceNotConnectedError("AgentTeleop not connected")
        
        with self._lock:
            self._process_command_queue()
            
            # Auto-stop on inactivity
            if time.time() - self._last_command_time > self.config.inactivity_timeout_s:
                self._current_action["x.vel"] = 0.0
                self._current_action["y.vel"] = 0.0
                self._current_action["theta.vel"] = 0.0
            
            return self._current_action.copy()
    
    def send_feedback(self, feedback: Dict[str, Any]) -> None:
        """Send feedback to the teleoperator.
        
        No-op for AgentTeleop as feedback is not used.
        
        Args:
            feedback: Feedback dictionary from the robot.
        """
        pass
    
    def get_teleop_events(self) -> Dict[str, Any]:
        """Get teleoperation events.
        
        Returns:
            Dictionary of teleoperation event flags.
        """
        return {
            TeleopEvents.IS_INTERVENTION: False,
            TeleopEvents.TERMINATE_EPISODE: False,
            TeleopEvents.SUCCESS: False,
            TeleopEvents.RERECORD_EPISODE: False,
        }
    
    # Agent-facing API
    
    def queue_base_command(
        self,
        x_vel: float = 0.0,
        y_vel: float = 0.0,
        theta_vel: float = 0.0,
        duration: Optional[float] = None,
    ) -> None:
        """Queue a base movement command.
        
        Queues a velocity command for the robot's mobile base. Velocities are
        automatically clamped to the configured safety limits.
        
        Args:
            x_vel: Forward/backward velocity in m/s (positive = forward).
            y_vel: Left/right strafing velocity in m/s (positive = left).
            theta_vel: Rotational velocity in deg/s (positive = CCW).
            duration: Optional duration in seconds. If set, velocities will be
                     applied for this duration and then set to zero.
        """
        with self._lock:
            cmd = AgentCommand(
                action_type="base",
                target_values={
                    "x.vel": np.clip(x_vel, -self.config.max_base_linear_vel, self.config.max_base_linear_vel),
                    "y.vel": np.clip(y_vel, -self.config.max_base_linear_vel, self.config.max_base_linear_vel),
                    "theta.vel": np.clip(theta_vel, -self.config.max_base_angular_vel, self.config.max_base_angular_vel),
                },
                duration=duration,
            )
            self._command_queue.append(cmd)
            self._last_command_time = time.time()
    
    def queue_arm_command(
        self,
        shoulder_pan: Optional[float] = None,
        shoulder_lift: Optional[float] = None,
        elbow_flex: Optional[float] = None,
        wrist_flex: Optional[float] = None,
        wrist_roll: Optional[float] = None,
        duration: Optional[float] = None,
    ) -> None:
        """Queue an arm position command.
        
        Queues a position command for one or more arm joints. Only specified
        joints will be updated; unspecified joints maintain their current values.
        
        Args:
            shoulder_pan: Target position for shoulder pan joint in radians.
            shoulder_lift: Target position for shoulder lift joint in radians.
            elbow_flex: Target position for elbow flex joint in radians.
            wrist_flex: Target position for wrist flex joint in radians.
            wrist_roll: Target position for wrist roll joint in radians.
            duration: Optional duration in seconds for the movement.
        """
        with self._lock:
            targets = {}
            if shoulder_pan is not None:
                targets["arm_shoulder_pan.pos"] = shoulder_pan
            if shoulder_lift is not None:
                targets["arm_shoulder_lift.pos"] = shoulder_lift
            if elbow_flex is not None:
                targets["arm_elbow_flex.pos"] = elbow_flex
            if wrist_flex is not None:
                targets["arm_wrist_flex.pos"] = wrist_flex
            if wrist_roll is not None:
                targets["arm_wrist_roll.pos"] = wrist_roll
            
            cmd = AgentCommand(action_type="arm", target_values=targets, duration=duration)
            self._command_queue.append(cmd)
            self._last_command_time = time.time()
    
    def set_gripper(self, position: float) -> None:
        """Set gripper position immediately.
        
        Unlike queued commands, this sets the gripper position immediately
        without queuing. The position is clamped to [-1.0, 1.0].
        
        Args:
            position: Gripper position from -1.0 (closed) to 1.0 (open).
        """
        with self._lock:
            self._current_action["arm_gripper.pos"] = np.clip(position, -1.0, 1.0)
            self._last_command_time = time.time()
    
    def stop(self) -> None:
        """Emergency stop.
        
        Immediately stops all robot motion by:
        - Setting all action values to zero
        - Clearing the command queue
        - Canceling any active command
        - Resetting the last command time
        
        Use this for emergency situations where immediate stop is required.
        """
        with self._lock:
            self._current_action = self._get_zero_action()
            self._command_queue.clear()
            self._active_command = None
            self._last_command_time = time.time()
    
    def update_observation(self, observation: Dict[str, Any]) -> None:
        """Update cached observation.
        
        Stores the latest observation from the robot for retrieval by the agent.
        
        Args:
            observation: Dictionary containing observation data from the robot.
        """
        with self._lock:
            self._latest_observation = observation.copy()
    
    def get_cached_observation(self) -> Optional[Dict[str, Any]]:
        """Get latest cached observation.
        
        Returns:
            Copy of the latest observation, or None if no observation has been
            received since connection.
        """
        with self._lock:
            return self._latest_observation.copy() if self._latest_observation else None
    
    def is_idle(self) -> bool:
        """Check if the teleoperator is idle.
        
        Returns True if no commands are queued and no command is currently
        being executed.
        
        Returns:
            True if idle, False if commands are pending or active.
        """
        with self._lock:
            return len(self._command_queue) == 0 and self._active_command is None
    
    def wait_for_idle(self, timeout: Optional[float] = None) -> bool:
        """Block until all commands are completed.
        
        Polls the is_idle() method until it returns True or the timeout is reached.
        Uses a 10ms sleep between polls to avoid busy-waiting.
        
        Args:
            timeout: Maximum time to wait in seconds. If None, waits indefinitely.
            
        Returns:
            True if all commands completed before timeout, False if timeout occurred.
        """
        start_time = time.time()
        while not self.is_idle():
            if timeout and (time.time() - start_time) > timeout:
                return False
            time.sleep(0.01)
        return True
    
    # Internal methods
    
    def _get_zero_action(self) -> Dict[str, float]:
        """Return an action dict with base velocities zeroed.
        
        Arm joints are NOT included by default to avoid unexpected movement.
        Only base velocities are zeroed. Arm commands must be explicitly queued.
        
        Returns:
            Dictionary with base velocity keys set to 0.0.
        """
        return {
            # Base velocities only - arm joints omitted to prevent
            # automatic movement to zero position on connect
            "x.vel": 0.0,
            "y.vel": 0.0,
            "theta.vel": 0.0,
        }
    
    def _process_command_queue(self) -> None:
        """Process the command queue.
        
        Internal method that manages command execution state. Called by
        get_action() within the lock context. Handles:
        - Starting new commands from the queue
        - Tracking command duration
        - Marking commands as completed
        - Zeroing velocities when timed base commands complete
        """
        current_time = time.time()
        
        # Check active command
        if self._active_command:
            cmd = self._active_command
            if cmd.start_time is None:
                cmd.start_time = current_time
            
            elapsed = current_time - cmd.start_time
            
            if cmd.duration is not None and elapsed >= cmd.duration:
                # Command completed
                cmd.completed = True
                self._active_command = None
                # Zero velocities for base commands
                if cmd.action_type == "base":
                    self._current_action["x.vel"] = 0.0
                    self._current_action["y.vel"] = 0.0
                    self._current_action["theta.vel"] = 0.0
            else:
                # Apply command values
                self._current_action.update(cmd.target_values)
        
        # Start next command if available
        if not self._active_command and self._command_queue:
            self._active_command = self._command_queue.pop(0)
            self._active_command.start_time = current_time
