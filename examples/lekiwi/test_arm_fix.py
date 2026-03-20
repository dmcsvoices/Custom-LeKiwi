#!/usr/bin/env python

"""
Test script to verify the ARM movement fix.

This script tests the corrected proportional control implementation
that should now work like the XLeRobot implementation.
"""

import time
from lerobot.robots.lekiwi import LeKiwiClient, LeKiwiClientConfig
from lerobot.teleoperators.xbox import XboxTeleop, XboxTeleopConfig
from lerobot.utils.robot_utils import busy_wait

FPS = 30

def main():
    print("=== ARM MOVEMENT FIX TEST ===")
    print("Testing the corrected proportional control implementation.")
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
        print("=== FIXED CONTROL TEST ===")
        print("The ARM should now move using proportional control!")
        print("  Left Stick: Wrist roll (X) & wrist flex (Y)")
        print("  D-Pad: Shoulder pan (left/right) & shoulder lift (up/down)")
        print("  LS Press + Left Stick X: Elbow flex")
        print("  LT/RT: Gripper control")
        print("  Back: Exit")
        print()

        loop_count = 0

        while True:
            t0 = time.perf_counter()
            loop_count += 1

            # Get robot observation
            observation = robot.get_observation()

            # Get Xbox controller action WITH observation (key fix!)
            xbox_action = xbox.get_action(observation)

            # Create action with proper key format for LeKiwiClient
            action = {f"{k}.pos": v for k, v in xbox_action.items() if k.startswith("arm_")}
            action.update({k: v for k, v in xbox_action.items() if k in ["x.vel", "y.vel", "theta.vel"]})

            # Send action to robot
            robot.send_action(action)

            # Show feedback every 30 loops
            if loop_count % 30 == 0:
                if observation:
                    arm_obs = {k: v for k, v in observation.items() if k.startswith("arm_")}
                    if arm_obs:
                        print(f"Current ARM positions (loop {loop_count}):")
                        for k, v in sorted(arm_obs.items()):
                            print(f"  {k}: {v:.4f}")
                        print()

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

if __name__ == "__main__":
    main()