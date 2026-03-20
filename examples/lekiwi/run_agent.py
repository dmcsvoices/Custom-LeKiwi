#!/usr/bin/env python
"""Example script showing how to run an AI agent on LeKiwi.

WARNING: This script controls physical robot movement. DO NOT RUN without 
supervision - robot can cause damage if unattended.

Usage:
    1. Start the LeKiwi host on the robot first:
       conda activate lerobot
       python -m lerobot.robots.lekiwi.lekiwi_host --robot.id=my_robot
    
    2. Then run this script:
       cd /home/darren/lerobot/examples/lekiwi
       conda activate lerobot
       python run_agent.py
    
    3. Press Ctrl+C to stop the agent safely.

Configuration:
    - Change ROBOT_IP below to match your robot's IP address
    - Adjust movement distances, speeds, and behaviors in simple_agent_behavior()
    - Set enable_visualization=False if you don't need rerun visualization
"""

import time
from agent_control import LeKiwiAgentLoop, AgentInterface


def simple_agent_behavior(agent: AgentInterface):
    """Example agent that moves the robot in a pattern."""
    print("\n=== Starting Agent Behavior ===\n")
    
    # Move forward
    print("Moving forward 0.5m...")
    agent.move_forward(0.5)
    agent.wait_for_completion()
    
    # Rotate
    print("Rotating 90 degrees...")
    agent.rotate(90)
    agent.wait_for_completion()
    
    # Move forward again
    print("Moving forward 0.5m...")
    agent.move_forward(0.5)
    agent.wait_for_completion()
    
    # Get observation
    print("Getting observation...")
    obs = agent.get_observation()
    if obs:
        print(f"  Front camera shape: {obs.get('front', []).shape if 'front' in obs else 'N/A'}")
        print(f"  Robot state: {agent.get_robot_state()}")
    
    # Arm movement example
    print("Moving arm to position...")
    agent.move_arm(shoulder_pan=0.5, duration=1.0)
    agent.wait_for_completion()
    
    # Gripper
    print("Opening gripper...")
    agent.open_gripper()
    time.sleep(1.0)
    
    print("Closing gripper...")
    agent.close_gripper()
    time.sleep(1.0)
    
    # Home arm
    print("Homing arm...")
    agent.home_arm()
    agent.wait_for_completion()
    
    print("\n=== Agent Behavior Complete ===\n")


def main():
    """Main entry point."""
    # Configuration
    ROBOT_IP = "localhost"  # Change to your robot's IP
    
    # Initialize control loop
    loop = LeKiwiAgentLoop(
        robot_ip=ROBOT_IP,
        fps=30,
        enable_visualization=True,
    )
    
    try:
        # Start the control loop
        loop.start()
        
        # Create agent interface
        agent = AgentInterface(loop.agent_teleop)
        
        # Run agent behavior
        simple_agent_behavior(agent)
        
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    finally:
        # Cleanup - always stop the loop to ensure robot stops safely
        loop.stop()


if __name__ == "__main__":
    main()
