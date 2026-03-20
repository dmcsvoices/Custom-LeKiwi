#!/usr/bin/env python

"""
Debug script to diagnose ARM movement issues.

This script will help identify where the problem occurs:
1. Xbox controller input detection
2. Action generation
3. Robot communication
4. Arm motor response

Run this while using your Xbox controller to debug the ARM movement issue.
"""

import time
import sys

from lerobot.robots.lekiwi import LeKiwiClient, LeKiwiClientConfig
from lerobot.teleoperators.xbox import XboxTeleop, XboxTeleopConfig
from lerobot.utils.robot_utils import busy_wait

FPS = 10  # Slower for easier debugging

def main():
    print("=== ARM MOVEMENT DIAGNOSTIC ===")
    print("This script will help diagnose why the ARM is not moving.")
    print()

    # Create configs
    robot_config = LeKiwiClientConfig(remote_ip="192.168.8.157", id="my_lekiwi")
    xbox_config = XboxTeleopConfig(id="my_xbox_controller")

    # Initialize
    try:
        print("1. Connecting to Xbox controller...")
        xbox = XboxTeleop(xbox_config)
        xbox.connect()
        print(f"   ✓ Xbox controller connected: {xbox.is_connected}")

        print("2. Connecting to robot...")
        robot = LeKiwiClient(robot_config)
        robot.connect()
        print(f"   ✓ Robot connected: {robot.is_connected}")

        if not robot.is_connected or not xbox.is_connected:
            print("   ✗ Connection failed!")
            return

    except Exception as e:
        print(f"   ✗ Connection error: {e}")
        return

    print()
    print("=== DIAGNOSTIC CONTROLS ===")
    print("Move controls and watch the output:")
    print("  Left Stick: Wrist roll (X) & wrist flex (Y)")
    print("  D-Pad: Shoulder pan (left/right) & shoulder lift (up/down)")
    print("  LS Press + Left Stick X: Elbow flex")
    print("  LT/RT: Gripper control")
    print("  Back: Exit")
    print()

    loop_count = 0
    last_non_zero_action = None

    try:
        while True:
            t0 = time.perf_counter()
            loop_count += 1

            # Get current robot observation
            observation = robot.get_observation()

            # Get Xbox controller raw action
            xbox_action = xbox.get_action()

            # Create formatted action for robot
            action = {f"{k}.pos": v for k, v in xbox_action.items() if k.startswith("arm_")}
            action.update({k: v for k, v in xbox_action.items() if k in ["x.vel", "y.vel", "theta.vel"]})

            # Check for any non-zero arm actions
            arm_actions = {k: v for k, v in xbox_action.items() if k.startswith("arm_")}
            has_arm_movement = any(abs(v) > 0.001 for v in arm_actions.values())

            # Print diagnostics every 10 loops or when there's arm movement
            if loop_count % 10 == 0 or has_arm_movement:
                print(f"\n--- Loop {loop_count} ---")

                # Show current arm positions from observation
                if observation:
                    arm_obs = {k: v for k, v in observation.items() if k.startswith("arm_")}
                    if arm_obs:
                        print("Current ARM positions (observation):")
                        for k, v in arm_obs.items():
                            print(f"  {k}: {v:.4f}")

                # Show Xbox action generation
                print("Xbox generated actions:")
                for k, v in arm_actions.items():
                    marker = " ← MOVING!" if abs(v) > 0.001 else ""
                    print(f"  {k}: {v:.4f}{marker}")

                # Show formatted action sent to robot
                robot_arm_actions = {k: v for k, v in action.items() if k.startswith("arm_")}
                print("Action sent to robot:")
                for k, v in robot_arm_actions.items():
                    marker = " ← MOVING!" if abs(v) > 0.001 else ""
                    print(f"  {k}: {v:.4f}{marker}")

            # Track last non-zero action for reference
            if has_arm_movement:
                last_non_zero_action = arm_actions.copy()
                print("*** ARM MOVEMENT DETECTED! ***")

            # Send action to robot
            try:
                result = robot.send_action(action)
                if loop_count % 50 == 0:  # Show communication status occasionally
                    print(f"Robot communication: {'OK' if result else 'FAILED'}")
            except Exception as e:
                print(f"   ✗ Robot send_action failed: {e}")
                break

            # Check for quit
            events = xbox.get_teleop_events()
            if events.get("terminate_episode", False):
                print("\nQuit button pressed - exiting diagnostic...")
                break

            busy_wait(max(1.0 / FPS - (time.perf_counter() - t0), 0.0))

    except KeyboardInterrupt:
        print("\n\nKeyboard interrupt - exiting diagnostic...")

    finally:
        print("\n=== DIAGNOSTIC SUMMARY ===")
        if last_non_zero_action:
            print("Last detected ARM movement commands:")
            for k, v in last_non_zero_action.items():
                print(f"  {k}: {v:.4f}")
        else:
            print("⚠️  NO ARM MOVEMENT DETECTED during diagnostic!")
            print("Possible issues:")
            print("  1. Xbox controller not generating arm actions")
            print("  2. Deadzone too high (controller inputs ignored)")
            print("  3. Incorrect controller button/stick mapping")

        print("\nDisconnecting...")
        robot.disconnect()
        xbox.disconnect()
        print("Done!")

if __name__ == "__main__":
    main()