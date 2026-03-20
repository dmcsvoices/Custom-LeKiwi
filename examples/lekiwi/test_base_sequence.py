#!/usr/bin/env python
"""
Comprehensive base movement sequence for LeKiwi
Tests: forward, backward, strafe left/right, rotation
Uses velocity feedback instead of position (odometry not available)
"""

import sys
import time
sys.path.insert(0, '/home/darren/lerobot/examples/lekiwi')

from agent_control import LeKiwiAgentLoop, AgentInterface

# Movement configuration
SPEED = 0.2        # m/s - moderate speed for safety
ROT_SPEED = 45.0   # deg/s - rotation speed
DURATION = 1.5     # seconds per movement
PAUSE = 0.5        # seconds between movements

def main():
    print("=" * 50)
    print("🚗 LeKiwi Base Movement Sequence Test")
    print("=" * 50)
    print(f"Speed: {SPEED} m/s | Rotation: {ROT_SPEED} deg/s")
    print(f"Duration: {DURATION}s per move | Pause: {PAUSE}s")
    print("=" * 50)
    
    # Initialize
    print("\n📡 Connecting to robot...")
    loop = LeKiwiAgentLoop(robot_ip="localhost", fps=30, enable_visualization=False)
    loop.start()
    agent = AgentInterface(loop.agent_teleop)
    print("✓ Connected")
    
    # Wait for first observation
    print("\n⏳ Waiting for first observation...")
    for _ in range(10):
        obs = agent.get_observation()
        if obs is not None:
            break
        time.sleep(0.1)
    
    if obs is None:
        print("❌ Failed to get observation")
        loop.stop()
        return
    
    # Show initial velocity state
    x_vel = obs.get('x.vel', 0)
    y_vel = obs.get('y.vel', 0)
    theta_vel = obs.get('theta.vel', 0)
    print(f"\n📊 Initial velocity: x={x_vel:.2f}, y={y_vel:.2f}, θ={theta_vel:.2f}")
    
    movements = [
        ("⬆️  Forward", SPEED, 0, 0),
        ("⏸️  Stop", 0, 0, 0),
        ("⬇️  Backward", -SPEED, 0, 0),
        ("⏸️  Stop", 0, 0, 0),
        ("➡️  Strafe Right", 0, -SPEED, 0),
        ("⏸️  Stop", 0, 0, 0),
        ("⬅️  Strafe Left", 0, SPEED, 0),
        ("⏸️  Stop", 0, 0, 0),
        ("🔄 Rotate CW", 0, 0, -ROT_SPEED),
        ("⏸️  Stop", 0, 0, 0),
        ("🔄 Rotate CCW", 0, 0, ROT_SPEED),
        ("⏸️  Stop", 0, 0, 0),
    ]
    
    print(f"\n🎬 Starting movement sequence ({len(movements)} actions)...")
    print("-" * 50)
    
    for i, (name, x_cmd, y_cmd, theta_cmd) in enumerate(movements, 1):
        print(f"\n{i:2d}. {name}")
        
        # Get velocities before command
        obs_before = agent.get_observation()
        x_before = obs_before.get('x.vel', 0)
        y_before = obs_before.get('y.vel', 0)
        theta_before = obs_before.get('theta.vel', 0)
        
        print(f"    Before: x={x_before:+.2f}, y={y_before:+.2f}, θ={theta_before:+.2f}")
        
        # Send movement command
        if "Stop" in name:
            agent.stop_base()
        else:
            agent.move_base(x_cmd, y_cmd, theta_cmd, duration=DURATION)
        
        # Monitor velocities during movement
        max_x, max_y, max_theta = 0, 0, 0
        start_time = time.time()
        while time.time() - start_time < DURATION:
            obs = agent.get_observation()
            if obs:
                max_x = max(max_x, abs(obs.get('x.vel', 0)))
                max_y = max(max_y, abs(obs.get('y.vel', 0)))
                max_theta = max(max_theta, abs(obs.get('theta.vel', 0)))
            time.sleep(0.05)
        
        # Get velocities after command
        obs_after = agent.get_observation()
        x_after = obs_after.get('x.vel', 0)
        y_after = obs_after.get('y.vel', 0)
        theta_after = obs_after.get('theta.vel', 0)
        
        print(f"    After:  x={x_after:+.2f}, y={y_after:+.2f}, θ={theta_after:+.2f}")
        
        if "Stop" not in name:
            print(f"    Peak:   x={max_x:.2f}, y={max_y:.2f}, θ={max_theta:.2f}")
            
            # Check if movement was detected
            threshold = 0.05  # 5 cm/s or deg/s threshold
            moved = max_x > threshold or max_y > threshold or max_theta > threshold
            if moved:
                print(f"    ✅ Movement detected!")
            else:
                print(f"    ⚠️  No movement detected")
        
        # Pause between movements
        time.sleep(PAUSE)
    
    print("\n" + "=" * 50)
    print("✅ Movement sequence complete!")
    print("=" * 50)
    
    # Final stop
    print("\n🛑 Sending final stop command...")
    agent.stop_base()
    time.sleep(0.5)
    
    loop.stop()
    print("✓ Robot disconnected")
    print("\n✨ Test complete!")

if __name__ == "__main__":
    main()
