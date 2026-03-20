#!/usr/bin/env python

"""
Test script to verify the initialization and joint limits fix.

This should now properly initialize from robot's actual position
and allow full range of movement.
"""

import time
from lerobot.robots.lekiwi import LeKiwiClient, LeKiwiClientConfig
from lerobot.teleoperators.xbox import XboxTeleop, XboxTeleopConfig
from lerobot.utils.robot_utils import busy_wait

FPS = 30

def main():
    print("=== INITIALIZATION & JOINT LIMITS FIX TEST ===")
    print("This should fix the 1-degree limitation issue.")
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
        print("=== INITIALIZATION FIX ===")
        print("Key improvements:")
        print("- Initialize arm positions from robot's actual position")
        print("- Expanded joint limits: ±180° → ±720°")
        print("- Expanded gripper limits: ±1.0 → ±2.0")
        print("- Should eliminate 1-degree movement restriction")
        print()
        print("Watch for initialization message...")
        print()

        loop_count = 0
        last_positions = {}
        initialized_shown = False

        while True:
            t0 = time.perf_counter()
            loop_count += 1

            # Get robot observation
            observation = robot.get_observation()

            # Get Xbox controller action WITH observation (for initialization)
            xbox_action = xbox.get_action(observation)

            # Show initialization info once
            if xbox.initialized and not initialized_shown:
                print("*** ROBOT INITIALIZED ***")
                print("Starting positions:")
                for joint, pos in xbox.arm_positions.items():
                    if pos is not None:
                        degrees = pos * 180 / 3.14159
                        print(f"  {joint}: {pos:.3f} rad ({degrees:.1f}°)")
                print()
                initialized_shown = True

            # Create action with proper key format for LeKiwiClient
            action = {f"{k}.pos": v for k, v in xbox_action.items() if k.startswith("arm_")}
            action.update({k: v for k, v in xbox_action.items() if k in ["x.vel", "y.vel", "theta.vel"]})

            # Send action to robot
            robot.send_action(action)

            # Show position updates every 20 loops
            if observation and loop_count % 20 == 0 and xbox.initialized:
                current_positions = {k: v for k, v in observation.items() if k.startswith("arm_")}

                if last_positions:
                    print(f"--- Position Update (loop {loop_count}) ---")
                    total_movement = 0
                    for joint, current_pos in sorted(current_positions.items()):
                        if joint in last_positions:
                            change = current_pos - last_positions[joint]
                            degrees_change = abs(change) * 180 / 3.14159
                            total_movement += degrees_change
                            if abs(change) > 0.005:  # Show significant changes
                                print(f"{joint}: {current_pos:.3f} rad ({change:+.3f} change, {degrees_change:.1f}° moved)")

                    if total_movement > 0:
                        print(f"Total movement this period: {total_movement:.1f}°")
                    else:
                        print("No movement detected")

                    # Show active commands
                    arm_commands = {k: v for k, v in xbox_action.items() if k.startswith("arm_")}
                    active_commands = [k for k, v in arm_commands.items() if abs(v) > 0.01]
                    if active_commands:
                        print(f"Active commands: {active_commands}")
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
        print("- Should see proper initialization from robot position")
        print("- ARM movement should NOT be limited to 1 degree")
        print("- All joints (shoulder, elbow, wrist) should respond")
        print("- Gripper should respond to triggers")

if __name__ == "__main__":
    main()