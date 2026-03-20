#!/usr/bin/env python
"""
Real-time door navigation for LeKiwi.
Streams camera and navigates through the door to the left.
"""

import sys
import time
sys.path.insert(0, '/home/darren/lerobot/examples/lekiwi')

from agent_control import LeKiwiAgentLoop, AgentInterface

def save_image(img, filename):
    """Save a numpy image to file."""
    from PIL import Image
    Image.fromarray(img).save(filename)
    return filename

def main():
    print("=" * 60)
    print("🚪🚗 Door Navigation Mission")
    print("=" * 60)
    print("\nStreaming cameras and navigating through the door to the left.")
    print("-" * 60)
    
    # Initialize
    print("\n📡 Connecting to robot...")
    loop = LeKiwiAgentLoop(robot_ip="localhost", fps=30, enable_visualization=False)
    loop.start()
    agent = AgentInterface(loop.agent_teleop)
    print("✓ Connected")
    
    # Wait for camera feed
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
    
    print("✓ Cameras active")
    print(f"   Front: {obs['front'].shape}")
    print(f"   Wrist: {obs['wrist'].shape}")
    print(f"   Top: {obs['top'].shape}")
    
    # Save initial view
    timestamp = int(time.time())
    save_image(obs['front'], f'/tmp/door_nav_start_{timestamp}.jpg')
    print(f"\n📸 Saved initial view")
    
    # Navigation parameters
    speed = 0.15  # m/s - cautious speed
    rot_speed = 30  # deg/s
    
    print("\n" + "=" * 60)
    print("🎬 Starting door navigation sequence")
    print("=" * 60)
    
    img_counter = 0
    
    # Phase 1: Rotate left to face the door
    print("\n🔄 Phase 1: Rotating left to face the door...")
    agent.move_base(0, 0, rot_speed, duration=2.0)  # Rotate left ~60°
    
    start_time = time.time()
    while time.time() - start_time < 2.5:
        obs = agent.get_observation()
        if obs and time.time() - start_time > 1.0 and img_counter < 1:
            img_counter += 1
            save_image(obs['front'], f'/tmp/door_phase1_{img_counter}.jpg')
            print(f"   📸 Frame saved - should see door now")
        time.sleep(0.1)
    
    time.sleep(0.5)
    
    # Phase 2: Move forward toward door
    print("\n⬆️ Phase 2: Moving forward toward door...")
    agent.move_base(speed, 0, 0, duration=3.0)
    
    start_time = time.time()
    last_save = 0
    while time.time() - start_time < 3.5:
        obs = agent.get_observation()
        elapsed = time.time() - start_time
        if obs and elapsed - last_save > 1.0:
            img_counter += 1
            save_image(obs['front'], f'/tmp/door_phase2_{img_counter}.jpg')
            print(f"   📸 t={elapsed:.1f}s - approaching door")
            last_save = elapsed
        time.sleep(0.05)
    
    time.sleep(0.5)
    
    # Phase 3: Fine-tune alignment - rotate slightly if needed
    print("\n🔄 Phase 3: Fine-tuning alignment...")
    agent.move_base(0, 0, rot_speed * 0.3, duration=1.0)  # Small adjustment
    time.sleep(1.5)
    
    img_counter += 1
    obs = agent.get_observation()
    if obs:
        save_image(obs['front'], f'/tmp/door_phase3_{img_counter}.jpg')
        print(f"   📸 Aligned for door entry")
    
    time.sleep(0.5)
    
    # Phase 4: Move through the door
    print("\n🚪 Phase 4: Moving through the door...")
    agent.move_base(speed, 0, 0, duration=3.0)
    
    start_time = time.time()
    last_save = 0
    while time.time() - start_time < 3.5:
        obs = agent.get_observation()
        elapsed = time.time() - start_time
        if obs and elapsed - last_save > 1.0:
            img_counter += 1
            save_image(obs['front'], f'/tmp/door_phase4_{img_counter}.jpg')
            print(f"   📸 t={elapsed:.1f}s - moving through doorway")
            last_save = elapsed
        time.sleep(0.05)
    
    time.sleep(0.5)
    
    # Phase 5: Clear the door and stop
    print("\n✅ Phase 5: Clearing doorway and stopping...")
    agent.move_base(speed, 0, 0, duration=1.0)
    time.sleep(1.5)
    
    agent.stop_base()
    
    # Final snapshot
    img_counter += 1
    obs = agent.get_observation()
    if obs:
        save_image(obs['front'], f'/tmp/door_complete_{img_counter}.jpg')
        print(f"   📸 Final position - through the door!")
    
    print("\n" + "=" * 60)
    print("✅ Door navigation complete!")
    print("=" * 60)
    print(f"\n📁 Saved {img_counter} navigation frames to /tmp/")
    print("   View with: ls -la /tmp/door_*.jpg")
    
    # Cleanup
    loop.stop()
    print("\n✓ Robot disconnected")

if __name__ == "__main__":
    main()
