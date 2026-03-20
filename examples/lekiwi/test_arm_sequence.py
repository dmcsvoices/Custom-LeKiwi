#!/usr/bin/env python
"""
Comprehensive arm joint movement test for LeKiwi.
Tests each joint individually: shoulder pan/lift, elbow, wrist flex/roll, gripper.
"""

import sys
import time
import math
sys.path.insert(0, '/home/darren/lerobot/examples/lekiwi')

from agent_control import LeKiwiAgentLoop, AgentInterface

# Movement parameters
MOVE_DURATION = 2.0  # seconds per movement
PAUSE = 1.0  # seconds between movements

def get_arm_state(agent):
    """Get current arm joint positions in degrees."""
    obs = agent.get_observation()
    if not obs:
        return None
    return {
        'shoulder_pan': math.degrees(obs.get('arm_shoulder_pan.pos', 0)),
        'shoulder_lift': math.degrees(obs.get('arm_shoulder_lift.pos', 0)),
        'elbow_flex': math.degrees(obs.get('arm_elbow_flex.pos', 0)),
        'wrist_flex': math.degrees(obs.get('arm_wrist_flex.pos', 0)),
        'wrist_roll': math.degrees(obs.get('arm_wrist_roll.pos', 0)),
        'gripper': obs.get('arm_gripper.pos', 0),
    }

def print_arm_state(state, label=""):
    """Print arm state in readable format."""
    if label:
        print(f"    {label}")
    print(f"    Pan: {state['shoulder_pan']:+.1f}° | Lift: {state['shoulder_lift']:+.1f}° | "
          f"Elbow: {state['elbow_flex']:+.1f}°")
    print(f"    Wrist flex: {state['wrist_flex']:+.1f}° | Roll: {state['wrist_roll']:+.1f}° | "
          f"Gripper: {state['gripper']:+.2f}")

def test_joint(agent, joint_name, positions_deg, desc):
    """Test a joint through a sequence of positions."""
    print(f"\n{'='*50}")
    print(f"🔧 Testing: {desc}")
    print(f"{'='*50}")
    
    for i, pos_deg in enumerate(positions_deg, 1):
        print(f"\n  {i}. Moving to {pos_deg:+.1f}°")
        
        # Record start state
        start_state = get_arm_state(agent)
        print_arm_state(start_state, "Start:")
        
        # Move joint
        pos_rad = math.radians(pos_deg)
        
        if joint_name == 'shoulder_pan':
            agent.move_arm(shoulder_pan=pos_rad, duration=MOVE_DURATION)
        elif joint_name == 'shoulder_lift':
            agent.move_arm(shoulder_lift=pos_rad, duration=MOVE_DURATION)
        elif joint_name == 'elbow_flex':
            agent.move_arm(elbow_flex=pos_rad, duration=MOVE_DURATION)
        elif joint_name == 'wrist_flex':
            agent.move_arm(wrist_flex=pos_rad, duration=MOVE_DURATION)
        elif joint_name == 'wrist_roll':
            agent.move_arm(wrist_roll=pos_rad, duration=MOVE_DURATION)
        elif joint_name == 'gripper':
            agent.set_gripper(pos_deg)  # Gripper uses -1 to 1 directly
        
        # Wait for movement
        time.sleep(MOVE_DURATION + 0.3)
        
        # Record end state
        end_state = get_arm_state(agent)
        print_arm_state(end_state, "End:")
        
        # Calculate change
        joint_key = joint_name.replace('_', '_') if '_' in joint_name else joint_name
        if joint_name == 'gripper':
            delta = end_state['gripper'] - start_state['gripper']
            print(f"    Δ Gripper: {delta:+.3f}")
        else:
            delta = end_state[joint_name] - start_state[joint_name]
            print(f"    Δ {joint_name}: {delta:+.1f}°")
        
        time.sleep(PAUSE)

def main():
    print("=" * 60)
    print("🦾 LeKiwi Arm Movement Test Suite")
    print("=" * 60)
    print("\nTesting each joint individually with smooth movements.")
    print("-" * 60)
    
    # Initialize
    print("\n📡 Connecting to robot...")
    loop = LeKiwiAgentLoop(robot_ip="localhost", fps=30, enable_visualization=False)
    loop.start()
    agent = AgentInterface(loop.agent_teleop)
    print("✓ Connected")
    
    # Wait for first observation
    print("\n⏳ Waiting for arm state...")
    for _ in range(20):
        obs = agent.get_observation()
        if obs is not None:
            break
        time.sleep(0.1)
    
    if obs is None:
        print("❌ Failed to get arm state")
        loop.stop()
        return
    
    # Show initial state
    print("\n📊 Initial arm state:")
    initial_state = get_arm_state(agent)
    print_arm_state(initial_state)
    
    # ========================================
    # Test 1: Shoulder Pan (Rotation Left/Right)
    # ========================================
    test_joint(agent, 'shoulder_pan', [0, -45, 0, 45, 0], 
               "Shoulder Pan (Rotation Left/Right)")
    
    # ========================================
    # Test 2: Shoulder Lift (Up/Down)
    # ========================================
    test_joint(agent, 'shoulder_lift', [0, -30, 0, 30, 0],
               "Shoulder Lift (Up/Down)")
    
    # ========================================
    # Test 3: Elbow Flex (Extend/Retract)
    # ========================================
    test_joint(agent, 'elbow_flex', [90, 45, 90, 135, 90],
               "Elbow Flex (Bend/Extend)")
    
    # ========================================
    # Test 4: Wrist Flex (Up/Down)
    # ========================================
    test_joint(agent, 'wrist_flex', [0, -30, 0, 30, 0],
               "Wrist Flex (Up/Down)")
    
    # ========================================
    # Test 5: Wrist Roll (Rotate)
    # ========================================
    test_joint(agent, 'wrist_roll', [0, -45, 0, 45, 0],
               "Wrist Roll (Rotate Wrist)")
    
    # ========================================
    # Test 6: Gripper (Open/Close)
    # ========================================
    test_joint(agent, 'gripper', [0, -0.8, 0, 0.8, 0],
               "Gripper (Close/Open)")
    
    # ========================================
    # Final: Return to home
    # ========================================
    print(f"\n{'='*60}")
    print("🏠 Returning arm to home position")
    print(f"{'='*60}")
    agent.home_arm()
    time.sleep(3.0)
    
    final_state = get_arm_state(agent)
    print("\n📊 Final arm state:")
    print_arm_state(final_state)
    
    print("\n" + "=" * 60)
    print("✅ Arm movement test suite complete!")
    print("=" * 60)
    
    # Cleanup
    loop.stop()
    print("\n✓ Robot disconnected")

if __name__ == "__main__":
    main()
