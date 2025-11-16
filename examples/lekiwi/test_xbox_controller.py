#!/usr/bin/env python

"""
Test script for Xbox controller functionality without requiring robot connection.
This helps validate that controller inputs are being read correctly.
"""

import time

from lerobot.teleoperators.xbox import XboxTeleop, XboxTeleopConfig

def test_xbox_controller():
    """Test Xbox controller input without robot."""
    print("Xbox Controller Test")
    print("===================")
    print("This script tests Xbox controller input without connecting to robot.")
    print("Move controls to see output. Press Back button to quit.\n")

    # Create Xbox controller
    xbox_config = XboxTeleopConfig(id="test_xbox")
    xbox = XboxTeleop(xbox_config)

    try:
        # Connect to controller
        xbox.connect()
        print("Controller connected successfully!\n")

        print("Testing controller inputs...")
        print("Move left stick, right stick, D-pad, or press buttons to see output.")
        print("Press Back button to exit.\n")

        while True:
            # Get action and events
            action = xbox.get_action()
            events = xbox.get_teleop_events()

            # Print non-zero values
            active_actions = {k: v for k, v in action.items() if abs(v) > 0.001}
            if active_actions:
                print(f"Actions: {active_actions}")

            # Check for quit
            if events.get("terminate_episode", False):
                print("Back button pressed - exiting...")
                break

            time.sleep(0.033)  # ~30 FPS

    except KeyboardInterrupt:
        print("\nKeyboard interrupt - exiting...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        xbox.disconnect()
        print("Disconnected from controller.")

if __name__ == "__main__":
    test_xbox_controller()