#!/usr/bin/env python

"""
Test script using XLeRobot-style direct step control.

This should now work much better with proper 2-degree increments
and simple direct position control instead of complex proportional control.
"""

import time
from lerobot.robots.lekiwi import LeKiwiClient, LeKiwiClientConfig
from lerobot.teleoperators.xbox import XboxTeleop, XboxTeleopConfig
from lerobot.utils.robot_utils import busy_wait

FPS = 30

def main():
    print("=== XLEROBOT-STYLE CONTROL TEST ===")
    print("Testing simplified direct step-based control (like XLeRobot).")
    print()

    # Create configs
    robot_config = LeKiwiClientConfig(remote_ip="192.168.8.157", id="my_lekiwi")
    xbox_config = XboxTeleopConfig(id="my_xbox_controller")

    try:
        print("Connecting to Xbox controller...")
        xbox = XboxTeleop(xbox_config)
        xbox.connect()
        print("✓ Xbox controller connected")

        print("Connecting to robot...")
        robot = LeKiwiClient(robot_config)
        robot.connect()
        print("✓ Robot connected")

        if not robot.is_connected or not xbox.is_connected:
            print("✗ Connection failed!")
            return

        print()
        print("=== XLEROBOT-STYLE CONTROL ===")
        print("Now using simple 2-degree steps like XLeRobot!")
        print()
        print("Key improvements:")
        print("- degree_step = 2° (like XLeRobot)")
        print("- Direct position updates (no complex proportional control)")
        print("- Simple binary gripper control")
        print("- Real-time current position tracking")
        print()
        print("Controls:")
        print("  Left Stick UP/DOWN: Wrist flex (2° steps)")
        print("  Left Stick LEFT/RIGHT: Wrist roll (2° steps)")
        print("  D-Pad: Shoulder pan/lift (2° steps)")
        print("  LS Press + Left Stick X: Elbow flex (2° steps)")
        print("  LT: Open gripper")
        print("  RT: Close gripper")
        print("  RB: 2x speed multiplier")
        print("  Back: Exit")
        print()

        loop_count = 0
        last_positions = {}

        while True:
            t0 = time.perf_counter()
            loop_count += 1

            # Get robot observation
            observation = robot.get_observation()

            # Get Xbox controller action WITH observation
            xbox_action = xbox.get_action(observation)

            # Create action with proper key format for LeKiwiClient
            action = {f"{k}.pos": v for k, v in xbox_action.items() if k.startswith("arm_")}
            action.update({k: v for k, v in xbox_action.items() if k in ["x.vel", "y.vel", "theta.vel"]})

            # Send action to robot
            robot.send_action(action)

            # Show position updates every 20 loops
            if observation and loop_count % 20 == 0:
                current_positions = {k: v for k, v in observation.items() if k.startswith("arm_")}

                if last_positions:
                    print(f"--- Position Update (loop {loop_count}) ---")
                    for joint, current_pos in sorted(current_positions.items()):
                        if joint in last_positions:
                            change = current_pos - last_positions[joint]
                            degrees = change * 180 / 3.14159  # Convert to degrees
                            if abs(change) > 0.005:  # Show any significant change
                                print(f"{joint}: {current_pos:.3f} rad ({degrees:+.1f}°)")

                    # Show controller commands
                    arm_actions = {k: v for k, v in xbox_action.items() if k.startswith("arm_")}
                    active_joints = []
                    for joint, pos in arm_actions.items():
                        if joint in last_positions:
                            target_pos = action.get(f"{joint}.pos", pos)
                            if abs(target_pos - last_positions.get(joint.replace(".pos", ""), 0)) > 0.005:
                                active_joints.append(joint)

                    if active_joints:
                        print(f"Active commands: {active_joints}")
                    print()

                last_positions = current_positions.copy()

            # Check for quit
            events = xbox.get_teleop_events()
            if events.get("terminate_episode", False):
                print("Quit button pressed - exiting test...")
                break

            busy_wait(max(1.0 / FPS - (time.perf_counter() - t0), 0.0))

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        print("Disconnecting...")
        robot.disconnect()
        xbox.disconnect()
        print("Test complete!")
        print()
        print("Expected results with XLeRobot-style control:")
        print("- Clear 2° movements when you move sticks/D-pad")
        print("- All arm joints should now respond properly")
        print("- Gripper should open/close with triggers")
        print("- Movement should feel natural and responsive")

if __name__ == "__main__":
    main()