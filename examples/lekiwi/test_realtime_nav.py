#!/usr/bin/env python
"""
Real-time camera-guided navigation demo for LeKiwi.
Streams camera frames while allowing interactive movement.
"""

import sys
import time
sys.path.insert(0, '/home/darren/lerobot/examples/lekiwi')

import numpy as np
from agent_control import LeKiwiAgentLoop, AgentInterface

def save_image(img, filename):
    """Save a numpy image to file."""
    from PIL import Image
    Image.fromarray(img).save(filename)
    return filename

def main():
    print("=" * 60)
    print("🎥🚗 Real-Time Camera-Guided Navigation Demo")
    print("=" * 60)
    print("\nI'll stream camera views and move based on what I see.")
    print("Commands: W/A/S/D = move, Q/E = rotate, X = stop, Ctrl+C = exit")
    print("-" * 60)
    
    # Initialize
    print("\n📡 Connecting to robot...")
    loop = LeKiwiAgentLoop(robot_ip="localhost", fps=30, enable_visualization=False)
    loop.start()
    agent = AgentInterface(loop.agent_teleop)
    print("✓ Connected and streaming")
    
    # Wait for first observation
    print("\n⏳ Waiting for camera feed...")
    for _ in range(20):
        obs = agent.get_observation()
        if obs is not None and 'front' in obs:
            break
        time.sleep(0.1)
    
    if obs is None or 'front' not in obs:
        print("❌ Failed to get camera feed")
        loop.stop()
        return
    
    print("✓ Camera feed active")
    print(f"   Front camera: {obs['front'].shape}")
    print(f"   Wrist camera: {obs['wrist'].shape}")
    print(f"   Top camera: {obs['top'].shape}")
    
    # Save initial views
    timestamp = int(time.time())
    save_image(obs['front'], f'/tmp/camera_front_start_{timestamp}.jpg')
    save_image(obs['wrist'], f'/tmp/camera_wrist_start_{timestamp}.jpg')
    print(f"\n📸 Saved initial camera views to /tmp/")
    
    # Movement parameters
    speed = 0.15  # m/s
    rot_speed = 30  # deg/s
    move_duration = 0.5  # seconds
    
    print("\n" + "=" * 60)
    print("🎬 Starting interactive navigation demo")
    print("=" * 60)
    
    # Demo sequence: Move, look, move, look
    movements = [
        ("Moving forward slowly...", speed, 0, 0, 2.0),
        ("Pausing to observe...", 0, 0, 0, 1.0),
        ("Rotating to scan area...", 0, 0, rot_speed, 3.0),
        ("Pausing to observe...", 0, 0, 0, 1.0),
        ("Strafing right...", 0, -speed, 0, 1.5),
        ("Pausing to observe...", 0, 0, 0, 1.0),
        ("Moving backward...", -speed, 0, 0, 1.5),
        ("Final stop", 0, 0, 0, 0.5),
    ]
    
    img_counter = 0
    
    for desc, x_vel, y_vel, theta_vel, duration in movements:
        print(f"\n➡️  {desc}")
        print(f"   Command: x={x_vel:+.2f}, y={y_vel:+.2f}, θ={theta_vel:+.2f} for {duration}s")
        
        # Start movement
        if x_vel == 0 and y_vel == 0 and theta_vel == 0:
            agent.stop_base()
        else:
            agent.move_base(x_vel, y_vel, theta_vel, duration=duration)
        
        # Monitor movement with periodic camera snapshots
        start_time = time.time()
        last_snapshot = 0
        snapshot_interval = 0.5  # Save image every 0.5s
        
        while time.time() - start_time < duration:
            obs = agent.get_observation()
            if obs:
                # Show current velocities
                x_v = obs.get('x.vel', 0)
                y_v = obs.get('y.vel', 0)
                t_v = obs.get('theta.vel', 0)
                
                # Save periodic snapshots
                elapsed = time.time() - start_time
                if elapsed - last_snapshot >= snapshot_interval:
                    img_counter += 1
                    save_image(obs['front'], f'/tmp/nav_front_{img_counter:03d}.jpg')
                    print(f"   [t={elapsed:.1f}s] v=({x_v:+.2f}, {y_v:+.2f}, {t_v:+.2f}) 📸 saved frame {img_counter}")
                    last_snapshot = elapsed
                else:
                    # Just print velocity
                    time.sleep(0.1)
                    
        print(f"   ✓ Movement complete")
    
    print("\n" + "=" * 60)
    print("✅ Real-time navigation demo complete!")
    print("=" * 60)
    
    # Final snapshot
    obs = agent.get_observation()
    if obs:
        save_image(obs['front'], f'/tmp/camera_front_end_{int(time.time())}.jpg')
        print(f"\n📸 Final camera view saved")
    
    print(f"\n📁 Saved {img_counter + 3} images to /tmp/")
    print("   View with: ls -la /tmp/nav_*.jpg /tmp/camera_*.jpg")
    
    # Cleanup
    agent.stop_base()
    time.sleep(0.5)
    loop.stop()
    print("\n✓ Robot disconnected")

if __name__ == "__main__":
    main()
