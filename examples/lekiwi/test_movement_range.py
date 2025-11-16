#!/usr/bin/env python

"""
Test script to verify ARM movement range and scaling.

This script tests the improved movement scaling and shows expected ranges.
"""

import time
from lerobot.robots.lekiwi import LeKiwiClient, LeKiwiClientConfig
from lerobot.teleoperators.xbox import XboxTeleop, XboxTeleopConfig
from lerobot.utils.robot_utils import busy_wait

FPS = 30

def main():
    print("=== ARM MOVEMENT RANGE TEST ===")
    print("Testing improved movement scaling for full range of motion.")
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
        print("=== IMPROVED MOVEMENT TEST ===")
        print("Movement should now have much better range!")
        print()
        print("Expected improvements:")
        print("- arm_speed increased from 0.05 → 0.3 (6x faster)")
        print("- target_offset scaling increased from 10.0 → 3.0 with higher base speed")
        print("- kp reduced from 3.0 → 1.0 for smoother control")
        print()
        print("Controls:")
        print("  Left Stick UP/DOWN: Wrist flex (should move ~60° range)")
        print("  Left Stick LEFT/RIGHT: Wrist roll (should move ~60° range)")
        print("  D-Pad: Shoulder pan/lift (should move in larger increments)")
        print("  LS Press + Left Stick X: Elbow flex")
        print("  LT/RT: Gripper control")
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

            # Track position changes and show movement feedback
            if observation and loop_count % 15 == 0:
                current_positions = {k: v for k, v in observation.items() if k.startswith("arm_")}

                if last_positions:
                    print(f"--- Position Update (loop {loop_count}) ---")
                    for joint, current_pos in sorted(current_positions.items()):
                        if joint in last_positions:
                            change = current_pos - last_positions[joint]
                            degrees = change * 180 / 3.14159  # Convert radians to degrees
                            if abs(change) > 0.01:  # Only show significant changes
                                print(f"{joint}: {current_pos:.3f} rad ({change:+.3f} rad, {degrees:+.1f}°)")

                    # Check for controller input
                    arm_actions = {k: v for k, v in xbox_action.items() if k.startswith("arm_")}
                    active_inputs = [k for k, v in arm_actions.items() if abs(v) > 0.01]
                    if active_inputs:
                        print(f"Active inputs: {active_inputs}")
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
        print("Expected results:")
        print("- Full stick deflection should move joints ~30-60 degrees")
        print("- Movement should be smooth and responsive")
        print("- Range should feel natural for teleoperation")

if __name__ == "__main__":
    main()