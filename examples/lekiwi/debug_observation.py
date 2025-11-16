#!/usr/bin/env python

"""
Debug script to examine observation format and position tracking.
This will help us understand why the arm movement stopped working.
"""

import time
from lerobot.robots.lekiwi import LeKiwiClient, LeKiwiClientConfig
from lerobot.teleoperators.xbox import XboxTeleop, XboxTeleopConfig

def main():
    print("=== OBSERVATION DEBUG ===")
    print("Debugging observation format and position tracking.")
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
        print("=== OBSERVATION ANALYSIS ===")

        for i in range(5):
            print(f"\n--- Sample {i+1} ---")

            # Get robot observation
            observation = robot.get_observation()
            print(f"Observation type: {type(observation)}")
            print(f"Observation keys: {list(observation.keys()) if observation else 'None'}")

            if observation:
                print("\nAll observation entries:")
                for k, v in observation.items():
                    print(f"  {k}: {v} (type: {type(v)})")

                # Check for arm-related keys
                arm_keys = [k for k in observation.keys() if 'arm' in k.lower()]
                print(f"\nArm-related keys: {arm_keys}")

            # Get Xbox controller action
            print("\n--- Xbox Controller Analysis ---")
            xbox_action = xbox.get_action(observation)
            print(f"Xbox action type: {type(xbox_action)}")
            print(f"Xbox action keys: {list(xbox_action.keys())}")

            print("\nXbox action values:")
            for k, v in xbox_action.items():
                print(f"  {k}: {v}")

            # Check internal arm positions
            print(f"\nInternal arm positions: {xbox.arm_positions}")

            print("\nMove your controller and press Enter for next sample...")
            input()

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        print("Disconnecting...")
        robot.disconnect()
        xbox.disconnect()
        print("Debug complete!")

if __name__ == "__main__":
    main()