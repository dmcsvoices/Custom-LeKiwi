#!/usr/bin/env python
"""
Holonomic control demo - combining strafe and rotation.
Shows smooth curved paths and precise positioning.
"""

import sys
import time
import math
sys.path.insert(0, '/home/darren/lerobot/examples/lekiwi')

from agent_control import LeKiwiAgentLoop, AgentInterface

def save_image(img, filename):
    from PIL import Image
    Image.fromarray(img).save(filename)
    return filename

def main():
    print("=" * 60)
    print("🔄🚗 Holonomic Control Demo")
    print("Combined Strafe + Rotation Movements")
    print("=" * 60)
    
    print("\n📡 Connecting...")
    loop = LeKiwiAgentLoop(robot_ip="localhost", fps=30, enable_visualization=False)
    loop.start()
    agent = AgentInterface(loop.agent_teleop)
    print("✓ Connected")
    
    print("\n⏳ Waiting for cameras...")
    for _ in range(20):
        obs = agent.get_observation()
        if obs and 'front' in obs:
            break
        time.sleep(0.1)
    
    timestamp = int(time.time())
    save_image(obs['front'], f'/tmp/holo_start_{timestamp}.jpg')
    print("📸 Starting position saved")
    
    # Holonomic movement patterns
    movements = [
        ("↗️ Diagonal forward-right + rotate CW", 0.15, -0.15, -30, 2.0),
        ("⏸️ Stop & observe", 0, 0, 0, 1.0),
        ("↖️ Diagonal forward-left + rotate CCW", 0.15, 0.15, 30, 2.0),
        ("⏸️ Stop & observe", 0, 0, 0, 1.0),
        ("➡️ Pure strafe right while spinning", 0, -0.15, 45, 3.0),
        ("⏸️ Stop & observe", 0, 0, 0, 1.0),
        ("🌀 Circle pattern (forward + rotate)", 0.12, 0, 45, 4.0),
        ("⏸️ Stop & observe", 0, 0, 0, 1.0),
        ("🎯 Precision approach (slow diagonal)", 0.08, 0.08, 0, 2.0),
        ("🔄 Fine rotation in place", 0, 0, 20, 2.0),
        ("⏸️ Final stop", 0, 0, 0, 0.5),
    ]
    
    print(f"\n🎬 Executing {len(movements)} holonomic patterns")
    print("-" * 60)
    
    img_counter = 0
    
    for i, (desc, x_vel, y_vel, rot_vel, duration) in enumerate(movements, 1):
        print(f"\n{i}. {desc}")
        print(f"   Command: x={x_vel:+.2f}, y={y_vel:+.2f}, rot={rot_vel:+.1f}°/s for {duration}s")
        
        if x_vel == 0 and y_vel == 0 and rot_vel == 0:
            agent.stop_base()
            print("   🛑 Stopped")
            time.sleep(duration)
        else:
            # Convert deg/s to agent format (it expects deg/s)
            agent.move_base(x_vel, y_vel, rot_vel, duration=duration)
            
            # Monitor and capture
            start_time = time.time()
            last_save = 0
            while time.time() - start_time < duration + 0.3:
                obs = agent.get_observation()
                elapsed = time.time() - start_time
                
                if obs and elapsed - last_save > 1.0 and elapsed < duration:
                    img_counter += 1
                    save_image(obs['front'], f'/tmp/holo_{i:02d}_{img_counter:02d}.jpg')
                    print(f"   📸 t={elapsed:.1f}s")
                    last_save = elapsed
                
                time.sleep(0.05)
        
        # Show current velocity after movement
        obs = agent.get_observation()
        if obs:
            xv = obs.get('x.vel', 0)
            yv = obs.get('y.vel', 0)
            tv = obs.get('theta.vel', 0)
            print(f"   ✓ Complete | v=({xv:+.2f}, {yv:+.2f}, {tv:+.1f})")
    
    print("\n" + "=" * 60)
    print("✅ Holonomic demo complete!")
    print("=" * 60)
    print(f"\n📁 Saved {img_counter + 1} images to /tmp/holo_*.jpg")
    
    loop.stop()
    print("✓ Disconnected")

if __name__ == "__main__":
    main()
