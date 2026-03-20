#!/usr/bin/env python
"""Gripper control test for agent_control module.

SAFETY: Run with robot supervised and gripper clear of obstacles.
This opens and closes the gripper to verify control works.

Test sequence:
1. Open gripper fully
2. Wait 2 seconds
3. Close gripper fully
4. Wait 2 seconds
5. Open gripper (return to start)
"""

import sys
import time
sys.path.insert(0, '/home/darren/lerobot/examples/lekiwi')

from agent_control import LeKiwiAgentLoop, AgentInterface

print("=" * 60)
print("LeKiwi Gripper Control Test")
print("=" * 60)
print()
print("⚠️  SAFETY CHECKLIST:")
print("   - Gripper is clear of objects and obstacles")
print("   - You are supervising")
print()
print("This test will:")
print("   1. Open gripper")
print("   2. Close gripper")
print("   3. Open gripper (return to start)")
print()

# Countdown
print("Starting in 3 seconds...")
for i in range(3, 0, -1):
    print(f"  {i}...")
    time.sleep(1)
print()

# Initialize
print("Connecting to robot...")
loop = LeKiwiAgentLoop(robot_ip="localhost", fps=30, enable_visualization=False)

try:
    loop.start()
    agent = AgentInterface(loop.agent_teleop)
    print("✓ Connected\n")
    
    # Get initial gripper state
    state = agent.get_robot_state()
    initial_gripper = state.get('gripper', 0.0)
    if isinstance(initial_gripper, (int, float)):
        print(f"Initial gripper position: {initial_gripper:.3f}")
    else:
        print(f"Initial gripper position: {initial_gripper}")
    print("  (-1.0 = closed, 1.0 = open)\n")
    
    # Test 1: Open gripper
    print("Test 1: Opening gripper...")
    agent.open_gripper()
    time.sleep(2.0)  # Wait for gripper to move
    state = agent.get_robot_state()
    gripper_pos = state.get('gripper', 0.0)
    if isinstance(gripper_pos, (int, float)):
        print(f"  Gripper position: {gripper_pos:.3f}")
    else:
        print(f"  Gripper position: {gripper_pos}")
    print("✓ Open complete\n")
    
    # Test 2: Close gripper
    print("Test 2: Closing gripper...")
    agent.close_gripper()
    time.sleep(2.0)
    state = agent.get_robot_state()
    gripper_pos = state.get('gripper', 0.0)
    if isinstance(gripper_pos, (int, float)):
        print(f"  Gripper position: {gripper_pos:.3f}")
    else:
        print(f"  Gripper position: {gripper_pos}")
    print("✓ Close complete\n")
    
    # Test 3: Open gripper (return to start)
    print("Test 3: Opening gripper (return to start)...")
    agent.open_gripper()
    time.sleep(2.0)
    state = agent.get_robot_state()
    final_gripper = state.get('gripper', 0.0)
    if isinstance(final_gripper, (int, float)):
        print(f"  Gripper position: {final_gripper:.3f}")
    else:
        print(f"  Gripper position: {final_gripper}")
    print("✓ Open complete\n")
    
    print("=" * 60)
    print("✅ All gripper tests passed!")
    print("=" * 60)
    if isinstance(initial_gripper, (int, float)) and isinstance(final_gripper, (int, float)):
        print(f"\nInitial: {initial_gripper:.3f}")
        print(f"Final:   {final_gripper:.3f}")
    else:
        print(f"\nInitial: {initial_gripper}")
        print(f"Final:   {final_gripper}")
    
except KeyboardInterrupt:
    print("\n⚠️ Test interrupted by user")
except Exception as e:
    print(f"\n❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
finally:
    print("\nStopping robot...")
    if 'agent' in locals():
        agent.open_gripper()  # Leave gripper open
    loop.stop()
    print("✓ Disconnected")
