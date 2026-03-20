#!/usr/bin/env python
"""AgentInterface: High-level API for AI agents to control LeKiwi robot.

This module provides a simplified interface for AI agents to control the LeKiwi
mobile manipulator robot. It wraps the lower-level AgentTeleop class and provides
convenience methods for base movement, arm control, and observations.

Example:
    from agent_control import LeKiwiAgentLoop, AgentInterface
    
    loop = LeKiwiAgentLoop(robot_ip="localhost")
    loop.start()
    
    agent = AgentInterface(loop.agent_teleop)
    agent.move_forward(0.5)
    agent.wait_for_completion()
    agent.home_arm()
"""

from typing import Any, Dict, Optional
import numpy as np
import time

from .agent_teleop import AgentTeleop


class AgentInterface:
    """High-level interface for AI agents to control LeKiwi robot.
    
    This class provides a user-friendly API for controlling the LeKiwi robot's
    mobile base and robotic arm. It handles unit conversions, command queuing,
    and provides convenience methods for common movements.
    
    Attributes:
        teleop: The AgentTeleop instance for low-level command queuing.
        default_linear_speed: Default speed for linear base movements (m/s).
        default_angular_speed: Default speed for angular base movements (deg/s).
        default_arm_speed: Default speed for arm joint movements (rad/s).
    
    Args:
        agent_teleop: The AgentTeleop instance to use for command queuing.
        default_linear_speed: Default linear speed in m/s. Defaults to 0.2.
        default_angular_speed: Default angular speed in deg/s. Defaults to 45.0.
        default_arm_speed: Default arm speed in rad/s. Defaults to 0.5.
    """
    
    def __init__(
        self,
        agent_teleop: AgentTeleop,
        default_linear_speed: float = 0.2,
        default_angular_speed: float = 45.0,
        default_arm_speed: float = 0.5,
    ):
        self.teleop = agent_teleop
        self.default_linear_speed = default_linear_speed
        self.default_angular_speed = default_angular_speed
        self.default_arm_speed = default_arm_speed
    
    # ==================== Base Movement Methods ====================
    
    def move_forward(self, distance_m: float, speed: Optional[float] = None) -> None:
        """Move the robot forward by a specified distance.
        
        Args:
            distance_m: Distance to move in meters. Positive for forward.
            speed: Linear speed in m/s. Uses default if not specified.
        """
        speed = speed or self.default_linear_speed
        duration = abs(distance_m) / speed
        direction = 1.0 if distance_m >= 0 else -1.0
        self.teleop.queue_base_command(x_vel=direction * speed, duration=duration)
    
    def move_backward(self, distance_m: float, speed: Optional[float] = None) -> None:
        """Move the robot backward by a specified distance.
        
        Args:
            distance_m: Distance to move in meters.
            speed: Linear speed in m/s. Uses default if not specified.
        """
        self.move_forward(-distance_m, speed)
    
    def strafe_left(self, distance_m: float, speed: Optional[float] = None) -> None:
        """Strafe (move sideways) left by a specified distance.
        
        Args:
            distance_m: Distance to strafe in meters.
            speed: Linear speed in m/s. Uses default if not specified.
        """
        speed = speed or self.default_linear_speed
        duration = abs(distance_m) / speed
        self.teleop.queue_base_command(y_vel=speed, duration=duration)
    
    def strafe_right(self, distance_m: float, speed: Optional[float] = None) -> None:
        """Strafe (move sideways) right by a specified distance.
        
        Args:
            distance_m: Distance to strafe in meters.
            speed: Linear speed in m/s. Uses default if not specified.
        """
        speed = speed or self.default_linear_speed
        duration = abs(distance_m) / speed
        self.teleop.queue_base_command(y_vel=-speed, duration=duration)
    
    def rotate(self, degrees: float, speed: Optional[float] = None) -> None:
        """Rotate the robot in place by a specified angle.
        
        Args:
            degrees: Angle to rotate in degrees. Positive is counter-clockwise.
            speed: Angular speed in deg/s. Uses default if not specified.
        """
        speed = speed or self.default_angular_speed
        duration = abs(degrees) / speed
        direction = 1.0 if degrees >= 0 else -1.0
        self.teleop.queue_base_command(theta_vel=direction * speed, duration=duration)
    
    def rotate_left(self, degrees: float, speed: Optional[float] = None) -> None:
        """Rotate left (counter-clockwise) by a specified angle.
        
        Args:
            degrees: Angle to rotate in degrees.
            speed: Angular speed in deg/s. Uses default if not specified.
        """
        self.rotate(degrees, speed)
    
    def rotate_right(self, degrees: float, speed: Optional[float] = None) -> None:
        """Rotate right (clockwise) by a specified angle.
        
        Args:
            degrees: Angle to rotate in degrees.
            speed: Angular speed in deg/s. Uses default if not specified.
        """
        self.rotate(-degrees, speed)
    
    def move_base(
        self,
        x_vel: float = 0.0,
        y_vel: float = 0.0,
        theta_vel: float = 0.0,
        duration: Optional[float] = None,
    ) -> None:
        """Direct velocity control of the robot base.
        
        This method provides low-level velocity control for holonomic movement.
        
        Args:
            x_vel: Forward velocity in m/s. Positive is forward.
            y_vel: Lateral velocity in m/s. Positive is left.
            theta_vel: Angular velocity in deg/s. Positive is CCW.
            duration: How long to apply the velocity command in seconds.
        """
        self.teleop.queue_base_command(x_vel, y_vel, theta_vel, duration)
    
    def stop_base(self) -> None:
        """Stop all base movement immediately."""
        self.teleop.queue_base_command(x_vel=0, y_vel=0, theta_vel=0, duration=0.1)
    
    # ==================== Arm Movement Methods ====================
    
    def move_arm_joint(
        self,
        joint_name: str,
        position_degrees: float,
        duration: Optional[float] = None,
    ) -> None:
        """Move a single arm joint to a specified position.
        
        Args:
            joint_name: Name of the joint to move. Valid names are:
                - "shoulder_pan": Base rotation of the arm
                - "shoulder_lift": Shoulder elevation
                - "elbow_flex": Elbow bend
                - "wrist_flex": Wrist up/down
                - "wrist_roll": Wrist rotation
            position_degrees: Target position in degrees.
            duration: Movement duration in seconds.
        
        Raises:
            ValueError: If joint_name is not recognized.
        """
        position_rad = np.radians(position_degrees)
        
        joint_map = {
            "shoulder_pan": "arm_shoulder_pan",
            "shoulder_lift": "arm_shoulder_lift",
            "elbow_flex": "arm_elbow_flex",
            "wrist_flex": "arm_wrist_flex",
            "wrist_roll": "arm_wrist_roll",
        }
        
        if joint_name not in joint_map:
            raise ValueError(f"Unknown joint: {joint_name}")
        
        kwargs = {joint_name: position_rad}
        self.teleop.queue_arm_command(**kwargs, duration=duration)
    
    def move_arm(
        self,
        shoulder_pan: Optional[float] = None,
        shoulder_lift: Optional[float] = None,
        elbow_flex: Optional[float] = None,
        wrist_flex: Optional[float] = None,
        wrist_roll: Optional[float] = None,
        duration: Optional[float] = None,
    ) -> None:
        """Move multiple arm joints simultaneously.
        
        All positions should be specified in radians. Only specified joints
        will be moved; others maintain their current positions.
        
        Args:
            shoulder_pan: Target position for shoulder pan joint (rad).
            shoulder_lift: Target position for shoulder lift joint (rad).
            elbow_flex: Target position for elbow flex joint (rad).
            wrist_flex: Target position for wrist flex joint (rad).
            wrist_roll: Target position for wrist roll joint (rad).
            duration: Movement duration in seconds.
        """
        self.teleop.queue_arm_command(
            shoulder_pan=shoulder_pan,
            shoulder_lift=shoulder_lift,
            elbow_flex=elbow_flex,
            wrist_flex=wrist_flex,
            wrist_roll=wrist_roll,
            duration=duration,
        )
    
    def set_gripper(self, position: float) -> None:
        """Set the gripper to a specific position.
        
        Args:
            position: Gripper position from -1.0 (fully closed) to 
                     1.0 (fully open).
        """
        self.teleop.set_gripper(position)
    
    def open_gripper(self) -> None:
        """Open the gripper fully."""
        self.set_gripper(1.0)
    
    def close_gripper(self) -> None:
        """Close the gripper fully."""
        self.set_gripper(-1.0)
    
    def home_arm(self) -> None:
        """Move the arm to its home (zero) position.
        
        This moves all joints to 0 radians with a 2-second duration.
        """
        self.move_arm(
            shoulder_pan=0.0,
            shoulder_lift=0.0,
            elbow_flex=0.0,
            wrist_flex=0.0,
            wrist_roll=0.0,
            duration=2.0,
        )
    
    # ==================== Observation Methods ====================
    
    def get_observation(self) -> Optional[Dict[str, Any]]:
        """Get the latest observation from the robot.
        
        Returns:
            Dictionary containing observation data including camera images
            and robot state, or None if no observation is available.
        """
        return self.teleop.get_cached_observation()
    
    def get_camera_image(self, camera_name: str = "front") -> Optional[np.ndarray]:
        """Get an image from a specific camera.
        
        Args:
            camera_name: Name of the camera (e.g., "front", "wrist").
        
        Returns:
            Numpy array containing the camera image, or None if not available.
        """
        obs = self.get_observation()
        if obs and camera_name in obs:
            return obs[camera_name]
        return None
    
    def get_robot_state(self) -> Dict[str, float]:
        """Get the current state of the robot.
        
        Returns:
            Dictionary containing joint positions and base velocities.
        """
        obs = self.get_observation()
        if not obs:
            return {}
        
        return {
            "shoulder_pan": obs.get("arm_shoulder_pan.pos", 0.0),
            "shoulder_lift": obs.get("arm_shoulder_lift.pos", 0.0),
            "elbow_flex": obs.get("arm_elbow_flex.pos", 0.0),
            "wrist_flex": obs.get("arm_wrist_flex.pos", 0.0),
            "wrist_roll": obs.get("arm_wrist_roll.pos", 0.0),
            "gripper": obs.get("arm_gripper.pos", 0.0),
            "x_vel": obs.get("x.vel", 0.0),
            "y_vel": obs.get("y.vel", 0.0),
            "theta_vel": obs.get("theta.vel", 0.0),
        }
    
    # ==================== Utility Methods ====================
    
    def wait(self, duration_s: float) -> None:
        """Wait for a specified duration.
        
        Args:
            duration_s: Time to wait in seconds.
        """
        time.sleep(duration_s)
    
    def wait_for_completion(self, timeout: Optional[float] = None) -> bool:
        """Wait for all queued commands to complete.
        
        Args:
            timeout: Maximum time to wait in seconds. None means wait forever.
        
        Returns:
            True if all commands completed, False if timeout was reached.
        """
        return self.teleop.wait_for_idle(timeout)
    
    def emergency_stop(self) -> None:
        """Perform an emergency stop of all robot movement."""
        self.teleop.stop()
    
    def is_moving(self) -> bool:
        """Check if the robot has active commands.
        
        Returns:
            True if there are commands being executed or queued.
        """
        return not self.teleop.is_idle()
