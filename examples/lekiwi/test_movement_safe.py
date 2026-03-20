#!/usr/bin/env python
"""Safe movement test for agent_control module.

SAFETY: Run only with robot supervised and clear of obstacles.
This performs small, slow movements to verify control works.

Test sequence:
1. Wait 3 seconds (time to abort if needed)
2. Rotate 15 degrees left (small rotation)
3. Wait for completion
4. Rotate 15 degrees right (return to start)
5. Done
"""

import sys
import time
sys.path.insert(0, '/home/darren/lerobot/examples/lekiwi')

from agent_control import LeKiwiAgentLoop, AgentInterface

print("=" * 60)
print("LeKiwi Safe Movement Test")
print("=" * 60)
print()
print("⚠️  SAFETY CHECKLIST:")
print("   - Robot is on the ground/table (not held)")
print("   - Area around robot is clear")
print("   - You are supervising and can stop if needed")
print()
print("This test will:")
print("   1. Rotate 15° left (slowly)")
print("   2. Rotate 15° right (return to start)")
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
    
    # Test 1: Small rotation left
    print("Test 1: Rotating 15° left...")
    agent.rotate_left(15, speed=30)  # 15 degrees at 30 deg/s = 0.5 seconds
    agent.wait_for_completion(timeout=5.0)
    print("✓ Rotation complete\n")
    
    time.sleep(0.5)  # Brief pause
    
    # Test 2: Small rotation right (return to start)
    print("Test 2: Rotating 15° right (return)...")
    agent.rotate_right(15, speed=30)
    agent.wait_for_completion(timeout=5.0)
    print("✓ Rotation complete\n")
    
    print("=" * 60)
    print("✅ All movement tests passed!")
    print("=" * 60)
    
except KeyboardInterrupt:
    print("\n⚠️ Test interrupted by user")
except Exception as e:
    print(f"\n❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
finally:
    print("\nStopping robot...")
    agent.emergency_stop() if 'agent' in locals() else None
    loop.stop()
    print("✓ Disconnected")
