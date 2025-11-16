#!/usr/bin/env python

"""
Simple Xbox controller input test.
This script ONLY tests controller input without connecting to the robot.
Use this to verify your controller is working and generating proper actions.
"""

import time
from lerobot.teleoperators.xbox import XboxTeleop, XboxTeleopConfig

def main():
    print("=== XBOX CONTROLLER INPUT TEST ===")
    print("This tests ONLY the Xbox controller input (no robot connection).")
    print()

    # Create Xbox teleop
    xbox_config = XboxTeleopConfig(id="test_controller")
    xbox = XboxTeleop(xbox_config)

    try:
        print("Connecting to Xbox controller...")
        xbox.connect()
        print(f"✓ Connected: {xbox.controller.get_name()}")
        print()

        print("=== CONTROLLER TEST ===")
        print("Try these inputs and watch for changes:")
        print("  Left Stick: Move in any direction")
        print("  D-Pad: Press any direction")
        print("  LS (Left Stick Press): Hold and move left stick X")
        print("  LT/RT: Pull triggers")
        print("  Back: Exit test")
        print()

        last_action = None

        while True:
            # Get action from controller
            action = xbox.get_action()

            # Only print when action changes significantly
            action_changed = False
            if last_action is None:
                action_changed = True
            else:
                for key in action:
                    if abs(action[key] - last_action.get(key, 0)) > 0.01:
                        action_changed = True
                        break

            if action_changed:
                print("Controller Action:")
                arm_actions = {k: v for k, v in action.items() if k.startswith("arm_")}
                base_actions = {k: v for k, v in action.items() if k in ["x.vel", "y.vel", "theta.vel"]}

                print("  ARM:")
                for k, v in arm_actions.items():
                    marker = " ← NON-ZERO!" if abs(v) > 0.001 else ""
                    print(f"    {k}: {v:.4f}{marker}")

                print("  BASE:")
                for k, v in base_actions.items():
                    marker = " ← NON-ZERO!" if abs(v) > 0.001 else ""
                    print(f"    {k}: {v:.4f}{marker}")
                print()

                last_action = action.copy()

            # Check for quit
            events = xbox.get_teleop_events()
            if events.get("terminate_episode", False):
                print("Back button pressed - exiting...")
                break

            time.sleep(0.1)

    except Exception as e:
        print(f"Error: {e}")
        return

    finally:
        print("Disconnecting...")
        xbox.disconnect()
        print("Done!")

if __name__ == "__main__":
    main()