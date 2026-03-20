#!/usr/bin/env python
"""Gripper diagnostic test - verifies gripper action is being sent correctly.

This test will:
1. Check current gripper state
2. Send gripper commands and monitor if actions are actually being transmitted
3. Test with direct action inspection
"""

import sys
import time
sys.path.insert(0, '/home/darren/lerobot/examples/lekiwi')

from agent_control import LeKiwiAgentLoop, AgentInterface

print("=" * 60)
print("LeKiwi Gripper Diagnostic Test")
print("=" * 60)
print()

# Initialize
print("Connecting to robot...")
loop = LeKiwiAgentLoop(robot_ip="localhost", fps=30, enable_visualization=False)

try:
    loop.start()
    agent = AgentInterface(loop.agent_teleop)
    print("✓ Connected\n")
    
    # Test 1: Check teleop action directly
    print("Test 1: Checking teleop action output...")
    action = loop.agent_teleop.get_action()
    print(f"  Current action['arm_gripper.pos']: {action.get('arm_gripper.pos', 'NOT FOUND')}")
    print()
    
    # Test 2: Command gripper and check action immediately
    print("Test 2: Setting gripper to 1.0 (open)...")
    agent.set_gripper(1.0)
    time.sleep(0.1)  # Small delay for action to be set
    action = loop.agent_teleop.get_action()
    print(f"  After set_gripper(1.0):")
    print(f"    action['arm_gripper.pos']: {action.get('arm_gripper.pos', 'NOT FOUND')}")
    print()
    
    # Test 3: Wait and check robot observation
    print("Test 3: Waiting 2 seconds...")
    time.sleep(2.0)
    state = agent.get_robot_state()
    print(f"  Robot reported gripper: {state.get('gripper', 'unknown')}")
    print()
    
    # Test 4: Try intermediate values
    print("Test 4: Testing intermediate gripper values...")
    for target in [0.5, 0.0, -0.5, -1.0]:
        print(f"  Setting gripper to {target}...")
        agent.set_gripper(target)
        time.sleep(1.5)
        action = loop.agent_teleop.get_action()
        state = agent.get_robot_state()
        print(f"    Commanded: {target}")
        print(f"    Action:    {action.get('arm_gripper.pos', 'N/A')}")
        print(f"    Observed:  {state.get('gripper', 'N/A')}")
        print()
    
    print("=" * 60)
    print("Diagnostic complete")
    print("=" * 60)
    print("\nIf gripper didn't move but values changed:")
    print("  - Check if gripper motor has power")
    print("  - Check motor ID mapping (should be ID 6)")
    print("  - Try manually moving gripper - is it stuck?")
    
except KeyboardInterrupt:
    print("\n⚠️ Test interrupted")
except Exception as e:
    print(f"\n❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
finally:
    print("\nStopping robot...")
    loop.stop()
    print("✓ Disconnected")
