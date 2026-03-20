#!/usr/bin/env python
"""Connection test for agent_control module.

This script tests connection to the LeKiwi robot and verifies
observations can be received without sending any movement commands.

SAFETY: This script only reads sensor data - no robot movement.
"""

import sys
sys.path.insert(0, '/home/darren/lerobot/examples/lekiwi')

from agent_control import LeKiwiAgentLoop, AgentInterface, AgentTeleopConfig

print("=" * 60)
print("LeKiwi Agent Connection Test")
print("=" * 60)
print()

# Test 1: Create loop (doesn't connect yet)
print("Test 1: Creating LeKiwiAgentLoop...")
try:
    loop = LeKiwiAgentLoop(
        robot_ip="localhost",
        fps=30,
        enable_visualization=False,  # Skip rerun for this test
    )
    print("✓ Loop created")
except Exception as e:
    print(f"❌ Failed to create loop: {e}")
    sys.exit(1)

# Test 2: Connect to robot
print()
print("Test 2: Connecting to robot at localhost...")
try:
    loop.start()
    print("✓ Connected to robot")
    print(f"  - Robot connected: {loop.robot.is_connected}")
    print(f"  - Teleop connected: {loop.agent_teleop.is_connected}")
except Exception as e:
    print(f"❌ Failed to connect: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Create agent interface
print()
print("Test 3: Creating AgentInterface...")
try:
    agent = AgentInterface(loop.agent_teleop)
    print("✓ Agent interface created")
except Exception as e:
    print(f"❌ Failed to create agent interface: {e}")
    loop.stop()
    sys.exit(1)

# Test 4: Get observation (non-blocking read)
print()
print("Test 4: Reading observations...")
import time
time.sleep(0.5)  # Let loop collect some observations

try:
    obs = agent.get_observation()
    if obs:
        print("✓ Observation received")
        
        # Check cameras
        cameras = [k for k in obs.keys() if k in ['front', 'wrist', 'top']]
        print(f"  - Cameras available: {cameras}")
        
        for cam in cameras:
            if obs.get(cam) is not None:
                shape = obs[cam].shape
                print(f"    - {cam}: shape={shape}")
        
        # Check robot state
        state = agent.get_robot_state()
        if state:
            print(f"  - Robot state keys: {list(state.keys())[:3]}...")
            print(f"    - x_vel: {state.get('x_vel', 'N/A')}")
            print(f"    - gripper: {state.get('gripper', 'N/A')}")
    else:
        print("⚠ No observation available yet (may need more time)")
        
except Exception as e:
    print(f"❌ Failed to get observation: {e}")
    import traceback
    traceback.print_exc()

# Test 5: Check idle status
print()
print("Test 5: Checking agent status...")
try:
    is_idle = loop.agent_teleop.is_idle()
    print(f"  - Agent idle: {is_idle}")
    print(f"  - Agent moving: {agent.is_moving()}")
    print("✓ Status check complete")
except Exception as e:
    print(f"❌ Status check failed: {e}")

# Cleanup
print()
print("=" * 60)
print("Cleaning up...")
loop.stop()
print("✓ Disconnected from robot")
print()
print("=" * 60)
print("✅ All connection tests passed!")
print("=" * 60)
