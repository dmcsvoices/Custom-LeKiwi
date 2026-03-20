#!/usr/bin/env python
"""Verify gripper actions are being sent frame-to-frame.

This test monitors the actual actions being sent to the robot
in real-time to see if the gripper command is persisting.
"""

import sys
import time
import threading
sys.path.insert(0, '/home/darren/lerobot/examples/lekiwi')

from agent_control import LeKiwiAgentLoop, AgentInterface

print("=" * 60)
print("Gripper Frame-by-Frame Monitor")
print("=" * 60)
print()

# Track actions
actions_log = []
stop_monitor = threading.Event()

def monitor_actions(loop):
    """Monitor actions being sent."""
    while not stop_monitor.is_set():
        try:
            action = loop.agent_teleop.get_action()
            actions_log.append({
                'time': time.time(),
                'gripper': action.get('arm_gripper.pos', 'N/A')
            })
        except:
            pass
        time.sleep(0.1)  # 10 Hz monitoring

# Initialize
print("Connecting to robot...")
loop = LeKiwiAgentLoop(robot_ip="localhost", fps=30, enable_visualization=False)

try:
    loop.start()
    agent = AgentInterface(loop.agent_teleop)
    print("✓ Connected\n")
    
    # Start monitoring
    monitor_thread = threading.Thread(target=monitor_actions, args=(loop,))
    monitor_thread.start()
    
    # Test: Command sequence with observation checks
    print("Commanding gripper sequence...")
    print()
    
    commands = [
        ("Close ( -1.0 )", -1.0),
        ("Wait", None),
        ("Open ( 1.0 )", 1.0),
        ("Wait", None),
        ("Close ( -1.0 )", -1.0),
    ]
    
    for label, value in commands:
        if value is not None:
            print(f"{label}")
            agent.set_gripper(value)
        else:
            print(f"{label} 2 seconds...")
        
        # Show last few actions
        time.sleep(2.0)
        recent = actions_log[-10:] if len(actions_log) >= 10 else actions_log
        gripper_values = [a['gripper'] for a in recent]
        print(f"  Actions sent: {gripper_values}")
        
        state = agent.get_robot_state()
        print(f"  Robot reports: {state.get('gripper', 'N/A'):.3f}")
        print()
    
    stop_monitor.set()
    monitor_thread.join(timeout=1.0)
    
    print("=" * 60)
    print("Summary:")
    print(f"  Total actions logged: {len(actions_log)}")
    if actions_log:
        unique = set(a['gripper'] for a in actions_log)
        print(f"  Unique gripper values: {sorted(unique)}")
    
except KeyboardInterrupt:
    print("\n⚠️ Interrupted")
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    stop_monitor.set()
    print("\nDisconnecting...")
    loop.stop()
    print("✓ Done")
