#!/usr/bin/env python
"""Check raw observation values for gripper.

Shows the raw observation data to understand what values the robot is reporting.
"""

import sys
import time
sys.path.insert(0, '/home/darren/lerobot/examples/lekiwi')

from agent_control import LeKiwiAgentLoop, AgentInterface

print("=" * 60)
print("Raw Gripper Observation Check")
print("=" * 60)
print()

loop = LeKiwiAgentLoop(robot_ip="localhost", fps=30, enable_visualization=False)

try:
    loop.start()
    agent = AgentInterface(loop.agent_teleop)
    print("✓ Connected\n")
    
    # Get raw observation
    obs = agent.get_observation()
    if obs:
        print("Available observation keys:")
        for key in sorted(obs.keys()):
            val = obs[key]
            if hasattr(val, 'shape'):
                print(f"  {key}: shape={val.shape}")
            else:
                print(f"  {key}: {val}")
        print()
        
        # Check gripper-related keys
        print("Gripper-related values:")
        for key in sorted(obs.keys()):
            if 'gripper' in key.lower():
                print(f"  {key}: {obs[key]}")
    
    # Now command and watch
    print("\n" + "=" * 60)
    print("Commanding close (-1.0) for 3 seconds...")
    agent.set_gripper(-1.0)
    for i in range(6):
        time.sleep(0.5)
        obs = agent.get_observation()
        gripper_val = obs.get('arm_gripper.pos', 'N/A')
        print(f"  t={i*0.5:.1f}s: arm_gripper.pos = {gripper_val}")
    
    print("\nCommanding open (1.0) for 3 seconds...")
    agent.set_gripper(1.0)
    for i in range(6):
        time.sleep(0.5)
        obs = agent.get_observation()
        gripper_val = obs.get('arm_gripper.pos', 'N/A')
        print(f"  t={i*0.5:.1f}s: arm_gripper.pos = {gripper_val}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    print("\nDisconnecting...")
    loop.stop()
    print("✓ Done")
